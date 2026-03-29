"""Cache-based provider ID resolver."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.provider_match import ProviderMatch
from jellyfin_media_normalizer.utils.logging import LoggingMixin


class ProviderIdCacheResolver(LoggingMixin):
    """Resolve provider IDs from a local cache file.

    The cache file is expected at ``workspace/cache/provider_ids.json`` and uses
    canonical lookup keys. For TV episodes, the lookup key is always based on the
    series title only, never on episode-level attributes.

    :param cache_file_path: Path to cache JSON file.
    """

    def __init__(self, cache_file_path: Path) -> None:
        """Initialize resolver.

        :param cache_file_path: Path to provider ID cache JSON file.
        """
        self.cache_file_path = cache_file_path
        self._cache_entries: dict[str, ProviderMatch] | None = None

    def resolve(self, item: ParsedMediaItem) -> ProviderMatch | None:
        """Resolve provider ID for one parsed media item.

        :param item: Parsed media item to resolve.
        :return: Provider match when available, otherwise ``None``.
        """
        lookup_key: str | None = self.build_lookup_key(item)
        if lookup_key is None:
            return None

        entries: dict[str, ProviderMatch] = self._load_cache_entries()
        cached_match: ProviderMatch | None = entries.get(lookup_key)
        if cached_match is None:
            return None

        return ProviderMatch(
            provider=cached_match.provider,
            provider_id=cached_match.provider_id,
            confidence=cached_match.confidence,
            reason=f"cache_exact_key:{lookup_key}",
            lookup_key=lookup_key,
        )

    def build_lookup_key(self, item: ParsedMediaItem) -> str | None:
        """Build canonical lookup key from parsed media item.

        :param item: Parsed media item.
        :return: Canonical lookup key or ``None`` for unsupported media type.
        """
        normalized_title: str = item.normalized_title.strip().lower()
        if normalized_title == "":
            return None

        if item.media_type == "movie":
            if item.year is not None:
                return f"movie|{normalized_title}|{item.year}"
            return f"movie|{normalized_title}"

        if item.media_type == "tv_episode":
            return f"tv_series|{normalized_title}"

        return None

    def _load_cache_entries(self) -> dict[str, ProviderMatch]:
        """Load cache entries from disk once and memoize them.

        :return: Cache entries indexed by lookup key.
        """
        if self._cache_entries is not None:
            return self._cache_entries

        if not self.cache_file_path.exists():
            self._cache_entries = {}
            return self._cache_entries

        raw_payload: Any = json.loads(self.cache_file_path.read_text(encoding="utf-8"))
        cache_node: Any = (
            raw_payload.get("entries", raw_payload) if isinstance(raw_payload, dict) else {}
        )

        entries: dict[str, ProviderMatch] = {}
        if not isinstance(cache_node, dict):
            self._cache_entries = entries
            return entries

        for lookup_key, value in cache_node.items():
            if not isinstance(value, dict):
                continue

            provider_value: Any = value.get("provider")
            provider_id_value: Any = value.get("provider_id")
            if not isinstance(provider_value, str) or not isinstance(provider_id_value, str):
                continue

            confidence_value: Any = value.get("confidence", 1.0)
            confidence: float = (
                float(confidence_value) if isinstance(confidence_value, int | float) else 1.0
            )

            reason_value: Any = value.get("reason", "cache_entry")
            reason: str = reason_value if isinstance(reason_value, str) else "cache_entry"

            entries[lookup_key] = ProviderMatch(
                provider=provider_value.strip().lower(),
                provider_id=provider_id_value.strip(),
                confidence=confidence,
                reason=reason,
                lookup_key=lookup_key,
            )

        self._cache_entries = entries
        return entries
