import { baseApi } from "../../../store/api/base_api";
import type { ApiResponse } from "../../../common/types/api_types";
import type { UpdateProfileRequest, UserProfile } from "../types/user.types";

export const userApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getProfile: builder.query<ApiResponse<UserProfile>, void>({
      query: () => ({
        url: "/users/me",
        method: "GET",
      }),
      providesTags: ["User"],
    }),

    updateProfile: builder.mutation<
      ApiResponse<UserProfile>,
      UpdateProfileRequest
    >({
      query: (body) => ({
        url: "/users/me",
        method: "PATCH",
        body,
      }),
      invalidatesTags: ["User", "Auth"],
    }),
  }),
  overrideExisting: false,
});

export const { useGetProfileQuery, useUpdateProfileMutation } = userApi;
