import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import { FaCommentDots, FaWhatsapp } from "react-icons/fa";
import { useAuth } from "../hooks/useAuth";
import type { OtpChannel } from "../types/auth.types";

interface OtpFormProps {
  onSuccess?: () => void;
}

export const OtpForm: React.FC<OtpFormProps> = ({ onSuccess }) => {
  const { t } = useTranslation(["auth", "validation", "common"]);
  const { sendOtp, verifyOtp, isLoading } = useAuth();

  const [phone, setPhone] = useState("");
  const [channel, setChannel] = useState<OtpChannel>("whatsapp");
  const [step, setStep] = useState<"phone" | "otp">("phone");
  const [otp, setOtp] = useState("");
  const [countdown, setCountdown] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let timer: number | undefined;
    if (countdown > 0) {
      timer = window.setInterval(() => {
        setCountdown((prev) => prev - 1);
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [countdown]);

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const cleanPhone = phone.trim();
    if (!cleanPhone || cleanPhone.length < 10) {
      setErrorMessage(t("validation:invalidPhone"));
      return;
    }

    try {
      const res = await sendOtp({ phone: cleanPhone, channel });
      if (res.data) {
        setCountdown(res.data.cooldown_seconds || 30);
        setStep("otp");
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

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (otp.length < 4) {
      setErrorMessage(t("validation:invalidOtp"));
      return;
    }

    try {
      await verifyOtp({ phone: phone.trim(), otp: otp.trim() });
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

      {step === "phone" ? (
        <form onSubmit={handleSendOtp}>
          <Stack spacing={3}>
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                {t("auth:channel")}
              </Typography>
              <Tabs
                value={channel}
                onChange={(_, val: OtpChannel) => setChannel(val)}
                variant="fullWidth"
                sx={{ mb: 2, bgcolor: "background.paper", borderRadius: 1 }}
              >
                <Tab
                  value="whatsapp"
                  icon={<FaWhatsapp className="text-emerald-500 text-lg" />}
                  iconPosition="start"
                  label={t("auth:whatsapp")}
                />
                <Tab
                  value="sms"
                  icon={<FaCommentDots className="text-blue-500 text-lg" />}
                  iconPosition="start"
                  label={t("auth:sms")}
                />
              </Tabs>
            </Box>

            <TextField
              label={t("auth:phoneNumber")}
              placeholder={t("auth:enterPhone")}
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
              fullWidth
              autoFocus
              disabled={isLoading}
              slotProps={{
                input: {
                  inputMode: "tel",
                },
              }}
            />

            <Button
              type="submit"
              variant="contained"
              color="primary"
              size="large"
              fullWidth
              disabled={isLoading || !phone.trim()}
              startIcon={
                isLoading ? (
                  <CircularProgress size={20} color="inherit" />
                ) : null
              }
            >
              {isLoading ? t("auth:sending") : t("auth:getOtp")}
            </Button>
          </Stack>
        </form>
      ) : (
        <form onSubmit={handleVerifyOtp}>
          <Stack spacing={3}>
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <Typography variant="body2" color="text.secondary">
                {phone}
              </Typography>
              <Button
                variant="text"
                size="small"
                onClick={() => {
                  setStep("phone");
                  setOtp("");
                  setErrorMessage(null);
                }}
              >
                {t("common:edit")}
              </Button>
            </Box>

            <TextField
              label={t("auth:enterOtp")}
              value={otp}
              onChange={(e) =>
                setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))
              }
              required
              fullWidth
              autoFocus
              disabled={isLoading}
              slotProps={{
                htmlInput: {
                  maxLength: 6,
                  inputMode: "numeric",
                  pattern: "[0-9]*",
                  style: {
                    letterSpacing: "0.5rem",
                    textAlign: "center",
                    fontSize: "1.25rem",
                  },
                },
              }}
            />

            <Button
              type="submit"
              variant="contained"
              color="primary"
              size="large"
              fullWidth
              disabled={isLoading || otp.length < 4}
              startIcon={
                isLoading ? (
                  <CircularProgress size={20} color="inherit" />
                ) : null
              }
            >
              {isLoading ? t("auth:verifying") : t("auth:verifyOtp")}
            </Button>

            <Box sx={{ textAlign: "center" }}>
              {countdown > 0 ? (
                <Typography variant="body2" color="text.secondary">
                  {t("auth:resendIn", { seconds: countdown })}
                </Typography>
              ) : (
                <Button
                  variant="text"
                  size="small"
                  disabled={isLoading}
                  onClick={async () => {
                    try {
                      const res = await sendOtp({
                        phone: phone.trim(),
                        channel,
                      });
                      if (res.data) {
                        setCountdown(res.data.cooldown_seconds || 30);
                      }
                    } catch {
                      setErrorMessage(t("validation:serverError"));
                    }
                  }}
                >
                  {t("auth:resendOtp")}
                </Button>
              )}
            </Box>
          </Stack>
        </form>
      )}
    </Box>
  );
};
