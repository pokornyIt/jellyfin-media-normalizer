"""JSON reporting utilities."""

from __future__ import annotations

import json
from pathlib import Path

from jellyfin_media_normalizer.models.scan_result import ScanResult
from jellyfin_media_normalizer.utils.logging import LoggingMixin


class JsonReporter(LoggingMixin):
    """Write scan results into JSON files."""

    def write_report(self, scan_result: ScanResult, output_path: Path) -> None:
        """Write a JSON report for the given scan result.

        :param scan_result: Scan result to report.
        :param output_path: Output file path for the JSON report.
        """
        self.log.info(
            "Writing JSON report",
            extra={"extra": {"output_path": str(output_path)}},
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(scan_result, f, ensure_ascii=False, indent=4)
