import { baseApi } from "@/store/api/base_api";
import type { ApiResponse } from "@/common/types/api_types";

export interface PackageProduct {
  id: string;
  title: string;
  description: string;
  session_count: number;
  validity_days: number;
  price_minor: number;
  currency: string;
  is_active: boolean;
}

export interface UserPackage {
  id: string;
  user_id: string;
  package_product_id: string;
  title: string;
  total_sessions: number;
  remaining_sessions: number;
  purchased_at: string;
  expires_at: string;
  status: "active" | "exhausted" | "expired";
}

export const packageApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listPackages: builder.query<ApiResponse<PackageProduct[]>, void>({
      query: () => ({
        url: "/packages",
        method: "GET",
      }),
      providesTags: ["Package"],
    }),
    getPackage: builder.query<ApiResponse<PackageProduct>, string>({
      query: (id) => ({
        url: `/packages/${id}`,
        method: "GET",
      }),
      providesTags: (_res, _err, id) => [{ type: "Package", id }],
    }),
    listMyPackages: builder.query<ApiResponse<UserPackage[]>, void>({
      query: () => ({
        url: "/packages/my",
        method: "GET",
      }),
      providesTags: ["UserPackage"],
    }),
    listMyUsablePackages: builder.query<ApiResponse<UserPackage[]>, void>({
      query: () => ({
        url: "/packages/my/usable",
        method: "GET",
      }),
      providesTags: ["UserPackage"],
    }),
  }),
});

export const {
  useListPackagesQuery,
  useGetPackageQuery,
  useListMyPackagesQuery,
  useListMyUsablePackagesQuery,
} = packageApi;
