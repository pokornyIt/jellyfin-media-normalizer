"""Tests for the high-level MediaParser."""

from __future__ import annotations

from pathlib import Path

import pytest

from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.media_type import MediaType
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.parsed_name import ParsedName
from jellyfin_media_normalizer.parsers.media_parser import MediaParser


def _item(filename: str) -> MediaItem:
    """Build a MediaItem using a filename within a sample library path.

    :param filename: Filename including extension.
    :return: MediaItem for parser input.
    """
    return MediaItem(
        path=Path("/library") / filename,
        relative_path=Path(filename),
        extension=Path(filename).suffix,
    )


class TestMediaParserParse:
    """Tests for :meth:`MediaParser.parse`."""

    @pytest.mark.parametrize(
        (
            "filename",
            "expected_title",
            "expected_norm_title",
            "expected_season",
            "expected_episode",
        ),
        [
            (
                "Breaking.Bad.S01E01.-.EN.mkv",
                "Breaking Bad",
                "Breaking Bad",
                1,
                1,
            ),
            (
                "Dark.S03E08.-.CZ.mkv",
                "Dark",
                "Dark",
                3,
                8,
            ),
        ],
    )
    def test_parse_tv_episode(
        self,
        filename: str,
        expected_title: str,
        expected_norm_title: str,
        expected_season: int,
        expected_episode: int,
    ) -> None:
        """Parse TV episodes and extract series title and episode markers.

        :param filename: Input filename.
        :param expected_title: Expected parsed title.
        :param expected_norm_title: Expected normalized title.
        :param expected_season: Expected season number.
        :param expected_episode: Expected episode number.
        """
        parsed: ParsedMediaItem = MediaParser().parse(_item(filename))
        assert parsed.media_type == "tv_episode"
        assert parsed.title == expected_title
        assert parsed.normalized_title == expected_norm_title
        assert parsed.season == expected_season
        assert parsed.episode == expected_episode
        assert parsed.confidence == pytest.approx(0.95)

    @pytest.mark.parametrize(
        ("filename", "expected_title", "expected_year", "expected_norm_title"),
        [
            ("Avatar.2009.-.EN.mkv", "Avatar", 2009, "Avatar"),
            (
                "The.Matrix.1999.1080p.BluRay.x264.-.EN.mkv",
                "The Matrix",
                1999,
                "The Matrix",
            ),
            (
                "Underworld 5 - Krvave valky (2016) - CZ.mkv",
                "Underworld 5 - Krvave valky",
                2016,
                "Underworld 5 - Krvave valky",
            ),
        ],
    )
    def test_parse_movie(
        self,
        filename: str,
        expected_title: str,
        expected_year: int,
        expected_norm_title: str,
    ) -> None:
        """Parse movies and extract title/year metadata.

        :param filename: Input filename.
        :param expected_title: Expected parsed title.
        :param expected_year: Expected year.
        :param expected_norm_title: Expected normalized title.
        """
        parsed: ParsedMediaItem = MediaParser().parse(_item(filename))
        assert parsed.media_type == "movie"
        assert parsed.title == expected_title
        assert parsed.year == expected_year
        assert parsed.normalized_title == expected_norm_title
        assert parsed.confidence == pytest.approx(0.9)

    @pytest.mark.parametrize(
        "filename",
        [
            "Random.File.Without.Markers.mkv",
            "Documentary.Name.mp4",
        ],
    )
    def test_parse_unknown(self, filename: str) -> None:
        """Return unknown classification when no movie or TV pattern is detected.

        :param filename: Input filename without recognizable markers.
        """
        parsed: ParsedMediaItem = MediaParser().parse(_item(filename))
        assert parsed.media_type == "unknown"
        assert parsed.confidence == pytest.approx(0.2)
        assert parsed.issues == ["Unable to detect movie year or TV episode pattern."]


class TestMediaParserLanguageExtraction:
    """Tests for language extraction behavior in parse outcomes."""

    @pytest.mark.parametrize(
        ("filename", "expected_lang", "expected_sub"),
        [
            ("Avatar.2009.-.EN.mkv", "EN", None),
            ("Avatar.2009.-.CZ.(tit.EN).mkv", "CZ", "EN"),
            ("Avatar.2009.-.XX.mkv", None, None),
            ("Dark.S01E01.-.DE.mkv", "DE", None),
            ("Dark.S01E01.-.DE.(title.CZ).mkv", "DE", "CZ"),
            ("Dark S01E01 (2021) - DE (tit CZ).mkv", "DE", "CZ"),
        ],
    )
    def test_language_and_subtitle_language(
        self,
        filename: str,
        expected_lang: str | None,
        expected_sub: str | None,
    ) -> None:
        """Extract language suffix only when it matches supported language codes.

        :param filename: Input filename.
        :param expected_lang: Expected language code.
        :param expected_sub: Expected subtitle language code.
        """
        parsed: ParsedMediaItem = MediaParser().parse(_item(filename))
        assert parsed.language == expected_lang
        assert parsed.subtitle_language == expected_sub


class _FakeCleaner:
    """Fake cleaner for dependency injection tests."""

    def clean(self, filename: str) -> str:
        """Return deterministic cleaned value.

        :param filename: Raw filename.
        :return: Constant cleaned value.
        """
        _ = filename
        return "cleaned-name"


class _FakeClassifier:
    """Fake classifier for dependency injection tests."""

    def classify(self, name: str) -> MediaType:
        """Classify all inputs as movies.

        :param name: Cleaned filename.
        :return: Fixed movie type.
        """
        _ = name
        return MediaType.MOVIE


class _FakeMovieParser:
    """Fake movie parser for dependency injection tests."""

    def parse(self, raw_name: str, normalized_name: str) -> ParsedName:
        """Return deterministic parsed movie data.

        :param raw_name: Original filename.
        :param normalized_name: Cleaned filename.
        :return: ParsedName with injected values.
        """
        _ = raw_name
        _ = normalized_name
        return ParsedName(
            media_type=MediaType.MOVIE,
            raw_name="fake.mkv",
            normalized_name="fake normalized",
            title="Injected Title",
            year=1984,
            season=None,
            episode=None,
            language_code="EN",
            has_czech_subtitles=False,
            has_english_subtitles=True,
            confidence=0.77,
        )


class _FakeTvParser:
    """Fake TV parser for dependency injection tests."""

    def parse(self, raw_name: str, normalized_name: str) -> ParsedName:
        """Return unknown for all inputs.

        :param raw_name: Original filename.
        :param normalized_name: Cleaned filename.
        :return: Unknown ParsedName.
        """
        _ = raw_name
        _ = normalized_name
        return ParsedName(
            media_type=MediaType.UNKNOWN,
            raw_name="fake.mkv",
            normalized_name="fake normalized",
            title=None,
            year=None,
            season=None,
            episode=None,
            language_code=None,
            has_czech_subtitles=False,
            has_english_subtitles=False,
            confidence=0.0,
        )


class TestMediaParserDependencyInjection:
    """Tests constructor-based dependency injection on MediaParser."""

    def test_parse_uses_injected_dependencies(self) -> None:
        """Injected cleaner/classifier/parsers are used instead of defaults.

        :return: None
        """
        parser = MediaParser(
            cleaner=_FakeCleaner(),
            classifier=_FakeClassifier(),
            movie_parser=_FakeMovieParser(),
            tv_parser=_FakeTvParser(),
        )

        parsed: ParsedMediaItem = parser.parse(_item("anything.mkv"))

        assert parsed.media_type == "movie"
        assert parsed.title == "Injected Title"
        assert parsed.year == 1984
        assert parsed.subtitle_language == "EN"
        assert parsed.confidence == pytest.approx(0.77)
