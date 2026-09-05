import React from "react";
import { useTranslation } from "react-i18next";
import { Chip } from "@mui/material";
import { FaCheckCircle, FaLaptop, FaMapMarkerAlt } from "react-icons/fa";
import type {
  SessionMode,
  TherapistSpecialization,
} from "../types/therapist.types";

export const VerifiedBadge: React.FC = () => {
  const { t } = useTranslation(["therapist"]);
  return (
    <Chip
      icon={<FaCheckCircle className="text-emerald-500" />}
      label={t("therapist:verified")}
      size="small"
      color="success"
      variant="outlined"
      sx={{ fontWeight: 600, fontSize: "0.7rem", height: 24 }}
    />
  );
};

interface SpecializationBadgeProps {
  specialization: TherapistSpecialization;
}

export const SpecializationBadge: React.FC<SpecializationBadgeProps> = ({
  specialization,
}) => {
  const { t } = useTranslation(["therapist"]);
  const label = t(`therapist:specializations.${specialization}`, {
    defaultValue: specialization.replace(/_/g, " "),
  });

  return (
    <Chip
      label={label}
      size="small"
      color="primary"
      variant="filled"
      sx={{ fontWeight: 600, fontSize: "0.75rem" }}
    />
  );
};

interface SessionModeBadgeProps {
  mode: SessionMode;
}

export const SessionModeBadge: React.FC<SessionModeBadgeProps> = ({ mode }) => {
  const { t } = useTranslation(["therapist"]);
  const label = t(`therapist:sessionModes.${mode}`, {
    defaultValue: mode.replace(/_/g, " "),
  });

  const icon =
    mode === "online" ? (
      <FaLaptop className="text-blue-500 text-xs" />
    ) : (
      <FaMapMarkerAlt className="text-amber-500 text-xs" />
    );

  return (
    <Chip
      icon={icon}
      label={label}
      size="small"
      variant="outlined"
      sx={{ fontSize: "0.7rem", height: 24 }}
    />
  );
};
