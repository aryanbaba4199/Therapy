import React, { useEffect } from "react";
import { Outlet, Link, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { FiPhone, FiMail, FiMapPin, FiHeart } from "react-icons/fi";
import { LanguageSwitcher } from "@/common/components/language_switcher";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { LANGUAGE_STORAGE_KEY, SUPPORTED_LANGUAGES } from "@/i18n/config";

export const MainLayout: React.FC = () => {
  const { t, i18n } = useTranslation(["common", "navigation", "auth"]);
  const { user, isAuthenticated, logout, hasRole } = useAuth();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const lng = searchParams.get("lng")?.toLowerCase();
    if (lng && (SUPPORTED_LANGUAGES as readonly string[]).includes(lng)) {
      if (i18n.language !== lng) {
        void i18n.changeLanguage(lng);
        localStorage.setItem(LANGUAGE_STORAGE_KEY, lng);
      }
    }
  }, [searchParams, i18n]);

  return (
    <div className="min-h-screen flex flex-col bg-white text-oppam-black font-sans">
      {/* Top Banner & Header */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-gray-100 transition-all">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          {/* Brand Identity */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-10 h-10 rounded-full bg-oppam-yellow flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
              <FiHeart className="w-5 h-5 text-oppam-dark" />
            </div>
            <div>
              <span className="text-2xl font-black tracking-tight text-oppam-dark block leading-none">
                {t("common:appName")}
              </span>
              <span className="text-[10px] uppercase font-bold tracking-widest text-gray-500 block mt-0.5">
                {t("common:onlineTherapy")}
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            <Link
              to="/"
              className="text-sm font-semibold text-gray-700 hover:text-oppam-dark transition-colors"
            >
              {t("navigation:home")}
            </Link>
            <Link
              to="/therapists"
              className="text-sm font-semibold text-gray-700 hover:text-oppam-dark transition-colors"
            >
              {t("navigation:therapists")}
            </Link>
            {(hasRole("super_admin") || hasRole("admin")) && (
              <Link
                to="/operations/therapists"
                className="text-sm font-semibold text-purple-700 hover:text-purple-900 transition-colors"
              >
                Therapists Management
              </Link>
            )}
            <span className="text-sm font-semibold text-gray-400 cursor-not-allowed">
              {t("navigation:services")}
            </span>
            <span className="text-sm font-semibold text-gray-400 cursor-not-allowed">
              {t("navigation:concerns")}
            </span>
            <span className="text-sm font-semibold text-gray-400 cursor-not-allowed">
              {t("navigation:aboutUs")}
            </span>
          </nav>

          {/* Controls: Language Switcher & Auth Action */}
          <div className="flex items-center gap-4">
            <LanguageSwitcher />

            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                {hasRole("therapist") && (
                  <Link
                    to="/therapist/dashboard"
                    className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold text-teal-900 bg-teal-100/70 hover:bg-teal-200 transition-colors"
                  >
                    <span>Therapist Portal</span>
                  </Link>
                )}
                {(hasRole("super_admin") || hasRole("admin")) && (
                  <Link
                    to="/admin/therapists/new"
                    className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold text-white bg-oppam-dark hover:bg-neutral-800 transition-colors shadow-xs"
                  >
                    <span>+ Onboard Therapist</span>
                  </Link>
                )}
                {(hasRole("staff") ||
                  hasRole("first_responder") ||
                  hasRole("admin") ||
                  hasRole("super_admin")) && (
                  <Link
                    to="/operations/dashboard"
                    className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold text-purple-900 bg-purple-100/70 hover:bg-purple-200 transition-colors"
                  >
                    <span>Operations Hub</span>
                  </Link>
                )}
                {!hasRole("therapist") && (
                  <>
                    <Link
                      to="/my-sessions"
                      className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold text-teal-800 hover:bg-teal-50 transition-colors"
                    >
                      <span>My Sessions</span>
                    </Link>
                    <Link
                      to="/bookings"
                      className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold text-teal-800 hover:bg-teal-50 transition-colors"
                    >
                      <span>My Bookings</span>
                    </Link>
                    <Link
                      to="/my-reviews"
                      className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold text-teal-800 hover:bg-teal-50 transition-colors"
                    >
                      <span>My Reviews</span>
                    </Link>
                    <Link
                      to="/support"
                      className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold text-teal-800 hover:bg-teal-50 transition-colors"
                    >
                      <span>Support</span>
                    </Link>
                  </>
                )}
                <Link
                  to="/profile"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-neutral-100 hover:bg-neutral-200 text-xs font-bold text-oppam-dark transition-colors"
                >
                  <span className="w-6 h-6 rounded-full bg-oppam-yellow flex items-center justify-center font-bold text-[10px]">
                    {user?.first_name?.[0]?.toUpperCase() || "U"}
                  </span>
                  <span>{user?.first_name || t("auth:profile")}</span>
                </Link>
                <button
                  type="button"
                  onClick={() => void logout()}
                  className="hidden sm:inline-flex items-center justify-center px-4 py-2 rounded-full border border-gray-300 text-gray-700 hover:bg-gray-50 text-xs font-bold tracking-wider transition-colors"
                >
                  {t("auth:logout")}
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className="hidden sm:inline-flex items-center justify-center px-5 py-2.5 rounded-full bg-oppam-dark text-white hover:bg-neutral-800 text-xs font-bold uppercase tracking-wider transition-colors shadow-sm"
              >
                {t("auth:login")}
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* Main Routed Content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Global Footer */}
      <footer className="bg-oppam-yellow py-12 px-4 sm:px-6 lg:px-8 border-t border-amber-300">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-xl font-bold text-oppam-dark mb-2">
              {t("common:appName")}
            </h3>
            <p className="text-sm text-neutral-800 font-medium max-w-sm">
              {t("common:tagline")}
            </p>
          </div>

          <div>
            <h4 className="text-xs uppercase font-bold tracking-widest text-oppam-dark mb-3 flex items-center gap-1.5">
              <FiMapPin className="w-4 h-4" />
              {t("common:footer.addressTitle")}
            </h4>
            <address className="not-italic text-sm text-neutral-800 leading-relaxed font-medium">
              {t("common:footer.address")}
            </address>
          </div>

          <div>
            <h4 className="text-xs uppercase font-bold tracking-widest text-oppam-dark mb-3">
              {t("common:footer.contact")}
            </h4>
            <div className="space-y-2 text-sm font-semibold text-oppam-dark">
              <a
                href={`tel:${t("common:footer.phone")}`}
                className="flex items-center gap-2 hover:opacity-80 transition-opacity"
              >
                <FiPhone className="w-4 h-4" />
                {t("common:footer.phone")}
              </a>
              <a
                href={`mailto:${t("common:footer.email")}`}
                className="flex items-center gap-2 hover:opacity-80 transition-opacity"
              >
                <FiMail className="w-4 h-4" />
                {t("common:footer.email")}
              </a>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto mt-8 pt-6 border-t border-amber-300/80 text-center text-xs font-medium text-neutral-700">
          {t("common:footer.copyright")}
        </div>
      </footer>
    </div>
  );
};
