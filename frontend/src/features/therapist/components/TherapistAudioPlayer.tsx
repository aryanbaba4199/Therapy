import React, { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, Card, IconButton, Slider, Typography } from "@mui/material";
import { FaPause, FaPlay, FaVolumeUp } from "react-icons/fa";

interface TherapistAudioPlayerProps {
  audioUrl?: string | null;
  displayName: string;
}

export const TherapistAudioPlayer: React.FC<TherapistAudioPlayerProps> = ({
  audioUrl,
  displayName,
}) => {
  const { t } = useTranslation(["therapist"]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [hasError, setHasError] = useState(false);

  if (!audioUrl) {
    return null;
  }

  const togglePlayPause = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current
        .play()
        .then(() => setIsPlaying(true))
        .catch(() => setHasError(true));
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const handleSeek = (_: Event, value: number | number[]) => {
    const newTime = typeof value === "number" ? value : (value[0] ?? 0);
    if (audioRef.current) {
      audioRef.current.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
  };

  if (hasError) {
    return (
      <Typography variant="caption" color="text.secondary">
        {t("therapist:audioError")}
      </Typography>
    );
  }

  return (
    <Card
      variant="outlined"
      sx={{
        p: 2,
        borderRadius: 2,
        bgcolor: "background.paper",
        display: "flex",
        alignItems: "center",
        gap: 2,
        width: "100%",
        maxWidth: 450,
      }}
    >
      <audio
        ref={audioRef}
        src={audioUrl}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={() => setIsPlaying(false)}
        onError={() => setHasError(true)}
      />

      <IconButton
        onClick={togglePlayPause}
        color="primary"
        aria-label={
          isPlaying ? "Pause" : `Play voice introduction of ${displayName}`
        }
        sx={{
          bgcolor: "primary.light",
          color: "primary.contrastText",
          "&:hover": { bgcolor: "primary.main" },
        }}
      >
        {isPlaying ? (
          <FaPause className="text-sm" />
        ) : (
          <FaPlay className="text-sm ml-0.5" />
        )}
      </IconButton>

      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
          <FaVolumeUp className="text-gray-500 text-xs" />
          <Typography
            variant="caption"
            sx={{ fontWeight: 600, color: "text.primary" }}
          >
            {t("therapist:audioIntro")}
          </Typography>
        </Box>
        <Slider
          size="small"
          value={currentTime}
          min={0}
          max={duration || 100}
          onChange={handleSeek}
          sx={{ py: 0.5 }}
        />
        <Box sx={{ display: "flex", justifyContent: "space-between" }}>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ fontSize: "0.65rem" }}
          >
            {formatTime(currentTime)}
          </Typography>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ fontSize: "0.65rem" }}
          >
            {formatTime(duration)}
          </Typography>
        </Box>
      </Box>
    </Card>
  );
};
