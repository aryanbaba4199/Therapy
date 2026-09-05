import type { SessionMode } from "../../therapist/types/therapist.types";

export type DayOfWeek = 0 | 1 | 2 | 3 | 4 | 5 | 6;

export interface TimeInterval {
  start_time: string;
  end_time: string;
  session_modes: SessionMode[];
}

export interface DaySchedule {
  day_of_week: DayOfWeek;
  intervals: TimeInterval[];
}

export interface WeeklySchedule {
  id: string;
  therapist_id: string;
  timezone: string;
  days: DaySchedule[];
  updated_at: string;
}

export interface SetWeeklySchedulePayload {
  timezone: string;
  days: DaySchedule[];
}

export interface DateException {
  id: string;
  therapist_id: string;
  date: string;
  is_unavailable: boolean;
  custom_intervals: TimeInterval[];
  reason: string | null;
  created_at: string;
}

export interface CreateDateExceptionPayload {
  date: string;
  is_unavailable: boolean;
  custom_intervals?: TimeInterval[];
  reason?: string | null;
}

export interface ExtraSlot {
  id: string;
  therapist_id: string;
  date: string;
  start_time: string;
  end_time: string;
  session_mode: SessionMode;
  status: "available" | "reserved" | "booked" | "blocked" | "expired";
}

export interface CreateExtraSlotPayload {
  date: string;
  start_time: string;
  end_time: string;
  session_mode: SessionMode;
}

export interface TherapistAvailabilityResponse {
  therapist_id: string;
  timezone: string;
  schedule: WeeklySchedule | null;
  exceptions: DateException[];
}
