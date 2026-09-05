import React from "react";
import {
  Box,
  Card,
  CardContent,
  LinearProgress,
  Typography,
} from "@mui/material";
import { FiStar } from "react-icons/fi";
import { useTranslation } from "react-i18next";
import type { TherapistRatingSummaryResponse } from "../types/review_types";

interface TherapistRatingSummaryProps {
  summary: TherapistRatingSummaryResponse;
}

export const TherapistRatingSummary: React.FC<TherapistRatingSummaryProps> = ({
  summary,
}) => {
  const { t } = useTranslation("review");
  const total = summary.review_count;

  return (
    <Card className="rounded-3xl border border-neutral-200/90 shadow-sm p-2 bg-gradient-to-br from-white to-amber-50/20">
      <CardContent className="p-6">
        <Box className="flex flex-col sm:flex-row items-center gap-8 justify-between">
          {/* Main Rating Score */}
          <Box className="flex flex-col items-center sm:items-start text-center sm:text-left space-y-1">
            <Typography
              variant="h2"
              className="font-black text-neutral-900 leading-none"
            >
              {summary.average_rating > 0
                ? summary.average_rating.toFixed(1)
                : "0.0"}
            </Typography>
            <Box className="flex items-center gap-1 py-1">
              {Array.from({ length: 5 }, (_, i) => {
                const isFilled = i + 1 <= Math.round(summary.average_rating);
                return (
                  <FiStar
                    key={i}
                    size={20}
                    className={
                      isFilled
                        ? "fill-amber-400 text-amber-400"
                        : "text-neutral-300"
                    }
                  />
                );
              })}
            </Box>
            <Typography
              variant="body2"
              className="text-neutral-500 font-medium"
            >
              {total === 1
                ? t("basedOnReviews", { count: total })
                : t("basedOnReviews_plural", { count: total })}
            </Typography>
          </Box>

          {/* Star Distribution Bars */}
          <Box className="w-full sm:max-w-xs space-y-1.5 flex-1">
            {[5, 4, 3, 2, 1].map((stars) => {
              const count = summary.distribution[stars.toString()] || 0;
              const percentage = total > 0 ? (count / total) * 100 : 0;

              return (
                <Box
                  key={stars}
                  className="flex items-center gap-2 text-xs text-neutral-600"
                >
                  <span className="w-12 text-right font-semibold shrink-0">
                    {stars} ★
                  </span>
                  <Box className="flex-1">
                    <LinearProgress
                      variant="determinate"
                      value={percentage}
                      className="h-2 rounded-full bg-neutral-100"
                      sx={{
                        "& .MuiLinearProgress-bar": {
                          backgroundColor: "#f59e0b",
                          borderRadius: "9999px",
                        },
                      }}
                    />
                  </Box>
                  <span className="w-8 text-neutral-400 text-right shrink-0 font-mono">
                    {count}
                  </span>
                </Box>
              );
            })}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};
