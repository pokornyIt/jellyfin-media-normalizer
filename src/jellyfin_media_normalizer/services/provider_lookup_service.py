"""Provider lookup service."""

from __future__ import annotations

from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.provider_match import ProviderMatch
from jellyfin_media_normalizer.providers.online_provider_resolver import OnlineProviderResolver
from jellyfin_media_normalizer.providers.provider_id_cache import ProviderIdCacheResolver
from jellyfin_media_normalizer.providers.provider_resolver_chain import ProviderResolverChain
from jellyfin_media_normalizer.providers.provider_resolver_chain import (
    ProviderResolverProtocol as ResolverProtocol,
)
from jellyfin_media_normalizer.settings import Settings
from jellyfin_media_normalizer.utils.logging import LoggingMixin


class ProviderLookupService(LoggingMixin):
    """Resolve and attach provider IDs to parsed media items."""

    def __init__(
        self,
        settings: Settings,
        resolver: ResolverProtocol | None = None,
    ) -> None:
        """Initialize service.

        :param settings: Application settings.
        :param resolver: Optional provider resolver implementation.
        """
        self.settings: Settings = settings
        self.resolver: ResolverProtocol = resolver or self._build_default_resolver()
        self.progress_interval: int = settings.provider_lookup_progress_interval

    def run(self, media_items: list[ParsedMediaItem]) -> list[ParsedMediaItem]:
        """Resolve provider IDs for all parsed items.

        :param media_items: Parsed items that already passed parsing and validation.
        :return: The same list with ``provider_match`` field populated when possible.
        """
        self.log.info(
            "Running provider lookup service",
            extra={"extra": {"item_count": len(media_items)}},
        )

        total: int = len(media_items)
        resolved_count: int = 0
        cache_count: int = 0
        online_count: int = 0

        for processed, item in enumerate(media_items, start=1):
            if item.media_type == "unknown":
                _append_issue(item, "Provider lookup skipped for unknown media type.")
            else:
                match: ProviderMatch | None = self.resolver.resolve(item)
                if match is None:
                    _append_issue(
                        item, "Provider ID not found in provider cache or online providers."
                    )
                else:
                    item.provider_match = match
                    resolved_count += 1
                    if match.reason.startswith("cache_exact_key:"):
                        cache_count += 1
                    else:
                        online_count += 1

            if processed % self.progress_interval == 0:
                self.log.info(
                    "Provider lookup progress",
                    extra={
                        "extra": {
                            "processed": processed,
                            "total": total,
                            "resolved": resolved_count,
                            "unresolved": processed - resolved_count,
                        }
                    },
                )

        unresolved_count: int = total - resolved_count
        self.log.info(
            "Provider lookup service finished",
            extra={
                "extra": {
                    "item_count": total,
                    "resolved_count": resolved_count,
                    "cache_count": cache_count,
                    "online_count": online_count,
                    "unresolved_count": unresolved_count,
                }
            },
        )

        return media_items

    def _build_default_resolver(self) -> ResolverProtocol:
        """Build default cache-first resolver chain.

        :return: Resolver chain instance.
        """
        cache_resolver = ProviderIdCacheResolver(self.settings.cache_path / "provider_ids.json")
        try:
            cache_resolver.bootstrap()
        except OSError:
            self.log.warning(
                "Provider cache bootstrap failed",
                extra={"extra": {"cache_path": str(cache_resolver.cache_file_path)}},
            )
        online_resolver = OnlineProviderResolver(
            settings=self.settings,
            cache_resolver=cache_resolver,
        )
        return ProviderResolverChain([cache_resolver, online_resolver])


def _append_issue(item: ParsedMediaItem, issue: str) -> None:
    """Append issue once.

    :param item: Parsed media item.
    :param issue: Issue text.
    """
    if issue not in item.issues:
        item.issues.append(issue)
