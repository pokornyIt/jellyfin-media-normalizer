"""Parsed media name models."""

from __future__ import annotations

from dataclasses import dataclass

from jellyfin_media_normalizer.models.media_type import MediaType


@dataclass(slots=True)
class ParsedName:
    """Represent parsed filename data.

    :param media_type: Detected media type.
    :param raw_name: Original filename without path.
    :param normalized_name: Cleaned name used for further parsing.
    :param title: Parsed title or episode title.
    :param year: Parsed year if available.
    :param season: Parsed season number for TV episodes.
    :param episode: Parsed episode number for TV episodes.
    :param language_code: Parsed audio language code if available.
    :param has_czech_subtitles: Whether Czech subtitles were detected.
    :param has_english_subtitles: Whether English subtitles were detected.
    :param confidence: Parser confidence score in range 0.0 to 1.0.
    """

    media_type: MediaType
    raw_name: str
    normalized_name: str
    title: str | None
    year: int | None
    season: int | None
    episode: int | None
    language_code: str | None
    has_czech_subtitles: bool
    has_english_subtitles: bool
    confidence: float
