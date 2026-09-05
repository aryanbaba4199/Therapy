import { baseApi } from "./base_api";
import type { ApiResponse, HealthData } from "@/common/types/api_types";

export const healthApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getHealth: builder.query<ApiResponse<HealthData>, void>({
      query: () => "/health",
      providesTags: ["Health"],
    }),
  }),
});

export const { useGetHealthQuery } = healthApi;
