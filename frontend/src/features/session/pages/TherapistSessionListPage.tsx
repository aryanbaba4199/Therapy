import React, { useState } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import {
  FiArrowLeft,
  FiCalendar,
  FiClock,
  FiFileText,
  FiVideo,
} from "react-icons/fi";
import { useListTherapistSessionsQuery } from "../api/session_api";
import {
  AttendanceChip,
  SessionStatusChip,
} from "../components/SessionStatusChip";
import type { SessionStatus } from "../types/session_types";

type StatusFilterTab = "all" | SessionStatus;

export const TherapistSessionListPage: React.FC = () => {
  const { t } = useTranslation(["session", "common"]);
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<StatusFilterTab>("all");
  const [dateFilter, setDateFilter] = useState<string>("");

  const queryParams = {
    status: activeTab === "all" ? undefined : activeTab,
    date_filter: dateFilter.trim() || undefined,
    page: 1,
    limit: 50,
  };

  const { data, isLoading, isError, refetch } =
    useListTherapistSessionsQuery(queryParams);

  const sessions = data?.data || [];

  return (
    <Container maxWidth="lg" className="py-10 space-y-6">
      {/* Breadcrumb / Back button */}
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

      {/* Header */}
      <Box className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <Box>
          <Typography
            variant="h4"
            className="font-extrabold text-neutral-900 tracking-tight"
          >
            {t("session:sessions")}
          </Typography>
          <Typography variant="body1" className="text-neutral-500 mt-1">
            Manage your past and scheduled therapy consultations
          </Typography>
        </Box>

        {/* Date Filter */}
        <Box className="w-full md:w-auto">
          <TextField
            type="date"
            size="small"
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            slotProps={{
              input: {
                className: "rounded-xl bg-white",
              },
            }}
          />
        </Box>
      </Box>

      {/* Status Filter Tabs */}
      <Box className="border-b border-neutral-200">
        <Tabs
          value={activeTab}
          onChange={(_e, val: StatusFilterTab) => setActiveTab(val)}
          variant="scrollable"
          scrollButtons="auto"
          textColor="primary"
          indicatorColor="primary"
        >
          <Tab
            value="all"
            label={t("common:all", "All")}
            className="normal-case font-bold"
          />
          <Tab
            value="scheduled"
            label={t("session:statusValues.scheduled")}
            className="normal-case font-medium"
          />
          <Tab
            value="in_progress"
            label={t("session:statusValues.in_progress")}
            className="normal-case font-medium"
          />
          <Tab
            value="completed"
            label={t("session:statusValues.completed")}
            className="normal-case font-medium"
          />
          <Tab
            value="cancelled"
            label={t("session:statusValues.cancelled")}
            className="normal-case font-medium"
          />
        </Tabs>
      </Box>

      {/* Session List */}
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
        <Box className="space-y-3">
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
                <CardContent className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-4">
                  <Box className="space-y-2">
                    <Box className="flex items-center gap-2 flex-wrap">
                      <SessionStatusChip status={sess.status} />
                      <AttendanceChip attendance={sess.attendance} />
                      <span className="text-xs text-neutral-400 font-mono">
                        ID: {sess.id.slice(-6).toUpperCase()}
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

                  <Button
                    variant="outlined"
                    color="primary"
                    startIcon={<FiFileText />}
                    onClick={() => navigate(`/therapist/sessions/${sess.id}`)}
                    className="rounded-xl normal-case font-semibold self-end md:self-auto"
                  >
                    {t("session:sessionDetails")}
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </Box>
      )}
    </Container>
  );
};
