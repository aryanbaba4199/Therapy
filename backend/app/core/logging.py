"""Structured, secure logging configuration."""

import json
import logging
import sys
from typing import Any

from app.core.config import get_settings

SENSITIVE_KEYS = {
    "password",
    "token",
    "access_token",
    "refresh_token",
    "jwt",
    "otp",
    "secret",
    "authorization",
    "cookie",
}


def sanitize_data(data: Any) -> Any:
    """Recursively mask sensitive values in dictionaries and lists."""
    if isinstance(data, dict):
        sanitized: dict[str, Any] = {}
        for key, value in data.items():
            if str(key).lower() in SENSITIVE_KEYS:
                sanitized[key] = "********"
            else:
                sanitized[key] = sanitize_data(value)
        return sanitized
    if isinstance(data, list):
        return [sanitize_data(item) for item in data]
    return data


class JsonLogFormatter(logging.Formatter):
    """Format log records as structured JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "extra_data"):
            log_obj["data"] = sanitize_data(record.extra_data)
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging() -> None:
    """Initialize application logger with standard or JSON output."""
    settings = get_settings()
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())

    # Clear existing handlers to prevent duplicate lines
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(settings.log_level.upper())

    if settings.log_json_format:
        handler.setFormatter(JsonLogFormatter())
    else:
        standard_format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
        handler.setFormatter(logging.Formatter(standard_format))

    root_logger.addHandler(handler)


logger = logging.getLogger("app")
