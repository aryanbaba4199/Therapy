import React, { useState } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Divider,
  TextField,
  Typography,
} from "@mui/material";
import { FiCheckCircle, FiShield, FiXCircle } from "react-icons/fi";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  useCancelReservationMutation,
  useConfirmBookingMutation,
  useGetReservationQuery,
} from "../api/booking_api";
import { ReservationTimer } from "../components/ReservationTimer";
import { useGetTherapistQuery } from "@/features/therapist/api/therapist_api";

export const BookingCheckoutPage: React.FC = () => {
  const { t } = useTranslation("booking");
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const reservationId = searchParams.get("reservationId") || "";

  const [notes, setNotes] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    data: resData,
    isLoading: isResLoading,
    error: resError,
  } = useGetReservationQuery(reservationId, {
    skip: !reservationId,
    pollingInterval: 15000,
  });

  const reservation = resData?.data;

  const { data: therapistData } = useGetTherapistQuery(
    reservation?.therapist_id || "",
    {
      skip: !reservation?.therapist_id,
    }
  );
  const therapist = therapistData?.data;

  const [confirmBooking, { isLoading: isConfirming }] =
    useConfirmBookingMutation();
  const [cancelReservation, { isLoading: isCancelling }] =
    useCancelReservationMutation();

  if (!reservationId) {
    return (
      <Container maxWidth="sm" className="py-16 text-center">
        <Typography variant="h6" className="text-neutral-700">
          No reservation found. Please select an available slot first.
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

  if (isResLoading) {
    return (
      <Box className="flex justify-center items-center min-h-[60vh]">
        <CircularProgress className="text-teal-600" />
      </Box>
    );
  }

  if (resError || !reservation) {
    return (
      <Container maxWidth="sm" className="py-16 text-center">
        <Box className="p-6 bg-red-50 text-red-700 rounded-2xl border border-red-200">
          <Typography variant="h6" className="font-bold mb-2">
            Reservation Expired or Not Found
          </Typography>
          <Typography variant="body2" className="mb-4">
            {t("reservation.expired")}
          </Typography>
          <Button
            variant="contained"
            className="bg-teal-600 hover:bg-teal-700 text-white rounded-xl"
            onClick={() => navigate("/therapists")}
          >
            Find Another Slot
          </Button>
        </Box>
      </Container>
    );
  }

  const startDate = new Date(reservation.start_at);
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

  const handleConfirm = async () => {
    try {
      setErrorMessage(null);
      const res = await confirmBooking({
        reservation_id: reservation.id,
        client_notes: notes.trim() || undefined,
      }).unwrap();

      if (res.data?.id) {
        navigate(`/bookings/confirmation?bookingId=${res.data.id}`);
      }
    } catch (err: unknown) {
      const errorObj = err as { data?: { message?: string } };
      setErrorMessage(errorObj.data?.message || t("confirm.failed"));
    }
  };

  const handleCancelReservation = async () => {
    try {
      await cancelReservation(reservation.id).unwrap();
      navigate(
        reservation.therapist_id
          ? `/therapists/${reservation.therapist_id}`
          : "/therapists"
      );
    } catch {
      navigate("/therapists");
    }
  };

  return (
    <Container maxWidth="md" className="py-10">
      <Box className="max-w-xl mx-auto space-y-6">
        <Typography
          variant="h4"
          className="font-bold text-neutral-900 text-center"
        >
          {t("reservation.title")}
        </Typography>

        <ReservationTimer
          expiresAt={reservation.expires_at}
          onExpire={() => navigate("/therapists")}
        />

        {errorMessage && (
          <Box className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200">
            <Typography variant="body2">{errorMessage}</Typography>
          </Box>
        )}

        <Card className="rounded-2xl border border-neutral-200 shadow-sm overflow-hidden">
          <CardContent className="p-6 space-y-6">
            <Typography variant="h6" className="font-bold text-neutral-900">
              {t("summary.title")}
            </Typography>

            <Box className="space-y-3 text-sm">
              <Box className="flex justify-between">
                <span className="text-neutral-500">
                  {t("summary.therapist")}:
                </span>
                <span className="font-semibold text-neutral-900">
                  {therapist?.display_name || "Consultant"}
                </span>
              </Box>
              <Box className="flex justify-between">
                <span className="text-neutral-500">
                  {t("summary.sessionMode")}:
                </span>
                <span className="font-semibold text-neutral-900 capitalize">
                  {reservation.session_mode.replace("_", " ")}
                </span>
              </Box>
              <Box className="flex justify-between">
                <span className="text-neutral-500">{t("summary.date")}:</span>
                <span className="font-semibold text-neutral-900">
                  {formattedDate}
                </span>
              </Box>
              <Box className="flex justify-between">
                <span className="text-neutral-500">{t("summary.time")}:</span>
                <span className="font-semibold text-neutral-900">
                  {formattedTime}
                </span>
              </Box>
              <Box className="flex justify-between">
                <span className="text-neutral-500">
                  {t("summary.duration")}:
                </span>
                <span className="font-semibold text-neutral-900">
                  {t("summary.minutes", {
                    count: reservation.duration_minutes,
                  })}
                </span>
              </Box>

              <Divider className="my-2" />

              <Box className="flex justify-between items-center text-base pt-1">
                <span className="font-bold text-neutral-900">
                  {t("summary.total")}:
                </span>
                <span className="font-bold text-xl text-teal-700">
                  ₹{therapist?.pricing.amount || 0}
                </span>
              </Box>
            </Box>

            <TextField
              fullWidth
              multiline
              rows={3}
              label={t("confirm.notesLabel")}
              placeholder={t("confirm.notesPlaceholder")}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="mt-4"
            />

            <Box className="flex items-center gap-2 text-xs text-neutral-500">
              <FiShield className="text-teal-600 flex-shrink-0" />
              <span>{t("confirm.terms")}</span>
            </Box>

            <Box className="flex flex-col sm:flex-row gap-3 pt-2">
              <Button
                variant="outlined"
                color="inherit"
                fullWidth
                disabled={isConfirming || isCancelling}
                onClick={handleCancelReservation}
                startIcon={<FiXCircle />}
                className="rounded-xl py-2.5 text-neutral-600 capitalize"
              >
                {t("reservation.cancel")}
              </Button>

              <Button
                variant="contained"
                fullWidth
                disabled={isConfirming || isCancelling}
                onClick={handleConfirm}
                startIcon={
                  isConfirming ? (
                    <CircularProgress size={18} color="inherit" />
                  ) : (
                    <FiCheckCircle />
                  )
                }
                className="rounded-xl py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-bold capitalize shadow-none"
              >
                {isConfirming ? t("confirm.submitting") : t("confirm.submit")}
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
};
