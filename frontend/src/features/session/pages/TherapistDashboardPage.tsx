import React, { useState } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  Grid,
  Radio,
  RadioGroup,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import {
  FiCalendar,
  FiCheckCircle,
  FiClock,
  FiFileText,
  FiPlay,
  FiUserCheck,
  FiVideo,
} from "react-icons/fi";
import {
  useCompleteSessionMutation,
  useGetTherapistDashboardQuery,
  useRecordAttendanceMutation,
  useStartSessionMutation,
} from "../api/session_api";
import {
  AttendanceChip,
  SessionStatusChip,
} from "../components/SessionStatusChip";
import type { AttendanceStatus, SessionResponse } from "../types/session_types";

export const TherapistDashboardPage: React.FC = () => {
  const { t } = useTranslation(["session", "common"]);
  const navigate = useNavigate();

  const { data, isLoading, isError, error, refetch } =
    useGetTherapistDashboardQuery();
  const [startSession, { isLoading: isStarting }] = useStartSessionMutation();
  const [completeSession, { isLoading: isCompleting }] =
    useCompleteSessionMutation();
  const [recordAttendance, { isLoading: isRecordingAttendance }] =
    useRecordAttendanceMutation();

  const [attendanceModalSession, setAttendanceModalSession] =
    useState<SessionResponse | null>(null);
  const [selectedAttendance, setSelectedAttendance] =
    useState<AttendanceStatus>("present");
  const [actionError, setActionError] = useState<string | null>(null);

  const dashboard = data?.data;

  const handleStartSession = async (sessionId: string) => {
    setActionError(null);
    try {
      await startSession(sessionId).unwrap();
      refetch();
    } catch (err: unknown) {
      const errorObj = err as { data?: { error?: { message?: string } } };
      setActionError(
        errorObj.data?.error?.message || t("session:startTooEarly")
      );
    }
  };

  const handleCompleteSession = async (sessionId: string) => {
    setActionError(null);
    try {
      await completeSession(sessionId).unwrap();
      refetch();
    } catch (err: unknown) {
      const errorObj = err as { data?: { error?: { message?: string } } };
      setActionError(
        errorObj.data?.error?.message || "Failed to complete session."
      );
    }
  };

  const handleOpenAttendance = (session: SessionResponse) => {
    setAttendanceModalSession(session);
    setSelectedAttendance(
      session.attendance === "unknown" ? "present" : session.attendance
    );
  };

  const handleSaveAttendance = async () => {
    if (!attendanceModalSession) return;
    setActionError(null);
    try {
      await recordAttendance({
        id: attendanceModalSession.id,
        body: { attendance: selectedAttendance },
      }).unwrap();
      setAttendanceModalSession(null);
      refetch();
    } catch (err: unknown) {
      const errorObj = err as { data?: { error?: { message?: string } } };
      setActionError(
        errorObj.data?.error?.message || "Failed to record attendance."
      );
    }
  };

  if (isLoading) {
    return (
      <Box className="flex justify-center items-center min-h-[60vh]">
        <CircularProgress color="primary" />
      </Box>
    );
  }

  if (isError || !dashboard) {
    const isProfileMissing =
      (error as { status?: number; data?: { error?: { code?: string } } })
        ?.status === 403 ||
      (error as { data?: { error?: { code?: string } } })?.data?.error
        ?.code === "THERAPIST_NOT_FOUND";

    return (
      <Container maxWidth="lg" className="py-12">
        <Box className="text-center py-16 bg-neutral-50 rounded-3xl border border-neutral-200 p-8 max-w-xl mx-auto space-y-4">
          <Typography variant="h6" className="text-neutral-800 font-bold">
            {isProfileMissing
              ? "No Active Therapist Profile Found"
              : "Failed to load therapist dashboard"}
          </Typography>
          <Typography variant="body2" className="text-neutral-500">
            {isProfileMissing
              ? "Your current user account does not have an active therapist profile attached to it. The Therapist Portal is intended for clinical practitioners."
              : "An error occurred while loading your daily agenda. Please try again."}
          </Typography>
          <Box className="flex justify-center gap-3 pt-2">
            {isProfileMissing ? (
              <>
                <Button
                  variant="outlined"
                  onClick={() => navigate("/operations/dashboard")}
                >
                  Operations Hub
                </Button>
                <Button
                  variant="contained"
                  onClick={() => navigate("/admin/therapists/new")}
                >
                  Onboard Therapist
                </Button>
              </>
            ) : (
              <Button
                variant="outlined"
                color="primary"
                onClick={() => refetch()}
              >
                Retry
              </Button>
            )}
          </Box>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" className="py-10 space-y-8">
      {/* Header */}
      <Box className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <Box>
          <Typography
            variant="h4"
            className="font-extrabold text-neutral-900 tracking-tight"
          >
            {t("session:dashboard")}
          </Typography>
          <Typography variant="body1" className="text-neutral-500 mt-1">
            {t("session:dashboardSubtitle")}
          </Typography>
        </Box>
        <Button
          variant="outlined"
          color="primary"
          onClick={() => navigate("/therapist/sessions")}
          className="self-start md:self-auto rounded-xl font-semibold"
        >
          {t("session:upcomingSessions")} &rarr;
        </Button>
      </Box>

      {/* Action Error Alert */}
      {actionError && (
        <Box className="p-4 bg-red-50 text-red-700 rounded-2xl border border-red-200 text-sm flex justify-between items-center">
          <span>{actionError}</span>
          <Button
            size="small"
            color="inherit"
            onClick={() => setActionError(null)}
          >
            Dismiss
          </Button>
        </Box>
      )}

      {/* Metrics Cards */}
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card className="rounded-3xl border border-neutral-200/80 shadow-sm p-2 hover:border-teal-400 transition-all">
            <CardContent className="space-y-2">
              <Box className="flex items-center justify-between">
                <Typography
                  variant="subtitle2"
                  className="font-bold text-neutral-500 uppercase tracking-wider text-xs"
                >
                  {t("session:todayAgenda")}
                </Typography>
                <Box className="w-10 h-10 rounded-2xl bg-teal-50 flex items-center justify-center text-teal-600">
                  <FiCalendar size={20} />
                </Box>
              </Box>
              <Typography variant="h3" className="font-black text-neutral-900">
                {dashboard.today_sessions_count}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 4 }}>
          <Card className="rounded-3xl border border-neutral-200/80 shadow-sm p-2 hover:border-teal-400 transition-all">
            <CardContent className="space-y-2">
              <Box className="flex items-center justify-between">
                <Typography
                  variant="subtitle2"
                  className="font-bold text-neutral-500 uppercase tracking-wider text-xs"
                >
                  {t("session:upcomingSessions")}
                </Typography>
                <Box className="w-10 h-10 rounded-2xl bg-blue-50 flex items-center justify-center text-blue-600">
                  <FiClock size={20} />
                </Box>
              </Box>
              <Typography variant="h3" className="font-black text-neutral-900">
                {dashboard.upcoming_sessions_count}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 4 }}>
          <Card className="rounded-3xl border border-neutral-200/80 shadow-sm p-2 hover:border-teal-400 transition-all">
            <CardContent className="space-y-2">
              <Box className="flex items-center justify-between">
                <Typography
                  variant="subtitle2"
                  className="font-bold text-neutral-500 uppercase tracking-wider text-xs"
                >
                  {t("session:completedSessions")}
                </Typography>
                <Box className="w-10 h-10 rounded-2xl bg-emerald-50 flex items-center justify-center text-emerald-600">
                  <FiCheckCircle size={20} />
                </Box>
              </Box>
              <Typography variant="h3" className="font-black text-neutral-900">
                {dashboard.completed_sessions_count}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Today's Agenda Section */}
      <Box className="space-y-4">
        <Box className="flex items-center justify-between">
          <Typography variant="h5" className="font-bold text-neutral-900">
            {t("session:todayAgenda")}
          </Typography>
          <Typography variant="body2" className="text-neutral-500">
            {new Date().toLocaleDateString(undefined, {
              weekday: "long",
              year: "numeric",
              month: "short",
              day: "numeric",
            })}
          </Typography>
        </Box>

        {dashboard.today_sessions.length === 0 ? (
          <Box className="text-center py-16 bg-neutral-50 rounded-3xl border border-dashed border-neutral-200">
            <FiCalendar size={36} className="mx-auto text-neutral-400 mb-3" />
            <Typography
              variant="body1"
              className="text-neutral-600 font-medium"
            >
              {t("session:noTodaySessions")}
            </Typography>
          </Box>
        ) : (
          <Box className="space-y-3">
            {dashboard.today_sessions.map((sess) => {
              const startDate = new Date(sess.scheduled_start_at);
              const endDate = new Date(sess.scheduled_end_at);
              const formattedTime = `${startDate.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })} - ${endDate.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}`;

              return (
                <Card
                  key={sess.id}
                  className="rounded-2xl border border-neutral-200/90 shadow-sm p-2 hover:shadow transition-all"
                >
                  <CardContent className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-4">
                    <Box className="space-y-2">
                      <Box className="flex items-center gap-2 flex-wrap">
                        <SessionStatusChip status={sess.status} />
                        <AttendanceChip attendance={sess.attendance} />
                        <span className="text-xs text-neutral-400 font-mono">
                          ID: {sess.id.slice(-6).toUpperCase()}
                        </span>
                      </Box>
                      <Box className="flex items-center gap-4 text-sm text-neutral-600">
                        <Box className="flex items-center gap-1 font-semibold text-neutral-900">
                          <FiClock className="text-teal-600" />
                          <span>{formattedTime}</span>
                        </Box>
                        <Box className="flex items-center gap-1">
                          <FiVideo className="text-neutral-400" />
                          <span className="capitalize">
                            {sess.session_mode}
                          </span>
                        </Box>
                        <span>{sess.duration_minutes} mins</span>
                      </Box>
                    </Box>

                    {/* Action Controls */}
                    <Box className="flex items-center gap-2 flex-wrap self-end md:self-auto">
                      {(sess.status === "scheduled" ||
                        sess.status === "ready") && (
                        <Button
                          variant="contained"
                          color="primary"
                          size="small"
                          startIcon={<FiPlay />}
                          onClick={() => handleStartSession(sess.id)}
                          disabled={isStarting}
                          className="rounded-xl normal-case font-bold"
                        >
                          {t("session:startSession")}
                        </Button>
                      )}

                      {sess.status === "in_progress" && (
                        <Button
                          variant="contained"
                          color="success"
                          size="small"
                          startIcon={<FiCheckCircle />}
                          onClick={() => handleCompleteSession(sess.id)}
                          disabled={isCompleting}
                          className="rounded-xl normal-case font-bold"
                        >
                          {t("session:completeSession")}
                        </Button>
                      )}

                      <Button
                        variant="outlined"
                        color="inherit"
                        size="small"
                        startIcon={<FiUserCheck />}
                        onClick={() => handleOpenAttendance(sess)}
                        className="rounded-xl normal-case"
                      >
                        {t("session:attendance")}
                      </Button>

                      <Button
                        variant="outlined"
                        color="primary"
                        size="small"
                        startIcon={<FiFileText />}
                        onClick={() =>
                          navigate(`/therapist/sessions/${sess.id}`)
                        }
                        className="rounded-xl normal-case font-medium"
                      >
                        {t("session:clinicalNotes")}
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              );
            })}
          </Box>
        )}
      </Box>

      {/* Attendance Recording Dialog */}
      <Dialog
        open={Boolean(attendanceModalSession)}
        onClose={() => setAttendanceModalSession(null)}
        maxWidth="xs"
        fullWidth
        slotProps={{ paper: { className: "rounded-3xl p-2" } }}
      >
        <DialogTitle className="font-bold text-neutral-900">
          {t("session:recordAttendance")}
        </DialogTitle>
        <DialogContent className="pt-2">
          <FormControl component="fieldset">
            <RadioGroup
              value={selectedAttendance}
              onChange={(e) =>
                setSelectedAttendance(e.target.value as AttendanceStatus)
              }
            >
              <FormControlLabel
                value="present"
                control={<Radio color="primary" />}
                label={t("session:attendanceStatus.present")}
              />
              <FormControlLabel
                value="absent"
                control={<Radio color="error" />}
                label={t("session:attendanceStatus.absent")}
              />
              <FormControlLabel
                value="late"
                control={<Radio color="warning" />}
                label={t("session:attendanceStatus.late")}
              />
            </RadioGroup>
          </FormControl>
        </DialogContent>
        <DialogActions className="p-4">
          <Button
            onClick={() => setAttendanceModalSession(null)}
            color="inherit"
            className="normal-case rounded-xl"
          >
            {t("common:cancel")}
          </Button>
          <Button
            onClick={handleSaveAttendance}
            variant="contained"
            color="primary"
            disabled={isRecordingAttendance}
            className="normal-case rounded-xl font-bold"
          >
            {isRecordingAttendance ? (
              <CircularProgress size={20} color="inherit" />
            ) : (
              t("common:save")
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};
