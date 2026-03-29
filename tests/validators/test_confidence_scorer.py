"""Tests for confidence scorer."""

from pathlib import Path

import pytest

from jellyfin_media_normalizer.models.confidence_level import ConfidenceLevel
from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.validators.confidence_scorer import ConfidenceScorer


class TestConfidenceScorer:
    """Test ConfidenceScorer."""

    @pytest.fixture
    def scorer(self) -> ConfidenceScorer:
        """Create a confidence scorer instance."""
        return ConfidenceScorer()

    @pytest.fixture
    def base_item(self) -> ParsedMediaItem:
        """Create a base parsed media item."""
        return ParsedMediaItem(
            source=MediaItem(
                path=Path("/library/Avatar (2009).mkv"),
                relative_path=Path("Avatar (2009).mkv"),
                extension=".mkv",
            ),
            media_type="movie",
            title="Avatar",
            normalized_title="Avatar",
            year=2009,
            confidence=0.95,
        )

    def test_high_confidence_movie_complete(
        self, scorer: ConfidenceScorer, base_item: ParsedMediaItem
    ) -> None:
        """Test high confidence for complete movie."""
        result: ConfidenceLevel = scorer.score(base_item)
        assert result == ConfidenceLevel.HIGH

    def test_high_confidence_movie_with_language(
        self, scorer: ConfidenceScorer, base_item: ParsedMediaItem
    ) -> None:
        """Test high confidence for movie with language code."""
        base_item.language = "CZ"
        result: ConfidenceLevel = scorer.score(base_item)
        assert result == ConfidenceLevel.HIGH

    def test_medium_confidence_movie_without_year(
        self, scorer: ConfidenceScorer, base_item: ParsedMediaItem
    ) -> None:
        """Test medium confidence for movie without year."""
        base_item.year = None
        base_item.language = "CZ"
        base_item.confidence = 0.90
        result: ConfidenceLevel = scorer.score(base_item)
        assert result == ConfidenceLevel.MEDIUM

    def test_medium_confidence_movie_without_language(
        self, scorer: ConfidenceScorer, base_item: ParsedMediaItem
    ) -> None:
        """Test medium confidence for movie without language."""
        base_item.language = None
        base_item.confidence = 0.85
        result: ConfidenceLevel = scorer.score(base_item)
        assert result == ConfidenceLevel.MEDIUM

    def test_low_confidence_with_issues(
        self, scorer: ConfidenceScorer, base_item: ParsedMediaItem
    ) -> None:
        """Test low confidence when issues are present."""
        base_item.issues = ["Missing audio track", "Invalid encoding"]
        base_item.confidence = 0.95
        result: ConfidenceLevel = scorer.score(base_item)
        assert result == ConfidenceLevel.LOW

    def test_low_confidence_tv_episode_without_season(
        self, scorer: ConfidenceScorer, base_item: ParsedMediaItem
    ) -> None:
        """Test low confidence for TV episode without season."""
        base_item.media_type = "tv_episode"
        base_item.season = None
        base_item.episode = 5
        base_item.confidence = 0.9
        result: ConfidenceLevel = scorer.score(base_item)
        assert result == ConfidenceLevel.LOW

    def test_low_confidence_tv_episode_without_episode(
        self, scorer: ConfidenceScorer, base_item: ParsedMediaItem
    ) -> None:
        """Test low confidence for TV episode without episode number."""
        base_item.media_type = "tv_episode"
        base_item.season = 1
        base_item.episode = None
        base_item.confidence = 0.9
        result: ConfidenceLevel = scorer.score(base_item)
        assert result == ConfidenceLevel.LOW

    def test_medium_confidence_tv_episode_complete(
        self, scorer: ConfidenceScorer, base_item: ParsedMediaItem
    ) -> None:
        """Test confidence for complete TV episode."""
        base_item.media_type = "tv_episode"
        base_item.season = 1
        base_item.episode = 5
        base_item.confidence = 0.80
        result: ConfidenceLevel = scorer.score(base_item)
        assert result == ConfidenceLevel.MEDIUM

    def test_high_confidence_tv_episode_with_title(
        self, scorer: ConfidenceScorer, base_item: ParsedMediaItem
    ) -> None:
        """Test high confidence for TV episode with all data."""
        base_item.media_type = "tv_episode"
        base_item.season = 1
        base_item.episode = 5
        base_item.title = "Episode Title"
        base_item.confidence = 0.95
        result: ConfidenceLevel = scorer.score(base_item)
        assert result == ConfidenceLevel.HIGH

    def test_low_confidence_very_low_parser_score(
        self, scorer: ConfidenceScorer, base_item: ParsedMediaItem
    ) -> None:
        """Test low confidence when parser score is very low."""
        base_item.confidence = 0.5
        result: ConfidenceLevel = scorer.score(base_item)
        assert result == ConfidenceLevel.LOW

    def test_boundary_high_threshold(
        self, scorer: ConfidenceScorer, base_item: ParsedMediaItem
    ) -> None:
        """Test boundary at high confidence threshold."""
        base_item.language = "CZ"
        base_item.confidence = scorer.HIGH_THRESHOLD + 0.01
        result: ConfidenceLevel = scorer.score(base_item)
        assert result == ConfidenceLevel.HIGH

    def test_boundary_below_high_threshold(
        self, scorer: ConfidenceScorer, base_item: ParsedMediaItem
    ) -> None:
        """Test just below high confidence threshold."""
        base_item.confidence = scorer.HIGH_THRESHOLD - 0.01
        result: ConfidenceLevel = scorer.score(base_item)
        assert result == ConfidenceLevel.MEDIUM

    def test_boundary_medium_threshold(
        self, scorer: ConfidenceScorer, base_item: ParsedMediaItem
    ) -> None:
        """Test boundary at medium confidence threshold."""
        base_item.language = "CZ"
        base_item.confidence = scorer.MEDIUM_THRESHOLD + 0.01
        result: ConfidenceLevel = scorer.score(base_item)
        assert result == ConfidenceLevel.MEDIUM

    def test_boundary_below_medium_threshold(
        self, scorer: ConfidenceScorer, base_item: ParsedMediaItem
    ) -> None:
        """Test just below medium confidence threshold."""
        base_item.confidence = scorer.MEDIUM_THRESHOLD - 0.01
        result: ConfidenceLevel = scorer.score(base_item)
        assert result == ConfidenceLevel.LOW
