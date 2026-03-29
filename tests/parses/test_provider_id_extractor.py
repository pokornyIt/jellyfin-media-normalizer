"""Tests for provider ID extraction from source paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.provider_match import ProviderMatch
from jellyfin_media_normalizer.parsers.provider_id_extractor import extract_provider_id_from_source


@pytest.mark.parametrize(
    ("relative_path", "expected_provider", "expected_provider_id"),
    [
        ("Avatar (2009) [imdbid-tt0499549].mkv", "imdb", "tt0499549"),
        ("Avatar (2009) [IMDBID-tt0499549].mkv", "imdb", "tt0499549"),
        ("Avatar (2009) [tmdbid-19995].mkv", "tmdb", "19995"),
        ("Avatar (2009) [TMDBID-19995].mkv", "tmdb", "19995"),
    ],
)
def test_extract_provider_id_from_source_match(
    relative_path: str,
    expected_provider: str,
    expected_provider_id: str,
) -> None:
    """Extract provider ID from source path when embedded marker is present.

    :param relative_path: Relative path containing embedded provider marker.
    :param expected_provider: Expected provider name.
    :param expected_provider_id: Expected provider ID.
    """
    item = ParsedMediaItem(
        source=MediaItem(
            path=Path("/library") / relative_path,
            relative_path=Path(relative_path),
            extension=".mkv",
        ),
        media_type="movie",
        title="Avatar",
        normalized_title="avatar",
        year=2009,
    )

    match: ProviderMatch | None = extract_provider_id_from_source(item)

    assert match is not None
    assert match.provider == expected_provider
    assert match.provider_id == expected_provider_id


def test_extract_provider_id_from_source_no_match() -> None:
    """Return ``None`` when no embedded marker is present.

    :return: None
    """
    item = ParsedMediaItem(
        source=MediaItem(
            path=Path("/library/Avatar (2009).mkv"),
            relative_path=Path("Avatar (2009).mkv"),
            extension=".mkv",
        ),
        media_type="movie",
        title="Avatar",
        normalized_title="avatar",
        year=2009,
    )

    match: ProviderMatch | None = extract_provider_id_from_source(item)

    assert match is None
