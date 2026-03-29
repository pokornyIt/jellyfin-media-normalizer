"""Online provider clients for provider ID lookup."""

from __future__ import annotations

from typing import Any

import httpx

from jellyfin_media_normalizer.constants import PROVIDER_TMDB, PROVIDER_TVDB
from jellyfin_media_normalizer.models.provider_match import ProviderMatch
from jellyfin_media_normalizer.utils.logging import LoggingMixin


class TmdbClient(LoggingMixin):
    """Client for TMDb search API."""

    api_key: str
    base_url: str
    timeout_seconds: float

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.themoviedb.org/3",
        timeout_seconds: float = 8.0,
    ) -> None:
        """Initialize client.

        :param api_key: TMDb API key.
        :param base_url: TMDb API base URL.
        :param timeout_seconds: Request timeout in seconds.
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def search_movie(self, title: str, year: int | None = None) -> ProviderMatch | None:
        """Search TMDb movie by title and optional year.

        :param title: Normalized title.
        :param year: Optional release year.
        :return: Provider match when found.
        """
        self.log.debug(
            "Searching TMDb for movie",
            extra={"extra": {"title": title, "year": year}},
        )
        params: dict[str, str | int] = {
            "api_key": self.api_key,
            "query": title,
        }
        if year is not None:
            params["year"] = year

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response: httpx.Response = client.get(
                    f"{self.base_url}/search/movie", params=params
                )
                response.raise_for_status()
                payload: Any = response.json()
        except httpx.HTTPError as e:
            self.log.warning(
                "TMDb movie search failed",
                extra={"extra": {"title": title, "error": str(e)}},
            )
            return None

        results: Any = payload.get("results", []) if isinstance(payload, dict) else []
        if not isinstance(results, list) or len(results) == 0:
            self.log.debug(
                "TMDb movie search returned no results",
                extra={"extra": {"title": title}},
            )
            return None

        first_result: Any = results[0]
        tmdb_id: Any = first_result.get("id") if isinstance(first_result, dict) else None
        if tmdb_id is None:
            return None

        self.log.debug(
            "TMDb movie search found match",
            extra={"extra": {"title": title, "tmdb_id": tmdb_id}},
        )
        return ProviderMatch(
            provider=PROVIDER_TMDB,
            provider_id=str(tmdb_id),
            confidence=0.9,
            reason="tmdb_search_movie",
            lookup_key="",
        )

    def search_tv_series(self, title: str) -> ProviderMatch | None:
        """Search TMDb TV series by title.

        :param title: Normalized title.
        :return: Provider match when found.
        """
        self.log.debug(
            "Searching TMDb for TV series",
            extra={"extra": {"title": title}},
        )
        params: dict[str, str] = {
            "api_key": self.api_key,
            "query": title,
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response: httpx.Response = client.get(f"{self.base_url}/search/tv", params=params)
                response.raise_for_status()
                payload: Any = response.json()
        except httpx.HTTPError as e:
            self.log.warning(
                "TMDb TV series search failed",
                extra={"extra": {"title": title, "error": str(e)}},
            )
            return None

        results: Any = payload.get("results", []) if isinstance(payload, dict) else []
        if not isinstance(results, list) or len(results) == 0:
            self.log.debug(
                "TMDb TV series search returned no results",
                extra={"extra": {"title": title}},
            )
            return None

        first_result: Any = results[0]
        tmdb_id: Any = first_result.get("id") if isinstance(first_result, dict) else None
        if tmdb_id is None:
            return None

        self.log.debug(
            "TMDb TV series search found match",
            extra={"extra": {"title": title, "tmdb_id": tmdb_id}},
        )
        return ProviderMatch(
            provider=PROVIDER_TMDB,
            provider_id=str(tmdb_id),
            confidence=0.88,
            reason="tmdb_search_tv",
            lookup_key="",
        )


class TvdbClient(LoggingMixin):
    """Client for TVDB search API using API key login."""

    api_key: str
    base_url: str
    timeout_seconds: float

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api4.thetvdb.com/v4",
        timeout_seconds: float = 8.0,
    ) -> None:
        """Initialize client.

        :param api_key: TVDB API key.
        :param base_url: TVDB API base URL.
        :param timeout_seconds: Request timeout in seconds.
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def search_tv_series(self, title: str) -> ProviderMatch | None:
        """Search TVDB series by title.

        :param title: Normalized title.
        :return: Provider match when found.
        """
        self.log.debug(
            "Searching TVDB for TV series",
            extra={"extra": {"title": title}},
        )
        token: str | None = self._login()
        if token is None:
            self.log.debug(
                "TVDB authentication failed",
                extra={"extra": {"title": title}},
            )
            return None

        headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
        params: dict[str, str] = {"query": title, "type": "series"}

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response: httpx.Response = client.get(
                    f"{self.base_url}/search", headers=headers, params=params
                )
                response.raise_for_status()
                payload: Any = response.json()
        except httpx.HTTPError as e:
            self.log.warning(
                "TVDB TV series search failed",
                extra={"extra": {"title": title, "error": str(e)}},
            )
            return None

        data: Any = payload.get("data", []) if isinstance(payload, dict) else []
        if not isinstance(data, list) or len(data) == 0:
            self.log.debug(
                "TVDB TV series search returned no results",
                extra={"extra": {"title": title}},
            )
            return None

        first_item: Any = data[0]
        series_id: Any = first_item.get("tvdb_id") if isinstance(first_item, dict) else None
        if series_id is None and isinstance(first_item, dict):
            series_id = first_item.get("id")
        if series_id is None:
            return None

        self.log.debug(
            "TVDB TV series search found match",
            extra={"extra": {"title": title, "tvdb_id": series_id}},
        )
        return ProviderMatch(
            provider=PROVIDER_TVDB,
            provider_id=str(series_id),
            confidence=0.82,
            reason="tvdb_search_series",
            lookup_key="",
        )

    def _login(self) -> str | None:
        """Login and return bearer token.

        :return: Token string or ``None``.
        """
        self.log.debug(
            "Authenticating with TVDB",
            extra={"extra": {}},
        )
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response: httpx.Response = client.post(
                    f"{self.base_url}/login",
                    json={"apikey": self.api_key},
                )
                if response.status_code >= 400:
                    self.log.warning(
                        "TVDB authentication failed",
                        extra={"extra": {"status_code": response.status_code}},
                    )
                    return None
                payload: Any = response.json()
        except httpx.HTTPError as e:
            self.log.warning(
                "TVDB authentication request failed",
                extra={"extra": {"error": str(e)}},
            )
            return None

        data: Any = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            return None

        token: Any = data.get("token")
        if not isinstance(token, str) or token.strip() == "":
            return None

        self.log.debug(
            "TVDB authentication successful",
            extra={"extra": {}},
        )
        return token
