import React from "react";
import { Box, Card, CardContent, Typography } from "@mui/material";
import { FiCheckCircle, FiStar } from "react-icons/fi";
import { useTranslation } from "react-i18next";
import type { PublicReviewResponse } from "../types/review_types";

interface ReviewCardProps {
  review: PublicReviewResponse;
}

export const ReviewCard: React.FC<ReviewCardProps> = ({ review }) => {
  const { t } = useTranslation("review");
  const formattedDate = new Date(review.created_at).toLocaleDateString(
    undefined,
    {
      year: "numeric",
      month: "short",
      day: "numeric",
    }
  );

  return (
    <Card className="rounded-2xl border border-neutral-200/80 shadow-sm hover:shadow transition-all">
      <CardContent className="p-5 space-y-3">
        {/* Header: Rating & Date */}
        <Box className="flex items-center justify-between">
          <Box className="flex items-center gap-1">
            {Array.from({ length: 5 }, (_, i) => (
              <FiStar
                key={i}
                size={16}
                className={
                  i < review.rating
                    ? "fill-amber-400 text-amber-400"
                    : "text-neutral-200"
                }
              />
            ))}
          </Box>
          <Typography variant="caption" className="text-neutral-400">
            {formattedDate}
          </Typography>
        </Box>

        {/* Feedback Comment */}
        {review.comment && (
          <Typography
            variant="body2"
            className="text-neutral-700 leading-relaxed italic"
          >
            &ldquo;{review.comment}&rdquo;
          </Typography>
        )}

        {/* Client Attribution */}
        <Box className="flex items-center gap-1.5 pt-1 border-t border-neutral-100">
          <Typography variant="caption" className="font-bold text-neutral-800">
            {review.client_display_name}
          </Typography>
          <span className="inline-flex items-center gap-0.5 text-[10px] text-teal-700 font-medium bg-teal-50 px-1.5 py-0.5 rounded-full">
            <FiCheckCircle size={10} />
            <span>{t("verifiedClient")}</span>
          </span>
        </Box>
      </CardContent>
    </Card>
  );
};
