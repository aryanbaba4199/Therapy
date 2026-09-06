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

interface RefreshTokenResponseData {
  access_token: string;
  refresh_token?: string;
  token_type?: string;
  expires_in?: number;
}

interface ApiResponseEnvelope<T> {
  success: boolean;
  data: T;
  message?: string;
}

let refreshPromise: Promise<string | null> | null = null;

const requestNewAccessToken = async (): Promise<string | null> => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      credentials: "include",
    });

    if (!response.ok) {
      localStorage.removeItem("oppam_access_token");
      return null;
    }

    const payload =
      (await response.json()) as ApiResponseEnvelope<RefreshTokenResponseData>;
    if (
      payload.success &&
      payload.data &&
      typeof payload.data.access_token === "string"
    ) {
      const newToken = payload.data.access_token;
      localStorage.setItem("oppam_access_token", newToken);
      return newToken;
    }

    localStorage.removeItem("oppam_access_token");
    return null;
  } catch {
    localStorage.removeItem("oppam_access_token");
    return null;
  }
};

/**
 * Custom base query wrapper providing reauthentication handling,
 * unified error normalization, and single-flight token refresh mutex.
 */
const baseQueryWithReauth: BaseQueryFn<
  string | FetchArgs,
  unknown,
  FetchBaseQueryError
> = async (args, api, extraOptions) => {
  let result = await rawBaseQuery(args, api, extraOptions);

  if (result.error && result.error.status === 401) {
    const requestUrl = typeof args === "string" ? args : args.url;
    if (!requestUrl.includes("/auth/refresh")) {
      if (!refreshPromise) {
        refreshPromise = requestNewAccessToken().finally(() => {
          refreshPromise = null;
        });
      }

      const newToken = await refreshPromise;
      if (newToken) {
        // Retry the original query with fresh token
        result = await rawBaseQuery(args, api, extraOptions);
      }
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
    "Availability",
    "Slot",
    "ExtraSlot",
    "Booking",
    "Reservation",
    "Package",
    "UserPackage",
    "Offer",
    "Payment",
    "Session",
    "SessionNote",
    "TherapyGoal",
    "TherapistDashboard",
    "Review",
    "TherapistRating",
    "SupportTicket",
    "SupportMessage",
    "OperationsMetrics",
    "OperationsUser",
    "Lead",
    "AuditLog",
  ],
  endpoints: () => ({}),
});
