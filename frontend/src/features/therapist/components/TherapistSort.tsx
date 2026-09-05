import React from "react";
import { useTranslation } from "react-i18next";
import {
  FormControl,
  MenuItem,
  Select,
  type SelectChangeEvent,
} from "@mui/material";
import type { TherapistSortBy } from "../types/therapist.types";

interface TherapistSortProps {
  value: TherapistSortBy;
  onChange: (sort: TherapistSortBy) => void;
}

export const TherapistSort: React.FC<TherapistSortProps> = ({
  value,
  onChange,
}) => {
  const { t } = useTranslation(["therapist"]);

  const handleChange = (e: SelectChangeEvent<TherapistSortBy>) => {
    onChange(e.target.value as TherapistSortBy);
  };

  return (
    <FormControl size="small" sx={{ minWidth: 200 }}>
      <Select
        value={value}
        onChange={handleChange}
        displayEmpty
        sx={{
          borderRadius: 2,
          bgcolor: "background.paper",
          fontWeight: 600,
          fontSize: "0.875rem",
        }}
      >
        <MenuItem value="relevance">{t("therapist:sortRelevance")}</MenuItem>
        <MenuItem value="experience_desc">
          {t("therapist:sortExperience")}
        </MenuItem>
        <MenuItem value="price_asc">{t("therapist:sortPriceLow")}</MenuItem>
        <MenuItem value="price_desc">{t("therapist:sortPriceHigh")}</MenuItem>
        <MenuItem value="therapy_hours_desc">
          {t("therapist:sortHours")}
        </MenuItem>
      </Select>
    </FormControl>
  );
};
