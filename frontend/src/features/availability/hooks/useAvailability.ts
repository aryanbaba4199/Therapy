import {
  useGetTherapistAvailabilityQuery,
  useListExtraSlotsQuery,
} from "../api/availability_api";

export function useAvailability(therapistId: string) {
  const {
    data: availabilityResponse,
    isLoading: isAvailabilityLoading,
    isError: isAvailabilityError,
    refetch: refetchAvailability,
  } = useGetTherapistAvailabilityQuery(therapistId, {
    skip: !therapistId,
  });

  const {
    data: extraSlotsResponse,
    isLoading: isExtraSlotsLoading,
    refetch: refetchExtraSlots,
  } = useListExtraSlotsQuery({ therapistId }, { skip: !therapistId });

  return {
    availability: availabilityResponse?.data,
    extraSlots: extraSlotsResponse?.data ?? [],
    isLoading: isAvailabilityLoading || isExtraSlotsLoading,
    isError: isAvailabilityError,
    refetch: () => {
      void refetchAvailability();
      void refetchExtraSlots();
    },
  };
}
