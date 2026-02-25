"""Unit tests for app.main - filters and HTTP routes."""

import hashlib
import hmac
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from markupsafe import Markup

from app.main import (
    markdown_filter,
    markdown_inline_filter,
    slugify_filter,
    strip_images_filter,
    get_base_context,
)
from app.models import (
    CollectionCategory,
    IdeaStatus,
    Project,
    ProjectStatus,
    RepositoryData,
)


# ---------------------------------------------------------------------------
# Filter: markdown_filter
# ---------------------------------------------------------------------------


class TestMarkdownFilter:
    def test_converts_bold(self):
        result = markdown_filter("**bold**")
        assert "<strong>bold</strong>" in result

    def test_converts_heading(self):
        result = markdown_filter("# Heading")
        assert "<h1>" in result

    def test_empty_string(self):
        result = markdown_filter("")
        assert result == Markup("")

    def test_none_value(self):
        result = markdown_filter(None)
        assert result == Markup("")

    def test_returns_markup(self):
        result = markdown_filter("hello")
        assert isinstance(result, Markup)

    def test_fenced_code(self):
        result = markdown_filter("```python\nprint('hi')\n```")
        assert "<code" in result

    def test_table_extension(self):
        result = markdown_filter("| a | b |\n|---|---|\n| 1 | 2 |")
        assert "<table>" in result


# ---------------------------------------------------------------------------
# Filter: markdown_inline_filter
# ---------------------------------------------------------------------------


class TestMarkdownInlineFilter:
    def test_strips_outer_p_tags(self):
        result = markdown_inline_filter("hello world")
        assert not str(result).startswith("<p>")
        assert not str(result).endswith("</p>")

    def test_empty_string(self):
        assert markdown_inline_filter("") == Markup("")

    def test_none_value(self):
        assert markdown_inline_filter(None) == Markup("")

    def test_returns_markup(self):
        result = markdown_inline_filter("test")
        assert isinstance(result, Markup)

    def test_preserves_inline_code(self):
        result = markdown_inline_filter("`code`")
        assert "<code>" in str(result)

    def test_multiline_keeps_inner_structure(self):
        # Multi-paragraph won't be stripped since it's more than one <p>
        result = markdown_inline_filter("line one\n\nline two")
        assert "line" in str(result)


# ---------------------------------------------------------------------------
# Filter: strip_images_filter
# ---------------------------------------------------------------------------


class TestStripImagesFilter:
    def test_strips_image(self):
        result = strip_images_filter("Text ![alt](path/to/img.png) more text")
        assert "![" not in result
        assert "more text" in result

    def test_empty_string(self):
        assert strip_images_filter("") == ""

    def test_none_value(self):
        assert strip_images_filter(None) == ""

    def test_no_image(self):
        text = "Just some text without images."
        assert strip_images_filter(text) == text

    def test_multiple_images(self):
        text = "![a](a.png) text ![b](b.png)"
        result = strip_images_filter(text)
        assert "![" not in result
        assert "text" in result


# ---------------------------------------------------------------------------
# Filter: slugify_filter
# ---------------------------------------------------------------------------


class TestSlugifyFilter:
    def test_basic(self):
        assert slugify_filter("Hello World") == "hello-world"

    def test_empty_string(self):
        assert slugify_filter("") == ""

    def test_none_value(self):
        assert slugify_filter(None) == ""

    def test_special_chars_removed(self):
        result = slugify_filter("Research & Development!")
        assert "&" not in result
        assert "!" not in result

    def test_spaces_become_hyphens(self):
        assert slugify_filter("My Section Title") == "my-section-title"

    def test_underscores_become_hyphens(self):
        assert slugify_filter("my_section") == "my-section"


# ---------------------------------------------------------------------------
# get_base_context
# ---------------------------------------------------------------------------


class TestGetBaseContext:
    def test_returns_expected_keys(self, repository_data):
        request = MagicMock()
        request.app.state.repo_data = repository_data
        context = get_base_context(request)
        expected_keys = [
            "request", "app_name", "total_genomes", "total_species", "total_genes",
            "project_count", "discovery_count", "idea_count", "collection_count",
            "contributor_count", "skill_count", "last_updated",
        ]
        for key in expected_keys:
            assert key in context, f"Missing key: {key}"

    def test_counts_match_data(self, repository_data):
        request = MagicMock()
        request.app.state.repo_data = repository_data
        context = get_base_context(request)
        assert context["project_count"] == len(repository_data.projects)
        assert context["discovery_count"] == len(repository_data.discoveries)
        assert context["idea_count"] == len(repository_data.research_ideas)
        assert context["collection_count"] == len(repository_data.collections)

    def test_total_genomes_formatted(self, repository_data):
        request = MagicMock()
        request.app.state.repo_data = repository_data
        context = get_base_context(request)
        # Should be comma-formatted
        assert "," in context["total_genomes"]


# ---------------------------------------------------------------------------
# HTTP Routes via TestClient
# ---------------------------------------------------------------------------


@pytest.fixture
def client(repository_data):
    """TestClient with injected repository data, no lifespan startup."""
    from app.main import app

    with TestClient(app, raise_server_exceptions=True) as c:
        app.state.repo_data = repository_data
        yield c


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


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

    def test_collection_detail_200(self, client):
        response = client.get("/collections/kbase_ke_pangenome")
        assert response.status_code == 200

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
        with patch("app.main.settings") as mock_settings:
            mock_settings.data_repo_url = None
            mock_settings.webhook_secret = None
            response = client.post(
                "/api/webhook/data-update",
                content=b"{}",
            )
        assert response.status_code == 400

    def test_missing_signature_with_secret_returns_401(self, client):
        with patch("app.main.settings") as mock_settings:
            mock_settings.webhook_secret = "mysecret"
            mock_settings.data_repo_url = "http://example.com/repo"
            mock_settings.data_repo_path = MagicMock()
            mock_settings.data_repo_branch = "data-cache"
            response = client.post(
                "/api/webhook/data-update",
                content=b"{}",
            )
        assert response.status_code == 401

    def test_invalid_signature_returns_401(self, client):
        with patch("app.main.settings") as mock_settings:
            mock_settings.webhook_secret = "mysecret"
            mock_settings.data_repo_url = "http://example.com/repo"
            mock_settings.data_repo_path = MagicMock()
            mock_settings.data_repo_branch = "data-cache"
            response = client.post(
                "/api/webhook/data-update",
                content=b"{}",
                headers={"x-webhook-signature": "badsignature"},
            )
        assert response.status_code == 401

    def test_valid_signature_triggers_reload(self, client, repository_data):
        secret = "mysecret"
        body = b"{}"
        expected_sig = hmac.new(
            secret.encode(), body, hashlib.sha256
        ).hexdigest()

        with (
            patch("app.main.settings") as mock_settings,
            patch("app.main.pull_latest", new_callable=AsyncMock),
            patch("app.main.load_repository_data", return_value=repository_data),
        ):
            mock_settings.webhook_secret = secret
            mock_settings.data_repo_url = "http://example.com/repo"
            mock_settings.data_repo_path = MagicMock()
            mock_settings.data_repo_branch = "data-cache"

            response = client.post(
                "/api/webhook/data-update",
                content=body,
                headers={"x-webhook-signature": expected_sig},
            )
        assert response.status_code == 200
        assert response.json()["status"] == "success"


# ---------------------------------------------------------------------------
# PlotlyPreprocessor
# ---------------------------------------------------------------------------


class TestPlotlyPreprocessor:
    def test_converts_plotly_output(self):
        import nbformat
        from app.main import PlotlyPreprocessor

        cell = nbformat.from_dict({
            "cell_type": "code",
            "source": "",
            "metadata": {},
            "outputs": [
                {
                    "output_type": "display_data",
                    "metadata": {},
                    "data": {
                        "application/vnd.plotly.v1+json": {
                            "data": [],
                            "layout": {},
                        }
                    },
                }
            ],
        })

        preprocessor = PlotlyPreprocessor()
        result_cell, resources = preprocessor.preprocess_cell(cell, {}, 0)

        assert resources.get("needs_plotly") is True
        output = result_cell["outputs"][0]
        assert "text/html" in output["data"]
        html = output["data"]["text/html"]
        assert "Plotly.newPlot" in html
        assert "<div id=" in html

    def test_non_plotly_output_unchanged(self):
        import nbformat
        from app.main import PlotlyPreprocessor

        cell = nbformat.from_dict({
            "cell_type": "code",
            "source": "",
            "metadata": {},
            "outputs": [
                {
                    "output_type": "stream",
                    "name": "stdout",
                    "text": "hello\n",
                }
            ],
        })

        preprocessor = PlotlyPreprocessor()
        result_cell, resources = preprocessor.preprocess_cell(cell, {}, 0)

        assert not resources.get("needs_plotly")
        assert result_cell["outputs"][0]["output_type"] == "stream"

    def test_empty_outputs_no_plotly_flag(self):
        import nbformat
        from app.main import PlotlyPreprocessor

        cell = nbformat.from_dict({
            "cell_type": "code",
            "source": "",
            "metadata": {},
            "outputs": [],
        })

        preprocessor = PlotlyPreprocessor()
        _, resources = preprocessor.preprocess_cell(cell, {}, 0)
        assert not resources.get("needs_plotly")
