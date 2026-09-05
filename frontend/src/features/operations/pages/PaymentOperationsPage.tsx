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
import { useListPaymentsOperationalQuery } from "../api/operations_api";

export const PaymentOperationsPage: React.FC = () => {
  const { t } = useTranslation(["operations", "common"]);
  const [statusFilter, setStatusFilter] = useState("");
  const [providerFilter, setProviderFilter] = useState("");
  const [userId, setUserId] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useListPaymentsOperationalQuery({
    status: statusFilter || undefined,
    provider: providerFilter || undefined,
    user_id: userId || undefined,
    page,
    limit: 20,
  });

  const payments = data?.data || [];
  const meta = data?.meta as { total_pages?: number } | undefined;

  return (
    <Container maxWidth="lg" className="py-10 space-y-6">
      <div>
        <Typography
          variant="h4"
          className="font-extrabold text-neutral-900 tracking-tight"
        >
          {t("operations:payments")}
        </Typography>
        <Typography variant="body1" className="text-neutral-500 mt-1">
          Complete commercial ledger, gateway reconciliation, and failed
          transaction analysis.
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
            <MenuItem value="paid">Paid</MenuItem>
            <MenuItem value="pending">Pending</MenuItem>
            <MenuItem value="failed">Failed</MenuItem>
            <MenuItem value="refunded">Refunded</MenuItem>
          </Select>

          <Select
            size="small"
            value={providerFilter}
            displayEmpty
            onChange={(e) => {
              setProviderFilter(e.target.value);
              setPage(1);
            }}
            className="min-w-[150px]"
          >
            <MenuItem value="">All Gateways</MenuItem>
            <MenuItem value="razorpay">Razorpay</MenuItem>
            <MenuItem value="mock">Mock Gateway</MenuItem>
            <MenuItem value="package_redemption">Package Redemption</MenuItem>
          </Select>

          <TextField
            size="small"
            placeholder="Filter User UUID..."
            value={userId}
            onChange={(e) => {
              setUserId(e.target.value);
              setPage(1);
            }}
            className="flex-1 min-w-[200px]"
          />
        </CardContent>
      </Card>

      {/* Payments Table */}
      <Card className="rounded-2xl border border-neutral-200 shadow-sm overflow-hidden">
        {isLoading ? (
          <Box className="flex justify-center py-12">
            <CircularProgress />
          </Box>
        ) : payments.length === 0 ? (
          <Box className="p-12 text-center text-neutral-500">
            No payment records found.
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead className="bg-neutral-50">
                <TableRow>
                  <TableCell className="font-bold text-neutral-700">
                    Order ID / Date
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    User ID
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Target
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Amount
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Provider
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Status
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Failure Diagnostics
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {payments.map((p) => (
                  <TableRow key={p.id} hover>
                    <TableCell>
                      <Typography
                        variant="subtitle2"
                        className="font-bold font-mono text-neutral-900"
                      >
                        {p.order_id}
                      </Typography>
                      <Typography
                        variant="caption"
                        className="text-neutral-500"
                      >
                        {new Date(p.created_at).toLocaleDateString(undefined, {
                          dateStyle: "medium",
                          timeStyle: "short",
                        })}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="caption"
                        className="font-mono text-neutral-600"
                      >
                        {p.user_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={p.target_type}
                        size="small"
                        variant="outlined"
                        className="capitalize"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="body2"
                        className="font-bold text-neutral-900"
                      >
                        ₹{(p.final_amount_minor / 100).toFixed(2)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="caption"
                        className="font-mono uppercase text-neutral-600"
                      >
                        {p.provider}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={p.status}
                        size="small"
                        color={
                          p.status === "paid"
                            ? "success"
                            : p.status === "failed"
                              ? "error"
                              : "default"
                        }
                        className="font-bold capitalize"
                      />
                    </TableCell>
                    <TableCell>
                      {p.failure_message ? (
                        <Box>
                          <Typography
                            variant="caption"
                            className="text-red-600 font-semibold block"
                          >
                            {p.failure_code}
                          </Typography>
                          <Typography
                            variant="caption"
                            className="text-neutral-500"
                          >
                            {p.failure_message}
                          </Typography>
                        </Box>
                      ) : (
                        <span className="text-neutral-400">—</span>
                      )}
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
