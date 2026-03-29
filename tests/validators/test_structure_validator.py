"""Tests for structure validator."""

from pathlib import Path

import pytest

from jellyfin_media_normalizer.models.confidence_level import ConfidenceLevel
from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.validation_result import ValidationResult
from jellyfin_media_normalizer.models.validation_status import ValidationStatus
from jellyfin_media_normalizer.validators.structure_validator import StructureValidator


class TestStructureValidator:
    """Test StructureValidator."""

    @pytest.fixture
    def validator(self) -> StructureValidator:
        """Create a validator instance."""
        return StructureValidator()

    @pytest.fixture
    def base_item(self) -> ParsedMediaItem:
        """Create a base valid parsed media item."""
        return ParsedMediaItem(
            source=MediaItem(
                path=Path("/library/Movie.mkv"),
                relative_path=Path("Movie.mkv"),
                extension=".mkv",
            ),
            media_type="movie",
            title="Avatar",
            normalized_title="avatar",
            year=2009,
            confidence=0.9,
        )

    def test_valid_movie(self, validator: StructureValidator, base_item: ParsedMediaItem) -> None:
        """Test validation of a valid movie."""
        result: ValidationResult = validator.validate(base_item)
        assert result.is_valid is True
        assert result.status == ValidationStatus.PASSED
        assert result.confidence == ConfidenceLevel.HIGH
        assert len(result.issues) == 0
        assert len(result.warnings) == 0

    def test_movie_without_year(
        self, validator: StructureValidator, base_item: ParsedMediaItem
    ) -> None:
        """Test validation of movie without year."""
        base_item.year = None
        result: ValidationResult = validator.validate(base_item)
        assert result.is_valid is True
        assert result.status == ValidationStatus.REVIEW_NEEDED
        assert result.confidence == ConfidenceLevel.MEDIUM
        assert len(result.warnings) == 1
        assert "no year" in result.warnings[0].lower()

    def test_movie_invalid_year(
        self, validator: StructureValidator, base_item: ParsedMediaItem
    ) -> None:
        """Test validation of movie with invalid year."""
        base_item.year = 5000
        result: ValidationResult = validator.validate(base_item)
        assert result.is_valid is False
        assert result.status == ValidationStatus.FAILED
        assert result.confidence == ConfidenceLevel.LOW
        assert len(result.issues) > 0
        assert any("year" in issue.lower() for issue in result.issues)

    def test_empty_title(self, validator: StructureValidator, base_item: ParsedMediaItem) -> None:
        """Test validation with empty title."""
        base_item.title = ""
        result: ValidationResult = validator.validate(base_item)
        assert result.is_valid is False
        assert result.status == ValidationStatus.FAILED
        assert "title" in result.issues[0].lower()

    def test_empty_normalized_title(
        self, validator: StructureValidator, base_item: ParsedMediaItem
    ) -> None:
        """Test validation with empty normalized title."""
        base_item.normalized_title = ""
        result: ValidationResult = validator.validate(base_item)
        assert result.is_valid is False
        assert result.status == ValidationStatus.FAILED

    def test_valid_tv_episode(
        self, validator: StructureValidator, base_item: ParsedMediaItem
    ) -> None:
        """Test validation of a valid TV episode."""
        base_item.media_type = "tv_episode"
        base_item.season = 1
        base_item.episode = 5
        result: ValidationResult = validator.validate(base_item)
        assert result.is_valid is True
        assert result.status == ValidationStatus.PASSED

    def test_tv_episode_missing_season(
        self, validator: StructureValidator, base_item: ParsedMediaItem
    ) -> None:
        """Test validation of TV episode without season."""
        base_item.media_type = "tv_episode"
        base_item.season = None
        base_item.episode = 5
        result: ValidationResult = validator.validate(base_item)
        assert result.is_valid is False
        assert "season" in result.issues[0].lower()

    def test_tv_episode_missing_episode(
        self, validator: StructureValidator, base_item: ParsedMediaItem
    ) -> None:
        """Test validation of TV episode without episode number."""
        base_item.media_type = "tv_episode"
        base_item.season = 1
        base_item.episode = None
        result: ValidationResult = validator.validate(base_item)
        assert result.is_valid is False
        assert "episode" in result.issues[0].lower()

    def test_invalid_season_negative(
        self, validator: StructureValidator, base_item: ParsedMediaItem
    ) -> None:
        """Test validation with negative season number."""
        base_item.media_type = "tv_episode"
        base_item.season = -1
        base_item.episode = 1
        result: ValidationResult = validator.validate(base_item)
        assert result.is_valid is False
        assert "season" in result.issues[0].lower()

    def test_invalid_episode_negative(
        self, validator: StructureValidator, base_item: ParsedMediaItem
    ) -> None:
        """Test validation with negative episode number."""
        base_item.media_type = "tv_episode"
        base_item.season = 1
        base_item.episode = -1
        result: ValidationResult = validator.validate(base_item)
        assert result.is_valid is False
        assert "episode" in result.issues[0].lower()

    def test_invalid_language_code_length(
        self, validator: StructureValidator, base_item: ParsedMediaItem
    ) -> None:
        """Test validation with invalid language code length."""
        base_item.language = "CZE"
        result: ValidationResult = validator.validate(base_item)
        assert result.is_valid is False
        assert "language" in result.issues[0].lower()

    def test_valid_language_code(
        self, validator: StructureValidator, base_item: ParsedMediaItem
    ) -> None:
        """Test validation with valid language code."""
        base_item.language = "CZ"
        result: ValidationResult = validator.validate(base_item)
        assert result.is_valid is True
        assert result.status == ValidationStatus.PASSED

    def test_unknown_media_type(
        self, validator: StructureValidator, base_item: ParsedMediaItem
    ) -> None:
        """Test validation of unknown media type marks item for review."""
        base_item.media_type = "unknown"
        result: ValidationResult = validator.validate(base_item)
        assert result.is_valid is True
        assert result.status == ValidationStatus.REVIEW_NEEDED
        assert any("classified" in w.lower() for w in result.warnings)
