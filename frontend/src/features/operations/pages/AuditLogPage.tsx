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
import { useListAuditLogsQuery } from "../api/operations_api";

export const AuditLogPage: React.FC = () => {
  const { t } = useTranslation(["operations", "common"]);
  const [resourceType, setResourceType] = useState("");
  const [resourceId, setResourceId] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useListAuditLogsQuery({
    resource_type: resourceType || undefined,
    resource_id: resourceId || undefined,
    page,
    limit: 20,
  });

  const logs = data?.data || [];
  const meta = data?.meta as { total_pages?: number } | undefined;

  return (
    <Container maxWidth="lg" className="py-10 space-y-6">
      <div>
        <Typography
          variant="h4"
          className="font-extrabold text-neutral-900 tracking-tight"
        >
          {t("operations:auditLogs")}
        </Typography>
        <Typography variant="body1" className="text-neutral-500 mt-1">
          Immutable, append-only operational audit trail of all privileged
          actions.
        </Typography>
      </div>

      {/* Filter Toolbar */}
      <Card className="rounded-2xl border border-neutral-200 shadow-xs">
        <CardContent className="p-4 flex flex-wrap gap-4 items-center">
          <Select
            size="small"
            value={resourceType}
            displayEmpty
            onChange={(e) => {
              setResourceType(e.target.value);
              setPage(1);
            }}
            className="min-w-[160px]"
          >
            <MenuItem value="">All Resources</MenuItem>
            <MenuItem value="user">User</MenuItem>
            <MenuItem value="therapist">Therapist</MenuItem>
            <MenuItem value="lead">Lead</MenuItem>
            <MenuItem value="support_ticket">Support Ticket</MenuItem>
            <MenuItem value="booking">Booking</MenuItem>
          </Select>

          <TextField
            size="small"
            placeholder="Filter by Resource ID..."
            value={resourceId}
            onChange={(e) => {
              setResourceId(e.target.value);
              setPage(1);
            }}
            className="flex-1 min-w-[240px]"
          />
        </CardContent>
      </Card>

      {/* Audit Table */}
      <Card className="rounded-2xl border border-neutral-200 shadow-sm overflow-hidden">
        {isLoading ? (
          <Box className="flex justify-center py-12">
            <CircularProgress />
          </Box>
        ) : logs.length === 0 ? (
          <Box className="p-12 text-center text-neutral-500">
            No audit records found.
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead className="bg-neutral-50">
                <TableRow>
                  <TableCell className="font-bold text-neutral-700">
                    Timestamp
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Actor
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Action
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Resource
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Metadata Details
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.id} hover>
                    <TableCell>
                      <Typography
                        variant="body2"
                        className="font-mono text-neutral-800"
                      >
                        {new Date(log.created_at).toLocaleDateString(
                          undefined,
                          {
                            dateStyle: "medium",
                            timeStyle: "medium",
                          }
                        )}
                      </Typography>
                      {log.request_id && (
                        <Typography
                          variant="caption"
                          className="text-neutral-400 font-mono block"
                        >
                          req: {log.request_id.slice(-8)}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="subtitle2"
                        className="font-bold text-neutral-900"
                      >
                        {log.actor_role.toUpperCase()}
                      </Typography>
                      <Typography
                        variant="caption"
                        className="text-neutral-400 font-mono"
                      >
                        {log.actor_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={log.action}
                        size="small"
                        color="primary"
                        variant="outlined"
                        className="font-mono text-xs"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="body2"
                        className="font-semibold text-neutral-800 capitalize"
                      >
                        {log.resource_type}
                      </Typography>
                      <Typography
                        variant="caption"
                        className="text-neutral-400 font-mono block"
                      >
                        {log.resource_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <pre className="text-[11px] font-mono bg-neutral-100/80 p-2 rounded-lg max-w-sm overflow-x-auto text-neutral-700">
                        {JSON.stringify(log.metadata, null, 2)}
                      </pre>
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
