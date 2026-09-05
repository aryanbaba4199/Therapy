export type UserRole =
  "user" | "therapist" | "staff" | "first_responder" | "admin" | "super_admin";
export type UserStatus = "active" | "inactive" | "suspended" | "deleted";
export type AuthProvider = "password" | "otp" | "google";

export interface UserPreferences {
  language: string;
  notifications: boolean;
}

export interface UserProfile {
  id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  roles: UserRole[];
  status: UserStatus;
  is_verified: boolean;
  auth_providers: AuthProvider[];
  profile: Record<string, unknown>;
  preferences: UserPreferences;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
}

export interface UpdateProfileRequest {
  first_name?: string;
  last_name?: string;
  profile?: Record<string, unknown>;
  preferences?: Partial<UserPreferences>;
}
