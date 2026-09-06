"""Operational Service encapsulating administrative logic, lead triage, and audit emissions."""

import secrets
import uuid
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.common.exceptions.app_exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.common.exceptions.error_codes import ErrorCode
from app.common.utils.datetime_utils import utc_now
from app.modules.auth.auth_utils import hash_password
from app.modules.availability.availability_schema import SetWeeklyScheduleRequest
from app.modules.availability.availability_service import AvailabilityService
from app.modules.booking.booking_model import BookingInDB
from app.modules.booking.booking_repository import BookingRepository
from app.modules.operations.operations_constants import (
    ROLE_PERMISSIONS,
    AuditAction,
    LeadStatus,
    Permission,
)
from app.modules.operations.operations_model import AuditLogInDB, LeadInDB
from app.modules.operations.operations_repository import OperationsRepository
from app.modules.operations.operations_schema import (
    AdminDashboardMetricsResponse,
    LeadAssignRequest,
    LeadCreateRequest,
    LeadResponse,
    LeadUpdateRequest,
    OnboardTherapistRequest,
    OnboardTherapistResponse,
    OperationUserDetailResponse,
    UpdateUserRolesRequest,
    UpdateUserStatusRequest,
)
from app.modules.payment.payment_model import PaymentInDB
from app.modules.payment.payment_repository import PaymentRepository
from app.modules.therapist.therapist_constants import (
    TherapistStatus,
    TherapistVerificationStatus,
)
from app.modules.therapist.therapist_model import (
    PricingModel,
    TherapistInDB,
    VerificationModel,
)
from app.modules.therapist.therapist_repository import TherapistRepository
from app.modules.therapist.therapist_schema import (
    AdminUpdateTherapistVerificationRequest,
    TherapistDetailResponse,
    UpdateTherapistRequest,
)
from app.modules.therapist.therapist_service import TherapistService
from app.modules.user.user_constants import AuthProvider, UserRole, UserStatus
from app.modules.user.user_model import UserInDB
from app.modules.user.user_repository import UserRepository


class OperationsService:
    """Core administrative, first responder, and audit orchestration service."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase[dict[str, Any]],
        ops_repo: OperationsRepository,
        user_repo: UserRepository,
        therapist_repo: TherapistRepository,
        therapist_service: TherapistService,
        booking_repo: BookingRepository,
        payment_repo: PaymentRepository,
        availability_service: AvailabilityService,
    ) -> None:
        self.db = db
        self.ops_repo = ops_repo
        self.user_repo = user_repo
        self.therapist_repo = therapist_repo
        self.therapist_service = therapist_service
        self.booking_repo = booking_repo
        self.payment_repo = payment_repo
        self.availability_service = availability_service

    def has_permission(self, user: UserInDB, permission: Permission) -> bool:
        """Evaluate if user possesses a given operational permission."""
        if UserRole.SUPER_ADMIN in user.roles:
            return True
        for role in user.roles:
            role_perms = ROLE_PERMISSIONS.get(role.value, set())
            if permission in role_perms:
                return True
        return False

    def require_permission(self, user: UserInDB, permission: Permission) -> None:
        """Enforce permission, raising ForbiddenException on failure."""
        if not self.has_permission(user, permission):
            raise ForbiddenException(
                message=f"Access denied: Requires permission '{permission.value}'",
                code=ErrorCode.OPS_PERMISSION_REQUIRED,
            )

    async def log_audit_event(
        self,
        actor: UserInDB,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        metadata: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        """Append-only audit event logging."""
        primary_role = actor.roles[0].value if actor.roles else "user"
        event = AuditLogInDB(
            id=str(uuid.uuid4()),
            actor_id=actor.id,
            actor_role=primary_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata or {},
            request_id=request_id,
            created_at=utc_now(),
        )
        await self.ops_repo.record_audit_event(event)

    # --- Operational Dashboard ---

    async def get_dashboard_metrics(self, caller: UserInDB) -> AdminDashboardMetricsResponse:
        """Aggregate high-level operational statistics."""
        self.require_permission(caller, Permission.DASHBOARD_VIEW)
        metrics = await self.ops_repo.get_dashboard_metrics()
        return AdminDashboardMetricsResponse(**metrics)

    # --- User Management Operations ---

    async def list_users(
        self,
        caller: UserInDB,
        role: UserRole | None = None,
        status: UserStatus | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[OperationUserDetailResponse], int]:
        """List platform users with filtering."""
        self.require_permission(caller, Permission.USERS_READ)
        query: dict[str, Any] = {}
        if role:
            query["roles"] = role.value
        if status:
            query["status"] = status.value
        if search:
            query["$or"] = [
                {"first_name": {"$regex": search, "$options": "i"}},
                {"last_name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"phone": {"$regex": search, "$options": "i"}},
            ]

        total = await self.db["users"].count_documents(query)
        cursor = (
            self.db["users"]
            .find(query)
            .sort("created_at", -1)
            .skip((page - 1) * limit)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        users = [UserInDB(**d) for d in docs]
        return [OperationUserDetailResponse.from_db(u) for u in users], total

    async def get_user_detail(
        self, caller: UserInDB, user_id: str
    ) -> OperationUserDetailResponse:
        """Retrieve user details for operational review."""
        self.require_permission(caller, Permission.USERS_READ)
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(
                message=f"User '{user_id}' not found",
                code=ErrorCode.USER_NOT_FOUND,
            )
        return OperationUserDetailResponse.from_db(user)

    async def update_user_status(
        self,
        caller: UserInDB,
        user_id: str,
        req: UpdateUserStatusRequest,
        request_id: str | None = None,
    ) -> OperationUserDetailResponse:
        """Suspend or activate user account with audit logging."""
        self.require_permission(caller, Permission.USERS_SUSPEND)
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(
                message=f"User '{user_id}' not found",
                code=ErrorCode.USER_NOT_FOUND,
            )

        # Protection: Cannot suspend a Super Admin unless caller is Super Admin
        if UserRole.SUPER_ADMIN in user.roles and UserRole.SUPER_ADMIN not in caller.roles:
            raise ForbiddenException(
                message="Cannot modify Super Admin accounts",
                code=ErrorCode.OPS_ROLE_CHANGE_FORBIDDEN,
            )

        updated = await self.user_repo.update(user_id, {"status": req.status.value})
        assert updated is not None

        await self.log_audit_event(
            actor=caller,
            action=AuditAction.USER_STATUS_UPDATED,
            resource_type="user",
            resource_id=user_id,
            metadata={"old_status": user.status.value, "new_status": req.status.value, "reason": req.reason},
            request_id=request_id,
        )
        return OperationUserDetailResponse.from_db(updated)

    async def update_user_roles(
        self,
        caller: UserInDB,
        user_id: str,
        req: UpdateUserRolesRequest,
        request_id: str | None = None,
    ) -> OperationUserDetailResponse:
        """Modify user roles. Super Admin only."""
        self.require_permission(caller, Permission.ROLES_MANAGE)
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(
                message=f"User '{user_id}' not found",
                code=ErrorCode.USER_NOT_FOUND,
            )

        # Only super_admin can grant or revoke admin/super_admin roles
        is_elevated_assignment = any(
            r in req.roles or r in user.roles for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
        )
        if is_elevated_assignment and UserRole.SUPER_ADMIN not in caller.roles:
            raise ForbiddenException(
                message="Only Super Admin can assign or remove Admin and Super Admin roles",
                code=ErrorCode.OPS_ROLE_CHANGE_FORBIDDEN,
            )

        updated = await self.user_repo.update(user_id, {"roles": [r.value for r in req.roles]})
        assert updated is not None

        await self.log_audit_event(
            actor=caller,
            action=AuditAction.USER_ROLES_UPDATED,
            resource_type="user",
            resource_id=user_id,
            metadata={
                "old_roles": [r.value for r in user.roles],
                "new_roles": [r.value for r in req.roles],
                "reason": req.reason,
            },
            request_id=request_id,
        )
        return OperationUserDetailResponse.from_db(updated)

    # --- Therapist Operations ---

    async def list_therapists_operational(
        self,
        caller: UserInDB,
        status: str | None = None,
        verification_status: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[TherapistDetailResponse], int]:
        """Admin listing of therapists with operational details."""
        self.require_permission(caller, Permission.THERAPISTS_READ)
        query: dict[str, Any] = {}
        if status:
            query["status"] = status
        if verification_status:
            query["verification.status"] = verification_status

        total = await self.db["therapists"].count_documents(query)
        cursor = (
            self.db["therapists"]
            .find(query)
            .sort("created_at", -1)
            .skip((page - 1) * limit)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        therapists = [TherapistInDB(**d) for d in docs]
        return [TherapistDetailResponse.from_therapist_db(t) for t in therapists], total

    async def verify_therapist(
        self,
        caller: UserInDB,
        therapist_id: str,
        req: AdminUpdateTherapistVerificationRequest,
        request_id: str | None = None,
    ) -> TherapistDetailResponse:
        """Verify or reject therapist credentials using TherapistService."""
        self.require_permission(caller, Permission.THERAPISTS_VERIFY)
        res = await self.therapist_service.update_verification(
            therapist_id=therapist_id, admin_user=caller, req=req
        )
        await self.log_audit_event(
            actor=caller,
            action=AuditAction.THERAPIST_VERIFIED,
            resource_type="therapist",
            resource_id=therapist_id,
            metadata={"status": req.status.value, "rejection_reason": req.rejection_reason},
            request_id=request_id,
        )
        return res

    async def update_therapist_operational_status(
        self,
        caller: UserInDB,
        therapist_id: str,
        req: UpdateTherapistRequest,
        request_id: str | None = None,
    ) -> TherapistDetailResponse:
        """Update therapist status through TherapistService."""
        self.require_permission(caller, Permission.THERAPISTS_MANAGE)
        res = await self.therapist_service.update_therapist(
            therapist_id=therapist_id, caller=caller, req=req
        )
        await self.log_audit_event(
            actor=caller,
            action=AuditAction.THERAPIST_STATUS_UPDATED,
            resource_type="therapist",
            resource_id=therapist_id,
            metadata={"updates": req.model_dump(exclude_unset=True)},
            request_id=request_id,
        )
        return res

    async def onboard_therapist(
        self,
        caller: UserInDB,
        req: OnboardTherapistRequest,
        request_id: str | None = None,
    ) -> OnboardTherapistResponse:
        """Onboard a new practitioner with User account, Therapist profile, and optional schedule.

        Super Admin only. Guarantees atomic verification-status invariants, user credential creation,
        and append-only audit logging.
        """
        # 1. Access Control: Super Admin role or THERAPISTS_MANAGE permission required
        if UserRole.SUPER_ADMIN not in caller.roles and not self.has_permission(
            caller, Permission.THERAPISTS_MANAGE
        ):
            raise ForbiddenException(
                message="Only Super Admin can onboard and provision new therapists",
                code=ErrorCode.OPS_FORBIDDEN,
            )

        # 2. Invariant Validation: ACTIVE status requires VERIFIED credentials
        if (
            req.status == TherapistStatus.ACTIVE
            and req.verification.status != TherapistVerificationStatus.VERIFIED
        ):
            raise BadRequestException(
                message="Therapist cannot be activated without verified credentials",
                code=ErrorCode.THERAPIST_VERIFICATION_REQUIRED,
            )

        normalized_email = req.account.email.strip().lower()
        normalized_phone = req.account.phone.strip()

        # 3. Check for User collision before provisioning
        existing_email = await self.user_repo.get_by_email(normalized_email)
        if existing_email:
            raise BadRequestException(
                message=f"User with email '{normalized_email}' already exists",
                code=ErrorCode.USER_EMAIL_ALREADY_EXISTS,
            )

        existing_phone = await self.user_repo.get_by_phone(normalized_phone)
        if existing_phone:
            raise BadRequestException(
                message=f"User with phone '{normalized_phone}' already exists",
                code=ErrorCode.USER_PHONE_ALREADY_EXISTS,
            )

        # 4. Generate or hash password
        raw_password = req.account.temporary_password
        if not raw_password or not raw_password.strip():
            raw_password = secrets.token_urlsafe(12)
        password_hash = hash_password(raw_password)

        now = utc_now()
        user_id = str(uuid.uuid4())
        therapist_id = str(uuid.uuid4())

        user = UserInDB(
            id=user_id,
            first_name=req.account.first_name.strip(),
            last_name=req.account.last_name.strip(),
            email=normalized_email,
            phone=normalized_phone,
            password_hash=password_hash,
            roles=[UserRole.THERAPIST],
            status=UserStatus.ACTIVE,
            is_verified=True,
            auth_providers=[AuthProvider.PASSWORD],
            profile={
                "display_name": req.profile.display_name
                or f"{req.account.first_name.strip()} {req.account.last_name.strip()}",
                "onboarded_by": caller.id,
            },
            created_at=now,
            updated_at=now,
        )

        try:
            await self.user_repo.create(user)
        except DuplicateKeyError as exc:
            raise ConflictException(
                message="User account already exists with these credentials",
                code=ErrorCode.USER_ALREADY_EXISTS,
            ) from exc

        # 5. Build and persist Therapist Profile
        display_name = req.profile.display_name or f"{user.first_name} {user.last_name}"
        therapist = TherapistInDB(
            id=therapist_id,
            user_id=user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            display_name=display_name,
            bio=req.profile.bio,
            profile_image_url=req.profile.profile_image_url,
            introduction_audio_url=req.profile.introduction_audio_url,
            designation=req.profile.designation,
            specialization=req.profile.specialization,
            qualifications=req.profile.qualifications,
            experience_years=req.profile.experience_years,
            therapy_hours=req.profile.therapy_hours,
            languages=[lang.strip().lower() for lang in req.profile.languages if lang.strip()],
            expertises=[exp.strip().lower() for exp in req.profile.expertises if exp.strip()],
            session_modes=req.profile.session_modes,
            pricing=PricingModel(
                amount=req.pricing.amount,
                currency=req.pricing.currency,
                duration_minutes=req.pricing.duration_minutes,
            ),
            verification=VerificationModel(
                status=req.verification.status,
                verified_at=now if req.verification.status == TherapistVerificationStatus.VERIFIED else None,
                verified_by=caller.id if req.verification.status == TherapistVerificationStatus.VERIFIED else None,
                rejection_reason=req.verification.rejection_reason,
            ),
            status=req.status,
            metadata={
                "registration_number": req.verification.registration_number,
                "registration_authority": req.verification.registration_authority,
                "onboarded_by": caller.id,
            },
            created_at=now,
            updated_at=now,
        )

        try:
            await self.therapist_repo.create(therapist)
        except DuplicateKeyError as exc:
            # Clean up user if therapist profile uniqueness is violated
            await self.user_repo.collection.delete_one({"id": user_id})
            raise ConflictException(
                message="Therapist profile already exists for this user",
                code=ErrorCode.THERAPIST_ALREADY_EXISTS_FOR_USER,
            ) from exc

        # 6. Optional Initial Availability Schedule
        schedule_configured = False
        if req.availability and req.availability.days:
            try:
                schedule_req = SetWeeklyScheduleRequest(
                    timezone=req.availability.timezone,
                    days=req.availability.days,
                )
                await self.availability_service.set_weekly_schedule(
                    therapist_id=therapist_id,
                    caller=caller,
                    req=schedule_req,
                )
                schedule_configured = True
            except Exception:
                # Keep therapist profile intact even if schedule setup has a minor error
                schedule_configured = False

        # 7. Audit Logging
        await self.log_audit_event(
            actor=caller,
            action=AuditAction.THERAPIST_CREATED,
            resource_type="therapist",
            resource_id=therapist_id,
            metadata={
                "user_id": user_id,
                "email": normalized_email,
                "status": req.status.value,
                "verification_status": req.verification.status.value,
                "schedule_configured": schedule_configured,
            },
            request_id=request_id,
        )

        if req.verification.status == TherapistVerificationStatus.VERIFIED:
            await self.log_audit_event(
                actor=caller,
                action=AuditAction.THERAPIST_VERIFIED,
                resource_type="therapist",
                resource_id=therapist_id,
                metadata={"status": "verified", "initial_onboarding": True},
                request_id=request_id,
            )

        if req.status == TherapistStatus.ACTIVE:
            await self.log_audit_event(
                actor=caller,
                action=AuditAction.THERAPIST_ACTIVATED,
                resource_type="therapist",
                resource_id=therapist_id,
                metadata={"status": "active", "initial_onboarding": True},
                request_id=request_id,
            )

        return OnboardTherapistResponse(
            therapist=TherapistDetailResponse.from_therapist_db(therapist),
            user_id=user_id,
            email=normalized_email,
            phone=normalized_phone,
            temporary_password=raw_password,
            status=req.status,
            verification_status=req.verification.status,
            schedule_configured=schedule_configured,
        )

    # --- Booking & Payment Operations Visibility ---

    async def list_bookings_operational(
        self,
        caller: UserInDB,
        status: str | None = None,
        therapist_id: str | None = None,
        client_id: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[BookingInDB], int]:
        """Operational listing of all bookings across therapists."""
        self.require_permission(caller, Permission.BOOKINGS_READ)
        query: dict[str, Any] = {}
        if status:
            query["status"] = status
        if therapist_id:
            query["therapist_id"] = therapist_id
        if client_id:
            query["client_id"] = client_id

        total = await self.db["bookings"].count_documents(query)
        cursor = (
            self.db["bookings"]
            .find(query)
            .sort("start_at", -1)
            .skip((page - 1) * limit)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [BookingInDB(**d) for d in docs], total

    async def list_payments_operational(
        self,
        caller: UserInDB,
        status: str | None = None,
        provider: str | None = None,
        user_id: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[PaymentInDB], int]:
        """Operational visibility into all payments and failure codes."""
        self.require_permission(caller, Permission.PAYMENTS_READ)
        query: dict[str, Any] = {}
        if status:
            query["status"] = status
        if provider:
            query["provider"] = provider
        if user_id:
            query["user_id"] = user_id

        total = await self.db["payments"].count_documents(query)
        cursor = (
            self.db["payments"]
            .find(query)
            .sort("created_at", -1)
            .skip((page - 1) * limit)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [PaymentInDB(**d) for d in docs], total

    # --- First Responder & Lead Operations ---

    async def create_lead(
        self, caller: UserInDB, req: LeadCreateRequest, request_id: str | None = None
    ) -> LeadResponse:
        """Create a prospective lead."""
        self.require_permission(caller, Permission.LEADS_MANAGE)
        now = utc_now()
        lead = LeadInDB(
            id=str(uuid.uuid4()),
            name=req.name.strip(),
            phone=req.phone.strip(),
            email=req.email.strip() if req.email else None,
            source=req.source,
            status=LeadStatus.NEW,
            assigned_to=caller.id,  # Default creator assignment
            notes=req.notes,
            last_contacted_at=None,
            next_follow_up_at=req.next_follow_up_at,
            converted_user_id=None,
            created_at=now,
            updated_at=now,
        )
        saved = await self.ops_repo.create_lead(lead)
        await self.log_audit_event(
            actor=caller,
            action=AuditAction.LEAD_CREATED,
            resource_type="lead",
            resource_id=saved.id,
            metadata={"name": saved.name, "source": saved.source.value},
            request_id=request_id,
        )
        return LeadResponse.from_db(saved)

    async def list_leads(
        self,
        caller: UserInDB,
        status: LeadStatus | None = None,
        assigned_to: str | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[LeadResponse], int]:
        """List leads for first responders and staff."""
        self.require_permission(caller, Permission.LEADS_READ)
        leads, total = await self.ops_repo.list_leads(
            status=status, assigned_to=assigned_to, search=search, page=page, limit=limit
        )
        return [LeadResponse.from_db(lead_item) for lead_item in leads], total

    async def get_lead_by_id(self, caller: UserInDB, lead_id: str) -> LeadResponse:
        """Retrieve lead details."""
        self.require_permission(caller, Permission.LEADS_READ)
        lead = await self.ops_repo.get_lead_by_id(lead_id)
        if not lead:
            raise NotFoundException(
                message=f"Lead '{lead_id}' not found",
                code=ErrorCode.OPS_LEAD_NOT_FOUND,
            )
        return LeadResponse.from_db(lead)

    async def update_lead(
        self,
        caller: UserInDB,
        lead_id: str,
        req: LeadUpdateRequest,
        request_id: str | None = None,
    ) -> LeadResponse:
        """Update lead status or follow-up details."""
        self.require_permission(caller, Permission.LEADS_MANAGE)
        lead = await self.ops_repo.get_lead_by_id(lead_id)
        if not lead:
            raise NotFoundException(
                message=f"Lead '{lead_id}' not found",
                code=ErrorCode.OPS_LEAD_NOT_FOUND,
            )

        updates: dict[str, Any] = req.model_dump(exclude_unset=True)
        if (
            "status" in updates
            and updates["status"] != lead.status.value
            and updates["status"] == LeadStatus.CONTACTED.value
        ):
            updates["last_contacted_at"] = utc_now()

        updated = await self.ops_repo.update_lead(lead_id, updates)
        assert updated is not None

        await self.log_audit_event(
            actor=caller,
            action=AuditAction.LEAD_STATUS_UPDATED,
            resource_type="lead",
            resource_id=lead_id,
            metadata={"updates": updates},
            request_id=request_id,
        )
        return LeadResponse.from_db(updated)

    async def assign_lead(
        self,
        caller: UserInDB,
        lead_id: str,
        req: LeadAssignRequest,
        request_id: str | None = None,
    ) -> LeadResponse:
        """Assign or reassign a lead to a first responder or staff member."""
        self.require_permission(caller, Permission.LEADS_ASSIGN)
        lead = await self.ops_repo.get_lead_by_id(lead_id)
        if not lead:
            raise NotFoundException(
                message=f"Lead '{lead_id}' not found",
                code=ErrorCode.OPS_LEAD_NOT_FOUND,
            )

        # Verify assignee exists and has staff or first_responder role
        assignee = await self.user_repo.get_by_id(req.assigned_to)
        if not assignee:
            raise NotFoundException(
                message=f"Assignee user '{req.assigned_to}' not found",
                code=ErrorCode.USER_NOT_FOUND,
            )
        valid_roles = [UserRole.STAFF, UserRole.FIRST_RESPONDER, UserRole.ADMIN, UserRole.SUPER_ADMIN]
        if not any(r in assignee.roles for r in valid_roles):
            raise BadRequestException(
                message="Assignee must possess staff, first_responder, or admin role",
                code=ErrorCode.OPS_INVALID_OPERATION,
            )

        updates: dict[str, Any] = {"assigned_to": req.assigned_to}
        if req.notes:
            updates["notes"] = req.notes

        updated = await self.ops_repo.update_lead(lead_id, updates)
        assert updated is not None

        await self.log_audit_event(
            actor=caller,
            action=AuditAction.LEAD_ASSIGNED,
            resource_type="lead",
            resource_id=lead_id,
            metadata={
                "previous_assigned_to": lead.assigned_to,
                "new_assigned_to": req.assigned_to,
                "notes": req.notes,
            },
            request_id=request_id,
        )
        return LeadResponse.from_db(updated)

    async def convert_lead_to_user(
        self,
        caller: UserInDB,
        lead_id: str,
        user_id: str,
        request_id: str | None = None,
    ) -> LeadResponse:
        """Associate lead with an existing registered user upon conversion."""
        self.require_permission(caller, Permission.LEADS_MANAGE)
        lead = await self.ops_repo.get_lead_by_id(lead_id)
        if not lead:
            raise NotFoundException(
                message=f"Lead '{lead_id}' not found",
                code=ErrorCode.OPS_LEAD_NOT_FOUND,
            )

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(
                message=f"User '{user_id}' not found",
                code=ErrorCode.USER_NOT_FOUND,
            )

        updates: dict[str, Any] = {
            "status": LeadStatus.CONVERTED.value,
            "converted_user_id": user_id,
        }
        updated = await self.ops_repo.update_lead(lead_id, updates)
        assert updated is not None

        await self.log_audit_event(
            actor=caller,
            action=AuditAction.LEAD_CONVERTED,
            resource_type="lead",
            resource_id=lead_id,
            metadata={"converted_user_id": user_id},
            request_id=request_id,
        )
        return LeadResponse.from_db(updated)
