"""Tests for parse service."""

from __future__ import annotations

from pathlib import Path

from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.services.parse_service import ParseService
from jellyfin_media_normalizer.settings import Settings


def _make_settings(
    library_path: Path | None = None, workspace_path: Path | None = None
) -> Settings:
    """Create test settings.

    :param library_path: Optional library path.
    :param workspace_path: Optional workspace path.
    :return: Configured Settings instance.
    """
    if library_path is None:
        library_path = Path("/library")
    if workspace_path is None:
        workspace_path = Path("/workspace")

    return Settings(
        app_name="test-app",
        library_path=library_path,
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


def _make_media_item(
    path: str = "/library/movies/Avatar.mkv",
    relative_path: str = "Avatar.mkv",
    extension: str = ".mkv",
) -> MediaItem:
    """Create a test MediaItem.

    :param path: Absolute file path.
    :param relative_path: Relative file path.
    :param extension: File extension.
    :return: Constructed MediaItem.
    """
    return MediaItem(
        path=Path(path),
        relative_path=Path(relative_path),
        extension=extension,
    )


class TestParseServiceInitialization:
    """Tests for :class:`ParseService` initialization."""

    def test_init_stores_settings(self) -> None:
        """Initialization stores provided settings.

        :return: None
        """
        settings: Settings = _make_settings()
        service = ParseService(settings=settings)

        assert service.settings is settings

    def test_init_creates_parser(self) -> None:
        """Initialization creates a MediaParser instance.

        :return: None
        """
        settings: Settings = _make_settings()
        service = ParseService(settings=settings)

        assert service.parser is not None

    def test_init_accepts_settings_object(self) -> None:
        """Initialization accepts Settings object.

        :return: None
        """
        settings: Settings = _make_settings()
        service = ParseService(settings=settings)

        assert isinstance(service.settings, Settings)


class TestParseServiceRun:
    """Tests for :meth:`ParseService.run`."""

    def test_run_returns_list(self) -> None:
        """Run returns a list of ParsedMediaItems.

        :return: None
        """
        settings: Settings = _make_settings()
        service = ParseService(settings=settings)
        items: list[MediaItem] = [_make_media_item(path="/library/movies/Avatar.mkv")]

        result: list[ParsedMediaItem] = service.run(media_items=items)

        assert isinstance(result, list)

    def test_run_parses_single_item(self) -> None:
        """Run parses a single media item.

        :return: None
        """
        settings: Settings = _make_settings()
        service = ParseService(settings=settings)
        items: list[MediaItem] = [_make_media_item(path="/library/movies/Avatar.2009.mkv")]

        result: list[ParsedMediaItem] = service.run(media_items=items)

        assert len(result) == 1
        assert isinstance(result[0], ParsedMediaItem)
        assert result[0].title == "Avatar"
        assert result[0].year == 2009

    def test_run_parses_multiple_items(self) -> None:
        """Run parses multiple media items.

        :return: None
        """
        settings: Settings = _make_settings()
        service = ParseService(settings=settings)
        items: list[MediaItem] = [
            _make_media_item(path="/library/movies/Avatar.2009.mkv"),
            _make_media_item(path="/library/movies/The.Matrix.1999.mp4"),
            _make_media_item(path="/library/series/Breaking.Bad.S01E01.mkv"),
        ]

        result: list[ParsedMediaItem] = service.run(media_items=items)

        assert len(result) == 3
        assert all(isinstance(item, ParsedMediaItem) for item in result)

    def test_run_preserves_media_item_count(self) -> None:
        """Run returns same number of items as input.

        :return: None
        """
        settings: Settings = _make_settings()
        service = ParseService(settings=settings)
        items: list[MediaItem] = [_make_media_item(path=f"/library/movie{i}.mkv") for i in range(5)]

        result: list[ParsedMediaItem] = service.run(media_items=items)

        assert len(result) == len(items)

    def test_run_handles_empty_list(self) -> None:
        """Run handles empty media items list.

        :return: None
        """
        settings: Settings = _make_settings()
        service = ParseService(settings=settings)

        result: list[ParsedMediaItem] = service.run(media_items=[])

        assert result == []

    def test_run_parses_all_items_sequentially(self) -> None:
        """Run parses all items maintaining order.

        :return: None
        """
        settings: Settings = _make_settings()
        service = ParseService(settings=settings)
        items: list[MediaItem] = [
            _make_media_item(path="/library/Avatar.2009.mkv"),
            _make_media_item(path="/library/Matrix.1999.mkv"),
            _make_media_item(path="/library/Inception.2010.mkv"),
        ]

        result: list[ParsedMediaItem] = service.run(media_items=items)

        assert result[0].year == 2009
        assert result[1].year == 1999
        assert result[2].year == 2010

    def test_run_sets_source_reference(self) -> None:
        """Run maintains reference to source MediaItem.

        :return: None
        """
        settings: Settings = _make_settings()
        service = ParseService(settings=settings)
        items: list[MediaItem] = [_make_media_item(path="/library/Avatar.2009.mkv")]

        result: list[ParsedMediaItem] = service.run(media_items=items)

        assert result[0].source == items[0]

    def test_run_with_different_media_types(self) -> None:
        """Run parses both movies and TV episodes.

        :return: None
        """
        settings: Settings = _make_settings()
        service = ParseService(settings=settings)
        items: list[MediaItem] = [
            _make_media_item(path="/library/Avatar.2009.mkv"),
            _make_media_item(path="/library/Breaking.Bad.S01E01.mkv"),
        ]

        result: list[ParsedMediaItem] = service.run(media_items=items)

        media_types: set[str] = {item.media_type for item in result}
        assert "movie" in media_types
        assert "tv_episode" in media_types

    def test_run_preserves_confidence_scores(self) -> None:
        """Run preserves confidence scores from parser.

        :return: None
        """
        settings: Settings = _make_settings()
        service = ParseService(settings=settings)
        items: list[MediaItem] = [
            _make_media_item(path="/library/Avatar.2009.mkv"),
            _make_media_item(path="/library/Unknown.File.mkv"),
        ]

        result: list[ParsedMediaItem] = service.run(media_items=items)

        # Movie with year should have higher confidence
        assert result[0].confidence > result[1].confidence

    def test_run_with_problematic_filenames(self) -> None:
        """Run handles filenames without standard patterns.

        :return: None
        """
        settings: Settings = _make_settings()
        service = ParseService(settings=settings)
        items: list[MediaItem] = [
            _make_media_item(path="/library/NoYearNoPattern.mkv"),
            _make_media_item(path="/library/Abstract.Title.mkv"),
        ]

        result: list[ParsedMediaItem] = service.run(media_items=items)

        assert len(result) == 2
        assert all(item.media_type == "unknown" for item in result)

    def test_run_multiple_calls_independent(self) -> None:
        """Run can be called multiple times independently.

        :return: None
        """
        settings: Settings = _make_settings()
        service = ParseService(settings=settings)
        items1: list[MediaItem] = [_make_media_item(path="/library/Avatar.2009.mkv")]
        items2: list[MediaItem] = [_make_media_item(path="/library/Matrix.1999.mkv")]

        result1: list[ParsedMediaItem] = service.run(media_items=items1)
        result2: list[ParsedMediaItem] = service.run(media_items=items2)

        assert result1[0].year == 2009
        assert result2[0].year == 1999
