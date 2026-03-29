"""Tests for media filename classification."""

from __future__ import annotations

import pytest

from jellyfin_media_normalizer.models.media_type import MediaType
from jellyfin_media_normalizer.parsers.classifier import Classifier


class TestClassifier:
    """Tests for :class:`Classifier`."""

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("Breaking Bad S01E01", MediaType.TV_EPISODE),
            ("breaking.bad.s01e02.1080p", MediaType.TV_EPISODE),
            ("Dark - s03e08 - DE", MediaType.TV_EPISODE),
            ("Beze-stopy-03x02-Nezabijes", MediaType.TV_EPISODE),
            ("Series-01x01-Episode-title", MediaType.TV_EPISODE),
            ("Some-Show-12x15-ep", MediaType.TV_EPISODE),
            ("Movie Title 1999", MediaType.MOVIE),
            ("Avatar 2009 EN", MediaType.MOVIE),
            ("Some Documentary 2100", MediaType.MOVIE),
            ("Readme file", MediaType.UNKNOWN),
            ("Random_name_without_markers", MediaType.UNKNOWN),
        ],
    )
    def test_classify(self, name: str, expected: MediaType) -> None:
        """Classify normalized names by TV/year/unknown patterns.

        :param name: Normalized name string.
        :param expected: Expected media type.
        """
        classifier = Classifier()
        assert classifier.classify(name) is expected

    @pytest.mark.parametrize(
        "name",
        [
            "Show S01E01 2001",
            "Mini.Series.s02e03.2012",
        ],
    )
    def test_tv_pattern_has_priority_over_year(self, name: str) -> None:
        """Prefer TV classification when TV and year markers are both present.

        :param name: Name containing both TV and year patterns.
        """
        classifier = Classifier()
        assert classifier.classify(name) is MediaType.TV_EPISODE

    @pytest.mark.parametrize(
        "name",
        [
            "Beze-stopy-03x02-Nezabijes",
            "Some-Series-01x05-Episode",
        ],
    )
    def test_hyphen_format_classified_as_tv(self, name: str) -> None:
        """Classify hyphen-separated NNxNN format as TV episode.

        :param name: Name containing hyphen-format season/episode marker.
        """
        classifier = Classifier()
        assert classifier.classify(name) is MediaType.TV_EPISODE

    @pytest.mark.parametrize(
        "name",
        [
            "Beze-stopy-03x02-Nezabijes 2005",
            "Series-01x01-Episode 2000",
        ],
    )
    def test_hyphen_tv_has_priority_over_year(self, name: str) -> None:
        """Prefer hyphen TV classification over year-based movie classification.

        :param name: Name containing both NNxNN and year markers.
        """
        classifier = Classifier()
        assert classifier.classify(name) is MediaType.TV_EPISODE
