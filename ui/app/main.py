"""BERIL Research Observatory - FastAPI Application."""

from pathlib import Path

import nbformat
from markupsafe import Markup
from nbconvert import HTMLExporter

# Add custom Jinja2 filters
import markdown
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .models import CollectionCategory
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


# Register filters
templates.env.filters["markdown"] = markdown_filter
templates.env.filters["md"] = markdown_filter  # Alias
templates.env.filters["markdown_inline"] = markdown_inline_filter
templates.env.filters["mdi"] = markdown_inline_filter  # Alias


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
        "collection_count": len(repo_data.collections),
        "contributor_count": len(repo_data.contributors),
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
            "primary_collections": repo_data.get_collections_by_category(CollectionCategory.PRIMARY)[:3],
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
    context["primary_collections"] = repo_data.get_collections_by_category(CollectionCategory.PRIMARY)
    return templates.TemplateResponse("about/about.html", context)


# Health check
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
