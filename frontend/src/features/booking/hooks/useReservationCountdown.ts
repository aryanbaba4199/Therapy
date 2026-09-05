import { useCallback, useEffect, useState } from "react";

interface UseReservationCountdownProps {
  expiresAt: string | null | undefined;
  onExpire?: () => void;
}

export const useReservationCountdown = ({
  expiresAt,
  onExpire,
}: UseReservationCountdownProps) => {
  const calculateRemaining = useCallback((): number => {
    if (!expiresAt) return 0;
    const target = new Date(expiresAt).getTime();
    const now = Date.now();
    const diff = Math.max(0, Math.floor((target - now) / 1000));
    return diff;
  }, [expiresAt]);

  const [secondsRemaining, setSecondsRemaining] =
    useState<number>(calculateRemaining);

  useEffect(() => {
    if (!expiresAt) {
      setSecondsRemaining(0);
      return;
    }

    setSecondsRemaining(calculateRemaining());

    const interval = setInterval(() => {
      const remaining = calculateRemaining();
      setSecondsRemaining(remaining);
      if (remaining <= 0) {
        clearInterval(interval);
        onExpire?.();
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [expiresAt, calculateRemaining, onExpire]);

  const minutes = Math.floor(secondsRemaining / 60);
  const seconds = secondsRemaining % 60;
  const formatted = `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;

  return {
    secondsRemaining,
    formatted,
    isExpired: secondsRemaining <= 0,
  };
};
