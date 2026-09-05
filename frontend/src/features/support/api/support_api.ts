import { baseApi } from "@/store/api/base_api";
import type { ApiResponse } from "@/common/types/api_types";
import type {
  CreateSupportMessageRequest,
  CreateSupportTicketRequest,
  SupportMessageResponse,
  SupportTicketDetailResponse,
  SupportTicketResponse,
  SupportTicketStatus,
} from "../types/support_types";

export const supportApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    createTicket: builder.mutation<
      ApiResponse<SupportTicketResponse>,
      CreateSupportTicketRequest
    >({
      query: (body) => ({
        url: "/support/tickets",
        method: "POST",
        body,
      }),
      invalidatesTags: ["SupportTicket"],
    }),

    listMyTickets: builder.query<
      ApiResponse<SupportTicketResponse[]>,
      { status?: SupportTicketStatus; page?: number; limit?: number } | void
    >({
      query: (params) => ({
        url: "/support/tickets",
        params: params || {},
      }),
      providesTags: ["SupportTicket"],
    }),

    getTicketById: builder.query<
      ApiResponse<SupportTicketDetailResponse>,
      string
    >({
      query: (id) => `/support/tickets/${id}`,
      providesTags: (_result, _err, id) => [
        { type: "SupportTicket", id },
        { type: "SupportMessage", id },
      ],
    }),

    sendMessage: builder.mutation<
      ApiResponse<SupportMessageResponse>,
      { ticketId: string; body: CreateSupportMessageRequest }
    >({
      query: ({ ticketId, body }) => ({
        url: `/support/tickets/${ticketId}/messages`,
        method: "POST",
        body,
      }),
      invalidatesTags: (_result, _err, { ticketId }) => [
        { type: "SupportMessage", id: ticketId },
        { type: "SupportTicket", id: ticketId },
      ],
    }),

    closeTicket: builder.mutation<ApiResponse<SupportTicketResponse>, string>({
      query: (ticketId) => ({
        url: `/support/tickets/${ticketId}/close`,
        method: "POST",
      }),
      invalidatesTags: (_result, _err, ticketId) => [
        { type: "SupportTicket", id: ticketId },
        "SupportTicket",
      ],
    }),
  }),
});

export const {
  useCreateTicketMutation,
  useListMyTicketsQuery,
  useGetTicketByIdQuery,
  useSendMessageMutation,
  useCloseTicketMutation,
} = supportApi;
