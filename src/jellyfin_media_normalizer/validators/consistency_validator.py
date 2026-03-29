"""Consistency validation across grouped media items."""

from __future__ import annotations

from jellyfin_media_normalizer.models.confidence_level import ConfidenceLevel
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.validation_result import ValidationResult
from jellyfin_media_normalizer.models.validation_status import ValidationStatus


class ConsistencyValidator:
    """Validate consistency within grouped items (e.g., episodes in a series)."""

    def validate_series_episodes(
        self,
        episodes: list[ParsedMediaItem],
    ) -> ValidationResult:
        """Validate consistency of TV episodes within a series.

        :param episodes: List of ParsedMediaItem objects representing episodes.
        :return: Validation result.
        """
        issues: list[str] = []
        warnings: list[str] = []

        if not episodes:
            return ValidationResult(
                is_valid=True,
                status=ValidationStatus.PASSED,
                confidence=ConfidenceLevel.HIGH,
                issues=[],
                warnings=[],
            )

        # Check that all episodes are TV episodes
        non_episodes: list[ParsedMediaItem] = [e for e in episodes if e.media_type != "tv_episode"]
        if non_episodes:
            issues.append(f"Found {len(non_episodes)} non-TV-episode items in series group")

        # Check for consistent series title
        series_titles: set[str] = {e.normalized_title for e in episodes}
        if len(series_titles) > 1:
            issues.append(f"Inconsistent series titles found: {', '.join(series_titles)}")
        elif len(series_titles) == 0:
            issues.append("No series title could be determined")

        # Check for duplicate season/episode combinations
        seen_se_pairs: set[tuple[int, int]] = set()
        duplicates: list[tuple[int, int]] = []
        for ep in episodes:
            if ep.season is not None and ep.episode is not None:
                se_pair: tuple[int, int] = (ep.season, ep.episode)
                if se_pair in seen_se_pairs:
                    duplicates.append(se_pair)
                else:
                    seen_se_pairs.add(se_pair)

        if duplicates:
            warnings.append(f"Found duplicate season/episode combinations: {duplicates}")

        # Check for gaps in season/episode numbering (warning only)
        episodes_by_season: dict[int, list[int]] = {}
        for ep in episodes:
            if ep.season is not None and ep.episode is not None:
                if ep.season not in episodes_by_season:
                    episodes_by_season[ep.season] = []
                episodes_by_season[ep.season].append(ep.episode)

        # Determine validation status
        status: ValidationStatus
        confidence: ConfidenceLevel
        is_valid: bool
        if issues:
            status = ValidationStatus.FAILED
            confidence = ConfidenceLevel.LOW
            is_valid = False
        elif warnings or len(series_titles) > 1:
            status = ValidationStatus.REVIEW_NEEDED
            confidence = ConfidenceLevel.MEDIUM
            is_valid = True
        else:
            status = ValidationStatus.PASSED
            confidence = ConfidenceLevel.HIGH
            is_valid = True

        return ValidationResult(
            is_valid=is_valid,
            status=status,
            confidence=confidence,
            issues=issues,
            warnings=warnings,
        )

    def validate_movies_in_folder(
        self,
        movies: list[ParsedMediaItem],
    ) -> ValidationResult:
        """Validate consistency of movies in a folder.

        :param movies: List of ParsedMediaItem objects representing movies.
        :return: Validation result.
        """
        issues: list[str] = []
        warnings: list[str] = []

        if not movies:
            return ValidationResult(
                is_valid=True,
                status=ValidationStatus.PASSED,
                confidence=ConfidenceLevel.HIGH,
                issues=[],
                warnings=[],
            )

        # Check that all items are movies
        non_movies: list[ParsedMediaItem] = [m for m in movies if m.media_type != "movie"]
        if non_movies:
            issues.append(f"Found {len(non_movies)} non-movie items in movies folder")

        # Check that folder doesn't contain multiple different movies
        movie_titles: set[str] = {m.normalized_title for m in movies}
        if len(movie_titles) > 1:
            issues.append(f"Folder contains multiple different movies: {', '.join(movie_titles)}")

        # Check for duplicate movies (same title and year)
        seen_movies: set[tuple[str, int | None]] = set()
        duplicates: list[str] = []
        for movie in movies:
            movie_key: tuple[str, int | None] = (movie.normalized_title, movie.year)
            if movie_key in seen_movies:
                duplicates.append(f"{movie.title} ({movie.year})")
            else:
                seen_movies.add(movie_key)

        if duplicates:
            warnings.append(f"Found possible duplicates: {', '.join(duplicates)}")

        # Determine validation status
        status: ValidationStatus
        confidence: ConfidenceLevel
        is_valid: bool
        if issues:
            status = ValidationStatus.FAILED
            confidence = ConfidenceLevel.LOW
            is_valid = False
        elif warnings:
            status = ValidationStatus.REVIEW_NEEDED
            confidence = ConfidenceLevel.MEDIUM
            is_valid = True
        else:
            status = ValidationStatus.PASSED
            confidence = ConfidenceLevel.HIGH
            is_valid = True

        return ValidationResult(
            is_valid=is_valid,
            status=status,
            confidence=confidence,
            issues=issues,
            warnings=warnings,
        )
