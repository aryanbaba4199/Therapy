import { baseApi } from "../../../store/api/base_api";
import type { ApiResponse } from "../../../common/types/api_types";

import type {
  CreateDateExceptionPayload,
  CreateExtraSlotPayload,
  DateException,
  ExtraSlot,
  SetWeeklySchedulePayload,
  TherapistAvailabilityResponse,
  WeeklySchedule,
} from "../types/availability.types";
import type { GeneratedSlot, SlotDiscoveryParams } from "../types/slot.types";

export const availabilityApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getTherapistAvailability: builder.query<
      ApiResponse<TherapistAvailabilityResponse>,
      string
    >({
      query: (therapistId) => `/therapists/${therapistId}/availability`,
      providesTags: (_result, _error, therapistId) => [
        { type: "Availability", id: therapistId },
      ],
    }),

    setWeeklySchedule: builder.mutation<
      ApiResponse<WeeklySchedule>,
      { therapistId: string; payload: SetWeeklySchedulePayload }
    >({
      query: ({ therapistId, payload }) => ({
        url: `/therapists/${therapistId}/availability`,
        method: "POST",
        body: payload,
      }),
      invalidatesTags: (_result, _error, { therapistId }) => [
        { type: "Availability", id: therapistId },
        { type: "Slot", id: therapistId },
      ],
    }),

    deleteWeeklySchedule: builder.mutation<
      ApiResponse<{ deleted: boolean }>,
      string
    >({
      query: (therapistId) => ({
        url: `/therapists/${therapistId}/availability`,
        method: "DELETE",
      }),
      invalidatesTags: (_result, _error, therapistId) => [
        { type: "Availability", id: therapistId },
        { type: "Slot", id: therapistId },
      ],
    }),

    upsertDateException: builder.mutation<
      ApiResponse<DateException>,
      { therapistId: string; payload: CreateDateExceptionPayload }
    >({
      query: ({ therapistId, payload }) => ({
        url: `/therapists/${therapistId}/availability/exceptions`,
        method: "POST",
        body: payload,
      }),
      invalidatesTags: (_result, _error, { therapistId }) => [
        { type: "Availability", id: therapistId },
        { type: "Slot", id: therapistId },
      ],
    }),

    deleteDateException: builder.mutation<
      ApiResponse<{ deleted: boolean }>,
      { therapistId: string; dateStr: string }
    >({
      query: ({ therapistId, dateStr }) => ({
        url: `/therapists/${therapistId}/availability/exceptions/${dateStr}`,
        method: "DELETE",
      }),
      invalidatesTags: (_result, _error, { therapistId }) => [
        { type: "Availability", id: therapistId },
        { type: "Slot", id: therapistId },
      ],
    }),

    listExtraSlots: builder.query<
      ApiResponse<ExtraSlot[]>,
      { therapistId: string; startDate?: string; endDate?: string }
    >({
      query: ({ therapistId, startDate, endDate }) => {
        const params = new URLSearchParams();
        if (startDate) params.set("start_date", startDate);
        if (endDate) params.set("end_date", endDate);
        const q = params.toString();
        return `/therapists/${therapistId}/extra-slots${q ? `?${q}` : ""}`;
      },
      providesTags: (_result, _error, { therapistId }) => [
        { type: "ExtraSlot", id: therapistId },
      ],
    }),

    createExtraSlot: builder.mutation<
      ApiResponse<ExtraSlot>,
      { therapistId: string; payload: CreateExtraSlotPayload }
    >({
      query: ({ therapistId, payload }) => ({
        url: `/therapists/${therapistId}/extra-slots`,
        method: "POST",
        body: payload,
      }),
      invalidatesTags: (_result, _error, { therapistId }) => [
        { type: "ExtraSlot", id: therapistId },
        { type: "Slot", id: therapistId },
      ],
    }),

    deleteExtraSlot: builder.mutation<
      ApiResponse<{ deleted: boolean }>,
      { therapistId: string; slotId: string }
    >({
      query: ({ therapistId, slotId }) => ({
        url: `/therapists/${therapistId}/extra-slots/${slotId}`,
        method: "DELETE",
      }),
      invalidatesTags: (_result, _error, { therapistId }) => [
        { type: "ExtraSlot", id: therapistId },
        { type: "Slot", id: therapistId },
      ],
    }),

    getAvailableSlots: builder.query<
      ApiResponse<GeneratedSlot[]>,
      SlotDiscoveryParams
    >({
      query: ({ therapist_id, date, start_date, end_date, session_mode }) => {
        const params = new URLSearchParams();
        if (date) params.set("date", date);
        if (start_date) params.set("start_date", start_date);
        if (end_date) params.set("end_date", end_date);
        if (session_mode) params.set("session_mode", session_mode);
        const q = params.toString();
        return `/therapists/${therapist_id}/slots${q ? `?${q}` : ""}`;
      },
      providesTags: (_result, _error, { therapist_id }) => [
        { type: "Slot", id: therapist_id },
      ],
    }),
  }),
});

export const {
  useGetTherapistAvailabilityQuery,
  useSetWeeklyScheduleMutation,
  useDeleteWeeklyScheduleMutation,
  useUpsertDateExceptionMutation,
  useDeleteDateExceptionMutation,
  useListExtraSlotsQuery,
  useCreateExtraSlotMutation,
  useDeleteExtraSlotMutation,
  useGetAvailableSlotsQuery,
} = availabilityApi;
