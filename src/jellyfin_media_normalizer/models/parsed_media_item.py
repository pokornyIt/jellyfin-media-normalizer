"""Parsed media item models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from jellyfin_media_normalizer.models.confidence_level import ConfidenceLevel
from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.provider_match import ProviderMatch
from jellyfin_media_normalizer.models.validation_result import ValidationResult
from jellyfin_media_normalizer.models.validation_status import ValidationStatus


@dataclass(slots=True)
class ParsedMediaItem:
    """Represent a parsed and classified media item.

    :param source: The original MediaItem that was parsed.
    :param media_type: The classified media type (e.g. "movie", "tv_episode", "unknown").
    :param title: The extracted title from the filename.
    :param normalized_title: A cleaned and normalized version of the title for matching.
    :param year: The extracted release year for movies, if available.
    :param season: The extracted season number for TV episodes, if available.
    :param episode: The extracted episode number for TV episodes, if available.
    :param language: The extracted language code, if available.
    :param subtitle_language: The extracted subtitle language code, if available.
    :param confidence: The confidence score of the parsing result.
    :param validation_status: The validation status of the parsed item.
    :param validation_confidence: The confidence level of the validation result.
    :param validation_result: Detailed validation result information.
    :param provider_match: Provider lookup result for movie or TV series.
    :param issues: Any issues encountered during parsing.
    """

    source: MediaItem
    media_type: str
    title: str
    normalized_title: str
    year: int | None = None
    season: int | None = None
    episode: int | None = None
    language: str | None = None
    subtitle_language: str | None = None
    confidence: float = 0.0
    validation_status: ValidationStatus = ValidationStatus.PASSED
    validation_confidence: ConfidenceLevel = ConfidenceLevel.LOW
    validation_result: ValidationResult | None = None
    provider_match: ProviderMatch | None = None
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Serialize the parsed item to a JSON-friendly dictionary."""
        payload: dict[str, object] = asdict(self)
        source: object = payload.pop("source")
        payload.pop("validation_result", None)
        if isinstance(source, dict):
            source["path"] = str(source["path"])
            source["relative_path"] = str(source["relative_path"])
            payload["source"] = source
        return payload
