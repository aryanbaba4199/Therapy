import React from "react";
import { Button, CircularProgress } from "@mui/material";
import { useTranslation } from "react-i18next";
import { FiRefreshCw, FiVideo } from "react-icons/fi";
import { useRetryMeetingMutation } from "../api/session_api";
import type { SessionMeetingResponse } from "../types/session_types";

interface JoinMeetingButtonProps {
  sessionId: string;
  sessionMode: string;
  meeting?: SessionMeetingResponse | null;
  size?: "small" | "medium" | "large";
  fullWidth?: boolean;
}

export const JoinMeetingButton: React.FC<JoinMeetingButtonProps> = ({
  sessionId,
  sessionMode,
  meeting,
  size = "medium",
  fullWidth = false,
}) => {
  const { t } = useTranslation("session");
  const [retryMeeting, { isLoading: isRetrying }] = useRetryMeetingMutation();

  if (sessionMode !== "online" || meeting?.status === "not_required") {
    return null;
  }

  const handleRetry = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    try {
      await retryMeeting(sessionId).unwrap();
    } catch {
      // Error handling managed through RTK Query cache / notifications
    }
  };

  // State 1: READY with join_url
  if (meeting?.status === "ready" && meeting.join_url) {
    return (
      <Button
        variant="contained"
        color="success"
        size={size}
        fullWidth={fullWidth}
        startIcon={<FiVideo className="text-lg" />}
        component="a"
        href={meeting.join_url}
        target="_blank"
        rel="noopener noreferrer"
        onClick={(e) => e.stopPropagation()}
        className="font-medium shadow-sm hover:shadow"
      >
        {t("joinMeeting", "Join Google Meet")}
      </Button>
    );
  }

  // State 2: FAILED
  if (meeting?.status === "failed") {
    return (
      <Button
        variant="outlined"
        color="error"
        size={size}
        fullWidth={fullWidth}
        disabled={isRetrying}
        startIcon={
          isRetrying ? (
            <CircularProgress size={16} color="inherit" />
          ) : (
            <FiRefreshCw className="text-sm" />
          )
        }
        onClick={handleRetry}
        className="font-medium"
      >
        {isRetrying
          ? t("retryingMeeting", "Retrying...")
          : t("retryMeeting", "Retry Meeting Setup")}
      </Button>
    );
  }

  // State 3: PROCESSING or NOT_STARTED
  return (
    <Button
      variant="outlined"
      color="inherit"
      size={size}
      fullWidth={fullWidth}
      disabled
      startIcon={<CircularProgress size={16} color="inherit" />}
      className="font-medium opacity-75"
    >
      {t("meetingPreparing", "Meeting is being prepared...")}
    </Button>
  );
};
