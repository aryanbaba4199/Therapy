"""Therapist entity factory for deterministic test data."""

import uuid
from typing import Any

from app.common.utils.datetime_utils import utc_now
from app.modules.therapist.therapist_constants import (
    SessionMode,
    TherapistSpecialization,
    TherapistStatus,
    TherapistVerificationStatus,
)
from app.modules.therapist.therapist_model import (
    PricingModel,
    TherapistInDB,
    VerificationModel,
)


class TherapistFactory:
    @staticmethod
    def build(
        *,
        id: str | None = None,
        user_id: str | None = None,
        first_name: str = "Dr. Anita",
        last_name: str = "Menon",
        display_name: str = "Dr. Anita Menon",
        bio: str = "Experienced psychotherapist specializing in anxiety and trauma.",
        designation: str = "Senior Clinical Psychologist",
        specialization: TherapistSpecialization = TherapistSpecialization.CLINICAL_PSYCHOLOGIST,
        qualifications: list[str] | None = None,
        experience_years: int = 8,
        therapy_hours: int = 1500,
        languages: list[str] | None = None,
        expertises: list[str] | None = None,
        session_modes: list[SessionMode] | None = None,
        pricing: PricingModel | None = None,
        status: TherapistStatus = TherapistStatus.ACTIVE,
        verification_status: TherapistVerificationStatus = TherapistVerificationStatus.VERIFIED,
    ) -> TherapistInDB:
        t_id = id or str(uuid.uuid4())
        u_id = user_id or str(uuid.uuid4())
        now = utc_now()

        return TherapistInDB(
            id=t_id,
            user_id=u_id,
            first_name=first_name,
            last_name=last_name,
            display_name=display_name,
            bio=bio,
            designation=designation,
            specialization=specialization,
            qualifications=qualifications or ["M.Phil Clinical Psychology", "Ph.D"],
            experience_years=experience_years,
            therapy_hours=therapy_hours,
            languages=languages or ["en", "ml"],
            expertises=expertises or ["anxiety", "depression"],
            session_modes=session_modes or [SessionMode.ONLINE],
            pricing=pricing or PricingModel(amount=1500, currency="INR", duration_minutes=60),
            status=status,
            verification=VerificationModel(
                status=verification_status,
                verified_at=now if verification_status == TherapistVerificationStatus.VERIFIED else None,
            ),
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    async def create(mock_db: Any, **kwargs: Any) -> TherapistInDB:
        therapist = TherapistFactory.build(**kwargs)
        await mock_db["therapists"].insert_one(therapist.model_dump(mode="json"))
        return therapist
