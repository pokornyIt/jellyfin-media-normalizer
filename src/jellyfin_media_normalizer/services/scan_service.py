"""Service for executing library scans."""

from __future__ import annotations

from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.scanners.library_scanner import LibraryScanner
from jellyfin_media_normalizer.settings import Settings
from jellyfin_media_normalizer.utils.logging import LoggingMixin


class ScanService(LoggingMixin):
    """Coordinate media library scanning."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the service.

        :param settings: Application settings.
        """
        self.settings: Settings = settings
        self.scanner: LibraryScanner = LibraryScanner(settings.library_path)

    def run(self) -> list[MediaItem]:
        """Run a full scan.

        :return: Discovered media items.
        """
        self.log.info("Running scan service")
        return self.scanner.scan()
