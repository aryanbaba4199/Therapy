import React from "react";
import { useTranslation } from "react-i18next";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Container,
  Grid,
  Skeleton,
  Typography,
} from "@mui/material";
import {
  FiActivity,
  FiArrowRight,
  FiCheckCircle,
  FiClock,
  FiRefreshCw,
  FiUsers,
} from "react-icons/fi";
import { TherapistCard } from "@/features/therapist/components/TherapistCard";
import { useTherapists } from "@/features/therapist/hooks/useTherapists";
import { useGetHealthQuery } from "@/store/api/health_api";

export const HomePage: React.FC = () => {
  const { t } = useTranslation(["common", "therapist"]);
  const navigate = useNavigate();
  const { data: healthResp, isLoading: isHealthLoading } = useGetHealthQuery();
  const {
    therapists,
    isLoading: isTherapistsLoading,
    isError: isTherapistsError,
    refetch: refetchTherapists,
  } = useTherapists({ limit: 6, sort: "relevance" });

  const isHealthy = healthResp?.data?.status === "healthy";

  return (
    <div className="space-y-16 pb-20">
      {/* Hero Section */}
      <section className="bg-[#FECF2D] py-20 px-4 sm:px-6 lg:px-8 border-b border-amber-300">
        <div className="max-w-5xl mx-auto text-center space-y-6">
          <span className="inline-block text-sm uppercase font-extrabold tracking-widest text-neutral-800 bg-white/70 backdrop-blur-sm px-4 py-1.5 rounded-full shadow-xs">
            {t("common:onlineTherapy")}
          </span>

          <h1 className="text-4xl sm:text-6xl font-black text-oppam-dark tracking-tight leading-tight">
            {t("common:therapyHours")}
          </h1>

          <p className="text-lg sm:text-xl font-medium text-neutral-800 max-w-2xl mx-auto">
            {t("common:tagline")}
          </p>

          <div className="pt-4 flex flex-wrap items-center justify-center gap-4">
            <button
              type="button"
              onClick={() => navigate("/therapists")}
              className="cursor-pointer px-8 py-3.5 rounded-full bg-oppam-dark text-white hover:bg-neutral-800 font-bold text-sm tracking-wider uppercase transition-all shadow-md hover:shadow-lg active:scale-98"
            >
              {t("common:consultTherapist")}
            </button>

            <button
              type="button"
              onClick={() => {
                const element = document.getElementById("featured-therapists");
                if (element) {
                  element.scrollIntoView({ behavior: "smooth" });
                } else {
                  navigate("/therapists");
                }
              }}
              className="cursor-pointer px-8 py-3.5 rounded-full bg-white text-oppam-dark hover:bg-gray-50 border border-gray-200 font-bold text-sm tracking-wider uppercase transition-all shadow-xs"
            >
              {t("common:bookNow")}
            </button>
          </div>
        </div>
      </section>

      {/* Proof Points & System Health Architecture Verification */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Key Stat Card 1 */}
          <div className="p-6 rounded-2xl bg-[#FAFBFD] border border-gray-100 shadow-xs flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center text-oppam-dark shrink-0">
              <FiClock className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-oppam-dark">
                {t("common:therapyHours")}
              </h3>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mt-0.5">
                {t("common:onlineTherapy")}
              </p>
            </div>
          </div>

          {/* Key Stat Card 2 */}
          <div className="p-6 rounded-2xl bg-[#FAFBFD] border border-gray-100 shadow-xs flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center text-emerald-800 shrink-0">
              <FiUsers className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-oppam-dark">
                {t("common:verifiedTherapists")}
              </h3>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mt-0.5">
                {t("common:tagline")}
              </p>
            </div>
          </div>

          {/* Live Architecture Status Card (RTK Query + FastAPI verification) */}
          <div className="p-6 rounded-2xl bg-[#FAFBFD] border border-gray-100 shadow-xs flex items-start gap-4">
            <div
              className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${
                isHealthLoading
                  ? "bg-gray-100 text-gray-400"
                  : isHealthy
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-amber-100 text-amber-700"
              }`}
            >
              {isHealthy ? (
                <FiCheckCircle className="w-6 h-6" />
              ) : (
                <FiActivity className="w-6 h-6" />
              )}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-lg font-bold text-oppam-dark">
                  {t("common:systemStatus")}
                </h3>
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                    isHealthy
                      ? "bg-emerald-100 text-emerald-800"
                      : "bg-amber-100 text-amber-800"
                  }`}
                >
                  {isHealthLoading
                    ? t("common:loading")
                    : isHealthy
                      ? t("common:healthy")
                      : t("common:degraded")}
                </span>
              </div>
              <p className="text-xs font-semibold text-gray-500 mt-1 truncate">
                {healthResp?.data?.version
                  ? `v${healthResp.data.version} (${healthResp.data.environment})`
                  : t("common:tagline")}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Therapists List & Booking Section */}
      <section
        id="featured-therapists"
        className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 scroll-mt-10"
      >
        <Box
          sx={{
            mb: 4,
            display: "flex",
            flexWrap: "wrap",
            alignItems: "flex-end",
            justifyContent: "space-between",
            gap: 2,
          }}
        >
          <Box>
            <Typography
              variant="h4"
              component="h2"
              sx={{
                fontWeight: 800,
                color: "text.primary",
                fontSize: { xs: "1.75rem", md: "2.25rem" },
                letterSpacing: "-0.02em",
                mb: 0.5,
              }}
            >
              {t(
                "therapist:featuredTitle",
                "Book a Session with Verified Therapists"
              )}
            </Typography>
            <Typography
              variant="body1"
              color="text.secondary"
              sx={{ fontSize: "1rem" }}
            >
              {t(
                "therapist:featuredSubtitle",
                "Browse licensed counsellors and book your session directly."
              )}
            </Typography>
          </Box>

          <Button
            component={RouterLink}
            to="/therapists"
            variant="outlined"
            color="primary"
            endIcon={<FiArrowRight />}
            sx={{
              borderRadius: 3,
              fontWeight: 700,
              textTransform: "none",
              px: 2.5,
              py: 1,
              fontSize: "0.9rem",
            }}
          >
            {t("therapist:viewAll", "View All Therapists")}
          </Button>
        </Box>

        {/* Loading Skeletons */}
        {isTherapistsLoading && (
          <Grid container spacing={3}>
            {Array.from({ length: 3 }).map((_, index) => (
              <Grid key={`skeleton-${index}`} size={{ xs: 12, sm: 6, md: 4 }}>
                <Skeleton
                  variant="rounded"
                  height={360}
                  sx={{ borderRadius: 3 }}
                />
              </Grid>
            ))}
          </Grid>
        )}

        {/* Error State */}
        {isTherapistsError && !isTherapistsLoading && (
          <Alert
            severity="error"
            action={
              <Button
                color="inherit"
                size="small"
                startIcon={<FiRefreshCw />}
                onClick={() => void refetchTherapists()}
              >
                {t("common:retry", "Retry")}
              </Button>
            }
            sx={{ borderRadius: 3 }}
          >
            {t(
              "therapist:error",
              "Failed to load therapists. Please try again."
            )}
          </Alert>
        )}

        {/* Success Grid */}
        {!isTherapistsLoading &&
          !isTherapistsError &&
          therapists.length > 0 && (
            <>
              <Grid container spacing={3}>
                {therapists.map((therapist) => (
                  <Grid key={therapist.id} size={{ xs: 12, sm: 6, md: 4 }}>
                    <TherapistCard therapist={therapist} />
                  </Grid>
                ))}
              </Grid>

              {/* Bottom View All Button */}
              <Box sx={{ mt: 5, textAlign: "center" }}>
                <Button
                  component={RouterLink}
                  to="/therapists"
                  variant="contained"
                  color="primary"
                  size="large"
                  endIcon={<FiArrowRight />}
                  sx={{
                    borderRadius: 3,
                    px: 4,
                    py: 1.5,
                    fontWeight: 700,
                    textTransform: "none",
                    fontSize: "1rem",
                    boxShadow: 2,
                  }}
                >
                  {t("therapist:viewAll", "View All Therapists")}
                </Button>
              </Box>
            </>
          )}

        {/* Empty State */}
        {!isTherapistsLoading &&
          !isTherapistsError &&
          therapists.length === 0 && (
            <Container maxWidth="sm" sx={{ py: 6, textAlign: "center" }}>
              <Typography
                variant="h6"
                color="text.primary"
                sx={{ fontWeight: 700, mb: 1 }}
              >
                {t("therapist:noResults", "No therapists currently available.")}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t(
                  "therapist:tryAdjustingFilters",
                  "Please check back shortly or explore our full catalogue."
                )}
              </Typography>
            </Container>
          )}
      </section>
    </div>
  );
};
