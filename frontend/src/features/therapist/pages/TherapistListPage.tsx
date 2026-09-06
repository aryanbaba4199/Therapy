import React from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Container,
  Grid,
  Pagination,
  Skeleton,
  Stack,
  Typography,
} from "@mui/material";
import { FaExclamationTriangle, FaPlus, FaSearch } from "react-icons/fa";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { TherapistCard } from "../components/TherapistCard";
import { TherapistFilters } from "../components/TherapistFilters";
import { TherapistSearch } from "../components/TherapistSearch";
import { TherapistSort } from "../components/TherapistSort";
import { useTherapists } from "../hooks/useTherapists";

export const TherapistListPage: React.FC = () => {
  const { t } = useTranslation(["therapist", "common"]);
  const navigate = useNavigate();
  const { hasRole } = useAuth();
  const canOnboardTherapist = hasRole("super_admin") || hasRole("admin");
  const {
    filters,
    setFilters,
    setPage,
    setSearch,
    setSort,
    clearFilters,
    therapists,
    pagination,
    isLoading,
    isError,
    refetch,
  } = useTherapists();

  return (
    <Box sx={{ bgcolor: "grey.50", minHeight: "100vh", py: 6 }}>
      <Container maxWidth="xl">
        {/* Page Hero Title */}
        <Box
          sx={{
            mb: 5,
            display: "flex",
            flexDirection: { xs: "column", md: "row" },
            alignItems: { xs: "center", md: "flex-start" },
            justifyContent: "space-between",
            gap: 2,
            textAlign: { xs: "center", md: "left" },
          }}
        >
          <Box>
            <Typography
              variant="h3"
              component="h1"
              sx={{
                fontWeight: 800,
                color: "text.primary",
                mb: 1.5,
                fontSize: { xs: "2rem", md: "2.75rem" },
              }}
            >
              {t("therapist:title")}
            </Typography>
            <Typography
              variant="body1"
              color="text.secondary"
              sx={{ maxWidth: 700, fontSize: "1.1rem" }}
            >
              {t("therapist:subtitle")}
            </Typography>
          </Box>

          {canOnboardTherapist && (
            <Button
              variant="contained"
              color="primary"
              startIcon={<FaPlus />}
              onClick={() => navigate("/admin/therapists/new")}
              sx={{
                borderRadius: 3,
                px: 3,
                py: 1.5,
                fontWeight: 700,
                textTransform: "none",
                fontSize: "0.95rem",
                boxShadow: 2,
                whiteSpace: "nowrap",
                alignSelf: { xs: "center", md: "flex-start" },
              }}
            >
              {t("therapist:addTherapist", "Add Therapist")}
            </Button>
          )}
        </Box>

        {/* Top Search & Sort Bar */}
        <Box sx={{ mb: 4 }}>
          <Grid container spacing={2} sx={{ alignItems: "center" }}>
            <Grid size={{ xs: 12, md: 8 }}>
              <TherapistSearch
                value={filters.search || ""}
                onChange={setSearch}
              />
            </Grid>
            <Grid
              size={{ xs: 12, md: 4 }}
              sx={{
                display: "flex",
                justifyContent: { xs: "flex-start", md: "flex-end" },
              }}
            >
              <Stack
                direction="row"
                spacing={1.5}
                sx={{ alignItems: "center", width: { xs: "100%", md: "auto" } }}
              >
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ fontWeight: 600, display: { xs: "none", sm: "block" } }}
                >
                  {t("therapist:sortBy")}:
                </Typography>
                <TherapistSort
                  value={filters.sort || "relevance"}
                  onChange={setSort}
                />
              </Stack>
            </Grid>
          </Grid>
        </Box>

        {/* Main Content: Sidebar Filters & Therapist Grid */}
        <Grid container spacing={4}>
          {/* Sidebar Filters */}
          <Grid size={{ xs: 12, md: 3.5, lg: 3 }}>
            <TherapistFilters
              filters={filters}
              onChange={setFilters}
              onClear={clearFilters}
            />
          </Grid>

          {/* Therapist Listings */}
          <Grid size={{ xs: 12, md: 8.5, lg: 9 }}>
            {isError ? (
              <Alert
                severity="error"
                icon={<FaExclamationTriangle />}
                action={
                  <Button
                    color="inherit"
                    size="small"
                    onClick={() => void refetch()}
                  >
                    {t("common:retry")}
                  </Button>
                }
                sx={{ borderRadius: 2 }}
              >
                {t("therapist:error")}
              </Alert>
            ) : isLoading ? (
              <Grid container spacing={3}>
                {Array.from({ length: 6 }).map((_, idx) => (
                  <Grid key={idx} size={{ xs: 12, sm: 6, lg: 4 }}>
                    <Skeleton
                      variant="rounded"
                      height={320}
                      sx={{ borderRadius: 3 }}
                    />
                  </Grid>
                ))}
              </Grid>
            ) : therapists.length === 0 ? (
              <Box
                sx={{
                  py: 10,
                  px: 3,
                  bgcolor: "background.paper",
                  borderRadius: 3,
                  border: "1px solid",
                  borderColor: "divider",
                  textAlign: "center",
                }}
              >
                <Box
                  sx={{
                    width: 64,
                    height: 64,
                    borderRadius: "50%",
                    bgcolor: "grey.100",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    mx: "auto",
                    mb: 2,
                  }}
                >
                  <FaSearch className="text-gray-400 text-2xl" />
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                  {t("therapist:noResults")}
                </Typography>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 3 }}
                >
                  {t("therapist:tryAdjustingFilters")}
                </Typography>
                <Button
                  variant="outlined"
                  color="primary"
                  onClick={clearFilters}
                >
                  {t("therapist:clearFilters")}
                </Button>
              </Box>
            ) : (
              <>
                <Grid container spacing={3}>
                  {therapists.map((therapist) => (
                    <Grid key={therapist.id} size={{ xs: 12, sm: 6, lg: 4 }}>
                      <TherapistCard therapist={therapist} />
                    </Grid>
                  ))}
                </Grid>

                {/* Pagination Controls */}
                {pagination && pagination.total_pages > 1 && (
                  <Box
                    sx={{ display: "flex", justifyContent: "center", mt: 6 }}
                  >
                    <Pagination
                      count={pagination.total_pages}
                      page={pagination.page}
                      onChange={(_, page) => setPage(page)}
                      color="primary"
                      size="large"
                      showFirstButton
                      showLastButton
                    />
                  </Box>
                )}
              </>
            )}
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};
