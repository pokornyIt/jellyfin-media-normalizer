"""Media type definitions."""

from __future__ import annotations

from enum import StrEnum


class MediaType(StrEnum):
    """Represent supported media types."""

    MOVIE = "movie"
    TV_EPISODE = "tv_episode"
    UNKNOWN = "unknown"
