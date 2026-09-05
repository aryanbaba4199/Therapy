import React from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Box,
  CircularProgress,
  Grid,
  Skeleton,
  Typography,
} from "@mui/material";
import { FaCloudSun, FaMoon, FaSun } from "react-icons/fa";
import type { GeneratedSlot, GroupedSlots } from "../types/slot.types";
import { SlotCard } from "./SlotCard";

interface SlotGridProps {
  groupedSlots: GroupedSlots;
  selectedSlot: GeneratedSlot | null;
  onSelectSlot: (slot: GeneratedSlot) => void;
  isLoading: boolean;
  isError: boolean;
}

export const SlotGrid: React.FC<SlotGridProps> = ({
  groupedSlots,
  selectedSlot,
  onSelectSlot,
  isLoading,
  isError,
}) => {
  const { t } = useTranslation(["availability", "common"]);

  if (isLoading) {
    return (
      <Box sx={{ py: 3 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 2 }}>
          <CircularProgress size={20} />
          <Typography variant="body2" color="text.secondary">
            {t("availability:loadingSlots")}
          </Typography>
        </Box>
        <Grid container spacing={1.5}>
          {Array.from({ length: 6 }).map((_, idx) => (
            <Grid key={idx} size={{ xs: 6, sm: 4, md: 3 }}>
              <Skeleton
                variant="rectangular"
                height={44}
                sx={{ borderRadius: 2 }}
              />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  if (isError) {
    return (
      <Alert severity="error" sx={{ my: 2 }}>
        {t("availability:slotsError")}
      </Alert>
    );
  }

  const totalSlots =
    groupedSlots.morning.length +
    groupedSlots.afternoon.length +
    groupedSlots.evening.length;

  if (totalSlots === 0) {
    return (
      <Box
        sx={{
          py: 4,
          px: 2,
          textAlign: "center",
          backgroundColor: "action.hover",
          borderRadius: 2.5,
          my: 2,
        }}
      >
        <Typography
          variant="body1"
          color="text.secondary"
          sx={{ fontWeight: 500 }}
        >
          {t("availability:noSlots")}
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3, my: 2 }}>
      {/* Morning Section */}
      {groupedSlots.morning.length > 0 && (
        <Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
            <FaSun color="#f59e0b" />
            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
              {t("availability:morning")}
            </Typography>
          </Box>
          <Grid container spacing={1.5}>
            {groupedSlots.morning.map((slot) => (
              <Grid key={slot.id} size={{ xs: 6, sm: 4, md: 4 }}>
                <SlotCard
                  slot={slot}
                  isSelected={selectedSlot?.id === slot.id}
                  onSelect={onSelectSlot}
                />
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Afternoon Section */}
      {groupedSlots.afternoon.length > 0 && (
        <Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
            <FaCloudSun color="#3b82f6" />
            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
              {t("availability:afternoon")}
            </Typography>
          </Box>
          <Grid container spacing={1.5}>
            {groupedSlots.afternoon.map((slot) => (
              <Grid key={slot.id} size={{ xs: 6, sm: 4, md: 4 }}>
                <SlotCard
                  slot={slot}
                  isSelected={selectedSlot?.id === slot.id}
                  onSelect={onSelectSlot}
                />
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Evening Section */}
      {groupedSlots.evening.length > 0 && (
        <Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
            <FaMoon color="#6366f1" />
            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
              {t("availability:evening")}
            </Typography>
          </Box>
          <Grid container spacing={1.5}>
            {groupedSlots.evening.map((slot) => (
              <Grid key={slot.id} size={{ xs: 6, sm: 4, md: 4 }}>
                <SlotCard
                  slot={slot}
                  isSelected={selectedSlot?.id === slot.id}
                  onSelect={onSelectSlot}
                />
              </Grid>
            ))}
          </Grid>
        </Box>
      )}
    </Box>
  );
};
