"""Movie filename parser."""

from __future__ import annotations

import re

from jellyfin_media_normalizer.constants import LANGUAGE_CODES
from jellyfin_media_normalizer.models.media_type import MediaType
from jellyfin_media_normalizer.models.parsed_name import ParsedName
from jellyfin_media_normalizer.parsers.patterns import (
    CZ_SUB_PATTERN,
    EN_SUB_PATTERN,
    LANGUAGE_PATTERN,
    YEAR_PATTERN,
)


class MovieNameParser:
    """Parse normalized movie filenames."""

    _YEAR_PATTERN: re.Pattern[str] = YEAR_PATTERN
    _LANGUAGE_PATTERN: re.Pattern[str] = LANGUAGE_PATTERN
    _CZ_SUB_PATTERN: re.Pattern[str] = CZ_SUB_PATTERN
    _EN_SUB_PATTERN: re.Pattern[str] = EN_SUB_PATTERN

    def parse(self, raw_name: str, normalized_name: str) -> ParsedName:
        """Parse a movie filename.

        :param raw_name: Original filename including extension.
        :param normalized_name: Cleaned filename without extension.
        :return: Parsed filename data.
        """
        year_match: re.Match[str] | None = self._YEAR_PATTERN.search(normalized_name)
        year: int | None = int(year_match.group(1)) if year_match else None

        language_code: str | None = self._detect_language(normalized_name)
        has_czech_subtitles: bool = self._CZ_SUB_PATTERN.search(normalized_name) is not None
        has_english_subtitles: bool = self._EN_SUB_PATTERN.search(normalized_name) is not None

        title: str = normalized_name
        if year_match is not None:
            # Find start of the year (handle parentheses like (2016))
            year_start: int = year_match.start()
            # Backtrack to find opening parenthesis if present
            paren_start: int = normalized_name.rfind("(", 0, year_start)
            if paren_start != -1:
                title = normalized_name[:paren_start].strip(" -")
            else:
                title = normalized_name[:year_start].strip(" -")

        # Remove remaining language codes and subtitles
        title = re.sub(r"\s*-\s*[A-Z]{2}(?:\s+\(tit\. CZ\))?\s*$", "", title).strip()
        title = re.sub(r"\s+\(tit\. CZ\)\s*$", "", title).strip()

        confidence: float = 0.9 if year is not None and title else 0.55

        return ParsedName(
            media_type=MediaType.MOVIE,
            raw_name=raw_name,
            normalized_name=normalized_name,
            title=title or None,
            year=year,
            season=None,
            episode=None,
            language_code=language_code,
            has_czech_subtitles=has_czech_subtitles,
            has_english_subtitles=has_english_subtitles,
            confidence=confidence,
        )

    def _detect_language(self, normalized_name: str) -> str | None:
        """Detect a two-letter language code in the normalized name.

        :param normalized_name: Cleaned filename without extension.
        :return: Parsed language code or ``None``.
        """
        match: re.Match[str] | None = self._LANGUAGE_PATTERN.search(normalized_name)
        if match is None:
            return None
        lang: str = match.group("lang").upper()
        if lang not in LANGUAGE_CODES:
            return None
        return lang
