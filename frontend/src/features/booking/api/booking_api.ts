import { baseApi } from "../../../store/api/base_api";
import type { ApiResponse } from "../../../common/types/api_types";
import type {
  BookingDetail,
  BookingListQueryParams,
  CancelBookingRequest,
  ConfirmBookingRequest,
  CreateReservationRequest,
  PaginatedBookings,
  Reservation,
} from "../types/booking.types";

export const bookingApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    createReservation: builder.mutation<
      ApiResponse<Reservation>,
      CreateReservationRequest
    >({
      query: (payload) => ({
        url: "/bookings/reservations",
        method: "POST",
        body: payload,
      }),
      invalidatesTags: (_result, _error, { therapist_id }) => [
        { type: "Slot", id: therapist_id },
        { type: "Reservation", id: "CURRENT" },
      ],
    }),

    getReservation: builder.query<ApiResponse<Reservation>, string>({
      query: (id) => `/bookings/reservations/${id}`,
      providesTags: (_result, _error, id) => [{ type: "Reservation", id }],
    }),

    cancelReservation: builder.mutation<
      ApiResponse<{ cancelled: boolean }>,
      string
    >({
      query: (id) => ({
        url: `/bookings/reservations/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: [
        { type: "Reservation", id: "CURRENT" },
        { type: "Slot" },
      ],
    }),

    confirmBooking: builder.mutation<
      ApiResponse<BookingDetail>,
      ConfirmBookingRequest
    >({
      query: (payload) => ({
        url: "/bookings/confirm",
        method: "POST",
        body: payload,
      }),
      invalidatesTags: [
        { type: "Booking", id: "LIST" },
        { type: "Reservation", id: "CURRENT" },
        { type: "Slot" },
      ],
    }),

    listBookings: builder.query<
      ApiResponse<PaginatedBookings>,
      BookingListQueryParams | void
    >({
      query: (params) => {
        const query = new URLSearchParams();
        if (params?.page) query.append("page", params.page.toString());
        if (params?.limit) query.append("limit", params.limit.toString());
        if (params?.filter) query.append("filter", params.filter);
        if (params?.status) query.append("status", params.status);
        const qs = query.toString();
        return `/bookings${qs ? `?${qs}` : ""}`;
      },
      providesTags: (result) =>
        result?.data?.items
          ? [
              ...result.data.items.map(({ id }) => ({
                type: "Booking" as const,
                id,
              })),
              { type: "Booking" as const, id: "LIST" },
            ]
          : [{ type: "Booking" as const, id: "LIST" }],
    }),

    getBookingDetail: builder.query<ApiResponse<BookingDetail>, string>({
      query: (id) => `/bookings/${id}`,
      providesTags: (_result, _error, id) => [{ type: "Booking", id }],
    }),

    cancelBooking: builder.mutation<
      ApiResponse<BookingDetail>,
      { bookingId: string; payload: CancelBookingRequest }
    >({
      query: ({ bookingId, payload }) => ({
        url: `/bookings/${bookingId}/cancel`,
        method: "POST",
        body: payload,
      }),
      invalidatesTags: (_result, _error, { bookingId }) => [
        { type: "Booking", id: bookingId },
        { type: "Booking", id: "LIST" },
        { type: "Slot" },
      ],
    }),
  }),
});

export const {
  useCreateReservationMutation,
  useGetReservationQuery,
  useCancelReservationMutation,
  useConfirmBookingMutation,
  useListBookingsQuery,
  useGetBookingDetailQuery,
  useCancelBookingMutation,
} = bookingApi;
