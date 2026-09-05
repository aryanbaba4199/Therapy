import { baseApi } from "@/store/api/base_api";
import type { ApiResponse } from "@/common/types/api_types";

export interface OfferResponse {
  id: string;
  code: string;
  title: string;
  description: string;
  discount_type: "percentage" | "fixed";
  discount_value: number;
  min_order_minor: number;
  max_discount_minor: number | null;
  valid_from: string;
  valid_until: string;
  status: string;
}

export interface ValidateOfferRequest {
  code: string;
  base_amount_minor: number;
}

export interface PricingBreakdownResponse {
  base_amount_minor: number;
  discount_amount_minor: number;
  payable_amount_minor: number;
  currency: string;
  offer_applied: OfferResponse | null;
  package_applied: boolean;
  message: string | null;
}

export const offerApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listOffers: builder.query<ApiResponse<OfferResponse[]>, void>({
      query: () => ({
        url: "/offers",
        method: "GET",
      }),
      providesTags: ["Offer"],
    }),
    validateOffer: builder.mutation<
      ApiResponse<PricingBreakdownResponse>,
      ValidateOfferRequest
    >({
      query: (body) => ({
        url: "/offers/validate",
        method: "POST",
        body,
      }),
    }),
  }),
});

export const { useListOffersQuery, useValidateOfferMutation } = offerApi;
