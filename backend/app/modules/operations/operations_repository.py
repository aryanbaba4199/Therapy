"""MongoDB repositories for Audit Logs, Leads, and Operations Metrics aggregation."""

from datetime import datetime, time
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.utils.datetime_utils import utc_now
from app.modules.operations.operations_constants import AuditAction, LeadStatus
from app.modules.operations.operations_model import AuditLogInDB, LeadInDB


class OperationsRepository:
    """Encapsulates MongoDB collections for audit logs, leads, and metric queries."""

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, Any]]) -> None:
        self.db = db
        self.audit_logs = db["audit_logs"]
        self.leads = db["leads"]
        self.users = db["users"]
        self.therapists = db["therapists"]
        self.bookings = db["bookings"]
        self.sessions = db["sessions"]
        self.payments = db["payments"]
        self.support_tickets = db["support_tickets"]

    async def ensure_indexes(self) -> None:
        """Create database indexes for optimal operational lookups."""
        audit_indexes = [
            IndexModel([("created_at", DESCENDING)], name="idx_audit_created_at"),
            IndexModel([("actor_id", ASCENDING), ("created_at", DESCENDING)], name="idx_audit_actor"),
            IndexModel(
                [("resource_type", ASCENDING), ("resource_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_audit_resource",
            ),
            IndexModel([("action", ASCENDING), ("created_at", DESCENDING)], name="idx_audit_action"),
        ]
        await self.audit_logs.create_indexes(audit_indexes)

        lead_indexes = [
            IndexModel([("status", ASCENDING), ("next_follow_up_at", ASCENDING)], name="idx_lead_status_followup"),
            IndexModel([("assigned_to", ASCENDING), ("status", ASCENDING)], name="idx_lead_assigned_status"),
            IndexModel([("phone", ASCENDING)], name="idx_lead_phone"),
            IndexModel([("email", ASCENDING)], name="idx_lead_email"),
            IndexModel([("created_at", DESCENDING)], name="idx_lead_created_at"),
        ]
        await self.leads.create_indexes(lead_indexes)

    # --- Audit Log Operations (Append-Only) ---

    async def record_audit_event(self, event: AuditLogInDB) -> AuditLogInDB:
        """Append an immutable audit record."""
        await self.audit_logs.insert_one(event.model_dump())
        return event

    async def list_audit_logs(
        self,
        actor_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        action: AuditAction | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[AuditLogInDB], int]:
        """List audit records with filtering and pagination."""
        query: dict[str, Any] = {}
        if actor_id:
            query["actor_id"] = actor_id
        if resource_type:
            query["resource_type"] = resource_type
        if resource_id:
            query["resource_id"] = resource_id
        if action:
            query["action"] = action.value

        total = await self.audit_logs.count_documents(query)
        cursor = (
            self.audit_logs.find(query)
            .sort("created_at", DESCENDING)
            .skip((page - 1) * limit)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [AuditLogInDB(**d) for d in docs], total

    # --- Lead Operations ---

    async def create_lead(self, lead: LeadInDB) -> LeadInDB:
        """Insert a new prospective lead."""
        await self.leads.insert_one(lead.model_dump())
        return lead

    async def get_lead_by_id(self, lead_id: str) -> LeadInDB | None:
        """Retrieve lead by UUID."""
        doc = await self.leads.find_one({"id": lead_id})
        return LeadInDB(**doc) if doc else None

    async def update_lead(self, lead_id: str, updates: dict[str, Any]) -> LeadInDB | None:
        """Update lead fields."""
        updates["updated_at"] = utc_now()
        doc = await self.leads.find_one_and_update(
            {"id": lead_id},
            {"$set": updates},
            return_document=True,
        )
        return LeadInDB(**doc) if doc else None

    async def list_leads(
        self,
        status: LeadStatus | None = None,
        assigned_to: str | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[LeadInDB], int]:
        """List and search leads."""
        query: dict[str, Any] = {}
        if status:
            query["status"] = status.value
        if assigned_to:
            query["assigned_to"] = assigned_to
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"phone": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
            ]

        total = await self.leads.count_documents(query)
        cursor = (
            self.leads.find(query)
            .sort("created_at", DESCENDING)
            .skip((page - 1) * limit)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [LeadInDB(**d) for d in docs], total

    # --- Operational Aggregated Metrics ---

    async def get_dashboard_metrics(self) -> dict[str, Any]:
        """Aggregate high-level operational statistics using MongoDB queries."""
        now = utc_now()
        today_start = datetime.combine(now.date(), time.min)
        today_end = datetime.combine(now.date(), time.max)

        # 1. Today's bookings
        today_bookings = await self.bookings.count_documents(
            {"created_at": {"$gte": today_start, "$lte": today_end}}
        )

        # 2. Upcoming sessions (scheduled or ready, start_at >= now)
        upcoming_sessions = await self.sessions.count_documents(
            {"status": {"$in": ["scheduled", "ready"]}, "start_at": {"$gte": now}}
        )

        # 3. Completed sessions
        completed_sessions = await self.sessions.count_documents({"status": "completed"})

        # 4. Active therapists & pending verification
        active_therapists = await self.therapists.count_documents({"status": "active"})
        pending_verification_therapists = await self.therapists.count_documents(
            {"verification.status": "pending"}
        )

        # 5. Pending support tickets
        pending_support_tickets = await self.support_tickets.count_documents(
            {"status": {"$in": ["open", "in_progress", "waiting_for_user"]}}
        )

        # 6. Failed payments
        failed_payments = await self.payments.count_documents({"status": "failed"})

        # 7. Total revenue minor (paid payments)
        pipeline: list[dict[str, Any]] = [
            {"$match": {"status": "paid"}},
            {"$group": {"_id": None, "total": {"$sum": "$final_amount_minor"}}},
        ]
        rev_res = await self.payments.aggregate(pipeline).to_list(1)
        total_revenue_minor = rev_res[0]["total"] if rev_res else 0

        # 8. New leads
        new_leads = await self.leads.count_documents({"status": LeadStatus.NEW.value})

        return {
            "today_bookings": today_bookings,
            "upcoming_sessions": upcoming_sessions,
            "completed_sessions": completed_sessions,
            "active_therapists": active_therapists,
            "pending_verification_therapists": pending_verification_therapists,
            "pending_support_tickets": pending_support_tickets,
            "failed_payments_count": failed_payments,
            "total_revenue_minor": total_revenue_minor,
            "new_leads_count": new_leads,
        }
