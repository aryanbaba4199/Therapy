import { baseApi } from "@/store/api/base_api";
import type { ApiResponse } from "@/common/types/api_types";
import type {
  ClientSessionNoteResponse,
  ClientSessionResponse,
  CreateTherapyGoalRequest,
  RecordAttendanceRequest,
  SessionNoteResponse,
  SessionResponse,
  SessionStatus,
  TherapistDashboardSummaryResponse,
  TherapyGoalResponse,
  UpdateTherapyGoalRequest,
  UpsertSessionNoteRequest,
} from "../types/session_types";

export const sessionApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getTherapistDashboard: builder.query<
      ApiResponse<TherapistDashboardSummaryResponse>,
      void
    >({
      query: () => "/therapist/portal/dashboard",
      providesTags: ["TherapistDashboard"],
    }),

    listTherapistSessions: builder.query<
      ApiResponse<SessionResponse[]>,
      {
        status?: SessionStatus;
        date_filter?: string;
        page?: number;
        limit?: number;
      } | void
    >({
      query: (params) => ({
        url: "/therapist/portal/sessions",
        params: params || {},
      }),
      providesTags: ["Session"],
    }),

    getSessionById: builder.query<ApiResponse<SessionResponse>, string>({
      query: (id) => `/sessions/${id}`,
      providesTags: (_result, _err, id) => [{ type: "Session", id }],
    }),

    getClientSession: builder.query<ApiResponse<ClientSessionResponse>, string>(
      {
        query: (id) => `/sessions/${id}/client-view`,
        providesTags: (_result, _err, id) => [{ type: "Session", id }],
      }
    ),

    startSession: builder.mutation<ApiResponse<SessionResponse>, string>({
      query: (id) => ({
        url: `/sessions/${id}/start`,
        method: "POST",
      }),
      invalidatesTags: ["Session", "TherapistDashboard"],
    }),

    completeSession: builder.mutation<ApiResponse<SessionResponse>, string>({
      query: (id) => ({
        url: `/sessions/${id}/complete`,
        method: "POST",
      }),
      invalidatesTags: ["Session", "TherapistDashboard"],
    }),

    recordAttendance: builder.mutation<
      ApiResponse<SessionResponse>,
      { id: string; body: RecordAttendanceRequest }
    >({
      query: ({ id, body }) => ({
        url: `/sessions/${id}/attendance`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["Session", "TherapistDashboard"],
    }),

    getSessionNote: builder.query<ApiResponse<SessionNoteResponse>, string>({
      query: (sessionId) => `/sessions/${sessionId}/notes`,
      providesTags: (_result, _err, sessionId) => [
        { type: "SessionNote", id: sessionId },
      ],
    }),

    getClientSessionNote: builder.query<
      ApiResponse<ClientSessionNoteResponse>,
      string
    >({
      query: (sessionId) => `/sessions/${sessionId}/notes/client`,
      providesTags: (_result, _err, sessionId) => [
        { type: "SessionNote", id: sessionId },
      ],
    }),

    upsertSessionNote: builder.mutation<
      ApiResponse<SessionNoteResponse>,
      { sessionId: string; body: UpsertSessionNoteRequest }
    >({
      query: ({ sessionId, body }) => ({
        url: `/sessions/${sessionId}/notes`,
        method: "POST",
        body,
      }),
      invalidatesTags: (_result, _err, { sessionId }) => [
        { type: "SessionNote", id: sessionId },
      ],
    }),

    listGoals: builder.query<ApiResponse<TherapyGoalResponse[]>, string>({
      query: (sessionId) => `/sessions/${sessionId}/goals`,
      providesTags: ["TherapyGoal"],
    }),

    createGoal: builder.mutation<
      ApiResponse<TherapyGoalResponse>,
      { sessionId: string; body: CreateTherapyGoalRequest }
    >({
      query: ({ sessionId, body }) => ({
        url: `/sessions/${sessionId}/goals`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["TherapyGoal"],
    }),

    updateGoal: builder.mutation<
      ApiResponse<TherapyGoalResponse>,
      { goalId: string; body: UpdateTherapyGoalRequest }
    >({
      query: ({ goalId, body }) => ({
        url: `/sessions/goals/${goalId}`,
        method: "PATCH",
        body,
      }),
      invalidatesTags: ["TherapyGoal"],
    }),

    listMySessions: builder.query<
      ApiResponse<ClientSessionResponse[]>,
      { status?: SessionStatus; page?: number; limit?: number } | void
    >({
      query: (params) => ({
        url: "/sessions/my/sessions",
        params: params || {},
      }),
      providesTags: ["Session"],
    }),

    retryMeeting: builder.mutation<ApiResponse<SessionResponse>, string>({
      query: (sessionId) => ({
        url: `/sessions/${sessionId}/meeting/retry`,
        method: "POST",
      }),
      invalidatesTags: (_result, _err, sessionId) => [
        { type: "Session", id: sessionId },
        "Session",
        "TherapistDashboard",
      ],
    }),
  }),
});

export const {
  useGetTherapistDashboardQuery,
  useListTherapistSessionsQuery,
  useGetSessionByIdQuery,
  useGetClientSessionQuery,
  useStartSessionMutation,
  useCompleteSessionMutation,
  useRecordAttendanceMutation,
  useGetSessionNoteQuery,
  useGetClientSessionNoteQuery,
  useUpsertSessionNoteMutation,
  useListGoalsQuery,
  useCreateGoalMutation,
  useUpdateGoalMutation,
  useListMySessionsQuery,
  useRetryMeetingMutation,
} = sessionApi;
