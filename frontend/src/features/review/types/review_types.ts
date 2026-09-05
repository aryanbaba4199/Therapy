export type ReviewStatus = "published" | "hidden" | "flagged";

export interface CreateReviewRequest {
  session_id: string;
  rating: number;
  comment?: string;
  is_anonymous?: boolean;
}

export interface ReviewResponse {
  id: string;
  session_id: string;
  booking_id: string;
  therapist_id: string;
  client_id: string;
  rating: number;
  comment: string;
  client_display_name: string;
  is_anonymous: boolean;
  status: ReviewStatus;
  created_at: string;
  updated_at: string;
}

export interface PublicReviewResponse {
  id: string;
  therapist_id: string;
  rating: number;
  comment: string;
  client_display_name: string;
  created_at: string;
}

export interface TherapistRatingSummaryResponse {
  therapist_id: string;
  average_rating: number;
  review_count: number;
  distribution: Record<string, number>;
}
