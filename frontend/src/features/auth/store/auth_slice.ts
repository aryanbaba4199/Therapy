import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { AuthState } from "../types/auth.types";
import type { UserProfile } from "../../user/types/user.types";

const storedToken =
  typeof window !== "undefined"
    ? localStorage.getItem("oppam_access_token")
    : null;

const initialState: AuthState = {
  user: null,
  accessToken: storedToken,
  isAuthenticated: Boolean(storedToken),
  isInitialized: false,
  isLoading: false,
};

export const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setCredentials: (
      state,
      action: PayloadAction<{ user: UserProfile; accessToken: string }>
    ) => {
      state.user = action.payload.user;
      state.accessToken = action.payload.accessToken;
      state.isAuthenticated = true;
      state.isInitialized = true;
      state.isLoading = false;
      localStorage.setItem("oppam_access_token", action.payload.accessToken);
    },
    setUser: (state, action: PayloadAction<UserProfile>) => {
      state.user = action.payload;
      state.isAuthenticated = true;
      state.isInitialized = true;
      state.isLoading = false;
    },
    clearCredentials: (state) => {
      state.user = null;
      state.accessToken = null;
      state.isAuthenticated = false;
      state.isInitialized = true;
      state.isLoading = false;
      localStorage.removeItem("oppam_access_token");
    },
    setInitialized: (state, action: PayloadAction<boolean>) => {
      state.isInitialized = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
  },
});

export const {
  setCredentials,
  setUser,
  clearCredentials,
  setInitialized,
  setLoading,
} = authSlice.actions;

export const authReducer = authSlice.reducer;
