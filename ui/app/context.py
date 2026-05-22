import logging

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.auth import get_current_session_user
from app.config import Settings
from app.lakehouses import get_lakehouse_source
from app.models import RepositoryData

logger = logging.getLogger(__name__)

# Initialized by create_app(); imported by route modules to render responses.
templates: Jinja2Templates | None = None


def get_repo_data(request: Request) -> RepositoryData:
    return request.app.state.repo_data


def get_base_context(request: Request) -> dict:
    context = dict(request.app.state.base_context)
    context["current_user"] = get_current_session_user(request)
    context["path"] = request.url.path
    return context


async def initialize_data(settings: Settings) -> RepositoryData:
    """Initialize app on startup via the active lakehouse source.

    The source's ``sync()`` owns the decision tree (git clone vs. local parse,
    retry, fallback). Startup only needs the parsed ``RepositoryData``; the
    importer reads ``projects_dir`` from the same result inside the webhook
    handler.
    """
    logger.info("Initializing repository data")
    source = get_lakehouse_source(settings)
    result = await source.sync()
    logger.info("Loaded repository data from lakehouse source %r", result.source_name)
    return result.repo_data


def generate_base_context(settings: Settings, repo_data: RepositoryData) -> dict:
    return {
        "app_name": settings.app_name,
        "total_genomes": f"{settings.total_genomes:,}",
        "total_species": f"{settings.total_species:,}",
        "total_genes": settings.total_genes,
        "project_count": len(repo_data.projects),
        "discovery_count": len(repo_data.discoveries),
        "idea_count": len(repo_data.research_ideas),
        "collection_count": len(repo_data.collections),
        "contributor_count": len(repo_data.contributors),
        "skill_count": len(repo_data.skills),
        "atlas_count": len(repo_data.atlas_index.pages),
        "last_updated": repo_data.last_updated,
    }
