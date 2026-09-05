export type SupportCategory =
  | "booking"
  | "payment"
  | "therapist"
  | "session"
  | "package"
  | "account"
  | "technical"
  | "other";

export type SupportPriority = "low" | "normal" | "high" | "urgent";

export type SupportTicketStatus =
  "open" | "in_progress" | "waiting_for_user" | "resolved" | "closed";

export interface SupportAttachment {
  filename: string;
  file_url: string;
  mime_type: string;
  size_bytes: number;
}

export interface SupportTicketResponse {
  id: string;
  ticket_number: string;
  requester_id: string;
  requester_role: string;
  assigned_to: string | null;
  category: SupportCategory;
  priority: SupportPriority;
  status: SupportTicketStatus;
  subject: string;
  description: string;
  booking_id: string | null;
  payment_id: string | null;
  package_id: string | null;
  session_id: string | null;
  attachments: SupportAttachment[];
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  closed_at: string | null;
}

export interface SupportMessageResponse {
  id: string;
  ticket_id: string;
  sender_id: string;
  sender_role: string;
  sender_display_name: string;
  message: string;
  attachments: SupportAttachment[];
  is_internal_note: boolean;
  created_at: string;
  updated_at: string;
}

export interface SupportTicketDetailResponse {
  ticket: SupportTicketResponse;
  messages: SupportMessageResponse[];
}

export interface CreateSupportTicketRequest {
  category: SupportCategory;
  subject: string;
  description: string;
  priority?: SupportPriority;
  booking_id?: string;
  payment_id?: string;
  package_id?: string;
  session_id?: string;
  attachments?: SupportAttachment[];
}

export interface CreateSupportMessageRequest {
  message: string;
  attachments?: SupportAttachment[];
  is_internal_note?: boolean;
}
