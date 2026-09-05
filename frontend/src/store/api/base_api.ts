import {
  createApi,
  fetchBaseQuery,
  type BaseQueryFn,
  type FetchArgs,
  type FetchBaseQueryError,
} from "@reduxjs/toolkit/query/react";

// Dynamic API base URL based on environment
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL !== undefined &&
  typeof import.meta.env.VITE_API_BASE_URL === "string" &&
  import.meta.env.VITE_API_BASE_URL.length > 0
    ? import.meta.env.VITE_API_BASE_URL
    : "/api/v1";

const rawBaseQuery = fetchBaseQuery({
  baseUrl: API_BASE_URL,
  credentials: "include",
  prepareHeaders: (headers) => {
    headers.set("Accept", "application/json");

    // Retrieve token from local storage or cookie session if available
    const token = localStorage.getItem("oppam_access_token");
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    // Attach active language code for potential backend localized formatting
    const currentLang = localStorage.getItem("oppam_language") || "en";
    headers.set("Accept-Language", currentLang);

    return headers;
  },
});

/**
 * Custom base query wrapper providing reauthentication handling,
 * unified error normalization, and request trace telemetry.
 */
const baseQueryWithReauth: BaseQueryFn<
  string | FetchArgs,
  unknown,
  FetchBaseQueryError
> = async (args, api, extraOptions) => {
  const result = await rawBaseQuery(args, api, extraOptions);

  if (result.error) {
    const status = result.error.status;

    // Handle 401 Unauthorized for token refresh architecture
    if (status === 401) {
      // Re-authentication / refresh token flow placeholder:
      // In future auth phase: dispatch refreshToken endpoint, retry original query if succeeded.
      // For now, clear stale token and notify listeners
      localStorage.removeItem("oppam_access_token");
    }
  }

  return result;
};

export const baseApi = createApi({
  reducerPath: "api",
  baseQuery: baseQueryWithReauth,
  tagTypes: [
    "Health",
    "Auth",
    "User",
    "Therapist",
    "Booking",
    "Package",
    "Payment",
    "Session",
  ],
  endpoints: () => ({}),
});
