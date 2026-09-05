import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { IconButton, InputAdornment, TextField } from "@mui/material";
import { FaSearch, FaTimes } from "react-icons/fa";

interface TherapistSearchProps {
  value: string;
  onChange: (query: string) => void;
  debounceMs?: number;
}

export const TherapistSearch: React.FC<TherapistSearchProps> = ({
  value,
  onChange,
  debounceMs = 300,
}) => {
  const { t } = useTranslation(["therapist"]);
  const [searchTerm, setSearchTerm] = useState(value);

  useEffect(() => {
    setSearchTerm(value);
  }, [value]);

  useEffect(() => {
    const handler = setTimeout(() => {
      if (searchTerm !== value) {
        onChange(searchTerm);
      }
    }, debounceMs);

    return () => clearTimeout(handler);
  }, [searchTerm, onChange, debounceMs, value]);

  const handleClear = () => {
    setSearchTerm("");
    onChange("");
  };

  return (
    <TextField
      fullWidth
      variant="outlined"
      placeholder={t("therapist:searchPlaceholder")}
      value={searchTerm}
      onChange={(e) => setSearchTerm(e.target.value)}
      slotProps={{
        input: {
          startAdornment: (
            <InputAdornment position="start">
              <FaSearch className="text-gray-400 text-sm" />
            </InputAdornment>
          ),
          endAdornment: searchTerm ? (
            <InputAdornment position="end">
              <IconButton
                size="small"
                onClick={handleClear}
                aria-label="Clear search"
              >
                <FaTimes className="text-xs" />
              </IconButton>
            </InputAdornment>
          ) : null,
          sx: {
            borderRadius: 3,
            bgcolor: "background.paper",
            boxShadow: "0 2px 6px rgba(0,0,0,0.04)",
          },
        },
      }}
    />
  );
};
