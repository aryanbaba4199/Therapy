import React from "react";
import { useTranslation } from "react-i18next";
import { Box, CircularProgress, Container, Typography } from "@mui/material";
import { UserProfileCard } from "../components/UserProfileCard";
import { useGetProfileQuery } from "../api/user_api";
import { useAuth } from "../../auth/hooks/useAuth";

export const ProfilePage: React.FC = () => {
  const { t } = useTranslation(["auth", "common"]);
  const { user: authUser } = useAuth();
  const { data: profileResponse, isLoading } = useGetProfileQuery();

  const user = profileResponse?.data || authUser;

  if (isLoading && !user) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "50vh",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (!user) {
    return (
      <Container maxWidth="md" sx={{ py: 6 }}>
        <Typography variant="body1" color="error">
          {t("common:error")}
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Typography
        variant="h4"
        component="h1"
        gutterBottom
        sx={{ fontWeight: 700, mb: 4 }}
      >
        {t("auth:myProfile")}
      </Typography>
      <UserProfileCard user={user} />
    </Container>
  );
};
