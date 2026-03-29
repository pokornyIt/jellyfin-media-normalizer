"""Shared compiled regex patterns used across parser modules."""

from __future__ import annotations

import re

YEAR_PATTERN: re.Pattern[str] = re.compile(r"\b(19\d{2}|20\d{2}|21\d{2})\b")
"""Match a four-digit year in the range 1900-2199."""

LANGUAGE_PATTERN: re.Pattern[str] = re.compile(r"(?:^| - )(?P<lang>[A-Z]{2})(?:$| )")
"""Match a two-letter language code optionally preceded by `` - ``."""

CZ_SUB_PATTERN: re.Pattern[str] = re.compile(r"\(tit(?:le)?\.?\s*CZ\)", re.IGNORECASE)
"""Match a Czech subtitle annotation such as ``(tit. CZ)``."""

EN_SUB_PATTERN: re.Pattern[str] = re.compile(r"\(tit(?:le)?\.?\s*EN\)", re.IGNORECASE)
"""Match an English subtitle annotation such as ``(tit. EN)``."""
