"""Tests for library scanner."""

from __future__ import annotations

from pathlib import Path

import pytest

from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.scanners.library_scanner import LibraryScanner


class TestLibraryScannerInitialization:
    """Tests for :class:`LibraryScanner` initialization."""

    def test_init_stores_library_path(self, tmp_path: Path) -> None:
        """Initialization stores provided library path.

        :param tmp_path: Temporary directory for test artifacts.
        """
        scanner = LibraryScanner(library_path=tmp_path)

        assert scanner.library_path == tmp_path

    def test_init_accepts_path_object(self, tmp_path: Path) -> None:
        """Initialization accepts pathlib.Path objects.

        :param tmp_path: Temporary directory for test artifacts.
        """
        scanner = LibraryScanner(library_path=tmp_path)

        assert isinstance(scanner.library_path, Path)


class TestLibraryScannerScanning:
    """Tests for :meth:`LibraryScanner.scan`."""

    def test_scan_returns_list(self, tmp_path: Path) -> None:
        """Scan returns a list of MediaItems.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "movie.mkv").touch()
        scanner = LibraryScanner(library_path=tmp_path)

        result: list[MediaItem] = scanner.scan()

        assert isinstance(result, list)

    def test_scan_finds_single_video_file(self, tmp_path: Path) -> None:
        """Scan detects a single video file at root level.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "movie.mkv").touch()
        scanner = LibraryScanner(library_path=tmp_path)

        items: list[MediaItem] = scanner.scan()

        assert len(items) == 1
        assert items[0].extension == ".mkv"
        assert items[0].relative_path == Path("movie.mkv")

    def test_scan_finds_multiple_files(self, tmp_path: Path) -> None:
        """Scan detects multiple video files.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "movie1.mkv").touch()
        (tmp_path / "movie2.mp4").touch()
        (tmp_path / "movie3.avi").touch()
        scanner = LibraryScanner(library_path=tmp_path)

        items: list[MediaItem] = scanner.scan()

        assert len(items) == 3

    @pytest.mark.parametrize(
        "extension",
        [".mkv", ".mp4", ".avi", ".mov", ".m4v", ".wmv", ".ts", ".m2ts"],
    )
    def test_scan_supports_multiple_extensions(self, tmp_path: Path, extension: str) -> None:
        """Scan detects all supported video extensions.

        :param tmp_path: Temporary directory for test artifacts.
        :param extension: File extension to test.
        """
        (tmp_path / f"movie{extension}").touch()
        scanner = LibraryScanner(library_path=tmp_path)

        items: list[MediaItem] = scanner.scan()

        assert len(items) == 1
        assert items[0].extension == extension

    def test_scan_handles_nested_directories(self, tmp_path: Path) -> None:
        """Scan discovers files in nested subdirectories.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "movies" / "action").mkdir(parents=True)
        (tmp_path / "movies" / "action" / "movie.mkv").touch()
        (tmp_path / "series").mkdir()
        (tmp_path / "series" / "episode.mp4").touch()
        scanner = LibraryScanner(library_path=tmp_path)

        items: list[MediaItem] = scanner.scan()

        assert len(items) == 2

    def test_scan_calculates_relative_paths(self, tmp_path: Path) -> None:
        """Scan correctly calculates relative paths for all items.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "root_movie.mkv").touch()
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "nested_movie.mp4").touch()
        scanner = LibraryScanner(library_path=tmp_path)

        items: list[MediaItem] = scanner.scan()

        relative_paths: set[Path] = {item.relative_path for item in items}
        assert Path("root_movie.mkv") in relative_paths
        assert Path("subdir/nested_movie.mp4") in relative_paths

    def test_scan_returns_sorted_results(self, tmp_path: Path) -> None:
        """Scan returns items in sorted order.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "z_movie.mkv").touch()
        (tmp_path / "a_movie.mkv").touch()
        (tmp_path / "m_movie.mkv").touch()
        scanner = LibraryScanner(library_path=tmp_path)

        items: list[MediaItem] = scanner.scan()
        paths: list[Path] = [item.path for item in items]

        assert paths == sorted(paths)

    def test_scan_normalizes_extension_to_lowercase(self, tmp_path: Path) -> None:
        """Scan normalizes file extensions to lowercase.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "movie.MKV").touch()
        scanner = LibraryScanner(library_path=tmp_path)

        items: list[MediaItem] = scanner.scan()

        assert items[0].extension == ".mkv"

    def test_scan_ignores_non_video_files(self, tmp_path: Path) -> None:
        """Scan excludes files with unsupported extensions.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "movie.mkv").touch()
        (tmp_path / "readme.txt").touch()
        (tmp_path / "image.jpg").touch()
        (tmp_path / "document.pdf").touch()
        scanner = LibraryScanner(library_path=tmp_path)

        items: list[MediaItem] = scanner.scan()

        assert len(items) == 1
        assert items[0].extension == ".mkv"

    def test_scan_ignores_directories(self, tmp_path: Path) -> None:
        """Scan ignores directories and only returns files.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "movies").mkdir()
        (tmp_path / "movies" / "movie.mkv").touch()
        scanner = LibraryScanner(library_path=tmp_path)

        items: list[MediaItem] = scanner.scan()

        assert len(items) == 1
        assert all(item for item in items)

    def test_scan_empty_library_returns_empty_list(self, tmp_path: Path) -> None:
        """Scan on empty library returns empty list.

        :param tmp_path: Temporary directory for test artifacts.
        """
        scanner = LibraryScanner(library_path=tmp_path)

        items: list[MediaItem] = scanner.scan()

        assert items == []

    def test_scan_library_with_only_non_video_files(self, tmp_path: Path) -> None:
        """Scan library with only non-video files returns empty list.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "file.txt").touch()
        (tmp_path / "image.jpg").touch()
        scanner = LibraryScanner(library_path=tmp_path)

        items: list[MediaItem] = scanner.scan()

        assert items == []

    def test_scan_returns_media_items(self, tmp_path: Path) -> None:
        """Scan returns MediaItem instances.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "movie.mkv").touch()
        scanner = LibraryScanner(library_path=tmp_path)

        items: list[MediaItem] = scanner.scan()

        assert all(isinstance(item, MediaItem) for item in items)

    def test_scan_sets_absolute_path(self, tmp_path: Path) -> None:
        """Scan correctly sets absolute path for items.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "movie.mkv").touch()
        scanner = LibraryScanner(library_path=tmp_path)

        items: list[MediaItem] = scanner.scan()

        assert items[0].path.is_absolute()
        assert items[0].path.exists()

    def test_scan_mixed_extensions_and_directories(self, tmp_path: Path) -> None:
        """Scan handles complex structure with mixed extensions and depths.

        :param tmp_path: Temporary directory for test artifacts.
        """
        (tmp_path / "movies" / "action").mkdir(parents=True)
        (tmp_path / "movies" / "action" / "film1.mkv").touch()
        (tmp_path / "movies" / "action" / "film2.mp4").touch()
        (tmp_path / "series" / "s01").mkdir(parents=True)
        (tmp_path / "series" / "s01" / "e01.mkv").touch()
        (tmp_path / "readme.txt").touch()
        scanner = LibraryScanner(library_path=tmp_path)

        items: list[MediaItem] = scanner.scan()

        assert len(items) == 3
        assert all(item.extension in [".mkv", ".mp4"] for item in items)


class TestLibraryScannerErrorHandling:
    """Tests for error handling in :class:`LibraryScanner`."""

    def test_scan_missing_library_path_raises_file_not_found(self, tmp_path: Path) -> None:
        """Scan raises FileNotFoundError when library path does not exist.

        :param tmp_path: Temporary directory for test artifacts.
        """
        non_existent_path: Path = tmp_path / "does_not_exist"
        scanner = LibraryScanner(library_path=non_existent_path)

        with pytest.raises(FileNotFoundError):
            scanner.scan()

    def test_scan_error_message_includes_path(self, tmp_path: Path) -> None:
        """FileNotFoundError message includes the missing path.

        :param tmp_path: Temporary directory for test artifacts.
        """
        non_existent_path: Path = tmp_path / "does_not_exist"
        scanner = LibraryScanner(library_path=non_existent_path)

        with pytest.raises(FileNotFoundError, match=str(non_existent_path)):
            scanner.scan()

    def test_scan_file_instead_of_directory_raises_not_a_directory(self, tmp_path: Path) -> None:
        """Scan raises NotADirectoryError when library path is a file.

        :param tmp_path: Temporary directory for test artifacts.
        """
        file_path: Path = tmp_path / "file.txt"
        file_path.touch()
        scanner = LibraryScanner(library_path=file_path)

        with pytest.raises(NotADirectoryError):
            scanner.scan()

    def test_scan_not_a_directory_error_message_includes_path(self, tmp_path: Path) -> None:
        """NotADirectoryError message includes the problematic path.

        :param tmp_path: Temporary directory for test artifacts.
        """
        file_path: Path = tmp_path / "file.txt"
        file_path.touch()
        scanner = LibraryScanner(library_path=file_path)

        with pytest.raises(NotADirectoryError, match=str(file_path)):
            scanner.scan()

    def test_scan_non_existent_is_checked_before_is_dir(self, tmp_path: Path) -> None:
        """Scan checks path existence before directory status.

        :param tmp_path: Temporary directory for test artifacts.
        """
        non_existent: Path = tmp_path / "does_not_exist"
        scanner = LibraryScanner(library_path=non_existent)

        # Should raise FileNotFoundError, not NotADirectoryError
        with pytest.raises(FileNotFoundError):
            scanner.scan()
