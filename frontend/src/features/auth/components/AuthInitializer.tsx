import React, { useEffect } from "react";
import { useAppDispatch, useAppSelector } from "../../../store/hooks";
import { useLazyGetMeQuery } from "../api/auth_api";
import { clearCredentials, setInitialized, setUser } from "../store/auth_slice";

interface AuthInitializerProps {
  children: React.ReactNode;
}

export const AuthInitializer: React.FC<AuthInitializerProps> = ({
  children,
}) => {
  const dispatch = useAppDispatch();
  const { accessToken } = useAppSelector((state) => state.auth);
  const [triggerGetMe] = useLazyGetMeQuery();

  useEffect(() => {
    const initializeAuth = async () => {
      if (accessToken) {
        try {
          const res = await triggerGetMe().unwrap();
          if (res.data) {
            dispatch(setUser(res.data));
          } else {
            dispatch(clearCredentials());
          }
        } catch {
          dispatch(clearCredentials());
        }
      } else {
        dispatch(setInitialized(true));
      }
    };

    void initializeAuth();
  }, [accessToken, dispatch, triggerGetMe]);

  return <>{children}</>;
};
