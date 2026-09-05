import { baseApi } from "@/store/api/base_api";
import type { ApiResponse } from "@/common/types/api_types";
import type {
  AdminDashboardMetrics,
  AssignLeadRequest,
  AuditLog,
  BookingOperationalView,
  CreateLeadRequest,
  Lead,
  LeadStatus,
  OperationUserDetail,
  PaymentOperationalView,
  UpdateLeadRequest,
  UpdateUserRolesRequest,
  UpdateUserStatusRequest,
} from "../types/operations_types";
import type { TherapistDetail } from "@/features/therapist/types/therapist.types";

export const operationsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getDashboardMetrics: builder.query<
      ApiResponse<AdminDashboardMetrics>,
      void
    >({
      query: () => "/operations/dashboard/metrics",
      providesTags: ["OperationsMetrics"],
    }),

    listUsers: builder.query<
      ApiResponse<OperationUserDetail[]>,
      {
        role?: string;
        status?: string;
        search?: string;
        page?: number;
        limit?: number;
      } | void
    >({
      query: (params) => ({
        url: "/operations/users",
        params: params || {},
      }),
      providesTags: ["OperationsUser"],
    }),

    getUserDetail: builder.query<ApiResponse<OperationUserDetail>, string>({
      query: (userId) => `/operations/users/${userId}`,
      providesTags: (_res, _err, id) => [{ type: "OperationsUser", id }],
    }),

    updateUserStatus: builder.mutation<
      ApiResponse<OperationUserDetail>,
      { userId: string; body: UpdateUserStatusRequest }
    >({
      query: ({ userId, body }) => ({
        url: `/operations/users/${userId}/status`,
        method: "PATCH",
        body,
      }),
      invalidatesTags: ["OperationsUser", "OperationsMetrics", "AuditLog"],
    }),

    updateUserRoles: builder.mutation<
      ApiResponse<OperationUserDetail>,
      { userId: string; body: UpdateUserRolesRequest }
    >({
      query: ({ userId, body }) => ({
        url: `/operations/users/${userId}/roles`,
        method: "PATCH",
        body,
      }),
      invalidatesTags: ["OperationsUser", "AuditLog"],
    }),

    listTherapistsOperational: builder.query<
      ApiResponse<TherapistDetail[]>,
      {
        status?: string;
        verification_status?: string;
        page?: number;
        limit?: number;
      } | void
    >({
      query: (params) => ({
        url: "/operations/therapists",
        params: params || {},
      }),
      providesTags: ["Therapist"],
    }),

    verifyTherapist: builder.mutation<
      ApiResponse<TherapistDetail>,
      {
        therapistId: string;
        body: { status: string; rejection_reason?: string };
      }
    >({
      query: ({ therapistId, body }) => ({
        url: `/operations/therapists/${therapistId}/verify`,
        method: "PATCH",
        body,
      }),
      invalidatesTags: ["Therapist", "OperationsMetrics", "AuditLog"],
    }),

    listBookingsOperational: builder.query<
      ApiResponse<BookingOperationalView[]>,
      {
        status?: string;
        therapist_id?: string;
        client_id?: string;
        page?: number;
        limit?: number;
      } | void
    >({
      query: (params) => ({
        url: "/operations/bookings",
        params: params || {},
      }),
      providesTags: ["Booking"],
    }),

    listPaymentsOperational: builder.query<
      ApiResponse<PaymentOperationalView[]>,
      {
        status?: string;
        provider?: string;
        user_id?: string;
        page?: number;
        limit?: number;
      } | void
    >({
      query: (params) => ({
        url: "/operations/payments",
        params: params || {},
      }),
      providesTags: ["Payment"],
    }),

    listLeads: builder.query<
      ApiResponse<Lead[]>,
      {
        status?: LeadStatus;
        assigned_to?: string;
        search?: string;
        page?: number;
        limit?: number;
      } | void
    >({
      query: (params) => ({
        url: "/operations/leads",
        params: params || {},
      }),
      providesTags: ["Lead"],
    }),

    getLeadById: builder.query<ApiResponse<Lead>, string>({
      query: (leadId) => `/operations/leads/${leadId}`,
      providesTags: (_res, _err, id) => [{ type: "Lead", id }],
    }),

    createLead: builder.mutation<ApiResponse<Lead>, CreateLeadRequest>({
      query: (body) => ({
        url: "/operations/leads",
        method: "POST",
        body,
      }),
      invalidatesTags: ["Lead", "OperationsMetrics", "AuditLog"],
    }),

    updateLead: builder.mutation<
      ApiResponse<Lead>,
      { leadId: string; body: UpdateLeadRequest }
    >({
      query: ({ leadId, body }) => ({
        url: `/operations/leads/${leadId}`,
        method: "PATCH",
        body,
      }),
      invalidatesTags: ["Lead", "OperationsMetrics", "AuditLog"],
    }),

    assignLead: builder.mutation<
      ApiResponse<Lead>,
      { leadId: string; body: AssignLeadRequest }
    >({
      query: ({ leadId, body }) => ({
        url: `/operations/leads/${leadId}/assign`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["Lead", "AuditLog"],
    }),

    convertLeadToUser: builder.mutation<
      ApiResponse<Lead>,
      { leadId: string; userId: string }
    >({
      query: ({ leadId, userId }) => ({
        url: `/operations/leads/${leadId}/convert/${userId}`,
        method: "POST",
      }),
      invalidatesTags: ["Lead", "OperationsMetrics", "AuditLog"],
    }),

    listAuditLogs: builder.query<
      ApiResponse<AuditLog[]>,
      {
        actor_id?: string;
        resource_type?: string;
        resource_id?: string;
        action?: string;
        page?: number;
        limit?: number;
      } | void
    >({
      query: (params) => ({
        url: "/operations/audit-logs",
        params: params || {},
      }),
      providesTags: ["AuditLog"],
    }),
  }),
});

export const {
  useGetDashboardMetricsQuery,
  useListUsersQuery,
  useGetUserDetailQuery,
  useUpdateUserStatusMutation,
  useUpdateUserRolesMutation,
  useListTherapistsOperationalQuery,
  useVerifyTherapistMutation,
  useListBookingsOperationalQuery,
  useListPaymentsOperationalQuery,
  useListLeadsQuery,
  useGetLeadByIdQuery,
  useCreateLeadMutation,
  useUpdateLeadMutation,
  useAssignLeadMutation,
  useConvertLeadToUserMutation,
  useListAuditLogsQuery,
} = operationsApi;
