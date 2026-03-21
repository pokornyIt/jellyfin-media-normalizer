"""CLI entrypoint."""

from __future__ import annotations

from pathlib import Path

import click

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
    logger = get_logger(__name__)

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
    media_items = service.run()

    click.echo(f"Discovered {len(media_items)} media files.")

    preview_limit: int = min(10, len(media_items))
    for item in media_items[:preview_limit]:
        click.echo(f"- {item.relative_path}")


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
