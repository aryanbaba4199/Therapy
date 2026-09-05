import type { SessionMode } from "../../therapist/types/therapist.types";

export type SlotStatus =
  "available" | "reserved" | "booked" | "blocked" | "expired";

export interface GeneratedSlot {
  id: string;
  therapist_id: string;
  start_at: string; // ISO 8601 UTC string
  end_at: string; // ISO 8601 UTC string
  session_mode: SessionMode;
  status: SlotStatus;
}

export interface SlotDiscoveryParams {
  therapist_id: string;
  date?: string;
  start_date?: string;
  end_date?: string;
  session_mode?: SessionMode;
}

export type TimeOfDayGroup = "morning" | "afternoon" | "evening";

export interface GroupedSlots {
  morning: GeneratedSlot[];
  afternoon: GeneratedSlot[];
  evening: GeneratedSlot[];
}
