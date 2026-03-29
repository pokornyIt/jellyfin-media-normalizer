"""Filename parsing and classification logic."""

from __future__ import annotations

from typing import Protocol

from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.media_type import MediaType
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.parsed_name import ParsedName
from jellyfin_media_normalizer.parsers.classifier import Classifier
from jellyfin_media_normalizer.parsers.filename_cleaner import FilenameCleaner
from jellyfin_media_normalizer.parsers.movie_name_parser import MovieNameParser
from jellyfin_media_normalizer.parsers.tv_episode_parser import TvEpisodeParser
from jellyfin_media_normalizer.utils.logging import LoggingMixin


class FilenameCleanerProtocol(Protocol):
    """Protocol for filename cleaning dependencies."""

    def clean(self, filename: str) -> str:
        """Clean a raw filename.

        :param filename: Raw filename.
        :return: Cleaned filename.
        """
        ...


class ClassifierProtocol(Protocol):
    """Protocol for media type classifier dependencies."""

    def classify(self, name: str) -> MediaType:
        """Classify a cleaned filename.

        :param name: Cleaned filename.
        :return: Classified media type.
        """
        ...


class MovieNameParserProtocol(Protocol):
    """Protocol for movie parser dependencies."""

    def parse(self, raw_name: str, normalized_name: str) -> ParsedName:
        """Parse movie naming information.

        :param raw_name: Raw input filename.
        :param normalized_name: Cleaned filename.
        :return: Parsed movie information.
        """
        ...


class TvEpisodeParserProtocol(Protocol):
    """Protocol for TV episode parser dependencies."""

    def parse(self, raw_name: str, normalized_name: str) -> ParsedName:
        """Parse TV naming information.

        :param raw_name: Raw input filename.
        :param normalized_name: Cleaned filename.
        :return: Parsed episode information.
        """
        ...


class MediaParser(LoggingMixin):
    """Parse discovered media items into a structured representation."""

    def __init__(
        self,
        cleaner: FilenameCleanerProtocol | None = None,
        classifier: ClassifierProtocol | None = None,
        movie_parser: MovieNameParserProtocol | None = None,
        tv_parser: TvEpisodeParserProtocol | None = None,
    ) -> None:
        """Initialize the parser and allow dependency injection.

        :param cleaner: Optional filename cleaner implementation.
        :param classifier: Optional media type classifier implementation.
        :param movie_parser: Optional movie filename parser implementation.
        :param tv_parser: Optional TV episode parser implementation.
        """
        self._cleaner: FilenameCleanerProtocol = cleaner or FilenameCleaner()
        self._classifier: ClassifierProtocol = classifier or Classifier()
        self._movie_parser: MovieNameParserProtocol = movie_parser or MovieNameParser()
        self._tv_parser: TvEpisodeParserProtocol = tv_parser or TvEpisodeParser()

    def parse(self, item: MediaItem) -> ParsedMediaItem:
        """Parse a media item from its filename and path context.

        :param item: The media item to parse.
        :return: A ParsedMediaItem with extracted metadata and classification.
        """
        raw_name: str = item.path.name
        normalized_name: str = self._cleaner.clean(raw_name)
        media_type: MediaType = self._classifier.classify(normalized_name)

        if media_type == MediaType.TV_EPISODE:
            parsed: ParsedName = self._tv_parser.parse(raw_name, normalized_name)
        elif media_type == MediaType.MOVIE:
            parsed = self._movie_parser.parse(raw_name, normalized_name)
        else:
            return ParsedMediaItem(
                source=item,
                media_type=MediaType.UNKNOWN,
                title=normalized_name,
                normalized_title=normalized_name,
                confidence=0.2,
                issues=["Unable to detect movie year or TV episode pattern."],
            )

        return self._to_parsed_media_item(item, parsed)

    def _to_parsed_media_item(self, item: MediaItem, parsed: ParsedName) -> ParsedMediaItem:
        """Convert a ParsedName to a ParsedMediaItem with its source item attached.

        :param item: The original scanned MediaItem.
        :param parsed: The parsing result from a specialized parser.
        :return: A ParsedMediaItem combining the source and parsed data.
        """
        issues: list[str] = []
        if not parsed.title:
            issues.append("Title could not be extracted from the filename.")
        subtitle_language: str | None = "CZ" if parsed.has_czech_subtitles else None
        if parsed.has_english_subtitles and not parsed.has_czech_subtitles:
            subtitle_language = "EN"
        title: str = parsed.title or parsed.normalized_name
        return ParsedMediaItem(
            source=item,
            media_type=parsed.media_type,
            title=title,
            normalized_title=title,
            year=parsed.year,
            season=parsed.season,
            episode=parsed.episode,
            language=parsed.language_code,
            subtitle_language=subtitle_language,
            confidence=parsed.confidence,
            issues=issues,
        )
