import React from "react";
import { Outlet, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { FiPhone, FiMail, FiMapPin, FiHeart } from "react-icons/fi";
import { LanguageSwitcher } from "@/common/components/language_switcher";

export const MainLayout: React.FC = () => {
  const { t } = useTranslation();

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
                {t("common.appName")}
              </span>
              <span className="text-[10px] uppercase font-bold tracking-widest text-gray-500 block mt-0.5">
                {t("common.onlineTherapy")}
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            <Link
              to="/"
              className="text-sm font-semibold text-gray-700 hover:text-oppam-dark transition-colors"
            >
              {t("navigation.home")}
            </Link>
            <span className="text-sm font-semibold text-gray-400 cursor-not-allowed">
              {t("navigation.services")}
            </span>
            <span className="text-sm font-semibold text-gray-400 cursor-not-allowed">
              {t("navigation.concerns")}
            </span>
            <span className="text-sm font-semibold text-gray-400 cursor-not-allowed">
              {t("navigation.aboutUs")}
            </span>
          </nav>

          {/* Controls: Language Switcher & Auth Action */}
          <div className="flex items-center gap-4">
            <LanguageSwitcher />

            <button
              type="button"
              className="hidden sm:inline-flex items-center justify-center px-5 py-2.5 rounded-full bg-oppam-dark text-white hover:bg-neutral-800 text-xs font-bold uppercase tracking-wider transition-colors shadow-sm"
            >
              {t("auth.login")}
            </button>
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
              {t("common.appName")}
            </h3>
            <p className="text-sm text-neutral-800 font-medium max-w-sm">
              {t("common.tagline")}
            </p>
          </div>

          <div>
            <h4 className="text-xs uppercase font-bold tracking-widest text-oppam-dark mb-3 flex items-center gap-1.5">
              <FiMapPin className="w-4 h-4" />
              {t("common.footer.addressTitle")}
            </h4>
            <address className="not-italic text-sm text-neutral-800 leading-relaxed font-medium">
              {t("common.footer.address")}
            </address>
          </div>

          <div>
            <h4 className="text-xs uppercase font-bold tracking-widest text-oppam-dark mb-3">
              {t("common.footer.contact")}
            </h4>
            <div className="space-y-2 text-sm font-semibold text-oppam-dark">
              <a
                href={`tel:${t("common.footer.phone")}`}
                className="flex items-center gap-2 hover:opacity-80 transition-opacity"
              >
                <FiPhone className="w-4 h-4" />
                {t("common.footer.phone")}
              </a>
              <a
                href={`mailto:${t("common.footer.email")}`}
                className="flex items-center gap-2 hover:opacity-80 transition-opacity"
              >
                <FiMail className="w-4 h-4" />
                {t("common.footer.email")}
              </a>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto mt-8 pt-6 border-t border-amber-300/80 text-center text-xs font-medium text-neutral-700">
          {t("common.footer.copyright")}
        </div>
      </footer>
    </div>
  );
};
