import React from "react";
import { Chip } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { BookingStatus } from "../types/booking.types";

interface BookingStatusChipProps {
  status: BookingStatus;
}

export const BookingStatusChip: React.FC<BookingStatusChipProps> = ({
  status,
}) => {
  const { t } = useTranslation("booking");

  const getColor = (
    st: BookingStatus
  ):
    | "default"
    | "primary"
    | "secondary"
    | "error"
    | "info"
    | "success"
    | "warning" => {
    switch (st) {
      case "confirmed":
        return "success";
      case "pending":
        return "warning";
      case "cancelled":
        return "error";
      case "completed":
        return "info";
      case "no_show":
        return "default";
      default:
        return "default";
    }
  };

  return (
    <Chip
      size="small"
      label={t(`status.${status}`, { defaultValue: status })}
      color={getColor(status)}
      className="font-medium"
    />
  );
};
