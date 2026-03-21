"""Tests for path utility functions."""

from __future__ import annotations

from pathlib import Path

import pytest

from jellyfin_media_normalizer.utils.paths import ensure_directory


class TestEnsureDirectory:
    """Tests for :func:`ensure_directory`."""

    def test_creates_directory_if_not_exists(self, tmp_path: Path) -> None:
        """ensure_directory creates the directory when it does not exist.

        :param tmp_path: Temporary directory for test artifacts.
        """
        target = tmp_path / "new_dir"

        ensure_directory(target)

        assert target.exists()
        assert target.is_dir()

    def test_creates_nested_directories(self, tmp_path: Path) -> None:
        """ensure_directory creates all missing intermediate directories.

        :param tmp_path: Temporary directory for test artifacts.
        """
        target = tmp_path / "level1" / "level2" / "level3"

        ensure_directory(target)

        assert target.exists()
        assert target.is_dir()

    def test_does_not_raise_if_directory_already_exists(self, tmp_path: Path) -> None:
        """ensure_directory does not raise when directory already exists.

        :param tmp_path: Temporary directory for test artifacts.
        """
        target = tmp_path / "existing"
        target.mkdir()

        ensure_directory(target)

        assert target.exists()

    def test_does_not_raise_on_repeated_calls(self, tmp_path: Path) -> None:
        """ensure_directory is idempotent — repeated calls do not raise.

        :param tmp_path: Temporary directory for test artifacts.
        """
        target = tmp_path / "idempotent"

        ensure_directory(target)
        ensure_directory(target)

        assert target.is_dir()

    def test_accepts_path_object(self, tmp_path: Path) -> None:
        """ensure_directory accepts a pathlib.Path as input.

        :param tmp_path: Temporary directory for test artifacts.
        """
        target = tmp_path / "from_path"

        ensure_directory(target)

        assert isinstance(target, Path)
        assert target.is_dir()

    def test_existing_path_content_preserved(self, tmp_path: Path) -> None:
        """ensure_directory on existing directory does not remove its contents.

        :param tmp_path: Temporary directory for test artifacts.
        """
        target = tmp_path / "keep_content"
        target.mkdir()
        (target / "file.txt").write_text("data", encoding="utf-8")

        ensure_directory(target)

        assert (target / "file.txt").exists()
        assert (target / "file.txt").read_text(encoding="utf-8") == "data"

    @pytest.mark.parametrize(
        "dir_name",
        ["reports", "manifests", "cache", "logs", "nested/sub"],
    )
    def test_creates_common_project_directories(self, tmp_path: Path, dir_name: str) -> None:
        """ensure_directory creates common project directory names.

        :param tmp_path: Temporary directory for test artifacts.
        :param dir_name: Name of directory to create.
        """
        target = tmp_path / dir_name

        ensure_directory(target)

        assert target.is_dir()
