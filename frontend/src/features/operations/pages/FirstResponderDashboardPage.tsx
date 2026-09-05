import React from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Grid,
  Typography,
} from "@mui/material";
import {
  FiAlertCircle,
  FiArrowRight,
  FiCheckCircle,
  FiClock,
  FiPhoneCall,
  FiUserPlus,
} from "react-icons/fi";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import {
  useGetDashboardMetricsQuery,
  useListLeadsQuery,
} from "../api/operations_api";
import { useListAllTicketsQuery } from "@/features/support/api/support_api";
import type { SupportTicketResponse } from "@/features/support/types/support_types";

export const FirstResponderDashboardPage: React.FC = () => {
  const { t } = useTranslation(["operations", "support", "common"]);
  const navigate = useNavigate();

  const { data: metricsData, isLoading: isMetricsLoading } =
    useGetDashboardMetricsQuery();
  const { data: leadsData, isLoading: isLeadsLoading } = useListLeadsQuery({
    status: "new",
    limit: 5,
  });
  const { data: urgentTicketsData, isLoading: isTicketsLoading } =
    useListAllTicketsQuery({
      status: "open",
      limit: 5,
    });

  const metrics = metricsData?.data;
  const newLeads = leadsData?.data || [];
  const urgentTickets = urgentTicketsData?.data || [];

  if (isMetricsLoading || isLeadsLoading || isTicketsLoading) {
    return (
      <Box className="flex justify-center items-center min-h-[400px]">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" className="py-10 space-y-8">
      <div>
        <Typography
          variant="h4"
          className="font-extrabold text-neutral-900 tracking-tight"
        >
          {t("operations:firstResponderHub")}
        </Typography>
        <Typography variant="body1" className="text-neutral-500 mt-1">
          Inbound client triage, crisis triage queue, and active lead
          assignments.
        </Typography>
      </div>

      {/* Metrics Row */}
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card className="rounded-2xl border border-purple-200 bg-purple-50/50 shadow-xs">
            <CardContent className="p-6 flex items-center justify-between">
              <div>
                <Typography
                  variant="caption"
                  className="font-bold text-purple-700 uppercase tracking-wider"
                >
                  New Inbound Leads
                </Typography>
                <Typography
                  variant="h3"
                  className="font-extrabold text-neutral-900 mt-1"
                >
                  {metrics?.new_leads_count ?? 0}
                </Typography>
              </div>
              <Box className="p-3 bg-white rounded-xl shadow-xs border border-purple-100">
                <FiUserPlus className="w-6 h-6 text-purple-600" />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 4 }}>
          <Card className="rounded-2xl border border-rose-200 bg-rose-50/50 shadow-xs">
            <CardContent className="p-6 flex items-center justify-between">
              <div>
                <Typography
                  variant="caption"
                  className="font-bold text-rose-700 uppercase tracking-wider"
                >
                  Open Support Cases
                </Typography>
                <Typography
                  variant="h3"
                  className="font-extrabold text-neutral-900 mt-1"
                >
                  {metrics?.pending_support_tickets ?? 0}
                </Typography>
              </div>
              <Box className="p-3 bg-white rounded-xl shadow-xs border border-rose-100">
                <FiAlertCircle className="w-6 h-6 text-rose-600" />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 4 }}>
          <Card className="rounded-2xl border border-teal-200 bg-teal-50/50 shadow-xs">
            <CardContent className="p-6 flex items-center justify-between">
              <div>
                <Typography
                  variant="caption"
                  className="font-bold text-teal-700 uppercase tracking-wider"
                >
                  Upcoming Consultations
                </Typography>
                <Typography
                  variant="h3"
                  className="font-extrabold text-neutral-900 mt-1"
                >
                  {metrics?.upcoming_sessions ?? 0}
                </Typography>
              </div>
              <Box className="p-3 bg-white rounded-xl shadow-xs border border-teal-100">
                <FiClock className="w-6 h-6 text-teal-600" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Triage Queues */}
      <Grid container spacing={4}>
        {/* New Leads Queue */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card className="rounded-2xl border border-neutral-200 shadow-sm overflow-hidden h-full flex flex-col">
            <Box className="p-5 border-b border-neutral-200 bg-neutral-50/80 flex items-center justify-between">
              <Typography
                variant="subtitle1"
                className="font-bold text-neutral-900"
              >
                Incoming Leads Awaiting Contact
              </Typography>
              <Button
                size="small"
                endIcon={<FiArrowRight />}
                onClick={() => navigate("/operations/leads")}
                className="normal-case text-xs font-bold"
              >
                View All Leads
              </Button>
            </Box>
            <CardContent className="p-0 flex-1 divide-y divide-neutral-100">
              {newLeads.length === 0 ? (
                <Box className="p-8 text-center text-neutral-500 text-sm">
                  <FiCheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                  All prospective leads have been contacted!
                </Box>
              ) : (
                newLeads.map((lead) => (
                  <Box
                    key={lead.id}
                    className="p-4 flex items-center justify-between hover:bg-neutral-50 transition-colors"
                  >
                    <div>
                      <Typography
                        variant="subtitle2"
                        className="font-bold text-neutral-900"
                      >
                        {lead.name}
                      </Typography>
                      <Typography
                        variant="caption"
                        className="text-neutral-500 block"
                      >
                        {lead.phone} • {lead.source}
                      </Typography>
                    </div>
                    <Button
                      size="small"
                      variant="outlined"
                      color="primary"
                      startIcon={<FiPhoneCall />}
                      onClick={() => navigate("/operations/leads")}
                      className="rounded-xl normal-case text-xs font-bold"
                    >
                      Triage
                    </Button>
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Support Queue */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card className="rounded-2xl border border-neutral-200 shadow-sm overflow-hidden h-full flex flex-col">
            <Box className="p-5 border-b border-neutral-200 bg-neutral-50/80 flex items-center justify-between">
              <Typography
                variant="subtitle1"
                className="font-bold text-neutral-900"
              >
                Open Support Inquiries
              </Typography>
              <Button
                size="small"
                endIcon={<FiArrowRight />}
                onClick={() => navigate("/support")}
                className="normal-case text-xs font-bold"
              >
                Support Hub
              </Button>
            </Box>
            <CardContent className="p-0 flex-1 divide-y divide-neutral-100">
              {urgentTickets.length === 0 ? (
                <Box className="p-8 text-center text-neutral-500 text-sm">
                  <FiCheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                  Support inbox is clear!
                </Box>
              ) : (
                urgentTickets.map((tkt: SupportTicketResponse) => (
                  <Box
                    key={tkt.id}
                    className="p-4 flex items-center justify-between hover:bg-neutral-50 transition-colors"
                  >
                    <div className="max-w-xs">
                      <Typography
                        variant="subtitle2"
                        className="font-bold text-neutral-900 line-clamp-1"
                      >
                        {tkt.subject}
                      </Typography>
                      <Typography
                        variant="caption"
                        className="text-neutral-400 font-mono block"
                      >
                        {tkt.ticket_number} • {tkt.category}
                      </Typography>
                    </div>
                    <Button
                      size="small"
                      variant="outlined"
                      color="inherit"
                      onClick={() => navigate(`/support/tickets/${tkt.id}`)}
                      className="rounded-xl normal-case text-xs font-bold border-neutral-300 shrink-0"
                    >
                      Respond
                    </Button>
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};
