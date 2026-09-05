import React from "react";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router-dom";
import {
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Stack,
  Typography,
} from "@mui/material";
import { FaClock, FaGraduationCap, FaUser } from "react-icons/fa";
import {
  SessionModeBadge,
  SpecializationBadge,
  VerifiedBadge,
} from "./TherapistBadges";
import type { TherapistSummary } from "../types/therapist.types";

interface TherapistCardProps {
  therapist: TherapistSummary;
}

export const TherapistCard: React.FC<TherapistCardProps> = ({ therapist }) => {
  const { t } = useTranslation(["therapist", "common"]);

  const formattedPrice = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: therapist.pricing.currency || "INR",
    maximumFractionDigits: 0,
  }).format(therapist.pricing.amount);

  return (
    <Card
      elevation={1}
      sx={{
        borderRadius: 3,
        display: "flex",
        flexDirection: "column",
        height: "100%",
        transition: "all 0.2s ease-in-out",
        "&:hover": {
          elevation: 4,
          transform: "translateY(-4px)",
          boxShadow: "0 12px 24px -10px rgba(0, 0, 0, 0.12)",
        },
      }}
    >
      <CardContent
        sx={{ p: 3, flex: 1, display: "flex", flexDirection: "column" }}
      >
        {/* Header: Photo, Name & Badges */}
        <Stack direction="row" spacing={2} sx={{ mb: 2, alignItems: "center" }}>
          <Avatar
            src={therapist.profile_image_url || undefined}
            alt={therapist.display_name}
            sx={{
              width: 64,
              height: 64,
              bgcolor: "primary.main",
              fontWeight: 700,
              fontSize: "1.25rem",
              boxShadow: 1,
            }}
          >
            {therapist.display_name?.[0]?.toUpperCase() || <FaUser />}
          </Avatar>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1,
                flexWrap: "wrap",
              }}
            >
              <Typography
                variant="h6"
                component="h2"
                noWrap
                sx={{ fontWeight: 700, fontSize: "1.1rem" }}
              >
                {therapist.display_name}
              </Typography>
              {therapist.is_verified && <VerifiedBadge />}
            </Box>
            <Typography
              variant="body2"
              color="text.secondary"
              noWrap
              sx={{ mt: 0.25 }}
            >
              {therapist.designation}
            </Typography>
            <Box sx={{ mt: 0.5 }}>
              <SpecializationBadge specialization={therapist.specialization} />
            </Box>
          </Box>
        </Stack>

        {/* Experience & Therapy Hours */}
        <Stack
          direction="row"
          spacing={2}
          sx={{
            my: 1.5,
            py: 1,
            px: 1.5,
            bgcolor: "background.paper",
            border: "1px solid",
            borderColor: "divider",
            borderRadius: 2,
            alignItems: "center",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <FaGraduationCap className="text-gray-500 text-sm" />
            <Typography variant="caption" sx={{ fontWeight: 600 }}>
              {t("therapist:experience", { years: therapist.experience_years })}
            </Typography>
          </Box>
          <Divider orientation="vertical" flexItem />
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <FaClock className="text-gray-500 text-sm" />
            <Typography variant="caption" sx={{ fontWeight: 600 }}>
              {t("therapist:therapyHours", { hours: therapist.therapy_hours })}
            </Typography>
          </Box>
        </Stack>

        {/* Expertises / Tags */}
        <Box sx={{ my: 1.5, flex: 1 }}>
          <Stack
            direction="row"
            spacing={0.75}
            sx={{ gap: 0.75, flexWrap: "wrap" }}
          >
            {therapist.expertises.slice(0, 3).map((exp) => (
              <Chip
                key={exp}
                label={t(`therapist:expertises.${exp}`, {
                  defaultValue: exp.replace(/_/g, " "),
                })}
                size="small"
                variant="outlined"
                sx={{ fontSize: "0.7rem", height: 22, bgcolor: "grey.50" }}
              />
            ))}
            {therapist.expertises.length > 3 && (
              <Chip
                label={`+${therapist.expertises.length - 3}`}
                size="small"
                variant="outlined"
                sx={{ fontSize: "0.7rem", height: 22 }}
              />
            )}
          </Stack>
        </Box>

        {/* Session Modes & Languages */}
        <Stack
          direction="row"
          spacing={1}
          sx={{
            mb: 2,
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
          }}
        >
          <Stack direction="row" spacing={0.5} sx={{ flexWrap: "wrap" }}>
            {therapist.session_modes.map((mode) => (
              <SessionModeBadge key={mode} mode={mode} />
            ))}
          </Stack>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ fontWeight: 600 }}
          >
            {therapist.languages.map((l) => l.toUpperCase()).join(", ")}
          </Typography>
        </Stack>

        <Divider sx={{ my: 1.5 }} />

        {/* Pricing & CTA */}
        <Stack
          direction="row"
          sx={{
            alignItems: "center",
            justifyContent: "space-between",
            mt: "auto",
          }}
        >
          <Box>
            <Typography
              variant="h6"
              sx={{ fontWeight: 800, color: "text.primary", lineHeight: 1 }}
            >
              {formattedPrice}
            </Typography>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontSize: "0.65rem" }}
            >
              {t("therapist:perSession", {
                minutes: therapist.pricing.duration_minutes,
              })}
            </Typography>
          </Box>

          <Stack direction="row" spacing={1}>
            <Button
              component={RouterLink}
              to={`/therapists/${therapist.id}`}
              variant="outlined"
              size="small"
              sx={{ textTransform: "none", fontWeight: 600, borderRadius: 2 }}
            >
              {t("therapist:viewProfile")}
            </Button>
            <Button
              component={RouterLink}
              to={`/therapists/${therapist.id}`}
              variant="contained"
              color="primary"
              size="small"
              sx={{ textTransform: "none", fontWeight: 600, borderRadius: 2 }}
            >
              {t("therapist:bookNow")}
            </Button>
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
};
