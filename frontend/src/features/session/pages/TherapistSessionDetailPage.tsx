import React, { useState } from "react";
import {
  Alert,
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
  Divider,
  FormControl,
  FormControlLabel,
  Radio,
  RadioGroup,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";
import {
  FiArrowLeft,
  FiCalendar,
  FiCheckCircle,
  FiClock,
  FiLock,
  FiPlay,
  FiPlus,
  FiSave,
  FiTarget,
  FiUserCheck,
  FiVideo,
} from "react-icons/fi";
import {
  useCompleteSessionMutation,
  useCreateGoalMutation,
  useGetSessionByIdQuery,
  useGetSessionNoteQuery,
  useListGoalsQuery,
  useRecordAttendanceMutation,
  useStartSessionMutation,
  useUpdateGoalMutation,
  useUpsertSessionNoteMutation,
} from "../api/session_api";
import {
  AttendanceChip,
  SessionStatusChip,
} from "../components/SessionStatusChip";
import { JoinMeetingButton } from "../components/JoinMeetingButton";
import type { AttendanceStatus, GoalStatus } from "../types/session_types";

export const TherapistSessionDetailPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { t } = useTranslation(["session", "common"]);
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<number>(0);

  // Queries
  const {
    data: sessionData,
    isLoading: isSessionLoading,
    refetch: refetchSession,
  } = useGetSessionByIdQuery(sessionId || "", { skip: !sessionId });

  const {
    data: noteData,
    isLoading: isNoteLoading,
    refetch: refetchNote,
  } = useGetSessionNoteQuery(sessionId || "", { skip: !sessionId });

  const {
    data: goalsData,
    isLoading: isGoalsLoading,
    refetch: refetchGoals,
  } = useListGoalsQuery(sessionId || "", { skip: !sessionId });

  // Mutations
  const [startSession, { isLoading: isStarting }] = useStartSessionMutation();
  const [completeSession, { isLoading: isCompleting }] =
    useCompleteSessionMutation();
  const [recordAttendance, { isLoading: isRecordingAttendance }] =
    useRecordAttendanceMutation();
  const [upsertNote, { isLoading: isSavingNote }] =
    useUpsertSessionNoteMutation();
  const [createGoal, { isLoading: isCreatingGoal }] = useCreateGoalMutation();
  const [updateGoal, { isLoading: isUpdatingGoal }] = useUpdateGoalMutation();

  // Local State
  const [summaryText, setSummaryText] = useState<string | null>(null);
  const [privateNotesText, setPrivateNotesText] = useState<string | null>(null);
  const [noteSaveSuccess, setNoteSaveSuccess] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Attendance Dialog State
  const [attendanceDialogOpen, setAttendanceDialogOpen] = useState(false);
  const [selectedAttendance, setSelectedAttendance] =
    useState<AttendanceStatus>("present");

  // Add Goal Dialog State
  const [addGoalOpen, setAddGoalOpen] = useState(false);
  const [goalTitle, setGoalTitle] = useState("");
  const [goalDescription, setGoalDescription] = useState("");

  const session = sessionData?.data;
  const existingNote = noteData?.data;
  const goals = goalsData?.data || [];

  // Initialize note state once fetched
  const currentSummary =
    summaryText !== null ? summaryText : existingNote?.summary || "";
  const currentPrivateNotes =
    privateNotesText !== null
      ? privateNotesText
      : existingNote?.private_notes || "";

  const handleStartSession = async () => {
    if (!sessionId) return;
    setActionError(null);
    try {
      await startSession(sessionId).unwrap();
      refetchSession();
    } catch (err: unknown) {
      const errorObj = err as { data?: { error?: { message?: string } } };
      setActionError(
        errorObj.data?.error?.message || t("session:startTooEarly")
      );
    }
  };

  const handleCompleteSession = async () => {
    if (!sessionId) return;
    setActionError(null);
    try {
      await completeSession(sessionId).unwrap();
      refetchSession();
    } catch (err: unknown) {
      const errorObj = err as { data?: { error?: { message?: string } } };
      setActionError(
        errorObj.data?.error?.message || "Failed to complete session."
      );
    }
  };

  const handleOpenAttendance = () => {
    if (session) {
      setSelectedAttendance(
        session.attendance === "unknown" ? "present" : session.attendance
      );
    }
    setAttendanceDialogOpen(true);
  };

  const handleSaveAttendance = async () => {
    if (!sessionId) return;
    setActionError(null);
    try {
      await recordAttendance({
        id: sessionId,
        body: { attendance: selectedAttendance },
      }).unwrap();
      setAttendanceDialogOpen(false);
      refetchSession();
    } catch (err: unknown) {
      const errorObj = err as { data?: { error?: { message?: string } } };
      setActionError(
        errorObj.data?.error?.message || "Failed to record attendance."
      );
    }
  };

  const handleSaveNotes = async () => {
    if (!sessionId) return;
    setActionError(null);
    setNoteSaveSuccess(false);
    try {
      await upsertNote({
        sessionId,
        body: {
          summary: currentSummary,
          private_notes: currentPrivateNotes,
        },
      }).unwrap();
      setNoteSaveSuccess(true);
      refetchNote();
    } catch (err: unknown) {
      const errorObj = err as { data?: { error?: { message?: string } } };
      setActionError(
        errorObj.data?.error?.message || "Failed to save clinical notes."
      );
    }
  };

  const handleCreateGoal = async () => {
    if (!sessionId || !goalTitle.trim()) return;
    setActionError(null);
    try {
      await createGoal({
        sessionId,
        body: {
          title: goalTitle.trim(),
          description: goalDescription.trim(),
        },
      }).unwrap();
      setAddGoalOpen(false);
      setGoalTitle("");
      setGoalDescription("");
      refetchGoals();
    } catch (err: unknown) {
      const errorObj = err as { data?: { error?: { message?: string } } };
      setActionError(
        errorObj.data?.error?.message || "Failed to create therapy goal."
      );
    }
  };

  const handleUpdateGoalStatus = async (
    goalId: string,
    newStatus: GoalStatus
  ) => {
    setActionError(null);
    try {
      await updateGoal({
        goalId,
        body: { status: newStatus },
      }).unwrap();
      refetchGoals();
    } catch (err: unknown) {
      const errorObj = err as { data?: { error?: { message?: string } } };
      setActionError(
        errorObj.data?.error?.message || "Failed to update goal status."
      );
    }
  };

  if (isSessionLoading) {
    return (
      <Box className="flex justify-center items-center min-h-[60vh]">
        <CircularProgress color="primary" />
      </Box>
    );
  }

  if (!session) {
    return (
      <Container maxWidth="lg" className="py-12">
        <Box className="text-center py-16 bg-neutral-50 rounded-3xl border border-dashed border-neutral-200">
          <Typography variant="h6" className="text-neutral-700 font-bold mb-2">
            Session not found
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate("/therapist/dashboard")}
            className="rounded-xl"
          >
            {t("session:backToDashboard")}
          </Button>
        </Box>
      </Container>
    );
  }

  const startDate = new Date(session.scheduled_start_at);
  const endDate = new Date(session.scheduled_end_at);
  const formattedDate = startDate.toLocaleDateString(undefined, {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const formattedTime = `${startDate.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  })} - ${endDate.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  })}`;

  return (
    <Container maxWidth="lg" className="py-10 space-y-6">
      {/* Back Button */}
      <Box className="flex items-center gap-2">
        <Button
          startIcon={<FiArrowLeft />}
          onClick={() => navigate("/therapist/dashboard")}
          color="inherit"
          className="normal-case text-neutral-600 rounded-xl"
        >
          {t("session:backToDashboard")}
        </Button>
      </Box>

      {/* Error Alert */}
      {actionError && (
        <Alert
          severity="error"
          onClose={() => setActionError(null)}
          className="rounded-2xl"
        >
          {actionError}
        </Alert>
      )}

      {/* Session Hero Card */}
      <Card className="rounded-3xl border border-neutral-200 shadow-sm overflow-hidden">
        <CardContent className="p-6 md:p-8 space-y-6">
          <Box className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <Box className="space-y-2">
              <Box className="flex items-center gap-3 flex-wrap">
                <Typography
                  variant="h5"
                  className="font-extrabold text-neutral-900"
                >
                  {t("session:sessionDetails")}
                </Typography>
                <SessionStatusChip status={session.status} size="medium" />
                <AttendanceChip attendance={session.attendance} size="medium" />
              </Box>
              <Typography
                variant="body2"
                className="text-neutral-500 font-mono"
              >
                Session ID: {session.id} &bull; Booking ID: {session.booking_id}
              </Typography>
            </Box>

            {/* Action Buttons */}
            <Box className="flex items-center gap-2 flex-wrap">
              {(session.status === "scheduled" ||
                session.status === "ready" ||
                session.status === "in_progress") && (
                <JoinMeetingButton
                  sessionId={session.id}
                  sessionMode={session.session_mode}
                  meeting={session.meeting}
                  size="medium"
                />
              )}

              {(session.status === "scheduled" ||
                session.status === "ready") && (
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<FiPlay />}
                  onClick={handleStartSession}
                  disabled={isStarting}
                  className="rounded-xl normal-case font-bold"
                >
                  {isStarting
                    ? t("session:startingSession")
                    : t("session:startSession")}
                </Button>
              )}

              {session.status === "in_progress" && (
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<FiCheckCircle />}
                  onClick={handleCompleteSession}
                  disabled={isCompleting}
                  className="rounded-xl normal-case font-bold"
                >
                  {isCompleting
                    ? t("session:completingSession")
                    : t("session:completeSession")}
                </Button>
              )}

              <Button
                variant="outlined"
                color="inherit"
                startIcon={<FiUserCheck />}
                onClick={handleOpenAttendance}
                className="rounded-xl normal-case font-semibold"
              >
                {t("session:recordAttendance")}
              </Button>
            </Box>
          </Box>

          <Divider />

          {/* Meta Details */}
          <Box className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <Box className="p-3 bg-neutral-50 rounded-2xl">
              <span className="text-neutral-500 text-xs block mb-1">
                {t("session:scheduledTime")}
              </span>
              <Box className="flex items-center gap-1 font-semibold text-neutral-900">
                <FiCalendar className="text-teal-600" />
                <span>{formattedDate}</span>
              </Box>
              <Box className="flex items-center gap-1 text-neutral-600 text-xs mt-1">
                <FiClock className="text-neutral-400" />
                <span>{formattedTime}</span>
              </Box>
            </Box>

            <Box className="p-3 bg-neutral-50 rounded-2xl">
              <span className="text-neutral-500 text-xs block mb-1">
                {t("session:duration")}
              </span>
              <Typography
                variant="body2"
                className="font-bold text-neutral-900"
              >
                {session.duration_minutes} minutes
              </Typography>
            </Box>

            <Box className="p-3 bg-neutral-50 rounded-2xl">
              <span className="text-neutral-500 text-xs block mb-1">
                {t("session:sessionMode")}
              </span>
              <Box className="flex items-center gap-1 font-bold text-neutral-900 capitalize">
                <FiVideo className="text-teal-600" />
                <span>{session.session_mode}</span>
              </Box>
            </Box>

            <Box className="p-3 bg-neutral-50 rounded-2xl">
              <span className="text-neutral-500 text-xs block mb-1">
                {t("session:client")}
              </span>
              <Typography
                variant="body2"
                className="font-mono text-neutral-800 text-xs truncate"
              >
                {session.client_id}
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Box className="border-b border-neutral-200">
        <Tabs
          value={activeTab}
          onChange={(_e, val: number) => setActiveTab(val)}
          textColor="primary"
          indicatorColor="primary"
        >
          <Tab
            label={t("session:clinicalNotes")}
            className="normal-case font-bold"
          />
          <Tab
            label={t("session:therapyGoals")}
            className="normal-case font-bold"
          />
        </Tabs>
      </Box>

      {/* Tab 0: Clinical Notes */}
      {activeTab === 0 && (
        <Box className="space-y-6">
          {noteSaveSuccess && (
            <Alert
              severity="success"
              onClose={() => setNoteSaveSuccess(false)}
              className="rounded-2xl"
            >
              {t("session:notesSaved")}
            </Alert>
          )}

          {isNoteLoading ? (
            <Box className="flex justify-center py-12">
              <CircularProgress color="primary" />
            </Box>
          ) : (
            <Box className="space-y-6">
              {/* Summary Note (Shared with Client) */}
              <Card className="rounded-3xl border border-neutral-200 shadow-sm p-2">
                <CardContent className="space-y-3">
                  <Box>
                    <Typography
                      variant="h6"
                      className="font-bold text-neutral-900"
                    >
                      {t("session:summaryNote")}
                    </Typography>
                    <Typography
                      variant="body2"
                      className="text-neutral-500 text-xs mt-0.5"
                    >
                      Visible to the client in their session overview and
                      consultation history.
                    </Typography>
                  </Box>
                  <TextField
                    multiline
                    rows={4}
                    fullWidth
                    placeholder={t("session:summaryPlaceholder")}
                    value={currentSummary}
                    onChange={(e) => setSummaryText(e.target.value)}
                    slotProps={{
                      input: {
                        className: "rounded-2xl bg-neutral-50/70",
                      },
                    }}
                  />
                </CardContent>
              </Card>

              {/* Confidential Private Notes (Therapist Only) */}
              <Card className="rounded-3xl border border-amber-200/80 shadow-sm p-2 bg-amber-50/20">
                <CardContent className="space-y-3">
                  <Box className="flex items-center justify-between flex-wrap gap-2">
                    <Box className="flex items-center gap-2">
                      <FiLock className="text-amber-700" size={18} />
                      <Typography
                        variant="h6"
                        className="font-bold text-amber-950"
                      >
                        {t("session:privateNotes")}
                      </Typography>
                    </Box>
                  </Box>

                  {/* Security Notice Banner */}
                  <Box className="p-3 bg-amber-100/70 border border-amber-300 text-amber-950 rounded-2xl text-xs flex items-center gap-2 font-medium">
                    <FiLock size={14} className="shrink-0" />
                    <span>{t("session:privateNotesNotice")}</span>
                  </Box>

                  <TextField
                    multiline
                    rows={6}
                    fullWidth
                    placeholder={t("session:privateNotesPlaceholder")}
                    value={currentPrivateNotes}
                    onChange={(e) => setPrivateNotesText(e.target.value)}
                    slotProps={{
                      input: {
                        className: "rounded-2xl bg-white",
                      },
                    }}
                  />
                </CardContent>
              </Card>

              {/* Save Button */}
              <Box className="flex justify-end">
                <Button
                  variant="contained"
                  color="primary"
                  size="large"
                  startIcon={<FiSave />}
                  onClick={handleSaveNotes}
                  disabled={isSavingNote}
                  className="rounded-2xl px-8 font-bold normal-case shadow-md hover:shadow-lg"
                >
                  {isSavingNote ? (
                    <CircularProgress size={22} color="inherit" />
                  ) : (
                    t("session:saveNotes")
                  )}
                </Button>
              </Box>
            </Box>
          )}
        </Box>
      )}

      {/* Tab 1: Therapy Goals */}
      {activeTab === 1 && (
        <Box className="space-y-6">
          <Box className="flex justify-between items-center">
            <Typography variant="h6" className="font-bold text-neutral-900">
              {t("session:therapyGoals")}
            </Typography>
            <Button
              variant="contained"
              color="primary"
              startIcon={<FiPlus />}
              onClick={() => setAddGoalOpen(true)}
              className="rounded-xl normal-case font-bold"
            >
              {t("session:addGoal")}
            </Button>
          </Box>

          {isGoalsLoading ? (
            <Box className="flex justify-center py-12">
              <CircularProgress color="primary" />
            </Box>
          ) : goals.length === 0 ? (
            <Box className="text-center py-16 bg-neutral-50 rounded-3xl border border-dashed border-neutral-200">
              <FiTarget size={36} className="mx-auto text-neutral-400 mb-3" />
              <Typography
                variant="body1"
                className="text-neutral-600 font-medium"
              >
                No therapy goals defined yet for this consultation.
              </Typography>
            </Box>
          ) : (
            <Box className="space-y-3">
              {goals.map((g) => (
                <Card
                  key={g.id}
                  className="rounded-2xl border border-neutral-200 shadow-sm p-1"
                >
                  <CardContent className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-4">
                    <Box className="space-y-1 flex-1">
                      <Box className="flex items-center gap-2">
                        <Typography
                          variant="subtitle1"
                          className="font-bold text-neutral-900"
                        >
                          {g.title}
                        </Typography>
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                            g.status === "completed"
                              ? "bg-emerald-100 text-emerald-800"
                              : g.status === "archived"
                                ? "bg-neutral-100 text-neutral-600"
                                : "bg-teal-100 text-teal-800"
                          }`}
                        >
                          {t(`session:goalStatus.${g.status}`, g.status)}
                        </span>
                      </Box>
                      {g.description && (
                        <Typography
                          variant="body2"
                          className="text-neutral-600"
                        >
                          {g.description}
                        </Typography>
                      )}
                    </Box>

                    {/* Status change actions */}
                    <Box className="flex items-center gap-2 self-end md:self-auto">
                      {g.status !== "completed" && (
                        <Button
                          size="small"
                          variant="outlined"
                          color="success"
                          disabled={isUpdatingGoal}
                          onClick={() =>
                            handleUpdateGoalStatus(g.id, "completed")
                          }
                          className="rounded-xl normal-case"
                        >
                          Mark Achieved
                        </Button>
                      )}
                      {g.status === "completed" && (
                        <Button
                          size="small"
                          variant="outlined"
                          color="primary"
                          disabled={isUpdatingGoal}
                          onClick={() => handleUpdateGoalStatus(g.id, "active")}
                          className="rounded-xl normal-case"
                        >
                          Reopen Goal
                        </Button>
                      )}
                      {g.status !== "archived" && (
                        <Button
                          size="small"
                          variant="text"
                          color="inherit"
                          disabled={isUpdatingGoal}
                          onClick={() =>
                            handleUpdateGoalStatus(g.id, "archived")
                          }
                          className="rounded-xl normal-case text-neutral-400 hover:text-neutral-700"
                        >
                          Archive
                        </Button>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}
        </Box>
      )}

      {/* Attendance Recording Dialog */}
      <Dialog
        open={attendanceDialogOpen}
        onClose={() => setAttendanceDialogOpen(false)}
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
            onClick={() => setAttendanceDialogOpen(false)}
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

      {/* Add Therapy Goal Dialog */}
      <Dialog
        open={addGoalOpen}
        onClose={() => setAddGoalOpen(false)}
        maxWidth="sm"
        fullWidth
        slotProps={{ paper: { className: "rounded-3xl p-2" } }}
      >
        <DialogTitle className="font-bold text-neutral-900">
          {t("session:addGoal")}
        </DialogTitle>
        <DialogContent className="space-y-4 pt-2">
          <TextField
            autoFocus
            fullWidth
            label={t("session:goalTitle")}
            placeholder={t("session:goalTitlePlaceholder")}
            value={goalTitle}
            onChange={(e) => setGoalTitle(e.target.value)}
            slotProps={{ input: { className: "rounded-xl" } }}
          />
          <TextField
            multiline
            rows={3}
            fullWidth
            label={t("session:goalDescription")}
            placeholder={t("session:goalDescriptionPlaceholder")}
            value={goalDescription}
            onChange={(e) => setGoalDescription(e.target.value)}
            slotProps={{ input: { className: "rounded-xl" } }}
          />
        </DialogContent>
        <DialogActions className="p-4">
          <Button
            onClick={() => setAddGoalOpen(false)}
            color="inherit"
            className="normal-case rounded-xl"
          >
            {t("common:cancel")}
          </Button>
          <Button
            onClick={handleCreateGoal}
            variant="contained"
            color="primary"
            disabled={isCreatingGoal || !goalTitle.trim()}
            className="normal-case rounded-xl font-bold"
          >
            {isCreatingGoal ? (
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
