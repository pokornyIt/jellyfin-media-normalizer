"""Tests for TV episode filename parser."""

from __future__ import annotations

import pytest

from jellyfin_media_normalizer.models.media_type import MediaType
from jellyfin_media_normalizer.models.parsed_name import ParsedName
from jellyfin_media_normalizer.parsers.tv_episode_parser import TvEpisodeParser


class TestTvEpisodeParser:
    """Tests for :class:`TvEpisodeParser`."""

    @pytest.mark.parametrize(
        (
            "raw_name",
            "normalized_name",
            "expected_title",
            "expected_season",
            "expected_episode",
            "expected_year",
            "expected_lang",
            "expected_sub",
        ),
        [
            (
                "Breaking.Bad.S01E01.EN.mkv",
                "Breaking Bad S01E01 - EN",
                "Breaking Bad",
                1,
                1,
                None,
                "EN",
                False,
            ),
            (
                "Dark.S03E08.CZ.mkv",
                "Dark S03E08 - CZ",
                "Dark",
                3,
                8,
                None,
                "CZ",
                False,
            ),
            (
                "Dark.S03E08.DE. tit.CZ.mkv",
                "Dark S03E08 - DE (tit. CZ)",
                "Dark",
                3,
                8,
                None,
                "DE",
                True,
            ),
            (
                "Show.2019.S02E05.mp4",
                "Show 2019 S02E05",
                "Show 2019",
                2,
                5,
                2019,
                None,
                False,
            ),
        ],
    )
    def test_parse_tv_episode(
        self,
        raw_name: str,
        normalized_name: str,
        expected_title: str,
        expected_season: int,
        expected_episode: int,
        expected_year: int | None,
        expected_lang: str | None,
        expected_sub: bool,
    ) -> None:
        """Extract TV metadata from names with SxxExx marker.

        :param raw_name: Original filename.
        :param normalized_name: Cleaned filename.
        :param expected_title: Expected parsed title.
        :param expected_season: Expected season number.
        :param expected_episode: Expected episode number.
        :param expected_year: Expected parsed year.
        :param expected_lang: Expected language code.
        :param expected_sub: Expected Czech subtitle flag.
        """
        parser = TvEpisodeParser()
        parsed: ParsedName = parser.parse(raw_name=raw_name, normalized_name=normalized_name)

        assert parsed.media_type is MediaType.TV_EPISODE
        assert parsed.title == expected_title
        assert parsed.season == expected_season
        assert parsed.episode == expected_episode
        assert parsed.year == expected_year
        assert parsed.language_code == expected_lang
        assert parsed.has_czech_subtitles is expected_sub

    @pytest.mark.parametrize(
        "normalized_name",
        [
            "Movie 2001 - EN",
            "No markers here",
            "S1E1 short format",
        ],
    )
    def test_returns_unknown_when_no_strict_sxxexx(self, normalized_name: str) -> None:
        """Return unknown when strict two-digit SxxExx marker is missing.

        :param normalized_name: Cleaned filename without strict TV marker.
        """
        parsed: ParsedName = TvEpisodeParser().parse(
            raw_name="x.mkv", normalized_name=normalized_name
        )
        assert parsed.media_type is MediaType.UNKNOWN
        assert parsed.title is None
        assert parsed.confidence == pytest.approx(0.0)

    @pytest.mark.parametrize(
        ("normalized_name", "expected_confidence"),
        [
            ("Show S01E01", 0.95),
            ("S01E01", 0.65),
        ],
    )
    def test_confidence_rule(self, normalized_name: str, expected_confidence: float) -> None:
        """Use lower confidence when title part is missing.

        :param normalized_name: Cleaned TV name.
        :param expected_confidence: Expected confidence score.
        """
        parsed: ParsedName = TvEpisodeParser().parse(
            raw_name="x.mkv", normalized_name=normalized_name
        )
        assert parsed.confidence == pytest.approx(expected_confidence)

    @pytest.mark.parametrize(
        ("normalized_name", "expected"),
        [
            ("Show S01E01 - EN", "EN"),
            ("Show S01E01 - DE (tit. CZ)", "DE"),
            ("Show S01E01", None),
            ("Show S01E01 - en", None),
        ],
    )
    def test_detect_language(self, normalized_name: str, expected: str | None) -> None:
        """Detect language only for uppercase two-letter pattern.

        :param normalized_name: Cleaned TV name.
        :param expected: Expected language code.
        """
        parser = TvEpisodeParser()
        assert parser._detect_language(normalized_name) == expected
