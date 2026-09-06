import type { UserRole, UserStatus } from "@/features/user/types/user.types";

export type LeadStatus =
  "new" | "contacted" | "follow_up" | "converted" | "lost";
export type LeadSource =
  "website" | "helpline" | "referral" | "campaign" | "other";

export type AuditAction =
  | "user_status_updated"
  | "user_roles_updated"
  | "therapist_verified"
  | "therapist_status_updated"
  | "booking_status_updated"
  | "support_ticket_assigned"
  | "support_ticket_status_updated"
  | "support_ticket_escalated"
  | "lead_created"
  | "lead_assigned"
  | "lead_status_updated"
  | "lead_converted"
  | "review_moderated";

export interface AdminDashboardMetrics {
  today_bookings: number;
  upcoming_sessions: number;
  completed_sessions: number;
  active_therapists: number;
  pending_verification_therapists: number;
  pending_support_tickets: number;
  failed_payments_count: number;
  total_revenue_minor: number;
  new_leads_count: number;
}

export interface OperationUserDetail {
  id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  roles: UserRole[];
  status: UserStatus;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
}

export interface UpdateUserStatusRequest {
  status: UserStatus;
  reason: string;
}

export interface UpdateUserRolesRequest {
  roles: UserRole[];
  reason: string;
}

export interface Lead {
  id: string;
  name: string;
  phone: string;
  email: string | null;
  source: LeadSource;
  status: LeadStatus;
  assigned_to: string | null;
  notes: string | null;
  last_contacted_at: string | null;
  next_follow_up_at: string | null;
  converted_user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateLeadRequest {
  name: string;
  phone: string;
  email?: string;
  source?: LeadSource;
  notes?: string;
  next_follow_up_at?: string;
}

export interface UpdateLeadRequest {
  name?: string;
  phone?: string;
  email?: string;
  source?: LeadSource;
  status?: LeadStatus;
  notes?: string;
  next_follow_up_at?: string;
}

export interface AssignLeadRequest {
  assigned_to: string;
  notes?: string;
}

export interface AuditLog {
  id: string;
  actor_id: string;
  actor_role: string;
  action: AuditAction;
  resource_type: string;
  resource_id: string;
  metadata: Record<string, unknown>;
  request_id: string | null;
  created_at: string;
}

export interface BookingOperationalView {
  id: string;
  booking_number: string;
  client_id: string;
  therapist_id: string;
  session_mode: string;
  status: string;
  start_at: string;
  end_at: string;
  created_at: string;
}

export interface PaymentOperationalView {
  id: string;
  order_id: string;
  user_id: string;
  target_type: string;
  provider: string;
  status: string;
  final_amount_minor: number;
  currency: string;
  failure_code: string | null;
  failure_message: string | null;
  created_at: string;
}

// --- Therapist Onboarding Types ---

export interface OnboardTherapistAccountRequest {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  temporary_password?: string;
}

export interface OnboardTherapistProfileRequest {
  display_name?: string;
  bio: string;
  designation: string;
  specialization: string;
  qualifications: string[];
  experience_years: number;
  therapy_hours?: number;
  languages: string[];
  expertises: string[];
  session_modes: string[];
  profile_image_url?: string;
  introduction_audio_url?: string;
}

export interface OnboardTherapistPricingRequest {
  amount: number;
  currency?: string;
  duration_minutes?: number;
}

export interface OnboardTherapistVerificationRequest {
  status: string;
  registration_number?: string;
  registration_authority?: string;
  rejection_reason?: string;
}

export interface OnboardTherapistAvailabilityRequest {
  timezone: string;
  days: {
    day_of_week: number;
    intervals: {
      start_time: string;
      end_time: string;
      session_modes: string[];
    }[];
  }[];
}

export interface OnboardTherapistRequest {
  account: OnboardTherapistAccountRequest;
  profile: OnboardTherapistProfileRequest;
  pricing: OnboardTherapistPricingRequest;
  verification: OnboardTherapistVerificationRequest;
  availability?: OnboardTherapistAvailabilityRequest;
  status: string;
}

export interface OnboardTherapistResponse {
  therapist: {
    id: string;
    user_id: string;
    first_name: string;
    last_name: string;
    display_name: string;
    bio: string;
    designation: string;
    specialization: string;
    qualifications: string[];
    experience_years: number;
    therapy_hours: number;
    languages: string[];
    expertises: string[];
    session_modes: string[];
    pricing: {
      amount: number;
      currency: string;
      duration_minutes: number;
    };
    verification: {
      status: string;
      verified_at: string | null;
      rejection_reason: string | null;
    };
    status: string;
    created_at: string;
  };
  user_id: string;
  email: string;
  phone: string;
  temporary_password: string | null;
  status: string;
  verification_status: string;
  schedule_configured: boolean;
}
