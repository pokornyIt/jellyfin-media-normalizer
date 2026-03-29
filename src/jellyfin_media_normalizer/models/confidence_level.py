"""Confidence level definitions."""

from __future__ import annotations

from enum import StrEnum


class ConfidenceLevel(StrEnum):
    """Represent confidence levels for parsed and validated data."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
