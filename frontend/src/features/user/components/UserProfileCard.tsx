import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { FaCheckCircle, FaUser } from "react-icons/fa";
import { useAppDispatch } from "../../../store/hooks";
import { setUser } from "../../auth/store/auth_slice";
import { useUpdateProfileMutation } from "../api/user_api";
import type { UserProfile } from "../types/user.types";

interface UserProfileCardProps {
  user: UserProfile;
}

export const UserProfileCard: React.FC<UserProfileCardProps> = ({ user }) => {
  const { t } = useTranslation(["auth", "common", "validation"]);
  const dispatch = useAppDispatch();
  const [updateProfile, { isLoading }] = useUpdateProfileMutation();

  const [isEditing, setIsEditing] = useState(false);
  const [firstName, setFirstName] = useState(user.first_name);
  const [lastName, setLastName] = useState(user.last_name);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage(null);
    setErrorMessage(null);

    try {
      const res = await updateProfile({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
      }).unwrap();

      if (res.data) {
        dispatch(setUser(res.data));
        setSuccessMessage(t("auth:profileUpdated"));
        setIsEditing(false);
      }
    } catch (err: unknown) {
      if (err && typeof err === "object" && "data" in err) {
        const apiError = err as { data?: { message?: string } };
        setErrorMessage(apiError.data?.message || t("validation:serverError"));
      } else {
        setErrorMessage(t("validation:networkError"));
      }
    }
  };

  return (
    <Card elevation={2} sx={{ borderRadius: 3 }}>
      <CardContent sx={{ p: { xs: 3, sm: 5 } }}>
        {successMessage && (
          <Alert
            severity="success"
            sx={{ mb: 3 }}
            onClose={() => setSuccessMessage(null)}
          >
            {successMessage}
          </Alert>
        )}
        {errorMessage && (
          <Alert
            severity="error"
            sx={{ mb: 3 }}
            onClose={() => setErrorMessage(null)}
          >
            {errorMessage}
          </Alert>
        )}

        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={3}
          sx={{ mb: 4, alignItems: "center" }}
        >
          <Avatar
            sx={{
              width: 80,
              height: 80,
              bgcolor: "primary.main",
              fontSize: "2rem",
              fontWeight: 700,
            }}
          >
            {user.first_name?.[0]?.toUpperCase() || <FaUser />}
          </Avatar>
          <Box sx={{ textAlign: { xs: "center", sm: "left" } }}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              {user.first_name} {user.last_name}
            </Typography>
            <Stack
              direction="row"
              spacing={1}
              sx={{ mt: 1, justifyContent: { xs: "center", sm: "flex-start" } }}
            >
              {user.roles.map((role) => (
                <Chip
                  key={role}
                  label={role.toUpperCase()}
                  size="small"
                  color={
                    role === "admin" || role === "super_admin"
                      ? "secondary"
                      : "primary"
                  }
                  variant="outlined"
                />
              ))}
              {user.is_verified && (
                <Chip
                  icon={<FaCheckCircle />}
                  label={t("auth:verified")}
                  size="small"
                  color="success"
                />
              )}
            </Stack>
          </Box>
        </Stack>

        <Divider sx={{ mb: 4 }} />

        {isEditing ? (
          <form onSubmit={handleUpdate}>
            <Stack spacing={3}>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    label={t("auth:firstName")}
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    required
                    fullWidth
                    disabled={isLoading}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    label={t("auth:lastName")}
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    required
                    fullWidth
                    disabled={isLoading}
                  />
                </Grid>
              </Grid>

              <Stack
                direction="row"
                spacing={2}
                sx={{ justifyContent: "flex-end" }}
              >
                <Button
                  variant="outlined"
                  color="inherit"
                  onClick={() => {
                    setIsEditing(false);
                    setFirstName(user.first_name);
                    setLastName(user.last_name);
                  }}
                  disabled={isLoading}
                >
                  {t("common:cancel")}
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  disabled={isLoading || !firstName.trim() || !lastName.trim()}
                  startIcon={
                    isLoading ? (
                      <CircularProgress size={18} color="inherit" />
                    ) : null
                  }
                >
                  {t("auth:saveChanges")}
                </Button>
              </Stack>
            </Stack>
          </form>
        ) : (
          <Stack spacing={3}>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="caption" color="text.secondary">
                  {t("auth:email")}
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>
                  {user.email || "—"}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="caption" color="text.secondary">
                  {t("auth:phoneNumber")}
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>
                  {user.phone || "—"}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="caption" color="text.secondary">
                  {t("auth:accountStatus")}
                </Typography>
                <Typography
                  variant="body1"
                  sx={{ fontWeight: 500, textTransform: "capitalize" }}
                >
                  {user.status}
                </Typography>
              </Grid>
            </Grid>

            <Box sx={{ pt: 2, display: "flex", justifyContent: "flex-end" }}>
              <Button
                variant="contained"
                color="primary"
                onClick={() => setIsEditing(true)}
              >
                {t("auth:editProfile")}
              </Button>
            </Box>
          </Stack>
        )}
      </CardContent>
    </Card>
  );
};
