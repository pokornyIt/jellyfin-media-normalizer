"""Path helper utilities."""

from __future__ import annotations

from pathlib import Path


def ensure_directory(path: Path) -> None:
    """Ensure that a directory exists.

    :param path: Target directory path.
    """
    path.mkdir(parents=True, exist_ok=True)
