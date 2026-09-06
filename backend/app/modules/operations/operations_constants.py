"""Operations, Admin, and First Responder domain constants and permissions."""

from enum import StrEnum


class Permission(StrEnum):
    """Granular operational permissions."""

    # Dashboard
    DASHBOARD_VIEW = "dashboard:view"

    # Users
    USERS_READ = "users:read"
    USERS_UPDATE = "users:update"
    USERS_SUSPEND = "users:suspend"
    ROLES_MANAGE = "roles:manage"

    # Therapists
    THERAPISTS_READ = "therapists:read"
    THERAPISTS_VERIFY = "therapists:verify"
    THERAPISTS_MANAGE = "therapists:manage"

    # Bookings & Sessions
    BOOKINGS_READ = "bookings:read"
    BOOKINGS_MANAGE = "bookings:manage"
    SESSIONS_READ = "sessions:read"

    # Payments & Commercial
    PAYMENTS_READ = "payments:read"
    OFFERS_MANAGE = "offers:manage"
    PACKAGES_MANAGE = "packages:manage"

    # Customer Support
    SUPPORT_READ = "support:read"
    SUPPORT_ASSIGN = "support:assign"
    SUPPORT_RESOLVE = "support:resolve"
    SUPPORT_ESCALATE = "support:escalate"

    # Leads & First Responder
    LEADS_READ = "leads:read"
    LEADS_MANAGE = "leads:manage"
    LEADS_ASSIGN = "leads:assign"

    # Moderation & Content
    REVIEWS_MODERATE = "reviews:moderate"

    # Audit & Compliance
    AUDIT_READ = "audit:read"


class LeadStatus(StrEnum):
    """Lifecycle status of a prospective client lead."""

    NEW = "new"
    CONTACTED = "contacted"
    FOLLOW_UP = "follow_up"
    CONVERTED = "converted"
    LOST = "lost"


class LeadSource(StrEnum):
    """Acquisition source of a prospective client lead."""

    WEBSITE = "website"
    HELPLINE = "helpline"
    REFERRAL = "referral"
    CAMPAIGN = "campaign"
    OTHER = "other"


class AuditAction(StrEnum):
    """Categorization of audited operational actions."""

    USER_STATUS_UPDATED = "user_status_updated"
    USER_ROLES_UPDATED = "user_roles_updated"
    THERAPIST_CREATED = "therapist_created"
    THERAPIST_VERIFIED = "therapist_verified"
    THERAPIST_STATUS_UPDATED = "therapist_status_updated"
    THERAPIST_ACTIVATED = "therapist_activated"
    BOOKING_STATUS_UPDATED = "booking_status_updated"
    SUPPORT_TICKET_ASSIGNED = "support_ticket_assigned"
    SUPPORT_TICKET_STATUS_UPDATED = "support_ticket_status_updated"
    SUPPORT_TICKET_ESCALATED = "support_ticket_escalated"
    LEAD_CREATED = "lead_created"
    LEAD_ASSIGNED = "lead_assigned"
    LEAD_STATUS_UPDATED = "lead_status_updated"
    LEAD_CONVERTED = "lead_converted"
    REVIEW_MODERATED = "review_moderated"


# Default Role-to-Permissions Mapping
ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    "super_admin": set(Permission),  # All permissions
    "admin": {
        Permission.DASHBOARD_VIEW,
        Permission.USERS_READ,
        Permission.USERS_UPDATE,
        Permission.USERS_SUSPEND,
        Permission.THERAPISTS_READ,
        Permission.THERAPISTS_VERIFY,
        Permission.THERAPISTS_MANAGE,
        Permission.BOOKINGS_READ,
        Permission.BOOKINGS_MANAGE,
        Permission.SESSIONS_READ,
        Permission.PAYMENTS_READ,
        Permission.OFFERS_MANAGE,
        Permission.PACKAGES_MANAGE,
        Permission.SUPPORT_READ,
        Permission.SUPPORT_ASSIGN,
        Permission.SUPPORT_RESOLVE,
        Permission.SUPPORT_ESCALATE,
        Permission.LEADS_READ,
        Permission.LEADS_MANAGE,
        Permission.LEADS_ASSIGN,
        Permission.REVIEWS_MODERATE,
        Permission.AUDIT_READ,
    },
    "staff": {
        Permission.DASHBOARD_VIEW,
        Permission.USERS_READ,
        Permission.THERAPISTS_READ,
        Permission.BOOKINGS_READ,
        Permission.PAYMENTS_READ,
        Permission.SUPPORT_READ,
        Permission.SUPPORT_ASSIGN,
        Permission.SUPPORT_RESOLVE,
        Permission.LEADS_READ,
        Permission.LEADS_MANAGE,
        Permission.REVIEWS_MODERATE,
    },
    "first_responder": {
        Permission.DASHBOARD_VIEW,
        Permission.USERS_READ,
        Permission.THERAPISTS_READ,
        Permission.SUPPORT_READ,
        Permission.SUPPORT_ASSIGN,
        Permission.SUPPORT_ESCALATE,
        Permission.LEADS_READ,
        Permission.LEADS_MANAGE,
        Permission.LEADS_ASSIGN,
    },
    "therapist": set(),
    "user": set(),
}
