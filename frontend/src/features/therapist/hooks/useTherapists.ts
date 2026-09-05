import { useCallback, useState } from "react";
import { useGetTherapistsQuery } from "../api/therapist_api";
import type {
  TherapistFilterParams,
  TherapistSortBy,
} from "../types/therapist.types";

export const useTherapists = (initialParams?: TherapistFilterParams) => {
  const [filters, setFilters] = useState<TherapistFilterParams>({
    page: 1,
    limit: 9,
    sort: "relevance",
    ...initialParams,
  });

  const { data, isLoading, isFetching, isError, refetch } =
    useGetTherapistsQuery(filters);

  const setPage = useCallback((page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  }, []);

  const setSearch = useCallback((search: string) => {
    setFilters((prev) => ({
      ...prev,
      search: search.trim() || undefined,
      page: 1,
    }));
  }, []);

  const setSort = useCallback((sort: TherapistSortBy) => {
    setFilters((prev) => ({ ...prev, sort, page: 1 }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({
      page: 1,
      limit: 9,
      sort: "relevance",
    });
  }, []);

  return {
    filters,
    setFilters,
    setPage,
    setSearch,
    setSort,
    clearFilters,
    therapists: data?.data?.items || [],
    pagination: data?.data?.pagination,
    isLoading,
    isFetching,
    isError,
    refetch,
  };
};
