import React from "react";
import { Chip } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { AttendanceStatus, SessionStatus } from "../types/session_types";

interface SessionStatusChipProps {
  status: SessionStatus;
  size?: "small" | "medium";
}

export const SessionStatusChip: React.FC<SessionStatusChipProps> = ({
  status,
  size = "small",
}) => {
  const { t } = useTranslation("session");

  let color:
    | "default"
    | "primary"
    | "secondary"
    | "error"
    | "info"
    | "success"
    | "warning" = "default";

  switch (status) {
    case "scheduled":
      color = "info";
      break;
    case "ready":
      color = "warning";
      break;
    case "in_progress":
      color = "primary";
      break;
    case "completed":
      color = "success";
      break;
    case "cancelled":
    case "no_show":
      color = "error";
      break;
  }

  return (
    <Chip
      label={t(`statusValues.${status}`, status)}
      color={color}
      size={size}
      variant={status === "in_progress" ? "filled" : "outlined"}
      className="font-medium"
    />
  );
};

interface AttendanceChipProps {
  attendance: AttendanceStatus;
  size?: "small" | "medium";
}

const getAttendanceColor = (
  attendance: AttendanceStatus
): "default" | "success" | "error" | "warning" => {
  switch (attendance) {
    case "present":
      return "success";
    case "absent":
      return "error";
    case "late":
      return "warning";
    default:
      return "default";
  }
};

export const AttendanceChip: React.FC<AttendanceChipProps> = ({
  attendance,
  size = "small",
}) => {
  const { t } = useTranslation("session");
  const color = getAttendanceColor(attendance);

  return (
    <Chip
      label={t(`attendanceStatus.${attendance}`, attendance)}
      color={color}
      size={size}
      variant="outlined"
      className="text-xs"
    />
  );
};
