import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  CircularProgress,
  FormControlLabel,
  FormGroup,
  IconButton,
  Paper,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import { FaPlus, FaSave, FaTrash } from "react-icons/fa";
import type { SessionMode } from "../../therapist/types/therapist.types";
import { useSetWeeklyScheduleMutation } from "../api/availability_api";
import type {
  DayOfWeek,
  DaySchedule,
  WeeklySchedule,
} from "../types/availability.types";

interface WeeklyScheduleEditorProps {
  therapistId: string;
  initialSchedule?: WeeklySchedule | null;
}

export const WeeklyScheduleEditor: React.FC<WeeklyScheduleEditorProps> = ({
  therapistId,
  initialSchedule,
}) => {
  const { t } = useTranslation(["availability", "common", "therapist"]);
  const [activeDay, setActiveDay] = useState<DayOfWeek>(0);
  const [timezone, setTimezone] = useState<string>(
    initialSchedule?.timezone ?? "Asia/Kolkata"
  );
  const [saveStatus, setSaveStatus] = useState<"idle" | "success" | "error">(
    "idle"
  );

  const [days, setDays] = useState<DaySchedule[]>(() => {
    if (initialSchedule?.days && initialSchedule.days.length > 0) {
      return initialSchedule.days;
    }
    // Default empty schedule with all 7 days
    return Array.from({ length: 7 }).map((_, i) => ({
      day_of_week: i as DayOfWeek,
      intervals:
        i < 5
          ? [
              {
                start_time: "09:00",
                end_time: "17:00",
                session_modes: ["online" as SessionMode],
              },
            ]
          : [],
    }));
  });

  const [setWeeklySchedule, { isLoading }] = useSetWeeklyScheduleMutation();

  const currentDaySchedule = days.find((d) => d.day_of_week === activeDay) ?? {
    day_of_week: activeDay,
    intervals: [],
  };

  const handleAddInterval = () => {
    setDays((prev) =>
      prev.map((d) => {
        if (d.day_of_week === activeDay) {
          return {
            ...d,
            intervals: [
              ...d.intervals,
              {
                start_time: "09:00",
                end_time: "12:00",
                session_modes: ["online" as SessionMode],
              },
            ],
          };
        }
        return d;
      })
    );
  };

  const handleRemoveInterval = (index: number) => {
    setDays((prev) =>
      prev.map((d) => {
        if (d.day_of_week === activeDay) {
          return {
            ...d,
            intervals: d.intervals.filter((_, i) => i !== index),
          };
        }
        return d;
      })
    );
  };

  const handleIntervalChange = (
    index: number,
    field: "start_time" | "end_time",
    value: string
  ) => {
    setDays((prev) =>
      prev.map((d) => {
        if (d.day_of_week === activeDay) {
          const updated = [...d.intervals];
          const curr = updated[index];
          if (curr) {
            updated[index] = { ...curr, [field]: value };
          }
          return { ...d, intervals: updated };
        }
        return d;
      })
    );
  };

  const handleModeToggle = (index: number, mode: SessionMode) => {
    setDays((prev) =>
      prev.map((d) => {
        if (d.day_of_week === activeDay) {
          const updated = [...d.intervals];
          const curr = updated[index];
          if (curr) {
            const hasMode = curr.session_modes.includes(mode);
            const nextModes = hasMode
              ? curr.session_modes.filter((m) => m !== mode)
              : [...curr.session_modes, mode];
            updated[index] = { ...curr, session_modes: nextModes };
          }
          return { ...d, intervals: updated };
        }
        return d;
      })
    );
  };

  const handleSave = async () => {
    setSaveStatus("idle");
    try {
      await setWeeklySchedule({
        therapistId,
        payload: {
          timezone,
          days,
        },
      }).unwrap();
      setSaveStatus("success");
    } catch {
      setSaveStatus("error");
    }
  };

  const availableModes: SessionMode[] = [
    "online",
    "offline_bangalore",
    "offline_kozhikode",
  ];

  return (
    <Card sx={{ borderRadius: 3, boxShadow: 2 }}>
      <CardContent sx={{ p: { xs: 2.5, md: 4 } }}>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: 3,
          }}
        >
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 800 }}>
              {t("availability:recurringSchedule")}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t("availability:configureHours")}
            </Typography>
          </Box>
          <TextField
            label={t("availability:timezone")}
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            size="small"
            sx={{ width: 180 }}
          />
        </Box>

        {saveStatus === "success" && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {t("availability:scheduleSaved")}
          </Alert>
        )}
        {saveStatus === "error" && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {t("availability:scheduleSaveFailed")}
          </Alert>
        )}

        <Tabs
          value={activeDay}
          onChange={(_e, v: number) => setActiveDay(v as DayOfWeek)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ borderBottom: 1, borderColor: "divider", mb: 3 }}
        >
          {Array.from({ length: 7 }).map((_, i) => (
            <Tab
              key={i}
              label={t(`availability:days.${i}`)}
              sx={{ fontWeight: 700, textTransform: "none" }}
            />
          ))}
        </Tabs>

        {currentDaySchedule.intervals.length === 0 ? (
          <Box
            sx={{
              py: 4,
              textAlign: "center",
              backgroundColor: "action.hover",
              borderRadius: 2,
              mb: 3,
            }}
          >
            <Typography variant="body2" color="text.secondary">
              {t("availability:noAvailability")}
            </Typography>
          </Box>
        ) : (
          <Stack spacing={2} sx={{ mb: 3 }}>
            {currentDaySchedule.intervals.map((interval, idx) => (
              <Paper
                key={idx}
                variant="outlined"
                sx={{
                  p: 2.5,
                  borderRadius: 2.5,
                  display: "flex",
                  flexDirection: { xs: "column", md: "row" },
                  gap: 2,
                  alignItems: { xs: "stretch", md: "center" },
                }}
              >
                <Box sx={{ display: "flex", gap: 1.5, flexGrow: 1 }}>
                  <TextField
                    type="time"
                    size="small"
                    label={t("availability:startTime")}
                    value={interval.start_time}
                    onChange={(e) =>
                      handleIntervalChange(idx, "start_time", e.target.value)
                    }
                    slotProps={{ inputLabel: { shrink: true } }}
                  />
                  <TextField
                    type="time"
                    size="small"
                    label={t("availability:endTime")}
                    value={interval.end_time}
                    onChange={(e) =>
                      handleIntervalChange(idx, "end_time", e.target.value)
                    }
                    slotProps={{ inputLabel: { shrink: true } }}
                  />
                </Box>

                <FormGroup row sx={{ gap: 1 }}>
                  {availableModes.map((mode) => (
                    <FormControlLabel
                      key={mode}
                      control={
                        <Checkbox
                          size="small"
                          checked={interval.session_modes.includes(mode)}
                          onChange={() => handleModeToggle(idx, mode)}
                        />
                      }
                      label={
                        <Typography variant="caption" sx={{ fontWeight: 600 }}>
                          {t(`therapist:sessionMode.${mode}`)}
                        </Typography>
                      }
                    />
                  ))}
                </FormGroup>

                <IconButton
                  color="error"
                  size="small"
                  onClick={() => handleRemoveInterval(idx)}
                  title={t("availability:removeInterval")}
                >
                  <FaTrash />
                </IconButton>
              </Paper>
            ))}
          </Stack>
        )}

        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Button
            variant="outlined"
            startIcon={<FaPlus />}
            onClick={handleAddInterval}
            sx={{ textTransform: "none", fontWeight: 600 }}
          >
            {t("availability:addInterval")}
          </Button>

          <Button
            variant="contained"
            color="primary"
            startIcon={isLoading ? <CircularProgress size={16} /> : <FaSave />}
            disabled={isLoading}
            onClick={handleSave}
            sx={{ textTransform: "none", fontWeight: 700, px: 3 }}
          >
            {t("availability:saveSchedule")}
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};
