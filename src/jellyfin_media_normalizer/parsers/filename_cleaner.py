"""Filename cleaning helpers."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path


class FilenameCleaner:
    """Clean raw media filenames before parsing."""

    _SEPARATORS_PATTERN: re.Pattern[str] = re.compile(r"[._]+")
    _MULTISPACE_PATTERN: re.Pattern[str] = re.compile(r"\s+")
    _RELEASE_TAGS_PATTERN: re.Pattern[str] = re.compile(
        r"\b("
        r"bluray|brrip|bdrip|webrip|web-dl|webdl|dvdrip|hdrip|"
        r"x264|x265|h264|h265|hevc|aac|dts|ac3|proper|repack|remux|"
        r"1080p|2160p|720p"
        r")\b",
        re.IGNORECASE,
    )

    def clean(self, filename: str) -> str:
        """Clean a raw filename into a normalized parse-friendly form.

        :param filename: Raw filename.
        :return: Cleaned filename without extension and release junk.
        """
        stem: str = Path(filename).stem
        normalized: str = self._SEPARATORS_PATTERN.sub(" ", stem)
        normalized = self._RELEASE_TAGS_PATTERN.sub(" ", normalized)
        normalized = self._transliterate(normalized)
        normalized = self._MULTISPACE_PATTERN.sub(" ", normalized).strip()
        return normalized

    def _transliterate(self, value: str) -> str:
        """Replace non-ASCII characters with their ASCII equivalents.

        Converts diacritical marks (Czech, Slovak, etc.) to ASCII base characters.
        For example: č→c, ž→z, š→s, ě→e, ř→r, ů→u, ó→o, ô→o.

        :param value: Input string with potential non-ASCII characters.
        :return: String with all non-ASCII characters converted to ASCII equivalents.
        """
        # Normalize to NFKD form (decomposes combined characters)
        normalized: str = unicodedata.normalize("NFKD", value)
        # Filter out combining marks (accents, diacritics)
        ascii_only: str = normalized.encode("ascii", "ignore").decode("ascii")
        return ascii_only
