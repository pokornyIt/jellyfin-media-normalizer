"""Tests for the ParsedMediaItem dataclass."""

from __future__ import annotations

from pathlib import Path

import pytest

from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem


def _make_source(
    path: str = "/library/movies/Avatar (2009)/Avatar (2009).mkv",
    relative_path: str = "movies/Avatar (2009)/Avatar (2009).mkv",
    extension: str = ".mkv",
) -> MediaItem:
    """Build a :class:`MediaItem` for use as a ParsedMediaItem source.

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


def _make_parsed(
    source: MediaItem | None = None,
    media_type: str = "movie",
    title: str = "Avatar",
    normalized_title: str = "avatar",
    year: int | None = 2009,
    season: int | None = None,
    episode: int | None = None,
    language: str | None = "EN",
    subtitle_language: str | None = None,
    confidence: float = 0.95,
    issues: list[str] | None = None,
) -> ParsedMediaItem:
    """Build a :class:`ParsedMediaItem` with sensible defaults.

    :param source: Source MediaItem; a default is created when None.
    :param media_type: Classified media type string.
    :param title: Extracted title.
    :param normalized_title: Normalized title.
    :param year: Release year for movies.
    :param season: Season number for TV episodes.
    :param episode: Episode number for TV episodes.
    :param language: Audio language code.
    :param subtitle_language: Subtitle language code.
    :param confidence: Parser confidence score.
    :param issues: List of issue messages; defaults to empty list.
    :return: Constructed ParsedMediaItem.
    """
    return ParsedMediaItem(
        source=source if source is not None else _make_source(),
        media_type=media_type,
        title=title,
        normalized_title=normalized_title,
        year=year,
        season=season,
        episode=episode,
        language=language,
        subtitle_language=subtitle_language,
        confidence=confidence,
        issues=issues if issues is not None else [],
    )


class TestParsedMediaItemDefaults:
    """Tests for default values of :class:`ParsedMediaItem`."""

    def test_optional_fields_default_to_none(self) -> None:
        """Optional fields not passed explicitly must default to None."""
        item = ParsedMediaItem(
            source=_make_source(),
            media_type="unknown",
            title="Unknown",
            normalized_title="unknown",
        )
        assert item.year is None
        assert item.season is None
        assert item.episode is None
        assert item.language is None
        assert item.subtitle_language is None

    def test_confidence_defaults_to_zero(self) -> None:
        """Confidence must default to 0.0 when not provided."""
        item = ParsedMediaItem(
            source=_make_source(),
            media_type="unknown",
            title="Unknown",
            normalized_title="unknown",
        )
        assert item.confidence == pytest.approx(0.0)

    def test_issues_defaults_to_empty_list(self) -> None:
        """Issues list must default to an empty list when not provided."""
        item = ParsedMediaItem(
            source=_make_source(),
            media_type="unknown",
            title="Unknown",
            normalized_title="unknown",
        )
        assert item.issues == []

    def test_issues_default_is_not_shared_between_instances(self) -> None:
        """Each instance must have its own independent issues list."""
        a = ParsedMediaItem(
            source=_make_source(),
            media_type="unknown",
            title="A",
            normalized_title="a",
        )
        b = ParsedMediaItem(
            source=_make_source(),
            media_type="unknown",
            title="B",
            normalized_title="b",
        )
        a.issues.append("some issue")
        assert b.issues == []


class TestParsedMediaItemFieldStorage:
    """Tests for correct field storage in :class:`ParsedMediaItem`."""

    @pytest.mark.parametrize(
        ("media_type", "title", "year", "season", "episode"),
        [
            ("movie", "Avatar", 2009, None, None),
            ("tv_episode", "Breaking Bad", None, 3, 7),
            ("unknown", "?", None, None, None),
            ("movie", "Avengers: Endgame", 2019, None, None),
            ("tv_episode", "Dark", None, 2, 1),
        ],
    )
    def test_core_fields_stored_correctly(
        self,
        media_type: str,
        title: str,
        year: int | None,
        season: int | None,
        episode: int | None,
    ) -> None:
        """Core classification fields must be stored exactly as provided.

        :param media_type: Classified media type string.
        :param title: Extracted title.
        :param year: Release year or None.
        :param season: Season number or None.
        :param episode: Episode number or None.
        """
        item: ParsedMediaItem = _make_parsed(
            media_type=media_type,
            title=title,
            year=year,
            season=season,
            episode=episode,
        )
        assert item.media_type == media_type
        assert item.title == title
        assert item.year == year
        assert item.season == season
        assert item.episode == episode

    @pytest.mark.parametrize(
        ("language", "subtitle_language"),
        [
            ("EN", None),
            ("CZ", "EN"),
            (None, None),
            ("DE", "CZ"),
        ],
    )
    def test_language_fields_stored_correctly(
        self,
        language: str | None,
        subtitle_language: str | None,
    ) -> None:
        """Language fields must reflect the values that were provided.

        :param language: Audio language code or None.
        :param subtitle_language: Subtitle language code or None.
        """
        item: ParsedMediaItem = _make_parsed(language=language, subtitle_language=subtitle_language)
        assert item.language == language
        assert item.subtitle_language == subtitle_language

    @pytest.mark.parametrize(
        "confidence",
        [0.0, 0.25, 0.5, 0.75, 1.0],
    )
    def test_confidence_stored_as_float(self, confidence: float) -> None:
        """Confidence value must be stored as-is.

        :param confidence: Confidence score to store.
        """
        item: ParsedMediaItem = _make_parsed(confidence=confidence)
        assert item.confidence == pytest.approx(confidence)

    @pytest.mark.parametrize(
        "issues",
        [
            [],
            ["missing year"],
            ["ambiguous title", "low confidence"],
        ],
    )
    def test_issues_stored_correctly(self, issues: list[str]) -> None:
        """Issues list must be preserved as provided.

        :param issues: List of issue strings to store.
        """
        item: ParsedMediaItem = _make_parsed(issues=issues)
        assert item.issues == issues


class TestParsedMediaItemToDict:
    """Tests for the :meth:`ParsedMediaItem.to_dict` method."""

    def test_returns_dict(self) -> None:
        """to_dict must return a dict instance."""
        assert isinstance(_make_parsed().to_dict(), dict)

    def test_source_path_is_string(self) -> None:
        """The ``source.path`` value in the dict must be a string, not a Path."""
        result: dict[str, object] = _make_parsed().to_dict()
        source: object = result["source"]
        assert isinstance(source, dict)
        assert isinstance(source["path"], str)

    def test_source_relative_path_is_string(self) -> None:
        """The ``source.relative_path`` value in the dict must be a string."""
        result: dict[str, object] = _make_parsed().to_dict()
        source: object = result["source"]
        assert isinstance(source, dict)
        assert isinstance(source["relative_path"], str)

    @pytest.mark.parametrize(
        "key",
        [
            "source",
            "media_type",
            "title",
            "normalized_title",
            "year",
            "season",
            "episode",
            "language",
            "subtitle_language",
            "confidence",
            "issues",
        ],
    )
    def test_all_fields_present_in_dict(self, key: str) -> None:
        """Every model field must appear as a key in the serialized dict.

        :param key: Expected key name in the serialized output.
        """
        result: dict[str, object] = _make_parsed().to_dict()
        assert key in result

    def test_path_values_match_original(self) -> None:
        """String paths in the dict must match the original Path objects."""
        source: MediaItem = _make_source(
            path="/library/movies/Avatar (2009)/Avatar (2009).mkv",
            relative_path="movies/Avatar (2009)/Avatar (2009).mkv",
        )
        item: ParsedMediaItem = _make_parsed(source=source)
        result: dict[str, object] = item.to_dict()

        assert result["source"]["path"] == str(source.path)  # pyright: ignore[reportIndexIssue]
        assert result["source"]["relative_path"] == str(source.relative_path)  # pyright: ignore[reportIndexIssue]

    @pytest.mark.parametrize(
        ("year", "season", "episode"),
        [
            (2009, None, None),
            (None, 1, 1),
            (None, None, None),
        ],
    )
    def test_optional_fields_in_dict_reflect_values(
        self,
        year: int | None,
        season: int | None,
        episode: int | None,
    ) -> None:
        """Optional numeric fields must appear verbatim in the serialized dict.

        :param year: Year value to use.
        :param season: Season value to use.
        :param episode: Episode value to use.
        """
        item = _make_parsed(year=year, season=season, episode=episode)
        result = item.to_dict()

        assert result["year"] == year
        assert result["season"] == season
        assert result["episode"] == episode

    def test_issues_list_serialized_correctly(self) -> None:
        """The issues list must appear as a list of strings in the dict."""
        issues = ["low confidence", "ambiguous title"]
        item = _make_parsed(issues=issues)
        result = item.to_dict()

        assert result["issues"] == issues
