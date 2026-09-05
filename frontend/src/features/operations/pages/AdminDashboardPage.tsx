import React from "react";
import {
  Box,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Grid,
  Typography,
} from "@mui/material";
import {
  FiCalendar,
  FiClock,
  FiCheckCircle,
  FiUsers,
  FiAward,
  FiHelpCircle,
  FiAlertCircle,
  FiDollarSign,
  FiUserPlus,
} from "react-icons/fi";
import { useTranslation } from "react-i18next";
import { useGetDashboardMetricsQuery } from "../api/operations_api";

export const AdminDashboardPage: React.FC = () => {
  const { t } = useTranslation(["operations", "common"]);
  const { data, isLoading } = useGetDashboardMetricsQuery();

  const metrics = data?.data;

  if (isLoading) {
    return (
      <Box className="flex justify-center items-center min-h-[400px]">
        <CircularProgress />
      </Box>
    );
  }

  const metricCards = [
    {
      title: t("operations:metrics.todayBookings"),
      value: metrics?.today_bookings ?? 0,
      icon: <FiCalendar className="w-6 h-6 text-blue-600" />,
      bg: "bg-blue-50 border-blue-200",
    },
    {
      title: t("operations:metrics.upcomingSessions"),
      value: metrics?.upcoming_sessions ?? 0,
      icon: <FiClock className="w-6 h-6 text-teal-600" />,
      bg: "bg-teal-50 border-teal-200",
    },
    {
      title: t("operations:metrics.completedSessions"),
      value: metrics?.completed_sessions ?? 0,
      icon: <FiCheckCircle className="w-6 h-6 text-emerald-600" />,
      bg: "bg-emerald-50 border-emerald-200",
    },
    {
      title: t("operations:metrics.activeTherapists"),
      value: metrics?.active_therapists ?? 0,
      icon: <FiUsers className="w-6 h-6 text-indigo-600" />,
      bg: "bg-indigo-50 border-indigo-200",
    },
    {
      title: t("operations:metrics.pendingVerifications"),
      value: metrics?.pending_verification_therapists ?? 0,
      icon: <FiAward className="w-6 h-6 text-amber-600" />,
      bg: "bg-amber-50 border-amber-200",
    },
    {
      title: t("operations:metrics.pendingTickets"),
      value: metrics?.pending_support_tickets ?? 0,
      icon: <FiHelpCircle className="w-6 h-6 text-rose-600" />,
      bg: "bg-rose-50 border-rose-200",
    },
    {
      title: t("operations:metrics.failedPayments"),
      value: metrics?.failed_payments_count ?? 0,
      icon: <FiAlertCircle className="w-6 h-6 text-red-600" />,
      bg: "bg-red-50 border-red-200",
    },
    {
      title: t("operations:metrics.totalRevenue"),
      value: `₹${((metrics?.total_revenue_minor ?? 0) / 100).toLocaleString("en-IN")}`,
      icon: <FiDollarSign className="w-6 h-6 text-green-600" />,
      bg: "bg-green-50 border-green-200",
    },
    {
      title: t("operations:metrics.newLeads"),
      value: metrics?.new_leads_count ?? 0,
      icon: <FiUserPlus className="w-6 h-6 text-purple-600" />,
      bg: "bg-purple-50 border-purple-200",
    },
  ];

  return (
    <Container maxWidth="lg" className="py-10 space-y-8">
      <div>
        <Typography
          variant="h4"
          className="font-extrabold text-neutral-900 tracking-tight"
        >
          {t("operations:operationsPortal")}
        </Typography>
        <Typography variant="body1" className="text-neutral-500 mt-1">
          Real-time aggregated platform health, activity indicators, and
          operational triage.
        </Typography>
      </div>

      <Grid container spacing={3}>
        {metricCards.map((card, index) => (
          <Grid key={index} size={{ xs: 12, sm: 6, md: 4 }}>
            <Card className={`rounded-2xl border shadow-sm ${card.bg}`}>
              <CardContent className="p-6">
                <Box className="flex items-center justify-between">
                  <div>
                    <Typography
                      variant="caption"
                      className="font-bold text-neutral-500 uppercase tracking-wider"
                    >
                      {card.title}
                    </Typography>
                    <Typography
                      variant="h4"
                      className="font-extrabold text-neutral-900 mt-1"
                    >
                      {card.value}
                    </Typography>
                  </div>
                  <Box className="p-3 bg-white rounded-xl shadow-xs border border-neutral-100">
                    {card.icon}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
};
