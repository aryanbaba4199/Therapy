import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

import {
  DEFAULT_LANGUAGE,
  DEFAULT_NAMESPACE,
  LANGUAGE_STORAGE_KEY,
  NAMESPACES,
  SUPPORTED_LANGUAGES,
} from "./config";

import enAuth from "./locales/en/auth.json";
import enCommon from "./locales/en/common.json";
import enNavigation from "./locales/en/navigation.json";
import enTherapist from "./locales/en/therapist.json";
import enValidation from "./locales/en/validation.json";

import mlAuth from "./locales/ml/auth.json";
import mlCommon from "./locales/ml/common.json";
import mlNavigation from "./locales/ml/navigation.json";
import mlTherapist from "./locales/ml/therapist.json";
import mlValidation from "./locales/ml/validation.json";

import taAuth from "./locales/ta/auth.json";
import taCommon from "./locales/ta/common.json";
import taNavigation from "./locales/ta/navigation.json";
import taTherapist from "./locales/ta/therapist.json";
import taValidation from "./locales/ta/validation.json";

export const resources = {
  en: {
    common: enCommon,
    navigation: enNavigation,
    auth: enAuth,
    validation: enValidation,
    therapist: enTherapist,
  },
  ml: {
    common: mlCommon,
    navigation: mlNavigation,
    auth: mlAuth,
    validation: mlValidation,
    therapist: mlTherapist,
  },
  ta: {
    common: taCommon,
    navigation: taNavigation,
    auth: taAuth,
    validation: taValidation,
    therapist: taTherapist,
  },
} as const;

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: DEFAULT_LANGUAGE,
    supportedLngs: SUPPORTED_LANGUAGES,
    defaultNS: DEFAULT_NAMESPACE,
    ns: NAMESPACES,
    detection: {
      order: ["localStorage", "navigator"],
      lookupLocalStorage: LANGUAGE_STORAGE_KEY,
      caches: ["localStorage"],
    },
    interpolation: {
      escapeValue: false, // React already escapes values safely
    },
    react: {
      useSuspense: false,
    },
  });

export default i18n;
