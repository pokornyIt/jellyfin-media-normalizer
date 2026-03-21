"""Logging utilities for jellyfin-media-normalizer.

This module provides:
- ISO8601 timestamp formatting with milliseconds and local timezone offset
- human-readable or JSON log formatting
- a single setup entrypoint
- a logger helper and mixin for consistent class-level logging
"""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any

from jellyfin_media_normalizer.constants import APP_NAME


def _iso8601_local_with_ms(ts: float) -> str:
    """Format a timestamp as ISO8601 with milliseconds and timezone.

    :param ts: Timestamp in seconds since epoch.
    :return: Formatted timestamp string.
    """
    local_time: time.struct_time = time.localtime(ts)
    base: str = time.strftime("%Y-%m-%dT%H:%M:%S", local_time)
    milliseconds: str = f"{int((ts % 1) * 1000):03d}"
    timezone: str = time.strftime("%z", local_time)
    return f"{base}.{milliseconds}{timezone}"


class JsonFormatter(logging.Formatter):
    """Format log records as JSON."""

    def __init__(self, static_fields: dict[str, Any] | None = None) -> None:
        """Initialize the formatter.

        :param static_fields: Static fields included in every record.
        """
        super().__init__()
        self.static_fields: dict[str, Any] = static_fields or {}

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON.

        :param record: Log record to format.
        :return: JSON log line.
        """
        payload: dict[str, Any] = {
            "ts": _iso8601_local_with_ms(record.created),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "func": record.funcName,
            "line": record.lineno,
            "thread": record.threadName,
            "pid": record.process,
            "module": record.module,
        }

        if self.static_fields:
            payload.update(self.static_fields)

        extra: Any | None = getattr(record, "extra", None)
        if isinstance(extra, dict) and extra:
            payload["extra"] = extra

        if record.exc_info and record.exc_info[0] is not None:
            payload["exc_type"] = record.exc_info[0].__name__  # type: ignore[union-attr]
            payload["exc"] = self.formatException(record.exc_info)

        cleaned_payload: dict[str, Any] = {
            key: value for key, value in payload.items() if value is not None
        }
        return json.dumps(cleaned_payload, ensure_ascii=False)


class HumanFormatter(logging.Formatter):
    """Format log records as readable text."""

    def __init__(self, static_fields: dict[str, Any] | None = None) -> None:
        """Initialize the formatter.

        :param static_fields: Static fields included in every record.
        """
        super().__init__()
        self.static_fields: dict[str, Any] = static_fields or {}

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as readable text.

        :param record: Log record to format.
        :return: Formatted log line.
        """
        timestamp: str = _iso8601_local_with_ms(record.created)
        app_name: str = str(self.static_fields.get("app", APP_NAME))
        base: str = (
            f"{timestamp} {record.levelname} "
            f"[{app_name}] [{record.threadName}] "
            f"{record.name}:{record.funcName}:{record.lineno} : {record.getMessage()}"
        )

        extra: Any | None = getattr(record, "extra", None)
        if isinstance(extra, dict) and extra:
            try:
                base += " | " + json.dumps(extra, ensure_ascii=False, separators=(",", ":"))
            except Exception:
                base += f" | {extra!r}"

        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)

        return base


def _coerce_level(level: str) -> int:
    """Convert a log level string into a logging constant.

    :param level: Requested log level name.
    :return: Logging module level constant.
    """
    return getattr(logging, level.upper(), logging.INFO)


def setup_logging(*, level: str, log_format: str, app_name: str) -> None:
    """Configure root logging.

    :param level: Requested logging level.
    :param log_format: Requested log format, either ``text`` or ``json``.
    :param app_name: Application name shown in logs.
    """
    root_logger: logging.Logger = logging.getLogger()
    root_logger.setLevel(_coerce_level(level))

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    stream_handler: logging.StreamHandler[Any] = logging.StreamHandler(stream=sys.stdout)
    static_fields: dict[str, Any] = {"app": app_name}

    if log_format == "json":
        stream_handler.setFormatter(JsonFormatter(static_fields=static_fields))
    else:
        stream_handler.setFormatter(HumanFormatter(static_fields=static_fields))

    root_logger.addHandler(stream_handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a project logger.

    :param name: Logger name.
    :return: Logger instance.
    """
    return logging.getLogger(name)


class LoggingMixin:
    """Provide a per-class logger property."""

    @property
    def log(self) -> logging.Logger:
        """Return a class-specific logger.

        :return: Logger instance.
        """
        return get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
