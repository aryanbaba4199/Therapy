import React, { useState } from "react";
import {
  Alert,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { useCreateTicketMutation } from "../api/support_api";
import type { SupportCategory } from "../types/support_types";

interface CreateTicketModalProps {
  open: boolean;
  onClose: () => void;
  defaultCategory?: SupportCategory;
  defaultBookingId?: string;
  defaultSessionId?: string;
  defaultPaymentId?: string;
  onSuccess?: (ticketId: string) => void;
}

const CATEGORIES: SupportCategory[] = [
  "booking",
  "payment",
  "therapist",
  "session",
  "package",
  "account",
  "technical",
  "other",
];

export const CreateTicketModal: React.FC<CreateTicketModalProps> = ({
  open,
  onClose,
  defaultCategory = "technical",
  defaultBookingId,
  defaultSessionId,
  defaultPaymentId,
  onSuccess,
}) => {
  const { t } = useTranslation(["support", "common"]);
  const [category, setCategory] = useState<SupportCategory>(defaultCategory);
  const [subject, setSubject] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [createTicket, { isLoading }] = useCreateTicketMutation();

  const handleSubmit = async () => {
    if (!subject.trim() || !description.trim()) return;
    setErrorMessage(null);

    try {
      const res = await createTicket({
        category,
        subject: subject.trim(),
        description: description.trim(),
        booking_id: defaultBookingId,
        session_id: defaultSessionId,
        payment_id: defaultPaymentId,
      }).unwrap();

      if (onSuccess && res.data) {
        onSuccess(res.data.id);
      }
      onClose();
    } catch (err: unknown) {
      const errorObj = err as { data?: { error?: { message?: string } } };
      setErrorMessage(
        errorObj.data?.error?.message || "Failed to create support ticket."
      );
    }
  };

  return (
    <Dialog
      open={open}
      onClose={!isLoading ? onClose : undefined}
      maxWidth="sm"
      fullWidth
      slotProps={{ paper: { className: "rounded-3xl p-2" } }}
    >
      <DialogTitle className="font-bold text-neutral-900 pb-1">
        {t("support:createTicket")}
      </DialogTitle>
      <DialogContent className="space-y-4 pt-2">
        <Typography variant="body2" className="text-neutral-500">
          Describe the issue you are facing and our support specialists will
          assist you.
        </Typography>

        {errorMessage && (
          <Alert severity="error" className="rounded-2xl">
            {errorMessage}
          </Alert>
        )}

        {/* Category Selector */}
        <FormControl fullWidth size="small">
          <InputLabel id="category-select-label">
            {t("support:category")}
          </InputLabel>
          <Select
            labelId="category-select-label"
            value={category}
            label={t("support:category")}
            onChange={(e) => setCategory(e.target.value as SupportCategory)}
            disabled={isLoading}
            className="rounded-xl"
          >
            {CATEGORIES.map((cat) => (
              <MenuItem key={cat} value={cat}>
                {t(`support:categories.${cat}`, cat)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Subject */}
        <TextField
          fullWidth
          label={t("support:subject")}
          placeholder={t("support:subjectPlaceholder")}
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          disabled={isLoading}
          slotProps={{
            input: {
              className: "rounded-xl",
            },
          }}
        />

        {/* Description */}
        <TextField
          multiline
          rows={5}
          fullWidth
          label={t("support:description")}
          placeholder={t("support:descriptionPlaceholder")}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          disabled={isLoading}
          slotProps={{
            input: {
              className: "rounded-2xl",
            },
          }}
        />
      </DialogContent>
      <DialogActions className="p-4">
        <Button
          onClick={onClose}
          color="inherit"
          disabled={isLoading}
          className="rounded-xl normal-case"
        >
          {t("common:cancel")}
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          color="primary"
          disabled={
            isLoading ||
            subject.trim().length < 3 ||
            description.trim().length < 5
          }
          className="rounded-xl font-bold normal-case px-6"
        >
          {isLoading ? (
            <CircularProgress size={20} color="inherit" />
          ) : (
            t("support:createTicket")
          )}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
