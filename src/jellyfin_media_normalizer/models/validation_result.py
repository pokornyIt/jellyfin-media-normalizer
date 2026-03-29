"""Validation result models."""

from __future__ import annotations

from dataclasses import dataclass, field

from jellyfin_media_normalizer.models.confidence_level import ConfidenceLevel
from jellyfin_media_normalizer.models.validation_status import ValidationStatus


@dataclass(slots=True)
class ValidationResult:
    """Represent the result of a validation check.

    :param is_valid: Whether the validation passed.
    :param status: The validation status (passed, review_needed, or failed).
    :param confidence: The confidence level of the validation.
    :param issues: List of issues found during validation.
    :param warnings: List of warnings found during validation.
    """

    is_valid: bool
    status: ValidationStatus
    confidence: ConfidenceLevel
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
