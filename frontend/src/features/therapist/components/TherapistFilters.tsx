import React from "react";
import { useTranslation } from "react-i18next";
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  FormControl,
  MenuItem,
  Select,
  type SelectChangeEvent,
  Stack,
  Typography,
} from "@mui/material";
import { FaFilter, FaUndo } from "react-icons/fa";
import type {
  SessionMode,
  TherapistFilterParams,
  TherapistSpecialization,
} from "../types/therapist.types";

const SPECIALIZATIONS: TherapistSpecialization[] = [
  "consultant_psychologist",
  "clinical_psychologist",
  "sexual_health_specialist",
  "psychiatrist",
];

const SESSION_MODES: SessionMode[] = [
  "online",
  "offline_bangalore",
  "offline_kozhikode",
];

const LANGUAGES = [
  { code: "en", name: "English" },
  { code: "ml", name: "മലയാളം (Malayalam)" },
  { code: "ta", name: "தமிழ் (Tamil)" },
];

const COMMON_EXPERTISES = [
  "anxiety",
  "depression",
  "relationship",
  "adhd",
  "trauma",
  "work_stress",
  "parenting",
  "grief",
  "queer_affirmative",
  "self_esteem",
  "anger_management",
  "sleep_issues",
];

interface TherapistFiltersProps {
  filters: TherapistFilterParams;
  onChange: (filters: TherapistFilterParams) => void;
  onClear: () => void;
}

export const TherapistFilters: React.FC<TherapistFiltersProps> = ({
  filters,
  onChange,
  onClear,
}) => {
  const { t } = useTranslation(["therapist", "common"]);

  const hasActiveFilters = Boolean(
    filters.language ||
    filters.specialization ||
    filters.session_mode ||
    filters.expertise ||
    filters.search
  );

  const handleSpecializationChange = (e: SelectChangeEvent<string>) => {
    const val = e.target.value as TherapistSpecialization | "";
    onChange({ ...filters, specialization: val || undefined, page: 1 });
  };

  return (
    <Card elevation={1} sx={{ borderRadius: 3, height: "fit-content" }}>
      <CardContent sx={{ p: 3 }}>
        {/* Header */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            mb: 2,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <FaFilter className="text-oppam-dark text-sm" />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: "1rem" }}>
              {t("therapist:filters")}
            </Typography>
          </Box>
          {hasActiveFilters && (
            <Button
              size="small"
              variant="text"
              startIcon={<FaUndo className="text-xs" />}
              onClick={onClear}
              sx={{ textTransform: "none", fontSize: "0.75rem", p: 0.5 }}
            >
              {t("therapist:clearFilters")}
            </Button>
          )}
        </Box>

        <Divider sx={{ mb: 3 }} />

        <Stack spacing={3}>
          {/* Languages */}
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1.5 }}>
              {t("therapist:language")}
            </Typography>
            <Stack
              direction="row"
              spacing={1}
              sx={{ gap: 1, flexWrap: "wrap" }}
            >
              <Chip
                label={t("therapist:allLanguages")}
                size="small"
                clickable
                color={!filters.language ? "primary" : "default"}
                variant={!filters.language ? "filled" : "outlined"}
                onClick={() =>
                  onChange({ ...filters, language: undefined, page: 1 })
                }
              />
              {LANGUAGES.map((lang) => (
                <Chip
                  key={lang.code}
                  label={lang.name}
                  size="small"
                  clickable
                  color={filters.language === lang.code ? "primary" : "default"}
                  variant={
                    filters.language === lang.code ? "filled" : "outlined"
                  }
                  onClick={() =>
                    onChange({
                      ...filters,
                      language:
                        filters.language === lang.code ? undefined : lang.code,
                      page: 1,
                    })
                  }
                />
              ))}
            </Stack>
          </Box>

          <Divider />

          {/* Specialization */}
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1.5 }}>
              {t("therapist:specialization")}
            </Typography>
            <FormControl fullWidth size="small">
              <Select
                value={filters.specialization || ""}
                onChange={handleSpecializationChange}
                displayEmpty
                sx={{ borderRadius: 2 }}
              >
                <MenuItem value="">
                  {t("therapist:allSpecializations")}
                </MenuItem>
                {SPECIALIZATIONS.map((spec) => (
                  <MenuItem key={spec} value={spec}>
                    {t(`therapist:specializations.${spec}`, {
                      defaultValue: spec.replace(/_/g, " "),
                    })}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          <Divider />

          {/* Session Mode */}
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1.5 }}>
              {t("therapist:sessionMode")}
            </Typography>
            <Stack
              direction="row"
              spacing={1}
              sx={{ gap: 1, flexWrap: "wrap" }}
            >
              <Chip
                label={t("therapist:allModes")}
                size="small"
                clickable
                color={!filters.session_mode ? "primary" : "default"}
                variant={!filters.session_mode ? "filled" : "outlined"}
                onClick={() =>
                  onChange({ ...filters, session_mode: undefined, page: 1 })
                }
              />
              {SESSION_MODES.map((mode) => (
                <Chip
                  key={mode}
                  label={t(`therapist:sessionModes.${mode}`, {
                    defaultValue: mode.replace(/_/g, " "),
                  })}
                  size="small"
                  clickable
                  color={filters.session_mode === mode ? "primary" : "default"}
                  variant={
                    filters.session_mode === mode ? "filled" : "outlined"
                  }
                  onClick={() =>
                    onChange({
                      ...filters,
                      session_mode:
                        filters.session_mode === mode ? undefined : mode,
                      page: 1,
                    })
                  }
                />
              ))}
            </Stack>
          </Box>

          <Divider />

          {/* Concerns / Expertise */}
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1.5 }}>
              {t("therapist:expertise")}
            </Typography>
            <Stack
              direction="row"
              spacing={0.75}
              sx={{ gap: 0.75, flexWrap: "wrap" }}
            >
              {COMMON_EXPERTISES.map((exp) => (
                <Chip
                  key={exp}
                  label={t(`therapist:expertises.${exp}`, {
                    defaultValue: exp.replace(/_/g, " "),
                  })}
                  size="small"
                  clickable
                  color={filters.expertise === exp ? "secondary" : "default"}
                  variant={filters.expertise === exp ? "filled" : "outlined"}
                  onClick={() =>
                    onChange({
                      ...filters,
                      expertise: filters.expertise === exp ? undefined : exp,
                      page: 1,
                    })
                  }
                  sx={{ fontSize: "0.75rem" }}
                />
              ))}
            </Stack>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
};
