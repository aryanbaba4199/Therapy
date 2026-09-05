import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Box, Button, Stack, Typography } from "@mui/material";
import { FaCalendarAlt } from "react-icons/fa";

interface AvailabilityCalendarProps {
  selectedDate: string;
  onSelectDate: (date: string) => void;
  daysAhead?: number;
}

export const AvailabilityCalendar: React.FC<AvailabilityCalendarProps> = ({
  selectedDate,
  onSelectDate,
  daysAhead = 14,
}) => {
  const { t } = useTranslation(["availability", "common"]);

  const dateOptions = useMemo(() => {
    const dates: Array<{
      isoDate: string;
      dayOfWeek: string;
      dayNum: number;
      month: string;
      isToday: boolean;
    }> = [];

    const today = new Date();
    for (let i = 0; i < daysAhead; i++) {
      const d = new Date(today);
      d.setDate(today.getDate() + i);

      const isoDate = d.toISOString().split("T")[0] ?? "";
      const dayOfWeek = d.toLocaleDateString(undefined, { weekday: "short" });
      const dayNum = d.getDate();
      const month = d.toLocaleDateString(undefined, { month: "short" });

      dates.push({
        isoDate,
        dayOfWeek,
        dayNum,
        month,
        isToday: i === 0,
      });
    }
    return dates;
  }, [daysAhead]);

  return (
    <Box sx={{ width: "100%", mb: 3 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
        <FaCalendarAlt color="#0284c7" />
        <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
          {t("availability:selectDate")}
        </Typography>
      </Box>

      <Stack
        direction="row"
        spacing={1.5}
        sx={{
          overflowX: "auto",
          py: 1,
          px: 0.5,
          "&::-webkit-scrollbar": { height: 6 },
          "&::-webkit-scrollbar-thumb": {
            backgroundColor: "divider",
            borderRadius: 3,
          },
        }}
      >
        {dateOptions.map((item) => {
          const isSelected = item.isoDate === selectedDate;
          return (
            <Button
              key={item.isoDate}
              variant={isSelected ? "contained" : "outlined"}
              color={isSelected ? "primary" : "inherit"}
              onClick={() => onSelectDate(item.isoDate)}
              sx={{
                minWidth: 72,
                py: 1.5,
                px: 1,
                borderRadius: 2.5,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 0.5,
                borderColor: isSelected ? "primary.main" : "divider",
                backgroundColor: isSelected
                  ? "primary.main"
                  : "background.paper",
                color: isSelected ? "primary.contrastText" : "text.primary",
                boxShadow: isSelected ? 2 : 0,
                "&:hover": {
                  backgroundColor: isSelected ? "primary.dark" : "action.hover",
                },
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  fontWeight: 600,
                  textTransform: "uppercase",
                  color: isSelected ? "inherit" : "text.secondary",
                }}
              >
                {item.isToday
                  ? t("common:today", { defaultValue: "Today" })
                  : item.dayOfWeek}
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 800, lineHeight: 1 }}>
                {item.dayNum}
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  fontSize: "0.7rem",
                  color: isSelected ? "inherit" : "text.secondary",
                }}
              >
                {item.month}
              </Typography>
            </Button>
          );
        })}
      </Stack>
    </Box>
  );
};
