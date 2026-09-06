export type SessionStatus =
  "scheduled" | "ready" | "in_progress" | "completed" | "cancelled" | "no_show";

export type AttendanceStatus = "unknown" | "present" | "absent" | "late";

export type GoalStatus = "active" | "completed" | "archived";

export type MeetingStatus =
  "not_required" | "not_started" | "processing" | "ready" | "failed";

export interface SessionMeetingResponse {
  provider: string;
  status: MeetingStatus;
  join_url: string | null;
}

export interface SessionResponse {
  id: string;
  booking_id: string;
  therapist_id: string;
  client_id: string;
  scheduled_start_at: string;
  scheduled_end_at: string;
  duration_minutes: number;
  session_mode: string;
  status: SessionStatus;
  started_at: string | null;
  ended_at: string | null;
  attendance: AttendanceStatus;
  meeting?: SessionMeetingResponse | null;
  created_at: string;
  updated_at: string;
}

export interface ClientSessionResponse {
  id: string;
  booking_id: string;
  therapist_id: string;
  scheduled_start_at: string;
  scheduled_end_at: string;
  duration_minutes: number;
  session_mode: string;
  status: SessionStatus;
  started_at: string | null;
  ended_at: string | null;
  meeting?: SessionMeetingResponse | null;
}

export interface RecordAttendanceRequest {
  attendance: AttendanceStatus;
}

export interface UpsertSessionNoteRequest {
  summary: string;
  private_notes: string;
}

export interface SessionNoteResponse {
  id: string;
  session_id: string;
  therapist_id: string;
  client_id: string;
  summary: string;
  private_notes: string;
  created_at: string;
  updated_at: string;
}

export interface ClientSessionNoteResponse {
  session_id: string;
  summary: string;
  updated_at: string;
}

export interface CreateTherapyGoalRequest {
  title: string;
  description?: string;
}

export interface UpdateTherapyGoalRequest {
  title?: string;
  description?: string;
  status?: GoalStatus;
}

export interface TherapyGoalResponse {
  id: string;
  session_id: string | null;
  therapist_id: string;
  client_id: string;
  title: string;
  description: string;
  status: GoalStatus;
  created_at: string;
  updated_at: string;
}

export interface TherapistDashboardSummaryResponse {
  today_sessions_count: number;
  upcoming_sessions_count: number;
  completed_sessions_count: number;
  today_sessions: SessionResponse[];
}
