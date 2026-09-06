import React from "react";
import { useTranslation } from "react-i18next";
import { FiCheckCircle, FiClock, FiUsers, FiActivity } from "react-icons/fi";
import { useGetHealthQuery } from "@/store/api/health_api";

export const HomePage: React.FC = () => {
  const { t } = useTranslation(["common"]);
  const { data: healthResp, isLoading } = useGetHealthQuery();

  const isHealthy = healthResp?.data?.status === "healthy";

  return (
    <div className="space-y-16 pb-16">
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
              className="px-8 py-3.5 rounded-full bg-oppam-dark text-white hover:bg-neutral-800 font-bold text-sm tracking-wider uppercase transition-all shadow-md hover:shadow-lg active:scale-98"
            >
              {t("common:consultTherapist")}
            </button>

            <button
              type="button"
              className="px-8 py-3.5 rounded-full bg-white text-oppam-dark hover:bg-gray-50 border border-gray-200 font-bold text-sm tracking-wider uppercase transition-all shadow-xs"
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
                isLoading
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
                  {isLoading
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
    </div>
  );
};
