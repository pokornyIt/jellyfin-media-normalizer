"""Tests for consistency validator."""

from pathlib import Path

import pytest

from jellyfin_media_normalizer.models.confidence_level import ConfidenceLevel
from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.validation_result import ValidationResult
from jellyfin_media_normalizer.models.validation_status import ValidationStatus
from jellyfin_media_normalizer.validators.consistency_validator import ConsistencyValidator


class TestConsistencyValidator:
    """Test ConsistencyValidator."""

    @pytest.fixture
    def validator(self) -> ConsistencyValidator:
        """Create a consistency validator instance."""
        return ConsistencyValidator()

    @pytest.fixture
    def base_episode(self) -> ParsedMediaItem:
        """Create a base TV episode item."""
        return ParsedMediaItem(
            source=MediaItem(
                path=Path("/library/Series 01/S01E01.mkv"),
                relative_path=Path("Series 01/S01E01.mkv"),
                extension=".mkv",
            ),
            media_type="tv_episode",
            title="Pilot",
            normalized_title="series_name",
            season=1,
            episode=1,
            confidence=0.9,
        )

    def test_empty_series(self, validator: ConsistencyValidator) -> None:
        """Test validation of empty series list."""
        result: ValidationResult = validator.validate_series_episodes([])
        assert result.is_valid is True
        assert result.status == ValidationStatus.PASSED
        assert result.confidence == ConfidenceLevel.HIGH

    def test_consistent_series(
        self, validator: ConsistencyValidator, base_episode: ParsedMediaItem
    ) -> None:
        """Test validation of consistent series episodes."""
        ep1: ParsedMediaItem = base_episode
        ep2 = ParsedMediaItem(
            source=MediaItem(
                path=Path("/library/Series 01/S01E02.mkv"),
                relative_path=Path("Series 01/S01E02.mkv"),
                extension=".mkv",
            ),
            media_type="tv_episode",
            title="Episode 2",
            normalized_title="series_name",
            season=1,
            episode=2,
            confidence=0.9,
        )
        result: ValidationResult = validator.validate_series_episodes([ep1, ep2])
        assert result.is_valid is True
        assert result.status == ValidationStatus.PASSED

    def test_inconsistent_series_titles(
        self, validator: ConsistencyValidator, base_episode: ParsedMediaItem
    ) -> None:
        """Test validation with inconsistent series titles."""
        ep1: ParsedMediaItem = base_episode
        ep2 = ParsedMediaItem(
            source=MediaItem(
                path=Path("/library/Other Series 01/S01E02.mkv"),
                relative_path=Path("Other Series 01/S01E02.mkv"),
                extension=".mkv",
            ),
            media_type="tv_episode",
            title="Episode 2",
            normalized_title="other_series",
            season=1,
            episode=2,
            confidence=0.9,
        )
        result: ValidationResult = validator.validate_series_episodes([ep1, ep2])
        assert result.is_valid is False
        assert result.status == ValidationStatus.FAILED
        assert any("inconsistent" in i.lower() for i in result.issues)

    def test_duplicate_season_episode(
        self, validator: ConsistencyValidator, base_episode: ParsedMediaItem
    ) -> None:
        """Test validation with duplicate season/episode combination."""
        ep1: ParsedMediaItem = base_episode
        ep2 = ParsedMediaItem(
            source=MediaItem(
                path=Path("/library/Series 01/S01E01_alt.mkv"),
                relative_path=Path("Series 01/S01E01_alt.mkv"),
                extension=".mkv",
            ),
            media_type="tv_episode",
            title="Pilot Alt",
            normalized_title="series_name",
            season=1,
            episode=1,
            confidence=0.9,
        )
        result: ValidationResult = validator.validate_series_episodes([ep1, ep2])
        assert result.is_valid is True
        assert result.status == ValidationStatus.REVIEW_NEEDED
        assert any("duplicate" in w.lower() for w in result.warnings)

    def test_non_episode_in_series(
        self, validator: ConsistencyValidator, base_episode: ParsedMediaItem
    ) -> None:
        """Test validation with non-episode item in series."""
        ep1: ParsedMediaItem = base_episode
        movie = ParsedMediaItem(
            source=MediaItem(
                path=Path("/library/Series 01/Movie.mkv"),
                relative_path=Path("Series 01/Movie.mkv"),
                extension=".mkv",
            ),
            media_type="movie",
            title="Some Movie",
            normalized_title="some_movie",
            year=2020,
            confidence=0.9,
        )
        result: ValidationResult = validator.validate_series_episodes([ep1, movie])
        assert result.is_valid is False
        assert "non-TV-episode" in result.issues[0]

    def test_empty_movies(self, validator: ConsistencyValidator) -> None:
        """Test validation of empty movies list."""
        result: ValidationResult = validator.validate_movies_in_folder([])
        assert result.is_valid is True
        assert result.status == ValidationStatus.PASSED

    def test_single_movie(self, validator: ConsistencyValidator) -> None:
        """Test validation of single movie."""
        movie = ParsedMediaItem(
            source=MediaItem(
                path=Path("/library/Movies 01/Avatar.mkv"),
                relative_path=Path("Movies 01/Avatar.mkv"),
                extension=".mkv",
            ),
            media_type="movie",
            title="Avatar",
            normalized_title="avatar",
            year=2009,
            confidence=0.9,
        )
        result: ValidationResult = validator.validate_movies_in_folder([movie])
        assert result.is_valid is True
        assert result.status == ValidationStatus.PASSED

    def test_multiple_movies_in_folder(self, validator: ConsistencyValidator) -> None:
        """Test validation of multiple different movies in folder."""
        movie1 = ParsedMediaItem(
            source=MediaItem(
                path=Path("/library/Movies/Avatar.mkv"),
                relative_path=Path("Movies/Avatar.mkv"),
                extension=".mkv",
            ),
            media_type="movie",
            title="Avatar",
            normalized_title="avatar",
            year=2009,
            confidence=0.9,
        )
        movie2 = ParsedMediaItem(
            source=MediaItem(
                path=Path("/library/Movies/Matrix.mkv"),
                relative_path=Path("Movies/Matrix.mkv"),
                extension=".mkv",
            ),
            media_type="movie",
            title="Matrix",
            normalized_title="matrix",
            year=1999,
            confidence=0.9,
        )
        result: ValidationResult = validator.validate_movies_in_folder([movie1, movie2])
        assert result.is_valid is False
        assert "multiple" in result.issues[0].lower()

    def test_duplicate_movies(self, validator: ConsistencyValidator) -> None:
        """Test validation with duplicate movies."""
        movie1 = ParsedMediaItem(
            source=MediaItem(
                path=Path("/library/Movies/Avatar.mkv"),
                relative_path=Path("Movies/Avatar.mkv"),
                extension=".mkv",
            ),
            media_type="movie",
            title="Avatar",
            normalized_title="avatar",
            year=2009,
            confidence=0.9,
        )
        movie2 = ParsedMediaItem(
            source=MediaItem(
                path=Path("/library/Movies/Avatar_2.mkv"),
                relative_path=Path("Movies/Avatar_2.mkv"),
                extension=".mkv",
            ),
            media_type="movie",
            title="Avatar",
            normalized_title="avatar",
            year=2009,
            confidence=0.9,
        )
        result: ValidationResult = validator.validate_movies_in_folder([movie1, movie2])
        assert result.is_valid is True
        assert result.status == ValidationStatus.REVIEW_NEEDED
        assert any("duplicate" in w.lower() or "possible" in w.lower() for w in result.warnings)

    def test_non_movie_in_folder(self, validator: ConsistencyValidator) -> None:
        """Test validation with non-movie item in folder."""
        movie = ParsedMediaItem(
            source=MediaItem(
                path=Path("/library/Movies/Avatar.mkv"),
                relative_path=Path("Movies/Avatar.mkv"),
                extension=".mkv",
            ),
            media_type="movie",
            title="Avatar",
            normalized_title="avatar",
            year=2009,
            confidence=0.9,
        )
        episode = ParsedMediaItem(
            source=MediaItem(
                path=Path("/library/Movies/S01E01.mkv"),
                relative_path=Path("Movies/S01E01.mkv"),
                extension=".mkv",
            ),
            media_type="tv_episode",
            title="Episode",
            normalized_title="series",
            season=1,
            episode=1,
            confidence=0.9,
        )
        result: ValidationResult = validator.validate_movies_in_folder([movie, episode])
        assert result.is_valid is False
        assert "non-movie" in result.issues[0].lower()
