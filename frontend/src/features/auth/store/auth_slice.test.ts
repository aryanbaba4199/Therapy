import { describe, it, expect } from "vitest";
import { authReducer, setCredentials, clearCredentials } from "./auth_slice";
import type { UserProfile } from "@/features/user/types/user.types";

describe("auth_slice", () => {
  const initialState = {
    user: null,
    accessToken: null,
    isAuthenticated: false,
    isInitialized: false,
    isLoading: false,
  };

  it("should return the initial state on empty action", () => {
    expect(authReducer(undefined, { type: "unknown" })).toEqual(initialState);
  });

  it("should update state on setCredentials", () => {
    const user: UserProfile = {
      id: "u123",
      phone: "+919876543210",
      email: "test@example.com",
      first_name: "Rahul",
      last_name: "Nair",
      roles: ["user"],
      status: "active",
      is_verified: true,
      auth_providers: ["otp"],
      profile: {},
      preferences: {
        language: "en",
        notifications: true,
      },
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      last_login_at: null,
    };

    const nextState = authReducer(
      initialState,
      setCredentials({ user, accessToken: "token-abc" })
    );

    expect(nextState.isAuthenticated).toBe(true);
    expect(nextState.isInitialized).toBe(true);
    expect(nextState.accessToken).toBe("token-abc");
    expect(nextState.user?.email).toBe("test@example.com");
  });

  it("should reset state on clearCredentials", () => {
    const loggedInState = {
      user: {
        id: "u123",
        phone: "+919876543210",
        email: "test@example.com",
        first_name: "Rahul",
        last_name: "Nair",
        roles: ["user" as const],
        status: "active" as const,
        is_verified: true,
        auth_providers: ["otp" as const],
        profile: {},
        preferences: {
          language: "en",
          notifications: true,
        },
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        last_login_at: null,
      },
      accessToken: "token-abc",
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
    };

    const nextState = authReducer(loggedInState, clearCredentials());
    expect(nextState.isAuthenticated).toBe(false);
    expect(nextState.accessToken).toBeNull();
    expect(nextState.user).toBeNull();
  });
});
