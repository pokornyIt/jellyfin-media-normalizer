"""Application settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    """Application runtime settings.

    :param app_name: Application name used for logging and diagnostics.
    :param library_path: Mounted media library path inside the container.
    :param workspace_path: Root workspace path for generated files.
    :param cache_path: Path for provider/API cache data.
    :param reports_path: Path for generated reports.
    :param manifests_path: Path for generated rename manifests.
    :param logs_path: Path for local log files or exported logs.
    :param log_level: Requested logging level.
    :param log_format: Logging format, either ``text`` or ``json``.
    :param dry_run: Whether destructive operations are disabled by default.
    :param tmdb_api_key: TMDb API key, if configured.
    :param tvdb_api_key: TVDB API key, if configured.
    """

    app_name: str
    library_path: Path
    workspace_path: Path
    cache_path: Path
    reports_path: Path
    manifests_path: Path
    logs_path: Path
    log_level: str
    log_format: str
    dry_run: bool
    tmdb_api_key: str | None
    tvdb_api_key: str | None

    @classmethod
    def from_env(cls) -> Settings:
        """Create settings from environment variables.

        :return: Initialized settings instance.
        """
        workspace_path: Path = Path(os.getenv("JMN_WORKSPACE_PATH", "/workspace"))

        return cls(
            app_name=os.getenv("JMN_APP_NAME", "jellyfin-media-normalizer"),
            library_path=Path(os.getenv("JMN_LIBRARY_PATH", "/library")),
            workspace_path=workspace_path,
            cache_path=Path(os.getenv("JMN_CACHE_PATH", str(workspace_path / "cache"))),
            reports_path=Path(os.getenv("JMN_REPORTS_PATH", str(workspace_path / "reports"))),
            manifests_path=Path(os.getenv("JMN_MANIFESTS_PATH", str(workspace_path / "manifests"))),
            logs_path=Path(os.getenv("JMN_LOGS_PATH", str(workspace_path / "logs"))),
            log_level=os.getenv("JMN_LOG_LEVEL", "INFO").upper(),
            log_format=os.getenv("JMN_LOG_FORMAT", "text").lower(),
            dry_run=_parse_bool(os.getenv("JMN_DRY_RUN", "true")),
            tmdb_api_key=_optional_env("JMN_TMDB_API_KEY"),
            tvdb_api_key=_optional_env("JMN_TVDB_API_KEY"),
        )

    def ensure_directories(self) -> None:
        """Create required workspace directories if they do not exist."""
        for directory in (
            self.workspace_path,
            self.cache_path,
            self.reports_path,
            self.manifests_path,
            self.logs_path,
        ):
            directory.mkdir(parents=True, exist_ok=True)


def _optional_env(name: str) -> str | None:
    """Return an environment variable value or ``None`` if empty.

    :param name: Environment variable name.
    :return: Normalized value or ``None``.
    """
    value: str | None = os.getenv(name)
    if value is None or value.strip() == "":
        return None
    return value.strip()


def _parse_bool(value: str) -> bool:
    """Parse a boolean-like environment variable value.

    :param value: Raw input value.
    :return: Parsed boolean value.
    """
    return value.strip().lower() in {"1", "true", "yes", "on"}
