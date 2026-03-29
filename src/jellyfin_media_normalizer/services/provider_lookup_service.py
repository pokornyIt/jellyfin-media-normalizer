"""Provider lookup service."""

from __future__ import annotations

from typing import Protocol

from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.provider_match import ProviderMatch
from jellyfin_media_normalizer.providers.provider_id_cache import ProviderIdCacheResolver
from jellyfin_media_normalizer.settings import Settings
from jellyfin_media_normalizer.utils.logging import LoggingMixin


class ProviderResolverProtocol(Protocol):
    """Protocol for provider resolver dependency."""

    def resolve(self, item: ParsedMediaItem) -> ProviderMatch | None:
        """Resolve provider ID for one parsed media item.

        :param item: Parsed media item.
        :return: Provider match if found.
        """
        ...


class ProviderLookupService(LoggingMixin):
    """Resolve and attach provider IDs to parsed media items."""

    def __init__(
        self,
        settings: Settings,
        resolver: ProviderResolverProtocol | None = None,
    ) -> None:
        """Initialize service.

        :param settings: Application settings.
        :param resolver: Optional provider resolver implementation.
        """
        self.settings: Settings = settings
        self.resolver: ProviderResolverProtocol = resolver or ProviderIdCacheResolver(
            settings.cache_path / "provider_ids.json"
        )

    def run(self, media_items: list[ParsedMediaItem]) -> list[ParsedMediaItem]:
        """Resolve provider IDs for all parsed items.

        :param media_items: Parsed items that already passed parsing and validation.
        :return: The same list with ``provider_match`` field populated when possible.
        """
        self.log.info(
            "Running provider lookup service",
            extra={"extra": {"item_count": len(media_items)}},
        )

        resolved_count: int = 0
        for item in media_items:
            if item.media_type == "unknown":
                _append_issue(item, "Provider lookup skipped for unknown media type.")
                continue

            match: ProviderMatch | None = self.resolver.resolve(item)
            if match is None:
                _append_issue(item, "Provider ID not found in provider cache.")
                continue

            item.provider_match = match
            resolved_count += 1

        self.log.info(
            "Provider lookup service finished",
            extra={
                "extra": {
                    "item_count": len(media_items),
                    "resolved_count": resolved_count,
                    "unresolved_count": len(media_items) - resolved_count,
                }
            },
        )

        return media_items


def _append_issue(item: ParsedMediaItem, issue: str) -> None:
    """Append issue once.

    :param item: Parsed media item.
    :param issue: Issue text.
    """
    if issue not in item.issues:
        item.issues.append(issue)
