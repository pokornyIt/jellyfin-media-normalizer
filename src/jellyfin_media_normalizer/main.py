"""Application module entrypoint."""

from __future__ import annotations

from jellyfin_media_normalizer.cli.app import app


def main() -> None:
    """Run the CLI application."""
    app()


if __name__ == "__main__":
    main()
