"""JSON report writer."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.utils.logging import LoggingMixin


class JsonReporter(LoggingMixin):
    """Write parsed scan results into a JSON report file."""

    def write(self, items: list[ParsedMediaItem], output_path: Path) -> Path:
        """Write a JSON report and return the file path."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        media_type_counter: Counter[str] = Counter(item.media_type for item in items)
        payload: dict[str, object] = {
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {
                "total_items": len(items),
                "movies": media_type_counter.get("movie", 0),
                "tv_episodes": media_type_counter.get("tv_episode", 0),
                "unknown": media_type_counter.get("unknown", 0),
                "manual_review": sum(1 for item in items if item.issues),
            },
            "items": [item.to_dict() for item in items],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.log.info(
            "JSON report written",
            extra={"extra": {"output_path": str(output_path), "item_count": len(items)}},
        )
        return output_path
