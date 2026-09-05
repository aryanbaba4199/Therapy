import React from "react";
import { Chip } from "@mui/material";
import { useTranslation } from "react-i18next";
import type {
  SupportPriority,
  SupportTicketStatus,
} from "../types/support_types";

interface TicketStatusChipProps {
  status: SupportTicketStatus;
  size?: "small" | "medium";
}

const getStatusColor = (
  status: SupportTicketStatus
):
  | "default"
  | "primary"
  | "secondary"
  | "error"
  | "info"
  | "success"
  | "warning" => {
  switch (status) {
    case "open":
      return "info";
    case "in_progress":
      return "primary";
    case "waiting_for_user":
      return "warning";
    case "resolved":
      return "success";
    case "closed":
      return "default";
    default:
      return "default";
  }
};

export const TicketStatusChip: React.FC<TicketStatusChipProps> = ({
  status,
  size = "small",
}) => {
  const { t } = useTranslation("support");
  const color = getStatusColor(status);

  return (
    <Chip
      label={t(`statuses.${status}`, status)}
      color={color}
      size={size}
      variant={status === "in_progress" ? "filled" : "outlined"}
      className="font-medium"
    />
  );
};

interface TicketPriorityChipProps {
  priority: SupportPriority;
  size?: "small" | "medium";
}

const getPriorityColor = (
  priority: SupportPriority
):
  | "default"
  | "primary"
  | "secondary"
  | "error"
  | "info"
  | "success"
  | "warning" => {
  switch (priority) {
    case "low":
      return "default";
    case "normal":
      return "info";
    case "high":
      return "warning";
    case "urgent":
      return "error";
    default:
      return "default";
  }
};

export const TicketPriorityChip: React.FC<TicketPriorityChipProps> = ({
  priority,
  size = "small",
}) => {
  const { t } = useTranslation("support");
  const color = getPriorityColor(priority);

  return (
    <Chip
      label={t(`priorities.${priority}`, priority)}
      color={color}
      size={size}
      variant="outlined"
      className="text-xs uppercase font-semibold tracking-wider"
    />
  );
};
