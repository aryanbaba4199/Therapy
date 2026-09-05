import React, { useState } from "react";
import {
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  MenuItem,
  Pagination,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { useListBookingsOperationalQuery } from "../api/operations_api";

export const BookingOperationsPage: React.FC = () => {
  const { t } = useTranslation(["operations", "common"]);
  const [statusFilter, setStatusFilter] = useState("");
  const [therapistId, setTherapistId] = useState("");
  const [clientId, setClientId] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useListBookingsOperationalQuery({
    status: statusFilter || undefined,
    therapist_id: therapistId || undefined,
    client_id: clientId || undefined,
    page,
    limit: 20,
  });

  const bookings = data?.data || [];
  const meta = data?.meta as { total_pages?: number } | undefined;

  return (
    <Container maxWidth="lg" className="py-10 space-y-6">
      <div>
        <Typography
          variant="h4"
          className="font-extrabold text-neutral-900 tracking-tight"
        >
          {t("operations:bookings")}
        </Typography>
        <Typography variant="body1" className="text-neutral-500 mt-1">
          Operational oversight across all consultation appointments and booking
          states.
        </Typography>
      </div>

      {/* Filter Toolbar */}
      <Card className="rounded-2xl border border-neutral-200 shadow-xs">
        <CardContent className="p-4 flex flex-wrap gap-4 items-center">
          <Select
            size="small"
            value={statusFilter}
            displayEmpty
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="min-w-[150px]"
          >
            <MenuItem value="">All Statuses</MenuItem>
            <MenuItem value="pending">Pending</MenuItem>
            <MenuItem value="confirmed">Confirmed</MenuItem>
            <MenuItem value="completed">Completed</MenuItem>
            <MenuItem value="cancelled">Cancelled</MenuItem>
          </Select>

          <TextField
            size="small"
            placeholder="Therapist UUID..."
            value={therapistId}
            onChange={(e) => {
              setTherapistId(e.target.value);
              setPage(1);
            }}
            className="flex-1 min-w-[200px]"
          />

          <TextField
            size="small"
            placeholder="Client UUID..."
            value={clientId}
            onChange={(e) => {
              setClientId(e.target.value);
              setPage(1);
            }}
            className="flex-1 min-w-[200px]"
          />
        </CardContent>
      </Card>

      {/* Bookings Table */}
      <Card className="rounded-2xl border border-neutral-200 shadow-sm overflow-hidden">
        {isLoading ? (
          <Box className="flex justify-center py-12">
            <CircularProgress />
          </Box>
        ) : bookings.length === 0 ? (
          <Box className="p-12 text-center text-neutral-500">
            No bookings found.
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead className="bg-neutral-50">
                <TableRow>
                  <TableCell className="font-bold text-neutral-700">
                    Booking #
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Client ID
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Therapist ID
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Session Window
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Mode
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Status
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {bookings.map((b) => (
                  <TableRow key={b.id} hover>
                    <TableCell>
                      <Typography
                        variant="subtitle2"
                        className="font-bold font-mono text-neutral-900"
                      >
                        {b.booking_number}
                      </Typography>
                      <Typography
                        variant="caption"
                        className="text-neutral-400 font-mono"
                      >
                        {b.id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="caption"
                        className="font-mono text-neutral-600"
                      >
                        {b.client_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="caption"
                        className="font-mono text-neutral-600"
                      >
                        {b.therapist_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" className="text-neutral-800">
                        {new Date(b.start_at).toLocaleDateString(undefined, {
                          dateStyle: "medium",
                          timeStyle: "short",
                        })}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={b.session_mode}
                        size="small"
                        variant="outlined"
                        className="capitalize"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={b.status}
                        size="small"
                        color={
                          b.status === "confirmed"
                            ? "success"
                            : b.status === "completed"
                              ? "primary"
                              : b.status === "cancelled"
                                ? "error"
                                : "default"
                        }
                        className="font-bold capitalize"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        {meta && (meta.total_pages ?? 1) > 1 && (
          <Box className="p-4 flex justify-center border-t border-neutral-100">
            <Pagination
              count={meta.total_pages}
              page={page}
              onChange={(_e, p) => setPage(p)}
              color="primary"
            />
          </Box>
        )}
      </Card>
    </Container>
  );
};
