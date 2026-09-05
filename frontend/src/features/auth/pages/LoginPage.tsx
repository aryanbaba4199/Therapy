import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";
import { Card, CardContent, Container, Typography } from "@mui/material";
import { LoginForm } from "../components/LoginForm";
import { useAuth } from "../hooks/useAuth";

export const LoginPage: React.FC = () => {
  const { t } = useTranslation(["auth", "common"]);
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated } = useAuth();

  const locationState = location.state as {
    from?: { pathname: string };
  } | null;
  const destination = locationState?.from?.pathname || "/profile";

  useEffect(() => {
    if (isAuthenticated) {
      navigate(destination, { replace: true });
    }
  }, [isAuthenticated, navigate, destination]);

  const handleSuccess = () => {
    navigate(destination, { replace: true });
  };

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Card elevation={2} sx={{ borderRadius: 3, p: { xs: 2, sm: 4 } }}>
        <CardContent>
          <Typography
            variant="h4"
            component="h1"
            align="center"
            gutterBottom
            sx={{ fontWeight: 700, color: "primary.main", mb: 1 }}
          >
            {t("auth:welcomeBack")}
          </Typography>
          <Typography
            variant="body1"
            align="center"
            color="text.secondary"
            sx={{ mb: 4 }}
          >
            {t("auth:login")}
          </Typography>

          <LoginForm onSuccess={handleSuccess} />
        </CardContent>
      </Card>
    </Container>
  );
};
