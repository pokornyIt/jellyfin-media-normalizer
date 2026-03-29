"""Tests for the MediaType enum."""

from __future__ import annotations

import pytest

from jellyfin_media_normalizer.models.media_type import MediaType


class TestMediaTypeValues:
    """Tests for string values of :class:`MediaType`."""

    @pytest.mark.parametrize(
        ("member", "expected_value"),
        [
            (MediaType.MOVIE, "movie"),
            (MediaType.TV_EPISODE, "tv_episode"),
            (MediaType.UNKNOWN, "unknown"),
        ],
    )
    def test_string_value(self, member: MediaType, expected_value: str) -> None:
        """Each member must expose its canonical string value.

        :param member: The enum member under test.
        :param expected_value: Expected string representation.
        """
        assert member == expected_value
        assert str(member) == expected_value

    def test_all_expected_members_present(self) -> None:
        """Enum must contain exactly the three expected members."""
        names: set[str] = {m.name for m in MediaType}
        assert names == {"MOVIE", "TV_EPISODE", "UNKNOWN"}

    @pytest.mark.parametrize(
        "raw",
        ["movie", "tv_episode", "unknown"],
    )
    def test_constructible_from_string(self, raw: str) -> None:
        """MediaType must be constructible from its string value.

        :param raw: String value used to construct the enum member.
        """
        member: MediaType = MediaType(raw)
        assert isinstance(member, MediaType)
        assert str(member) == raw

    @pytest.mark.parametrize(
        "invalid",
        ["Movie", "MOVIE", "tv episode", "series", "", "film"],
    )
    def test_invalid_string_raises_value_error(self, invalid: str) -> None:
        """Construction from an unrecognized string must raise ValueError.

        :param invalid: Unrecognized string to attempt construction with.
        """
        with pytest.raises(ValueError):
            MediaType(invalid)


class TestMediaTypeIsStrEnum:
    """Tests for StrEnum contract of :class:`MediaType`."""

    def test_is_str_subclass(self) -> None:
        """Each member must be an instance of str."""
        for member in MediaType:
            assert isinstance(member, str)

    @pytest.mark.parametrize(
        ("left", "right"),
        [
            (MediaType.MOVIE, "movie"),
            (MediaType.TV_EPISODE, "tv_episode"),
            (MediaType.UNKNOWN, "unknown"),
        ],
    )
    def test_equality_with_plain_string(self, left: MediaType, right: str) -> None:
        """Each member must compare equal to its plain-string counterpart.

        :param left: The enum member to compare.
        :param right: The plain string expected to be equal.
        """
        assert left == right

    @pytest.mark.parametrize(
        ("a", "b"),
        [
            (MediaType.MOVIE, MediaType.TV_EPISODE),
            (MediaType.MOVIE, MediaType.UNKNOWN),
            (MediaType.TV_EPISODE, MediaType.UNKNOWN),
        ],
    )
    def test_members_are_not_equal_to_each_other(self, a: MediaType, b: MediaType) -> None:
        """Distinct members must not be equal to one another.

        :param a: First enum member.
        :param b: Second enum member.
        """
        assert a != b
