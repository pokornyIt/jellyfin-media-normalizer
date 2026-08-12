"""Provider ID match model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ProviderMatch:
    """Represent a resolved provider identifier for a media title.

    :param provider: Provider name (for example ``tmdb`` or ``tvdb``).
    :param provider_id: Provider-specific identifier value.
    :param confidence: Confidence score for the selected provider ID.
    :param reason: Short explanation of how the provider ID was selected.
    :param lookup_key: Canonical lookup key used for the resolution.
    """

    provider: str
    provider_id: str
    confidence: float
    reason: str
    lookup_key: str
