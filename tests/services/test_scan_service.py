"""Tests for scan service."""

from __future__ import annotations

from pathlib import Path

import pytest

from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.services.scan_service import ScanService
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
        provider_lookup_progress_interval=100,
    )


class TestScanServiceInitialization:
    """Tests for :class:`ScanService` initialization."""

    def test_init_stores_settings(self, tmp_path: Path) -> None:
        """Initialization stores provided settings.

        :param tmp_path: Temporary directory for test artifacts.
        """
        settings: Settings = _make_settings(library_path=tmp_path)
        service = ScanService(settings=settings)

        assert service.settings is settings

    def test_init_creates_scanner(self, tmp_path: Path) -> None:
        """Initialization creates LibraryScanner instance.

        :param tmp_path: Temporary directory for test artifacts.
        """
        settings: Settings = _make_settings(library_path=tmp_path)
        service = ScanService(settings=settings)

        assert service.scanner is not None

    def test_init_scanner_uses_library_path(self, tmp_path: Path) -> None:
        """Scanner is initialized with library path from settings.

        :param tmp_path: Temporary directory for test artifacts.
        """
        settings: Settings = _make_settings(library_path=tmp_path)
        service = ScanService(settings=settings)

        assert service.scanner.library_path == tmp_path


class TestScanServiceRun:
    """Tests for :meth:`ScanService.run`."""

    def test_run_returns_list(self, tmp_path: Path) -> None:
        """Run returns a list of MediaItems.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "movie.mkv").touch()
        settings: Settings = _make_settings(library_path=tmp_path)
        service = ScanService(settings=settings)

        result: list[MediaItem] = service.run()

        assert isinstance(result, list)

    def test_run_discovers_single_file(self, tmp_path: Path) -> None:
        """Run discovers a single video file.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "movie.mkv").touch()
        settings: Settings = _make_settings(library_path=tmp_path)
        service = ScanService(settings=settings)

        result: list[MediaItem] = service.run()

        assert len(result) == 1
        assert isinstance(result[0], MediaItem)
        assert result[0].extension == ".mkv"

    def test_run_discovers_multiple_files(self, tmp_path: Path) -> None:
        """Run discovers multiple video files.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "movie1.mkv").touch()
        (tmp_path / "movie2.mp4").touch()
        (tmp_path / "movie3.avi").touch()
        settings: Settings = _make_settings(library_path=tmp_path)
        service = ScanService(settings=settings)

        result: list[MediaItem] = service.run()

        assert len(result) == 3
        assert all(isinstance(item, MediaItem) for item in result)

    def test_run_handles_empty_library(self, tmp_path: Path) -> None:
        """Run returns empty list for empty library.

        :param tmp_path: Temporary directory for test artifacts.
        """
        settings: Settings = _make_settings(library_path=tmp_path)
        service = ScanService(settings=settings)

        result: list[MediaItem] = service.run()

        assert result == []

    def test_run_discovers_nested_files(self, tmp_path: Path) -> None:
        """Run discovers files in nested directories.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "movies" / "action").mkdir(parents=True)
        (tmp_path / "movies" / "action" / "film.mkv").touch()
        (tmp_path / "series").mkdir()
        (tmp_path / "series" / "episode.mp4").touch()
        settings: Settings = _make_settings(library_path=tmp_path)
        service = ScanService(settings=settings)

        result: list[MediaItem] = service.run()

        assert len(result) == 2

    def test_run_ignores_non_video_files(self, tmp_path: Path) -> None:
        """Run ignores files with unsupported extensions.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "movie.mkv").touch()
        (tmp_path / "readme.txt").touch()
        (tmp_path / "image.jpg").touch()
        settings: Settings = _make_settings(library_path=tmp_path)
        service = ScanService(settings=settings)

        result: list[MediaItem] = service.run()

        assert len(result) == 1
        assert result[0].extension == ".mkv"

    def test_run_returns_absolute_paths(self, tmp_path: Path) -> None:
        """Run returns items with absolute paths.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "movie.mkv").touch()
        settings: Settings = _make_settings(library_path=tmp_path)
        service = ScanService(settings=settings)

        result: list[MediaItem] = service.run()

        assert result[0].path.is_absolute()

    def test_run_returns_relative_paths(self, tmp_path: Path) -> None:
        """Run returns items with relative paths.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "movie.mkv").touch()
        settings: Settings = _make_settings(library_path=tmp_path)
        service = ScanService(settings=settings)

        result: list[MediaItem] = service.run()

        assert result[0].relative_path == Path("subdir/movie.mkv")

    def test_run_normalizes_extensions(self, tmp_path: Path) -> None:
        """Run normalizes file extensions to lowercase.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "movie.MKV").touch()
        settings: Settings = _make_settings(library_path=tmp_path)
        service = ScanService(settings=settings)

        result: list[MediaItem] = service.run()

        assert result[0].extension == ".mkv"

    def test_run_multiple_calls_independent(self, tmp_path: Path) -> None:
        """Run can be called multiple times independently.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "movie1.mkv").touch()
        settings: Settings = _make_settings(library_path=tmp_path)
        service = ScanService(settings=settings)

        result1: list[MediaItem] = service.run()
        (tmp_path / "movie2.mkv").touch()
        result2: list[MediaItem] = service.run()

        assert len(result1) == 1
        assert len(result2) == 2

    def test_run_with_multiple_extensions(self, tmp_path: Path) -> None:
        """Run discovers files with various supported extensions.

        :param tmp_path: Temporary directory for test artifacts.
        """
        extensions: list[str] = [".mkv", ".mp4", ".avi", ".mov", ".m4v", ".wmv", ".ts", ".m2ts"]
        for i, ext in enumerate(extensions):
            (tmp_path / f"movie{i}{ext}").touch()

        settings: Settings = _make_settings(library_path=tmp_path)
        service = ScanService(settings=settings)

        result: list[MediaItem] = service.run()

        assert len(result) == len(extensions)
        found_extensions: set[str] = {item.extension for item in result}
        assert found_extensions == set(extensions)

    def test_run_with_deeply_nested_structure(self, tmp_path: Path) -> None:
        """Run discovers files in deeply nested directory structure.

        :param tmp_path: Temporary directory for test artifacts.
        """
        nested: Path = tmp_path / "level1" / "level2" / "level3" / "level4"
        nested.mkdir(parents=True)
        (nested / "deep_movie.mkv").touch()

        settings: Settings = _make_settings(library_path=tmp_path)
        service = ScanService(settings=settings)

        result: list[MediaItem] = service.run()

        assert len(result) == 1
        assert "level1" in str(result[0].relative_path)

    def test_run_returns_sorted_results(self, tmp_path: Path) -> None:
        """Run returns items in sorted order.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "z_movie.mkv").touch()
        (tmp_path / "a_movie.mkv").touch()
        (tmp_path / "m_movie.mkv").touch()

        settings: Settings = _make_settings(library_path=tmp_path)
        service = ScanService(settings=settings)

        result: list[MediaItem] = service.run()
        paths: list[Path] = [item.path for item in result]

        assert paths == sorted(paths)


class TestScanServiceErrorHandling:
    """Tests for error handling in :class:`ScanService`."""

    def test_run_with_non_existent_path_raises_error(self, tmp_path: Path) -> None:
        """Run raises error when library path does not exist.

        :param tmp_path: Temporary directory for test artifacts.
        """
        non_existent: Path = tmp_path / "does_not_exist"
        settings: Settings = _make_settings(library_path=non_existent)
        service = ScanService(settings=settings)

        with pytest.raises(FileNotFoundError):
            service.run()

    def test_run_with_file_instead_of_directory_raises_error(self, tmp_path: Path) -> None:
        """Run raises error when library path is a file.

        :param tmp_path: Temporary directory for test artifacts.
        """
        file_path: Path = tmp_path / "file.txt"
        file_path.touch()
        settings: Settings = _make_settings(library_path=file_path)
        service = ScanService(settings=settings)

        with pytest.raises(NotADirectoryError):
            service.run()
