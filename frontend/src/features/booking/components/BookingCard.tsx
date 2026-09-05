import React from "react";
import { Box, Card, CardContent, Typography, Button } from "@mui/material";
import { FiCalendar, FiClock, FiVideo, FiMapPin } from "react-icons/fi";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import type { BookingSummary } from "../types/booking.types";
import { BookingStatusChip } from "./BookingStatusChip";

interface BookingCardProps {
  booking: BookingSummary;
  onCancelClick?: (bookingId: string) => void;
}

export const BookingCard: React.FC<BookingCardProps> = ({
  booking,
  onCancelClick,
}) => {
  const { t } = useTranslation("booking");
  const navigate = useNavigate();

  const startDate = new Date(booking.start_at);
  const formattedDate = startDate.toLocaleDateString(undefined, {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
  });
  const formattedTime = startDate.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });

  const isUpcoming =
    booking.status === "confirmed" && new Date(booking.start_at) > new Date();

  return (
    <Card className="rounded-2xl border border-neutral-200 shadow-sm hover:shadow-md transition-shadow">
      <CardContent className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <Box className="space-y-2 flex-1">
          <Box className="flex items-center gap-3">
            <Typography variant="h6" className="font-bold text-neutral-900">
              {booking.therapist.display_name}
            </Typography>
            <BookingStatusChip status={booking.status} />
          </Box>

          <Typography variant="body2" className="text-neutral-500">
            {booking.therapist.designation}
          </Typography>

          <Box className="flex flex-wrap items-center gap-4 text-xs font-medium text-neutral-600 pt-1">
            <Box className="flex items-center gap-1">
              <FiCalendar className="text-teal-600" />
              <span>{formattedDate}</span>
            </Box>
            <Box className="flex items-center gap-1">
              <FiClock className="text-teal-600" />
              <span>
                {formattedTime} (
                {t("summary.minutes", { count: booking.duration_minutes })})
              </span>
            </Box>
            <Box className="flex items-center gap-1">
              {booking.session_mode === "online" ? (
                <>
                  <FiVideo className="text-teal-600" />
                  <span>Online Consultation</span>
                </>
              ) : (
                <>
                  <FiMapPin className="text-teal-600" />
                  <span className="capitalize">
                    {booking.session_mode.replace("_", " ")}
                  </span>
                </>
              )}
            </Box>
          </Box>
        </Box>

        <Box className="flex items-center gap-3 self-end md:self-center">
          {isUpcoming && onCancelClick && (
            <Button
              variant="outlined"
              color="error"
              size="small"
              className="rounded-xl capitalize"
              onClick={() => onCancelClick(booking.id)}
            >
              {t("history.cancel")}
            </Button>
          )}

          <Button
            variant="contained"
            color="primary"
            size="small"
            className="rounded-xl capitalize shadow-none bg-teal-600 hover:bg-teal-700 text-white"
            onClick={() => navigate(`/bookings/${booking.id}`)}
          >
            {t("history.details")}
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};
