"""Tests for JSON report writer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.reporters.json_reporter import JsonReporter


def _make_media_item(
    path: str = "/library/movies/Avatar.mkv",
    relative_path: str = "Avatar.mkv",
    extension: str = ".mkv",
) -> MediaItem:
    """Build a MediaItem for test input.

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


def _make_parsed_item(
    title: str = "Avatar",
    normalized_title: str = "Avatar",
    media_type: str = "movie",
    year: int | None = 2009,
    season: int | None = None,
    episode: int | None = None,
    language: str | None = "EN",
    subtitle_language: str | None = None,
    confidence: float = 0.9,
    issues: list[str] | None = None,
) -> ParsedMediaItem:
    """Build a ParsedMediaItem for test input.

    :param title: Item title.
    :param normalized_title: Normalized title.
    :param media_type: Classification type.
    :param year: Release year for movies.
    :param season: Season number for TV.
    :param episode: Episode number for TV.
    :param language: Language code.
    :param subtitle_language: Subtitle language code.
    :param confidence: Confidence score.
    :param issues: List of parsing issues.
    :return: Constructed ParsedMediaItem.
    """
    return ParsedMediaItem(
        source=_make_media_item(),
        title=title,
        normalized_title=normalized_title,
        media_type=media_type,
        year=year,
        season=season,
        episode=episode,
        language=language,
        subtitle_language=subtitle_language,
        confidence=confidence,
        issues=issues or [],
    )


class TestJsonReporterWrite:
    """Tests for :meth:`JsonReporter.write`."""

    def test_write_creates_file(self, tmp_path: Path) -> None:
        """Write creates output file at specified path.

        :param tmp_path: Temporary directory for test artifacts.
        """
        output_path: Path = tmp_path / "report.json"
        items: list[ParsedMediaItem] = [_make_parsed_item()]
        reporter = JsonReporter()

        result_path: Path = reporter.write(items=items, output_path=output_path)

        assert result_path == output_path
        assert output_path.exists()
        assert output_path.is_file()

    def test_write_creates_parent_directories(self, tmp_path: Path) -> None:
        """Write creates nested parent directories if they don't exist.

        :param tmp_path: Temporary directory for test artifacts.
        """
        output_path: Path = tmp_path / "nested" / "deep" / "report.json"
        items: list[ParsedMediaItem] = [_make_parsed_item()]
        reporter = JsonReporter()

        result_path: Path = reporter.write(items=items, output_path=output_path)

        assert result_path.parent.exists()
        assert output_path.exists()

    def test_write_valid_json_structure(self, tmp_path: Path) -> None:
        """Write produces valid JSON with required structure.

        :param tmp_path: Temporary directory for test artifacts.
        """
        output_path: Path = tmp_path / "report.json"
        items: list[ParsedMediaItem] = [_make_parsed_item(title="Avatar", media_type="movie")]
        reporter = JsonReporter()

        reporter.write(items=items, output_path=output_path)

        content: Any = json.loads(output_path.read_text(encoding="utf-8"))

        assert "generated_at" in content
        assert "summary" in content
        assert "items" in content

    @pytest.mark.parametrize(
        ("media_type", "expected_key"),
        [
            ("movie", "movies"),
            ("tv_episode", "tv_episodes"),
            ("unknown", "unknown"),
        ],
    )
    def test_write_summary_counts(self, tmp_path: Path, media_type: str, expected_key: str) -> None:
        """Write calculates correct summary counts for each media type.

        :param tmp_path: Temporary directory for test artifacts.
        :param media_type: Media type to test.
        :param expected_key: Key in summary dict.
        """
        output_path: Path = tmp_path / "report.json"
        items: list[ParsedMediaItem] = [
            _make_parsed_item(title="Item1", media_type=media_type),
            _make_parsed_item(title="Item2", media_type=media_type),
        ]
        reporter = JsonReporter()

        reporter.write(items=items, output_path=output_path)

        content: Any = json.loads(output_path.read_text(encoding="utf-8"))
        assert content["summary"][expected_key] == 2
        assert content["summary"]["total_items"] == 2

    def test_write_mixed_media_types_summary(self, tmp_path: Path) -> None:
        """Write correctly counts mixed media types.

        :param tmp_path: Temporary directory for test artifacts.
        """
        output_path: Path = tmp_path / "report.json"
        items: list[ParsedMediaItem] = [
            _make_parsed_item(title="Avatar", media_type="movie"),
            _make_parsed_item(title="Breaking Bad", media_type="tv_episode", year=None),
            _make_parsed_item(title="Unknown File", media_type="unknown", year=None),
        ]
        reporter = JsonReporter()

        reporter.write(items=items, output_path=output_path)

        content: Any = json.loads(output_path.read_text(encoding="utf-8"))
        summary: dict[str, int] = content["summary"]

        assert summary["total_items"] == 3
        assert summary["movies"] == 1
        assert summary["tv_episodes"] == 1
        assert summary["unknown"] == 1

    def test_write_manual_review_count(self, tmp_path: Path) -> None:
        """Write counts items with issues as requiring manual review.

        :param tmp_path: Temporary directory for test artifacts.
        """
        output_path: Path = tmp_path / "report.json"
        items: list[ParsedMediaItem] = [
            _make_parsed_item(title="Good Movie", issues=[]),
            _make_parsed_item(title="Bad Movie", issues=["Title not detected"]),
            _make_parsed_item(
                title="Ambiguous",
                issues=["Could not determine year", "Title unclear"],
            ),
        ]
        reporter = JsonReporter()

        reporter.write(items=items, output_path=output_path)

        content: Any = json.loads(output_path.read_text(encoding="utf-8"))
        assert content["summary"]["manual_review"] == 2

    def test_write_empty_items_list(self, tmp_path: Path) -> None:
        """Write handles empty items list.

        :param tmp_path: Temporary directory for test artifacts.
        """
        output_path: Path = tmp_path / "report.json"
        reporter = JsonReporter()

        reporter.write(items=[], output_path=output_path)

        content: Any = json.loads(output_path.read_text(encoding="utf-8"))
        assert content["summary"]["total_items"] == 0
        assert content["summary"]["movies"] == 0
        assert content["summary"]["tv_episodes"] == 0
        assert content["summary"]["unknown"] == 0
        assert content["summary"]["manual_review"] == 0
        assert content["items"] == []

    def test_write_preserves_item_data(self, tmp_path: Path) -> None:
        """Write preserves all item data in output.

        :param tmp_path: Temporary directory for test artifacts.
        """
        output_path: Path = tmp_path / "report.json"
        parsed_item: ParsedMediaItem = _make_parsed_item(
            title="The Matrix",
            normalized_title="The Matrix",
            media_type="movie",
            year=1999,
            language="EN",
            subtitle_language="CZ",
            confidence=0.95,
            issues=["Some issue"],
        )
        reporter = JsonReporter()

        reporter.write(items=[parsed_item], output_path=output_path)

        content: Any = json.loads(output_path.read_text(encoding="utf-8"))
        item: dict[str, Any] = content["items"][0]

        assert item["title"] == "The Matrix"
        assert item["normalized_title"] == "The Matrix"
        assert item["media_type"] == "movie"
        assert item["year"] == 1999
        assert item["language"] == "EN"
        assert item["subtitle_language"] == "CZ"
        assert item["confidence"] == 0.95
        assert item["issues"] == ["Some issue"]

    def test_write_uses_utf8_encoding(self, tmp_path: Path) -> None:
        """Write outputs valid UTF-8 with non-ASCII characters.

        :param tmp_path: Temporary directory for test artifacts.
        """
        output_path: Path = tmp_path / "report.json"
        parsed_item: ParsedMediaItem = _make_parsed_item(
            title="Jméno filmu",
            normalized_title="Jméno filmu",
        )
        reporter = JsonReporter()

        reporter.write(items=[parsed_item], output_path=output_path)

        content: Any = json.loads(output_path.read_text(encoding="utf-8"))
        assert content["items"][0]["title"] == "Jméno filmu"

    def test_write_generated_at_timestamp(self, tmp_path: Path) -> None:
        """Write includes ISO format timestamp in generated_at field.

        :param tmp_path: Temporary directory for test artifacts.
        """
        output_path: Path = tmp_path / "report.json"
        reporter = JsonReporter()

        reporter.write(items=[], output_path=output_path)

        content: Any = json.loads(output_path.read_text(encoding="utf-8"))
        generated_at: str = content["generated_at"]

        # Verify it's a valid ISO format timestamp
        assert "T" in generated_at
        assert "+" in generated_at or "Z" in generated_at

    def test_write_returns_output_path(self, tmp_path: Path) -> None:
        """Write returns the output path that was provided.

        :param tmp_path: Temporary directory for test artifacts.
        """
        output_path: Path = tmp_path / "report.json"
        reporter = JsonReporter()

        result: Path = reporter.write(items=[], output_path=output_path)

        assert result is output_path
