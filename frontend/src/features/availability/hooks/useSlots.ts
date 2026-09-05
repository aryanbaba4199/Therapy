import { useMemo, useState } from "react";
import type { SessionMode } from "../../therapist/types/therapist.types";
import { useGetAvailableSlotsQuery } from "../api/availability_api";
import type { GeneratedSlot, GroupedSlots } from "../types/slot.types";

export function useSlots(therapistId: string, initialMode?: SessionMode) {
  const [selectedDate, setSelectedDate] = useState<string>(() => {
    return new Date().toISOString().split("T")[0] ?? "";
  });
  const [selectedMode, setSelectedMode] = useState<SessionMode | undefined>(
    initialMode
  );
  const [selectedSlot, setSelectedSlot] = useState<GeneratedSlot | null>(null);

  const {
    data: response,
    isLoading,
    isFetching,
    isError,
    refetch,
  } = useGetAvailableSlotsQuery(
    {
      therapist_id: therapistId,
      date: selectedDate,
      session_mode: selectedMode,
    },
    {
      skip: !therapistId || !selectedDate,
    }
  );

  const slots = useMemo<GeneratedSlot[]>(() => {
    return response?.data ?? [];
  }, [response?.data]);

  const groupedSlots = useMemo<GroupedSlots>(() => {
    const groups: GroupedSlots = {
      morning: [],
      afternoon: [],
      evening: [],
    };

    for (const slot of slots) {
      const dt = new Date(slot.start_at);
      const hours = dt.getHours();
      if (hours < 12) {
        groups.morning.push(slot);
      } else if (hours < 17) {
        groups.afternoon.push(slot);
      } else {
        groups.evening.push(slot);
      }
    }

    return groups;
  }, [slots]);

  return {
    selectedDate,
    setSelectedDate,
    selectedMode,
    setSelectedMode,
    selectedSlot,
    setSelectedSlot,
    slots,
    groupedSlots,
    isLoading: isLoading || isFetching,
    isError,
    refetch,
  };
}
