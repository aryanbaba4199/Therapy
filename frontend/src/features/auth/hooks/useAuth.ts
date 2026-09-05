import { useCallback } from "react";
import { useAppDispatch, useAppSelector } from "../../../store/hooks";
import {
  useLoginMutation,
  useLogoutMutation,
  useRegisterMutation,
  useSendOtpMutation,
  useVerifyOtpMutation,
} from "../api/auth_api";
import { clearCredentials, setCredentials } from "../store/auth_slice";
import type {
  LoginRequest,
  RegisterRequest,
  SendOtpRequest,
  VerifyOtpRequest,
} from "../types/auth.types";
import type { UserRole } from "../../user/types/user.types";

export const useAuth = () => {
  const dispatch = useAppDispatch();
  const { user, accessToken, isAuthenticated, isInitialized, isLoading } =
    useAppSelector((state) => state.auth);

  const [loginMutation, { isLoading: isLoginLoading }] = useLoginMutation();
  const [registerMutation, { isLoading: isRegisterLoading }] =
    useRegisterMutation();
  const [sendOtpMutation, { isLoading: isSendOtpLoading }] =
    useSendOtpMutation();
  const [verifyOtpMutation, { isLoading: isVerifyOtpLoading }] =
    useVerifyOtpMutation();
  const [logoutMutation, { isLoading: isLogoutLoading }] = useLogoutMutation();

  const login = useCallback(
    async (credentials: LoginRequest) => {
      const response = await loginMutation(credentials).unwrap();
      if (response.data) {
        dispatch(
          setCredentials({
            user: response.data.user,
            accessToken: response.data.access_token,
          })
        );
      }
      return response;
    },
    [dispatch, loginMutation]
  );

  const register = useCallback(
    async (data: RegisterRequest) => {
      const response = await registerMutation(data).unwrap();
      if (response.data) {
        dispatch(
          setCredentials({
            user: response.data.user,
            accessToken: response.data.access_token,
          })
        );
      }
      return response;
    },
    [dispatch, registerMutation]
  );

  const sendOtp = useCallback(
    async (data: SendOtpRequest) => {
      return await sendOtpMutation(data).unwrap();
    },
    [sendOtpMutation]
  );

  const verifyOtp = useCallback(
    async (data: VerifyOtpRequest) => {
      const response = await verifyOtpMutation(data).unwrap();
      if (response.data) {
        dispatch(
          setCredentials({
            user: response.data.user,
            accessToken: response.data.access_token,
          })
        );
      }
      return response;
    },
    [dispatch, verifyOtpMutation]
  );

  const logout = useCallback(async () => {
    try {
      await logoutMutation().unwrap();
    } catch {
      // Ignore network errors on logout, proceed with local cleanup
    } finally {
      dispatch(clearCredentials());
    }
  }, [dispatch, logoutMutation]);

  const hasRole = useCallback(
    (role: UserRole): boolean => {
      if (!user) return false;
      return user.roles.includes(role) || user.roles.includes("super_admin");
    },
    [user]
  );

  const hasAnyRole = useCallback(
    (roles: UserRole[]): boolean => {
      if (!user) return false;
      if (user.roles.includes("super_admin")) return true;
      return roles.some((r) => user.roles.includes(r));
    },
    [user]
  );

  return {
    user,
    accessToken,
    isAuthenticated,
    isInitialized,
    isLoading:
      isLoading ||
      isLoginLoading ||
      isRegisterLoading ||
      isSendOtpLoading ||
      isVerifyOtpLoading ||
      isLogoutLoading,
    login,
    register,
    sendOtp,
    verifyOtp,
    logout,
    hasRole,
    hasAnyRole,
  };
};
