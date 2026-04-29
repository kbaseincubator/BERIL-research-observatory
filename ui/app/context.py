import logging

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.auth import get_current_session_user
from app.config import Settings
from app.dataloader import load_repository_data
from app.git_data_sync import ensure_repo_cloned
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
    """Initialize app on startup."""
    logger.info("Initializing repository data")

    if settings.force_local_data:
        logger.info("Forcing parsing and loading of local data")
        print("Forcing parsing and loading of local data")
        repo_data = load_repository_data(None)
    elif settings.data_repo_url:
        try:
            logger.info(f"Syncing data from git repository: {settings.data_repo_url}")
            await ensure_repo_cloned(
                settings.data_repo_url,
                settings.data_repo_branch,
                settings.data_repo_path,
            )
            data_file = settings.data_repo_path / "data_cache" / "data.pkl.gz"
            repo_data = load_repository_data(data_file)
            logger.info(
                f"Repository data loaded from git. Last updated: {repo_data.last_updated}"
            )
        except Exception as e:
            logger.error(f"Failed to load from git repo: {e}")
            logger.info("Falling back to local parsing")
            repo_data = load_repository_data(None)
    else:
        logger.info("No git repo configured, parsing local files")
        repo_data = load_repository_data(None)
    return repo_data


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
        "wiki_count": len(repo_data.wiki_index.pages),
        "last_updated": repo_data.last_updated,
    }
