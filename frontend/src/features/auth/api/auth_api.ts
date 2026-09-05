import { baseApi } from "../../../store/api/base_api";
import type { ApiResponse } from "../../../common/types/api_types";
import type {
  LoginRequest,
  RegisterRequest,
  SendOtpRequest,
  SendOtpResponse,
  TokenResponse,
  VerifyOtpRequest,
} from "../types/auth.types";
import type { UserProfile } from "../../user/types/user.types";

export const authApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    register: builder.mutation<ApiResponse<TokenResponse>, RegisterRequest>({
      query: (body) => ({
        url: "/auth/register",
        method: "POST",
        body,
      }),
      invalidatesTags: ["Auth", "User"],
    }),

    login: builder.mutation<ApiResponse<TokenResponse>, LoginRequest>({
      query: (body) => ({
        url: "/auth/login",
        method: "POST",
        body,
      }),
      invalidatesTags: ["Auth", "User"],
    }),

    sendOtp: builder.mutation<ApiResponse<SendOtpResponse>, SendOtpRequest>({
      query: (body) => ({
        url: "/auth/otp/send",
        method: "POST",
        body,
      }),
    }),

    verifyOtp: builder.mutation<ApiResponse<TokenResponse>, VerifyOtpRequest>({
      query: (body) => ({
        url: "/auth/otp/verify",
        method: "POST",
        body,
      }),
      invalidatesTags: ["Auth", "User"],
    }),

    refreshToken: builder.mutation<ApiResponse<TokenResponse>, void>({
      query: () => ({
        url: "/auth/refresh",
        method: "POST",
        body: {},
      }),
      invalidatesTags: ["Auth"],
    }),

    logout: builder.mutation<ApiResponse<{ status: string }>, void>({
      query: () => ({
        url: "/auth/logout",
        method: "POST",
      }),
      invalidatesTags: ["Auth", "User"],
    }),

    getMe: builder.query<ApiResponse<UserProfile>, void>({
      query: () => ({
        url: "/auth/me",
        method: "GET",
      }),
      providesTags: ["Auth", "User"],
    }),
  }),
  overrideExisting: false,
});

export const {
  useRegisterMutation,
  useLoginMutation,
  useSendOtpMutation,
  useVerifyOtpMutation,
  useRefreshTokenMutation,
  useLogoutMutation,
  useGetMeQuery,
  useLazyGetMeQuery,
} = authApi;
