"""Service for parsing scanned media items."""

from __future__ import annotations

from typing import Protocol

from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.parsers.media_parser import MediaParser
from jellyfin_media_normalizer.settings import Settings
from jellyfin_media_normalizer.utils.logging import LoggingMixin


class MediaItemParserProtocol(Protocol):
    """Protocol for parser dependency used by ParseService."""

    def parse(self, item: MediaItem) -> ParsedMediaItem:
        """Parse a media item.

        :param item: Input media item.
        :return: Parsed media item.
        """
        ...


class ParseService(LoggingMixin):
    """Coordinate parsing of scanned media items."""

    def __init__(self, settings: Settings, parser: MediaItemParserProtocol | None = None) -> None:
        """Initialize the service.

        :param settings: Application settings to use for parsing context.
        :param parser: Optional media parser implementation.
        """
        self.settings: Settings = settings
        self.parser: MediaItemParserProtocol = parser or MediaParser()

    def run(self, media_items: list[MediaItem]) -> list[ParsedMediaItem]:
        """Run the parsing process on a list of media items.

        :param media_items: A list of MediaItem objects to be parsed.
        :return: A list of ParsedMediaItem objects resulting from the parsing process.
        """
        self.log.info("Running parse service", extra={"extra": {"item_count": len(media_items)}})
        parsed_items: list[ParsedMediaItem] = [self.parser.parse(item) for item in media_items]
        self.log.info("Parse service finished", extra={"extra": {"item_count": len(parsed_items)}})
        return parsed_items
