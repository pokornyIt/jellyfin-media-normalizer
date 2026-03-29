"""JSON review report writer for items requiring manual attention."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.validation_status import ValidationStatus
from jellyfin_media_normalizer.utils.logging import LoggingMixin


class ReviewReporter(LoggingMixin):
    """Write items requiring manual review into a JSON report file."""

    def write(self, items: list[ParsedMediaItem], output_path: Path) -> Path:
        """Write a review JSON report with items needing attention and return the file path.

        :param items: All parsed media items. Only items with status review_needed or failed
            are included in the report.
        :param output_path: Target file path for the JSON report.
        :return: The path of the written report file.
        """
        review_items: list[ParsedMediaItem] = [
            item
            for item in items
            if item.validation_status in (ValidationStatus.REVIEW_NEEDED, ValidationStatus.FAILED)
        ]

        output_path.parent.mkdir(parents=True, exist_ok=True)

        media_type_counter: Counter[str] = Counter(item.media_type for item in review_items)
        status_counter: Counter[str] = Counter(
            item.validation_status.value for item in review_items
        )

        payload: dict[str, object] = {
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {
                "total_items_scanned": len(items),
                "review_needed": status_counter.get(ValidationStatus.REVIEW_NEEDED.value, 0),
                "failed": status_counter.get(ValidationStatus.FAILED.value, 0),
                "by_media_type": {
                    "movie": media_type_counter.get("movie", 0),
                    "tv_episode": media_type_counter.get("tv_episode", 0),
                    "unknown": media_type_counter.get("unknown", 0),
                },
            },
            "items": [
                {
                    "path": str(item.source.relative_path),
                    "media_type": item.media_type,
                    "title": item.title,
                    "normalized_title": item.normalized_title,
                    "year": item.year,
                    "season": item.season,
                    "episode": item.episode,
                    "language": item.language,
                    "confidence": item.confidence,
                    "validation_status": item.validation_status.value,
                    "validation_confidence": item.validation_confidence.value,
                    "issues": item.validation_result.issues if item.validation_result else [],
                    "warnings": item.validation_result.warnings if item.validation_result else [],
                }
                for item in review_items
            ],
        }

        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.log.info(
            "Review report written",
            extra={
                "extra": {
                    "output_path": str(output_path),
                    "review_item_count": len(review_items),
                }
            },
        )
        return output_path
