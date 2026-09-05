"""Therapist domain enumerations and constants."""

from enum import StrEnum


class TherapistStatus(StrEnum):
    """Operational lifecycle status of a therapist profile."""

    DRAFT = "draft"
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class TherapistVerificationStatus(StrEnum):
    """Administrative credential verification status."""

    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class TherapistSpecialization(StrEnum):
    """Clinical and counseling specializations."""

    CONSULTANT_PSYCHOLOGIST = "consultant_psychologist"
    CLINICAL_PSYCHOLOGIST = "clinical_psychologist"
    SEXUAL_HEALTH_SPECIALIST = "sexual_health_specialist"
    PSYCHIATRIST = "psychiatrist"


class SessionMode(StrEnum):
    """Delivery modes for therapy consultations."""

    ONLINE = "online"
    OFFLINE_BANGALORE = "offline_bangalore"
    OFFLINE_KOZHIKODE = "offline_kozhikode"


class TherapistSortBy(StrEnum):
    """Whitelisted sorting criteria for discovery listings."""

    RELEVANCE = "relevance"
    EXPERIENCE_DESC = "experience_desc"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    THERAPY_HOURS_DESC = "therapy_hours_desc"


VALID_STATUS_TRANSITIONS: dict[TherapistStatus, set[TherapistStatus]] = {
    TherapistStatus.DRAFT: {TherapistStatus.PENDING_VERIFICATION, TherapistStatus.INACTIVE},
    TherapistStatus.PENDING_VERIFICATION: {
        TherapistStatus.ACTIVE,
        TherapistStatus.DRAFT,
        TherapistStatus.INACTIVE,
    },
    TherapistStatus.ACTIVE: {TherapistStatus.INACTIVE, TherapistStatus.SUSPENDED},
    TherapistStatus.INACTIVE: {TherapistStatus.ACTIVE, TherapistStatus.PENDING_VERIFICATION},
    TherapistStatus.SUSPENDED: {TherapistStatus.INACTIVE, TherapistStatus.ACTIVE},
}
