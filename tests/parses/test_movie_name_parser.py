"""Tests for movie filename parser."""

from __future__ import annotations

import pytest

from jellyfin_media_normalizer.models.media_type import MediaType
from jellyfin_media_normalizer.models.parsed_name import ParsedName
from jellyfin_media_normalizer.parsers.movie_name_parser import MovieNameParser


class TestMovieNameParser:
    """Tests for :class:`MovieNameParser`."""

    @pytest.mark.parametrize(
        (
            "raw_name",
            "normalized_name",
            "expected_title",
            "expected_year",
            "expected_lang",
            "expected_sub",
        ),
        [
            (
                "Avatar.2009.EN. tit.cz.mkv",
                "Avatar 2009 - EN (tit. CZ)",
                "Avatar",
                2009,
                "EN",
                True,
            ),
            (
                "Interstellar.2014.CZ.mkv",
                "Interstellar 2014 - CZ",
                "Interstellar",
                2014,
                "CZ",
                False,
            ),
            (
                "Underworld 5 - Krvave valky (2016) - CZ.mkv",
                "Underworld 5 - Krvave valky (2016) - CZ",
                "Underworld 5 - Krvave valky",
                2016,
                "CZ",
                False,
            ),
            (
                "Movie.Without.Language.1999.mp4",
                "Movie Without Language 1999",
                "Movie Without Language",
                1999,
                None,
                False,
            ),
            (
                "No.Year.Title.mkv",
                "No Year Title",
                "No Year Title",
                None,
                None,
                False,
            ),
        ],
    )
    def test_parse(
        self,
        raw_name: str,
        normalized_name: str,
        expected_title: str,
        expected_year: int | None,
        expected_lang: str | None,
        expected_sub: bool,
    ) -> None:
        """Parse movie metadata from cleaned names.

        :param raw_name: Original filename.
        :param normalized_name: Cleaned filename.
        :param expected_title: Expected parsed title.
        :param expected_year: Expected parsed year.
        :param expected_lang: Expected language code.
        :param expected_sub: Expected Czech subtitle flag.
        """
        parser = MovieNameParser()
        parsed: ParsedName = parser.parse(raw_name=raw_name, normalized_name=normalized_name)

        assert parsed.media_type is MediaType.MOVIE
        assert parsed.raw_name == raw_name
        assert parsed.normalized_name == normalized_name
        assert parsed.title == expected_title
        assert parsed.year == expected_year
        assert parsed.language_code == expected_lang
        assert parsed.has_czech_subtitles is expected_sub
        assert parsed.season is None
        assert parsed.episode is None

    @pytest.mark.parametrize(
        ("normalized_name", "expected_confidence"),
        [
            ("Avatar 2009", 0.9),
            ("Only Title", 0.55),
        ],
    )
    def test_confidence_rule(self, normalized_name: str, expected_confidence: float) -> None:
        """Use higher confidence when both year and non-empty title are available.

        :param normalized_name: Cleaned movie name.
        :param expected_confidence: Expected confidence score.
        """
        parsed: ParsedName = MovieNameParser().parse(
            raw_name="x.mkv", normalized_name=normalized_name
        )
        assert parsed.confidence == pytest.approx(expected_confidence)

    @pytest.mark.parametrize(
        ("normalized_name", "expected"),
        [
            ("Title 2020 - EN", "EN"),
            ("Title 2020 - CZ (tit. CZ)", "CZ"),
            ("Title 2020", None),
            ("Title - en", None),
        ],
    )
    def test_detect_language(self, normalized_name: str, expected: str | None) -> None:
        """Detect language only for supported uppercase two-letter pattern.

        :param normalized_name: Cleaned movie name.
        :param expected: Expected language code.
        """
        parser = MovieNameParser()
        assert parser._detect_language(normalized_name) == expected
