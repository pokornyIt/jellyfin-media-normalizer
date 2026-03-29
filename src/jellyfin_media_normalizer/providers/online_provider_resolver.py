"""Online provider resolver with cache write-through."""

from __future__ import annotations

from typing import Protocol

from jellyfin_media_normalizer.models.parsed_media_item import ParsedMediaItem
from jellyfin_media_normalizer.models.provider_match import ProviderMatch
from jellyfin_media_normalizer.providers.provider_clients import TmdbClient, TvdbClient
from jellyfin_media_normalizer.providers.provider_id_cache import ProviderIdCacheResolver
from jellyfin_media_normalizer.settings import Settings
from jellyfin_media_normalizer.utils.logging import LoggingMixin


class MovieLookupClientProtocol(Protocol):
    """Protocol for movie lookup client."""

    def search_movie(self, title: str, year: int | None = None) -> ProviderMatch | None:
        """Search movie match.

        :param title: Normalized title.
        :param year: Optional year.
        :return: Matched provider ID.
        """
        ...


class TvSeriesLookupClientProtocol(Protocol):
    """Protocol for TV series lookup client."""

    def search_tv_series(self, title: str) -> ProviderMatch | None:
        """Search TV series match.

        :param title: Normalized title.
        :return: Matched provider ID.
        """
        ...


class OnlineProviderResolver(LoggingMixin):
    """Resolve provider IDs using remote provider APIs with cache write-through."""

    settings: Settings
    cache_resolver: ProviderIdCacheResolver
    movie_clients: list[MovieLookupClientProtocol]
    tv_series_clients: list[TvSeriesLookupClientProtocol]

    def __init__(
        self,
        settings: Settings,
        cache_resolver: ProviderIdCacheResolver,
        movie_clients: list[MovieLookupClientProtocol] | None = None,
        tv_series_clients: list[TvSeriesLookupClientProtocol] | None = None,
    ) -> None:
        """Initialize resolver.

        :param settings: Application settings.
        :param cache_resolver: Cache resolver used for key generation and persistence.
        :param movie_clients: Optional explicit movie clients.
        :param tv_series_clients: Optional explicit TV series clients.
        """
        self.settings = settings
        self.cache_resolver = cache_resolver
        self.movie_clients = movie_clients or self._build_movie_clients()
        self.tv_series_clients = tv_series_clients or self._build_tv_series_clients()

    def resolve(self, item: ParsedMediaItem) -> ProviderMatch | None:
        """Resolve provider ID online and persist result to cache.

        :param item: Parsed media item.
        :return: Provider match or ``None``.
        """
        lookup_key: str | None = self.cache_resolver.build_lookup_key(item)
        if lookup_key is None:
            return None

        if item.media_type == "movie":
            match: ProviderMatch | None = self._resolve_movie(item, lookup_key)
            return match

        if item.media_type == "tv_episode":
            match = self._resolve_tv_series(item, lookup_key)
            return match

        return None

    def _resolve_movie(self, item: ParsedMediaItem, lookup_key: str) -> ProviderMatch | None:
        """Resolve movie ID using configured movie clients.

        :param item: Parsed movie item.
        :param lookup_key: Cache lookup key.
        :return: Provider match or ``None``.
        """
        for client in self.movie_clients:
            match: ProviderMatch | None = client.search_movie(
                title=item.normalized_title,
                year=item.year,
            )
            if match is None:
                continue

            persisted_match: ProviderMatch = self.cache_resolver.store_lookup_result(
                lookup_key, match
            )
            return persisted_match

        return None

    def _resolve_tv_series(self, item: ParsedMediaItem, lookup_key: str) -> ProviderMatch | None:
        """Resolve TV series ID using configured clients.

        :param item: Parsed TV episode item.
        :param lookup_key: Cache lookup key.
        :return: Provider match or ``None``.
        """
        for client in self.tv_series_clients:
            match: ProviderMatch | None = client.search_tv_series(title=item.normalized_title)
            if match is None:
                continue

            persisted_match: ProviderMatch = self.cache_resolver.store_lookup_result(
                lookup_key, match
            )
            return persisted_match

        return None

    def _build_movie_clients(self) -> list[MovieLookupClientProtocol]:
        """Build default movie clients from settings.

        :return: Ordered list of movie clients.
        """
        clients: list[MovieLookupClientProtocol] = []
        if self.settings.tmdb_api_key is not None:
            clients.append(TmdbClient(api_key=self.settings.tmdb_api_key))
        return clients

    def _build_tv_series_clients(self) -> list[TvSeriesLookupClientProtocol]:
        """Build default TV series clients from settings.

        :return: Ordered list of TV series clients.
        """
        clients: list[TvSeriesLookupClientProtocol] = []
        if self.settings.tmdb_api_key is not None:
            clients.append(TmdbClient(api_key=self.settings.tmdb_api_key))
        if self.settings.tvdb_api_key is not None:
            clients.append(TvdbClient(api_key=self.settings.tvdb_api_key))
        return clients
