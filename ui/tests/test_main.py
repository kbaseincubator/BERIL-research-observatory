"""Unit tests for app.main - filters and HTTP routes."""

import hashlib
import hmac
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app, generate_base_context

# ---------------------------------------------------------------------------
# HTTP Routes via TestClient
# ---------------------------------------------------------------------------


@pytest.fixture
async def client(repository_data, app_data_context, db_session):
    """TestClient with injected repository data, no lifespan startup.

    Uses the shared in-memory db_session (which already has all tables created)
    so that routes that query the DB don't fail with 'no such table'.
    """
    from collections.abc import AsyncGenerator
    from app.db.session import get_db, init_db, close_db

    # init_db populates the module-level engine so check_db() works in /health
    await init_db("sqlite+aiosqlite:///:memory:")

    with patch.dict(os.environ, {"BERIL_TEST_SKIP_LIFESPAN": "True"}):
        app = create_app()

        async def override_get_db() -> AsyncGenerator:
            yield db_session

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app, raise_server_exceptions=True) as c:
            app.state.repo_data = repository_data
            app.state.base_context = app_data_context
            yield c
        app.dependency_overrides.pop(get_db, None)
    await close_db()


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        print(response.json())
        assert response.json().get("status") == "healthy"


class TestHomeRoute:
    def test_home_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_home_is_html(self, client):
        response = client.get("/")
        assert "text/html" in response.headers.get("content-type", "")


class TestProjectsListRoute:
    def test_projects_list_200(self, client):
        response = client.get("/projects")
        assert response.status_code == 200

    def test_projects_sort_alpha(self, client):
        response = client.get("/projects?sort=alpha")
        assert response.status_code == 200

    def test_projects_sort_alpha_asc(self, client):
        response = client.get("/projects?sort=alpha&dir=asc")
        assert response.status_code == 200

    def test_projects_sort_alpha_desc(self, client):
        response = client.get("/projects?sort=alpha&dir=desc")
        assert response.status_code == 200

    def test_projects_sort_status(self, client):
        response = client.get("/projects?sort=status")
        assert response.status_code == 200

    def test_projects_sort_author(self, client):
        response = client.get("/projects?sort=author")
        assert response.status_code == 200

    def test_projects_sort_recent_asc(self, client):
        response = client.get("/projects?sort=recent&dir=asc")
        assert response.status_code == 200


class TestProjectDetailRoute:
    def test_existing_project_returns_200(self, client):
        response = client.get("/projects/test_project")
        assert response.status_code == 200

    def test_missing_project_returns_404(self, client):
        response = client.get("/projects/nonexistent_project")
        assert response.status_code == 404

    def test_markdown_file_redirects(self, client):
        response = client.get(
            "/projects/test_project/README.md", follow_redirects=False
        )
        assert response.status_code == 302
        assert response.headers["location"] == "/projects/test_project"

    def test_non_md_file_returns_404(self, client):
        response = client.get("/projects/test_project/somefile.txt")
        assert response.status_code == 404


class TestCollectionsRoute:
    def test_collections_overview_200(self, client):
        response = client.get("/collections")
        assert response.status_code == 200
        assert "KBase" in response.text
        assert "kbase_ke_pangenome" in response.text

    def test_collection_detail_200(self, client):
        response = client.get("/collections/kbase_ke_pangenome")
        assert response.status_code == 200
        assert "Schema status" in response.text
        assert "Atlas Pages" in response.text

    def test_collection_detail_404_for_missing(self, client):
        response = client.get("/collections/nonexistent_collection")
        assert response.status_code == 404


class TestLegacyRedirects:
    def test_data_redirects_to_collections(self, client):
        response = client.get("/data", follow_redirects=False)
        assert response.status_code == 301
        assert response.headers["location"] == "/collections"

    def test_schema_redirects_to_pangenome(self, client):
        response = client.get("/data/schema", follow_redirects=False)
        assert response.status_code == 301
        assert "kbase_ke_pangenome" in response.headers["location"]


class TestKnowledgeRoutes:
    def test_discoveries_200(self, client):
        response = client.get("/knowledge/discoveries")
        assert response.status_code == 200

    def test_pitfalls_200(self, client):
        response = client.get("/knowledge/pitfalls")
        assert response.status_code == 200

    def test_performance_200(self, client):
        response = client.get("/knowledge/performance")
        assert response.status_code == 200

    def test_ideas_200(self, client):
        response = client.get("/knowledge/ideas")
        assert response.status_code == 200


class TestAtlasRoutes:
    def test_atlas_landing_200(self, client):
        response = client.get("/atlas")
        assert response.status_code == 200
        assert "BERIL Atlas" in response.text
        assert "Metrics To Watch" in response.text
        assert "Collection coverage" in response.text
        assert "Phase 0 Agent-Built Wiki Atlas" not in response.text

    def test_legacy_wiki_redirects_to_atlas(self, client):
        response = client.get("/wiki", follow_redirects=False)
        assert response.status_code == 301
        assert response.headers["location"] == "/atlas"

    def test_atlas_section_indexes_200(self, client):
        for path in ("/atlas/topics", "/atlas/data", "/atlas/claims", "/atlas/directions", "/atlas/hypotheses"):
            response = client.get(path)
            assert response.status_code == 200

    def test_existing_atlas_page_200(self, client):
        response = client.get("/atlas/topics/test")
        assert response.status_code == 200
        assert "Test Atlas Topic" in response.text
        assert "On This Page" in response.text
        assert "/projects/test_project" in response.text
        assert "/collections/kbase_ke_pangenome" in response.text

    def test_legacy_wiki_page_redirects(self, client):
        response = client.get("/wiki/topics/test", follow_redirects=False)
        assert response.status_code == 301
        assert response.headers["location"] == "/atlas/topics/test"

    def test_missing_atlas_page_404(self, client):
        response = client.get("/atlas/topics/missing")
        assert response.status_code == 404


class TestCommunityRoutes:
    def test_contributors_200(self, client):
        response = client.get("/community/contributors")
        assert response.status_code == 200


class TestCoScientistRoute:
    def test_co_scientist_200(self, client):
        response = client.get("/co-scientist")
        assert response.status_code == 200

    def test_skills_200(self, client):
        response = client.get("/skills")
        assert response.status_code == 200


class TestAboutRoute:
    def test_about_200(self, client):
        response = client.get("/about")
        assert response.status_code == 200


class TestResearchAreasRoute:
    def test_research_areas_200(self, client):
        response = client.get("/research-areas")
        assert response.status_code == 200


class TestNotebookViewerRoute:
    def test_missing_project_returns_404(self, client):
        response = client.get("/projects/nonexistent/notebooks/analysis.ipynb")
        assert response.status_code == 404

    def test_missing_notebook_returns_404(self, client):
        response = client.get("/projects/test_project/notebooks/nonexistent.ipynb")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Webhook endpoint
# ---------------------------------------------------------------------------


class TestWebhookEndpoint:
    def test_no_repo_configured_returns_400(self, client):
        mock_settings = Settings()
        mock_settings.data_repo_url = None
        mock_settings.webhook_secret = None

        with patch("app.main.get_settings", return_value=mock_settings):
            response = client.post(
                "/api/webhook/data-update",
                content=b"{}",
            )
            assert response.status_code == 400

    def test_missing_signature_with_secret_returns_401(self, client):
        mock_settings = Settings()
        mock_settings.webhook_secret = "mysecret"
        mock_settings.data_repo_url = "http://example.com/repo"
        mock_settings.data_repo_path = MagicMock()
        mock_settings.data_repo_branch = "data-cache"

        with patch("app.main.get_settings", return_value=mock_settings):
            response = client.post(
                "/api/webhook/data-update",
                content=b"{}",
            )
        assert response.status_code == 401

    def test_invalid_signature_returns_401(self, client):
        mock_settings = Settings()
        mock_settings.webhook_secret = "mysecret"
        mock_settings.data_repo_url = "http://example.com/repo"
        mock_settings.data_repo_path = MagicMock()
        mock_settings.data_repo_branch = "data-cache"

        with patch("app.main.get_settings", return_value=mock_settings):
            response = client.post(
                "/api/webhook/data-update",
                content=b"{}",
                headers={"x-webhook-signature": "badsignature"},
            )
        assert response.status_code == 401

    def test_valid_signature_triggers_reload(self, client, repository_data):
        secret = "mysecret"
        body = b"{}"
        expected_sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

        mock_settings = Settings()
        mock_settings.webhook_secret = secret
        mock_settings.data_repo_url = "http://example.com/repo"
        mock_settings.data_repo_path = MagicMock()
        mock_settings.data_repo_branch = "data-cache"

        with (
            patch("app.main.get_settings", return_value=mock_settings),
            patch("app.main.pull_latest", new_callable=AsyncMock),
            patch("app.main.load_repository_data", return_value=repository_data),
        ):
            response = client.post(
                "/api/webhook/data-update",
                content=body,
                headers={"x-webhook-signature": expected_sig},
            )
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_valid_webhook_updates_repo_data(self, client, repository_data):
        """After a successful webhook, app.state.repo_data is replaced."""
        secret = "mysecret"
        body = b"{}"
        expected_sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

        mock_settings = Settings()
        mock_settings.webhook_secret = secret
        mock_settings.data_repo_url = "http://example.com/repo"
        mock_settings.data_repo_path = MagicMock()
        mock_settings.data_repo_branch = "data-cache"

        new_repo_data = MagicMock()
        new_repo_data.last_updated = datetime(2025, 1, 1)

        with (
            patch("app.main.get_settings", return_value=mock_settings),
            patch("app.main.pull_latest", new_callable=AsyncMock),
            patch("app.main.load_repository_data", return_value=new_repo_data),
        ):
            response = client.post(
                "/api/webhook/data-update",
                content=body,
                headers={"x-webhook-signature": expected_sig},
            )

        assert response.status_code == 200
        assert client.app.state.repo_data is new_repo_data

    def test_valid_webhook_updates_base_context(self, client, repository_data):
        """After a successful webhook, app.state.base_context reflects the new data."""
        secret = "mysecret"
        body = b"{}"
        expected_sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

        mock_settings = Settings()
        mock_settings.webhook_secret = secret
        mock_settings.data_repo_url = "http://example.com/repo"
        mock_settings.data_repo_path = MagicMock()
        mock_settings.data_repo_branch = "data-cache"

        new_repo_data = MagicMock()
        new_repo_data.last_updated = datetime(2025, 1, 1)
        new_repo_data.projects = [MagicMock(), MagicMock(), MagicMock()]
        new_repo_data.discoveries = [MagicMock()]
        new_repo_data.research_ideas = []
        new_repo_data.collections = [MagicMock(), MagicMock()]
        new_repo_data.contributors = [MagicMock()]
        new_repo_data.skills = [MagicMock(), MagicMock()]

        with (
            patch("app.main.get_settings", return_value=mock_settings),
            patch("app.main.pull_latest", new_callable=AsyncMock),
            patch("app.main.load_repository_data", return_value=new_repo_data),
        ):
            response = client.post(
                "/api/webhook/data-update",
                content=body,
                headers={"x-webhook-signature": expected_sig},
            )

        assert response.status_code == 200
        ctx = client.app.state.base_context
        assert ctx["project_count"] == 3
        assert ctx["discovery_count"] == 1
        assert ctx["idea_count"] == 0
        assert ctx["collection_count"] == 2
        assert ctx["contributor_count"] == 1
        assert ctx["skill_count"] == 2
        assert ctx["last_updated"] == datetime(2025, 1, 1)


# ---------------------------------------------------------------------------
# generate_base_context unit tests
# ---------------------------------------------------------------------------


class TestGetBaseContext:
    def test_counts_match_repo_data(self, repository_data):
        settings = Settings()
        ctx = generate_base_context(settings, repository_data)
        assert ctx["project_count"] == len(repository_data.projects)
        assert ctx["discovery_count"] == len(repository_data.discoveries)
        assert ctx["idea_count"] == len(repository_data.research_ideas)
        assert ctx["collection_count"] == len(repository_data.collections)
        assert ctx["contributor_count"] == len(repository_data.contributors)
        assert ctx["skill_count"] == len(repository_data.skills)

    def test_last_updated_matches_repo_data(self, repository_data):
        settings = Settings()
        ctx = generate_base_context(settings, repository_data)
        assert ctx["last_updated"] == repository_data.last_updated

    def test_counts_update_when_repo_data_changes(self, repository_data, project):
        import dataclasses

        settings = Settings()
        ctx_before = generate_base_context(settings, repository_data)

        updated = dataclasses.replace(
            repository_data, projects=repository_data.projects + [project]
        )
        ctx_after = generate_base_context(settings, updated)

        assert ctx_after["project_count"] == ctx_before["project_count"] + 1
