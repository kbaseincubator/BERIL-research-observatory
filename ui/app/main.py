"""Pangenome Research Observatory - FastAPI Application."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .parser import get_parser

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    debug=settings.debug,
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


# Add custom template globals
@app.on_event("startup")
async def startup_event():
    """Initialize app on startup."""
    # Parse repository data
    parser = get_parser()
    app.state.repo_data = parser.parse_all()


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
        }
    )
    return templates.TemplateResponse("home.html", context)


@app.get("/projects", response_class=HTMLResponse)
async def projects_list(request: Request):
    """Projects list page."""
    repo_data = get_repo_data(request)
    context = get_base_context(request)
    context["projects"] = repo_data.projects
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
    return templates.TemplateResponse("projects/detail.html", context)


@app.get("/data", response_class=HTMLResponse)
async def data_overview(request: Request):
    """Data catalog overview page."""
    repo_data = get_repo_data(request)
    context = get_base_context(request)
    context["tables"] = repo_data.tables
    return templates.TemplateResponse("data/overview.html", context)


@app.get("/data/schema", response_class=HTMLResponse)
async def schema_browser(request: Request, table: str | None = None):
    """Schema browser page."""
    repo_data = get_repo_data(request)
    context = get_base_context(request)
    context["tables"] = repo_data.tables

    if table:
        selected = next((t for t in repo_data.tables if t.name == table), None)
        context["selected_table"] = selected

    return templates.TemplateResponse("data/schema.html", context)


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


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """About page."""
    context = get_base_context(request)
    return templates.TemplateResponse("about/about.html", context)


# Health check
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
