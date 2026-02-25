"""Unit tests for app.config.Settings."""

from pathlib import Path

from app.config import Settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_settings(**env_overrides) -> Settings:
    """Instantiate a fresh Settings object with explicit field overrides.

    pydantic-settings reads from the environment at construction time, so we
    pass overrides directly as constructor kwargs to avoid needing to mutate
    os.environ in most tests.
    """
    return Settings(**env_overrides)


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------


class TestDefaults:
    def test_app_name_default(self):
        s = make_settings()
        assert s.app_name == "Microbial Discovery Forge"

    def test_app_description_default(self):
        s = make_settings()
        assert "BERDL" in s.app_description

    def test_debug_default_false(self):
        s = make_settings()
        assert s.debug is False

    def test_total_genomes_default(self):
        s = make_settings()
        assert s.total_genomes == 293_059

    def test_total_species_default(self):
        s = make_settings()
        assert s.total_species == 27_000

    def test_total_genes_default(self):
        s = make_settings()
        assert s.total_genes == "1B+"

    def test_data_repo_url_default_none(self):
        s = make_settings()
        assert s.data_repo_url is None

    def test_data_repo_branch_default(self):
        s = make_settings()
        assert s.data_repo_branch == "data-cache"

    def test_data_repo_path_default(self):
        s = make_settings()
        assert s.data_repo_path == Path("/tmp/beril_data_cache")

    def test_webhook_secret_default_none(self):
        s = make_settings()
        assert s.webhook_secret is None


# ---------------------------------------------------------------------------
# Path defaults (app_dir, ui_dir, repo_dir)
# ---------------------------------------------------------------------------


class TestDefaultPaths:
    def test_app_dir_points_to_app_package(self):
        s = make_settings()
        # app_dir should be the directory containing config.py
        assert s.app_dir.name == "app"
        assert (s.app_dir / "config.py").exists()

    def test_ui_dir_is_parent_of_app_dir(self):
        s = make_settings()
        assert s.ui_dir == s.app_dir.parent

    def test_repo_dir_is_parent_of_ui_dir(self):
        s = make_settings()
        assert s.repo_dir == s.ui_dir.parent

    def test_repo_dir_contains_projects(self):
        """repo_dir should be the repository root, which has a projects/ folder."""
        s = make_settings()
        assert (s.repo_dir / "projects").exists()


# ---------------------------------------------------------------------------
# Derived path properties
# ---------------------------------------------------------------------------


class TestDerivedPaths:
    def test_projects_dir(self):
        s = make_settings()
        assert s.projects_dir == s.repo_dir / "projects"

    def test_docs_dir(self):
        s = make_settings()
        assert s.docs_dir == s.repo_dir / "docs"

    def test_data_dir(self):
        s = make_settings()
        assert s.data_dir == s.repo_dir / "data"

    def test_templates_dir(self):
        s = make_settings()
        assert s.templates_dir == s.app_dir / "templates"

    def test_static_dir(self):
        s = make_settings()
        assert s.static_dir == s.app_dir / "static"

    def test_cache_dir(self):
        s = make_settings()
        assert s.cache_dir == s.ui_dir / "data"

    def test_cache_file(self):
        s = make_settings()
        assert s.cache_file == s.cache_dir / "cache.json"

    def test_search_index_dir(self):
        s = make_settings()
        assert s.search_index_dir == s.cache_dir / "indexdir"

    def test_derived_paths_are_path_objects(self):
        s = make_settings()
        for prop in (
            s.projects_dir,
            s.docs_dir,
            s.data_dir,
            s.templates_dir,
            s.static_dir,
            s.cache_dir,
            s.cache_file,
            s.search_index_dir,
        ):
            assert isinstance(prop, Path), f"{prop!r} is not a Path"

    def test_derived_paths_are_absolute(self):
        s = make_settings()
        for prop in (
            s.projects_dir,
            s.docs_dir,
            s.data_dir,
            s.templates_dir,
            s.static_dir,
            s.cache_dir,
            s.cache_file,
            s.search_index_dir,
        ):
            assert prop.is_absolute(), f"{prop!r} is not absolute"


# ---------------------------------------------------------------------------
# Loading values from constructor kwargs (simulates env-var overrides)
# ---------------------------------------------------------------------------


class TestFieldOverrides:
    def test_override_app_name(self):
        s = make_settings(app_name="My Custom App")
        assert s.app_name == "My Custom App"

    def test_override_debug(self):
        s = make_settings(debug=True)
        assert s.debug is True

    def test_override_total_genomes(self):
        s = make_settings(total_genomes=500_000)
        assert s.total_genomes == 500_000

    def test_override_total_species(self):
        s = make_settings(total_species=50_000)
        assert s.total_species == 50_000

    def test_override_total_genes(self):
        s = make_settings(total_genes="2B+")
        assert s.total_genes == "2B+"

    def test_override_data_repo_url(self):
        s = make_settings(data_repo_url="https://github.com/org/repo.git")
        assert s.data_repo_url == "https://github.com/org/repo.git"

    def test_override_data_repo_branch(self):
        s = make_settings(data_repo_branch="main")
        assert s.data_repo_branch == "main"

    def test_override_data_repo_path(self):
        s = make_settings(data_repo_path=Path("/custom/path"))
        assert s.data_repo_path == Path("/custom/path")

    def test_override_webhook_secret(self):
        s = make_settings(webhook_secret="supersecret")
        assert s.webhook_secret == "supersecret"

    def test_override_does_not_affect_other_fields(self):
        s = make_settings(app_name="Custom")
        assert s.debug is False
        assert s.total_genomes == 293_059


# ---------------------------------------------------------------------------
# Loading from environment variables (BERIL_ prefix)
# ---------------------------------------------------------------------------


class TestEnvironmentVariables:
    def test_beril_prefix_app_name(self, monkeypatch):
        monkeypatch.setenv("BERIL_APP_NAME", "Env App Name")
        s = Settings()
        assert s.app_name == "Env App Name"

    def test_beril_prefix_debug_true(self, monkeypatch):
        monkeypatch.setenv("BERIL_DEBUG", "true")
        s = Settings()
        assert s.debug is True

    def test_beril_prefix_debug_false(self, monkeypatch):
        monkeypatch.setenv("BERIL_DEBUG", "false")
        s = Settings()
        assert s.debug is False

    def test_beril_prefix_data_repo_url(self, monkeypatch):
        monkeypatch.setenv("BERIL_DATA_REPO_URL", "https://example.com/repo.git")
        s = Settings()
        assert s.data_repo_url == "https://example.com/repo.git"

    def test_beril_prefix_data_repo_branch(self, monkeypatch):
        monkeypatch.setenv("BERIL_DATA_REPO_BRANCH", "my-branch")
        s = Settings()
        assert s.data_repo_branch == "my-branch"

    def test_beril_prefix_data_repo_path(self, monkeypatch, tmp_path):
        monkeypatch.setenv("BERIL_DATA_REPO_PATH", str(tmp_path))
        s = Settings()
        assert s.data_repo_path == tmp_path

    def test_beril_prefix_webhook_secret(self, monkeypatch):
        monkeypatch.setenv("BERIL_WEBHOOK_SECRET", "env-secret")
        s = Settings()
        assert s.webhook_secret == "env-secret"

    def test_beril_prefix_total_genomes(self, monkeypatch):
        monkeypatch.setenv("BERIL_TOTAL_GENOMES", "999999")
        s = Settings()
        assert s.total_genomes == 999_999

    def test_beril_prefix_total_species(self, monkeypatch):
        monkeypatch.setenv("BERIL_TOTAL_SPECIES", "12345")
        s = Settings()
        assert s.total_species == 12_345

    def test_unprefixed_var_is_ignored(self, monkeypatch):
        """Variables without BERIL_ prefix should not be loaded."""
        monkeypatch.setenv("APP_NAME", "Should Not Load")
        s = Settings()
        assert s.app_name == "Microbial Discovery Forge"

    def test_env_overrides_class_default(self, monkeypatch):
        """An environment variable takes precedence over the class-level default."""
        monkeypatch.setenv("BERIL_DATA_REPO_BRANCH", "env-branch")
        s = Settings()
        assert s.data_repo_branch == "env-branch"

    def test_env_cleared_restores_default(self, monkeypatch):
        """Once the env var is gone, the default is used again."""
        monkeypatch.setenv("BERIL_DATA_REPO_BRANCH", "temp-branch")
        s1 = Settings()
        assert s1.data_repo_branch == "temp-branch"

        monkeypatch.delenv("BERIL_DATA_REPO_BRANCH")
        s2 = Settings()
        assert s2.data_repo_branch == "data-cache"


# ---------------------------------------------------------------------------
# Type coercion
# ---------------------------------------------------------------------------


class TestTypeCoercion:
    def test_total_genomes_is_int(self):
        s = make_settings()
        assert isinstance(s.total_genomes, int)

    def test_total_species_is_int(self):
        s = make_settings()
        assert isinstance(s.total_species, int)

    def test_debug_is_bool(self):
        s = make_settings()
        assert isinstance(s.debug, bool)

    def test_data_repo_path_is_path(self):
        s = make_settings()
        assert isinstance(s.data_repo_path, Path)

    def test_app_dir_is_path(self):
        s = make_settings()
        assert isinstance(s.app_dir, Path)

    def test_string_path_coerced_to_path_via_env(self, monkeypatch):
        monkeypatch.setenv("BERIL_DATA_REPO_PATH", "/some/path")
        s = Settings()
        assert isinstance(s.data_repo_path, Path)
        assert s.data_repo_path == Path("/some/path")

    def test_integer_string_coerced_via_env(self, monkeypatch):
        monkeypatch.setenv("BERIL_TOTAL_GENOMES", "42")
        s = Settings()
        assert s.total_genomes == 42
        assert isinstance(s.total_genomes, int)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------


class TestSettingsSingleton:
    def test_singleton_is_settings_instance(self):
        from app.config import settings
        assert isinstance(settings, Settings)

    def test_singleton_has_correct_app_name(self):
        from app.config import settings
        assert settings.app_name == "Microbial Discovery Forge"

    def test_singleton_debug_is_false(self):
        from app.config import settings
        assert settings.debug is False

    def test_singleton_data_repo_url_is_none(self):
        from app.config import settings
        assert settings.data_repo_url is None

    def test_singleton_webhook_secret_is_none(self):
        from app.config import settings
        assert settings.webhook_secret is None
