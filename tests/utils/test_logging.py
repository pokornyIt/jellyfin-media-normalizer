"""Tests for logging utilities."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import pytest

from jellyfin_media_normalizer.utils.logging import (
    HumanFormatter,
    JsonFormatter,
    LoggingMixin,
    _coerce_level,
    _iso8601_local_with_ms,
    get_logger,
    setup_logging,
)


class TestIso8601LocalWithMs:
    """Tests for :func:`_iso8601_local_with_ms`."""

    def test_returns_string(self) -> None:
        """Returns a string value.

        :return: None
        """
        import time

        result: str = _iso8601_local_with_ms(time.time())

        assert isinstance(result, str)

    def test_format_has_date_and_time(self) -> None:
        """Output includes date and time separated by T.

        :return: None
        """
        import time

        result: str = _iso8601_local_with_ms(time.time())

        assert "T" in result

    def test_format_has_milliseconds(self) -> None:
        """Output includes milliseconds after seconds.

        :return: None
        """
        import time

        result: str = _iso8601_local_with_ms(time.time())

        # Pattern: YYYY-MM-DDTHH:MM:SS.mmm±HHMM
        assert re.search(r"\.\d{3}", result) is not None

    def test_format_has_timezone_offset(self) -> None:
        """Output includes timezone offset.

        :return: None
        """
        import time

        result: str = _iso8601_local_with_ms(time.time())

        # Timezone is either +HHMM, -HHMM, or +0000
        assert re.search(r"[+-]\d{4}$", result) is not None

    def test_known_timestamp_produces_correct_date(self) -> None:
        """Known epoch timestamp produces correct date components.

        :return: None
        """
        # Use epoch 0 (1970-01-01T00:00:00 UTC) offset by local timezone
        epoch_zero = 0.0
        result: str = _iso8601_local_with_ms(epoch_zero)

        # Result should start with 1970
        assert "1970" in result

    def test_milliseconds_three_digits(self) -> None:
        """Milliseconds are always exactly three digits.

        :return: None
        """
        import time

        result: str = _iso8601_local_with_ms(time.time())

        ms_match: re.Match[str] | None = re.search(r"\.(\d{3})", result)
        assert ms_match is not None
        assert len(ms_match.group(1)) == 3


class TestCoerceLevel:
    """Tests for :func:`_coerce_level`."""

    @pytest.mark.parametrize(
        ("level_str", "expected"),
        [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
        ],
    )
    def test_converts_known_levels(self, level_str: str, expected: int) -> None:
        """Known level names are correctly converted to logging constants.

        :param level_str: Input level string.
        :param expected: Expected integer constant.
        """
        assert _coerce_level(level_str) == expected

    def test_case_insensitive(self) -> None:
        """Level name matching is case-insensitive.

        :return: None
        """
        assert _coerce_level("debug") == logging.DEBUG
        assert _coerce_level("Info") == logging.INFO
        assert _coerce_level("WARNING") == logging.WARNING

    def test_unknown_level_defaults_to_info(self) -> None:
        """Unknown level names fall back to INFO.

        :return: None
        """
        assert _coerce_level("UNKNOWN_LEVEL") == logging.INFO
        assert _coerce_level("INVALID") == logging.INFO

    def test_returns_int(self) -> None:
        """Return value is always an integer.

        :return: None
        """
        assert isinstance(_coerce_level("INFO"), int)


class TestJsonFormatter:
    """Tests for :class:`JsonFormatter`."""

    def _make_record(
        self,
        message: str = "test message",
        level: int = logging.INFO,
    ) -> logging.LogRecord:
        """Create a log record for testing.

        :param message: Log message.
        :param level: Log level.
        :return: Constructed LogRecord.
        """
        record = logging.LogRecord(
            name="test.logger",
            level=level,
            pathname="test_file.py",
            lineno=42,
            msg=message,
            args=(),
            exc_info=None,
        )
        return record

    def test_format_returns_valid_json(self) -> None:
        """format() returns a valid JSON string.

        :return: None
        """
        formatter = JsonFormatter()
        record: logging.LogRecord = self._make_record()

        result: str = formatter.format(record)

        parsed: Any = json.loads(result)
        assert isinstance(parsed, dict)

    def test_format_includes_required_fields(self) -> None:
        """format() includes all required structured fields.

        :return: None
        """
        formatter = JsonFormatter()
        record: logging.LogRecord = self._make_record()

        result: Any = json.loads(formatter.format(record))

        assert "ts" in result
        assert "level" in result
        assert "logger" in result
        assert "message" in result

    def test_format_includes_message(self) -> None:
        """format() includes the log message.

        :return: None
        """
        formatter = JsonFormatter()
        record: logging.LogRecord = self._make_record(message="hello world")

        result: Any = json.loads(formatter.format(record))

        assert result["message"] == "hello world"

    def test_format_includes_static_fields(self) -> None:
        """format() merges static fields into the output.

        :return: None
        """
        formatter = JsonFormatter(static_fields={"app": "myapp", "env": "test"})
        record: logging.LogRecord = self._make_record()

        result: Any = json.loads(formatter.format(record))

        assert result["app"] == "myapp"
        assert result["env"] == "test"

    def test_format_includes_extra_fields(self) -> None:
        """format() includes extra dict attached to the log record.

        :return: None
        """
        formatter = JsonFormatter()
        record: logging.LogRecord = self._make_record()
        record.extra = {"item_count": 5, "path": "/some/path"}  # type: ignore[attr-defined]

        result: Any = json.loads(formatter.format(record))

        assert result["extra"]["item_count"] == 5
        assert result["extra"]["path"] == "/some/path"

    def test_format_omits_none_values(self) -> None:
        """format() excludes None values from the output.

        :return: None
        """
        formatter = JsonFormatter()
        record: logging.LogRecord = self._make_record()

        result: Any = json.loads(formatter.format(record))

        assert all(v is not None for v in result.values())

    @pytest.mark.parametrize(
        ("level", "expected_name"),
        [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARNING"),
            (logging.ERROR, "ERROR"),
        ],
    )
    def test_format_level_name(self, level: int, expected_name: str) -> None:
        """format() includes the correct level name.

        :param level: Log level integer.
        :param expected_name: Expected string name.
        """
        formatter = JsonFormatter()
        record: logging.LogRecord = self._make_record(level=level)

        result: Any = json.loads(formatter.format(record))

        assert result["level"] == expected_name

    def test_init_with_no_static_fields(self) -> None:
        """Initialization without static_fields uses empty dict.

        :return: None
        """
        formatter = JsonFormatter()

        assert formatter.static_fields == {}


class TestHumanFormatter:
    """Tests for :class:`HumanFormatter`."""

    def _make_record(
        self,
        message: str = "test message",
        level: int = logging.INFO,
    ) -> logging.LogRecord:
        """Create a log record for testing.

        :param message: Log message.
        :param level: Log level.
        :return: Constructed LogRecord.
        """
        record = logging.LogRecord(
            name="test.logger",
            level=level,
            pathname="test_file.py",
            lineno=10,
            msg=message,
            args=(),
            exc_info=None,
        )
        return record

    def test_format_returns_string(self) -> None:
        """format() returns a string.

        :return: None
        """
        formatter = HumanFormatter()
        record: logging.LogRecord = self._make_record()

        result: str = formatter.format(record)

        assert isinstance(result, str)

    def test_format_includes_log_message(self) -> None:
        """format() includes the log message in output.

        :return: None
        """
        formatter = HumanFormatter()
        record: logging.LogRecord = self._make_record(message="my log message")

        result: str = formatter.format(record)

        assert "my log message" in result

    def test_format_includes_level_name(self) -> None:
        """format() includes the log level name.

        :return: None
        """
        formatter = HumanFormatter()
        record: logging.LogRecord = self._make_record(level=logging.WARNING)

        result: str = formatter.format(record)

        assert "WARNING" in result

    def test_format_includes_logger_name(self) -> None:
        """format() includes the logger name.

        :return: None
        """
        formatter = HumanFormatter()
        record: logging.LogRecord = self._make_record()

        result: str = formatter.format(record)

        assert "test.logger" in result

    def test_format_includes_extra_as_json(self) -> None:
        """format() appends extra dict as JSON suffix.

        :return: None
        """
        formatter = HumanFormatter()
        record: logging.LogRecord = self._make_record()
        record.extra = {"key": "value"}  # type: ignore[attr-defined]

        result: str = formatter.format(record)

        assert "key" in result
        assert "value" in result

    def test_format_static_fields_shows_app_name(self) -> None:
        """format() uses app name from static_fields.

        :return: None
        """
        formatter = HumanFormatter(static_fields={"app": "my-app"})
        record: logging.LogRecord = self._make_record()

        result: str = formatter.format(record)

        assert "my-app" in result

    def test_init_with_no_static_fields(self) -> None:
        """Initialization without static_fields uses empty dict.

        :return: None
        """
        formatter = HumanFormatter()

        assert formatter.static_fields == {}


class TestSetupLogging:
    """Tests for :func:`setup_logging`."""

    def test_setup_logging_sets_root_level(self) -> None:
        """setup_logging configures root logger with requested level.

        :return: None
        """
        setup_logging(level="WARNING", log_format="text", app_name="test-app")
        root_logger: logging.Logger = logging.getLogger()

        assert root_logger.level == logging.WARNING

    def test_setup_logging_adds_handler(self) -> None:
        """setup_logging adds a stream handler to the root logger.

        :return: None
        """
        setup_logging(level="INFO", log_format="text", app_name="test-app")
        root_logger: logging.Logger = logging.getLogger()

        assert len(root_logger.handlers) >= 1

    def test_setup_logging_text_format_uses_human_formatter(self) -> None:
        """setup_logging with text format attaches HumanFormatter.

        :return: None
        """
        setup_logging(level="INFO", log_format="text", app_name="test-app")
        root_logger: logging.Logger = logging.getLogger()
        handler: logging.Handler = root_logger.handlers[0]

        assert isinstance(handler.formatter, HumanFormatter)

    def test_setup_logging_json_format_uses_json_formatter(self) -> None:
        """setup_logging with json format attaches JsonFormatter.

        :return: None
        """
        setup_logging(level="INFO", log_format="json", app_name="test-app")
        root_logger: logging.Logger = logging.getLogger()
        handler: logging.Handler = root_logger.handlers[0]

        assert isinstance(handler.formatter, JsonFormatter)

    def test_setup_logging_replaces_existing_handlers(self) -> None:
        """setup_logging removes previous handlers before adding new one.

        :return: None
        """
        setup_logging(level="INFO", log_format="text", app_name="test-app")
        setup_logging(level="INFO", log_format="text", app_name="test-app")
        root_logger: logging.Logger = logging.getLogger()

        assert len(root_logger.handlers) == 1

    def test_setup_logging_suppresses_httpx(self) -> None:
        """setup_logging sets httpx logger level to WARNING.

        :return: None
        """
        setup_logging(level="DEBUG", log_format="text", app_name="test-app")

        assert logging.getLogger("httpx").level == logging.WARNING

    def test_setup_logging_suppresses_httpcore(self) -> None:
        """setup_logging sets httpcore logger level to WARNING.

        :return: None
        """
        setup_logging(level="DEBUG", log_format="text", app_name="test-app")

        assert logging.getLogger("httpcore").level == logging.WARNING


class TestGetLogger:
    """Tests for :func:`get_logger`."""

    def test_returns_logger_instance(self) -> None:
        """get_logger returns a logging.Logger instance.

        :return: None
        """
        logger: logging.Logger = get_logger("test.module")

        assert isinstance(logger, logging.Logger)

    def test_logger_has_correct_name(self) -> None:
        """get_logger returns a logger with the provided name.

        :return: None
        """
        logger: logging.Logger = get_logger("my.test.logger")

        assert logger.name == "my.test.logger"

    def test_same_name_returns_same_logger(self) -> None:
        """get_logger returns the same instance for the same name.

        :return: None
        """
        logger1: logging.Logger = get_logger("shared.logger")
        logger2: logging.Logger = get_logger("shared.logger")

        assert logger1 is logger2


class TestLoggingMixin:
    """Tests for :class:`LoggingMixin`."""

    def test_log_property_returns_logger(self) -> None:
        """log property returns a logging.Logger instance.

        :return: None
        """

        class MyClass(LoggingMixin):
            """Test class using the mixin."""

        instance = MyClass()

        assert isinstance(instance.log, logging.Logger)

    def test_log_name_includes_class_name(self) -> None:
        """log property returns a logger named after the class.

        :return: None
        """

        class SomeService(LoggingMixin):
            """Test class using the mixin."""

        instance = SomeService()

        assert "SomeService" in instance.log.name

    def test_log_name_includes_module_name(self) -> None:
        """log property logger name includes the module.

        :return: None
        """

        class AnotherClass(LoggingMixin):
            """Test class using the mixin."""

        instance = AnotherClass()

        assert "." in instance.log.name

    def test_different_classes_have_different_loggers(self) -> None:
        """Different classes using the mixin get different loggers.

        :return: None
        """

        class ClassA(LoggingMixin):
            """Test class A."""

        class ClassB(LoggingMixin):
            """Test class B."""

        assert ClassA().log.name != ClassB().log.name
