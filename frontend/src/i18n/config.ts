export const SUPPORTED_LANGUAGES = ["en", "ml", "ta"] as const;
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];

export const LANGUAGE_NAMES: Record<SupportedLanguage, string> = {
  en: "English",
  ml: "മലയാളം",
  ta: "தமிழ்",
};

export const NAMESPACES = [
  "common",
  "navigation",
  "auth",
  "validation",
  "therapist",
  "availability",
  "booking",
] as const;

export type Namespace = (typeof NAMESPACES)[number];

export const DEFAULT_LANGUAGE: SupportedLanguage = "en";
export const DEFAULT_NAMESPACE: Namespace = "common";
export const LANGUAGE_STORAGE_KEY = "oppam_language";
