import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Box,
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
} from "@mui/material";
import type { SessionMode } from "../../therapist/types/therapist.types";
import { useCreateExtraSlotMutation } from "../api/availability_api";

interface ExtraSlotDialogProps {
  open: boolean;
  onClose: () => void;
  therapistId: string;
}

export const ExtraSlotDialog: React.FC<ExtraSlotDialogProps> = ({
  open,
  onClose,
  therapistId,
}) => {
  const { t } = useTranslation(["availability", "common", "therapist"]);
  const [createExtraSlot, { isLoading, error }] = useCreateExtraSlotMutation();

  const [dateStr, setDateStr] = useState<string>(() => {
    return new Date().toISOString().split("T")[0] ?? "";
  });
  const [startTime, setStartTime] = useState<string>("18:00");
  const [endTime, setEndTime] = useState<string>("19:00");
  const [sessionMode, setSessionMode] = useState<SessionMode>("online");
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (startTime >= endTime) {
      setFormError("Start time must be before end time.");
      return;
    }

    try {
      await createExtraSlot({
        therapistId,
        payload: {
          date: dateStr,
          start_time: startTime,
          end_time: endTime,
          session_mode: sessionMode,
        },
      }).unwrap();
      onClose();
    } catch {
      // Handled via RTK Query error state
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle sx={{ fontWeight: 700 }}>
          {t("availability:addExtraSlot")}
        </DialogTitle>
        <DialogContent
          sx={{ display: "flex", flexDirection: "column", gap: 2.5, pt: 1 }}
        >
          {(error || formError) && (
            <Alert severity="error">
              {formError ?? t("availability:scheduleSaveFailed")}
            </Alert>
          )}

          <TextField
            type="date"
            label={t("availability:selectDate")}
            value={dateStr}
            onChange={(e) => setDateStr(e.target.value)}
            slotProps={{ inputLabel: { shrink: true } }}
            fullWidth
            required
          />

          <Box sx={{ display: "flex", gap: 2 }}>
            <TextField
              type="time"
              label={t("availability:startTime")}
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
              fullWidth
              required
            />
            <TextField
              type="time"
              label={t("availability:endTime")}
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
              fullWidth
              required
            />
          </Box>

          <FormControl fullWidth>
            <InputLabel>{t("availability:sessionMode")}</InputLabel>
            <Select
              value={sessionMode}
              label={t("availability:sessionMode")}
              onChange={(e) => setSessionMode(e.target.value as SessionMode)}
            >
              <MenuItem value="online">
                {t("therapist:sessionMode.online")}
              </MenuItem>
              <MenuItem value="offline_bangalore">
                {t("therapist:sessionMode.offline_bangalore")}
              </MenuItem>
              <MenuItem value="offline_kozhikode">
                {t("therapist:sessionMode.offline_kozhikode")}
              </MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={onClose} color="inherit">
            {t("common:cancel", { defaultValue: "Cancel" })}
          </Button>
          <Button
            type="submit"
            variant="contained"
            color="primary"
            disabled={isLoading}
            startIcon={isLoading ? <CircularProgress size={16} /> : undefined}
          >
            {t("common:save", { defaultValue: "Save" })}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};
