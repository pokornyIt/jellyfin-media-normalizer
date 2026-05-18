"""Tests for review HTML reporter."""

from __future__ import annotations

from pathlib import Path

from jellyfin_media_normalizer.models.confidence_level import ConfidenceLevel
from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.validation_result import ValidationResult
from jellyfin_media_normalizer.models.validation_status import ValidationStatus
from jellyfin_media_normalizer.reporters.review_html_reporter import ReviewHtmlReporter


def _make_item(
    path: str,
    media_type: str = "movie",
    title: str = "Avatar",
    year: int | None = 2009,
    season: int | None = None,
    episode: int | None = None,
    confidence: float = 0.9,
    status: ValidationStatus = ValidationStatus.REVIEW_NEEDED,
    issues: list[str] | None = None,
    warnings: list[str] | None = None,
) -> ParsedMediaItem:
    """Create a parsed item for review HTML report tests.

    :param path: Relative source path.
    :param media_type: Parsed media type.
    :param title: Parsed title.
    :param year: Parsed year.
    :param season: Parsed season.
    :param episode: Parsed episode.
    :param confidence: Parser confidence score.
    :param status: Validation status value.
    :param issues: Validation issues.
    :param warnings: Validation warnings.
    :return: Parsed media item instance.
    """
    item = ParsedMediaItem(
        source=MediaItem(
            path=Path(f"/library/{path}"),
            relative_path=Path(path),
            extension=Path(path).suffix,
        ),
        media_type=media_type,
        title=title,
        normalized_title=title.lower(),
        year=year,
        season=season,
        episode=episode,
        confidence=confidence,
        validation_status=status,
    )
    item.validation_confidence = ConfidenceLevel.HIGH if confidence >= 0.85 else ConfidenceLevel.LOW
    item.validation_result = ValidationResult(
        is_valid=status != ValidationStatus.FAILED,
        status=status,
        confidence=item.validation_confidence,
        issues=issues or [],
        warnings=warnings or [],
    )
    return item


class TestReviewHtmlReporter:
    """Test review HTML reporter rendering and filtering behavior."""

    def test_write_creates_html_with_summary_and_rows(self, tmp_path: Path) -> None:
        """Write report with review summary cards and table rows.

        :param tmp_path: Temporary test directory.
        """
        reporter = ReviewHtmlReporter()
        output_path: Path = tmp_path / "parse-review-report.html"
        items: list[ParsedMediaItem] = [
            _make_item(
                path="Movies/Avatar.mkv",
                media_type="movie",
                title="Avatar",
                status=ValidationStatus.REVIEW_NEEDED,
                warnings=["No year certainty"],
            ),
            _make_item(
                path="Series/Show S01E03.mkv",
                media_type="tv_episode",
                title="Show",
                year=None,
                season=1,
                episode=3,
                status=ValidationStatus.FAILED,
                issues=["Missing title"],
            ),
        ]

        result_path: Path = reporter.write(items, output_path)
        content: str = output_path.read_text(encoding="utf-8")

        assert result_path == output_path
        assert output_path.exists()
        assert "Parse Review Report" in content
        assert "review_needed" in content
        assert "failed" in content
        assert "Avatar" in content
        assert "S1E3" in content
        assert "Missing title" in content

    def test_write_includes_only_review_and_failed_items(self, tmp_path: Path) -> None:
        """Include only review-needed and failed items in rendered output.

        :param tmp_path: Temporary test directory.
        """
        reporter = ReviewHtmlReporter()
        output_path: Path = tmp_path / "parse-review-report.html"
        items: list[ParsedMediaItem] = [
            _make_item(path="Movies/Include.mkv", title="Include", status=ValidationStatus.FAILED),
            _make_item(path="Movies/Pass.mkv", title="Pass", status=ValidationStatus.PASSED),
        ]

        reporter.write(items, output_path)
        content: str = output_path.read_text(encoding="utf-8")

        assert "Include" in content
        assert "Pass" not in content

    def test_write_escapes_html_in_values(self, tmp_path: Path) -> None:
        """Escape row values to avoid HTML injection in browser output.

        :param tmp_path: Temporary test directory.
        """
        reporter = ReviewHtmlReporter()
        output_path: Path = tmp_path / "parse-review-report.html"
        items: list[ParsedMediaItem] = [
            _make_item(
                path="Movies/Injected.mkv",
                title="<img src=x onerror=alert(1)>",
                issues=["<script>boom</script>"],
                status=ValidationStatus.FAILED,
            )
        ]

        reporter.write(items, output_path)
        content: str = output_path.read_text(encoding="utf-8")

        assert "<img src=x onerror=alert(1)>" not in content
        assert "&lt;img src=x onerror=alert(1)&gt;" in content
        assert "&lt;script&gt;boom&lt;/script&gt;" in content
