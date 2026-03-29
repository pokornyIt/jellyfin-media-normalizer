"""Resolver chain for provider ID lookup."""

from __future__ import annotations

from typing import Protocol

from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.provider_match import ProviderMatch


class ProviderResolverProtocol(Protocol):
    """Resolver protocol for chain components."""

    def resolve(self, item: ParsedMediaItem) -> ProviderMatch | None:
        """Resolve provider ID for parsed item.

        :param item: Parsed media item.
        :return: Provider match or ``None``.
        """
        ...


class ProviderResolverChain:
    """Run provider resolvers in order until first match."""

    resolvers: list[ProviderResolverProtocol]

    def __init__(self, resolvers: list[ProviderResolverProtocol]) -> None:
        """Initialize resolver chain.

        :param resolvers: Ordered resolver list.
        """
        self.resolvers = resolvers

    def resolve(self, item: ParsedMediaItem) -> ProviderMatch | None:
        """Resolve provider ID using first successful resolver.

        :param item: Parsed media item.
        :return: Provider match or ``None``.
        """
        for resolver in self.resolvers:
            match: ProviderMatch | None = resolver.resolve(item)
            if match is not None:
                return match
        return None
