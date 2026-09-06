import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link as RouterLink, useNavigate, useParams } from "react-router-dom";
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
import { AvailabilityCalendar, SlotGrid, useSlots } from "../../availability";
import { useCreateReservationMutation } from "../../booking/api/booking_api";
import { useAuth } from "../../auth/hooks/useAuth";
import { useGetTherapistQuery } from "../api/therapist_api";
import { TherapistAudioPlayer } from "../components/TherapistAudioPlayer";
import {
  SessionModeBadge,
  SpecializationBadge,
  VerifiedBadge,
} from "../components/TherapistBadges";
import {
  ReviewCard,
  TherapistRatingSummary,
  useGetTherapistRatingSummaryQuery,
  useListTherapistReviewsQuery,
} from "../../review";

export const TherapistDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { isAuthenticated, hasRole } = useAuth();
  const canManageTherapist = hasRole("super_admin") || hasRole("admin");
  const [bookingError, setBookingError] = useState<string | null>(null);
  const [createReservation, { isLoading: isReserving }] =
    useCreateReservationMutation();
  const { t } = useTranslation(["therapist", "availability", "common"]);
  const {
    data: response,
    isLoading,
    isError,
  } = useGetTherapistQuery(id || "", {
    skip: !id,
  });

  const { data: ratingSummaryData, isLoading: isSummaryLoading } =
    useGetTherapistRatingSummaryQuery(id || "", { skip: !id });

  const { data: reviewsData, isLoading: isReviewsLoading } =
    useListTherapistReviewsQuery(
      { therapistId: id || "", page: 1, limit: 20 },
      { skip: !id }
    );

  const {
    selectedDate,
    setSelectedDate,
    selectedMode,
    setSelectedMode,
    selectedSlot,
    setSelectedSlot,
    groupedSlots,
    isLoading: isSlotsLoading,
    isError: isSlotsError,
  } = useSlots(id || "");

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
        {/* Navigation Breadcrumb & Admin Controls */}
        <Box
          sx={{
            mb: 4,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 2,
          }}
        >
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

          {canManageTherapist && (
            <Stack direction="row" spacing={1.5}>
              <Button
                variant="outlined"
                color="secondary"
                size="small"
                onClick={() => navigate("/operations/therapists")}
                sx={{
                  borderRadius: 2,
                  textTransform: "none",
                  fontWeight: 600,
                }}
              >
                Therapist Operations
              </Button>
              <Button
                variant="contained"
                color="primary"
                size="small"
                onClick={() => navigate("/admin/therapists/new")}
                sx={{
                  borderRadius: 2,
                  textTransform: "none",
                  fontWeight: 600,
                }}
              >
                + Add Therapist
              </Button>
            </Stack>
          )}
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

            {/* Availability & Slots Selection Card */}
            <Card
              elevation={2}
              sx={{ borderRadius: 3, p: { xs: 3, md: 5 }, mt: 4 }}
            >
              <Typography variant="h5" sx={{ fontWeight: 800, mb: 1 }}>
                {t("availability:availableSlots")}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                {t("availability:selectDate")}
              </Typography>

              {/* Date Calendar Ribbon */}
              <AvailabilityCalendar
                selectedDate={selectedDate}
                onSelectDate={(newDate) => {
                  setSelectedDate(newDate);
                  setSelectedSlot(null);
                }}
              />

              {/* Session Mode Filter Chips */}
              <Box
                sx={{
                  display: "flex",
                  gap: 1,
                  mb: 2,
                  flexWrap: "wrap",
                  alignItems: "center",
                }}
              >
                <Typography variant="caption" sx={{ fontWeight: 700, mr: 1 }}>
                  {t("availability:sessionMode")}:
                </Typography>
                <Chip
                  label={t("availability:allModes")}
                  variant={selectedMode === undefined ? "filled" : "outlined"}
                  color={selectedMode === undefined ? "primary" : "default"}
                  onClick={() => setSelectedMode(undefined)}
                  sx={{ fontWeight: 600, cursor: "pointer" }}
                />
                {therapist.session_modes.map((mode) => (
                  <Chip
                    key={mode}
                    label={t(`therapist:sessionMode.${mode}`)}
                    variant={selectedMode === mode ? "filled" : "outlined"}
                    color={selectedMode === mode ? "primary" : "default"}
                    onClick={() => setSelectedMode(mode)}
                    sx={{ fontWeight: 600, cursor: "pointer" }}
                  />
                ))}
              </Box>

              {/* Slots Grid */}
              <SlotGrid
                groupedSlots={groupedSlots}
                selectedSlot={selectedSlot}
                onSelectSlot={(slot) => setSelectedSlot(slot)}
                isLoading={isSlotsLoading}
                isError={isSlotsError}
              />
            </Card>

            {/* Client Reviews & Rating Summary */}
            <Card
              elevation={2}
              sx={{ borderRadius: 3, p: { xs: 3, md: 5 }, mt: 4 }}
            >
              <Typography variant="h5" sx={{ fontWeight: 800, mb: 3 }}>
                Client Reviews & Ratings
              </Typography>

              {isSummaryLoading ? (
                <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
                  <CircularProgress size={32} />
                </Box>
              ) : ratingSummaryData?.data ? (
                <TherapistRatingSummary summary={ratingSummaryData.data} />
              ) : null}

              <Divider sx={{ my: 4 }} />

              {isReviewsLoading ? (
                <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
                  <CircularProgress size={32} />
                </Box>
              ) : reviewsData?.data && reviewsData.data.length > 0 ? (
                <Stack spacing={2}>
                  {reviewsData.data.map((review) => (
                    <ReviewCard key={review.id} review={review} />
                  ))}
                </Stack>
              ) : (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ textAlign: "center", py: 2 }}
                >
                  No published reviews yet. Be the first to share your
                  experience after your consultation!
                </Typography>
              )}
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

                {/* Selected Slot Information */}
                {selectedSlot && (
                  <Box
                    sx={{
                      p: 2,
                      mb: 3,
                      borderRadius: 2,
                      backgroundColor: "primary.main",
                      color: "primary.contrastText",
                    }}
                  >
                    <Typography
                      variant="caption"
                      sx={{ fontWeight: 700, textTransform: "uppercase" }}
                    >
                      {t("availability:selectedSlot")}
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{ fontWeight: 700, mt: 0.5 }}
                    >
                      {new Date(selectedSlot.start_at).toLocaleDateString(
                        undefined,
                        {
                          weekday: "short",
                          month: "short",
                          day: "numeric",
                        }
                      )}
                    </Typography>
                    <Typography variant="body2">
                      {new Date(selectedSlot.start_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}{" "}
                      –{" "}
                      {new Date(selectedSlot.end_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </Typography>
                  </Box>
                )}

                {bookingError && (
                  <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
                    {bookingError}
                  </Alert>
                )}

                <Button
                  variant="contained"
                  color="primary"
                  size="large"
                  fullWidth
                  disabled={!selectedSlot || isReserving}
                  startIcon={
                    isReserving ? (
                      <CircularProgress size={18} color="inherit" />
                    ) : (
                      <FaCalendarCheck />
                    )
                  }
                  sx={{
                    py: 1.5,
                    borderRadius: 2.5,
                    fontWeight: 700,
                    fontSize: "1rem",
                    textTransform: "none",
                  }}
                  onClick={async () => {
                    if (!selectedSlot) return;
                    if (!isAuthenticated) {
                      navigate(`/login?redirect=/therapists/${therapist.id}`);
                      return;
                    }
                    try {
                      setBookingError(null);
                      const res = await createReservation({
                        therapist_id: therapist.id,
                        slot_id: selectedSlot.id,
                        slot_date: selectedDate,
                        session_mode: selectedSlot.session_mode,
                      }).unwrap();

                      if (res.data?.id) {
                        navigate(
                          `/bookings/checkout?reservationId=${res.data.id}`
                        );
                      }
                    } catch (err: unknown) {
                      const errorObj = err as { data?: { message?: string } };
                      setBookingError(
                        errorObj.data?.message ||
                          "Unable to hold this slot. It may have just been reserved."
                      );
                    }
                  }}
                >
                  {isReserving
                    ? "Reserving Slot..."
                    : selectedSlot
                      ? t("availability:bookSlot")
                      : t("availability:selectDate")}
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};
