import React from "react";
import { useTranslation } from "react-i18next";
import { Link as RouterLink, useParams } from "react-router-dom";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  Divider,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import {
  FaArrowLeft,
  FaCalendarCheck,
  FaCheck,
  FaClock,
  FaGraduationCap,
  FaUser,
} from "react-icons/fa";
import { useGetTherapistQuery } from "../api/therapist_api";
import { TherapistAudioPlayer } from "../components/TherapistAudioPlayer";
import {
  SessionModeBadge,
  SpecializationBadge,
  VerifiedBadge,
} from "../components/TherapistBadges";

export const TherapistDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation(["therapist", "common"]);
  const {
    data: response,
    isLoading,
    isError,
  } = useGetTherapistQuery(id || "", {
    skip: !id,
  });

  const therapist = response?.data;

  if (isLoading) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "60vh",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !therapist) {
    return (
      <Container maxWidth="md" sx={{ py: 10, textAlign: "center" }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {t("therapist:error")}
        </Alert>
        <Button
          component={RouterLink}
          to="/therapists"
          startIcon={<FaArrowLeft />}
          variant="outlined"
        >
          {t("common:back")}
        </Button>
      </Container>
    );
  }

  const formattedPrice = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: therapist.pricing.currency || "INR",
    maximumFractionDigits: 0,
  }).format(therapist.pricing.amount);

  return (
    <Box sx={{ bgcolor: "grey.50", minHeight: "100vh", py: 6 }}>
      <Container maxWidth="lg">
        {/* Navigation Breadcrumb */}
        <Box sx={{ mb: 4 }}>
          <Button
            component={RouterLink}
            to="/therapists"
            startIcon={<FaArrowLeft className="text-xs" />}
            variant="text"
            sx={{
              textTransform: "none",
              color: "text.secondary",
              fontWeight: 600,
            }}
          >
            {t("therapist:title")}
          </Button>
        </Box>

        <Grid container spacing={4}>
          {/* Main Profile Info & Bio */}
          <Grid size={{ xs: 12, md: 8 }}>
            <Card
              elevation={1}
              sx={{ borderRadius: 3, p: { xs: 3, sm: 4 }, mb: 4 }}
            >
              {/* Header: Photo & Primary Credentials */}
              <Stack
                direction={{ xs: "column", sm: "row" }}
                spacing={3}
                sx={{ mb: 3, alignItems: { xs: "center", sm: "flex-start" } }}
              >
                <Avatar
                  src={therapist.profile_image_url || undefined}
                  alt={therapist.display_name}
                  sx={{
                    width: 100,
                    height: 100,
                    bgcolor: "primary.main",
                    fontWeight: 700,
                    fontSize: "2.5rem",
                    boxShadow: 2,
                  }}
                >
                  {therapist.display_name?.[0]?.toUpperCase() || <FaUser />}
                </Avatar>

                <Box sx={{ textAlign: { xs: "center", sm: "left" }, flex: 1 }}>
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 1.5,
                      flexWrap: "wrap",
                      justifyContent: { xs: "center", sm: "flex-start" },
                    }}
                  >
                    <Typography
                      variant="h4"
                      component="h1"
                      sx={{ fontWeight: 800 }}
                    >
                      {therapist.display_name}
                    </Typography>
                    {therapist.verification.status === "verified" && (
                      <VerifiedBadge />
                    )}
                  </Box>
                  <Typography
                    variant="h6"
                    color="text.secondary"
                    sx={{ mt: 0.5, fontWeight: 500, fontSize: "1.1rem" }}
                  >
                    {therapist.designation}
                  </Typography>
                  <Box sx={{ mt: 1 }}>
                    <SpecializationBadge
                      specialization={therapist.specialization}
                    />
                  </Box>

                  {/* Experience & Hours Stats */}
                  <Stack
                    direction="row"
                    spacing={3}
                    sx={{
                      mt: 2,
                      justifyContent: { xs: "center", sm: "flex-start" },
                    }}
                  >
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <FaGraduationCap className="text-gray-500" />
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {t("therapist:experience", {
                          years: therapist.experience_years,
                        })}
                      </Typography>
                    </Box>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <FaClock className="text-gray-500" />
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {t("therapist:therapyHours", {
                          hours: therapist.therapy_hours,
                        })}
                      </Typography>
                    </Box>
                  </Stack>
                </Box>
              </Stack>

              {/* Introduction Audio Player */}
              {therapist.introduction_audio_url && (
                <Box
                  sx={{
                    mb: 4,
                    pt: 2,
                    borderTop: "1px solid",
                    borderColor: "divider",
                  }}
                >
                  <TherapistAudioPlayer
                    audioUrl={therapist.introduction_audio_url}
                    displayName={therapist.display_name}
                  />
                </Box>
              )}

              <Divider sx={{ my: 3 }} />

              {/* Bio & Approach */}
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5 }}>
                {t("therapist:about")}
              </Typography>
              <Typography
                variant="body1"
                color="text.secondary"
                sx={{ lineHeight: 1.8, whiteSpace: "pre-line", mb: 4 }}
              >
                {therapist.bio}
              </Typography>

              {/* Qualifications */}
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5 }}>
                {t("therapist:qualifications")}
              </Typography>
              <Stack spacing={1} sx={{ mb: 4 }}>
                {therapist.qualifications.map((qual, idx) => (
                  <Box
                    key={idx}
                    sx={{ display: "flex", alignItems: "center", gap: 1.5 }}
                  >
                    <FaCheck className="text-emerald-500 text-xs" />
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {qual}
                    </Typography>
                  </Box>
                ))}
              </Stack>

              {/* Areas of Expertise */}
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5 }}>
                {t("therapist:areasOfExpertise")}
              </Typography>
              <Stack
                direction="row"
                spacing={1}
                sx={{ gap: 1, mb: 4, flexWrap: "wrap" }}
              >
                {therapist.expertises.map((exp) => (
                  <Chip
                    key={exp}
                    label={t(`therapist:expertises.${exp}`, {
                      defaultValue: exp.replace(/_/g, " "),
                    })}
                    variant="outlined"
                    color="primary"
                    sx={{ fontWeight: 500 }}
                  />
                ))}
              </Stack>

              {/* Languages Spoken */}
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5 }}>
                {t("therapist:languagesSpoken")}
              </Typography>
              <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                {therapist.languages.map((lang) => (
                  <Chip
                    key={lang}
                    label={lang.toUpperCase()}
                    variant="filled"
                    sx={{ fontWeight: 600 }}
                  />
                ))}
              </Stack>
            </Card>
          </Grid>

          {/* Booking / Action Card Sidebar */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Card
              elevation={2}
              sx={{ borderRadius: 3, p: 4, position: "sticky", top: 100 }}
            >
              <CardContent sx={{ p: 0 }}>
                <Typography
                  variant="overline"
                  color="text.secondary"
                  sx={{ fontWeight: 700 }}
                >
                  {t("therapist:pricing")}
                </Typography>
                <Typography
                  variant="h4"
                  sx={{
                    fontWeight: 800,
                    color: "text.primary",
                    mt: 0.5,
                    mb: 0.5,
                  }}
                >
                  {formattedPrice}
                </Typography>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 3 }}
                >
                  {t("therapist:perSession", {
                    minutes: therapist.pricing.duration_minutes,
                  })}
                </Typography>

                <Divider sx={{ mb: 3 }} />

                <Typography
                  variant="subtitle2"
                  sx={{ fontWeight: 700, mb: 1.5 }}
                >
                  {t("therapist:availableModes")}
                </Typography>
                <Stack spacing={1} sx={{ mb: 4 }}>
                  {therapist.session_modes.map((mode) => (
                    <Box
                      key={mode}
                      sx={{ display: "flex", alignItems: "center", gap: 1 }}
                    >
                      <SessionModeBadge mode={mode} />
                    </Box>
                  ))}
                </Stack>

                <Button
                  variant="contained"
                  color="primary"
                  size="large"
                  fullWidth
                  startIcon={<FaCalendarCheck />}
                  sx={{
                    py: 1.5,
                    borderRadius: 2.5,
                    fontWeight: 700,
                    fontSize: "1rem",
                    textTransform: "none",
                  }}
                  onClick={() => {
                    // Visual placeholder for Phase 4 / Phase 5 booking flow
                    alert(t("therapist:bookNow"));
                  }}
                >
                  {t("therapist:bookNow")}
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};
