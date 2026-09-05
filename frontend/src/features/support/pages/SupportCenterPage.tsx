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
  Typography,
} from "@mui/material";
import { FiClock, FiHelpCircle, FiMessageSquare, FiPlus } from "react-icons/fi";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useListMyTicketsQuery } from "../api/support_api";
import { CreateTicketModal } from "../components/CreateTicketModal";
import {
  TicketPriorityChip,
  TicketStatusChip,
} from "../components/TicketStatusChip";
import type { SupportTicketStatus } from "../types/support_types";

type StatusFilterTab = "all" | SupportTicketStatus;

export const SupportCenterPage: React.FC = () => {
  const { t } = useTranslation(["support", "common"]);
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<StatusFilterTab>("all");
  const [createModalOpen, setCreateModalOpen] = useState(false);

  const statusParam = activeTab === "all" ? undefined : activeTab;

  const { data, isLoading, isError, refetch } = useListMyTicketsQuery({
    status: statusParam,
    page: 1,
    limit: 50,
  });

  const tickets = data?.data || [];

  return (
    <Container maxWidth="md" className="py-10 space-y-6">
      {/* Header */}
      <Box className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Box>
          <Typography
            variant="h4"
            className="font-extrabold text-neutral-900 tracking-tight"
          >
            {t("support:helpCenter")}
          </Typography>
          <Typography variant="body1" className="text-neutral-500 mt-1">
            {t("support:supportSubtitle")}
          </Typography>
        </Box>
        <Button
          variant="contained"
          color="primary"
          startIcon={<FiPlus />}
          onClick={() => setCreateModalOpen(true)}
          className="rounded-xl normal-case font-bold self-start sm:self-auto shadow-md"
        >
          {t("support:createTicket")}
        </Button>
      </Box>

      {/* Filter Tabs */}
      <Box className="border-b border-neutral-200">
        <Tabs
          value={activeTab}
          onChange={(_e, val: StatusFilterTab) => setActiveTab(val)}
          textColor="primary"
          indicatorColor="primary"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab
            value="all"
            label={t("common:all", "All")}
            className="normal-case font-bold"
          />
          <Tab
            value="open"
            label={t("support:statuses.open")}
            className="normal-case font-medium"
          />
          <Tab
            value="in_progress"
            label={t("support:statuses.in_progress")}
            className="normal-case font-medium"
          />
          <Tab
            value="resolved"
            label={t("support:statuses.resolved")}
            className="normal-case font-medium"
          />
          <Tab
            value="closed"
            label={t("support:statuses.closed")}
            className="normal-case font-medium"
          />
        </Tabs>
      </Box>

      {/* Ticket List */}
      {isLoading ? (
        <Box className="flex justify-center py-20">
          <CircularProgress color="primary" />
        </Box>
      ) : isError ? (
        <Box className="text-center py-16 bg-red-50 rounded-3xl border border-red-100 p-6">
          <Typography variant="h6" className="text-red-700 font-bold mb-2">
            Failed to load support tickets
          </Typography>
          <Button variant="outlined" color="primary" onClick={() => refetch()}>
            Retry
          </Button>
        </Box>
      ) : tickets.length === 0 ? (
        <Box className="text-center py-20 bg-neutral-50 rounded-3xl border border-dashed border-neutral-200 space-y-3">
          <FiHelpCircle size={40} className="mx-auto text-neutral-400" />
          <Typography variant="body1" className="text-neutral-600 font-medium">
            {t("support:noTickets")}
          </Typography>
          <Button
            variant="contained"
            color="primary"
            startIcon={<FiPlus />}
            onClick={() => setCreateModalOpen(true)}
            className="rounded-xl normal-case font-semibold"
          >
            {t("support:createTicket")}
          </Button>
        </Box>
      ) : (
        <Box className="space-y-3">
          {tickets.map((ticket) => {
            const updatedDate = new Date(ticket.updated_at).toLocaleDateString(
              undefined,
              {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              }
            );

            return (
              <Card
                key={ticket.id}
                className="rounded-2xl border border-neutral-200 shadow-sm hover:shadow hover:border-teal-400 transition-all cursor-pointer"
                onClick={() => navigate(`/support/tickets/${ticket.id}`)}
              >
                <CardContent className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5">
                  <Box className="space-y-1.5 flex-1">
                    <Box className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-mono font-bold text-teal-800 bg-teal-50 px-2 py-0.5 rounded-lg border border-teal-100">
                        {ticket.ticket_number}
                      </span>
                      <TicketStatusChip status={ticket.status} />
                      <TicketPriorityChip priority={ticket.priority} />
                      <span className="text-xs text-neutral-400">
                        &bull;{" "}
                        {t(
                          `support:categories.${ticket.category}`,
                          ticket.category
                        )}
                      </span>
                    </Box>

                    <Typography
                      variant="subtitle1"
                      className="font-bold text-neutral-900 line-clamp-1"
                    >
                      {ticket.subject}
                    </Typography>

                    <Box className="flex items-center gap-1 text-xs text-neutral-400">
                      <FiClock size={12} />
                      <span>
                        {t("support:lastUpdated")}: {updatedDate}
                      </span>
                    </Box>
                  </Box>

                  <Button
                    variant="outlined"
                    color="inherit"
                    size="small"
                    startIcon={<FiMessageSquare />}
                    className="rounded-xl normal-case shrink-0 self-end sm:self-auto text-neutral-600"
                  >
                    View Thread
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </Box>
      )}

      {/* Ticket Creation Dialog */}
      <CreateTicketModal
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onSuccess={(ticketId) => {
          refetch();
          navigate(`/support/tickets/${ticketId}`);
        }}
      />
    </Container>
  );
};
