"""Tests for the high-level MediaParser."""

from __future__ import annotations

from pathlib import Path

import pytest

from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
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
                "Dark.s3e8.-.CZ.mkv",
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
        assert parsed.confidence == pytest.approx(0.92)

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


class TestMediaParserNormalizationHelpers:
    """Tests for internal cleanup and normalization helpers."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("Movie...Name___2020", "Movie Name 2020"),
            ("  A___B..C  ", "A B C"),
        ],
    )
    def test_cleanup_name(self, value: str, expected: str) -> None:
        """Replace separators and normalize spaces.

        :param value: Raw value to clean up.
        :param expected: Expected cleaned value.
        """
        parser = MediaParser()
        assert parser._cleanup_name(value) == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("The Matrix 1080p BluRay x264", "The Matrix"),
            ("Show Name remux h265", "Show Name"),
            ("Normal Title", "Normal Title"),
        ],
    )
    def test_normalize_title(self, value: str, expected: str) -> None:
        """Remove known noise tokens from title chunks.

        :param value: Title value with possible noise tokens.
        :param expected: Expected normalized title.
        """
        parser = MediaParser()
        assert parser._normalize_title(value) == expected
