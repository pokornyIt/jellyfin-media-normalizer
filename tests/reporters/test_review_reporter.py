"""Tests for review reporter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from jellyfin_media_normalizer.models.confidence_level import ConfidenceLevel
from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.validation_result import ValidationResult
from jellyfin_media_normalizer.models.validation_status import ValidationStatus
from jellyfin_media_normalizer.reporters.review_reporter import ReviewReporter


def _make_item(
    path: str = "Movies/Avatar.mkv",
    media_type: str = "movie",
    title: str = "Avatar",
    normalized_title: str = "avatar",
    year: int | None = 2009,
    season: int | None = None,
    episode: int | None = None,
    confidence: float = 0.9,
    validation_status: ValidationStatus = ValidationStatus.PASSED,
    issues: list[str] | None = None,
    warnings: list[str] | None = None,
) -> ParsedMediaItem:
    """Create a ParsedMediaItem for testing.

    :param path: Relative path of the media file.
    :param media_type: Media type string.
    :param title: Item title.
    :param normalized_title: Normalized title.
    :param year: Year if a movie.
    :param season: Season number for TV episodes.
    :param episode: Episode number for TV episodes.
    :param confidence: Parser confidence score.
    :param validation_status: Validation status.
    :param issues: List of validation issues.
    :param warnings: List of validation warnings.
    :return: Constructed ParsedMediaItem.
    """
    item = ParsedMediaItem(
        source=MediaItem(
            path=Path(f"/library/{path}"),
            relative_path=Path(path),
            extension=Path(path).suffix,
        ),
        media_type=media_type,
        title=title,
        normalized_title=normalized_title,
        year=year,
        season=season,
        episode=episode,
        confidence=confidence,
        validation_status=validation_status,
    )
    item.validation_result = ValidationResult(
        is_valid=validation_status != ValidationStatus.FAILED,
        status=validation_status,
        confidence=ConfidenceLevel.HIGH
        if validation_status == ValidationStatus.PASSED
        else ConfidenceLevel.MEDIUM,
        issues=issues or [],
        warnings=warnings or [],
    )
    item.validation_confidence = ConfidenceLevel.HIGH if confidence >= 0.85 else ConfidenceLevel.LOW
    return item


class TestReviewReporter:
    """Test ReviewReporter."""

    @pytest.fixture
    def reporter(self) -> ReviewReporter:
        """Create a review reporter instance."""
        return ReviewReporter()

    def test_write_creates_file(self, reporter: ReviewReporter, tmp_path: Path) -> None:
        """Test that write creates a JSON file.

        :param reporter: ReviewReporter fixture.
        :param tmp_path: Temporary directory fixture.
        """
        items: list[ParsedMediaItem] = [
            _make_item(validation_status=ValidationStatus.REVIEW_NEEDED, warnings=["No year"])
        ]
        out: Path = tmp_path / "review.json"
        result: Path = reporter.write(items, out)
        assert result == out
        assert out.exists()

    def test_write_returns_path(self, reporter: ReviewReporter, tmp_path: Path) -> None:
        """Test that write returns the written path.

        :param reporter: ReviewReporter fixture.
        :param tmp_path: Temporary directory fixture.
        """
        out: Path = tmp_path / "review.json"
        result: Path = reporter.write([], out)
        assert result == out

    def test_write_valid_json(self, reporter: ReviewReporter, tmp_path: Path) -> None:
        """Test that the written file is valid JSON.

        :param reporter: ReviewReporter fixture.
        :param tmp_path: Temporary directory fixture.
        """
        items: list[ParsedMediaItem] = [
            _make_item(validation_status=ValidationStatus.REVIEW_NEEDED, warnings=["No year"])
        ]
        out: Path = tmp_path / "review.json"
        reporter.write(items, out)
        data: Any = json.loads(out.read_text(encoding="utf-8"))
        assert "summary" in data
        assert "items" in data
        assert "generated_at" in data

    def test_only_review_and_failed_items_included(
        self, reporter: ReviewReporter, tmp_path: Path
    ) -> None:
        """Test that only review_needed and failed items appear in the report.

        :param reporter: ReviewReporter fixture.
        :param tmp_path: Temporary directory fixture.
        """
        items: list[ParsedMediaItem] = [
            _make_item(title="Passed Movie", validation_status=ValidationStatus.PASSED),
            _make_item(
                title="Review Movie",
                validation_status=ValidationStatus.REVIEW_NEEDED,
                warnings=["No year"],
            ),
            _make_item(
                title="Failed Movie",
                validation_status=ValidationStatus.FAILED,
                issues=["Missing title"],
            ),
        ]
        out: Path = tmp_path / "review.json"
        reporter.write(items, out)
        data: Any = json.loads(out.read_text(encoding="utf-8"))
        assert len(data["items"]) == 2
        titles: set[Any] = {item["title"] for item in data["items"]}
        assert "Review Movie" in titles
        assert "Failed Movie" in titles
        assert "Passed Movie" not in titles

    def test_empty_input_writes_empty_report(
        self, reporter: ReviewReporter, tmp_path: Path
    ) -> None:
        """Test that empty input produces an empty items list.

        :param reporter: ReviewReporter fixture.
        :param tmp_path: Temporary directory fixture.
        """
        out: Path = tmp_path / "review.json"
        reporter.write([], out)
        data: Any = json.loads(out.read_text(encoding="utf-8"))
        assert data["items"] == []
        assert data["summary"]["review_needed"] == 0
        assert data["summary"]["failed"] == 0

    def test_summary_counts_correct(self, reporter: ReviewReporter, tmp_path: Path) -> None:
        """Test that summary counts match actual data.

        :param reporter: ReviewReporter fixture.
        :param tmp_path: Temporary directory fixture.
        """
        items: list[ParsedMediaItem] = [
            _make_item(validation_status=ValidationStatus.PASSED),
            _make_item(validation_status=ValidationStatus.PASSED),
            _make_item(
                validation_status=ValidationStatus.REVIEW_NEEDED,
                warnings=["No year"],
            ),
            _make_item(
                validation_status=ValidationStatus.FAILED,
                issues=["Missing title"],
            ),
        ]
        out: Path = tmp_path / "review.json"
        reporter.write(items, out)
        data: dict[str, Any] = json.loads(out.read_text(encoding="utf-8"))
        summary: dict[str, Any] = data["summary"]
        assert summary["total_items_scanned"] == 4
        assert summary["review_needed"] == 1
        assert summary["failed"] == 1

    def test_item_fields_present(self, reporter: ReviewReporter, tmp_path: Path) -> None:
        """Test that each report item contains expected fields.

        :param reporter: ReviewReporter fixture.
        :param tmp_path: Temporary directory fixture.
        """
        items: list[ParsedMediaItem] = [
            _make_item(
                path="Series/S01E01.mkv",
                media_type="tv_episode",
                title="Pilot",
                season=1,
                episode=1,
                validation_status=ValidationStatus.REVIEW_NEEDED,
                warnings=["No year"],
            )
        ]
        out: Path = tmp_path / "review.json"
        reporter.write(items, out)
        data: dict[str, Any] = json.loads(out.read_text(encoding="utf-8"))
        item: dict[str, Any] = data["items"][0]
        assert item["path"] == "Series/S01E01.mkv"
        assert item["media_type"] == "tv_episode"
        assert item["title"] == "Pilot"
        assert item["season"] == 1
        assert item["episode"] == 1
        assert item["validation_status"] == "review_needed"
        assert "warnings" in item
        assert "issues" in item

    def test_issues_and_warnings_included(self, reporter: ReviewReporter, tmp_path: Path) -> None:
        """Test that validation issues and warnings are included per item.

        :param reporter: ReviewReporter fixture.
        :param tmp_path: Temporary directory fixture.
        """
        items: list[ParsedMediaItem] = [
            _make_item(
                validation_status=ValidationStatus.FAILED,
                issues=["Missing title", "Invalid year"],
                warnings=["Low confidence"],
            )
        ]
        out: Path = tmp_path / "review.json"
        reporter.write(items, out)
        data: dict[str, Any] = json.loads(out.read_text(encoding="utf-8"))
        item: dict[str, Any] = data["items"][0]
        assert "Missing title" in item["issues"]
        assert "Invalid year" in item["issues"]
        assert "Low confidence" in item["warnings"]

    def test_creates_parent_directories(self, reporter: ReviewReporter, tmp_path: Path) -> None:
        """Test that write creates parent directories if they don't exist.

        :param reporter: ReviewReporter fixture.
        :param tmp_path: Temporary directory fixture.
        """
        out: Path = tmp_path / "nested" / "deep" / "review.json"
        reporter.write([], out)
        assert out.exists()

    def test_by_media_type_summary(self, reporter: ReviewReporter, tmp_path: Path) -> None:
        """Test that summary contains per-media-type breakdown.

        :param reporter: ReviewReporter fixture.
        :param tmp_path: Temporary directory fixture.
        """
        items: list[ParsedMediaItem] = [
            _make_item(
                media_type="movie",
                validation_status=ValidationStatus.REVIEW_NEEDED,
                warnings=["No year"],
            ),
            _make_item(
                media_type="unknown",
                title="Unclassified",
                normalized_title="unclassified",
                year=None,
                validation_status=ValidationStatus.REVIEW_NEEDED,
                warnings=["Cannot classify"],
            ),
        ]
        out: Path = tmp_path / "review.json"
        reporter.write(items, out)
        data: dict[str, Any] = json.loads(out.read_text(encoding="utf-8"))
        by_type: dict[str, int] = data["summary"]["by_media_type"]
        assert by_type["movie"] == 1
        assert by_type["unknown"] == 1
        assert by_type["tv_episode"] == 0
