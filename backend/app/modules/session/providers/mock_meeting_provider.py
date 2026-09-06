"""Mock Meeting Provider for deterministic testing and local development."""

import hashlib

from app.modules.session.providers.meeting_provider import (
    MeetingCreationRequest,
    MeetingCreationResult,
    MeetingProvider,
)
from app.modules.session.session_constants import MeetingProviderType, MeetingStatus


class MockMeetingProvider(MeetingProvider):
    """Deterministic meeting provider that simulates Google Meet without network calls."""

    def __init__(self, should_fail: bool = False, is_pending: bool = False) -> None:
        self.should_fail = should_fail
        self.is_pending = is_pending
        self.call_count = 0

    @property
    def name(self) -> MeetingProviderType:
        return MeetingProviderType.MOCK

    async def create_meeting(self, req: MeetingCreationRequest) -> MeetingCreationResult:
        self.call_count += 1

        if self.should_fail:
            return MeetingCreationResult(
                provider=self.name,
                status=MeetingStatus.FAILED,
                error_message="Simulated mock meeting provider connection failure",
            )

        # Generate deterministic Google Meet code from session_id
        # Google meet code format: xxx-yyyy-zzz
        digest = hashlib.md5(req.session_id.encode("utf-8")).hexdigest()
        p1 = digest[:3]
        p2 = digest[3:7]
        p3 = digest[7:10]
        code = f"{p1}-{p2}-{p3}"

        provider_event_id = f"gcal_{digest[:16]}"
        join_url = f"https://meet.google.com/{code}"

        if self.is_pending:
            return MeetingCreationResult(
                provider=self.name,
                status=MeetingStatus.PROCESSING,
                provider_event_id=provider_event_id,
                conference_id=code,
                join_url=None,
            )

        return MeetingCreationResult(
            provider=self.name,
            status=MeetingStatus.READY,
            join_url=join_url,
            provider_event_id=provider_event_id,
            conference_id=code,
        )
