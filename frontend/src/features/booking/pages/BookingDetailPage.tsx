import React, { useState } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  TextField,
  Typography,
} from "@mui/material";
import {
  FiCalendar,
  FiClock,
  FiMapPin,
  FiVideo,
  FiArrowLeft,
} from "react-icons/fi";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";
import {
  useCancelBookingMutation,
  useGetBookingDetailQuery,
} from "../api/booking_api";
import { BookingStatusChip } from "../components/BookingStatusChip";
import { JoinMeetingButton } from "@/features/session/components/JoinMeetingButton";

export const BookingDetailPage: React.FC = () => {
  const { t } = useTranslation("booking");
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const { data, isLoading } = useGetBookingDetailQuery(id || "", {
    skip: !id,
  });
  const booking = data?.data;

  const [cancelBooking, { isLoading: isCancelling }] =
    useCancelBookingMutation();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState("");

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
          Booking details not found.
        </Typography>
        <Button
          variant="contained"
          className="mt-4 bg-teal-600 hover:bg-teal-700 text-white rounded-xl"
          onClick={() => navigate("/bookings")}
        >
          Back to Bookings
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

  const isUpcoming =
    booking.status === "confirmed" && new Date(booking.start_at) > new Date();

  const handleConfirmCancel = async () => {
    try {
      await cancelBooking({
        bookingId: booking.id,
        payload: { reason: cancelReason.trim() || undefined },
      }).unwrap();
      setDialogOpen(false);
    } catch {
      // Handled via mutation state
    }
  };

  return (
    <Container maxWidth="md" className="py-10">
      <Button
        startIcon={<FiArrowLeft />}
        onClick={() => navigate("/bookings")}
        className="text-neutral-600 hover:text-neutral-900 mb-6 capitalize"
      >
        Back to Bookings
      </Button>

      <Box className="space-y-6">
        <Box className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <Box>
            <Typography variant="h4" className="font-bold text-neutral-900">
              {t("detail.title")}
            </Typography>
            <Typography variant="body2" className="text-neutral-500 font-mono">
              Ref: {booking.id.slice(0, 8).toUpperCase()}
            </Typography>
          </Box>
          <Box className="flex items-center gap-3">
            <BookingStatusChip status={booking.status} />
            {isUpcoming && (
              <Button
                variant="outlined"
                color="error"
                size="small"
                onClick={() => setDialogOpen(true)}
                className="rounded-xl capitalize"
              >
                {t("history.cancel")}
              </Button>
            )}
          </Box>
        </Box>

        <Card className="rounded-2xl border border-neutral-200 shadow-sm overflow-hidden">
          <CardContent className="p-6 space-y-6">
            <Typography variant="h6" className="font-bold text-neutral-900">
              {t("detail.scheduledFor")}
            </Typography>

            <Box className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 bg-teal-50/60 rounded-xl border border-teal-100">
              <Box className="flex items-center gap-3">
                <FiCalendar className="w-5 h-5 text-teal-600" />
                <Box>
                  <Typography
                    variant="caption"
                    className="text-neutral-500 block"
                  >
                    {t("summary.date")}
                  </Typography>
                  <Typography
                    variant="body2"
                    className="font-semibold text-neutral-900"
                  >
                    {formattedDate}
                  </Typography>
                </Box>
              </Box>

              <Box className="flex items-center gap-3">
                <FiClock className="w-5 h-5 text-teal-600" />
                <Box>
                  <Typography
                    variant="caption"
                    className="text-neutral-500 block"
                  >
                    {t("summary.time")}
                  </Typography>
                  <Typography
                    variant="body2"
                    className="font-semibold text-neutral-900"
                  >
                    {formattedTime} (
                    {t("summary.minutes", { count: booking.duration_minutes })})
                  </Typography>
                </Box>
              </Box>

              <Box className="flex items-center gap-3">
                {booking.session_mode === "online" ? (
                  <FiVideo className="w-5 h-5 text-teal-600" />
                ) : (
                  <FiMapPin className="w-5 h-5 text-teal-600" />
                )}
                <Box>
                  <Typography
                    variant="caption"
                    className="text-neutral-500 block"
                  >
                    {t("summary.sessionMode")}
                  </Typography>
                  <Typography
                    variant="body2"
                    className="font-semibold text-neutral-900 capitalize"
                  >
                    {booking.session_mode.replace("_", " ")}
                  </Typography>
                </Box>
              </Box>
            </Box>

            {booking.session_mode === "online" && (
              <Box className="p-4 bg-teal-50/80 rounded-xl border border-teal-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <Box className="space-y-0.5">
                  <Typography
                    variant="subtitle2"
                    className="font-bold text-teal-950 flex items-center gap-2"
                  >
                    <FiVideo className="text-teal-600 w-5 h-5" />
                    Google Meet Video Consultation
                  </Typography>
                  <Typography variant="caption" className="text-teal-800">
                    Join link generated automatically for your online therapy
                    session.
                  </Typography>
                </Box>
                <JoinMeetingButton
                  sessionId={booking.session_id || ""}
                  sessionMode={booking.session_mode}
                  meeting={booking.meeting}
                />
              </Box>
            )}

            <Divider />

            <Box className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Box className="space-y-2">
                <Typography
                  variant="subtitle2"
                  className="font-bold text-neutral-900"
                >
                  {t("detail.therapistDetails")}
                </Typography>
                <Typography
                  variant="body2"
                  className="font-semibold text-teal-800"
                >
                  {booking.therapist.display_name}
                </Typography>
                <Typography variant="body2" className="text-neutral-600">
                  {booking.therapist.designation}
                </Typography>
                <Typography
                  variant="caption"
                  className="text-neutral-500 capitalize block"
                >
                  Specialization:{" "}
                  {booking.therapist.specialization.replace("_", " ")}
                </Typography>
              </Box>

              <Box className="space-y-2">
                <Typography
                  variant="subtitle2"
                  className="font-bold text-neutral-900"
                >
                  {t("detail.clientDetails")}
                </Typography>
                <Typography
                  variant="body2"
                  className="font-semibold text-neutral-800"
                >
                  {booking.client.first_name} {booking.client.last_name}
                </Typography>
                {booking.client.email && (
                  <Typography variant="body2" className="text-neutral-600">
                    {booking.client.email}
                  </Typography>
                )}
                {booking.client.phone && (
                  <Typography variant="body2" className="text-neutral-600">
                    {booking.client.phone}
                  </Typography>
                )}
              </Box>
            </Box>

            {booking.notes && (
              <>
                <Divider />
                <Box className="space-y-1">
                  <Typography
                    variant="subtitle2"
                    className="font-bold text-neutral-900"
                  >
                    {t("detail.notes")}
                  </Typography>
                  <Typography
                    variant="body2"
                    className="text-neutral-700 bg-neutral-50 p-3 rounded-lg border border-neutral-200"
                  >
                    {booking.notes}
                  </Typography>
                </Box>
              </>
            )}

            {booking.cancellation_reason && (
              <>
                <Divider />
                <Box className="space-y-1">
                  <Typography
                    variant="subtitle2"
                    className="font-bold text-red-700"
                  >
                    {t("detail.cancellationReason")}
                  </Typography>
                  <Typography
                    variant="body2"
                    className="text-red-800 bg-red-50 p-3 rounded-lg border border-red-200"
                  >
                    {booking.cancellation_reason}
                  </Typography>
                </Box>
              </>
            )}

            <Divider />

            <Box className="flex justify-between items-center text-lg">
              <span className="font-bold text-neutral-900">
                {t("summary.fee")}:
              </span>
              <span className="font-bold text-teal-700 text-xl">
                ₹{booking.pricing.amount}
              </span>
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Cancellation Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="xs"
        fullWidth
        slotProps={{ paper: { className: "rounded-2xl p-2" } }}
      >
        <DialogTitle className="font-bold text-neutral-900">
          {t("history.cancelConfirm")}
        </DialogTitle>
        <DialogContent className="space-y-3 pt-2">
          <TextField
            fullWidth
            multiline
            rows={3}
            label={t("history.cancelReason")}
            placeholder={t("history.cancelReasonPlaceholder")}
            value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
          />
        </DialogContent>
        <DialogActions className="p-4 gap-2">
          <Button
            onClick={() => setDialogOpen(false)}
            variant="outlined"
            className="rounded-xl capitalize text-neutral-600"
          >
            Keep Booking
          </Button>
          <Button
            onClick={handleConfirmCancel}
            variant="contained"
            color="error"
            disabled={isCancelling}
            className="rounded-xl capitalize shadow-none"
          >
            {isCancelling ? "Cancelling..." : t("history.cancel")}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};
