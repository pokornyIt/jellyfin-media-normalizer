"""Tests for unresolved HTML reporter."""

from __future__ import annotations

from pathlib import Path

from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.provider_match import ProviderMatch
from jellyfin_media_normalizer.reporters.unresolved_html_reporter import UnresolvedHtmlReporter


def _make_item(
    path: str,
    media_type: str = "movie",
    title: str = "Avatar",
    year: int | None = 2009,
    season: int | None = None,
    episode: int | None = None,
    confidence: float = 0.9,
    issues: list[str] | None = None,
    provider_match: ProviderMatch | None = None,
) -> ParsedMediaItem:
    """Create a parsed item for unresolved HTML report tests.

    :param path: Relative path in library.
    :param media_type: Media type string.
    :param title: Parsed title.
    :param year: Movie year.
    :param season: TV season.
    :param episode: TV episode.
    :param confidence: Parser confidence score.
    :param issues: Validation issues list.
    :param provider_match: Provider match if resolved.
    :return: Parsed media item instance.
    """
    return ParsedMediaItem(
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
        issues=issues or [],
        provider_match=provider_match,
    )


class TestUnresolvedHtmlReporter:
    """Test unresolved HTML reporter output and filtering behavior."""

    def test_write_creates_html_with_summary_and_rows(self, tmp_path: Path) -> None:
        """Write report with summary cards and unresolved table rows.

        :param tmp_path: Temporary test directory.
        """
        reporter = UnresolvedHtmlReporter()
        output_path: Path = tmp_path / "unresolved-provider-report.html"
        items: list[ParsedMediaItem] = [
            _make_item(path="Movies/Avatar.mkv", media_type="movie", title="Avatar", year=2009),
            _make_item(
                path="Shows/Show S01E02.mkv",
                media_type="tv_episode",
                title="Show",
                year=None,
                season=1,
                episode=2,
                issues=["No provider hit"],
            ),
        ]

        written_path: Path = reporter.write(items, output_path)
        content: str = output_path.read_text(encoding="utf-8")

        assert written_path == output_path
        assert output_path.exists()
        assert "Unresolved Provider Report" in content
        assert "Generated at" in content
        assert ">2<" in content
        assert ">1<" in content
        assert "Avatar" in content
        assert "S1E2" in content
        assert "No provider hit" in content

    def test_write_excludes_unknown_and_resolved_items(self, tmp_path: Path) -> None:
        """Include only unresolved non-unknown items in HTML output.

        :param tmp_path: Temporary test directory.
        """
        reporter = UnresolvedHtmlReporter()
        output_path: Path = tmp_path / "unresolved-provider-report.html"

        resolved_match = ProviderMatch(
            provider="tmdb",
            provider_id="12345",
            confidence=0.95,
            reason="tmdb_search_exact",
            lookup_key="movie:avatar:2009",
        )
        items: list[ParsedMediaItem] = [
            _make_item(path="Movies/Included.mkv", title="Included"),
            _make_item(path="Movies/Resolved.mkv", title="Resolved", provider_match=resolved_match),
            _make_item(path="Other/Unknown.bin", media_type="unknown", title="Unknown"),
        ]

        reporter.write(items, output_path)
        content: str = output_path.read_text(encoding="utf-8")

        assert "Included" in content
        assert "Resolved" not in content
        assert "Unknown" not in content

    def test_write_escapes_html_in_item_values(self, tmp_path: Path) -> None:
        """Escape item data to avoid HTML injection in rendered output.

        :param tmp_path: Temporary test directory.
        """
        reporter = UnresolvedHtmlReporter()
        output_path: Path = tmp_path / "unresolved-provider-report.html"
        items: list[ParsedMediaItem] = [
            _make_item(
                path="Movies/Injected.mkv",
                title="<script>alert('x')</script>",
                issues=["<b>unsafe</b>"],
            )
        ]

        reporter.write(items, output_path)
        content: str = output_path.read_text(encoding="utf-8")

        assert "<script>alert('x')</script>" not in content
        assert "&lt;script&gt;alert(&#39;x&#39;)&lt;/script&gt;" in content
        assert "&lt;b&gt;unsafe&lt;/b&gt;" in content
