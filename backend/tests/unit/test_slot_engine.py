"""Unit tests for the deterministic Slot Engine."""

from datetime import UTC, date, datetime

import pytest

from app.modules.availability.availability_constants import SlotStatus
from app.modules.availability.availability_model import (
    DateExceptionInDB,
    DayInterval,
    ExtraSlotInDB,
)
from app.modules.availability.slot_engine import (
    generate_slot_id,
    generate_slots_for_date,
)
from app.modules.therapist.therapist_constants import SessionMode


def test_basic_schedule_deterministic_slots() -> None:
    """09:00 to 17:00 with 60-minute duration produces 8 deterministic slots."""
    therapist_id = "th-test-1"
    target_date = date(2026, 10, 5)  # Monday
    weekly_intervals = [
        DayInterval(
            start_time="09:00",
            end_time="17:00",
            session_modes=[SessionMode.ONLINE],
        )
    ]
    # Current time in past relative to target_date
    current_utc_time = datetime(2026, 10, 1, 0, 0, tzinfo=UTC)

    slots = generate_slots_for_date(
        therapist_id=therapist_id,
        target_date=target_date,
        weekly_intervals=weekly_intervals,
        date_exception=None,
        extra_slots=[],
        duration_minutes=60,
        therapist_timezone="Asia/Kolkata",
        current_utc_time=current_utc_time,
    )

    assert len(slots) == 8
    # Asia/Kolkata is UTC+5:30.
    # 09:00 IST = 03:30 UTC. 17:00 IST = 11:30 UTC.
    first_slot = slots[0]
    assert first_slot.start_at == datetime(2026, 10, 5, 3, 30, tzinfo=UTC)
    assert first_slot.end_at == datetime(2026, 10, 5, 4, 30, tzinfo=UTC)
    assert first_slot.session_mode == SessionMode.ONLINE
    assert first_slot.status == SlotStatus.AVAILABLE

    last_slot = slots[-1]
    assert last_slot.start_at == datetime(2026, 10, 5, 10, 30, tzinfo=UTC)
    assert last_slot.end_at == datetime(2026, 10, 5, 11, 30, tzinfo=UTC)


def test_multiple_intervals_on_same_day() -> None:
    """09:00 to 12:00 and 14:00 to 18:00 produce 3 + 4 = 7 slots."""
    therapist_id = "th-test-1"
    target_date = date(2026, 10, 5)
    weekly_intervals = [
        DayInterval(start_time="09:00", end_time="12:00", session_modes=[SessionMode.ONLINE]),
        DayInterval(start_time="14:00", end_time="18:00", session_modes=[SessionMode.ONLINE]),
    ]
    current_utc_time = datetime(2026, 10, 1, 0, 0, tzinfo=UTC)

    slots = generate_slots_for_date(
        therapist_id=therapist_id,
        target_date=target_date,
        weekly_intervals=weekly_intervals,
        date_exception=None,
        extra_slots=[],
        duration_minutes=60,
        therapist_timezone="Asia/Kolkata",
        current_utc_time=current_utc_time,
    )

    assert len(slots) == 7
    # 12:00 to 14:00 lunch break has no slots
    slot_starts_utc = [s.start_at.hour * 60 + s.start_at.minute for s in slots]
    # 09:00 IST = 03:30 UTC (210 min), 10:00 IST = 04:30 (270 min), 11:00 IST = 05:30 (330 min)
    # 14:00 IST = 08:30 UTC (510 min)
    assert 210 in slot_starts_utc
    assert 270 in slot_starts_utc
    assert 330 in slot_starts_utc
    assert 510 in slot_starts_utc
    # 12:00 IST = 06:30 UTC (390 min) should NOT exist
    assert 390 not in slot_starts_utc


@pytest.mark.parametrize(
    "duration,expected_count",
    [
        (20, 6),  # 2 hours (120 mins) / 20 = 6 slots
        (45, 2),  # 120 mins / 45 = 2 slots (remainder 30 discarded)
        (50, 2),  # 120 mins / 50 = 2 slots (remainder 20 discarded)
        (60, 2),  # 120 mins / 60 = 2 slots
    ],
)
def test_different_durations(duration: int, expected_count: int) -> None:
    """Check durations 20, 45, 50, 60 minutes across a 2-hour window (10:00 to 12:00)."""
    slots = generate_slots_for_date(
        therapist_id="th-1",
        target_date=date(2026, 10, 5),
        weekly_intervals=[DayInterval(start_time="10:00", end_time="12:00", session_modes=[SessionMode.ONLINE])],
        date_exception=None,
        extra_slots=[],
        duration_minutes=duration,
        therapist_timezone="Asia/Kolkata",
        current_utc_time=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
    )
    assert len(slots) == expected_count


def test_exact_boundary_vs_insufficient_duration() -> None:
    """09:00 to 10:00 gives 1 slot for 60m; 09:00 to 09:30 gives 0 slots for 60m."""
    slots_exact = generate_slots_for_date(
        therapist_id="th-1",
        target_date=date(2026, 10, 5),
        weekly_intervals=[DayInterval(start_time="09:00", end_time="10:00", session_modes=[SessionMode.ONLINE])],
        date_exception=None,
        extra_slots=[],
        duration_minutes=60,
        therapist_timezone="Asia/Kolkata",
        current_utc_time=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
    )
    assert len(slots_exact) == 1

    slots_insufficient = generate_slots_for_date(
        therapist_id="th-1",
        target_date=date(2026, 10, 5),
        weekly_intervals=[DayInterval(start_time="09:00", end_time="09:30", session_modes=[SessionMode.ONLINE])],
        date_exception=None,
        extra_slots=[],
        duration_minutes=60,
        therapist_timezone="Asia/Kolkata",
        current_utc_time=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
    )
    assert len(slots_insufficient) == 0


def test_buffer_time_support() -> None:
    """09:00 to 11:30 with 60-min session and 15-min buffer gives slots at 09:00-10:00 and 10:15-11:15."""
    slots = generate_slots_for_date(
        therapist_id="th-1",
        target_date=date(2026, 10, 5),
        weekly_intervals=[DayInterval(start_time="09:00", end_time="11:30", session_modes=[SessionMode.ONLINE])],
        date_exception=None,
        extra_slots=[],
        duration_minutes=60,
        buffer_minutes=15,
        therapist_timezone="Asia/Kolkata",
        current_utc_time=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
    )
    assert len(slots) == 2
    # First slot: 09:00 IST = 03:30 UTC
    assert slots[0].start_at == datetime(2026, 10, 5, 3, 30, tzinfo=UTC)
    assert slots[0].end_at == datetime(2026, 10, 5, 4, 30, tzinfo=UTC)
    # Second slot: 10:15 IST = 04:45 UTC
    assert slots[1].start_at == datetime(2026, 10, 5, 4, 45, tzinfo=UTC)
    assert slots[1].end_at == datetime(2026, 10, 5, 5, 45, tzinfo=UTC)


def test_past_slots_exclusion() -> None:
    """Slots that already started relative to current_utc_time are excluded."""
    # Target date: Oct 5, 2026
    # 09:00 IST = 03:30 UTC, 10:00 IST = 04:30 UTC, 11:00 IST = 05:30 UTC
    # Set current UTC time to 04:00 UTC (09:30 IST)
    # 09:00 IST slot has already started, so it should be excluded!
    current_utc = datetime(2026, 10, 5, 4, 0, tzinfo=UTC)

    slots = generate_slots_for_date(
        therapist_id="th-1",
        target_date=date(2026, 10, 5),
        weekly_intervals=[DayInterval(start_time="09:00", end_time="12:00", session_modes=[SessionMode.ONLINE])],
        date_exception=None,
        extra_slots=[],
        duration_minutes=60,
        therapist_timezone="Asia/Kolkata",
        current_utc_time=current_utc,
    )

    # Out of 09:00, 10:00, 11:00, only 10:00 and 11:00 are in future
    assert len(slots) == 2
    assert slots[0].start_at == datetime(2026, 10, 5, 4, 30, tzinfo=UTC)
    assert slots[1].start_at == datetime(2026, 10, 5, 5, 30, tzinfo=UTC)


def test_date_exception_unavailable_holiday() -> None:
    """Date marked as unavailable in date_exception produces zero regular slots."""
    exception = DateExceptionInDB(
        id="ex-1",
        therapist_id="th-1",
        date="2026-10-05",
        is_unavailable=True,
        custom_intervals=[],
        reason="Diwali Holiday",
    )

    slots = generate_slots_for_date(
        therapist_id="th-1",
        target_date=date(2026, 10, 5),
        weekly_intervals=[DayInterval(start_time="09:00", end_time="17:00", session_modes=[SessionMode.ONLINE])],
        date_exception=exception,
        extra_slots=[],
        duration_minutes=60,
        therapist_timezone="Asia/Kolkata",
        current_utc_time=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
    )

    assert len(slots) == 0


def test_date_exception_custom_override() -> None:
    """Date exception with custom intervals replaces weekly schedule."""
    exception = DateExceptionInDB(
        id="ex-2",
        therapist_id="th-1",
        date="2026-10-05",
        is_unavailable=False,
        custom_intervals=[
            DayInterval(start_time="18:00", end_time="20:00", session_modes=[SessionMode.ONLINE])
        ],
        reason="Evening emergency clinic",
    )

    slots = generate_slots_for_date(
        therapist_id="th-1",
        target_date=date(2026, 10, 5),
        weekly_intervals=[DayInterval(start_time="09:00", end_time="17:00", session_modes=[SessionMode.ONLINE])],
        date_exception=exception,
        extra_slots=[],
        duration_minutes=60,
        therapist_timezone="Asia/Kolkata",
        current_utc_time=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
    )

    assert len(slots) == 2
    # 18:00 IST = 12:30 UTC
    assert slots[0].start_at == datetime(2026, 10, 5, 12, 30, tzinfo=UTC)
    assert slots[1].start_at == datetime(2026, 10, 5, 13, 30, tzinfo=UTC)


def test_extra_slots_merged_and_prioritized() -> None:
    """Extra slots are merged even if the day is otherwise marked unavailable."""
    exception = DateExceptionInDB(
        id="ex-1",
        therapist_id="th-1",
        date="2026-10-05",
        is_unavailable=True,
        custom_intervals=[],
        reason="Holiday",
    )
    extra_slot = ExtraSlotInDB(
        id="extra-1",
        therapist_id="th-1",
        date="2026-10-05",
        start_time="20:00",
        end_time="21:00",
        session_mode=SessionMode.ONLINE,
        status=SlotStatus.AVAILABLE,
    )

    slots = generate_slots_for_date(
        therapist_id="th-1",
        target_date=date(2026, 10, 5),
        weekly_intervals=[DayInterval(start_time="09:00", end_time="17:00", session_modes=[SessionMode.ONLINE])],
        date_exception=exception,
        extra_slots=[extra_slot],
        duration_minutes=60,
        therapist_timezone="Asia/Kolkata",
        current_utc_time=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
    )

    assert len(slots) == 1
    # 20:00 IST = 14:30 UTC
    assert slots[0].start_at == datetime(2026, 10, 5, 14, 30, tzinfo=UTC)
    assert slots[0].end_at == datetime(2026, 10, 5, 15, 30, tzinfo=UTC)


def test_mode_specific_filtering() -> None:
    """Session mode filtering returns only slots matching the requested mode."""
    weekly_intervals = [
        DayInterval(
            start_time="09:00",
            end_time="11:00",
            session_modes=[SessionMode.ONLINE, SessionMode.OFFLINE_BANGALORE],
        )
    ]

    slots_online = generate_slots_for_date(
        therapist_id="th-1",
        target_date=date(2026, 10, 5),
        weekly_intervals=weekly_intervals,
        date_exception=None,
        extra_slots=[],
        duration_minutes=60,
        session_mode=SessionMode.ONLINE,
        therapist_timezone="Asia/Kolkata",
        current_utc_time=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
    )
    assert len(slots_online) == 2
    assert all(s.session_mode == SessionMode.ONLINE for s in slots_online)

    slots_bangalore = generate_slots_for_date(
        therapist_id="th-1",
        target_date=date(2026, 10, 5),
        weekly_intervals=weekly_intervals,
        date_exception=None,
        extra_slots=[],
        duration_minutes=60,
        session_mode=SessionMode.OFFLINE_BANGALORE,
        therapist_timezone="Asia/Kolkata",
        current_utc_time=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
    )
    assert len(slots_bangalore) == 2
    assert all(s.session_mode == SessionMode.OFFLINE_BANGALORE for s in slots_bangalore)

    slots_kozhikode = generate_slots_for_date(
        therapist_id="th-1",
        target_date=date(2026, 10, 5),
        weekly_intervals=weekly_intervals,
        date_exception=None,
        extra_slots=[],
        duration_minutes=60,
        session_mode=SessionMode.OFFLINE_KOZHIKODE,
        therapist_timezone="Asia/Kolkata",
        current_utc_time=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
    )
    assert len(slots_kozhikode) == 0


def test_timezone_conversion_and_stability() -> None:
    """Verify slots with London timezone (BST/GMT transition awareness)."""
    # 2026-07-01 is during British Summer Time (BST = UTC+1)
    slots = generate_slots_for_date(
        therapist_id="th-lon",
        target_date=date(2026, 7, 1),
        weekly_intervals=[DayInterval(start_time="09:00", end_time="10:00", session_modes=[SessionMode.ONLINE])],
        date_exception=None,
        extra_slots=[],
        duration_minutes=60,
        therapist_timezone="Europe/London",
        current_utc_time=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
    )
    assert len(slots) == 1
    # 09:00 BST = 08:00 UTC
    assert slots[0].start_at == datetime(2026, 7, 1, 8, 0, tzinfo=UTC)

    # Check deterministic slot ID stability
    slot_id_1 = generate_slot_id(
        "th-lon",
        slots[0].start_at,
        slots[0].end_at,
        SessionMode.ONLINE,
    )
    slot_id_2 = generate_slot_id(
        "th-lon",
        slots[0].start_at,
        slots[0].end_at,
        SessionMode.ONLINE,
    )
    assert slot_id_1 == slot_id_2
    assert len(slot_id_1) == 24
