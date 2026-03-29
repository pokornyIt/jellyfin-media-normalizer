"""Tests for the MediaItem dataclass."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from jellyfin_media_normalizer.models.media_item import MediaItem


def _make_item(
    path: str = "/library/movies/Avatar (2009)/Avatar (2009).mkv",
    relative_path: str = "movies/Avatar (2009)/Avatar (2009).mkv",
    extension: str = ".mkv",
) -> MediaItem:
    """Build a :class:`MediaItem` from string arguments.

    :param path: Absolute path string.
    :param relative_path: Relative path string.
    :param extension: File extension string.
    :return: Constructed MediaItem.
    """
    return MediaItem(
        path=Path(path),
        relative_path=Path(relative_path),
        extension=extension,
    )


class TestMediaItemCreation:
    """Tests for basic construction of :class:`MediaItem`."""

    @pytest.mark.parametrize(
        ("path", "relative_path", "extension"),
        [
            (
                "/library/movies/Avatar (2009)/Avatar (2009).mkv",
                "movies/Avatar (2009)/Avatar (2009).mkv",
                ".mkv",
            ),
            (
                "/library/series/Breaking Bad/Season 01/S01E01.mp4",
                "series/Breaking Bad/Season 01/S01E01.mp4",
                ".mp4",
            ),
            (
                "/library/movies/Titanic (1997)/Titanic.avi",
                "movies/Titanic (1997)/Titanic.avi",
                ".avi",
            ),
        ],
    )
    def test_fields_stored_correctly(
        self,
        path: str,
        relative_path: str,
        extension: str,
    ) -> None:
        """All fields must be stored exactly as provided.

        :param path: Absolute path string.
        :param relative_path: Relative path string.
        :param extension: File extension string.
        """
        item = MediaItem(
            path=Path(path),
            relative_path=Path(relative_path),
            extension=extension,
        )
        assert item.path == Path(path)
        assert item.relative_path == Path(relative_path)
        assert item.extension == extension

    def test_path_is_path_instance(self) -> None:
        """The ``path`` field must be a :class:`~pathlib.Path` instance."""
        item: MediaItem = _make_item()
        assert isinstance(item.path, Path)

    def test_relative_path_is_path_instance(self) -> None:
        """The ``relative_path`` field must be a :class:`~pathlib.Path` instance."""
        item: MediaItem = _make_item()
        assert isinstance(item.relative_path, Path)

    @pytest.mark.parametrize(
        "extension",
        [".mkv", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".m4v"],
    )
    def test_various_extensions_stored(self, extension: str) -> None:
        """Extension field accepts any string value without modification.

        :param extension: File extension to store.
        """
        item: MediaItem = _make_item(extension=extension)
        assert item.extension == extension


class TestMediaItemEquality:
    """Tests for equality semantics of :class:`MediaItem`."""

    def test_equal_items_compare_equal(self) -> None:
        """Two items with identical fields must be equal."""
        a: MediaItem = _make_item()
        b: MediaItem = _make_item()
        assert a == b

    @pytest.mark.parametrize(
        ("field", "differing_value"),
        [
            ("path", Path("/library/other/file.mkv")),
            ("relative_path", Path("other/file.mkv")),
            ("extension", ".mp4"),
        ],
    )
    def test_differing_field_breaks_equality(
        self,
        field: str,
        differing_value: object,
    ) -> None:
        """Items that differ in any field must not be equal.

        :param field: Name of the field to change.
        :param differing_value: Replacement value for that field.
        """
        base: MediaItem = _make_item()
        kwargs: dict[str, Any] = {
            "path": base.path,
            "relative_path": base.relative_path,
            "extension": base.extension,
        }
        kwargs[field] = differing_value  # type: ignore[assignment]
        other: MediaItem = MediaItem(**kwargs)  # type: ignore[arg-type]
        assert base != other
