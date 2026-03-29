"""Tests for the ParsedName dataclass."""

from __future__ import annotations

import pytest

from jellyfin_media_normalizer.models.media_type import MediaType
from jellyfin_media_normalizer.models.parsed_name import ParsedName


def _make_parsed_name(
    media_type: MediaType = MediaType.MOVIE,
    raw_name: str = "Avatar (2009) - EN.mkv",
    normalized_name: str = "avatar 2009 en",
    title: str | None = "Avatar",
    year: int | None = 2009,
    season: int | None = None,
    episode: int | None = None,
    language_code: str | None = "EN",
    has_czech_subtitles: bool = False,
    has_english_subtitles: bool = False,
    confidence: float = 0.95,
) -> ParsedName:
    """Build a :class:`ParsedName` with sensible defaults.

    :param media_type: Detected media type.
    :param raw_name: Original filename without path.
    :param normalized_name: Cleaned name.
    :param title: Parsed title.
    :param year: Parsed year.
    :param season: Season number.
    :param episode: Episode number.
    :param language_code: Audio language code.
    :param has_czech_subtitles: Whether Czech subtitles exist.
    :param confidence: Parser confidence score.
    :return: Constructed ParsedName.
    """
    return ParsedName(
        media_type=media_type,
        raw_name=raw_name,
        normalized_name=normalized_name,
        title=title,
        year=year,
        season=season,
        episode=episode,
        language_code=language_code,
        has_czech_subtitles=has_czech_subtitles,
        has_english_subtitles=has_english_subtitles,
        confidence=confidence,
    )


class TestParsedNameCreation:
    """Tests for construction of :class:`ParsedName`."""

    @pytest.mark.parametrize(
        ("media_type", "title", "year", "season", "episode"),
        [
            (MediaType.MOVIE, "Avatar", 2009, None, None),
            (MediaType.TV_EPISODE, "Breaking Bad", None, 1, 1),
            (MediaType.UNKNOWN, None, None, None, None),
            (MediaType.TV_EPISODE, "The Witcher", None, 3, 8),
        ],
    )
    def test_fields_stored_correctly(
        self,
        media_type: MediaType,
        title: str | None,
        year: int | None,
        season: int | None,
        episode: int | None,
    ) -> None:
        """Fields must be stored exactly as provided.

        :param media_type: Detected media type.
        :param title: Parsed title or None.
        :param year: Parsed year or None.
        :param season: Season number or None.
        :param episode: Episode number or None.
        """
        pn: ParsedName = _make_parsed_name(
            media_type=media_type,
            title=title,
            year=year,
            season=season,
            episode=episode,
        )
        assert pn.media_type is media_type
        assert pn.title == title
        assert pn.year == year
        assert pn.season == season
        assert pn.episode == episode

    @pytest.mark.parametrize(
        "confidence",
        [0.0, 0.5, 1.0, 0.75, 0.123],
    )
    def test_confidence_stored_as_float(self, confidence: float) -> None:
        """Confidence value must be stored as-is.

        :param confidence: Confidence score to store.
        """
        pn: ParsedName = _make_parsed_name(confidence=confidence)
        assert pn.confidence == pytest.approx(confidence)

    @pytest.mark.parametrize(
        ("language_code", "has_czech_subtitles"),
        [
            ("EN", False),
            ("CZ", True),
            ("DE", False),
            (None, False),
            (None, True),
        ],
    )
    def test_language_fields_stored_correctly(
        self,
        language_code: str | None,
        has_czech_subtitles: bool,
    ) -> None:
        """Language and subtitle fields must reflect what was provided.

        :param language_code: Audio language code or None.
        :param has_czech_subtitles: Czech subtitle flag.
        """
        pn: ParsedName = _make_parsed_name(
            language_code=language_code,
            has_czech_subtitles=has_czech_subtitles,
        )
        assert pn.language_code == language_code
        assert pn.has_czech_subtitles is has_czech_subtitles

    @pytest.mark.parametrize(
        "media_type",
        list(MediaType),
    )
    def test_all_media_types_accepted(self, media_type: MediaType) -> None:
        """ParsedName must accept every defined MediaType member.

        :param media_type: MediaType member to test.
        """
        pn: ParsedName = _make_parsed_name(media_type=media_type)
        assert pn.media_type is media_type


class TestParsedNameAllNoneOptionals:
    """Tests for ParsedName with all optional fields set to None."""

    def test_optional_fields_accept_none(self) -> None:
        """ParsedName must allow None for all optional fields simultaneously."""
        pn = ParsedName(
            media_type=MediaType.UNKNOWN,
            raw_name="unknown_file.mkv",
            normalized_name="unknown file",
            title=None,
            year=None,
            season=None,
            episode=None,
            language_code=None,
            has_czech_subtitles=False,
            has_english_subtitles=False,
            confidence=0.0,
        )
        assert pn.title is None
        assert pn.year is None
        assert pn.season is None
        assert pn.episode is None
        assert pn.language_code is None
