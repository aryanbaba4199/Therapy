import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography,
} from "@mui/material";
import { FaCalendarPlus, FaPlus, FaTrash } from "react-icons/fa";
import { useGetMyTherapistProfileQuery } from "../../therapist/api/therapist_api";
import { useDeleteExtraSlotMutation } from "../api/availability_api";
import { ExtraSlotDialog } from "../components/ExtraSlotDialog";
import { WeeklyScheduleEditor } from "../components/WeeklyScheduleEditor";
import { useAvailability } from "../hooks/useAvailability";
import type { ExtraSlot } from "../types/availability.types";

export const AvailabilitySchedulePage: React.FC = () => {
  const { t } = useTranslation(["availability", "common", "therapist"]);
  const [extraSlotModalOpen, setExtraSlotModalOpen] = useState(false);

  const {
    data: myProfileRes,
    isLoading: isProfileLoading,
    isError: isProfileError,
  } = useGetMyTherapistProfileQuery();

  const therapist = myProfileRes?.data;
  const therapistId = therapist?.id ?? "";

  const { availability, extraSlots, isLoading, isError } =
    useAvailability(therapistId);
  const [deleteExtraSlot] = useDeleteExtraSlotMutation();

  if (isProfileLoading || isLoading) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "60vh",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (isProfileError || !therapist) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Alert severity="warning">{t("availability:noAvailability")}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1 }}>
          {t("availability:scheduleManagement")}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {therapist.display_name} • {therapist.designation}
        </Typography>
      </Box>

      {isError && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {t("availability:slotsError")}
        </Alert>
      )}

      <Stack spacing={4}>
        {/* Weekly Recurring Schedule Editor */}
        <WeeklyScheduleEditor
          therapistId={therapistId}
          initialSchedule={availability?.schedule}
        />

        {/* Extra Slots Card */}
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
                  {t("availability:extraSlots")}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {t("availability:addExtraSlot")}
                </Typography>
              </Box>
              <Button
                variant="outlined"
                startIcon={<FaPlus />}
                onClick={() => setExtraSlotModalOpen(true)}
                sx={{ textTransform: "none", fontWeight: 600 }}
              >
                {t("availability:addExtraSlot")}
              </Button>
            </Box>

            <Divider sx={{ mb: 2 }} />

            {extraSlots.length === 0 ? (
              <Box
                sx={{
                  py: 3,
                  textAlign: "center",
                  backgroundColor: "action.hover",
                  borderRadius: 2,
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  {t("availability:noSlots")}
                </Typography>
              </Box>
            ) : (
              <List disablePadding>
                {extraSlots.map((slot: ExtraSlot) => (
                  <ListItem
                    key={slot.id}
                    secondaryAction={
                      <IconButton
                        edge="end"
                        color="error"
                        onClick={() =>
                          deleteExtraSlot({
                            therapistId,
                            slotId: slot.id,
                          })
                        }
                        title={t("availability:removeInterval")}
                      >
                        <FaTrash />
                      </IconButton>
                    }
                    sx={{
                      borderBottom: 1,
                      borderColor: "divider",
                      py: 1.5,
                    }}
                  >
                    <ListItemText
                      primary={
                        <Stack
                          direction="row"
                          spacing={1.5}
                          sx={{ alignItems: "center" }}
                        >
                          <FaCalendarPlus color="#0284c7" />
                          <Typography variant="body1" sx={{ fontWeight: 700 }}>
                            {slot.date} • {slot.start_time} - {slot.end_time}
                          </Typography>

                          <Chip
                            label={t(
                              `therapist:sessionMode.${slot.session_mode}`
                            )}
                            size="small"
                            variant="outlined"
                          />
                        </Stack>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </CardContent>
        </Card>
      </Stack>

      <ExtraSlotDialog
        open={extraSlotModalOpen}
        onClose={() => setExtraSlotModalOpen(false)}
        therapistId={therapistId}
      />
    </Container>
  );
};
