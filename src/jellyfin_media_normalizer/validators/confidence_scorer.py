"""Confidence level scoring for parsed media items."""

from __future__ import annotations

from jellyfin_media_normalizer.models.confidence_level import ConfidenceLevel
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem


class ConfidenceScorer:
    """Score confidence level based on parsing result quality."""

    # Thresholds for confidence levels
    HIGH_THRESHOLD: float = 0.85
    MEDIUM_THRESHOLD: float = 0.65

    def score(self, item: ParsedMediaItem) -> ConfidenceLevel:
        """Determine confidence level based on item quality.

        :param item: Parsed media item to score.
        :return: Confidence level.
        """
        # Base confidence from parser
        parsing_confidence: float = item.confidence

        # Apply adjustments based on item properties
        if item.media_type == "movie":
            if item.year is None:
                parsing_confidence *= 0.75  # Reduce confidence without year
            if item.language is None:
                parsing_confidence *= 0.95  # Minimal reduction without language

        elif item.media_type == "tv_episode":
            if item.season is None or item.episode is None:
                parsing_confidence *= 0.5  # Major reduction without S/E info

        # Check for issues - only major penalty if many issues
        if item.issues and len(item.issues) >= 2:
            parsing_confidence *= 0.7  # Reduce for multiple issues

        # Map to confidence level
        if parsing_confidence >= self.HIGH_THRESHOLD:
            return ConfidenceLevel.HIGH
        elif parsing_confidence >= self.MEDIUM_THRESHOLD:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
