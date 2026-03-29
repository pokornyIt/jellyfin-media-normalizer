"""CLI entrypoint."""

from __future__ import annotations

from logging import Logger
from pathlib import Path

import click

from jellyfin_media_normalizer.models.media_item import MediaItem
from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.providers.provider_id_cache import ProviderIdCacheResolver
from jellyfin_media_normalizer.reporters.json_reporter import JsonReporter
from jellyfin_media_normalizer.reporters.review_reporter import ReviewReporter
from jellyfin_media_normalizer.reporters.unresolved_reporter import UnresolvedReporter
from jellyfin_media_normalizer.services.parse_service import ParseService
from jellyfin_media_normalizer.services.scan_service import ScanService
from jellyfin_media_normalizer.settings import Settings
from jellyfin_media_normalizer.utils.logging import get_logger, setup_logging


@click.group()
@click.pass_context
def app(ctx: click.Context) -> None:
    """Main CLI group."""
    settings: Settings = Settings.from_env()
    settings.ensure_directories()

    setup_logging(
        level=settings.log_level,
        log_format=settings.log_format,
        app_name=settings.app_name,
    )

    ctx.ensure_object(dict)
    ctx.obj["settings"] = settings


@app.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Show current runtime settings."""
    settings: Settings = ctx.obj["settings"]
    logger: Logger = get_logger(__name__)

    logger.info(
        "Displaying runtime settings",
        extra={
            "extra": {
                "library_path": str(settings.library_path),
                "workspace_path": str(settings.workspace_path),
                "cache_path": str(settings.cache_path),
                "reports_path": str(settings.reports_path),
                "manifests_path": str(settings.manifests_path),
                "logs_path": str(settings.logs_path),
                "log_level": settings.log_level,
                "log_format": settings.log_format,
                "dry_run": settings.dry_run,
            }
        },
    )

    click.echo("Application settings loaded successfully.")


@app.command()
@click.pass_context
def scan(ctx: click.Context) -> None:
    """Scan the media library and print a summary."""
    settings: Settings = ctx.obj["settings"]
    service: ScanService = ScanService(settings=settings)
    media_items: list[MediaItem] = service.run()

    click.echo(f"Discovered {len(media_items)} media files.")

    preview_limit: int = min(10, len(media_items))
    for item in media_items[:preview_limit]:
        click.echo(f"- {item.relative_path}")


@app.command()
@click.option(
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional custom path for the review JSON report.",
)
@click.pass_context
def parse(ctx: click.Context, output_path: Path | None) -> None:
    """Scan, parse and validate the media library. Writes a review report."""
    settings: Settings = ctx.obj["settings"]
    scan_service: ScanService = ScanService(settings=settings)
    parse_service: ParseService = ParseService(settings=settings)
    reporter: ReviewReporter = ReviewReporter()
    unresolved_reporter: UnresolvedReporter = UnresolvedReporter()

    media_items: list[MediaItem] = scan_service.run()
    parsed_items: list[ParsedMediaItem] = parse_service.run(media_items)

    click.echo(f"Parsed {len(parsed_items)} media files.")
    passed_count: int = sum(1 for item in parsed_items if item.validation_status.value == "passed")
    review_count: int = sum(
        1 for item in parsed_items if item.validation_status.value == "review_needed"
    )
    failed_count: int = sum(1 for item in parsed_items if item.validation_status.value == "failed")
    click.echo(
        "Validation summary: "
        f"passed={passed_count}, review_needed={review_count}, failed={failed_count}"
    )

    resolved_count: int = sum(1 for item in parsed_items if item.provider_match is not None)
    cache_count: int = sum(
        1
        for item in parsed_items
        if item.provider_match is not None
        and item.provider_match.reason.startswith("cache_exact_key:")
    )
    online_count: int = resolved_count - cache_count
    unresolved_count: int = sum(
        1 for item in parsed_items if item.provider_match is None and item.media_type != "unknown"
    )
    click.echo(
        "Provider lookup summary: "
        f"resolved={resolved_count} (cache={cache_count}, online={online_count}), "
        f"unresolved={unresolved_count}"
    )

    report_path: Path = output_path or (settings.reports_path / "parse-review-report.json")
    written_path: Path = reporter.write(parsed_items, report_path)
    click.echo(f"Review report written to: {written_path}")

    unresolved_path: Path = settings.reports_path / "unresolved-provider-report.json"
    written_unresolved_path: Path = unresolved_reporter.write(parsed_items, unresolved_path)
    click.echo(f"Unresolved provider report written to: {written_unresolved_path}")


@app.command(name="report-scan")
@click.option(
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional custom path for the JSON report.",
)
@click.pass_context
def report_scan(ctx: click.Context, output_path: Path | None) -> None:
    """Scan, parse and write a JSON report.

    :param output_path: Optional custom path for the JSON report. If not provided,
        defaults to 'reports/scan-report.json' in the workspace.
    """
    settings: Settings = ctx.obj["settings"]
    scan_service: ScanService = ScanService(settings=settings)
    parse_service: ParseService = ParseService(settings=settings)
    reporter: JsonReporter = JsonReporter()

    media_items: list[MediaItem] = scan_service.run()
    parsed_items: list[ParsedMediaItem] = parse_service.run(media_items)
    report_path: Path = output_path or (settings.reports_path / "report-scan-results.json")
    written_path: Path = reporter.write(parsed_items, report_path)
    click.echo(f"JSON report written to: {written_path}")


@app.command()
@click.argument("path_value", type=click.Path(path_type=Path))
def validate_path(path_value: Path) -> None:
    """Validate an arbitrary path for diagnostics.

    :param path_value: Path to validate.
    """
    if path_value.exists():
        click.echo(f"Path exists: {path_value}")
        return

    click.echo(f"Path does not exist: {path_value}")
    raise SystemExit(1)


@app.command(name="bootstrap-providers")
@click.pass_context
def bootstrap_providers(ctx: click.Context) -> None:
    """Bootstrap provider cache file in workspace cache directory."""
    settings: Settings = ctx.obj["settings"]
    cache_resolver = ProviderIdCacheResolver(settings.cache_path / "provider_ids.json")
    cache_resolver.bootstrap()
    click.echo(f"Provider cache bootstrapped: {cache_resolver.cache_file_path}")
