"""HTML reporter for review-needed and failed parsed items."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, select_autoescape

from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.validation_status import ValidationStatus
from jellyfin_media_normalizer.utils.logging import LoggingMixin


class ReviewHtmlReporter(LoggingMixin):
    """Write a human-friendly HTML report for items requiring manual review."""

    _TEMPLATE: str = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Parse Review Report</title>
  <style>
    :root {
      --bg: #f5f7fb;
      --surface: #ffffff;
      --text: #1d2635;
      --muted: #67758d;
      --border: #d7deeb;
      --review-bg: #fff7e8;
      --review-border: #ffddb2;
      --review-text: #8e4a00;
      --failed-bg: #ffeef0;
      --failed-border: #ffc7cf;
      --failed-text: #9d1c2e;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: "Segoe UI", "Noto Sans", "Liberation Sans", sans-serif;
      color: var(--text);
      background: linear-gradient(180deg, #eef3ff 0%, var(--bg) 260px);
      min-height: 100vh;
    }

    .container {
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px;
    }

    .header { margin-bottom: 18px; }

    .title {
      margin: 0;
      font-size: 2rem;
      line-height: 1.2;
    }

    .subtitle {
      margin-top: 6px;
      color: var(--muted);
      font-size: 0.95rem;
    }

    .cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin: 18px 0 20px;
    }

    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px;
      box-shadow: 0 2px 9px rgba(15, 38, 76, 0.05);
    }

    .card__label {
      color: var(--muted);
      font-size: 0.82rem;
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .card__value {
      font-size: 1.65rem;
      font-weight: 700;
    }

    .filters {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin-bottom: 12px;
    }

    .filters input,
    .filters select {
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 0.95rem;
      padding: 9px 12px;
      min-height: 40px;
      background: #fff;
      color: var(--text);
    }

    .filters input {
      flex: 1 1 260px;
    }

    .table-wrap {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: auto;
      box-shadow: 0 2px 9px rgba(15, 38, 76, 0.05);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 1120px;
    }

    th,
    td {
      border-bottom: 1px solid var(--border);
      padding: 10px 12px;
      text-align: left;
      vertical-align: top;
      font-size: 0.92rem;
    }

    th {
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--muted);
      background: #fbfcff;
      position: sticky;
      top: 0;
      z-index: 1;
    }

    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 600;
      border: 1px solid transparent;
      white-space: nowrap;
    }

    .badge--review {
      background: var(--review-bg);
      border-color: var(--review-border);
      color: var(--review-text);
    }

    .badge--failed {
      background: var(--failed-bg);
      border-color: var(--failed-border);
      color: var(--failed-text);
    }

    .issues { color: var(--failed-text); max-width: 320px; }
    .warnings { color: #a46300; max-width: 320px; }

    .no-data {
      padding: 18px;
      color: var(--muted);
      background: var(--surface);
      border: 1px dashed var(--border);
      border-radius: 12px;
    }
  </style>
</head>
<body>
  <main class=\"container\">
    <header class=\"header\">
      <h1 class=\"title\">Parse Review Report</h1>
      <p class=\"subtitle\">Generated at {{ generated_at }}. Source items: {{ total_scanned }}.</p>
    </header>

    <section class=\"cards\" aria-label=\"Summary\">
      <article class=\"card\"><div class=\"card__label\">Review total</div><div class=\"card__value\">{{ summary.total_review_items }}</div></article>
      <article class=\"card\"><div class=\"card__label\">Review needed</div><div class=\"card__value\">{{ summary.review_needed }}</div></article>
      <article class=\"card\"><div class=\"card__label\">Failed</div><div class=\"card__value\">{{ summary.failed }}</div></article>
      <article class=\"card\"><div class=\"card__label\">Movies</div><div class=\"card__value\">{{ summary.movies }}</div></article>
      <article class=\"card\"><div class=\"card__label\">TV episodes</div><div class=\"card__value\">{{ summary.tv_episodes }}</div></article>
    </section>

    {% if rows %}
    <section class=\"filters\" aria-label=\"Filters\">
      <input id=\"searchInput\" type=\"search\" placeholder=\"Search by title, path, issue or warning\" aria-label=\"Search rows\">
      <select id=\"statusFilter\" aria-label=\"Filter by validation status\">
        <option value=\"all\">All statuses</option>
        <option value=\"review_needed\">review_needed</option>
        <option value=\"failed\">failed</option>
      </select>
      <select id=\"mediaTypeFilter\" aria-label=\"Filter by media type\">
        <option value=\"all\">All media types</option>
        <option value=\"movie\">Movie</option>
        <option value=\"tv_episode\">TV episode</option>
        <option value=\"unknown\">Unknown</option>
      </select>
    </section>

    <section class=\"table-wrap\" aria-label=\"Review items table\">
      <table id=\"reportTable\">
        <thead>
          <tr>
            <th>Status</th>
            <th>Type</th>
            <th>Title</th>
            <th>Year / SxE</th>
            <th>Confidence</th>
            <th>Validation confidence</th>
            <th>Issues</th>
            <th>Warnings</th>
            <th>Path</th>
          </tr>
        </thead>
        <tbody>
          {% for row in rows %}
          <tr data-status=\"{{ row.validation_status }}\" data-media-type=\"{{ row.media_type }}\">
            <td>
              {% if row.validation_status == \"failed\" %}
              <span class=\"badge badge--failed\">failed</span>
              {% else %}
              <span class=\"badge badge--review\">review_needed</span>
              {% endif %}
            </td>
            <td>{{ row.media_type }}</td>
            <td>{{ row.title }}</td>
            <td>{{ row.time_ref }}</td>
            <td>{{ row.confidence }}</td>
            <td>{{ row.validation_confidence }}</td>
            <td class=\"issues\">{{ row.issues }}</td>
            <td class=\"warnings\">{{ row.warnings }}</td>
            <td>{{ row.path }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
    {% else %}
    <section class=\"no-data\">No review-needed or failed items found for this run.</section>
    {% endif %}
  </main>

  <script>
    (function () {
      const searchInput = document.getElementById("searchInput");
      const statusFilter = document.getElementById("statusFilter");
      const mediaTypeFilter = document.getElementById("mediaTypeFilter");
      const table = document.getElementById("reportTable");
      if (!searchInput || !statusFilter || !mediaTypeFilter || !table) {
        return;
      }

      function normalize(text) {
        return (text || "").toString().toLowerCase();
      }

      function applyFilters() {
        const searchValue = normalize(searchInput.value);
        const statusValue = statusFilter.value;
        const mediaTypeValue = mediaTypeFilter.value;
        const rows = table.querySelectorAll("tbody tr");

        rows.forEach((row) => {
          const rowText = normalize(row.textContent);
          const rowStatus = row.getAttribute("data-status") || "";
          const rowType = row.getAttribute("data-media-type") || "";
          const matchesText = rowText.includes(searchValue);
          const matchesStatus = statusValue === "all" || rowStatus === statusValue;
          const matchesType = mediaTypeValue === "all" || rowType === mediaTypeValue;
          row.style.display = matchesText && matchesStatus && matchesType ? "" : "none";
        });
      }

      searchInput.addEventListener("input", applyFilters);
      statusFilter.addEventListener("change", applyFilters);
      mediaTypeFilter.addEventListener("change", applyFilters);
    })();
  </script>
</body>
</html>
"""

    def write(self, items: list[ParsedMediaItem], output_path: Path) -> Path:
        """Write review-needed and failed items into a standalone HTML report.

        :param items: Parsed media items from validation stage.
        :param output_path: Destination file path for the HTML output.
        :return: The path of the written HTML report.
        """
        review_items: list[ParsedMediaItem] = [
            item
            for item in items
            if item.validation_status in (ValidationStatus.REVIEW_NEEDED, ValidationStatus.FAILED)
        ]
        rows: list[dict[str, str]] = [self._build_row(item) for item in review_items]

        media_type_counter: Counter[str] = Counter(item.media_type for item in review_items)
        status_counter: Counter[str] = Counter(
            item.validation_status.value for item in review_items
        )

        payload: dict[str, Any] = {
            "generated_at": datetime.now(UTC).isoformat(),
            "total_scanned": len(items),
            "summary": {
                "total_review_items": len(review_items),
                "review_needed": status_counter.get(ValidationStatus.REVIEW_NEEDED.value, 0),
                "failed": status_counter.get(ValidationStatus.FAILED.value, 0),
                "movies": media_type_counter.get("movie", 0),
                "tv_episodes": media_type_counter.get("tv_episode", 0),
            },
            "rows": rows,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self._render(payload), encoding="utf-8")

        self.log.info(
            "Review HTML report written",
            extra={
                "extra": {
                    "output_path": str(output_path),
                    "review_item_count": len(review_items),
                }
            },
        )
        return output_path

    def _build_row(self, item: ParsedMediaItem) -> dict[str, str]:
        """Build one HTML table row payload from parsed item data.

        :param item: Parsed media item requiring review.
        :return: Table row payload used by Jinja template rendering.
        """
        if item.media_type == "movie":
            time_ref: str = str(item.year) if item.year is not None else "-"
        else:
            season: str = "?" if item.season is None else str(item.season)
            episode: str = "?" if item.episode is None else str(item.episode)
            time_ref = f"S{season}E{episode}"

        issues: list[str] = item.validation_result.issues if item.validation_result else []
        warnings: list[str] = item.validation_result.warnings if item.validation_result else []

        return {
            "validation_status": item.validation_status.value,
            "media_type": item.media_type,
            "title": item.title,
            "time_ref": time_ref,
            "confidence": f"{item.confidence:.2f}",
            "validation_confidence": item.validation_confidence.value,
            "issues": "; ".join(issues) if issues else "-",
            "warnings": "; ".join(warnings) if warnings else "-",
            "path": str(item.source.relative_path),
        }

    def _render(self, payload: dict[str, Any]) -> str:
        """Render HTML from a payload using a safe Jinja environment.

        :param payload: Template payload with summary and table rows.
        :return: Rendered HTML document.
        """
        environment = Environment(
            autoescape=select_autoescape(
                enabled_extensions=("html", "xml"),
                default_for_string=True,
            ),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = environment.from_string(self._TEMPLATE)
        return template.render(**payload)
