import React, { useState } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
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
import { FiAward, FiCheck, FiX } from "react-icons/fi";
import { useTranslation } from "react-i18next";
import {
  useListTherapistsOperationalQuery,
  useVerifyTherapistMutation,
} from "../api/operations_api";
import type { TherapistDetail } from "@/features/therapist/types/therapist.types";

export const TherapistOperationsPage: React.FC = () => {
  const { t } = useTranslation(["operations", "therapist", "common"]);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [verificationFilter, setVerificationFilter] = useState<string>("");
  const [page, setPage] = useState(1);

  const [selectedTherapist, setSelectedTherapist] =
    useState<TherapistDetail | null>(null);
  const [verificationAction, setVerificationAction] = useState<
    "verified" | "rejected"
  >("verified");
  const [rejectionReason, setRejectionReason] = useState("");

  const { data, isLoading, refetch } = useListTherapistsOperationalQuery({
    status: statusFilter || undefined,
    verification_status: verificationFilter || undefined,
    page,
    limit: 20,
  });

  const [verifyTherapist, { isLoading: isSubmittingVerification }] =
    useVerifyTherapistMutation();

  const therapists = data?.data || [];
  const meta = data?.meta as { total_pages?: number } | undefined;

  const handleVerifySubmit = async () => {
    if (!selectedTherapist) return;
    try {
      await verifyTherapist({
        therapistId: selectedTherapist.id,
        body: {
          status: verificationAction,
          rejection_reason:
            verificationAction === "rejected"
              ? rejectionReason.trim()
              : undefined,
        },
      }).unwrap();
      setSelectedTherapist(null);
      setRejectionReason("");
      refetch();
    } catch {
      // Error handled by RTK Query
    }
  };

  return (
    <Container maxWidth="lg" className="py-10 space-y-6">
      <div>
        <Typography
          variant="h4"
          className="font-extrabold text-neutral-900 tracking-tight"
        >
          {t("operations:therapists")}
        </Typography>
        <Typography variant="body1" className="text-neutral-500 mt-1">
          Review credentials, approve licenses, and manage clinical practitioner
          statuses.
        </Typography>
      </div>

      {/* Filter Toolbar */}
      <Card className="rounded-2xl border border-neutral-200 shadow-xs">
        <CardContent className="p-4 flex flex-wrap gap-4 items-center">
          <Select
            size="small"
            value={verificationFilter}
            displayEmpty
            onChange={(e) => {
              setVerificationFilter(e.target.value);
              setPage(1);
            }}
            className="min-w-[180px]"
          >
            <MenuItem value="">All Verifications</MenuItem>
            <MenuItem value="pending">Pending Verification</MenuItem>
            <MenuItem value="verified">Verified</MenuItem>
            <MenuItem value="rejected">Rejected</MenuItem>
          </Select>

          <Select
            size="small"
            value={statusFilter}
            displayEmpty
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="min-w-[160px]"
          >
            <MenuItem value="">All Statuses</MenuItem>
            <MenuItem value="active">Active</MenuItem>
            <MenuItem value="inactive">Inactive</MenuItem>
            <MenuItem value="pending_verification">
              Pending Verification
            </MenuItem>
            <MenuItem value="suspended">Suspended</MenuItem>
          </Select>
        </CardContent>
      </Card>

      {/* Therapists Table */}
      <Card className="rounded-2xl border border-neutral-200 shadow-sm overflow-hidden">
        {isLoading ? (
          <Box className="flex justify-center py-12">
            <CircularProgress />
          </Box>
        ) : therapists.length === 0 ? (
          <Box className="p-12 text-center text-neutral-500">
            No therapists found.
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead className="bg-neutral-50">
                <TableRow>
                  <TableCell className="font-bold text-neutral-700">
                    Therapist
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Specializations
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Experience & Rate
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Verification
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Status
                  </TableCell>
                  <TableCell
                    align="right"
                    className="font-bold text-neutral-700"
                  >
                    Actions
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {therapists.map((th) => (
                  <TableRow key={th.id} hover>
                    <TableCell>
                      <Typography
                        variant="subtitle2"
                        className="font-bold text-neutral-900"
                      >
                        {th.display_name}
                      </Typography>
                      <Typography
                        variant="caption"
                        className="text-neutral-500 font-mono"
                      >
                        {th.id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={th.specialization}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" className="text-neutral-800">
                        {th.experience_years} years exp.
                      </Typography>
                      <Typography
                        variant="caption"
                        className="text-neutral-500"
                      >
                        ₹{(th.pricing.amount / 100).toFixed(0)} /{" "}
                        {th.pricing.duration_minutes}m
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={th.verification.status}
                        size="small"
                        color={
                          th.verification.status === "verified"
                            ? "success"
                            : th.verification.status === "pending"
                              ? "warning"
                              : "error"
                        }
                        className="font-bold capitalize"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={th.status}
                        size="small"
                        color={th.status === "active" ? "success" : "default"}
                        className="font-bold capitalize"
                      />
                    </TableCell>
                    <TableCell align="right">
                      {th.verification.status === "pending" && (
                        <Button
                          size="small"
                          variant="contained"
                          color="primary"
                          startIcon={<FiAward />}
                          onClick={() => {
                            setSelectedTherapist(th);
                            setVerificationAction("verified");
                            setRejectionReason("");
                          }}
                          className="rounded-xl normal-case text-xs shadow-xs"
                        >
                          Review
                        </Button>
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

      {/* Verification Decision Modal */}
      {selectedTherapist && (
        <Dialog
          open
          onClose={() => setSelectedTherapist(null)}
          maxWidth="sm"
          fullWidth
          slotProps={{ paper: { className: "rounded-2xl p-2" } }}
        >
          <DialogTitle className="font-bold">
            Verify Therapist: {selectedTherapist.display_name}
          </DialogTitle>
          <DialogContent className="space-y-4 pt-2">
            <Typography variant="body2" className="text-neutral-600">
              Qualifications:{" "}
              {selectedTherapist.qualifications.join(", ") || "None specified"}
            </Typography>
            <Typography variant="body2" className="text-neutral-600">
              Bio: {selectedTherapist.bio}
            </Typography>

            <Box className="flex gap-4 pt-2">
              <Button
                variant={
                  verificationAction === "verified" ? "contained" : "outlined"
                }
                color="success"
                startIcon={<FiCheck />}
                onClick={() => setVerificationAction("verified")}
                className="flex-1 rounded-xl normal-case font-bold"
              >
                Approve & Verify
              </Button>
              <Button
                variant={
                  verificationAction === "rejected" ? "contained" : "outlined"
                }
                color="error"
                startIcon={<FiX />}
                onClick={() => setVerificationAction("rejected")}
                className="flex-1 rounded-xl normal-case font-bold"
              >
                Reject
              </Button>
            </Box>

            {verificationAction === "rejected" && (
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Rejection Reason (Required)"
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="e.g. Invalid license credentials, unverified degrees..."
              />
            )}
          </DialogContent>
          <DialogActions className="p-4">
            <Button onClick={() => setSelectedTherapist(null)} color="inherit">
              Cancel
            </Button>
            <Button
              variant="contained"
              color={verificationAction === "verified" ? "success" : "error"}
              disabled={
                (verificationAction === "rejected" &&
                  !rejectionReason.trim()) ||
                isSubmittingVerification
              }
              onClick={handleVerifySubmit}
              className="rounded-xl normal-case font-bold"
            >
              Submit Decision
            </Button>
          </DialogActions>
        </Dialog>
      )}
    </Container>
  );
};
