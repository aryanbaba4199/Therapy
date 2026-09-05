import React from "react";
import { Button, Typography } from "@mui/material";
import { FaClock } from "react-icons/fa";
import type { GeneratedSlot } from "../types/slot.types";

interface SlotCardProps {
  slot: GeneratedSlot;
  isSelected: boolean;
  onSelect: (slot: GeneratedSlot) => void;
}

export const SlotCard: React.FC<SlotCardProps> = ({
  slot,
  isSelected,
  onSelect,
}) => {
  const formatTime = (isoString: string): string => {
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      });
    } catch {
      return isoString;
    }
  };

  const startFormatted = formatTime(slot.start_at);
  const endFormatted = formatTime(slot.end_at);

  return (
    <Button
      variant={isSelected ? "contained" : "outlined"}
      color={isSelected ? "primary" : "inherit"}
      onClick={() => onSelect(slot)}
      aria-pressed={isSelected}
      startIcon={<FaClock />}
      sx={{
        py: 1.25,
        px: 2,
        borderRadius: 2,
        textTransform: "none",
        fontWeight: isSelected ? 700 : 500,
        borderColor: isSelected ? "primary.main" : "divider",
        backgroundColor: isSelected ? "primary.main" : "background.paper",
        color: isSelected ? "primary.contrastText" : "text.primary",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        boxShadow: isSelected ? 2 : 0,
        "&:hover": {
          backgroundColor: isSelected ? "primary.dark" : "action.hover",
          borderColor: "primary.main",
        },
      }}
    >
      <Typography variant="body2" sx={{ fontWeight: "inherit" }}>
        {startFormatted} – {endFormatted}
      </Typography>
    </Button>
  );
};
