"""Project-wide constants."""

from __future__ import annotations

APP_NAME: str = "jellyfin-media-normalizer"

SUPPORTED_VIDEO_EXTENSIONS: tuple[str, ...] = (
    ".mkv",
    ".mp4",
    ".avi",
    ".mov",
    ".m4v",
    ".wmv",
    ".ts",
    ".m2ts",
)
