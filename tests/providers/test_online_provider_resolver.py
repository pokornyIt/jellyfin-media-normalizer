"""Tests for online provider resolver."""

from __future__ import annotations

from pathlib import Path

from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.provider_match import ProviderMatch
from jellyfin_media_normalizer.providers.online_provider_resolver import OnlineProviderResolver
from jellyfin_media_normalizer.providers.provider_id_cache import ProviderIdCacheResolver
from jellyfin_media_normalizer.settings import Settings


def _make_settings(workspace_path: Path | None = None) -> Settings:
    """Create settings for tests.

    :param workspace_path: Optional workspace path.
    :return: Settings object.
    """
    if workspace_path is None:
        workspace_path = Path("/workspace")

    return Settings(
        app_name="test-app",
        library_path=Path("/library"),
        workspace_path=workspace_path,
        cache_path=workspace_path / "cache",
        reports_path=workspace_path / "reports",
        manifests_path=workspace_path / "manifests",
        logs_path=workspace_path / "logs",
        log_level="INFO",
        log_format="text",
        dry_run=True,
        tmdb_api_key=None,
        tvdb_api_key=None,
    )


def _make_item(media_type: str, normalized_title: str, year: int | None = None) -> ParsedMediaItem:
    """Create parsed item.

    :param media_type: Media type.
    :param normalized_title: Normalized title.
    :param year: Optional year.
    :return: Parsed media item.
    """
    return ParsedMediaItem(
        source=MediaItem(
            path=Path("/library/file.mkv"),
            relative_path=Path("file.mkv"),
            extension=".mkv",
        ),
        media_type=media_type,
        title=normalized_title,
        normalized_title=normalized_title,
        year=year,
    )


class _FakeMovieClient:
    """Fake movie client."""

    def __init__(self, match: ProviderMatch | None) -> None:
        """Initialize fake client.

        :param match: Match to return.
        """
        self.match: ProviderMatch | None = match

    def search_movie(self, title: str, year: int | None = None) -> ProviderMatch | None:
        """Return fixed movie match.

        :param title: Normalized title.
        :param year: Optional year.
        :return: Fixed match.
        """
        return self.match


class _FakeTvClient:
    """Fake TV client."""

    def __init__(self, match: ProviderMatch | None) -> None:
        """Initialize fake client.

        :param match: Match to return.
        """
        self.match: ProviderMatch | None = match

    def search_tv_series(self, title: str) -> ProviderMatch | None:
        """Return fixed TV match.

        :param title: Normalized title.
        :return: Fixed match.
        """
        return self.match


class TestOnlineProviderResolver:
    """Test online resolver behavior."""

    def test_resolve_movie_persists_to_cache(self, tmp_path: Path) -> None:
        """Movie online match must be persisted in cache.

        :param tmp_path: Temporary path fixture.
        """
        settings: Settings = _make_settings(workspace_path=tmp_path)
        cache = ProviderIdCacheResolver(settings.cache_path / "provider_ids.json")
        resolver = OnlineProviderResolver(
            settings=settings,
            cache_resolver=cache,
            movie_clients=[
                _FakeMovieClient(
                    ProviderMatch(
                        provider="tmdb",
                        provider_id="19995",
                        confidence=0.91,
                        reason="tmdb_search_movie",
                        lookup_key="",
                    )
                )
            ],
            tv_series_clients=[],
        )

        item: ParsedMediaItem = _make_item("movie", "avatar", year=2009)
        match: ProviderMatch | None = resolver.resolve(item)

        assert match is not None
        assert match.lookup_key == "movie|avatar|2009"
        cached_match: ProviderMatch | None = cache.resolve(item)
        assert cached_match is not None
        assert cached_match.provider_id == "19995"

    def test_resolve_tv_episode_uses_series_only(self, tmp_path: Path) -> None:
        """TV lookup must store series-level key only.

        :param tmp_path: Temporary path fixture.
        """
        settings: Settings = _make_settings(workspace_path=tmp_path)
        cache = ProviderIdCacheResolver(settings.cache_path / "provider_ids.json")
        resolver = OnlineProviderResolver(
            settings=settings,
            cache_resolver=cache,
            movie_clients=[],
            tv_series_clients=[
                _FakeTvClient(
                    ProviderMatch(
                        provider="tvdb",
                        provider_id="81189",
                        confidence=0.82,
                        reason="tvdb_search_series",
                        lookup_key="",
                    )
                )
            ],
        )

        item: ParsedMediaItem = _make_item("tv_episode", "breaking bad")
        match: ProviderMatch | None = resolver.resolve(item)

        assert match is not None
        assert match.lookup_key == "tv_series|breaking bad"
        assert match.provider_id == "81189"
