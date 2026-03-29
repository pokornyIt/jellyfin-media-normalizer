"""Filesystem library scanning."""

from __future__ import annotations

from pathlib import Path

from jellyfin_media_normalizer.constants import SUPPORTED_VIDEO_EXTENSIONS
from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.utils.logging import LoggingMixin


class LibraryScanner(LoggingMixin):
    """Scan a mounted media library for supported video files."""

    def __init__(self, library_path: Path) -> None:
        """Initialize the scanner.

        :param library_path: Root library path to scan.
        """
        self.library_path: Path = library_path

    def scan(self) -> list[MediaItem]:
        """Scan the configured library path.

        :return: List of discovered media items.
        :raises FileNotFoundError: If the library path does not exist.
        :raises NotADirectoryError: If the library path is not a directory.
        """
        if not self.library_path.exists():
            raise FileNotFoundError(f"Library path does not exist: {self.library_path}")

        if not self.library_path.is_dir():
            raise NotADirectoryError(f"Library path is not a directory: {self.library_path}")

        self.log.info(
            "Starting library scan", extra={"extra": {"library_path": str(self.library_path)}}
        )

        items: list[MediaItem] = []
        for path in sorted(self.library_path.rglob("*")):
            if not path.is_file():
                continue

            if path.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
                continue

            items.append(
                MediaItem(
                    path=path,
                    relative_path=path.relative_to(self.library_path),
                    extension=path.suffix.lower(),
                )
            )

        self.log.info("Library scan finished", extra={"extra": {"item_count": len(items)}})
        return items
