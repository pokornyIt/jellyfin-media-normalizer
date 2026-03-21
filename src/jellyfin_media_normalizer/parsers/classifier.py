"""Media filename classifier."""

from __future__ import annotations

import re

from jellyfin_media_normalizer.models.media_type import MediaType


class Classifier:
    """Classify media filenames."""

    _TV_PATTERN: re.Pattern[str] = re.compile(r"\bS(\d{2})E(\d{2})\b", re.IGNORECASE)
    _YEAR_PATTERN: re.Pattern[str] = re.compile(r"\b(19\d{2}|20\d{2}|21\d{2})\b")

    def classify(self, name: str) -> MediaType:
        """Classify a normalized filename.

        :param name: Cleaned filename.
        :return: Detected media type.
        """
        if self._TV_PATTERN.search(name):
            return MediaType.TV_EPISODE

        if self._YEAR_PATTERN.search(name):
            return MediaType.MOVIE

        return MediaType.UNKNOWN
