import type { UserProfile } from "../../user/types/user.types";

export type OtpChannel = "whatsapp" | "sms";

export interface RegisterRequest {
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  password: string;
  language?: string;
}

export interface LoginRequest {
  identifier: string;
  password: string;
}

export interface SendOtpRequest {
  phone: string;
  channel?: OtpChannel;
}

export interface SendOtpResponse {
  phone: string;
  channel: OtpChannel;
  cooldown_seconds: number;
  expires_in: number;
}

export interface VerifyOtpRequest {
  phone: string;
  otp: string;
}

export interface RefreshTokenRequest {
  refresh_token?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  user: UserProfile;
}

export interface AuthState {
  user: UserProfile | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isInitialized: boolean;
  isLoading: boolean;
}
