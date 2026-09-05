import type { SessionMode } from "@/features/therapist/types/therapist.types";

export type BookingStatus =
  "pending" | "confirmed" | "cancelled" | "completed" | "no_show";

export type ReservationStatus =
  "active" | "converted" | "expired" | "cancelled";

export interface PricingSnapshot {
  amount: number;
  currency: string;
  duration_minutes: number;
}

export interface TherapistSnapshot {
  id: string;
  display_name: string;
  designation: string;
  specialization: string;
  profile_image_url?: string | null;
}

export interface ClientSnapshot {
  id: string;
  first_name: string;
  last_name: string;
  email?: string | null;
  phone?: string | null;
}

export interface Reservation {
  id: string;
  slot_id: string;
  therapist_id: string;
  client_id: string;
  session_mode: SessionMode;
  start_at: string;
  end_at: string;
  duration_minutes: number;
  status: ReservationStatus;
  expires_at: string;
  seconds_remaining: number;
  created_at: string;
}

export interface CreateReservationRequest {
  therapist_id: string;
  slot_id: string;
  slot_date: string;
  session_mode: SessionMode;
}

export interface ConfirmBookingRequest {
  reservation_id: string;
  client_notes?: string;
}

export interface CancelBookingRequest {
  reason?: string;
}

export interface BookingSummary {
  id: string;
  client_id: string;
  therapist_id: string;
  session_mode: SessionMode;
  start_at: string;
  end_at: string;
  duration_minutes: number;
  status: BookingStatus;
  pricing: PricingSnapshot;
  therapist: TherapistSnapshot;
  created_at: string;
}

export interface BookingDetail {
  id: string;
  client_id: string;
  therapist_id: string;
  slot_id: string;
  reservation_id: string;
  session_mode: SessionMode;
  start_at: string;
  end_at: string;
  duration_minutes: number;
  status: BookingStatus;
  pricing: PricingSnapshot;
  therapist: TherapistSnapshot;
  client: ClientSnapshot;
  notes?: string | null;
  cancellation_reason?: string | null;
  cancelled_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface BookingListQueryParams {
  page?: number;
  limit?: number;
  filter?: "upcoming" | "past" | "cancelled";
  status?: BookingStatus;
}

export interface PaginationInfo {
  page: number;
  limit: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface PaginatedBookings {
  items: BookingSummary[];
  pagination: PaginationInfo;
}
