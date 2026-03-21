"""Tests for the ScanResult dataclass."""

from __future__ import annotations

from pathlib import Path

import pytest

from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.media_type import MediaType
from jellyfin_media_normalizer.models.parsed_name import ParsedName
from jellyfin_media_normalizer.models.scan_result import ScanResult


def _make_media_item(
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


def _make_parsed_name(
    media_type: MediaType = MediaType.MOVIE,
    title: str | None = "Avatar",
    year: int | None = 2009,
    season: int | None = None,
    episode: int | None = None,
    language_code: str | None = "EN",
    confidence: float = 0.95,
) -> ParsedName:
    """Build a :class:`ParsedName` with the given fields.

    :param media_type: Detected media type.
    :param title: Parsed title.
    :param year: Parsed year.
    :param season: Season number.
    :param episode: Episode number.
    :param language_code: Audio language code.
    :param confidence: Confidence score.
    :return: Constructed ParsedName.
    """
    return ParsedName(
        media_type=media_type,
        raw_name="Avatar (2009) - EN.mkv",
        normalized_name="avatar 2009 en",
        title=title,
        year=year,
        season=season,
        episode=episode,
        language_code=language_code,
        has_czech_subtitles=False,
        confidence=confidence,
    )


class TestScanResultCreation:
    """Tests for construction of :class:`ScanResult`."""

    def test_fields_stored_correctly(self) -> None:
        """Both fields must be stored and accessible after construction."""
        item: MediaItem = _make_media_item()
        pn: ParsedName = _make_parsed_name()
        result = ScanResult(media_item=item, parsed_name=pn)

        assert result.media_item is item
        assert result.parsed_name is pn

    @pytest.mark.parametrize(
        ("media_type", "title", "year", "season", "episode"),
        [
            (MediaType.MOVIE, "Titanic", 1997, None, None),
            (MediaType.TV_EPISODE, "Breaking Bad", None, 3, 7),
            (MediaType.UNKNOWN, None, None, None, None),
        ],
    )
    def test_parsed_name_fields_accessible_via_result(
        self,
        media_type: MediaType,
        title: str | None,
        year: int | None,
        season: int | None,
        episode: int | None,
    ) -> None:
        """Fields from the nested ParsedName must be reachable through ScanResult.

        :param media_type: Media type used in ParsedName.
        :param title: Title used in ParsedName.
        :param year: Year used in ParsedName.
        :param season: Season number used in ParsedName.
        :param episode: Episode number used in ParsedName.
        """
        pn: ParsedName = _make_parsed_name(
            media_type=media_type,
            title=title,
            year=year,
            season=season,
            episode=episode,
        )
        result = ScanResult(media_item=_make_media_item(), parsed_name=pn)

        assert result.parsed_name.media_type is media_type
        assert result.parsed_name.title == title
        assert result.parsed_name.year == year
        assert result.parsed_name.season == season
        assert result.parsed_name.episode == episode

    @pytest.mark.parametrize(
        ("path", "relative_path", "extension"),
        [
            (
                "/library/movies/Avatar (2009)/Avatar (2009).mkv",
                "movies/Avatar (2009)/Avatar (2009).mkv",
                ".mkv",
            ),
            (
                "/library/series/Dark/Season 01/S01E01.mp4",
                "series/Dark/Season 01/S01E01.mp4",
                ".mp4",
            ),
        ],
    )
    def test_media_item_fields_accessible_via_result(
        self,
        path: str,
        relative_path: str,
        extension: str,
    ) -> None:
        """Fields from the nested MediaItem must be reachable through ScanResult.

        :param path: Absolute path string.
        :param relative_path: Relative path string.
        :param extension: File extension string.
        """
        item: MediaItem = _make_media_item(
            path=path, relative_path=relative_path, extension=extension
        )
        result = ScanResult(media_item=item, parsed_name=_make_parsed_name())

        assert result.media_item.path == Path(path)
        assert result.media_item.relative_path == Path(relative_path)
        assert result.media_item.extension == extension


class TestScanResultEquality:
    """Tests for equality semantics of :class:`ScanResult`."""

    def test_equal_results_compare_equal(self) -> None:
        """Two ScanResult instances with identical contents must be equal."""
        item: MediaItem = _make_media_item()
        pn: ParsedName = _make_parsed_name()
        assert ScanResult(media_item=item, parsed_name=pn) == ScanResult(
            media_item=item, parsed_name=pn
        )

    def test_different_media_item_breaks_equality(self) -> None:
        """ScanResult instances with different MediaItems must not be equal."""
        pn: ParsedName = _make_parsed_name()
        a = ScanResult(media_item=_make_media_item(extension=".mkv"), parsed_name=pn)
        b = ScanResult(media_item=_make_media_item(extension=".mp4"), parsed_name=pn)
        assert a != b
