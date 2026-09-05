import React, { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  TextField,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { useCreateReviewMutation } from "../api/review_api";
import { RatingInput } from "./RatingInput";

interface ReviewFormModalProps {
  open: boolean;
  onClose: () => void;
  sessionId: string;
  therapistName?: string;
  onSuccess?: () => void;
}

export const ReviewFormModal: React.FC<ReviewFormModalProps> = ({
  open,
  onClose,
  sessionId,
  therapistName,
  onSuccess,
}) => {
  const { t } = useTranslation(["review", "common"]);
  const [rating, setRating] = useState<number>(5);
  const [comment, setComment] = useState<string>("");
  const [isAnonymous, setIsAnonymous] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [createReview, { isLoading }] = useCreateReviewMutation();

  const handleSubmit = async () => {
    setErrorMessage(null);
    try {
      await createReview({
        session_id: sessionId,
        rating,
        comment: comment.trim() || undefined,
        is_anonymous: isAnonymous,
      }).unwrap();

      if (onSuccess) {
        onSuccess();
      }
      onClose();
    } catch (err: unknown) {
      const errorObj = err as {
        data?: { error?: { message?: string; code?: string } };
      };
      const code = errorObj.data?.error?.code;
      if (code === "REVIEW_ALREADY_EXISTS") {
        setErrorMessage(t("review:alreadyReviewed"));
      } else if (code === "REVIEW_NOT_ELIGIBLE") {
        setErrorMessage(t("review:onlyCompletedEligible"));
      } else {
        setErrorMessage(
          errorObj.data?.error?.message || "Failed to submit review."
        );
      }
    }
  };

  return (
    <Dialog
      open={open}
      onClose={!isLoading ? onClose : undefined}
      maxWidth="sm"
      fullWidth
      slotProps={{ paper: { className: "rounded-3xl p-2" } }}
    >
      <DialogTitle className="font-bold text-neutral-900 pb-1">
        {therapistName
          ? t("review:reviewPrompt", { therapist: therapistName })
          : t("review:writeReview")}
      </DialogTitle>
      <DialogContent className="space-y-4 pt-2">
        <Typography variant="body2" className="text-neutral-500">
          {t("review:reviewPromptSubtitle")}
        </Typography>

        {errorMessage && (
          <Alert severity="error" className="rounded-2xl">
            {errorMessage}
          </Alert>
        )}

        {/* Rating Selector */}
        <Box className="flex flex-col items-center justify-center p-6 bg-amber-50/50 rounded-2xl border border-amber-100 space-y-2">
          <Typography
            variant="subtitle2"
            className="font-semibold text-neutral-700"
          >
            {t("review:selectRating")}
          </Typography>
          <RatingInput
            value={rating}
            onChange={(val) => setRating(val)}
            size={36}
            disabled={isLoading}
          />
        </Box>

        {/* Written Comment */}
        <Box className="space-y-1">
          <Typography
            variant="body2"
            className="font-semibold text-neutral-800"
          >
            {t("review:yourFeedback")}
          </Typography>
          <TextField
            multiline
            rows={4}
            fullWidth
            placeholder={t("review:feedbackPlaceholder")}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            disabled={isLoading}
            slotProps={{
              input: {
                className: "rounded-2xl bg-neutral-50/70",
              },
            }}
          />
        </Box>

        {/* Anonymous Option */}
        <Box className="p-3 bg-neutral-50 rounded-2xl">
          <FormControlLabel
            control={
              <Checkbox
                checked={isAnonymous}
                onChange={(e) => setIsAnonymous(e.target.checked)}
                color="primary"
                disabled={isLoading}
              />
            }
            label={
              <Box>
                <Typography
                  variant="body2"
                  className="font-semibold text-neutral-800"
                >
                  {t("review:anonymousReview")}
                </Typography>
                <Typography
                  variant="caption"
                  className="text-neutral-500 block"
                >
                  {t("review:anonymousNotice")}
                </Typography>
              </Box>
            }
          />
        </Box>
      </DialogContent>
      <DialogActions className="p-4">
        <Button
          onClick={onClose}
          color="inherit"
          disabled={isLoading}
          className="rounded-xl normal-case"
        >
          {t("common:cancel")}
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          color="primary"
          disabled={isLoading || rating < 1}
          className="rounded-xl font-bold normal-case px-6"
        >
          {isLoading ? (
            <CircularProgress size={20} color="inherit" />
          ) : (
            t("review:submitReview")
          )}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
