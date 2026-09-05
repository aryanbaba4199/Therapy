import React from "react";
import { Box, Typography } from "@mui/material";
import { FiClock, FiAlertTriangle } from "react-icons/fi";
import { useTranslation } from "react-i18next";
import { useReservationCountdown } from "../hooks/useReservationCountdown";

interface ReservationTimerProps {
  expiresAt: string;
  onExpire?: () => void;
}

export const ReservationTimer: React.FC<ReservationTimerProps> = ({
  expiresAt,
  onExpire,
}) => {
  const { t } = useTranslation("booking");
  const { formatted, isExpired, secondsRemaining } = useReservationCountdown({
    expiresAt,
    onExpire,
  });

  const isUrgent = secondsRemaining > 0 && secondsRemaining < 180;

  if (isExpired) {
    return (
      <Box className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg border border-red-200">
        <FiAlertTriangle className="w-5 h-5 flex-shrink-0" />
        <Typography variant="body2" className="font-medium">
          {t("reservation.expired")}
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      className={`flex items-center justify-between p-3.5 rounded-xl border ${
        isUrgent
          ? "bg-amber-50 text-amber-900 border-amber-300 animate-pulse"
          : "bg-teal-50 text-teal-900 border-teal-200"
      }`}
    >
      <Box className="flex items-center gap-2">
        <FiClock className="w-5 h-5 flex-shrink-0" />
        <Typography variant="body2" className="font-medium">
          {t("reservation.expiresIn")}
        </Typography>
      </Box>
      <Typography
        variant="subtitle1"
        className="font-bold tracking-wider font-mono px-2 py-0.5 rounded bg-white shadow-xs"
      >
        {formatted}
      </Typography>
    </Box>
  );
};
