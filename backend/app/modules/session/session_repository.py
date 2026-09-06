"""Repository layer for Sessions, Clinical Notes, and Therapy Goals in MongoDB."""

from datetime import UTC, datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, IndexModel

from app.modules.session.session_constants import AttendanceStatus, GoalStatus, SessionStatus
from app.modules.session.session_model import SessionInDB, SessionNoteInDB, TherapyGoalInDB


class SessionRepository:
    """Data access layer managing sessions, clinical notes, and goals."""

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, Any]]) -> None:
        self.db = db
        self.sessions = db["sessions"]
        self.session_notes = db["session_notes"]
        self.therapy_goals = db["therapy_goals"]

    async def create_indexes(self) -> None:
        """Create indexes for deterministic querying and integrity constraints."""
        session_indexes = [
            # Exactly one session per booking
            IndexModel([("booking_id", ASCENDING)], unique=True, name="idx_sessions_booking_unique"),
            # Therapist agenda & session lookup
            IndexModel([("therapist_id", ASCENDING), ("scheduled_start_at", ASCENDING)], name="idx_sessions_therapist_time"),
            # Client session history
            IndexModel([("client_id", ASCENDING), ("scheduled_start_at", ASCENDING)], name="idx_sessions_client_time"),
            # Status filters
            IndexModel([("status", ASCENDING), ("scheduled_start_at", ASCENDING)], name="idx_sessions_status_time"),
        ]
        await self.sessions.create_indexes(session_indexes)

        notes_indexes = [
            IndexModel([("session_id", ASCENDING)], unique=True, name="idx_session_notes_session_unique"),
            IndexModel([("therapist_id", ASCENDING)], name="idx_session_notes_therapist"),
            IndexModel([("client_id", ASCENDING)], name="idx_session_notes_client"),
        ]
        await self.session_notes.create_indexes(notes_indexes)

        goals_indexes = [
            IndexModel([("client_id", ASCENDING), ("status", ASCENDING)], name="idx_goals_client_status"),
            IndexModel([("therapist_id", ASCENDING)], name="idx_goals_therapist"),
            IndexModel([("session_id", ASCENDING)], name="idx_goals_session"),
        ]
        await self.therapy_goals.create_indexes(goals_indexes)

    # --- Session Operations ---

    async def create_session(self, session: SessionInDB) -> SessionInDB:
        await self.sessions.insert_one(session.model_dump())
        return session

    async def get_session_by_id(self, session_id: str) -> SessionInDB | None:
        doc = await self.sessions.find_one({"id": session_id})
        return SessionInDB(**doc) if doc else None

    async def get_session_by_booking_id(self, booking_id: str) -> SessionInDB | None:
        doc = await self.sessions.find_one({"booking_id": booking_id})
        return SessionInDB(**doc) if doc else None

    async def start_session_atomic(self, session_id: str, started_at: datetime) -> SessionInDB | None:
        """Atomically transition session to IN_PROGRESS if SCHEDULED or READY."""
        now = datetime.now(UTC)
        query = {
            "id": session_id,
            "status": {"$in": [SessionStatus.SCHEDULED.value, SessionStatus.READY.value]},
        }
        update = {
            "$set": {
                "status": SessionStatus.IN_PROGRESS.value,
                "started_at": started_at,
                "updated_at": now,
            }
        }
        doc = await self.sessions.find_one_and_update(query, update, return_document=True)
        return SessionInDB(**doc) if doc else None

    async def complete_session_atomic(self, session_id: str, ended_at: datetime) -> SessionInDB | None:
        """Atomically transition session to COMPLETED if IN_PROGRESS."""
        now = datetime.now(UTC)
        query = {
            "id": session_id,
            "status": SessionStatus.IN_PROGRESS.value,
        }
        update = {
            "$set": {
                "status": SessionStatus.COMPLETED.value,
                "ended_at": ended_at,
                "updated_at": now,
            }
        }
        doc = await self.sessions.find_one_and_update(query, update, return_document=True)
        return SessionInDB(**doc) if doc else None

    async def update_attendance(self, session_id: str, attendance: AttendanceStatus) -> SessionInDB | None:
        now = datetime.now(UTC)
        doc = await self.sessions.find_one_and_update(
            {"id": session_id},
            {"$set": {"attendance": attendance.value, "updated_at": now}},
            return_document=True,
        )
        return SessionInDB(**doc) if doc else None

    async def cancel_session(self, session_id: str) -> SessionInDB | None:
        now = datetime.now(UTC)
        doc = await self.sessions.find_one_and_update(
            {"id": session_id},
            {"$set": {"status": SessionStatus.CANCELLED.value, "updated_at": now}},
            return_document=True,
        )
        return SessionInDB(**doc) if doc else None

    async def find_therapist_sessions(
        self,
        therapist_id: str,
        start_min: datetime | None = None,
        start_max: datetime | None = None,
        status: SessionStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[SessionInDB], int]:
        query: dict[str, Any] = {"therapist_id": therapist_id}
        if status:
            query["status"] = status.value
        if start_min or start_max:
            time_filter: dict[str, Any] = {}
            if start_min:
                time_filter["$gte"] = start_min
            if start_max:
                time_filter["$lte"] = start_max
            query["scheduled_start_at"] = time_filter

        total = await self.sessions.count_documents(query)
        cursor = self.sessions.find(query).sort("scheduled_start_at", ASCENDING).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [SessionInDB(**d) for d in docs], total

    async def find_client_sessions(
        self,
        client_id: str,
        status: SessionStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[SessionInDB], int]:
        query: dict[str, Any] = {"client_id": client_id}
        if status:
            query["status"] = status.value

        total = await self.sessions.count_documents(query)
        cursor = self.sessions.find(query).sort("scheduled_start_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [SessionInDB(**d) for d in docs], total

    # --- Clinical Notes Operations ---

    async def get_note_by_session_id(self, session_id: str) -> SessionNoteInDB | None:
        doc = await self.session_notes.find_one({"session_id": session_id})
        return SessionNoteInDB(**doc) if doc else None

    async def upsert_note(self, note: SessionNoteInDB) -> SessionNoteInDB:
        now = datetime.now(UTC)
        await self.session_notes.update_one(
            {"session_id": note.session_id},
            {
                "$set": {
                    "summary": note.summary,
                    "private_notes": note.private_notes,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "id": note.id,
                    "session_id": note.session_id,
                    "therapist_id": note.therapist_id,
                    "client_id": note.client_id,
                    "created_at": now,
                },
            },
            upsert=True,
        )
        updated = await self.get_note_by_session_id(note.session_id)
        assert updated is not None
        return updated

    # --- Therapy Goals Operations ---

    async def create_goal(self, goal: TherapyGoalInDB) -> TherapyGoalInDB:
        await self.therapy_goals.insert_one(goal.model_dump())
        return goal

    async def get_goal_by_id(self, goal_id: str) -> TherapyGoalInDB | None:
        doc = await self.therapy_goals.find_one({"id": goal_id})
        return TherapyGoalInDB(**doc) if doc else None

    async def list_goals_by_session(self, session_id: str) -> list[TherapyGoalInDB]:
        cursor = self.therapy_goals.find({"session_id": session_id}).sort("created_at", -1)
        docs = await cursor.to_list(length=100)
        return [TherapyGoalInDB(**d) for d in docs]

    async def list_client_goals(self, client_id: str) -> list[TherapyGoalInDB]:
        cursor = self.therapy_goals.find({"client_id": client_id}).sort("created_at", -1)
        docs = await cursor.to_list(length=100)
        return [TherapyGoalInDB(**d) for d in docs]

    async def update_goal(
        self, goal_id: str, title: str | None, description: str | None, status: GoalStatus | None
    ) -> TherapyGoalInDB | None:
        now = datetime.now(UTC)
        fields: dict[str, Any] = {"updated_at": now}
        if title is not None:
            fields["title"] = title
        if description is not None:
            fields["description"] = description
        if status is not None:
            fields["status"] = status.value

        doc = await self.therapy_goals.find_one_and_update(
            {"id": goal_id},
            {"$set": fields},
            return_document=True,
        )
        return TherapyGoalInDB(**doc) if doc else None
