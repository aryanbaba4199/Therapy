import React, { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Paper,
  TextField,
  Typography,
} from "@mui/material";
import {
  FiArrowLeft,
  FiCheckCircle,
  FiClock,
  FiCornerDownRight,
  FiSend,
  FiUser,
} from "react-icons/fi";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";
import {
  useCloseTicketMutation,
  useGetTicketByIdQuery,
  useSendMessageMutation,
} from "../api/support_api";
import {
  TicketPriorityChip,
  TicketStatusChip,
} from "../components/TicketStatusChip";
import type { SupportMessageResponse } from "../types/support_types";

export const TicketDetailPage: React.FC = () => {
  const { ticketId } = useParams<{ ticketId: string }>();
  const { t } = useTranslation(["support", "common"]);
  const navigate = useNavigate();

  const [messageText, setMessageText] = useState("");

  const { data, isLoading, isError, refetch } = useGetTicketByIdQuery(
    ticketId || "",
    { skip: !ticketId }
  );

  const [sendMessage, { isLoading: isSending }] = useSendMessageMutation();
  const [closeTicket, { isLoading: isClosing }] = useCloseTicketMutation();

  const ticketData = data?.data;
  const ticket = ticketData?.ticket;
  const messages = ticketData?.messages || [];

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticketId || !messageText.trim()) return;

    try {
      await sendMessage({
        ticketId,
        body: {
          message: messageText.trim(),
        },
      }).unwrap();
      setMessageText("");
      refetch();
    } catch {
      // Handled by RTK Query / notification
    }
  };

  const handleCloseTicket = async () => {
    if (!ticketId) return;
    try {
      await closeTicket(ticketId).unwrap();
      refetch();
    } catch {
      // Handled by RTK Query
    }
  };

  if (isLoading) {
    return (
      <Box className="flex justify-center items-center min-h-[400px]">
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !ticket) {
    return (
      <Container maxWidth="md" className="py-12">
        <Alert
          severity="error"
          action={
            <Button
              color="inherit"
              size="small"
              onClick={() => navigate("/support")}
            >
              {t("support:backToTickets")}
            </Button>
          }
        >
          {t("support:ticketNotFound")}
        </Alert>
      </Container>
    );
  }

  const isClosed = ticket.status === "resolved" || ticket.status === "closed";

  return (
    <Container maxWidth="md" className="py-10 space-y-6">
      {/* Navigation Header */}
      <Box className="flex items-center justify-between">
        <Button
          startIcon={<FiArrowLeft />}
          onClick={() => navigate("/support")}
          className="text-neutral-600 hover:text-neutral-900 normal-case font-medium"
        >
          {t("support:backToTickets")}
        </Button>

        {!isClosed && (
          <Button
            variant="outlined"
            color="inherit"
            startIcon={<FiCheckCircle />}
            disabled={isClosing}
            onClick={handleCloseTicket}
            className="rounded-xl normal-case text-neutral-600 border-neutral-300 hover:bg-neutral-50 font-medium"
          >
            {isClosing ? t("support:closing") : t("support:closeTicket")}
          </Button>
        )}
      </Box>

      {/* Ticket Overview Card */}
      <Card className="rounded-2xl border border-neutral-200 shadow-sm overflow-hidden">
        <Box className="bg-neutral-50 px-6 py-4 border-b border-neutral-200 flex flex-wrap items-center justify-between gap-3">
          <Box className="flex items-center gap-3">
            <Typography
              variant="subtitle1"
              className="font-bold text-neutral-800 tracking-wide"
            >
              {ticket.ticket_number}
            </Typography>
            <TicketStatusChip status={ticket.status} />
            <TicketPriorityChip priority={ticket.priority} />
          </Box>
          <Box className="flex items-center gap-2 text-xs text-neutral-500">
            <FiClock />
            <span>
              {new Date(ticket.created_at).toLocaleDateString(undefined, {
                dateStyle: "medium",
                timeStyle: "short",
              })}
            </span>
          </Box>
        </Box>

        <CardContent className="p-6 space-y-4">
          <Typography variant="h5" className="font-extrabold text-neutral-900">
            {ticket.subject}
          </Typography>

          <Box className="flex flex-wrap gap-4 text-xs text-neutral-500 bg-neutral-100/70 p-3 rounded-xl">
            <div>
              <span className="font-semibold text-neutral-700">
                {t("support:category")}:{" "}
              </span>
              <span className="capitalize">{ticket.category}</span>
            </div>
            {ticket.booking_id && (
              <div>
                <span className="font-semibold text-neutral-700">
                  {t("support:referenceBooking")}:{" "}
                </span>
                <span className="font-mono">{ticket.booking_id}</span>
              </div>
            )}
            {ticket.session_id && (
              <div>
                <span className="font-semibold text-neutral-700">
                  {t("support:referenceSession")}:{" "}
                </span>
                <span className="font-mono">{ticket.session_id}</span>
              </div>
            )}
            {ticket.payment_id && (
              <div>
                <span className="font-semibold text-neutral-700">
                  {t("support:referencePayment")}:{" "}
                </span>
                <span className="font-mono">{ticket.payment_id}</span>
              </div>
            )}
            {ticket.package_id && (
              <div>
                <span className="font-semibold text-neutral-700">
                  {t("support:referencePackage")}:{" "}
                </span>
                <span className="font-mono">{ticket.package_id}</span>
              </div>
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Conversation Thread */}
      <Box className="space-y-4 pt-4">
        <Typography variant="h6" className="font-bold text-neutral-800">
          {t("support:conversationThread")}
        </Typography>

        {messages.map((msg: SupportMessageResponse) => {
          const isStaff = msg.sender_role === "staff";
          return (
            <Paper
              key={msg.id}
              elevation={0}
              className={`p-5 rounded-2xl border transition-all ${
                isStaff
                  ? "bg-primary-50/50 border-primary-200 ml-4 sm:ml-12"
                  : "bg-white border-neutral-200 mr-4 sm:mr-12"
              }`}
            >
              <Box className="flex items-center justify-between mb-2">
                <Box className="flex items-center gap-2">
                  <Box
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                      isStaff
                        ? "bg-primary-600 text-white"
                        : "bg-neutral-200 text-neutral-700"
                    }`}
                  >
                    {isStaff ? <FiCornerDownRight /> : <FiUser />}
                  </Box>
                  <Typography
                    variant="subtitle2"
                    className="font-bold text-neutral-900"
                  >
                    {msg.sender_display_name}
                  </Typography>
                  {isStaff && (
                    <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-primary-100 text-primary-800">
                      {t("support:supportTeam")}
                    </span>
                  )}
                </Box>
                <Typography variant="caption" className="text-neutral-400">
                  {new Date(msg.created_at).toLocaleDateString(undefined, {
                    dateStyle: "medium",
                    timeStyle: "short",
                  })}
                </Typography>
              </Box>

              <Typography
                variant="body2"
                className="text-neutral-800 whitespace-pre-wrap leading-relaxed mt-2"
              >
                {msg.message}
              </Typography>
            </Paper>
          );
        })}
      </Box>

      {/* Reply Composer */}
      {isClosed ? (
        <Alert severity="info" className="rounded-2xl">
          {t("support:ticketClosedNotice")}
        </Alert>
      ) : (
        <Paper
          elevation={0}
          className="p-5 rounded-2xl border border-neutral-200 bg-white space-y-4"
        >
          <Typography
            variant="subtitle2"
            className="font-bold text-neutral-800"
          >
            {t("support:replyToTicket")}
          </Typography>
          <form onSubmit={handleSendMessage} className="space-y-3">
            <TextField
              fullWidth
              multiline
              minRows={3}
              maxRows={6}
              placeholder={t("support:typeYourReply")}
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              className="bg-neutral-50/50 rounded-xl"
            />
            <Box className="flex justify-end">
              <Button
                type="submit"
                variant="contained"
                color="primary"
                endIcon={<FiSend />}
                disabled={!messageText.trim() || isSending}
                className="rounded-xl normal-case font-bold px-6 shadow-md"
              >
                {isSending ? t("support:sending") : t("support:sendReply")}
              </Button>
            </Box>
          </form>
        </Paper>
      )}
    </Container>
  );
};
