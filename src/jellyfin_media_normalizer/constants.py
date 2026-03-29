"""Project-wide constants."""

from __future__ import annotations

APP_NAME: str = "jellyfin-media-normalizer"

SUPPORTED_VIDEO_EXTENSIONS: tuple[str, ...] = (
    ".mkv",
    ".mp4",
    ".avi",
    ".mov",
    ".m4v",
    ".wmv",
    ".ts",
    ".m2ts",
)

KNOWN_NOISE_TOKENS: tuple[str, ...] = (
    "1080p",
    "2160p",
    "720p",
    "bluray",
    "bdrip",
    "brrip",
    "webrip",
    "web-dl",
    "webdl",
    "dvdrip",
    "hdrip",
    "x264",
    "x265",
    "h264",
    "h265",
    "hevc",
    "aac",
    "dts",
    "ac3",
    "proper",
    "repack",
    "extended",
    "remux",
    "uhd",
)

LANGUAGE_CODES: tuple[str, ...] = ("CZ", "EN", "DE", "SK", "FR", "IT", "ES")
