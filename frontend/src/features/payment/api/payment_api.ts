import { baseApi } from "@/store/api/base_api";
import type { ApiResponse } from "@/common/types/api_types";

export interface CreatePaymentRequest {
  target_type: "booking" | "package";
  target_id: string;
  payment_method: "upi" | "card" | "netbanking" | "package_redemption";
  offer_code?: string;
  user_package_id?: string;
  idempotency_key?: string;
}

export interface VerifyPaymentRequest {
  provider_order_id: string;
  provider_payment_id: string;
  provider_signature: string;
  payment_method?: string;
}

export interface PaymentPricingSnapshot {
  base_amount_minor: number;
  discount_amount_minor: number;
  payable_amount_minor: number;
  currency: string;
  offer_code?: string;
  user_package_id?: string;
}

export interface PaymentResponse {
  id: string;
  user_id: string;
  target_type: "booking" | "package";
  target_id: string;
  amount_minor: number;
  currency: string;
  provider: string;
  provider_order_id: string;
  status: "created" | "pending" | "paid" | "failed" | "refunded";
  payment_method?: string;
  pricing: PaymentPricingSnapshot;
  created_at: string;
  updated_at: string;
}

export const paymentApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    initiatePayment: builder.mutation<
      ApiResponse<PaymentResponse>,
      CreatePaymentRequest
    >({
      query: (body) => ({
        url: "/payments",
        method: "POST",
        body,
      }),
      invalidatesTags: ["Payment", "Booking", "UserPackage"],
    }),
    verifyPayment: builder.mutation<
      ApiResponse<PaymentResponse>,
      { paymentId: string; body: VerifyPaymentRequest }
    >({
      query: ({ paymentId, body }) => ({
        url: `/payments/${paymentId}/verify`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["Payment", "Booking", "UserPackage"],
    }),
    getPayment: builder.query<ApiResponse<PaymentResponse>, string>({
      query: (id) => ({
        url: `/payments/${id}`,
        method: "GET",
      }),
      providesTags: (_res, _err, id) => [{ type: "Payment", id }],
    }),
  }),
});

export const {
  useInitiatePaymentMutation,
  useVerifyPaymentMutation,
  useGetPaymentQuery,
} = paymentApi;
