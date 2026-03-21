"""Filename parsing and classification logic."""

from __future__ import annotations

import re

from jellyfin_media_normalizer.constants import KNOWN_NOISE_TOKENS, LANGUAGE_CODES
from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.utils.logging import LoggingMixin

YEAR_RE: re.Pattern[str] = re.compile(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)")
EPISODE_RE: re.Pattern[str] = re.compile(r"(?i)\bS(?P<season>\d{1,2})E(?P<episode>\d{1,3})\b")
LANGUAGE_RE: re.Pattern[str] = re.compile(
    r"(?i)(?:^|\s-\s)(?P<lang>[A-Z]{2})(?:\s*\((?:tit|title)[\s.]*(?P<sub>[A-Z]{2})\))?$"
)
SEPARATORS_RE: re.Pattern[str] = re.compile(r"[._]+")
MULTISPACE_RE: re.Pattern[str] = re.compile(r"\s+")


class MediaParser(LoggingMixin):
    """Parse discovered media items into a structured representation."""

    def parse(self, item: MediaItem) -> ParsedMediaItem:
        """Parse a media item from its filename and path context.

        :param item: The media item to parse.
        :return: A ParsedMediaItem with extracted metadata and classification.
        """
        raw_name: str = item.path.stem
        cleaned_name: str = self._cleanup_name(raw_name)

        episode_match: re.Match[str] | None = EPISODE_RE.search(cleaned_name)
        if episode_match is not None:
            return self._parse_tv_episode(item=item, cleaned_name=cleaned_name, match=episode_match)

        year_match: re.Match[str] | None = YEAR_RE.search(cleaned_name)
        if year_match is not None:
            return self._parse_movie(item=item, cleaned_name=cleaned_name, match=year_match)

        return ParsedMediaItem(
            source=item,
            media_type="unknown",
            title=cleaned_name,
            normalized_title=cleaned_name,
            confidence=0.2,
            issues=["Unable to detect movie year or TV episode pattern."],
        )

    def _parse_movie(
        self, item: MediaItem, cleaned_name: str, match: re.Match[str]
    ) -> ParsedMediaItem:
        """Parse a movie item based on a year pattern match.

        :param item: The media item to parse.
        :param cleaned_name: The cleaned filename to extract metadata from.
        :param match: The regex match object containing the year.
        :return: A ParsedMediaItem with extracted movie metadata.
        """
        language: str | None
        subtitle_language: str | None
        name_without_language: str
        language, subtitle_language, name_without_language = self._extract_language(cleaned_name)
        year: int = int(match.group(1))
        title_part: str = name_without_language[: match.start()].strip(" -")
        normalized_title: str = self._normalize_title(title_part)
        issues: list[str] = []
        confidence: float = 0.9
        if not normalized_title:
            normalized_title = cleaned_name
            issues.append("Movie title could not be normalized cleanly.")
            confidence = 0.5
        return ParsedMediaItem(
            source=item,
            media_type="movie",
            title=title_part or cleaned_name,
            normalized_title=normalized_title,
            year=year,
            language=language,
            subtitle_language=subtitle_language,
            confidence=confidence,
            issues=issues,
        )

    def _parse_tv_episode(
        self, item: MediaItem, cleaned_name: str, match: re.Match[str]
    ) -> ParsedMediaItem:
        """Parse a TV episode item based on an SxxExx pattern match.

        :param item: The media item to parse.
        :param cleaned_name: The cleaned filename to extract metadata from.
        :param match: The regex match object containing the season and episode.
        :return: A ParsedMediaItem with extracted TV episode metadata.
        """
        language: str | None
        subtitle_language: str | None
        name_without_language: str
        language, subtitle_language, name_without_language = self._extract_language(cleaned_name)
        title_part: str = name_without_language[: match.start()].strip(" -")
        normalized_title: str = self._normalize_title(title_part)
        season: int = int(match.group("season"))
        episode: int = int(match.group("episode"))
        issues: list[str] = []
        confidence: float = 0.92
        if not normalized_title:
            normalized_title = cleaned_name
            issues.append("Episode title could not be normalized cleanly.")
            confidence = 0.55
        return ParsedMediaItem(
            source=item,
            media_type="tv_episode",
            title=title_part or cleaned_name,
            normalized_title=normalized_title,
            season=season,
            episode=episode,
            language=language,
            subtitle_language=subtitle_language,
            confidence=confidence,
            issues=issues,
        )

    def _cleanup_name(self, value: str) -> str:
        """Clean up the raw filename by replacing separators and normalizing whitespace.

        :param value: The raw filename to clean up.
        :return: The cleaned filename.
        """
        normalized: str = SEPARATORS_RE.sub(" ", value)
        normalized = MULTISPACE_RE.sub(" ", normalized).strip()
        return normalized

    def _extract_language(self, value: str) -> tuple[str | None, str | None, str]:
        """Extract language and subtitle information from the filename if present.

        :param value: The cleaned filename to extract language info from.
        :return: A tuple of (language, subtitle_language, name_without_language).
        """
        match: re.Match[str] | None = LANGUAGE_RE.search(value)
        if match is None:
            return None, None, value
        language: str | None = match.group("lang").upper()
        subtitle_language: str | None = match.group("sub")
        if language not in LANGUAGE_CODES:
            return None, None, value
        if subtitle_language is not None:
            subtitle_language = subtitle_language.upper()
        stripped: str = value[: match.start()].strip()
        return language, subtitle_language, stripped

    def _normalize_title(self, value: str) -> str:
        """Normalize the title by removing known noise tokens and extra whitespace.

        :param value: The title part of the filename to normalize.
        :return: The normalized title.
        """
        tokens: list[str] = []
        for token in value.split():
            if token.lower() in KNOWN_NOISE_TOKENS:
                continue
            tokens.append(token)
        joined: str = " ".join(tokens).strip(" -")
        return MULTISPACE_RE.sub(" ", joined).strip()
