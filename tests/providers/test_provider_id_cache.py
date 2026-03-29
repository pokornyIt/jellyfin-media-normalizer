"""Tests for cache-based provider ID resolver."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.provider_match import ProviderMatch
from jellyfin_media_normalizer.providers.provider_id_cache import ProviderIdCacheResolver


def _make_parsed_item(
    media_type: str,
    normalized_title: str,
    year: int | None = None,
    season: int | None = None,
    episode: int | None = None,
) -> ParsedMediaItem:
    """Create parsed item for tests.

    :param media_type: Media type string.
    :param normalized_title: Normalized title value.
    :param year: Movie year.
    :param season: TV season.
    :param episode: TV episode.
    :return: Parsed item.
    """
    return ParsedMediaItem(
        source=MediaItem(
            path=Path("/library/item.mkv"),
            relative_path=Path("item.mkv"),
            extension=".mkv",
        ),
        media_type=media_type,
        title=normalized_title,
        normalized_title=normalized_title,
        year=year,
        season=season,
        episode=episode,
    )


class TestProviderIdCacheResolver:
    """Test ProviderIdCacheResolver."""

    def test_resolve_movie_with_year(self, tmp_path: Path) -> None:
        """Resolve movie key with year from cache.

        :param tmp_path: Temporary path fixture.
        """
        cache_path: Path = tmp_path / "provider_ids.json"
        cache_payload: dict[str, object] = {
            "entries": {
                "movie|avatar|2009": {
                    "provider": "tmdb",
                    "provider_id": "19995",
                    "confidence": 0.99,
                }
            }
        }
        cache_path.write_text(json.dumps(cache_payload), encoding="utf-8")

        resolver = ProviderIdCacheResolver(cache_path)
        item: ParsedMediaItem = _make_parsed_item(
            media_type="movie",
            normalized_title="Avatar",
            year=2009,
        )

        match: ProviderMatch | None = resolver.resolve(item)

        assert match is not None
        assert match.provider == "tmdb"
        assert match.provider_id == "19995"
        assert match.lookup_key == "movie|avatar|2009"

    def test_resolve_tv_episode_uses_series_key_only(self, tmp_path: Path) -> None:
        """Resolve TV episode by series-level key only.

        :param tmp_path: Temporary path fixture.
        """
        cache_path: Path = tmp_path / "provider_ids.json"
        cache_payload: dict[str, object] = {
            "entries": {
                "tv_series|breaking bad": {
                    "provider": "tvdb",
                    "provider_id": "81189",
                }
            }
        }
        cache_path.write_text(json.dumps(cache_payload), encoding="utf-8")

        resolver = ProviderIdCacheResolver(cache_path)
        item: ParsedMediaItem = _make_parsed_item(
            media_type="tv_episode",
            normalized_title="Breaking Bad",
            season=1,
            episode=1,
        )

        match: ProviderMatch | None = resolver.resolve(item)

        assert match is not None
        assert match.lookup_key == "tv_series|breaking bad"
        assert match.provider_id == "81189"

    def test_resolve_returns_none_when_file_missing(self, tmp_path: Path) -> None:
        """Missing cache file must return no match.

        :param tmp_path: Temporary path fixture.
        """
        resolver = ProviderIdCacheResolver(tmp_path / "provider_ids.json")
        item: ParsedMediaItem = _make_parsed_item(
            media_type="movie",
            normalized_title="Avatar",
            year=2009,
        )

        assert resolver.resolve(item) is None

    @pytest.mark.parametrize("media_type", ["unknown", "music_video"])
    def test_resolve_returns_none_for_unsupported_media_type(
        self,
        media_type: str,
        tmp_path: Path,
    ) -> None:
        """Unsupported media types are not resolved.

        :param media_type: Media type under test.
        :param tmp_path: Temporary path fixture.
        """
        resolver = ProviderIdCacheResolver(tmp_path / "provider_ids.json")
        item: ParsedMediaItem = _make_parsed_item(
            media_type=media_type,
            normalized_title="Anything",
        )

        assert resolver.resolve(item) is None
