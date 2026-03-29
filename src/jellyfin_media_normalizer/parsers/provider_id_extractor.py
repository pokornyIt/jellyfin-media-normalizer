"""Provider ID extraction from source paths."""

from __future__ import annotations

import re

from jellyfin_media_normalizer.constants import PROVIDER_IMDB, PROVIDER_TMDB
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.provider_match import ProviderMatch

IMDB_ID_PATTERN: re.Pattern[str] = re.compile(r"\[imdbid-(tt\d+)\]", re.IGNORECASE)
TMDB_ID_PATTERN: re.Pattern[str] = re.compile(r"\[tmdbid-(\d+)\]", re.IGNORECASE)

PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (IMDB_ID_PATTERN, PROVIDER_IMDB),
    (TMDB_ID_PATTERN, PROVIDER_TMDB),
]


def extract_provider_id_from_source(item: ParsedMediaItem) -> ProviderMatch | None:
    """Extract explicit provider ID from source path.

    IDs in the form ``[imdbid-tt1234567]`` or ``[tmdbid-12345]`` are respected
    and used directly.

    :param item: Parsed media item.
    :return: Provider match built from source path metadata or ``None``.
    """
    source_path_text: str = str(item.source.relative_path)

    for pattern, provider in PATTERNS:
        match: re.Match[str] | None = pattern.search(source_path_text)
        if match is not None:
            return ProviderMatch(
                provider=provider,
                provider_id=match.group(1),
                confidence=1.0,
                reason=f"source_embedded_id:{provider}",
                lookup_key="",
            )

    return None
