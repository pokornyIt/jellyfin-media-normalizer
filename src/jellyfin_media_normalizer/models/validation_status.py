"""Validation status definitions."""

from __future__ import annotations

from enum import StrEnum


class ValidationStatus(StrEnum):
    """Represent validation status of parsed items."""

    PASSED = "passed"
    REVIEW_NEEDED = "review_needed"
    FAILED = "failed"
