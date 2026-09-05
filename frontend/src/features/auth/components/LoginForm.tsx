import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Divider,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import { FaLock, FaMobileAlt } from "react-icons/fa";
import { useAuth } from "../hooks/useAuth";
import { OtpForm } from "./OtpForm";

interface LoginFormProps {
  onSuccess?: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {
  const { t } = useTranslation(["auth", "validation", "common"]);
  const { login, isLoading } = useAuth();

  const [activeTab, setActiveTab] = useState<"otp" | "password">("otp");
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!identifier.trim() || !password) {
      setErrorMessage(t("validation:required"));
      return;
    }

    try {
      await login({ identifier: identifier.trim(), password });
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: unknown) {
      if (err && typeof err === "object" && "data" in err) {
        const apiError = err as { data?: { message?: string } };
        setErrorMessage(apiError.data?.message || t("auth:invalidCredentials"));
      } else {
        setErrorMessage(t("validation:networkError"));
      }
    }
  };

  return (
    <Box sx={{ width: "100%" }}>
      <Tabs
        value={activeTab}
        onChange={(_, val: "otp" | "password") => {
          setActiveTab(val);
          setErrorMessage(null);
        }}
        variant="fullWidth"
        sx={{ mb: 4, borderBottom: 1, borderColor: "divider" }}
      >
        <Tab
          value="otp"
          icon={<FaMobileAlt />}
          iconPosition="start"
          label={t("auth:signInWithOtp")}
        />
        <Tab
          value="password"
          icon={<FaLock />}
          iconPosition="start"
          label={t("auth:signInWithPassword")}
        />
      </Tabs>

      {activeTab === "otp" ? (
        <OtpForm onSuccess={onSuccess} />
      ) : (
        <form onSubmit={handlePasswordLogin}>
          {errorMessage && (
            <Alert
              severity="error"
              sx={{ mb: 3 }}
              onClose={() => setErrorMessage(null)}
            >
              {errorMessage}
            </Alert>
          )}

          <Stack spacing={3}>
            <TextField
              label={t("auth:email")}
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              required
              fullWidth
              autoFocus
              disabled={isLoading}
            />

            <TextField
              label={t("auth:password")}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              fullWidth
              disabled={isLoading}
            />

            <Button
              type="submit"
              variant="contained"
              color="primary"
              size="large"
              fullWidth
              disabled={isLoading || !identifier.trim() || !password}
              startIcon={
                isLoading ? (
                  <CircularProgress size={20} color="inherit" />
                ) : null
              }
            >
              {isLoading ? t("auth:loggingIn") : t("auth:login")}
            </Button>
          </Stack>
        </form>
      )}

      <Divider sx={{ my: 4 }}>
        <Typography variant="body2" color="text.secondary">
          {t("auth:or")}
        </Typography>
      </Divider>

      <Box sx={{ textAlign: "center" }}>
        <Typography variant="body2" color="text.secondary">
          {t("auth:dontHaveAccount")}{" "}
          <Button
            component={RouterLink}
            to="/register"
            variant="text"
            sx={{ fontWeight: 600, textTransform: "none" }}
          >
            {t("auth:signUp")}
          </Button>
        </Typography>
      </Box>
    </Box>
  );
};
