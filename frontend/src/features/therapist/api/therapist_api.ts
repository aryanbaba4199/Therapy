import { baseApi } from "../../../store/api/base_api";
import type { ApiResponse } from "../../../common/types/api_types";
import type {
  PaginatedTherapists,
  TherapistDetail,
  TherapistFilterParams,
} from "../types/therapist.types";

export const therapistApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getTherapists: builder.query<
      ApiResponse<PaginatedTherapists>,
      TherapistFilterParams | void
    >({
      query: (params) => {
        const queryParams = new URLSearchParams();
        if (params) {
          if (params.page !== undefined)
            queryParams.set("page", params.page.toString());
          if (params.limit !== undefined)
            queryParams.set("limit", params.limit.toString());
          if (params.search) queryParams.set("search", params.search);
          if (params.language) queryParams.set("language", params.language);
          if (params.specialization)
            queryParams.set("specialization", params.specialization);
          if (params.expertise) queryParams.set("expertise", params.expertise);
          if (params.session_mode)
            queryParams.set("session_mode", params.session_mode);
          if (params.sort) queryParams.set("sort", params.sort);
        }
        const qs = queryParams.toString();
        return {
          url: `/therapists${qs ? `?${qs}` : ""}`,
          method: "GET",
        };
      },
      providesTags: (result) =>
        result?.data?.items
          ? [
              ...result.data.items.map(({ id }) => ({
                type: "Therapist" as const,
                id,
              })),
              { type: "Therapist", id: "LIST" },
            ]
          : [{ type: "Therapist", id: "LIST" }],
    }),

    getTherapist: builder.query<ApiResponse<TherapistDetail>, string>({
      query: (id) => ({
        url: `/therapists/${id}`,
        method: "GET",
      }),
      providesTags: (_result, _err, id) => [{ type: "Therapist", id }],
    }),

    getMyTherapistProfile: builder.query<ApiResponse<TherapistDetail>, void>({
      query: () => ({
        url: "/therapists/me",
        method: "GET",
      }),
      providesTags: [{ type: "Therapist", id: "ME" }],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetTherapistsQuery,
  useGetTherapistQuery,
  useGetMyTherapistProfileQuery,
  useLazyGetTherapistsQuery,
} = therapistApi;
