"""TV episode filename parser."""

from __future__ import annotations

import re

from jellyfin_media_normalizer.models.media_type import MediaType
from jellyfin_media_normalizer.models.parsed_name import ParsedName


class TvEpisodeParser:
    """Parse normalized TV episode filenames."""

    _TV_PATTERN: re.Pattern[str] = re.compile(
        r"\bS(?P<season>\d{2})E(?P<episode>\d{2})\b", re.IGNORECASE
    )
    _YEAR_PATTERN: re.Pattern[str] = re.compile(r"\b(19\d{2}|20\d{2}|21\d{2})\b")
    _LANGUAGE_PATTERN: re.Pattern[str] = re.compile(r"(?:^| - )(?P<lang>[A-Z]{2})(?:$| )")
    _CZ_SUB_PATTERN: re.Pattern[str] = re.compile(r"\(tit\. CZ\)", re.IGNORECASE)

    def parse(self, raw_name: str, normalized_name: str) -> ParsedName:
        """Parse a TV episode filename.

        :param raw_name: Original filename including extension.
        :param normalized_name: Cleaned filename without extension.
        :return: Parsed filename data.
        """
        tv_match: re.Match[str] | None = self._TV_PATTERN.search(normalized_name)
        if tv_match is None:
            return ParsedName(
                media_type=MediaType.UNKNOWN,
                raw_name=raw_name,
                normalized_name=normalized_name,
                title=None,
                year=None,
                season=None,
                episode=None,
                language_code=None,
                has_czech_subtitles=False,
                confidence=0.0,
            )

        season: int = int(tv_match.group("season"))
        episode: int = int(tv_match.group("episode"))

        year_match: re.Match[str] | None = self._YEAR_PATTERN.search(normalized_name)
        year: int | None = int(year_match.group(1)) if year_match else None

        language_code: str | None = self._detect_language(normalized_name)
        has_czech_subtitles: bool = self._CZ_SUB_PATTERN.search(normalized_name) is not None

        title_part: str = normalized_name[: tv_match.start()].strip(" -")
        title_part = re.sub(r"\s+\(tit\. CZ\)\s*$", "", title_part).strip()
        title_part = re.sub(r"\s*-\s*[A-Z]{2}(?:\s+\(tit\. CZ\))?\s*$", "", title_part).strip()

        confidence: float = 0.95 if title_part else 0.65

        return ParsedName(
            media_type=MediaType.TV_EPISODE,
            raw_name=raw_name,
            normalized_name=normalized_name,
            title=title_part or None,
            year=year,
            season=season,
            episode=episode,
            language_code=language_code,
            has_czech_subtitles=has_czech_subtitles,
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
        return match.group("lang")
