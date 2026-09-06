"""MongoDB persistence repository layer for Support domain."""

from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.utils.datetime_utils import utc_now
from app.modules.support.support_constants import (
    SupportCategory,
    SupportTicketStatus,
)
from app.modules.support.support_model import (
    SupportMessageInDB,
    SupportTicketInDB,
)


class SupportRepository:
    """Repository managing MongoDB operations for support tickets and conversations."""

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, Any]]) -> None:
        self.db = db
        self.tickets_collection = db.get_collection("support_tickets")
        self.messages_collection = db.get_collection("support_messages")
        self.counters = db.get_collection("counters")

    async def create_indexes(self) -> None:
        """Create query performance and uniqueness indexes."""
        ticket_indexes = [
            IndexModel(
                [("ticket_number", ASCENDING)],
                unique=True,
                name="idx_support_tickets_number_unique",
            ),
            IndexModel(
                [("requester_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_support_tickets_requester_created",
            ),
            IndexModel(
                [
                    ("assigned_to", ASCENDING),
                    ("status", ASCENDING),
                    ("updated_at", DESCENDING),
                ],
                name="idx_support_tickets_assigned_status_updated",
            ),
            IndexModel(
                [
                    ("status", ASCENDING),
                    ("priority", ASCENDING),
                    ("updated_at", DESCENDING),
                ],
                name="idx_support_tickets_status_priority_updated",
            ),
            IndexModel(
                [("category", ASCENDING), ("created_at", DESCENDING)],
                name="idx_support_tickets_category_created",
            ),
        ]
        await self.tickets_collection.create_indexes(ticket_indexes)

        message_indexes = [
            IndexModel(
                [("ticket_id", ASCENDING), ("created_at", ASCENDING)],
                name="idx_support_messages_ticket_created",
            ),
        ]
        await self.messages_collection.create_indexes(message_indexes)

    async def get_next_ticket_number(self) -> str:
        """Generate human-readable ticket number atomically using counters collection."""
        res = await self.counters.find_one_and_update(
            {"_id": "support_ticket"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True,
        )
        seq = res.get("seq", 1) if res else 1
        return f"TCK-{10000 + int(seq)}"

    async def create_ticket(self, ticket: SupportTicketInDB) -> SupportTicketInDB:
        """Insert a new support ticket."""
        doc = ticket.model_dump()
        await self.tickets_collection.insert_one(doc)
        return ticket

    async def get_ticket_by_id(self, ticket_id: str) -> SupportTicketInDB | None:
        """Find a ticket by its UUID."""
        doc = await self.tickets_collection.find_one({"id": ticket_id})
        if not doc:
            return None
        return SupportTicketInDB.model_validate(doc)

    async def list_tickets_for_requester(
        self,
        requester_id: str,
        status: SupportTicketStatus | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[SupportTicketInDB], int]:
        """List tickets created by a specific user with pagination."""
        query: dict[str, Any] = {"requester_id": requester_id}
        if status:
            query["status"] = status.value

        total = await self.tickets_collection.count_documents(query)
        skip = (page - 1) * limit
        cursor = (
            self.tickets_collection.find(query)
            .sort("updated_at", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [SupportTicketInDB.model_validate(d) for d in docs], total

    async def list_all_tickets(
        self,
        status: SupportTicketStatus | None = None,
        category: SupportCategory | None = None,
        assigned_to: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[SupportTicketInDB], int]:
        """List tickets across the system for staff/admin."""
        query: dict[str, Any] = {}
        if status:
            query["status"] = status.value
        if category:
            query["category"] = category.value
        if assigned_to:
            query["assigned_to"] = assigned_to

        total = await self.tickets_collection.count_documents(query)
        skip = (page - 1) * limit
        cursor = (
            self.tickets_collection.find(query)
            .sort("updated_at", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [SupportTicketInDB.model_validate(d) for d in docs], total

    async def update_ticket_status(
        self,
        ticket_id: str,
        status: SupportTicketStatus,
        resolved_at: datetime | None = None,
        closed_at: datetime | None = None,
    ) -> SupportTicketInDB | None:
        """Atomically transition ticket status."""
        update_fields: dict[str, Any] = {
            "status": status.value,
            "updated_at": utc_now(),
        }
        if resolved_at is not None:
            update_fields["resolved_at"] = resolved_at
        if closed_at is not None:
            update_fields["closed_at"] = closed_at

        doc = await self.tickets_collection.find_one_and_update(
            {"id": ticket_id},
            {"$set": update_fields},
            return_document=True,
        )
        if not doc:
            return None
        return SupportTicketInDB.model_validate(doc)

    async def assign_ticket(
        self, ticket_id: str, staff_id: str
    ) -> SupportTicketInDB | None:
        """Assign ticket to a staff member and transition to IN_PROGRESS if OPEN."""
        doc = await self.tickets_collection.find_one({"id": ticket_id})
        if not doc:
            return None

        current_status = doc.get("status")
        new_status = (
            SupportTicketStatus.IN_PROGRESS.value
            if current_status == SupportTicketStatus.OPEN.value
            else current_status
        )

        updated = await self.tickets_collection.find_one_and_update(
            {"id": ticket_id},
            {
                "$set": {
                    "assigned_to": staff_id,
                    "status": new_status,
                    "updated_at": utc_now(),
                }
            },
            return_document=True,
        )
        if not updated:
            return None
        return SupportTicketInDB.model_validate(updated)

    async def create_message(
        self, message: SupportMessageInDB
    ) -> SupportMessageInDB:
        """Insert a new conversation message and touch ticket's updated_at."""
        doc = message.model_dump()
        await self.messages_collection.insert_one(doc)
        # Touch ticket updated_at
        await self.tickets_collection.update_one(
            {"id": message.ticket_id},
            {"$set": {"updated_at": utc_now()}},
        )
        return message

    async def list_messages_for_ticket(
        self, ticket_id: str, include_internal: bool = False
    ) -> list[SupportMessageInDB]:
        """List messages chronologically for a ticket."""
        query: dict[str, Any] = {"ticket_id": ticket_id}
        if not include_internal:
            query["is_internal_note"] = False

        cursor = self.messages_collection.find(query).sort("created_at", ASCENDING)
        docs = await cursor.to_list(length=500)
        return [SupportMessageInDB.model_validate(d) for d in docs]
