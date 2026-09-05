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
import { FiCheckCircle, FiPlus, FiUserCheck } from "react-icons/fi";
import { useTranslation } from "react-i18next";
import {
  useAssignLeadMutation,
  useConvertLeadToUserMutation,
  useCreateLeadMutation,
  useListLeadsQuery,
  useUpdateLeadMutation,
} from "../api/operations_api";
import type { Lead, LeadSource, LeadStatus } from "../types/operations_types";

export const LeadManagementPage: React.FC = () => {
  const { t } = useTranslation(["operations", "common"]);
  const [statusFilter, setStatusFilter] = useState<LeadStatus | "">("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [newLeadName, setNewLeadName] = useState("");
  const [newLeadPhone, setNewLeadPhone] = useState("");
  const [newLeadEmail, setNewLeadEmail] = useState("");
  const [newLeadSource, setNewLeadSource] = useState<LeadSource>("helpline");
  const [newLeadNotes, setNewLeadNotes] = useState("");

  const [selectedLeadForAssign, setSelectedLeadForAssign] =
    useState<Lead | null>(null);
  const [assigneeId, setAssigneeId] = useState("");

  const [selectedLeadForConvert, setSelectedLeadForConvert] =
    useState<Lead | null>(null);
  const [convertUserId, setConvertUserId] = useState("");

  const { data, isLoading, refetch } = useListLeadsQuery({
    status: statusFilter || undefined,
    search: search || undefined,
    page,
    limit: 20,
  });

  const [createLead, { isLoading: isCreating }] = useCreateLeadMutation();
  const [updateLead] = useUpdateLeadMutation();
  const [assignLead, { isLoading: isAssigning }] = useAssignLeadMutation();
  const [convertLead, { isLoading: isConverting }] =
    useConvertLeadToUserMutation();

  const leads = data?.data || [];
  const meta = data?.meta as { total_pages?: number } | undefined;

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLeadName.trim() || !newLeadPhone.trim()) return;

    try {
      await createLead({
        name: newLeadName.trim(),
        phone: newLeadPhone.trim(),
        email: newLeadEmail.trim() || undefined,
        source: newLeadSource,
        notes: newLeadNotes.trim() || undefined,
      }).unwrap();
      setCreateModalOpen(false);
      setNewLeadName("");
      setNewLeadPhone("");
      setNewLeadEmail("");
      setNewLeadNotes("");
      refetch();
    } catch {
      // Error handled by RTK Query
    }
  };

  const handleStatusChange = async (leadId: string, newStatus: LeadStatus) => {
    try {
      await updateLead({
        leadId,
        body: { status: newStatus },
      }).unwrap();
      refetch();
    } catch {
      // Error handled by RTK Query
    }
  };

  const handleAssignSubmit = async () => {
    if (!selectedLeadForAssign || !assigneeId.trim()) return;
    try {
      await assignLead({
        leadId: selectedLeadForAssign.id,
        body: { assigned_to: assigneeId.trim() },
      }).unwrap();
      setSelectedLeadForAssign(null);
      setAssigneeId("");
      refetch();
    } catch {
      // Error handled by RTK Query
    }
  };

  const handleConvertSubmit = async () => {
    if (!selectedLeadForConvert || !convertUserId.trim()) return;
    try {
      await convertLead({
        leadId: selectedLeadForConvert.id,
        userId: convertUserId.trim(),
      }).unwrap();
      setSelectedLeadForConvert(null);
      setConvertUserId("");
      refetch();
    } catch {
      // Error handled by RTK Query
    }
  };

  return (
    <Container maxWidth="lg" className="py-10 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Typography
            variant="h4"
            className="font-extrabold text-neutral-900 tracking-tight"
          >
            {t("operations:firstResponderHub")}
          </Typography>
          <Typography variant="body1" className="text-neutral-500 mt-1">
            Triaging prospective client leads, follow-ups, and customer
            conversions.
          </Typography>
        </div>
        <Button
          variant="contained"
          color="primary"
          startIcon={<FiPlus />}
          onClick={() => setCreateModalOpen(true)}
          className="rounded-xl normal-case font-bold self-start sm:self-auto shadow-md"
        >
          {t("operations:leadTable.createLead")}
        </Button>
      </div>

      {/* Filter Toolbar */}
      <Card className="rounded-2xl border border-neutral-200 shadow-xs">
        <CardContent className="p-4 flex flex-wrap gap-4 items-center">
          <TextField
            size="small"
            placeholder="Search prospects by name, phone, email..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="flex-1 min-w-[240px]"
          />

          <Select
            size="small"
            value={statusFilter}
            displayEmpty
            onChange={(e) => {
              setStatusFilter(e.target.value as LeadStatus | "");
              setPage(1);
            }}
            className="min-w-[150px]"
          >
            <MenuItem value="">All Statuses</MenuItem>
            <MenuItem value="new">New</MenuItem>
            <MenuItem value="contacted">Contacted</MenuItem>
            <MenuItem value="follow_up">Follow Up</MenuItem>
            <MenuItem value="converted">Converted</MenuItem>
            <MenuItem value="lost">Lost</MenuItem>
          </Select>
        </CardContent>
      </Card>

      {/* Leads Table */}
      <Card className="rounded-2xl border border-neutral-200 shadow-sm overflow-hidden">
        {isLoading ? (
          <Box className="flex justify-center py-12">
            <CircularProgress />
          </Box>
        ) : leads.length === 0 ? (
          <Box className="p-12 text-center text-neutral-500">
            No leads found.
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead className="bg-neutral-50">
                <TableRow>
                  <TableCell className="font-bold text-neutral-700">
                    Prospect
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Source
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Status
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Assigned To
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Last Contact
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
                {leads.map((lead) => (
                  <TableRow key={lead.id} hover>
                    <TableCell>
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
                        {lead.phone} {lead.email ? `• ${lead.email}` : ""}
                      </Typography>
                      {lead.notes && (
                        <Typography
                          variant="caption"
                          className="text-neutral-400 italic line-clamp-1 mt-0.5"
                        >
                          "{lead.notes}"
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={lead.source}
                        size="small"
                        variant="outlined"
                        className="capitalize"
                      />
                    </TableCell>
                    <TableCell>
                      <Select
                        size="small"
                        value={lead.status}
                        onChange={(e) =>
                          handleStatusChange(
                            lead.id,
                            e.target.value as LeadStatus
                          )
                        }
                        className="text-xs capitalize font-bold rounded-lg"
                      >
                        <MenuItem value="new">New</MenuItem>
                        <MenuItem value="contacted">Contacted</MenuItem>
                        <MenuItem value="follow_up">Follow Up</MenuItem>
                        <MenuItem value="converted">Converted</MenuItem>
                        <MenuItem value="lost">Lost</MenuItem>
                      </Select>
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="caption"
                        className="font-mono text-neutral-600"
                      >
                        {lead.assigned_to || "Unassigned"}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="caption"
                        className="text-neutral-500"
                      >
                        {lead.last_contacted_at
                          ? new Date(lead.last_contacted_at).toLocaleDateString(
                              undefined,
                              {
                                dateStyle: "short",
                                timeStyle: "short",
                              }
                            )
                          : "Never"}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Box className="flex justify-end gap-2">
                        <Button
                          size="small"
                          variant="outlined"
                          color="inherit"
                          startIcon={<FiUserCheck />}
                          onClick={() => {
                            setSelectedLeadForAssign(lead);
                            setAssigneeId(lead.assigned_to || "");
                          }}
                          className="rounded-xl normal-case text-xs border-neutral-300"
                        >
                          Assign
                        </Button>
                        {lead.status !== "converted" && (
                          <Button
                            size="small"
                            variant="outlined"
                            color="success"
                            startIcon={<FiCheckCircle />}
                            onClick={() => {
                              setSelectedLeadForConvert(lead);
                              setConvertUserId("");
                            }}
                            className="rounded-xl normal-case text-xs"
                          >
                            Convert
                          </Button>
                        )}
                      </Box>
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

      {/* Create Lead Modal */}
      {createModalOpen && (
        <Dialog
          open
          onClose={() => setCreateModalOpen(false)}
          maxWidth="xs"
          fullWidth
          slotProps={{ paper: { className: "rounded-2xl p-2" } }}
        >
          <form onSubmit={handleCreateSubmit}>
            <DialogTitle className="font-bold">
              New Prospective Client Lead
            </DialogTitle>
            <DialogContent className="space-y-4 pt-2">
              <TextField
                fullWidth
                required
                label="Full Name"
                value={newLeadName}
                onChange={(e) => setNewLeadName(e.target.value)}
              />
              <TextField
                fullWidth
                required
                label="Phone Number"
                value={newLeadPhone}
                onChange={(e) => setNewLeadPhone(e.target.value)}
              />
              <TextField
                fullWidth
                label="Email (Optional)"
                value={newLeadEmail}
                onChange={(e) => setNewLeadEmail(e.target.value)}
              />
              <Select
                fullWidth
                value={newLeadSource}
                onChange={(e) => setNewLeadSource(e.target.value as LeadSource)}
              >
                <MenuItem value="helpline">Helpline Inbound</MenuItem>
                <MenuItem value="website">Website Contact</MenuItem>
                <MenuItem value="referral">Referral</MenuItem>
                <MenuItem value="campaign">Marketing Campaign</MenuItem>
                <MenuItem value="other">Other</MenuItem>
              </Select>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Clinical/Inquiry Notes"
                value={newLeadNotes}
                onChange={(e) => setNewLeadNotes(e.target.value)}
              />
            </DialogContent>
            <DialogActions className="p-4">
              <Button onClick={() => setCreateModalOpen(false)} color="inherit">
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                color="primary"
                disabled={
                  !newLeadName.trim() || !newLeadPhone.trim() || isCreating
                }
                className="rounded-xl normal-case font-bold"
              >
                Create Lead
              </Button>
            </DialogActions>
          </form>
        </Dialog>
      )}

      {/* Assign Modal */}
      {selectedLeadForAssign && (
        <Dialog
          open
          onClose={() => setSelectedLeadForAssign(null)}
          maxWidth="xs"
          fullWidth
          slotProps={{ paper: { className: "rounded-2xl p-2" } }}
        >
          <DialogTitle className="font-bold">
            Assign Lead: {selectedLeadForAssign.name}
          </DialogTitle>
          <DialogContent className="space-y-4 pt-2">
            <TextField
              fullWidth
              required
              label="Staff / First Responder User ID"
              value={assigneeId}
              onChange={(e) => setAssigneeId(e.target.value)}
              placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
            />
          </DialogContent>
          <DialogActions className="p-4">
            <Button
              onClick={() => setSelectedLeadForAssign(null)}
              color="inherit"
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              color="primary"
              disabled={!assigneeId.trim() || isAssigning}
              onClick={handleAssignSubmit}
              className="rounded-xl normal-case font-bold"
            >
              Confirm Assignment
            </Button>
          </DialogActions>
        </Dialog>
      )}

      {/* Convert to User Modal */}
      {selectedLeadForConvert && (
        <Dialog
          open
          onClose={() => setSelectedLeadForConvert(null)}
          maxWidth="xs"
          fullWidth
          slotProps={{ paper: { className: "rounded-2xl p-2" } }}
        >
          <DialogTitle className="font-bold">
            Convert Lead to Client
          </DialogTitle>
          <DialogContent className="space-y-4 pt-2">
            <Typography variant="body2" className="text-neutral-600">
              Link prospective lead ({selectedLeadForConvert.name}) to a
              registered client account.
            </Typography>
            <TextField
              fullWidth
              required
              label="Registered Client User ID"
              value={convertUserId}
              onChange={(e) => setConvertUserId(e.target.value)}
              placeholder="Enter client UUID"
            />
          </DialogContent>
          <DialogActions className="p-4">
            <Button
              onClick={() => setSelectedLeadForConvert(null)}
              color="inherit"
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              color="success"
              disabled={!convertUserId.trim() || isConverting}
              onClick={handleConvertSubmit}
              className="rounded-xl normal-case font-bold"
            >
              Convert Lead
            </Button>
          </DialogActions>
        </Dialog>
      )}
    </Container>
  );
};
