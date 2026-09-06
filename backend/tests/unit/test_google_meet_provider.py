"""Unit tests for GoogleMeetProvider and MockMeetingProvider."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from googleapiclient.errors import HttpError  # type: ignore[import-untyped]
from httplib2 import Response  # type: ignore[import-untyped]

from app.modules.session.providers.google_meet_provider import GoogleMeetProvider
from app.modules.session.providers.meeting_provider import (
    MeetingAttendee,
    MeetingCreationRequest,
)
from app.modules.session.providers.mock_meeting_provider import MockMeetingProvider
from app.modules.session.session_constants import MeetingProviderType, MeetingStatus


@pytest.fixture
def sample_request() -> MeetingCreationRequest:
    now = datetime.now(UTC)
    return MeetingCreationRequest(
        session_id="123e4567-e89b-12d3-a456-426614174000",
        title="Therapy Session — Dr. Smith",
        start_at=now,
        end_at=now + timedelta(minutes=50),
        timezone="Asia/Kolkata",
        attendees=[
            MeetingAttendee(name="Dr. Smith", email="smith@example.com", role="therapist"),
            MeetingAttendee(name="Jane Doe", email="jane@example.com", role="client"),
        ],
    )


@pytest.mark.asyncio
async def test_mock_meeting_provider_deterministic(sample_request: MeetingCreationRequest) -> None:
    provider = MockMeetingProvider()
    assert provider.name == MeetingProviderType.MOCK

    result = await provider.create_meeting(sample_request)
    assert result.status == MeetingStatus.READY
    assert result.join_url is not None
    assert "https://meet.google.com/" in result.join_url
    assert result.conference_id is not None
    assert result.provider_event_id is not None
    assert provider.call_count == 1

    # Determinism: same session_id produces same URL
    result2 = await provider.create_meeting(sample_request)
    assert result2.join_url == result.join_url
    assert provider.call_count == 2


@pytest.mark.asyncio
async def test_mock_meeting_provider_simulated_failure(sample_request: MeetingCreationRequest) -> None:
    provider = MockMeetingProvider(should_fail=True)
    result = await provider.create_meeting(sample_request)
    assert result.status == MeetingStatus.FAILED
    assert result.join_url is None
    assert result.error_message is not None


@pytest.mark.asyncio
async def test_mock_meeting_provider_simulated_pending(sample_request: MeetingCreationRequest) -> None:
    provider = MockMeetingProvider(is_pending=True)
    result = await provider.create_meeting(sample_request)
    assert result.status == MeetingStatus.PROCESSING
    assert result.join_url is None


def test_google_meet_provider_missing_credentials(sample_request: MeetingCreationRequest) -> None:
    provider = GoogleMeetProvider()
    assert provider.name == MeetingProviderType.GOOGLE_MEET

    result = provider._sync_create_meeting(sample_request)
    assert result.status == MeetingStatus.FAILED
    assert "credentials are not configured" in (result.error_message or "")


@patch("app.modules.session.providers.google_meet_provider.build")
@pytest.mark.asyncio
async def test_google_meet_provider_success(mock_build: MagicMock, sample_request: MeetingCreationRequest) -> None:
    provider = GoogleMeetProvider(
        service_account_email="test@appspot.gserviceaccount.com",
        private_key="dummy-key\n",
        calendar_id="c_12345",
    )

    mock_service = MagicMock()
    mock_events = MagicMock()
    mock_insert = MagicMock()

    mock_insert.execute.return_value = {
        "id": "therapy123e4567e89b12d3a4564266",
        "conferenceData": {
            "conferenceId": "abc-defg-hij",
            "entryPoints": [
                {"entryPointType": "video", "uri": "https://meet.google.com/abc-defg-hij"}
            ],
            "createRequest": {"status": {"statusCode": "success"}},
        },
    }
    mock_events.insert.return_value = mock_insert
    mock_service.events.return_value = mock_events
    mock_build.return_value = mock_service

    with patch.object(provider, "_get_credentials", return_value=MagicMock()):
        result = await provider.create_meeting(sample_request)

    assert result.status == MeetingStatus.READY
    assert result.join_url == "https://meet.google.com/abc-defg-hij"
    assert result.conference_id == "abc-defg-hij"
    assert result.provider_event_id == "therapy123e4567e89b12d3a4564266"

    # Verify insert arguments
    mock_events.insert.assert_called_once()
    kwargs = mock_events.insert.call_args.kwargs
    assert kwargs["calendarId"] == "c_12345"
    assert kwargs["conferenceDataVersion"] == 1
    body = kwargs["body"]
    assert body["id"] == "therapy123e4567e89b12d3a4564266"
    assert body["conferenceData"]["createRequest"]["conferenceSolutionKey"]["type"] == "hangoutsMeet"
    assert len(body["attendees"]) == 2


@patch("app.modules.session.providers.google_meet_provider.build")
@pytest.mark.asyncio
async def test_google_meet_provider_http_error(mock_build: MagicMock, sample_request: MeetingCreationRequest) -> None:
    provider = GoogleMeetProvider(
        service_account_email="test@appspot.gserviceaccount.com",
        private_key="dummy-key",
    )

    mock_service = MagicMock()
    mock_events = MagicMock()
    mock_insert = MagicMock()

    resp = Response({"status": "403", "reason": "Forbidden"})
    mock_insert.execute.side_effect = HttpError(resp=resp, content=b'{"error": "Forbidden"}')
    mock_events.insert.return_value = mock_insert
    mock_service.events.return_value = mock_events
    mock_build.return_value = mock_service

    with patch.object(provider, "_get_credentials", return_value=MagicMock()):
        result = await provider.create_meeting(sample_request)

    assert result.status == MeetingStatus.FAILED
    assert result.join_url is None
    assert "403" in (result.error_message or "")
