import { baseApi } from "@/store/api/base_api";
import type { ApiResponse } from "@/common/types/api_types";
import type {
  CreateReviewRequest,
  PublicReviewResponse,
  ReviewResponse,
  TherapistRatingSummaryResponse,
} from "../types/review_types";

export const reviewApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    createReview: builder.mutation<
      ApiResponse<ReviewResponse>,
      CreateReviewRequest
    >({
      query: (body) => ({
        url: "/reviews",
        method: "POST",
        body,
      }),
      invalidatesTags: ["Review", "TherapistRating"],
    }),

    getReviewById: builder.query<ApiResponse<ReviewResponse>, string>({
      query: (id) => `/reviews/${id}`,
      providesTags: (_result, _err, id) => [{ type: "Review", id }],
    }),

    listTherapistReviews: builder.query<
      ApiResponse<PublicReviewResponse[]>,
      { therapistId: string; page?: number; limit?: number }
    >({
      query: ({ therapistId, page = 1, limit = 20 }) => ({
        url: `/reviews/therapist/${therapistId}`,
        params: { page, limit },
      }),
      providesTags: (_result, _err, { therapistId }) => [
        { type: "Review", id: therapistId },
      ],
    }),

    getTherapistRatingSummary: builder.query<
      ApiResponse<TherapistRatingSummaryResponse>,
      string
    >({
      query: (therapistId) => `/reviews/therapist/${therapistId}/summary`,
      providesTags: (_result, _err, therapistId) => [
        { type: "TherapistRating", id: therapistId },
      ],
    }),

    listMyReviews: builder.query<
      ApiResponse<ReviewResponse[]>,
      { page?: number; limit?: number } | void
    >({
      query: (params) => ({
        url: "/reviews/my/history",
        params: params || {},
      }),
      providesTags: ["Review"],
    }),
  }),
});

export const {
  useCreateReviewMutation,
  useGetReviewByIdQuery,
  useListTherapistReviewsQuery,
  useGetTherapistRatingSummaryQuery,
  useListMyReviewsQuery,
} = reviewApi;
