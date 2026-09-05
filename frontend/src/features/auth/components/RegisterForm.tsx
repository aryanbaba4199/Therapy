import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Divider,
  Grid,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useAuth } from "../hooks/useAuth";

interface RegisterFormProps {
  onSuccess?: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onSuccess }) => {
  const { t, i18n } = useTranslation(["auth", "validation", "common"]);
  const { register, isLoading } = useAuth();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!firstName.trim() || !lastName.trim() || !password) {
      setErrorMessage(t("validation:required"));
      return;
    }

    if (!email.trim() && !phone.trim()) {
      setErrorMessage(t("validation:required"));
      return;
    }

    if (password.length < 8) {
      setErrorMessage(t("validation:passwordTooShort"));
      return;
    }

    try {
      await register({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim() || undefined,
        phone: phone.trim() || undefined,
        password,
        language: i18n.language || "en",
      });

      if (onSuccess) {
        onSuccess();
      }
    } catch (err: unknown) {
      if (err && typeof err === "object" && "data" in err) {
        const apiError = err as { data?: { message?: string } };
        setErrorMessage(apiError.data?.message || t("validation:serverError"));
      } else {
        setErrorMessage(t("validation:networkError"));
      }
    }
  };

  return (
    <Box sx={{ width: "100%" }}>
      {errorMessage && (
        <Alert
          severity="error"
          sx={{ mb: 3 }}
          onClose={() => setErrorMessage(null)}
        >
          {errorMessage}
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <Stack spacing={3}>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                label={t("auth:firstName")}
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                required
                fullWidth
                disabled={isLoading}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                label={t("auth:lastName")}
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                required
                fullWidth
                disabled={isLoading}
              />
            </Grid>
          </Grid>

          <TextField
            label={t("auth:email")}
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            fullWidth
            disabled={isLoading}
          />

          <TextField
            label={t("auth:phoneNumber")}
            placeholder="+91..."
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            fullWidth
            disabled={isLoading}
          />

          <TextField
            label={t("auth:password")}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            fullWidth
            helperText={t("validation:passwordTooShort")}
            disabled={isLoading}
          />

          <Button
            type="submit"
            variant="contained"
            color="primary"
            size="large"
            fullWidth
            disabled={isLoading}
            startIcon={
              isLoading ? <CircularProgress size={20} color="inherit" /> : null
            }
          >
            {isLoading ? t("auth:registering") : t("auth:register")}
          </Button>
        </Stack>
      </form>

      <Divider sx={{ my: 4 }}>
        <Typography variant="body2" color="text.secondary">
          {t("auth:or")}
        </Typography>
      </Divider>

      <Box sx={{ textAlign: "center" }}>
        <Typography variant="body2" color="text.secondary">
          {t("auth:alreadyHaveAccount")}{" "}
          <Button
            component={RouterLink}
            to="/login"
            variant="text"
            sx={{ fontWeight: 600, textTransform: "none" }}
          >
            {t("auth:login")}
          </Button>
        </Typography>
      </Box>
    </Box>
  );
};
