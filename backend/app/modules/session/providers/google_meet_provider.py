"""Google Meet / Calendar API Provider implementation."""

import asyncio
import logging
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build  # type: ignore[import-untyped]
from googleapiclient.errors import HttpError  # type: ignore[import-untyped]

from app.modules.session.providers.meeting_provider import (
    MeetingCreationRequest,
    MeetingCreationResult,
    MeetingProvider,
)
from app.modules.session.session_constants import MeetingProviderType, MeetingStatus

logger = logging.getLogger(__name__)

CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


class GoogleMeetProvider(MeetingProvider):
    """Production provider integrating with Google Calendar API to create Google Meet conferences."""

    def __init__(
        self,
        service_account_email: str | None = None,
        private_key: str | None = None,
        calendar_id: str = "primary",
        delegated_user: str | None = None,
    ) -> None:
        self.service_account_email = service_account_email
        self.private_key = private_key
        self.calendar_id = calendar_id
        self.delegated_user = delegated_user

    @property
    def name(self) -> MeetingProviderType:
        return MeetingProviderType.GOOGLE_MEET

    def _get_credentials(self) -> service_account.Credentials | None:
        """Construct Google service account credentials."""
        if not self.service_account_email or not self.private_key:
            return None

        # Format PEM private key if necessary (handling escaped newlines in env vars)
        formatted_key = self.private_key.replace("\\n", "\n")
        info = {
            "client_email": self.service_account_email,
            "private_key": formatted_key,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        creds = (
            service_account.Credentials.from_service_account_info(  # type: ignore[no-untyped-call]
                info, scopes=CALENDAR_SCOPES
            )
        )
        if self.delegated_user:
            creds = creds.with_subject(self.delegated_user)
        return creds  # type: ignore[no-any-return]

    def _sync_create_meeting(self, req: MeetingCreationRequest) -> MeetingCreationResult:
        """Synchronous Google Calendar execution run inside async executor."""
        creds = self._get_credentials()
        if not creds:
            logger.error("Google Calendar credentials are not configured")
            return MeetingCreationResult(
                provider=self.name,
                status=MeetingStatus.FAILED,
                error_message="Google Calendar credentials are not configured",
            )

        try:
            service = build("calendar", "v3", credentials=creds, cache_discovery=False)

            # Google Calendar accepts base32hex client-generated event ID (chars [a-v0-9])
            # Minimum length 5, max 1024. Use clean alphanumeric hex string:
            clean_uuid = req.session_id.replace("-", "").lower()
            deterministic_event_id = f"therapy{clean_uuid[:24]}"

            # Attendees without clinical notes or private info
            attendees_payload = [{"email": a.email, "displayName": a.name} for a in req.attendees]

            event_body: dict[str, Any] = {
                "id": deterministic_event_id,
                "summary": req.title,
                "description": "Oppam Therapy Consultation — Confirmed Online Video Session",
                "start": {
                    "dateTime": req.start_at.isoformat(),
                    "timeZone": req.timezone,
                },
                "end": {
                    "dateTime": req.end_at.isoformat(),
                    "timeZone": req.timezone,
                },
                "attendees": attendees_payload,
                "conferenceData": {
                    "createRequest": {
                        "requestId": req.session_id,
                        "conferenceSolutionKey": {
                            "type": "hangoutsMeet",
                        },
                    },
                },
            }

            created_event = (
                service.events()
                .insert(
                    calendarId=self.calendar_id,
                    body=event_body,
                    conferenceDataVersion=1,
                )
                .execute()
            )

            event_id = created_event.get("id")
            conf_data = created_event.get("conferenceData", {})
            conf_id = conf_data.get("conferenceId")
            entry_points = conf_data.get("entryPoints", [])

            join_url: str | None = None
            for ep in entry_points:
                if ep.get("entryPointType") == "video":
                    join_url = ep.get("uri")
                    break

            create_status = conf_data.get("createRequest", {}).get("status", {}).get("statusCode")

            if join_url:
                return MeetingCreationResult(
                    provider=self.name,
                    status=MeetingStatus.READY,
                    join_url=join_url,
                    provider_event_id=event_id,
                    conference_id=conf_id,
                )

            if create_status == "pending":
                return MeetingCreationResult(
                    provider=self.name,
                    status=MeetingStatus.PROCESSING,
                    provider_event_id=event_id,
                    conference_id=conf_id,
                )

            return MeetingCreationResult(
                provider=self.name,
                status=MeetingStatus.FAILED,
                provider_event_id=event_id,
                error_message="Conference was created but no video entryPoint was returned by Google",
            )

        except HttpError as http_err:
            logger.error("Google Calendar API HTTP error (%s): %s", http_err.status_code, http_err)
            return MeetingCreationResult(
                provider=self.name,
                status=MeetingStatus.FAILED,
                error_message=f"Google Calendar API error {http_err.status_code}: {http_err.reason}",
            )
        except Exception as exc:
            logger.exception("Unexpected error during Google Calendar event creation: %s", exc)
            return MeetingCreationResult(
                provider=self.name,
                status=MeetingStatus.FAILED,
                error_message=f"Unexpected error: {str(exc)}",
            )

    async def create_meeting(self, req: MeetingCreationRequest) -> MeetingCreationResult:
        """Non-blocking call offloading synchronous Google client to threadpool executor."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_create_meeting, req)
