import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, Container, Typography } from "@mui/material";
import { RegisterForm } from "../components/RegisterForm";
import { useAuth } from "../hooks/useAuth";

export const RegisterPage: React.FC = () => {
  const { t } = useTranslation(["auth", "common"]);
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/profile", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSuccess = () => {
    navigate("/profile", { replace: true });
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
            {t("auth:register")}
          </Typography>

          <RegisterForm onSuccess={handleSuccess} />
        </CardContent>
      </Card>
    </Container>
  );
};
