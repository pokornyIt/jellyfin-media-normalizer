"""Scan result models."""

from __future__ import annotations

from dataclasses import dataclass

from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.parsed_name import ParsedName


@dataclass(slots=True)
class ScanResult:
    """Represent a scanned media item with parser output.

    :param media_item: Original discovered media item.
    :param parsed_name: Parsed filename data.
    """

    media_item: MediaItem
    parsed_name: ParsedName
