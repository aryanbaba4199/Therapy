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
  Tab,
  Tabs,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { FiCalendar, FiClock, FiFileText, FiVideo } from "react-icons/fi";
import {
  useGetClientSessionNoteQuery,
  useListMySessionsQuery,
} from "../api/session_api";
import { SessionStatusChip } from "../components/SessionStatusChip";
import type {
  ClientSessionResponse,
  SessionStatus,
} from "../types/session_types";

type ClientTabFilter = "all" | "upcoming" | "completed";

export const ClientSessionHistoryPage: React.FC = () => {
  const { t } = useTranslation(["session", "common"]);
  const [activeTab, setActiveTab] = useState<ClientTabFilter>("all");
  const [selectedSessionForNotes, setSelectedSessionForNotes] =
    useState<ClientSessionResponse | null>(null);

  const statusParam: SessionStatus | undefined =
    activeTab === "upcoming"
      ? "scheduled"
      : activeTab === "completed"
        ? "completed"
        : undefined;

  const { data, isLoading, isError, refetch } = useListMySessionsQuery({
    status: statusParam,
    page: 1,
    limit: 50,
  });

  const sessions = data?.data || [];

  return (
    <Container maxWidth="md" className="py-10 space-y-6">
      {/* Header */}
      <Box>
        <Typography
          variant="h4"
          className="font-extrabold text-neutral-900 tracking-tight"
        >
          {t("session:mySessions")}
        </Typography>
        <Typography variant="body1" className="text-neutral-500 mt-1">
          {t("session:mySessionsSubtitle")}
        </Typography>
      </Box>

      {/* Tabs */}
      <Box className="border-b border-neutral-200">
        <Tabs
          value={activeTab}
          onChange={(_e, val: ClientTabFilter) => setActiveTab(val)}
          textColor="primary"
          indicatorColor="primary"
        >
          <Tab
            value="all"
            label={t("common:all", "All Consultations")}
            className="normal-case font-bold"
          />
          <Tab
            value="upcoming"
            label={t("session:upcomingSessions")}
            className="normal-case font-medium"
          />
          <Tab
            value="completed"
            label={t("session:completedSessions")}
            className="normal-case font-medium"
          />
        </Tabs>
      </Box>

      {/* List */}
      {isLoading ? (
        <Box className="flex justify-center items-center py-24">
          <CircularProgress color="primary" />
        </Box>
      ) : isError ? (
        <Box className="text-center py-16 bg-red-50 rounded-3xl border border-red-100 p-6">
          <Typography variant="h6" className="text-red-700 font-bold mb-2">
            Failed to load sessions
          </Typography>
          <Button variant="outlined" color="primary" onClick={() => refetch()}>
            Retry
          </Button>
        </Box>
      ) : sessions.length === 0 ? (
        <Box className="text-center py-20 bg-neutral-50 rounded-3xl border border-dashed border-neutral-200">
          <FiCalendar size={40} className="mx-auto text-neutral-400 mb-3" />
          <Typography variant="body1" className="text-neutral-600 font-medium">
            {t("session:noSessions")}
          </Typography>
        </Box>
      ) : (
        <Box className="space-y-4">
          {sessions.map((sess) => {
            const startDate = new Date(sess.scheduled_start_at);
            const endDate = new Date(sess.scheduled_end_at);
            const formattedDate = startDate.toLocaleDateString(undefined, {
              weekday: "short",
              month: "short",
              day: "numeric",
              year: "numeric",
            });
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
                className="rounded-2xl border border-neutral-200 shadow-sm hover:shadow transition-all"
              >
                <CardContent className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5">
                  <Box className="space-y-2">
                    <Box className="flex items-center gap-2">
                      <SessionStatusChip status={sess.status} />
                      <span className="text-xs text-neutral-400 font-mono">
                        #{sess.id.slice(-6).toUpperCase()}
                      </span>
                    </Box>
                    <Box className="flex items-center gap-4 text-sm text-neutral-600 flex-wrap">
                      <Box className="flex items-center gap-1 font-semibold text-neutral-900">
                        <FiCalendar className="text-teal-600" />
                        <span>{formattedDate}</span>
                      </Box>
                      <Box className="flex items-center gap-1">
                        <FiClock className="text-neutral-400" />
                        <span>{formattedTime}</span>
                      </Box>
                      <Box className="flex items-center gap-1">
                        <FiVideo className="text-neutral-400" />
                        <span className="capitalize">{sess.session_mode}</span>
                      </Box>
                      <span>{sess.duration_minutes} mins</span>
                    </Box>
                  </Box>

                  {sess.status === "completed" && (
                    <Button
                      variant="outlined"
                      color="primary"
                      size="small"
                      startIcon={<FiFileText />}
                      onClick={() => setSelectedSessionForNotes(sess)}
                      className="rounded-xl normal-case font-semibold shrink-0"
                    >
                      {t("session:summaryNote")}
                    </Button>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </Box>
      )}

      {/* Client Note Modal Dialog (Strictly sanitized summary only) */}
      {selectedSessionForNotes && (
        <ClientSessionNoteModal
          session={selectedSessionForNotes}
          onClose={() => setSelectedSessionForNotes(null)}
        />
      )}
    </Container>
  );
};

interface ClientSessionNoteModalProps {
  session: ClientSessionResponse;
  onClose: () => void;
}

const ClientSessionNoteModal: React.FC<ClientSessionNoteModalProps> = ({
  session,
  onClose,
}) => {
  const { t } = useTranslation(["session", "common"]);
  const { data, isLoading } = useGetClientSessionNoteQuery(session.id);

  const note = data?.data;

  return (
    <Dialog
      open
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      slotProps={{ paper: { className: "rounded-3xl p-2" } }}
    >
      <DialogTitle className="font-bold text-neutral-900">
        {t("session:summaryNote")}
      </DialogTitle>
      <DialogContent className="space-y-4 pt-2">
        {isLoading ? (
          <Box className="flex justify-center py-8">
            <CircularProgress color="primary" />
          </Box>
        ) : note?.summary ? (
          <Box className="p-4 bg-teal-50/50 rounded-2xl border border-teal-100 text-neutral-800 text-sm whitespace-pre-wrap leading-relaxed">
            {note.summary}
          </Box>
        ) : (
          <Alert severity="info" className="rounded-2xl">
            No clinical summary notes have been shared for this session yet.
          </Alert>
        )}
      </DialogContent>
      <DialogActions className="p-4">
        <Button
          onClick={onClose}
          variant="contained"
          color="primary"
          className="rounded-xl normal-case font-bold"
        >
          {t("common:close")}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
