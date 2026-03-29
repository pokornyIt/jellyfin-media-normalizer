"""Structure validation for parsed media items."""

from __future__ import annotations

from jellyfin_media_normalizer.models.confidence_level import ConfidenceLevel
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.validation_result import ValidationResult
from jellyfin_media_normalizer.models.validation_status import ValidationStatus


class StructureValidator:
    """Validate structural integrity of parsed items.

    Checks that required fields are present and properly formatted.
    """

    def validate(self, item: ParsedMediaItem) -> ValidationResult:
        """Validate the structure of a parsed media item.

        :param item: Parsed media item to validate.
        :return: Validation result.
        """
        issues: list[str] = []
        warnings: list[str] = []

        # Check basic required fields
        if not item.title or not item.title.strip():
            issues.append("Missing or empty title")

        if not item.normalized_title or not item.normalized_title.strip():
            issues.append("Missing or empty normalized_title")

        # Movie-specific validation
        if item.media_type == "movie":
            if item.year is None:
                warnings.append("Movie has no year information")
            elif not (1800 <= item.year <= 2100):
                issues.append(f"Invalid movie year: {item.year}")

        # TV episode-specific validation
        if item.media_type == "tv_episode":
            if item.season is None:
                issues.append("TV episode missing season number")
            elif item.season < 0:
                issues.append(f"Invalid season number: {item.season}")

            if item.episode is None:
                issues.append("TV episode missing episode number")
            elif item.episode < 0:
                issues.append(f"Invalid episode number: {item.episode}")

        # Unknown media type — item could not be classified
        if item.media_type == "unknown":
            warnings.append("Media type could not be classified")

        # Check language code if present
        if item.language is not None and (
            not isinstance(item.language, str) or len(item.language) != 2
        ):
            issues.append(f"Invalid language code: {item.language}")

        # Determine validation status
        status: ValidationStatus
        confidence: ConfidenceLevel
        is_valid: bool
        if issues:
            status = ValidationStatus.FAILED
            confidence = ConfidenceLevel.LOW
            is_valid = False
        elif warnings:
            status = ValidationStatus.REVIEW_NEEDED
            confidence = ConfidenceLevel.MEDIUM
            is_valid = True
        else:
            status = ValidationStatus.PASSED
            confidence = ConfidenceLevel.HIGH
            is_valid = True

        return ValidationResult(
            is_valid=is_valid,
            status=status,
            confidence=confidence,
            issues=issues,
            warnings=warnings,
        )
