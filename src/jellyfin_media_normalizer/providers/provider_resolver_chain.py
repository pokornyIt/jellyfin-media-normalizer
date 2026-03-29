"""Resolver chain for provider ID lookup."""

from __future__ import annotations

from typing import Protocol

from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.provider_match import ProviderMatch
from jellyfin_media_normalizer.utils.logging import LoggingMixin


class ProviderResolverProtocol(Protocol):
    """Resolver protocol for chain components."""

    def resolve(self, item: ParsedMediaItem) -> ProviderMatch | None:
        """Resolve provider ID for parsed item.

        :param item: Parsed media item.
        :return: Provider match or ``None``.
        """
        ...


class ProviderResolverChain(LoggingMixin):
    """Run provider resolvers in order until first match."""

    resolvers: list[ProviderResolverProtocol]

    def __init__(self, resolvers: list[ProviderResolverProtocol]) -> None:
        """Initialize resolver chain.

        :param resolvers: Ordered resolver list.
        """
        self.resolvers = resolvers
        self.log.debug(
            "Initialized provider resolver chain",
            extra={"extra": {"resolver_count": len(resolvers)}},
        )

    def resolve(self, item: ParsedMediaItem) -> ProviderMatch | None:
        """Resolve provider ID using first successful resolver.

        :param item: Parsed media item.
        :return: Provider match or ``None``.
        """
        for resolver in self.resolvers:
            self.log.debug(
                "Trying resolver",
                extra={
                    "extra": {
                        "resolver": resolver.__class__.__name__,
                        "title": item.normalized_title,
                    }
                },
            )
            match: ProviderMatch | None = resolver.resolve(item)
            if match is not None:
                self.log.debug(
                    "Resolver found match",
                    extra={
                        "extra": {
                            "resolver": resolver.__class__.__name__,
                            "provider": match.provider,
                            "provider_id": match.provider_id,
                        }
                    },
                )
                return match

        self.log.debug(
            "No resolver found match",
            extra={"extra": {"title": item.normalized_title}},
        )
        return None
