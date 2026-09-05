"""Deterministic slot generation engine."""

import hashlib
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.modules.availability.availability_constants import (
    DEFAULT_BUFFER_MINUTES,
    DEFAULT_TIMEZONE,
    SlotStatus,
)
from app.modules.availability.availability_model import (
    DateExceptionInDB,
    DayInterval,
    ExtraSlotInDB,
)
from app.modules.availability.availability_schema import GeneratedSlotResponse
from app.modules.therapist.therapist_constants import SessionMode


def generate_slot_id(
    therapist_id: str,
    start_at_utc: datetime,
    end_at_utc: datetime,
    session_mode: SessionMode,
) -> str:
    """Derive a stable, deterministic 24-character hexadecimal slot identifier."""
    raw = f"{therapist_id}:{start_at_utc.isoformat()}:{end_at_utc.isoformat()}:{session_mode.value}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def parse_time_string(time_str: str) -> time:
    """Parse 'HH:MM' string into a datetime.time object."""
    hours, minutes = map(int, time_str.split(":"))
    return time(hour=hours, minute=minutes)


def generate_slots_for_date(
    therapist_id: str,
    target_date: date,
    weekly_intervals: list[DayInterval],
    date_exception: DateExceptionInDB | None,
    extra_slots: list[ExtraSlotInDB],
    duration_minutes: int,
    buffer_minutes: int = DEFAULT_BUFFER_MINUTES,
    session_mode: SessionMode | None = None,
    therapist_timezone: str = DEFAULT_TIMEZONE,
    current_utc_time: datetime | None = None,
) -> list[GeneratedSlotResponse]:
    """Pure domain function generating available consultation slots for a specific date.

    Precedence:
    1. Base schedule is determined:
       - If date_exception exists and is_unavailable is True -> 0 base intervals.
       - If date_exception exists and is_unavailable is False -> custom_intervals override weekly_intervals.
       - Else -> weekly_intervals.
    2. Base intervals are chunked into slots matching duration_minutes (+ buffer_minutes).
    3. Extra slots for this date are converted into slots (extra slots take effect even on custom/unavailable dates).
    4. Slots in the past relative to current_utc_time are excluded.
    5. Deduplication and chronological sorting are applied.
    """
    if current_utc_time is None:
        current_utc_time = datetime.now(UTC)
    elif current_utc_time.tzinfo is None:
        current_utc_time = current_utc_time.replace(tzinfo=UTC)

    tz = ZoneInfo(therapist_timezone)

    # 1. Determine active base intervals
    if date_exception is not None:
        if date_exception.is_unavailable:
            active_intervals: list[DayInterval] = []
        else:
            active_intervals = date_exception.custom_intervals
    else:
        active_intervals = weekly_intervals

    slots_map: dict[tuple[datetime, datetime, SessionMode], GeneratedSlotResponse] = {}

    # 2. Process base intervals
    for interval in active_intervals:
        modes_to_generate = (
            [session_mode]
            if session_mode and session_mode in interval.session_modes
            else [m for m in interval.session_modes if session_mode is None or m == session_mode]
        )
        if not modes_to_generate:
            continue

        start_t = parse_time_string(interval.start_time)
        end_t = parse_time_string(interval.end_time)

        interval_start_dt = datetime.combine(target_date, start_t, tzinfo=tz)
        interval_end_dt = datetime.combine(target_date, end_t, tzinfo=tz)

        step_delta = timedelta(minutes=duration_minutes + buffer_minutes)
        slot_duration = timedelta(minutes=duration_minutes)

        curr_start = interval_start_dt
        while curr_start + slot_duration <= interval_end_dt:
            curr_end = curr_start + slot_duration

            # Convert to UTC
            start_utc = curr_start.astimezone(UTC)
            end_utc = curr_end.astimezone(UTC)

            # Exclude past slots
            if start_utc > current_utc_time:
                for mode in modes_to_generate:
                    key = (start_utc, end_utc, mode)
                    if key not in slots_map:
                        slot_id = generate_slot_id(therapist_id, start_utc, end_utc, mode)
                        slots_map[key] = GeneratedSlotResponse(
                            id=slot_id,
                            therapist_id=therapist_id,
                            start_at=start_utc,
                            end_at=end_utc,
                            session_mode=mode,
                            status=SlotStatus.AVAILABLE,
                        )

            curr_start += step_delta

    # 3. Process extra slots
    for extra in extra_slots:
        if session_mode is not None and extra.session_mode != session_mode:
            continue
        if extra.status != SlotStatus.AVAILABLE:
            continue

        extra_start_t = parse_time_string(extra.start_time)
        extra_end_t = parse_time_string(extra.end_time)

        extra_start_dt = datetime.combine(target_date, extra_start_t, tzinfo=tz)
        extra_end_dt = datetime.combine(target_date, extra_end_t, tzinfo=tz)

        start_utc = extra_start_dt.astimezone(UTC)
        end_utc = extra_end_dt.astimezone(UTC)

        if start_utc > current_utc_time:
            key = (start_utc, end_utc, extra.session_mode)
            if key not in slots_map:
                slot_id = generate_slot_id(therapist_id, start_utc, end_utc, extra.session_mode)
                slots_map[key] = GeneratedSlotResponse(
                    id=slot_id,
                    therapist_id=therapist_id,
                    start_at=start_utc,
                    end_at=end_utc,
                    session_mode=extra.session_mode,
                    status=SlotStatus.AVAILABLE,
                )

    # 4. Sort deterministically
    sorted_slots = sorted(
        slots_map.values(),
        key=lambda s: (s.start_at, s.session_mode.value),
    )

    return sorted_slots
