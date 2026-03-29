"""Tests for application settings module."""

from __future__ import annotations

from pathlib import Path

import pytest

from jellyfin_media_normalizer.settings import Settings, _optional_env, _parse_bool


class TestParseBool:
    """Tests for the :func:`_parse_bool` helper."""

    @pytest.mark.parametrize(
        "value",
        ["1", "true", "yes", "on", "TRUE", "YES", "ON", "True", "  true  ", "  1  "],
    )
    def test_truthy_values_return_true(self, value: str) -> None:
        """Return ``True`` for all recognized truthy representations.

        :param value: Raw input value to evaluate.
        """
        assert _parse_bool(value) is True

    @pytest.mark.parametrize(
        "value",
        ["0", "false", "no", "off", "FALSE", "NO", "OFF", "False", "", "  ", "random", "2", "nope"],
    )
    def test_falsy_values_return_false(self, value: str) -> None:
        """Return ``False`` for all unrecognized or falsy representations.

        :param value: Raw input value to evaluate.
        """
        assert _parse_bool(value) is False


class TestOptionalEnv:
    """Tests for the :func:`_optional_env` helper."""

    def test_returns_value_when_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Return the variable value when it is non-empty.

        :param monkeypatch: pytest fixture for environment patching.
        """
        monkeypatch.setenv("TEST_VAR", "my-api-key")
        assert _optional_env("TEST_VAR") == "my-api-key"

    def test_strips_surrounding_whitespace(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Return a stripped value when the variable contains surrounding whitespace.

        :param monkeypatch: pytest fixture for environment patching.
        """
        monkeypatch.setenv("TEST_VAR", "  key  ")
        assert _optional_env("TEST_VAR") == "key"

    @pytest.mark.parametrize("value", ["", "   ", "\t", "\n"])
    def test_returns_none_for_blank_values(
        self,
        monkeypatch: pytest.MonkeyPatch,
        value: str,
    ) -> None:
        """Return ``None`` when the variable is set but blank.

        :param monkeypatch: pytest fixture for environment patching.
        :param value: Blank value to assign to the variable.
        """
        monkeypatch.setenv("TEST_VAR", value)
        assert _optional_env("TEST_VAR") is None

    def test_returns_none_when_not_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Return ``None`` when the variable is absent from the environment.

        :param monkeypatch: pytest fixture for environment patching.
        """
        monkeypatch.delenv("TEST_VAR", raising=False)
        assert _optional_env("TEST_VAR") is None


class TestSettingsFromEnv:
    """Tests for :meth:`Settings.from_env`."""

    def test_defaults_when_no_env_vars_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Use built-in defaults when no environment variables are configured.

        :param monkeypatch: pytest fixture for environment patching.
        """
        for var in (
            "JMN_APP_NAME",
            "JMN_LIBRARY_PATH",
            "JMN_WORKSPACE_PATH",
            "JMN_CACHE_PATH",
            "JMN_REPORTS_PATH",
            "JMN_MANIFESTS_PATH",
            "JMN_LOGS_PATH",
            "JMN_LOG_LEVEL",
            "JMN_LOG_FORMAT",
            "JMN_DRY_RUN",
            "JMN_TMDB_API_KEY",
            "JMN_TVDB_API_KEY",
        ):
            monkeypatch.delenv(var, raising=False)

        settings: Settings = Settings.from_env()

        assert settings.app_name == "jellyfin-media-normalizer"
        assert settings.library_path == Path("./data/library")
        assert settings.workspace_path == Path("./data/workspace")
        assert settings.cache_path == Path("./data/workspace/cache")
        assert settings.reports_path == Path("./data/workspace/reports")
        assert settings.manifests_path == Path("./data/workspace/manifests")
        assert settings.logs_path == Path("./data/workspace/logs")
        assert settings.log_level == "INFO"
        assert settings.log_format == "text"
        assert settings.dry_run is True
        assert settings.tmdb_api_key is None
        assert settings.tvdb_api_key is None

    @pytest.mark.parametrize(
        ("env_var", "env_value", "attr", "expected"),
        [
            ("JMN_APP_NAME", "my-app", "app_name", "my-app"),
            ("JMN_LIBRARY_PATH", "/media/movies", "library_path", Path("/media/movies")),
            ("JMN_LOG_LEVEL", "debug", "log_level", "DEBUG"),
            ("JMN_LOG_FORMAT", "JSON", "log_format", "json"),
        ],
    )
    def test_individual_env_vars_override_defaults(
        self,
        monkeypatch: pytest.MonkeyPatch,
        env_var: str,
        env_value: str,
        attr: str,
        expected: object,
    ) -> None:
        """Override each default with a corresponding environment variable.

        :param monkeypatch: pytest fixture for environment patching.
        :param env_var: Environment variable name to set.
        :param env_value: Value to assign to the variable.
        :param attr: Settings attribute to inspect.
        :param expected: Expected attribute value after parsing.
        """
        monkeypatch.setenv(env_var, env_value)
        settings: Settings = Settings.from_env()
        assert getattr(settings, attr) == expected

    @pytest.mark.parametrize(
        ("dry_run_value", "expected"),
        [
            ("true", True),
            ("True", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("0", False),
            ("no", False),
            ("off", False),
        ],
    )
    def test_dry_run_env_var_parsing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        dry_run_value: str,
        expected: bool,
    ) -> None:
        """Parse the ``JMN_DRY_RUN`` variable as a boolean correctly.

        :param monkeypatch: pytest fixture for environment patching.
        :param dry_run_value: Raw string value for dry-run env var.
        :param expected: Expected parsed boolean result.
        """
        monkeypatch.setenv("JMN_DRY_RUN", dry_run_value)
        settings: Settings = Settings.from_env()
        assert settings.dry_run is expected

    def test_workspace_derived_paths_use_custom_workspace(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Derive sub-paths from ``JMN_WORKSPACE_PATH`` when no overrides are set.

        :param monkeypatch: pytest fixture for environment patching.
        """
        monkeypatch.setenv("JMN_WORKSPACE_PATH", "/data/ws")
        for var in ("JMN_CACHE_PATH", "JMN_REPORTS_PATH", "JMN_MANIFESTS_PATH", "JMN_LOGS_PATH"):
            monkeypatch.delenv(var, raising=False)

        settings: Settings = Settings.from_env()

        assert settings.cache_path == Path("/data/ws/cache")
        assert settings.reports_path == Path("/data/ws/reports")
        assert settings.manifests_path == Path("/data/ws/manifests")
        assert settings.logs_path == Path("/data/ws/logs")

    def test_sub_paths_can_be_overridden_independently(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Allow each sub-path to be set independently of workspace path.

        :param monkeypatch: pytest fixture for environment patching.
        """
        monkeypatch.setenv("JMN_WORKSPACE_PATH", "/data/ws")
        monkeypatch.setenv("JMN_CACHE_PATH", "/tmp/cache")

        settings: Settings = Settings.from_env()

        assert settings.cache_path == Path("/tmp/cache")
        assert settings.reports_path == Path("/data/ws/reports")

    @pytest.mark.parametrize(
        ("api_key_var", "attr"),
        [
            ("JMN_TMDB_API_KEY", "tmdb_api_key"),
            ("JMN_TVDB_API_KEY", "tvdb_api_key"),
        ],
    )
    def test_api_key_set_when_provided(
        self,
        monkeypatch: pytest.MonkeyPatch,
        api_key_var: str,
        attr: str,
    ) -> None:
        """Return API key value when environment variable is non-empty.

        :param monkeypatch: pytest fixture for environment patching.
        :param api_key_var: Name of the API key environment variable.
        :param attr: Settings attribute to inspect.
        """
        monkeypatch.setenv(api_key_var, "secret-key-123")
        settings: Settings = Settings.from_env()
        assert getattr(settings, attr) == "secret-key-123"

    @pytest.mark.parametrize(
        ("api_key_var", "attr"),
        [
            ("JMN_TMDB_API_KEY", "tmdb_api_key"),
            ("JMN_TVDB_API_KEY", "tvdb_api_key"),
        ],
    )
    def test_api_key_none_when_absent_or_blank(
        self,
        monkeypatch: pytest.MonkeyPatch,
        api_key_var: str,
        attr: str,
    ) -> None:
        """Return ``None`` for API key when variable is absent or empty.

        :param monkeypatch: pytest fixture for environment patching.
        :param api_key_var: Name of the API key environment variable.
        :param attr: Settings attribute to inspect.
        """
        monkeypatch.delenv(api_key_var, raising=False)
        settings: Settings = Settings.from_env()
        assert getattr(settings, attr) is None

        monkeypatch.setenv(api_key_var, "  ")
        settings = Settings.from_env()
        assert getattr(settings, attr) is None


class TestSettingsEnsureDirectories:
    """Tests for :meth:`Settings.ensure_directories`."""

    def test_creates_all_required_directories(self, tmp_path: Path) -> None:
        """Create all workspace directories when they do not yet exist.

        :param tmp_path: pytest built-in temporary directory fixture.
        """
        ws: Path = tmp_path / "workspace"
        settings = Settings(
            app_name="test",
            library_path=tmp_path / "library",
            workspace_path=ws,
            cache_path=ws / "cache",
            reports_path=ws / "reports",
            manifests_path=ws / "manifests",
            logs_path=ws / "logs",
            log_level="INFO",
            log_format="text",
            dry_run=True,
            tmdb_api_key=None,
            tvdb_api_key=None,
            provider_lookup_progress_interval=100,
        )

        settings.ensure_directories()

        assert ws.is_dir()
        assert (ws / "cache").is_dir()
        assert (ws / "reports").is_dir()
        assert (ws / "manifests").is_dir()
        assert (ws / "logs").is_dir()

    def test_idempotent_when_directories_already_exist(self, tmp_path: Path) -> None:
        """Not raise an error when directories already exist.

        :param tmp_path: pytest built-in temporary directory fixture.
        """
        ws: Path = tmp_path / "workspace"
        ws.mkdir(parents=True)

        settings = Settings(
            app_name="test",
            library_path=tmp_path / "library",
            workspace_path=ws,
            cache_path=ws / "cache",
            reports_path=ws / "reports",
            manifests_path=ws / "manifests",
            logs_path=ws / "logs",
            log_level="INFO",
            log_format="text",
            dry_run=True,
            tmdb_api_key=None,
            tvdb_api_key=None,
            provider_lookup_progress_interval=100,
        )

        settings.ensure_directories()
        settings.ensure_directories()  # second call must not raise

        assert (ws / "cache").is_dir()

    @pytest.mark.parametrize(
        "attr",
        ["workspace_path", "cache_path", "reports_path", "manifests_path", "logs_path"],
    )
    def test_each_directory_is_created(self, tmp_path: Path, attr: str) -> None:
        """Verify that each individual directory is created by ensure_directories.

        :param tmp_path: pytest built-in temporary directory fixture.
        :param attr: Settings attribute name of the directory to verify.
        """
        ws: Path = tmp_path / "workspace"
        settings = Settings(
            app_name="test",
            library_path=tmp_path / "library",
            workspace_path=ws,
            cache_path=ws / "cache",
            reports_path=ws / "reports",
            manifests_path=ws / "manifests",
            logs_path=ws / "logs",
            log_level="INFO",
            log_format="text",
            dry_run=True,
            tmdb_api_key=None,
            tvdb_api_key=None,
            provider_lookup_progress_interval=100,
        )

        settings.ensure_directories()

        assert getattr(settings, attr).is_dir()
