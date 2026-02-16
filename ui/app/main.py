"""BERIL Research Observatory - FastAPI Application."""

import hashlib
import hmac
import logging
from contextlib import asynccontextmanager
from datetime import datetime

import nbformat
from markupsafe import Markup
from nbconvert import HTMLExporter

# Add custom Jinja2 filters
import markdown
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .dataloader import load_repository_data
from .git_data_sync import ensure_repo_cloned, pull_latest
from .models import CollectionCategory

logger = logging.getLogger(__name__)


# Add custom template globals
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize app on startup."""
    logger.info("Initializing repository data")

    # If git repo is configured, clone/pull it first
    if settings.data_repo_url:
        try:
            logger.info(f"Syncing data from git repository: {settings.data_repo_url}")
            await ensure_repo_cloned(
                settings.data_repo_url,
                settings.data_repo_branch,
                settings.data_repo_path
            )

            # Load from local git repo
            data_file = settings.data_repo_path / "data_cache" / "data.pkl.gz"
            app.state.repo_data = load_repository_data(data_file)
            logger.info(f"Repository data loaded from git. Last updated: {app.state.repo_data.last_updated}")
        except Exception as e:
            logger.error(f"Failed to load from git repo: {e}")
            logger.info("Falling back to local parsing")
            app.state.repo_data = load_repository_data(None)
    else:
        # No git repo configured, load from local parsing
        logger.info("No git repo configured, parsing local files")
        app.state.repo_data = load_repository_data(None)

    yield


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    debug=settings.debug,
    lifespan=lifespan,
)



# Mount static files
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

# Mount project data files for visualization serving
app.mount(
    "/project-assets",
    StaticFiles(directory=settings.projects_dir),
    name="project-assets",
)

# Configure templates
templates = Jinja2Templates(directory=settings.templates_dir)


def markdown_filter(text: str) -> Markup:
    """Convert markdown text to HTML."""
    if not text:
        return Markup("")
    # Convert markdown to HTML
    html = markdown.markdown(
        text,
        extensions=["fenced_code", "tables", "nl2br"],
    )
    return Markup(html)


def markdown_inline_filter(text: str) -> Markup:
    """Convert markdown text to inline HTML (strips outer <p> tags)."""
    if not text:
        return Markup("")
    html = markdown.markdown(text, extensions=["fenced_code"])
    # Strip outer <p> tags for inline use
    if html.startswith("<p>") and html.endswith("</p>"):
        html = html[3:-4]
    return Markup(html)


def strip_images_filter(text: str) -> str:
    """Strip markdown image syntax from text for preview use."""
    if not text:
        return ""
    import re
    return re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)


# Register filters
templates.env.filters["markdown"] = markdown_filter
templates.env.filters["md"] = markdown_filter  # Alias
templates.env.filters["markdown_inline"] = markdown_inline_filter
templates.env.filters["mdi"] = markdown_inline_filter  # Alias
templates.env.filters["strip_images"] = strip_images_filter


def get_repo_data(request: Request):
    """Get repository data from app state."""
    return request.app.state.repo_data


# Template context processor
def get_base_context(request: Request) -> dict:
    """Get base context for all templates."""
    repo_data = get_repo_data(request)
    return {
        "request": request,
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
        "last_updated": repo_data.last_updated,
    }


# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page - Research Observatory dashboard."""
    repo_data = get_repo_data(request)
    context = get_base_context(request)
    context.update(
        {
            "projects": repo_data.projects[:3],  # Latest 3 projects
            "discoveries": repo_data.discoveries[:3],  # Latest 3 discoveries
            "total_notebooks": repo_data.total_notebooks,
            "total_visualizations": repo_data.total_visualizations,
            "primary_collections": repo_data.get_collections_by_category(
                CollectionCategory.PRIMARY
            )[:3],
        }
    )
    return templates.TemplateResponse("home.html", context)


@app.get("/co-scientist", response_class=HTMLResponse)
async def co_scientist(request: Request):
    """AI Co-Scientist page."""
    repo_data = get_repo_data(request)
    context = get_base_context(request)
    context["skills"] = repo_data.skills
    # Example project for the workflow walkthrough
    context["example_project"] = next(
        (p for p in repo_data.projects if p.id == "costly_dispensable_genes"), None
    )
    return templates.TemplateResponse("co-scientist.html", context)


@app.get("/skills", response_class=HTMLResponse)
async def skills_page(request: Request):
    """Skills catalog page."""
    repo_data = get_repo_data(request)
    context = get_base_context(request)
    context["skills"] = repo_data.skills
    return templates.TemplateResponse("skills.html", context)


@app.get("/projects", response_class=HTMLResponse)
async def projects_list(request: Request, sort: str = "recent"):
    """Projects list page with sortable project grid."""
    repo_data = get_repo_data(request)
    context = get_base_context(request)

    projects = list(repo_data.projects)  # copy to avoid mutating cached data

    if sort == "status":
        status_order = {"Completed": 0, "In Progress": 1, "Proposed": 2}
        projects.sort(
            key=lambda p: (
                status_order.get(p.status.value, 9),
                -(p.updated_date or datetime.min).timestamp(),
            )
        )
    elif sort == "alpha":
        projects.sort(key=lambda p: p.title.lower())
    # else: "recent" — already sorted by updated_date desc from dataloader

    context["projects"] = projects
    context["current_sort"] = sort
    return templates.TemplateResponse("projects/list.html", context)


@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_detail(request: Request, project_id: str):
    """Project detail page."""
    repo_data = get_repo_data(request)
    context = get_base_context(request)

    # Find project
    project = next((p for p in repo_data.projects if p.id == project_id), None)
    if not project:
        context["error"] = f"Project '{project_id}' not found"
        return templates.TemplateResponse("error.html", context, status_code=404)

    context["project"] = project

    # Find discoveries from this project
    context["project_discoveries"] = [
        d for d in repo_data.discoveries if d.project_tag == project_id
    ]

    # Resolve collection IDs to full objects for richer display
    context["project_collections"] = [
        c for c in (repo_data.get_collection(cid) for cid in project.related_collections) if c
    ]

    return templates.TemplateResponse("projects/detail.html", context)


@app.get(
    "/projects/{project_id}/notebooks/{notebook_name}", response_class=HTMLResponse
)
async def notebook_viewer(request: Request, project_id: str, notebook_name: str):
    """Render a Jupyter notebook as HTML."""

    repo_data = get_repo_data(request)
    context = get_base_context(request)

    # Find project
    project = next((p for p in repo_data.projects if p.id == project_id), None)
    if not project:
        context["error"] = f"Project '{project_id}' not found"
        return templates.TemplateResponse("error.html", context, status_code=404)

    # Find notebook
    notebook = next((n for n in project.notebooks if n.filename == notebook_name), None)
    if not notebook:
        context["error"] = (
            f"Notebook '{notebook_name}' not found in project '{project_id}'"
        )
        return templates.TemplateResponse("error.html", context, status_code=404)

    # Load and convert notebook
    notebook_path = settings.repo_dir / notebook.path
    if not notebook_path.exists():
        context["error"] = f"Notebook file not found: {notebook.path}"
        return templates.TemplateResponse("error.html", context, status_code=404)

    try:
        # Read the notebook
        with open(notebook_path, "r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)

        # Convert to HTML
        html_exporter = HTMLExporter()
        html_exporter.template_name = "classic"
        html_exporter.theme = "dark"
        html_exporter.exclude_input_prompt = False
        html_exporter.exclude_output_prompt = False

        (body, resources) = html_exporter.from_notebook_node(nb)

        context.update(
            {
                "project": project,
                "notebook": notebook,
                "notebook_html": body,
            }
        )
        return templates.TemplateResponse("projects/notebook.html", context)

    except Exception as e:
        context["error"] = f"Error rendering notebook: {str(e)}"
        return templates.TemplateResponse("error.html", context, status_code=500)


@app.get("/projects/{project_id}/{filename:path}", response_class=HTMLResponse)
async def project_file_redirect(request: Request, project_id: str, filename: str):
    """Redirect markdown file links to the project detail page."""
    from fastapi.responses import RedirectResponse

    if filename.endswith(".md"):
        return RedirectResponse(url=f"/projects/{project_id}", status_code=302)
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/collections", response_class=HTMLResponse)
async def collections_overview(request: Request):
    """Collections overview page - browse all BERDL collections."""
    repo_data = get_repo_data(request)
    context = get_base_context(request)
    context["collections"] = repo_data.collections
    context["primary_collections"] = repo_data.get_collections_by_category(
        CollectionCategory.PRIMARY
    )
    context["domain_collections"] = repo_data.get_collections_by_category(
        CollectionCategory.DOMAIN
    )
    context["reference_collections"] = repo_data.get_collections_by_category(
        CollectionCategory.REFERENCE
    )
    return templates.TemplateResponse("collections/overview.html", context)


@app.get("/collections/{collection_id}", response_class=HTMLResponse)
async def collection_detail(request: Request, collection_id: str):
    """Collection detail page with schema browser."""
    repo_data = get_repo_data(request)
    context = get_base_context(request)

    # Find the collection
    collection = repo_data.get_collection(collection_id)
    if not collection:
        context["error"] = f"Collection '{collection_id}' not found"
        return templates.TemplateResponse("error.html", context, status_code=404)

    context["collection"] = collection
    context["collection_id"] = collection_id

    # Get related collections as full objects
    related = [repo_data.get_collection(cid) for cid in collection.related_collections]
    context["related_collections"] = [c for c in related if c is not None]

    # Pass collection-specific schema tables (if any schema doc exists)
    context["tables"] = repo_data.get_tables_for_collection(collection_id)

    # Find projects that reference this collection
    context["related_projects"] = [
        p for p in repo_data.projects if collection_id in p.related_collections
    ]

    return templates.TemplateResponse("collections/detail.html", context)


# Legacy redirect for /data routes
@app.get("/data", response_class=HTMLResponse)
async def data_redirect(request: Request):
    """Redirect legacy /data to /collections."""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/collections", status_code=301)


@app.get("/data/schema", response_class=HTMLResponse)
async def schema_redirect(request: Request):
    """Redirect legacy /data/schema to /collections/kbase_ke_pangenome."""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/collections/kbase_ke_pangenome", status_code=301)


@app.get("/knowledge/discoveries", response_class=HTMLResponse)
async def discoveries_timeline(request: Request):
    """Discoveries timeline page."""
    repo_data = get_repo_data(request)
    context = get_base_context(request)
    context["discoveries"] = repo_data.discoveries
    return templates.TemplateResponse("knowledge/discoveries.html", context)


@app.get("/knowledge/pitfalls", response_class=HTMLResponse)
async def pitfalls_list(request: Request):
    """Pitfalls and gotchas page."""
    repo_data = get_repo_data(request)
    context = get_base_context(request)
    context["pitfalls"] = repo_data.pitfalls
    return templates.TemplateResponse("knowledge/pitfalls.html", context)


@app.get("/knowledge/performance", response_class=HTMLResponse)
async def performance_tips(request: Request):
    """Performance tips and query patterns page."""
    repo_data = get_repo_data(request)
    context = get_base_context(request)
    context["tips"] = repo_data.performance_tips
    return templates.TemplateResponse("knowledge/performance.html", context)


@app.get("/knowledge/ideas", response_class=HTMLResponse)
async def research_ideas(request: Request):
    """Research ideas board page."""
    repo_data = get_repo_data(request)
    context = get_base_context(request)

    # Group ideas by status
    ideas = repo_data.research_ideas
    context["proposed_ideas"] = [i for i in ideas if i.status.value == "PROPOSED"]
    context["in_progress_ideas"] = [i for i in ideas if i.status.value == "IN_PROGRESS"]
    context["completed_ideas"] = [i for i in ideas if i.status.value == "COMPLETED"]

    return templates.TemplateResponse("knowledge/ideas.html", context)


@app.get("/community/contributors", response_class=HTMLResponse)
async def community_contributors(request: Request):
    """Community contributors page."""
    repo_data = get_repo_data(request)
    context = get_base_context(request)
    context["contributors"] = repo_data.contributors
    context["total_orcids"] = sum(1 for c in repo_data.contributors if c.orcid)
    return templates.TemplateResponse("community/contributors.html", context)


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """About page."""
    repo_data = get_repo_data(request)
    context = get_base_context(request)
    context["primary_collections"] = repo_data.get_collections_by_category(
        CollectionCategory.PRIMARY
    )
    return templates.TemplateResponse("about/about.html", context)


# Webhook endpoint for data cache updates
@app.post("/api/webhook/data-update")
async def data_update_webhook(request: Request, x_webhook_signature: str = Header(None)):
    """
    Webhook endpoint to receive data cache update notifications.

    Expected to be called by GitHub Actions after building new cache.
    Validates signature and reloads data from the remote source.
    """
    # Read the request body
    body = await request.body()

    # Verify webhook signature if secret is configured
    if settings.webhook_secret:
        if not x_webhook_signature:
            logger.warning("Webhook request missing signature")
            raise HTTPException(status_code=401, detail="Missing webhook signature")

        # Compute expected signature
        expected_signature = hmac.new(
            settings.webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(x_webhook_signature, expected_signature):
            logger.warning("Webhook signature validation failed")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    logger.info("Received data update webhook notification")

    # Pull latest changes and reload
    if settings.data_repo_url:
        try:
            logger.info(f"Pulling latest changes from git repository")

            # Pull latest changes
            await pull_latest(settings.data_repo_path, settings.data_repo_branch)

            # Reload from local git repo
            data_file = settings.data_repo_path / "data_cache" / "data.pkl.gz"
            request.app.state.repo_data = load_repository_data(data_file)

            logger.info(f"Data reloaded successfully. New last_updated: {request.app.state.repo_data.last_updated}")

            return JSONResponse({
                "status": "success",
                "message": "Data reloaded successfully from git",
                "last_updated": request.app.state.repo_data.last_updated.isoformat() if request.app.state.repo_data.last_updated else None
            })
        except Exception as e:
            logger.error(f"Failed to reload data from git: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to reload data: {str(e)}")
    else:
        logger.warning("Webhook received but no data_repo_url configured")
        raise HTTPException(status_code=400, detail="No git repository configured")


# Health check
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
