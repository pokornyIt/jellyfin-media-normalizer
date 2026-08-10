"""HTML reporter for unresolved provider matches."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, select_autoescape

from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.utils.logging import LoggingMixin


class UnresolvedHtmlReporter(LoggingMixin):
    """Write unresolved provider matches into a human-friendly HTML report."""

    _TEMPLATE: str = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Unresolved Provider Report</title>
  <style>
    :root {
      --bg: #f5f7fb;
      --surface: #ffffff;
      --text: #1d2635;
      --muted: #67758d;
      --accent: #0f6db3;
      --danger: #ae2a2a;
      --border: #d7deeb;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      font-family: "Segoe UI", "Noto Sans", "Liberation Sans", sans-serif;
      color: var(--text);
      background: linear-gradient(180deg, #eef3ff 0%, var(--bg) 260px);
      min-height: 100vh;
    }

    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 24px;
    }

    .header {
      margin-bottom: 18px;
    }

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
      min-width: 980px;
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

    .badge--movie {
      background: #eaf4ff;
      border-color: #bfddff;
      color: #0f4f84;
    }

    .badge--tv {
      background: #ecfff1;
      border-color: #baeac8;
      color: #17663a;
    }

    .issues {
      color: var(--danger);
      max-width: 380px;
    }

    .no-data {
      padding: 18px;
      color: var(--muted);
      background: var(--surface);
      border: 1px dashed var(--border);
      border-radius: 12px;
    }

    .footnote {
      margin-top: 10px;
      color: var(--muted);
      font-size: 0.85rem;
    }
  </style>
</head>
<body>
  <main class=\"container\">
    <header class=\"header\">
      <h1 class=\"title\">Unresolved Provider Report</h1>
      <p class=\"subtitle\">Generated at {{ generated_at }}. Source items: {{ total_scanned }}.</p>
    </header>

    <section class=\"cards\" aria-label=\"Summary\">
      <article class=\"card\">
        <div class=\"card__label\">Unresolved total</div>
        <div class=\"card__value\">{{ summary.total_unresolved }}</div>
      </article>
      <article class=\"card\">
        <div class=\"card__label\">Movies</div>
        <div class=\"card__value\">{{ summary.movies }}</div>
      </article>
      <article class=\"card\">
        <div class=\"card__label\">TV episodes</div>
        <div class=\"card__value\">{{ summary.tv_episodes }}</div>
      </article>
    </section>

    {% if rows %}
    <section class=\"filters\" aria-label=\"Filters\">
      <input
        id=\"searchInput\"
        type=\"search\"
        placeholder=\"Search by title, path or issue\"
        aria-label=\"Search rows\"
      >
      <select id=\"mediaTypeFilter\" aria-label=\"Filter by media type\">
        <option value=\"all\">All media types</option>
        <option value=\"movie\">Movie</option>
        <option value=\"tv_episode\">TV episode</option>
      </select>
    </section>

    <section class=\"table-wrap\" aria-label=\"Unresolved items table\">
      <table id=\"reportTable\">
        <thead>
          <tr>
            <th>Type</th>
            <th>Title</th>
            <th>Year / SxE</th>
            <th>Confidence</th>
            <th>Validation</th>
            <th>Issues</th>
            <th>Source path</th>
          </tr>
        </thead>
        <tbody>
          {% for row in rows %}
          <tr data-media-type=\"{{ row.media_type }}\">
            <td>
              {% if row.media_type == \"movie\" %}
              <span class=\"badge badge--movie\">Movie</span>
              {% else %}
              <span class=\"badge badge--tv\">TV episode</span>
              {% endif %}
            </td>
            <td>{{ row.title }}</td>
            <td>{{ row.time_ref }}</td>
            <td>{{ row.confidence }}</td>
            <td>{{ row.validation_status }}</td>
            <td class=\"issues\">{{ row.issues }}</td>
            <td>{{ row.source_path }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
    <p class=\"footnote\">Tip: Use search and media type filters to triage manual fixes quickly.</p>
    {% else %}
    <section class=\"no-data\">
      No unresolved items found for this run.
    </section>
    {% endif %}
  </main>

  <script>
    (function () {
      const searchInput = document.getElementById("searchInput");
      const mediaTypeFilter = document.getElementById("mediaTypeFilter");
      const table = document.getElementById("reportTable");
      if (!searchInput || !mediaTypeFilter || !table) {
        return;
      }

      function normalize(text) {
        return (text || "").toString().toLowerCase();
      }

      function applyFilters() {
        const searchValue = normalize(searchInput.value);
        const mediaTypeValue = mediaTypeFilter.value;
        const rows = table.querySelectorAll("tbody tr");

        rows.forEach((row) => {
          const rowText = normalize(row.textContent);
          const mediaType = row.getAttribute("data-media-type") || "";
          const matchesText = rowText.includes(searchValue);
          const matchesType = mediaTypeValue === "all" || mediaType === mediaTypeValue;
          row.style.display = matchesText && matchesType ? "" : "none";
        });
      }

      searchInput.addEventListener("input", applyFilters);
      mediaTypeFilter.addEventListener("change", applyFilters);
    })();
  </script>
</body>
</html>
"""

    def write(self, items: list[ParsedMediaItem], output_path: Path) -> Path:
        """Write unresolved items into a standalone HTML report.

        :param items: Parsed media items from provider lookup stage.
        :param output_path: Destination file path for the HTML output.
        :return: The path of the written HTML report.
        """
        unresolved_items: list[ParsedMediaItem] = [
            item for item in items if item.provider_match is None and item.media_type != "unknown"
        ]
        rows: list[dict[str, str]] = [self._build_row(item) for item in unresolved_items]

        payload: dict[str, Any] = {
            "generated_at": datetime.now(UTC).isoformat(),
            "total_scanned": len(items),
            "summary": {
                "total_unresolved": len(unresolved_items),
                "movies": sum(1 for item in unresolved_items if item.media_type == "movie"),
                "tv_episodes": sum(1 for item in unresolved_items if item.media_type == "tv_episode"),
            },
            "rows": rows,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self._render(payload), encoding="utf-8")

        self.log.info(
            "Unresolved HTML report written",
            extra={
                "extra": {
                    "output_path": str(output_path),
                    "unresolved_count": len(unresolved_items),
                }
            },
        )
        return output_path

    def _build_row(self, item: ParsedMediaItem) -> dict[str, str]:
        """Build one HTML table row payload from parsed item data.

        :param item: Parsed media item that remains unresolved.
        :return: Table row payload used by Jinja template rendering.
        """
        if item.media_type == "movie":
            time_ref: str = str(item.year) if item.year is not None else "-"
        else:
            season: str = "?" if item.season is None else str(item.season)
            episode: str = "?" if item.episode is None else str(item.episode)
            time_ref = f"S{season}E{episode}"

        issue_text: str = "; ".join(item.issues) if item.issues else "-"

        return {
            "media_type": item.media_type,
            "title": item.title,
            "time_ref": time_ref,
            "confidence": f"{item.confidence:.2f}",
            "validation_status": item.validation_status.value,
            "issues": issue_text,
            "source_path": str(item.source.path),
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
