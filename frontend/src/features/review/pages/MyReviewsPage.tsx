import React from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Typography,
} from "@mui/material";
import { FiCalendar, FiStar } from "react-icons/fi";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useListMyReviewsQuery } from "../api/review_api";

export const MyReviewsPage: React.FC = () => {
  const { t } = useTranslation(["review", "common"]);
  const navigate = useNavigate();

  const { data, isLoading, isError, refetch } = useListMyReviewsQuery();
  const reviews = data?.data || [];

  return (
    <Container maxWidth="md" className="py-10 space-y-6">
      <Box>
        <Typography
          variant="h4"
          className="font-extrabold text-neutral-900 tracking-tight"
        >
          {t("review:myReviews")}
        </Typography>
        <Typography variant="body1" className="text-neutral-500 mt-1">
          {t("review:myReviewsSubtitle")}
        </Typography>
      </Box>

      {isLoading ? (
        <Box className="flex justify-center py-20">
          <CircularProgress color="primary" />
        </Box>
      ) : isError ? (
        <Box className="text-center py-16 bg-red-50 rounded-3xl border border-red-100 p-6">
          <Typography variant="h6" className="text-red-700 font-bold mb-2">
            Failed to load reviews
          </Typography>
          <Button variant="outlined" color="primary" onClick={() => refetch()}>
            Retry
          </Button>
        </Box>
      ) : reviews.length === 0 ? (
        <Box className="text-center py-20 bg-neutral-50 rounded-3xl border border-dashed border-neutral-200 space-y-3">
          <FiStar size={40} className="mx-auto text-neutral-400" />
          <Typography variant="body1" className="text-neutral-600 font-medium">
            {t("review:noReviews")}
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate("/my-sessions")}
            className="rounded-xl normal-case"
          >
            View Completed Consultations
          </Button>
        </Box>
      ) : (
        <Box className="space-y-4">
          {reviews.map((rev) => {
            const formattedDate = new Date(rev.created_at).toLocaleDateString(
              undefined,
              {
                year: "numeric",
                month: "short",
                day: "numeric",
              }
            );

            return (
              <Card
                key={rev.id}
                className="rounded-2xl border border-neutral-200 shadow-sm p-2"
              >
                <CardContent className="space-y-3 p-4">
                  <Box className="flex items-center justify-between">
                    <Box className="flex items-center gap-1">
                      {Array.from({ length: 5 }, (_, i) => (
                        <FiStar
                          key={i}
                          size={18}
                          className={
                            i < rev.rating
                              ? "fill-amber-400 text-amber-400"
                              : "text-neutral-200"
                          }
                        />
                      ))}
                    </Box>
                    <Box className="flex items-center gap-1 text-xs text-neutral-400">
                      <FiCalendar size={12} />
                      <span>{formattedDate}</span>
                    </Box>
                  </Box>

                  {rev.comment && (
                    <Typography
                      variant="body2"
                      className="text-neutral-700 italic"
                    >
                      &ldquo;{rev.comment}&rdquo;
                    </Typography>
                  )}

                  <Box className="flex items-center justify-between pt-2 border-t border-neutral-100 text-xs text-neutral-500">
                    <span className="font-mono">
                      Session #{rev.session_id.slice(-6).toUpperCase()}
                    </span>
                    <span className="capitalize">
                      {rev.is_anonymous
                        ? "Submitted Anonymously"
                        : rev.client_display_name}
                    </span>
                  </Box>
                </CardContent>
              </Card>
            );
          })}
        </Box>
      )}
    </Container>
  );
};
