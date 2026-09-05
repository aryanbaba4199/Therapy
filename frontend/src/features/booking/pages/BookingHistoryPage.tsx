import React, { useState } from "react";
import {
  Box,
  Button,
  CircularProgress,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import {
  useCancelBookingMutation,
  useListBookingsQuery,
} from "../api/booking_api";
import { BookingCard } from "../components/BookingCard";

type TabFilter = "upcoming" | "past" | "cancelled";

export const BookingHistoryPage: React.FC = () => {
  const { t } = useTranslation("booking");
  const [activeTab, setActiveTab] = useState<TabFilter>("upcoming");

  const { data, isLoading, refetch } = useListBookingsQuery({
    filter: activeTab,
    page: 1,
    limit: 20,
  });

  const [cancelBooking, { isLoading: isCancelling }] =
    useCancelBookingMutation();

  const [selectedBookingId, setSelectedBookingId] = useState<string | null>(
    null
  );
  const [cancelReason, setCancelReason] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);

  const bookings = data?.data?.items || [];

  const handleOpenCancelDialog = (bookingId: string) => {
    setSelectedBookingId(bookingId);
    setCancelReason("");
    setDialogOpen(true);
  };

  const handleConfirmCancel = async () => {
    if (!selectedBookingId) return;
    try {
      await cancelBooking({
        bookingId: selectedBookingId,
        payload: { reason: cancelReason.trim() || undefined },
      }).unwrap();
      setDialogOpen(false);
      refetch();
    } catch {
      // Error handled via RTK Query tag invalidation or state
    }
  };

  return (
    <Container maxWidth="md" className="py-10">
      <Typography variant="h4" className="font-bold text-neutral-900 mb-6">
        {t("history.title")}
      </Typography>

      <Box className="border-b border-neutral-200 mb-6">
        <Tabs
          value={activeTab}
          onChange={(_e, val: TabFilter) => setActiveTab(val)}
          textColor="primary"
          indicatorColor="primary"
          className="text-teal-600"
        >
          <Tab
            label={t("history.upcoming")}
            value="upcoming"
            className="capitalize font-semibold"
          />
          <Tab
            label={t("history.past")}
            value="past"
            className="capitalize font-semibold"
          />
          <Tab
            label={t("history.cancelled")}
            value="cancelled"
            className="capitalize font-semibold"
          />
        </Tabs>
      </Box>

      {isLoading ? (
        <Box className="flex justify-center py-16">
          <CircularProgress className="text-teal-600" />
        </Box>
      ) : bookings.length === 0 ? (
        <Box className="text-center py-16 bg-neutral-50 rounded-2xl border border-neutral-200">
          <Typography variant="body1" className="text-neutral-500">
            {t("history.noBookings")}
          </Typography>
        </Box>
      ) : (
        <Box className="space-y-4">
          {bookings.map((booking) => (
            <BookingCard
              key={booking.id}
              booking={booking}
              onCancelClick={handleOpenCancelDialog}
            />
          ))}
        </Box>
      )}

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
          <Typography variant="body2" className="text-neutral-600">
            Please let us know why you need to cancel this appointment.
          </Typography>
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
