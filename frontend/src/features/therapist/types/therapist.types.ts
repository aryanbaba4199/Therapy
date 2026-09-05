export type TherapistStatus =
  "draft" | "pending_verification" | "active" | "inactive" | "suspended";

export type TherapistVerificationStatus = "pending" | "verified" | "rejected";

export type TherapistSpecialization =
  | "consultant_psychologist"
  | "clinical_psychologist"
  | "sexual_health_specialist"
  | "psychiatrist";

export type SessionMode = "online" | "offline_bangalore" | "offline_kozhikode";

export type TherapistSortBy =
  | "relevance"
  | "experience_desc"
  | "price_asc"
  | "price_desc"
  | "therapy_hours_desc";

export interface TherapistPricing {
  amount: number;
  currency: string;
  duration_minutes: number;
}

export interface TherapistVerification {
  status: TherapistVerificationStatus;
  verified_at: string | null;
  rejection_reason: string | null;
}

export interface TherapistSummary {
  id: string;
  display_name: string;
  designation: string;
  specialization: TherapistSpecialization;
  experience_years: number;
  therapy_hours: number;
  languages: string[];
  expertises: string[];
  session_modes: SessionMode[];
  pricing: TherapistPricing;
  profile_image_url: string | null;
  is_verified: boolean;
  status: TherapistStatus;
}

export interface TherapistDetail {
  id: string;
  user_id: string;
  first_name: string;
  last_name: string;
  display_name: string;
  bio: string;
  profile_image_url: string | null;
  introduction_audio_url: string | null;
  designation: string;
  specialization: TherapistSpecialization;
  qualifications: string[];
  experience_years: number;
  therapy_hours: number;
  languages: string[];
  expertises: string[];
  session_modes: SessionMode[];
  pricing: TherapistPricing;
  verification: TherapistVerification;
  status: TherapistStatus;
  created_at: string;
}

export interface TherapistFilterParams {
  page?: number;
  limit?: number;
  search?: string;
  language?: string;
  specialization?: TherapistSpecialization;
  expertise?: string;
  session_mode?: SessionMode;
  sort?: TherapistSortBy;
}

export interface PaginationInfo {
  page: number;
  limit: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface PaginatedTherapists {
  items: TherapistSummary[];
  pagination: PaginationInfo;
}
