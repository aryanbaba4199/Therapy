export interface ApiErrorDetails {
  code: string;
  details: unknown;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data: T | null;
  meta: Record<string, unknown> | null;
  error: ApiErrorDetails | null;
  request_id: string | null;
}

export interface HealthData {
  status: "healthy" | "degraded";
  environment: string;
  version: string;
  database: {
    connected: boolean;
    status: string;
  };
}
