"""Validation service for parsed media items."""

from __future__ import annotations

from jellyfin_media_normalizer.models.confidence_level import ConfidenceLevel
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.validation_result import ValidationResult
from jellyfin_media_normalizer.models.validation_status import ValidationStatus
from jellyfin_media_normalizer.utils.logging import LoggingMixin
from jellyfin_media_normalizer.validators.confidence_scorer import ConfidenceScorer
from jellyfin_media_normalizer.validators.structure_validator import StructureValidator


class ValidationService(LoggingMixin):
    """Coordinate validation of parsed media items."""

    def __init__(self) -> None:
        """Initialize the service."""
        self.structure_validator = StructureValidator()
        self.confidence_scorer = ConfidenceScorer()

    def run(self, media_items: list[ParsedMediaItem]) -> list[ParsedMediaItem]:
        """Run validation on a list of parsed media items.

        :param media_items: A list of ParsedMediaItem objects to be validated.
        :return: A list of validated ParsedMediaItem objects with validation results.
        """
        self.log.info(
            "Running validation service", extra={"extra": {"item_count": len(media_items)}}
        )

        validated_items: list[ParsedMediaItem] = []
        for item in media_items:
            # Run structure validation
            validation_result: ValidationResult = self.structure_validator.validate(item)

            # Score confidence level
            confidence_level: ConfidenceLevel = self.confidence_scorer.score(item)

            # Update item with validation results
            item.validation_result = validation_result
            item.validation_status = validation_result.status
            item.validation_confidence = confidence_level

            validated_items.append(item)

        self.log.info(
            "Validation service finished",
            extra={
                "extra": {
                    "item_count": len(validated_items),
                    "passed": sum(
                        1 for i in validated_items if i.validation_status == ValidationStatus.PASSED
                    ),
                    "review_needed": sum(
                        1
                        for i in validated_items
                        if i.validation_status == ValidationStatus.REVIEW_NEEDED
                    ),
                    "failed": sum(
                        1
                        for i in validated_items
                        if i.validation_result and not i.validation_result.is_valid
                    ),
                }
            },
        )

        return validated_items
