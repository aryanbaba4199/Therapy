"""Common platform enumerations."""

from enum import StrEnum


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class SupportedLanguage(StrEnum):
    ENGLISH = "en"
    MALAYALAM = "ml"
    TAMIL = "ta"
