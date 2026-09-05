import React, { useState } from "react";
import {
  Alert,
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
import { FiSearch, FiShield, FiUserCheck, FiUserX } from "react-icons/fi";
import { useTranslation } from "react-i18next";
import {
  useListUsersQuery,
  useUpdateUserRolesMutation,
  useUpdateUserStatusMutation,
} from "../api/operations_api";
import type { OperationUserDetail } from "../types/operations_types";
import type { UserRole, UserStatus } from "@/features/user/types/user.types";

export const UserManagementPage: React.FC = () => {
  const { t } = useTranslation(["operations", "common"]);
  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [page, setPage] = useState(1);

  const [selectedUserForStatus, setSelectedUserForStatus] =
    useState<OperationUserDetail | null>(null);
  const [selectedUserForRoles, setSelectedUserForRoles] =
    useState<OperationUserDetail | null>(null);
  const [actionReason, setActionReason] = useState("");
  const [newRoles, setNewRoles] = useState<UserRole[]>([]);

  const { data, isLoading, refetch } = useListUsersQuery({
    search: searchTerm || undefined,
    role: roleFilter || undefined,
    status: statusFilter || undefined,
    page,
    limit: 20,
  });

  const [updateStatus, { isLoading: isUpdatingStatus }] =
    useUpdateUserStatusMutation();
  const [updateRoles, { isLoading: isUpdatingRoles }] =
    useUpdateUserRolesMutation();

  const users = data?.data || [];
  const meta = data?.meta as { total_pages?: number } | undefined;

  const handleStatusChange = async (targetStatus: UserStatus) => {
    if (!selectedUserForStatus || !actionReason.trim()) return;
    try {
      await updateStatus({
        userId: selectedUserForStatus.id,
        body: { status: targetStatus, reason: actionReason.trim() },
      }).unwrap();
      setSelectedUserForStatus(null);
      setActionReason("");
      refetch();
    } catch {
      // Error handled by RTK Query
    }
  };

  const handleRolesChange = async () => {
    if (!selectedUserForRoles || !actionReason.trim()) return;
    try {
      await updateRoles({
        userId: selectedUserForRoles.id,
        body: { roles: newRoles, reason: actionReason.trim() },
      }).unwrap();
      setSelectedUserForRoles(null);
      setActionReason("");
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
            {t("operations:users")}
          </Typography>
          <Typography variant="body1" className="text-neutral-500 mt-1">
            Search, review, and manage account statuses and role privileges.
          </Typography>
        </div>
      </div>

      {/* Filter Toolbar */}
      <Card className="rounded-2xl border border-neutral-200 shadow-xs">
        <CardContent className="p-4 flex flex-wrap gap-4 items-center">
          <TextField
            size="small"
            placeholder="Search by name, email, phone..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(1);
            }}
            slotProps={{
              input: {
                startAdornment: <FiSearch className="text-neutral-400 mr-2" />,
              },
            }}
            className="flex-1 min-w-[240px]"
          />

          <Select
            size="small"
            value={roleFilter}
            displayEmpty
            onChange={(e) => {
              setRoleFilter(e.target.value);
              setPage(1);
            }}
            className="min-w-[140px]"
          >
            <MenuItem value="">All Roles</MenuItem>
            <MenuItem value="user">User</MenuItem>
            <MenuItem value="therapist">Therapist</MenuItem>
            <MenuItem value="staff">Staff</MenuItem>
            <MenuItem value="first_responder">First Responder</MenuItem>
            <MenuItem value="admin">Admin</MenuItem>
            <MenuItem value="super_admin">Super Admin</MenuItem>
          </Select>

          <Select
            size="small"
            value={statusFilter}
            displayEmpty
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="min-w-[140px]"
          >
            <MenuItem value="">All Statuses</MenuItem>
            <MenuItem value="active">Active</MenuItem>
            <MenuItem value="inactive">Inactive</MenuItem>
            <MenuItem value="suspended">Suspended</MenuItem>
          </Select>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card className="rounded-2xl border border-neutral-200 shadow-sm overflow-hidden">
        {isLoading ? (
          <Box className="flex justify-center py-12">
            <CircularProgress />
          </Box>
        ) : users.length === 0 ? (
          <Box className="p-12 text-center text-neutral-500">
            No users found matching query.
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead className="bg-neutral-50">
                <TableRow>
                  <TableCell className="font-bold text-neutral-700">
                    User
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Contact
                  </TableCell>
                  <TableCell className="font-bold text-neutral-700">
                    Roles
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
                {users.map((u) => (
                  <TableRow key={u.id} hover>
                    <TableCell>
                      <Typography
                        variant="subtitle2"
                        className="font-bold text-neutral-900"
                      >
                        {u.first_name} {u.last_name}
                      </Typography>
                      <Typography
                        variant="caption"
                        className="text-neutral-400 font-mono"
                      >
                        {u.id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" className="text-neutral-700">
                        {u.email || "—"}
                      </Typography>
                      <Typography
                        variant="caption"
                        className="text-neutral-500"
                      >
                        {u.phone || "—"}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box className="flex flex-wrap gap-1">
                        {u.roles.map((r) => (
                          <Chip
                            key={r}
                            label={r}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={u.status}
                        size="small"
                        color={
                          u.status === "active"
                            ? "success"
                            : u.status === "suspended"
                              ? "error"
                              : "default"
                        }
                        className="font-bold capitalize"
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Box className="flex justify-end gap-2">
                        {u.status === "active" ? (
                          <Button
                            size="small"
                            color="error"
                            variant="outlined"
                            startIcon={<FiUserX />}
                            onClick={() => {
                              setSelectedUserForStatus(u);
                              setActionReason("");
                            }}
                            className="rounded-xl normal-case text-xs"
                          >
                            Suspend
                          </Button>
                        ) : (
                          <Button
                            size="small"
                            color="success"
                            variant="outlined"
                            startIcon={<FiUserCheck />}
                            onClick={() => {
                              setSelectedUserForStatus(u);
                              setActionReason("");
                            }}
                            className="rounded-xl normal-case text-xs"
                          >
                            Activate
                          </Button>
                        )}
                        <Button
                          size="small"
                          color="inherit"
                          variant="outlined"
                          startIcon={<FiShield />}
                          onClick={() => {
                            setSelectedUserForRoles(u);
                            setNewRoles(u.roles);
                            setActionReason("");
                          }}
                          className="rounded-xl normal-case text-xs border-neutral-300"
                        >
                          Roles
                        </Button>
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

      {/* Status Modal Dialog */}
      {selectedUserForStatus && (
        <Dialog
          open
          onClose={() => setSelectedUserForStatus(null)}
          maxWidth="xs"
          fullWidth
          slotProps={{ paper: { className: "rounded-2xl p-2" } }}
        >
          <DialogTitle className="font-bold">
            {selectedUserForStatus.status === "active"
              ? "Suspend Account"
              : "Activate Account"}
          </DialogTitle>
          <DialogContent className="space-y-4 pt-2">
            <Typography variant="body2" className="text-neutral-600">
              User: {selectedUserForStatus.first_name}{" "}
              {selectedUserForStatus.last_name} ({selectedUserForStatus.email})
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Operational Reason (Required for Audit)"
              value={actionReason}
              onChange={(e) => setActionReason(e.target.value)}
              placeholder="e.g. Terms of service violation, customer request..."
            />
          </DialogContent>
          <DialogActions className="p-4">
            <Button
              onClick={() => setSelectedUserForStatus(null)}
              color="inherit"
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              color={
                selectedUserForStatus.status === "active" ? "error" : "success"
              }
              disabled={actionReason.trim().length < 3 || isUpdatingStatus}
              onClick={() =>
                handleStatusChange(
                  selectedUserForStatus.status === "active"
                    ? "suspended"
                    : "active"
                )
              }
              className="rounded-xl normal-case font-bold"
            >
              Confirm
            </Button>
          </DialogActions>
        </Dialog>
      )}

      {/* Roles Modal Dialog */}
      {selectedUserForRoles && (
        <Dialog
          open
          onClose={() => setSelectedUserForRoles(null)}
          maxWidth="xs"
          fullWidth
          slotProps={{ paper: { className: "rounded-2xl p-2" } }}
        >
          <DialogTitle className="font-bold">Manage User Roles</DialogTitle>
          <DialogContent className="space-y-4 pt-2">
            <Alert severity="warning" className="rounded-xl text-xs">
              Assigning or removing Admin and Super Admin roles is strictly
              restricted to Super Admins.
            </Alert>
            <Typography variant="body2" className="text-neutral-600">
              User: {selectedUserForRoles.first_name}{" "}
              {selectedUserForRoles.last_name}
            </Typography>

            <Box className="space-y-2">
              <Typography
                variant="caption"
                className="font-bold text-neutral-500"
              >
                Active Roles
              </Typography>
              <Box className="flex flex-wrap gap-2">
                {(
                  [
                    "user",
                    "therapist",
                    "staff",
                    "first_responder",
                    "admin",
                    "super_admin",
                  ] as UserRole[]
                ).map((role) => {
                  const isSelected = newRoles.includes(role);
                  return (
                    <Chip
                      key={role}
                      label={role}
                      color={isSelected ? "primary" : "default"}
                      onClick={() => {
                        if (isSelected) {
                          if (newRoles.length > 1) {
                            setNewRoles(newRoles.filter((r) => r !== role));
                          }
                        } else {
                          setNewRoles([...newRoles, role]);
                        }
                      }}
                      className="cursor-pointer font-semibold capitalize"
                    />
                  );
                })}
              </Box>
            </Box>

            <TextField
              fullWidth
              multiline
              rows={3}
              label="Administrative Reason (Required for Audit)"
              value={actionReason}
              onChange={(e) => setActionReason(e.target.value)}
              placeholder="e.g. Promotion to First Responder, operational assignment..."
            />
          </DialogContent>
          <DialogActions className="p-4">
            <Button
              onClick={() => setSelectedUserForRoles(null)}
              color="inherit"
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              color="primary"
              disabled={actionReason.trim().length < 3 || isUpdatingRoles}
              onClick={handleRolesChange}
              className="rounded-xl normal-case font-bold"
            >
              Save Roles
            </Button>
          </DialogActions>
        </Dialog>
      )}
    </Container>
  );
};
