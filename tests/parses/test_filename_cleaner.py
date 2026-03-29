"""Tests for filename normalization before parsing."""

from __future__ import annotations

import pytest

from jellyfin_media_normalizer.parsers.filename_cleaner import FilenameCleaner


class TestFilenameCleaner:
    """Tests for :class:`FilenameCleaner`."""

    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("Avatar.2009.1080p.BluRay.x264.mkv", "Avatar 2009"),
            ("Breaking.Bad.S01E01.WEB-DL.720p.mp4", "Breaking Bad S01E01"),
            ("Movie__Name__2020__HDRip__AAC.avi", "Movie Name 2020"),
            ("Series.S01E02.remux.h265.mkv", "Series S01E02"),
            ("Simple Name.mp4", "Simple Name"),
            ("Name.with.multiple...dots.mkv", "Name with multiple dots"),
        ],
    )
    def test_clean(self, filename: str, expected: str) -> None:
        """Normalize separators and remove known release tags.

        :param filename: Raw filename including extension.
        :param expected: Expected cleaned value.
        """
        cleaner = FilenameCleaner()
        assert cleaner.clean(filename) == expected

    @pytest.mark.parametrize(
        "filename",
        [
            "Movie.2021.x264.AAC.mkv",
            "Film.1999.H265.DTS.mp4",
            "Title.2012.remux.proper.avi",
        ],
    )
    def test_removes_only_known_release_tokens(self, filename: str) -> None:
        """Remove known noise tokens but keep semantic title/year parts.

        :param filename: Filename with release tags.
        """
        cleaned: str = FilenameCleaner().clean(filename)
        assert "x264" not in cleaned.lower()
        assert "aac" not in cleaned.lower()
        assert "h265" not in cleaned.lower()
        assert any(char.isdigit() for char in cleaned)

    def test_strips_whitespace_after_transformations(self) -> None:
        """Return value should not have leading or trailing whitespace."""
        cleaned: str = FilenameCleaner().clean("Movie...2022...WEBRip...mkv")
        assert cleaned == cleaned.strip()

    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("Cesta_českou_krajinou_2020.mkv", "Cesta ceskou krajinou 2020"),
            ("Žízala.žena.S01E01.mkv", "Zizala zena S01E01"),
            ("Mašinglil.Slovenská.Série.mkv", "Masinglil Slovenska Serie"),
            ("Dve.Letní.Noci.2018.mkv", "Dve Letni Noci 2018"),
            ("Říjany_muži_nebrědá.mkv", "Rijany muzi nebreda"),
            ("Český.Velký.Rok.S01E02.mkv", "Cesky Velky Rok S01E02"),
        ],
    )
    def test_transliterates_czech_slovak_diacritics(self, filename: str, expected: str) -> None:
        """Convert Czech/Slovak diacritical marks to ASCII equivalents.

        :param filename: Filename with diacritical marks.
        :param expected: Expected result with ASCII characters.
        """
        cleaner = FilenameCleaner()
        assert cleaner.clean(filename) == expected

    def test_transliteration_preserves_other_characters(self) -> None:
        """Transliteration should not affect numbers or standard ASCII."""
        cleaned: str = FilenameCleaner().clean("Film.Cesky.2024.mkv")
        assert "2024" in cleaned
        assert "Film" in cleaned
        assert "Cesky" in cleaned

    def test_transliteration_handles_mixed_content(self) -> None:
        """Transliteration should work with mixed Czech/English content."""
        cleaned: str = FilenameCleaner().clean("Czech.Drama.žížala.2020.mkv")
        # After transliteration and cleanup, should be normalized
        assert cleaned == "Czech Drama zizala 2020"
