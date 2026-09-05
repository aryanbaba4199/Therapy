import React from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Divider,
  Typography,
} from "@mui/material";
import { FiCalendar, FiCheck, FiClock, FiList, FiPlus } from "react-icons/fi";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useGetBookingDetailQuery } from "../api/booking_api";

export const BookingConfirmationPage: React.FC = () => {
  const { t } = useTranslation("booking");
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const bookingId = searchParams.get("bookingId") || "";

  const { data, isLoading } = useGetBookingDetailQuery(bookingId, {
    skip: !bookingId,
  });
  const booking = data?.data;

  if (isLoading) {
    return (
      <Box className="flex justify-center items-center min-h-[60vh]">
        <CircularProgress className="text-teal-600" />
      </Box>
    );
  }

  if (!booking) {
    return (
      <Container maxWidth="sm" className="py-16 text-center">
        <Typography variant="h6" className="text-neutral-700">
          Booking not found.
        </Typography>
        <Button
          variant="contained"
          className="mt-4 bg-teal-600 hover:bg-teal-700 text-white rounded-xl"
          onClick={() => navigate("/therapists")}
        >
          Browse Therapists
        </Button>
      </Container>
    );
  }

  const startDate = new Date(booking.start_at);
  const formattedDate = startDate.toLocaleDateString(undefined, {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const formattedTime = startDate.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <Container maxWidth="sm" className="py-12">
      <Box className="text-center space-y-3 mb-8">
        <Box className="w-16 h-16 bg-teal-100 text-teal-600 rounded-full flex items-center justify-center mx-auto shadow-xs">
          <FiCheck className="w-8 h-8" />
        </Box>
        <Typography variant="h4" className="font-extrabold text-neutral-900">
          {t("success.title")}
        </Typography>
        <Typography variant="body1" className="text-neutral-600">
          {t("success.subtitle")}
        </Typography>
      </Box>

      <Card className="rounded-2xl border border-neutral-200 shadow-sm overflow-hidden mb-6">
        <CardContent className="p-6 space-y-4">
          <Box className="flex justify-between items-center pb-2 border-b border-neutral-100">
            <span className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
              {t("success.reference")}
            </span>
            <span className="font-mono font-bold text-sm text-teal-700 bg-teal-50 px-2.5 py-1 rounded-lg">
              {booking.id.slice(0, 8).toUpperCase()}
            </span>
          </Box>

          <Box className="space-y-3 text-sm">
            <Box className="flex justify-between">
              <span className="text-neutral-500">
                {t("summary.therapist")}:
              </span>
              <span className="font-semibold text-neutral-900">
                {booking.therapist.display_name}
              </span>
            </Box>
            <Box className="flex justify-between">
              <span className="text-neutral-500">
                {t("summary.sessionMode")}:
              </span>
              <span className="font-semibold text-neutral-900 capitalize">
                {booking.session_mode.replace("_", " ")}
              </span>
            </Box>
            <Box className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-neutral-500">
                <FiCalendar className="text-teal-600" />
                {t("summary.date")}:
              </span>
              <span className="font-semibold text-neutral-900">
                {formattedDate}
              </span>
            </Box>
            <Box className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-neutral-500">
                <FiClock className="text-teal-600" />
                {t("summary.time")}:
              </span>
              <span className="font-semibold text-neutral-900">
                {formattedTime}
              </span>
            </Box>

            <Divider className="my-2" />

            <Box className="flex justify-between items-center text-base pt-1">
              <span className="font-bold text-neutral-900">
                {t("summary.fee")}:
              </span>
              <span className="font-bold text-lg text-teal-700">
                ₹{booking.pricing.amount}
              </span>
            </Box>
          </Box>
        </CardContent>
      </Card>

      <Box className="flex flex-col sm:flex-row gap-3">
        <Button
          variant="outlined"
          fullWidth
          startIcon={<FiPlus />}
          className="rounded-xl py-2.5 text-teal-700 border-teal-600 hover:bg-teal-50 capitalize"
          onClick={() => navigate("/therapists")}
        >
          {t("success.bookAnother")}
        </Button>

        <Button
          variant="contained"
          fullWidth
          startIcon={<FiList />}
          className="rounded-xl py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-bold capitalize shadow-none"
          onClick={() => navigate("/bookings")}
        >
          {t("success.viewBookings")}
        </Button>
      </Box>
    </Container>
  );
};
