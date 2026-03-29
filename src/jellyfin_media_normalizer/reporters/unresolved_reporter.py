"""Reporter for unresolved (unidentified) media items."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.utils.logging import LoggingMixin


class UnresolvedReporter(LoggingMixin):
    """Write a JSON report containing only items without a resolved provider ID."""

    def write(self, items: list[ParsedMediaItem], output_path: Path) -> Path:
        """Write unresolved items report and return the file path.

        Only items with ``provider_match`` unset and ``media_type`` other than
        ``unknown`` are included. Unknown items are excluded because they are
        expected to be unidentifiable by design.

        :param items: All parsed media items from the lookup stage.
        :param output_path: Destination path for the JSON report.
        :return: The path of the written report file.
        """
        unresolved: list[ParsedMediaItem] = [
            item for item in items if item.provider_match is None and item.media_type != "unknown"
        ]

        movie_count: int = sum(1 for item in unresolved if item.media_type == "movie")
        tv_count: int = sum(1 for item in unresolved if item.media_type == "tv_episode")

        payload: dict[str, object] = {
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {
                "total_unresolved": len(unresolved),
                "movies": movie_count,
                "tv_episodes": tv_count,
            },
            "items": [
                {
                    "media_type": item.media_type,
                    "title": item.title,
                    "normalized_title": item.normalized_title,
                    "year": item.year,
                    "season": item.season,
                    "episode": item.episode,
                    "language": item.language,
                    "confidence": item.confidence,
                    "validation_status": item.validation_status.value,
                    "issues": item.issues,
                    "source_path": str(item.source.path),
                }
                for item in unresolved
            ],
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        self.log.info(
            "Unresolved items report written",
            extra={
                "extra": {
                    "output_path": str(output_path),
                    "unresolved_count": len(unresolved),
                    "movies": movie_count,
                    "tv_episodes": tv_count,
                }
            },
        )

        return output_path
