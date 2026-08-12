"""Media item models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class MediaItem:
    """Represent a discovered media file.

    :param path: Absolute file path inside the container.
    :param relative_path: File path relative to the configured library root.
    :param extension: File extension including the leading dot.
    """

    path: Path
    relative_path: Path
    extension: str
