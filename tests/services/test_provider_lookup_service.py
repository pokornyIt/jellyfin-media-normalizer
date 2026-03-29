"""Tests for provider lookup service."""

from __future__ import annotations

from pathlib import Path

from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.provider_match import ProviderMatch
from jellyfin_media_normalizer.services.provider_lookup_service import ProviderLookupService
from jellyfin_media_normalizer.settings import Settings


def _make_settings(workspace_path: Path | None = None) -> Settings:
    """Create settings for tests.

    :param workspace_path: Optional workspace path.
    :return: Settings instance.
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
    """Create parsed item for tests.

    :param media_type: Media type value.
    :param normalized_title: Normalized title.
    :param year: Movie year.
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


class _FakeResolver:
    """Fake provider resolver."""

    def __init__(self, match: ProviderMatch | None) -> None:
        """Initialize fake resolver.

        :param match: Match returned for non-unknown media.
        """
        self.match: ProviderMatch | None = match

    def resolve(self, item: ParsedMediaItem) -> ProviderMatch | None:
        """Resolve deterministic test output.

        :param item: Parsed item.
        :return: Fixed match.
        """
        return self.match


class TestProviderLookupService:
    """Test ProviderLookupService behavior."""

    def test_run_attaches_provider_match(self) -> None:
        """Resolved match must be stored on item."""
        settings: Settings = _make_settings()
        expected_match = ProviderMatch(
            provider="tmdb",
            provider_id="19995",
            confidence=0.98,
            reason="cache_exact_key:movie|avatar|2009",
            lookup_key="movie|avatar|2009",
        )
        service = ProviderLookupService(settings=settings, resolver=_FakeResolver(expected_match))
        items: list[ParsedMediaItem] = [_make_item("movie", "avatar", year=2009)]

        result: list[ParsedMediaItem] = service.run(items)

        assert result[0].provider_match is not None
        assert result[0].provider_match.provider == "tmdb"
        assert result[0].provider_match.provider_id == "19995"

    def test_run_adds_issue_when_match_missing(self) -> None:
        """Unresolved item gets provider lookup issue."""
        settings: Settings = _make_settings()
        service = ProviderLookupService(settings=settings, resolver=_FakeResolver(None))
        items: list[ParsedMediaItem] = [_make_item("movie", "avatar", year=2009)]

        result: list[ParsedMediaItem] = service.run(items)

        assert result[0].provider_match is None
        assert "Provider ID not found in provider cache." in result[0].issues

    def test_run_skips_unknown_media_type(self) -> None:
        """Unknown media type should not call provider mapping path."""
        settings: Settings = _make_settings()
        service = ProviderLookupService(settings=settings, resolver=_FakeResolver(None))
        items: list[ParsedMediaItem] = [_make_item("unknown", "unknown title")]

        result: list[ParsedMediaItem] = service.run(items)

        assert result[0].provider_match is None
        assert "Provider lookup skipped for unknown media type." in result[0].issues
