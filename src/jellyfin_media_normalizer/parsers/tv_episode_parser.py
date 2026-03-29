"""TV episode filename parser."""

from __future__ import annotations

import re

from jellyfin_media_normalizer.constants import LANGUAGE_CODES
from jellyfin_media_normalizer.models.media_type import MediaType
from jellyfin_media_normalizer.models.parsed_name import ParsedName


class TvEpisodeParser:
    """Parse normalized TV episode filenames."""

    _TV_PATTERN: re.Pattern[str] = re.compile(
        r"\bS(?P<season>\d{2})E(?P<episode>\d{1,2})\b", re.IGNORECASE
    )
    _TV_PATTERN_SEPARATED: re.Pattern[str] = re.compile(
        r"\bS(?P<season>\d{2})[ -]?E(?P<episode>\d{1,2})\b", re.IGNORECASE
    )
    _TV_PATTERN_SEPARATOR: re.Pattern[str] = re.compile(
        r"(?:^|[\s-])(?P<season>\d{1,2})[-_x](?P<episode>\d{1,2})(?=\s|-|$)", re.IGNORECASE
    )
    _YEAR_PATTERN: re.Pattern[str] = re.compile(r"\b(19\d{2}|20\d{2}|21\d{2})\b")
    _LANGUAGE_PATTERN: re.Pattern[str] = re.compile(r"(?:^| - )(?P<lang>[A-Z]{2})(?:$| )")
    _CZ_SUB_PATTERN: re.Pattern[str] = re.compile(r"\(tit(?:le)?\.?\s*CZ\)", re.IGNORECASE)
    _EN_SUB_PATTERN: re.Pattern[str] = re.compile(r"\(tit(?:le)?\.?\s*EN\)", re.IGNORECASE)

    def parse(self, raw_name: str, normalized_name: str) -> ParsedName:
        """Parse a TV episode filename.

        :param raw_name: Original filename including extension.
        :param normalized_name: Cleaned filename without extension.
        :return: Parsed filename data.
        """
        tv_match: re.Match[str] | None = self._TV_PATTERN.search(normalized_name)
        if tv_match is not None:
            return self._parse_sxxexx(raw_name, normalized_name, tv_match)

        tv_match = self._TV_PATTERN_SEPARATED.search(normalized_name)
        if tv_match is not None:
            return self._parse_sxxexx(raw_name, normalized_name, tv_match)

        hyphen_match: re.Match[str] | None = self._TV_PATTERN_SEPARATOR.search(normalized_name)
        if hyphen_match is not None:
            return self._parse_separator_format(raw_name, normalized_name, hyphen_match)

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
            has_english_subtitles=False,
            confidence=0.0,
        )

    def _parse_sxxexx(
        self,
        raw_name: str,
        normalized_name: str,
        tv_match: re.Match[str],
    ) -> ParsedName:
        """Parse a filename using the standard SxxExx marker.

        :param raw_name: Original filename including extension.
        :param normalized_name: Cleaned filename without extension.
        :param tv_match: Regex match for the SxxExx pattern.
        :return: Parsed filename data.
        """
        season: int = int(tv_match.group("season"))
        episode: int = int(tv_match.group("episode"))

        year_match: re.Match[str] | None = self._YEAR_PATTERN.search(normalized_name)
        year: int | None = int(year_match.group(1)) if year_match else None

        language_code: str | None = self._detect_language(normalized_name)
        has_czech_subtitles: bool = self._CZ_SUB_PATTERN.search(normalized_name) is not None
        has_english_subtitles: bool = self._EN_SUB_PATTERN.search(normalized_name) is not None
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
            has_english_subtitles=has_english_subtitles,
            confidence=confidence,
        )

    def _parse_separator_format(
        self,
        raw_name: str,
        normalized_name: str,
        hyphen_match: re.Match[str],
    ) -> ParsedName:
        """Parse a filename using the hyphen-separated NNxNN marker.

        Handles filenames of the form ``Title-words-NNxNN-Episode-title``
        where hyphens act as word separators. The series title is extracted
        from the part before the season/episode marker.

        :param raw_name: Original filename including extension.
        :param normalized_name: Cleaned filename without extension.
        :param hyphen_match: Regex match for the NNxNN pattern.
        :return: Parsed filename data.
        """
        season: int = int(hyphen_match.group("season"))
        episode: int = int(hyphen_match.group("episode"))

        title_raw: str = normalized_name[: hyphen_match.start()].strip(" -")
        title: str | None = title_raw.replace("-", " ").strip() or None

        confidence: float = 0.90 if title else 0.65

        return ParsedName(
            media_type=MediaType.TV_EPISODE,
            raw_name=raw_name,
            normalized_name=normalized_name,
            title=title,
            year=None,
            season=season,
            episode=episode,
            language_code=None,
            has_czech_subtitles=False,
            has_english_subtitles=False,
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
