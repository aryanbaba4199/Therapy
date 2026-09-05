import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { FiGlobe, FiCheck } from "react-icons/fi";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";

import {
  LANGUAGE_STORAGE_KEY,
  SUPPORTED_LANGUAGES,
  type SupportedLanguage,
} from "@/i18n/config";

export const LanguageSwitcher: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLanguageSelect = (lang: SupportedLanguage) => {
    void i18n.changeLanguage(lang);
    localStorage.setItem(LANGUAGE_STORAGE_KEY, lang);
    handleClose();
  };

  const currentLang = (i18n.language?.slice(0, 2) as SupportedLanguage) || "en";

  return (
    <div className="relative inline-block">
      <button
        type="button"
        onClick={handleClick}
        aria-label={t("common.selectLanguage")}
        aria-controls={open ? "language-menu" : undefined}
        aria-haspopup="true"
        aria-expanded={open ? "true" : undefined}
        className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-gray-200 bg-white hover:bg-gray-50 text-sm font-medium text-oppam-dark transition-colors shadow-xs focus:outline-none focus:ring-2 focus:ring-oppam-yellow"
      >
        <FiGlobe className="w-4 h-4 text-oppam-dark opacity-80" />
        <span className="font-semibold">
          {t(`common.languages.${currentLang}`)}
        </span>
      </button>

      <Menu
        id="language-menu"
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        slotProps={{
          paper: {
            className:
              "rounded-xl shadow-lg border border-gray-100 min-w-[160px]",
          },
        }}
      >
        {SUPPORTED_LANGUAGES.map((lang) => {
          const isSelected = currentLang === lang;
          return (
            <MenuItem
              key={lang}
              onClick={() => handleLanguageSelect(lang)}
              selected={isSelected}
              className={`text-sm py-2 px-3 ${
                isSelected ? "font-bold bg-amber-50" : ""
              }`}
            >
              <ListItemIcon className="min-w-[28px]">
                {isSelected ? (
                  <FiCheck className="w-4 h-4 text-oppam-dark" />
                ) : (
                  <span className="w-4" />
                )}
              </ListItemIcon>
              <ListItemText
                primary={t(`common.languages.${lang}`)}
                className={isSelected ? "font-semibold" : "font-normal"}
              />
            </MenuItem>
          );
        })}
      </Menu>
    </div>
  );
};
