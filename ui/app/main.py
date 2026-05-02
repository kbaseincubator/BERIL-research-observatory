"""BERIL Research Observatory - FastAPI Application."""

import hashlib
import hmac
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import app.context as ctx
from app.context import generate_base_context, get_base_context, get_repo_data, initialize_data
from app.db.session import init_db, close_db, check_db
from app.notebook_processors import PlotlyPreprocessor
import nbformat
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from nbconvert import HTMLExporter
from starlette.middleware.sessions import SessionMiddleware

from app.filters import (
    markdown_filter,
    markdown_inline_filter,
    slugify_filter,
    strip_images_filter,
)
from app.atlas_graph import (
    build_derived_product_context,
    build_opportunity_context,
    build_opportunity_contexts,
    build_reuse_overview,
    build_topic_overview_map,
    collection_atlas_reuse,
    conflicts_for_page,
    opportunities_for_page,
    project_atlas_reuse,
    review_routes_for_page,
)

from .routes.admin import ROUTER_ADMIN
from .routes.auth import ROUTER_AUTH
from .routes.chat import ROUTER_CHAT, ROUTER_CHAT_PAGES
from .routes.data import ROUTER_USER_DATA
from .routes.user import ROUTER_USER
from .config import get_settings
from .db.crud import get_project_by_id, user_project_to_model
from .db.session import get_db
from .dataloader import load_repository_data, RepositoryParser
from .git_data_sync import pull_latest
from .importer import run_full_migration
from .models import CollectionCategory, RepositoryData, AtlasPage
from .storage import LocalFileStorage
from .atlas_inventory import build_atlas_inventory

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

templates = None


ATLAS_SECTIONS = [
    ("Overview", "root", "/atlas"),
    ("Topics", "topics", "/atlas/topics"),
    ("Data", "data", "/atlas/data"),
    ("Claims", "claims", "/atlas/claims"),
    ("Tensions", "conflicts", "/atlas/conflicts"),
    ("Opportunities", "opportunities", "/atlas/opportunities"),
    ("Directions", "directions", "/atlas/directions"),
    ("Hypotheses", "hypotheses", "/atlas/hypotheses"),
    ("People", "people", "/atlas/people"),
    ("Methods", "methods", "/atlas/methods"),
    ("Meta", "meta", "/atlas/meta"),
]



@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if not settings.test_skip_lifespan:
        await init_db(settings.db_url)
        app.state.repo_data = await initialize_data(settings)
        app.state.base_context = generate_base_context(settings, app.state.repo_data)
    yield
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()

    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key, session_cookie="beril_session")

    # Mount static files
    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

    # Mount project data files for visualization serving
    app.mount(
        "/project-assets",
        StaticFiles(directory=settings.projects_dir),
        name="project-assets",
    )

    app.include_router(ROUTER_ADMIN)
    app.include_router(ROUTER_AUTH)
    app.include_router(ROUTER_CHAT)
    app.include_router(ROUTER_CHAT_PAGES)
    app.include_router(ROUTER_COLLECTIONS)
    app.include_router(ROUTER_USER)
    app.include_router(ROUTER_USER_DATA)
    app.include_router(ROUTER_COMMUNITY)
    app.include_router(ROUTER_COSCIENTIST)
    app.include_router(ROUTER_DATA)
    app.include_router(ROUTER_GENERAL)
    app.include_router(ROUTER_KNOWLEDGE)
    app.include_router(ROUTER_PROJECTS)
    app.include_router(ROUTER_SKILLS)
    app.include_router(ROUTER_ATLAS)

    # Configure templates
    global templates
    templates = Jinja2Templates(directory=settings.templates_dir)
    ctx.templates = templates

    # Register filters
    templates.env.filters["markdown"] = markdown_filter
    templates.env.filters["md"] = markdown_filter  # Alias
    templates.env.filters["markdown_inline"] = markdown_inline_filter
    templates.env.filters["mdi"] = markdown_inline_filter  # Alias
    templates.env.filters["strip_images"] = strip_images_filter
    templates.env.filters["slugify"] = slugify_filter

    return app


ROUTER_COLLECTIONS = APIRouter(tags=["Collections"])
ROUTER_COMMUNITY = APIRouter(tags=["Community"])
ROUTER_COSCIENTIST = APIRouter(tags=["Coscientist"])
ROUTER_DATA = APIRouter(tags=["Data"])
ROUTER_GENERAL = APIRouter(tags=["General"])
ROUTER_KNOWLEDGE = APIRouter(tags=["Knowledge"])
ROUTER_PROJECTS = APIRouter(tags=["Project"])
ROUTER_SKILLS = APIRouter(tags=["Skills"])
ROUTER_ATLAS = APIRouter(tags=["Atlas"])


# Routes
@ROUTER_GENERAL.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
):
    """Home page - Research Observatory dashboard."""
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
    return templates.TemplateResponse(request, "home.html", context)



@ROUTER_COSCIENTIST.get("/co-scientist", response_class=HTMLResponse)
async def co_scientist(
    request: Request,
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
):
    """AI Co-Scientist page."""
    context["skills"] = repo_data.skills
    # Example project for the workflow walkthrough
    context["example_project"] = next(
        (p for p in repo_data.projects if p.id == "costly_dispensable_genes"), None
    )
    return templates.TemplateResponse(request, "co-scientist.html", context)


@ROUTER_SKILLS.get("/skills", response_class=HTMLResponse)
async def skills_page(
    request: Request,
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
):
    """Skills catalog page."""
    context["skills"] = repo_data.skills
    return templates.TemplateResponse(request, "skills.html", context)


@ROUTER_PROJECTS.get("/projects", response_class=HTMLResponse)
async def projects_list(
    request: Request,
    sort: str = "recent",
    dir: str = "",
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
    db: AsyncSession = Depends(get_db),
):
    """Projects list page with sortable project grid."""

    # Fetch raw UserProject rows so we can inspect repo_path for de-duplication.
    # repo_data projects use the filesystem slug as their id (e.g. "my_project").
    # Imported DB rows have UUID PKs but store repo_path = "projects/{slug}".
    # We exclude any DB row whose repo_path slug matches a live repo_data project,
    # preventing the same project from appearing twice in the list.
    # /projects is a public catalog — only surface DB rows the owner has marked public.
    from sqlalchemy import select as _sa_select
    from app.db.models import UserProject as _UserProject
    _raw = await db.execute(
        _sa_select(_UserProject)
        .where(_UserProject.is_public.is_(True))
        .order_by(_UserProject.created_at.desc())
    )
    _raw_rows = _raw.scalars().all()

    repo_slugs = {p.id for p in repo_data.projects}
    db_projects = []
    for row in _raw_rows:
        # Extract slug from repo_path ("projects/slug" → "slug"); None for user-created rows.
        row_slug = row.repo_path.split("/")[-1] if row.repo_path else None
        if row_slug in repo_slugs:
            continue  # already represented by live repo_data entry
        db_projects.append(user_project_to_model(row))

    projects = list(repo_data.projects) + db_projects

    # Default directions: recent=desc, others=asc
    default_dir = "desc" if sort == "recent" else "asc"
    sort_dir = dir if dir in ("asc", "desc") else default_dir
    reverse = sort_dir == "desc"

    if sort == "status":
        status_order = {"Completed": 0, "In Progress": 1, "Proposed": 2}
        projects.sort(
            key=lambda p: (
                status_order.get(p.status.value, 9),
                -(p.updated_date or datetime.min).timestamp(),
            ),
            reverse=reverse,
        )
    elif sort == "alpha":
        projects.sort(key=lambda p: p.title.lower(), reverse=reverse)
    elif sort == "author":
        projects.sort(
            key=lambda p: (
                p.contributors[0].name.split()[-1].lower() if p.contributors else "zzz",
                p.title.lower(),
            ),
            reverse=reverse,
        )
    elif reverse:
        # "recent" is already desc from dataloader; reverse if asc requested
        projects.reverse()

    context["projects"] = projects
    context["current_sort"] = sort
    context["sort_dir"] = sort_dir
    return templates.TemplateResponse(request, "projects/list.html", context)


@ROUTER_COSCIENTIST.get("/research-areas", response_class=HTMLResponse)
async def research_areas(
    request: Request,
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
):
    """Research areas page - auto-clustered project groups."""
    # Resolve project IDs to full objects for each area
    project_map = {p.id: p for p in repo_data.projects}
    areas_with_projects = []
    for area in repo_data.research_areas:
        areas_with_projects.append(
            {
                "area": area,
                "projects": [
                    project_map[pid] for pid in area.project_ids if pid in project_map
                ],
            }
        )

    context["areas"] = areas_with_projects
    return templates.TemplateResponse(request, "research-areas.html", context)


@ROUTER_PROJECTS.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_detail(
    request: Request,
    project_id: str,
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
    db: AsyncSession = Depends(get_db),
):
    """Project detail page."""

    # Find project — check repo first, then fall back to DB
    project = next((p for p in repo_data.projects if p.id == project_id), None)
    if project is None:
        db_project = await get_project_by_id(db, project_id)
        if db_project is not None:
            # DB-backed projects default to private; this public route may only
            # render rows that are public OR owned by the caller. Otherwise we'd
            # leak private project metadata to anyone who guesses the UUID.
            viewer_id = request.session.get("beril_user_id")
            if db_project.is_public or db_project.owner_id == viewer_id:
                project = user_project_to_model(db_project)
    if not project:
        context["error"] = f"Project '{project_id}' not found"
        return templates.TemplateResponse(
            request, "error.html", context, status_code=404
        )

    # Enrich project contributors with aggregated data (ORCID, full name)
    agg_by_key = {
        RepositoryParser._contributor_key(c.name): c for c in repo_data.contributors
    }
    for contrib in project.contributors:
        key = RepositoryParser._contributor_key(contrib.name)
        agg = agg_by_key.get(key)
        if agg:
            if not contrib.orcid and agg.orcid:
                contrib.orcid = agg.orcid
            if len(agg.name) > len(contrib.name):
                contrib.name = agg.name

    context["project"] = project

    # Find discoveries from this project
    context["project_discoveries"] = [
        d for d in repo_data.discoveries if d.project_tag == project_id
    ]

    # Resolve collection IDs to full objects for richer display
    context["project_collections"] = [
        c
        for c in (repo_data.get_collection(cid) for cid in project.related_collections)
        if c
    ]

    # Resolve used_by IDs to full Project objects
    context["used_by_projects"] = [
        p for p in repo_data.projects if p.id in project.used_by
    ]
    context["project_atlas_reuse"] = project_atlas_reuse(project.id, repo_data)

    return templates.TemplateResponse(request, "projects/detail.html", context)


@ROUTER_PROJECTS.get(
    "/projects/{project_id}/notebooks/{notebook_name}", response_class=HTMLResponse
)
async def notebook_viewer(
    request: Request,
    project_id: str,
    notebook_name: str,
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
):
    """Render a Jupyter notebook as HTML."""
    # Find project
    project = next(
        (p for p in repo_data.projects if p.id == project_id), None
    )
    if not project:
        context["error"] = f"Project '{project_id}' not found"
        return templates.TemplateResponse(
            request, "error.html", context, status_code=404
        )

    # Find notebook
    notebook = next((n for n in project.notebooks if n.filename == notebook_name), None)
    if not notebook:
        context["error"] = (
            f"Notebook '{notebook_name}' not found in project '{project_id}'"
        )
        return templates.TemplateResponse(
            request, "error.html", context, status_code=404
        )

    # Load and convert notebook
    notebook_path = get_settings().repo_dir / notebook.path
    if not notebook_path.exists():
        context["error"] = f"Notebook file not found: {notebook.path}"
        return templates.TemplateResponse(
            request, "error.html", context, status_code=404
        )

    try:
        # Read the notebook
        with open(notebook_path, "r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)

        # Convert plotly outputs to renderable HTML before exporting
        preprocessor = PlotlyPreprocessor()
        nb, nb_resources = preprocessor.preprocess(nb, {})

        # Convert to HTML
        html_exporter = HTMLExporter()
        html_exporter.template_name = "classic"
        html_exporter.theme = "dark"
        html_exporter.exclude_input_prompt = False
        html_exporter.exclude_output_prompt = False

        (body, _) = html_exporter.from_notebook_node(nb)

        # Prepend Plotly CDN script if any plotly figures were found
        if nb_resources.get("needs_plotly"):
            plotly_cdn = f'<script src="{get_settings().plotly_cdn_url}" charset="utf-8"></script>'
            body = plotly_cdn + body

        context.update(
            {
                "project": project,
                "notebook": notebook,
                "notebook_html": body,
            }
        )
        return templates.TemplateResponse(request, "projects/notebook.html", context)

    except Exception as e:
        context["error"] = f"Error rendering notebook: {str(e)}"
        return templates.TemplateResponse(
            request, "error.html", context, status_code=500
        )


@ROUTER_PROJECTS.get(
    "/projects/{project_id}/{filename:path}", response_class=HTMLResponse
)
async def project_file_redirect(request: Request, project_id: str, filename: str):
    """Redirect markdown file links to the project detail page."""
    if filename.endswith(".md"):
        return RedirectResponse(url=f"/projects/{project_id}", status_code=302)
    raise HTTPException(status_code=404, detail="File not found")


@ROUTER_DATA.get("/data-explorer", response_class=HTMLResponse)
async def data_explorer(
    request: Request,
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
):
    """Cross-Collection Explorer Dashboard."""

    # Build collection lookup and node data
    collection_map = {c.id: c for c in repo_data.collections}
    project_map = {p.id: p for p in repo_data.projects}

    # Build adjacency info for each collection
    adjacency: dict[str, dict] = {}
    for coll in repo_data.collections:
        adjacency[coll.id] = {"explicit": set(), "project": set(), "projects": set()}

    for edge in repo_data.collection_edges:
        if edge.source_id in adjacency and edge.target_id in adjacency:
            if edge.edge_type == "explicit":
                adjacency[edge.source_id]["explicit"].add(edge.target_id)
                adjacency[edge.target_id]["explicit"].add(edge.source_id)
            adjacency[edge.source_id]["project"].update(edge.projects)
            adjacency[edge.target_id]["project"].update(edge.projects)
            adjacency[edge.source_id]["projects"].update(edge.projects)
            adjacency[edge.target_id]["projects"].update(edge.projects)

    # Build node info for template
    nodes = []
    for coll in repo_data.collections:
        adj = adjacency.get(coll.id, {})
        connected_ids = adj.get("explicit", set()) | {
            e.target_id if e.source_id == coll.id else e.source_id
            for e in repo_data.collection_edges
            if coll.id in (e.source_id, e.target_id)
        }
        nodes.append(
            {
                "collection": coll,
                "connection_count": len(connected_ids),
                "project_count": len(adj.get("projects", set())),
            }
        )

    context["nodes"] = nodes
    context["edges"] = repo_data.collection_edges
    context["collection_map"] = collection_map

    # Build join paths from explicit related_collections with sample queries
    join_paths = []
    seen_pairs: set[tuple[str, str]] = set()
    for coll in repo_data.collections:
        for related_id in coll.related_collections:
            pair = (min(coll.id, related_id), max(coll.id, related_id))
            if pair in seen_pairs or related_id not in collection_map:
                continue
            seen_pairs.add(pair)
            join_paths.append(
                {
                    "source": coll,
                    "target": collection_map[related_id],
                }
            )

    context["join_paths"] = join_paths

    # Explorer project highlights
    explorer_ids = [
        "env_embedding_explorer",
        "paperblast_explorer",
        "webofmicrobes_explorer",
        "acinetobacter_adp1_explorer",
    ]
    context["explorer_projects"] = [
        project_map[pid] for pid in explorer_ids if pid in project_map
    ]

    # Cross-collection stats
    multi_coll_projects = [
        p for p in repo_data.projects if len(p.related_collections) >= 2
    ]
    context["multi_collection_project_count"] = len(multi_coll_projects)
    context["edge_count"] = len(repo_data.collection_edges)

    return templates.TemplateResponse(request, "data-explorer.html", context)


@ROUTER_COLLECTIONS.get("/collections", response_class=HTMLResponse)
async def collections_overview(
    request: Request,
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
):
    """Collections overview page - browse all BERDL collections."""

    tenant_groups = {}
    for collection in repo_data.collections:
        tenant_id = collection.tenant_id or collection.category.value
        tenant_groups.setdefault(
            tenant_id,
            {
                "id": tenant_id,
                "name": collection.tenant_name or tenant_id.replace("_", " ").title(),
                "collections": [],
            },
        )
        tenant_groups[tenant_id]["collections"].append(collection)

    context["collections"] = repo_data.collections
    context["tenant_groups"] = sorted(
        tenant_groups.values(), key=lambda group: group["name"].lower()
    )
    context["snapshot_discovered_at"] = next(
        (c.discovered_at for c in repo_data.collections if c.discovered_at), None
    )
    context["snapshot_source"] = next(
        (c.snapshot_source for c in repo_data.collections if c.snapshot_source), None
    )
    context["primary_collections"] = repo_data.get_collections_by_category(
        CollectionCategory.PRIMARY
    )
    context["domain_collections"] = repo_data.get_collections_by_category(
        CollectionCategory.DOMAIN
    )
    context["reference_collections"] = repo_data.get_collections_by_category(
        CollectionCategory.REFERENCE
    )
    return templates.TemplateResponse(request, "collections/overview.html", context)


@ROUTER_COLLECTIONS.get("/collections/{collection_id}", response_class=HTMLResponse)
async def collection_detail(
    request: Request,
    collection_id: str,
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
):
    """Collection detail page with schema browser."""

    # Find the collection
    collection = repo_data.get_collection(collection_id)
    if not collection:
        context["error"] = f"Collection '{collection_id}' not found"
        return templates.TemplateResponse(
            request, "error.html", context, status_code=404
        )

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
    context["related_atlas_pages"] = [
        page
        for page in repo_data.atlas_index.pages
        if collection_id in page.related_collections
    ]
    context["collection_atlas_reuse"] = collection_atlas_reuse(collection_id, repo_data)

    return templates.TemplateResponse(request, "collections/detail.html", context)


# Legacy redirect for /data routes
@ROUTER_DATA.get("/data", response_class=HTMLResponse)
async def data_redirect():
    """Redirect legacy /data to /collections."""
    return RedirectResponse(url="/collections", status_code=301)


@ROUTER_DATA.get("/data/schema", response_class=HTMLResponse)
async def schema_redirect():
    """Redirect legacy /data/schema to /collections/kbase_ke_pangenome."""
    return RedirectResponse(url="/collections/kbase_ke_pangenome", status_code=301)


@ROUTER_KNOWLEDGE.get("/knowledge/discoveries", response_class=HTMLResponse)
async def discoveries_timeline(
    request: Request,
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
):
    """Discoveries timeline page."""
    context["discoveries"] = repo_data.discoveries
    return templates.TemplateResponse(request, "knowledge/discoveries.html", context)


@ROUTER_KNOWLEDGE.get("/knowledge/pitfalls", response_class=HTMLResponse)
async def pitfalls_list(
    request: Request,
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
):
    """Pitfalls and gotchas page."""
    context["pitfalls"] = repo_data.pitfalls
    return templates.TemplateResponse(request, "knowledge/pitfalls.html", context)


@ROUTER_KNOWLEDGE.get("/knowledge/performance", response_class=HTMLResponse)
async def performance_tips(
    request: Request,
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
):
    """Performance tips and query patterns page."""
    context["tips"] = repo_data.performance_tips
    return templates.TemplateResponse(request, "knowledge/performance.html", context)


@ROUTER_KNOWLEDGE.get("/knowledge/ideas", response_class=HTMLResponse)
async def research_ideas(
    request: Request,
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
):
    """Research ideas board page."""
    # Group ideas by status
    ideas = repo_data.research_ideas
    context["proposed_ideas"] = [i for i in ideas if i.status.value == "PROPOSED"]
    context["in_progress_ideas"] = [i for i in ideas if i.status.value == "IN_PROGRESS"]
    context["completed_ideas"] = [i for i in ideas if i.status.value == "COMPLETED"]

    return templates.TemplateResponse(request, "knowledge/ideas.html", context)


def _atlas_nav(atlas_index) -> list[dict[str, Any]]:
    """Build global Atlas navigation with section counts."""
    section_counts = {
        section: len(
            [
                page
                for page in atlas_index.pages_by_section(section)
                if not page.path.endswith("/index")
            ]
        )
        for _, section, _ in ATLAS_SECTIONS
    }
    section_counts["root"] = len(atlas_index.pages_by_section("root"))
    return [
        {"label": label, "section": section, "url": url, "count": section_counts[section]}
        for label, section, url in ATLAS_SECTIONS
    ]


def _page_refs(pages: list[AtlasPage], limit: int | None = None) -> list[dict[str, Any]]:
    """Return compact page references for map panels."""
    selected = pages[:limit] if limit else pages
    return [
        {
            "title": page.title,
            "url": page.url,
            "summary": page.summary,
            "type": page.type.replace("_", " "),
            "source_count": len(page.source_projects),
            "collection_count": len(page.related_collections),
            "confidence": page.confidence,
            "nodes": [],
        }
        for page in selected
    ]


def _build_atlas_maps(repo_data: RepositoryData, atlas_inventory: dict[str, Any]) -> list[dict[str, Any]]:
    """Build deterministic overview maps from Atlas frontmatter and inventory."""
    atlas_index = repo_data.atlas_index
    topics = atlas_index.pages_by_type("topic")
    data_pages = atlas_index.pages_by_section("data")
    claims = atlas_index.pages_by_type("claim")
    directions = atlas_index.pages_by_type("direction")
    hypotheses = atlas_index.pages_by_type("hypothesis")
    derived_products = atlas_index.pages_by_type("derived_product")
    conflicts = atlas_index.pages_by_type("conflict")
    opportunities = atlas_index.pages_by_type("opportunity")

    collection_use = {
        collection.id: sum(
            1
            for page in atlas_index.pages
            if collection.id in page.related_collections
        )
        for collection in repo_data.collections
    }
    top_collections = sorted(
        repo_data.collections,
        key=lambda collection: (-collection_use.get(collection.id, 0), collection.name.lower()),
    )[:8]

    topic_links = []
    for topic in topics:
        linked = [
            page
            for related_id in topic.related_pages
            if (page := atlas_index.get_page_by_id(related_id))
        ]
        topic_links.append(
            {
                "title": topic.title,
                "url": topic.url,
                "summary": topic.summary,
                "nodes": [page.title for page in linked[:4]],
                "source_count": len(topic.source_projects),
                "collection_count": len(topic.related_collections),
            }
        )

    return [
        {
            "title": "Topic Landscape",
            "claim": "Science topics are the first interpretive map: each one connects projects to reusable claims, directions, hypotheses, and data.",
            "items": topic_links,
            "fallback": f"{len(topics)} topics integrate {sum(len(t.source_projects) for t in topics)} project references.",
        },
        {
            "title": "Data Landscape",
            "claim": "Data pages separate physical BERDL collections from cross-collection analytical roles and reusable outputs.",
            "items": [
                {
                    "title": collection.name,
                    "url": f"/collections/{collection.id}",
                    "summary": collection.description,
                    "nodes": [collection.tenant_name or collection.tenant_id or "tenant"],
                    "source_count": collection_use.get(collection.id, 0),
                    "collection_count": len(collection.key_tables),
                }
                for collection in top_collections
            ],
            "fallback": (
                f"{atlas_inventory['counts']['covered_collections']}/"
                f"{atlas_inventory['counts']['collections']} collections have Atlas pages."
            ),
        },
        {
            "title": "Claim to Experiment Flow",
            "claim": "The Atlas should let a reader move from synthesis to reusable claims, then into directions and concrete hypotheses.",
            "items": [
                {
                    "title": "Claims",
                    "url": "/atlas/claims",
                    "summary": "Evidence-backed statements reused across topics.",
                    "nodes": [page.title for page in claims[:4]],
                    "source_count": len(claims),
                    "collection_count": 0,
                },
                {
                    "title": "Directions",
                    "url": "/atlas/directions",
                    "summary": "High-value research opportunities grounded in existing work.",
                    "nodes": [page.title for page in directions[:4]],
                    "source_count": len(directions),
                    "collection_count": 0,
                },
                {
                    "title": "Hypotheses",
                    "url": "/atlas/hypotheses",
                    "summary": "Testable units that can become projects or experiments.",
                    "nodes": [page.title for page in hypotheses[:4]],
                    "source_count": len(hypotheses),
                    "collection_count": 0,
                },
                {
                    "title": "Opportunities",
                    "url": "/atlas/opportunities",
                    "summary": "Concrete next analyses prioritized from Atlas evidence and reusable products.",
                    "nodes": [page.title for page in opportunities[:4]],
                    "source_count": len(opportunities),
                    "collection_count": 0,
                },
            ],
            "fallback": f"{len(claims)} claims, {len(directions)} directions, {len(hypotheses)} hypotheses, and {len(opportunities)} opportunities are currently indexed.",
        },
        {
            "title": "Derived Product Reuse",
            "claim": "Reusable scores, labels, mappings, and joins are the outputs most likely to compound across projects.",
            "items": _page_refs(derived_products, limit=6),
            "fallback": f"{len(derived_products)} derived products are currently tracked from {len(data_pages)} data pages.",
        },
        {
            "title": "Tension and Resolution",
            "claim": "Apparent conflicts are preserved as reviewable objects with evidence on multiple sides and resolving work.",
            "items": _page_refs(conflicts, limit=6),
            "fallback": f"{len(conflicts)} tension pages track where synthesis needs reconciliation.",
        },
    ]


def _related_page_groups(related_pages: list[AtlasPage]) -> dict[str, list[AtlasPage]]:
    groups: dict[str, list[AtlasPage]] = {}
    for page in related_pages:
        groups.setdefault(page.type, []).append(page)
    return dict(sorted(groups.items()))


def _atlas_landing_context(repo_data: RepositoryData, context: dict) -> dict:
    atlas_index = repo_data.atlas_index
    atlas_page = atlas_index.get_page_by_path("atlas") or next(
        (p for p in atlas_index.pages if p.type == "atlas"), None
    )

    data_pages = [
        p for p in atlas_index.pages_by_section("data") if p.path != "data/index"
    ]
    data_page_groups = {
        "collections": atlas_index.pages_by_type("data_collection"),
        "data_types": atlas_index.pages_by_type("data_type"),
        "derived_products": atlas_index.pages_by_type("derived_product"),
        "joins": atlas_index.pages_by_type("join_recipe"),
        "gaps": atlas_index.pages_by_type("data_gap"),
    }
    claim_pages = atlas_index.pages_by_type("claim")
    direction_pages = atlas_index.pages_by_type("direction")
    hypothesis_pages = atlas_index.pages_by_type("hypothesis")
    conflict_pages = atlas_index.pages_by_type("conflict")
    opportunity_pages = atlas_index.pages_by_type("opportunity")
    opportunity_contexts = build_opportunity_contexts(repo_data)
    reuse_overview = build_reuse_overview(repo_data)
    atlas_inventory = build_atlas_inventory(repo_data)
    context.update(
        {
            "atlas_index": atlas_index,
            "atlas_page": atlas_page,
            "atlas_nav": _atlas_nav(atlas_index),
            "atlas_maps": _build_atlas_maps(repo_data, atlas_inventory),
            "topic_pages": atlas_index.pages_by_type("topic"),
            "data_pages": data_pages,
            "data_page_groups": data_page_groups,
            "atlas_inventory": atlas_inventory,
            "claim_pages": claim_pages,
            "direction_pages": direction_pages,
            "hypothesis_pages": hypothesis_pages,
            "conflict_pages": conflict_pages,
            "opportunity_pages": opportunity_pages,
            "opportunity_contexts": opportunity_contexts,
            "reuse_overview": reuse_overview,
            "research_primitive_pages": (
                claim_pages + direction_pages + hypothesis_pages
            ),
        }
    )
    return context


@ROUTER_ATLAS.get("/atlas", response_class=HTMLResponse)
async def atlas_landing(
    request: Request,
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
):
    """BERIL Atlas landing page."""
    context = _atlas_landing_context(repo_data, context)
    return templates.TemplateResponse(request, "atlas/index.html", context)


@ROUTER_ATLAS.get("/atlas/{atlas_path:path}", response_class=HTMLResponse)
async def atlas_page(
    request: Request,
    atlas_path: str,
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
):
    """Render an Atlas markdown page."""
    atlas_index = repo_data.atlas_index
    page = atlas_index.get_page_by_path(atlas_path)
    if not page:
        context["error"] = f"Atlas page '{atlas_path}' not found"
        return templates.TemplateResponse(
            request, "error.html", context, status_code=404
        )

    project_map = {p.id: p for p in repo_data.projects}
    collection_map = {c.id: c for c in repo_data.collections}
    source_projects = [
        project_map[pid] for pid in page.source_projects if pid in project_map
    ]
    related_collections = [
        collection_map[cid]
        for cid in page.related_collections
        if cid in collection_map
    ]
    related_pages = [
        p
        for p in (atlas_index.get_page_by_id(pid) for pid in page.related_pages)
        if p
    ]
    derived_product_context = (
        build_derived_product_context(page, repo_data)
        if page.type == "derived_product"
        else None
    )
    opportunity_context = (
        build_opportunity_context(page, repo_data)
        if page.type == "opportunity"
        else None
    )
    topic_overview_map = build_topic_overview_map(page, repo_data)
    page_conflicts = conflicts_for_page(page, repo_data)
    page_opportunities = opportunities_for_page(page, repo_data)
    page_review_routes = review_routes_for_page(page, repo_data)
    reuse_overview = build_reuse_overview(repo_data)
    opportunity_contexts = build_opportunity_contexts(repo_data)

    context.update(
        {
            "page": page,
            "atlas_index": atlas_index,
            "atlas_nav": _atlas_nav(atlas_index),
            "section_pages": atlas_index.pages_by_section(page.section),
            "related_pages": related_pages,
            "related_page_groups": _related_page_groups(related_pages),
            "derived_product_context": derived_product_context,
            "opportunity_context": opportunity_context,
            "topic_overview_map": topic_overview_map,
            "page_conflicts": page_conflicts,
            "page_opportunities": page_opportunities,
            "page_review_routes": page_review_routes,
            "reuse_overview": reuse_overview,
            "opportunity_contexts": opportunity_contexts,
            "source_projects": source_projects,
            "source_project_ids": page.source_projects,
            "missing_source_project_ids": [
                pid for pid in page.source_projects if pid not in project_map
            ],
            "related_collections": related_collections,
            "related_collection_ids": page.related_collections,
            "missing_related_collection_ids": [
                cid for cid in page.related_collections if cid not in collection_map
            ],
        }
    )
    return templates.TemplateResponse(request, "atlas/page.html", context)


@ROUTER_COMMUNITY.get("/community/contributors", response_class=HTMLResponse)
async def community_contributors(
    request: Request,
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
):
    """Community contributors page."""

    # Sort by project count (most projects first)
    contributors = sorted(
        repo_data.contributors, key=lambda c: len(c.project_ids), reverse=True
    )
    context["contributors"] = contributors
    context["total_orcids"] = sum(1 for c in contributors if c.orcid)

    # Compute collections used per contributor
    contributor_collections = {}
    all_collections = set()
    for contributor in contributors:
        colls = set()
        for pid in contributor.project_ids:
            proj = next((p for p in repo_data.projects if p.id == pid), None)
            if proj:
                colls.update(proj.related_collections)
        contributor_collections[contributor.name] = sorted(colls)
        all_collections.update(colls)
    context["contributor_collections"] = contributor_collections
    context["total_collections_used"] = len(all_collections)

    return templates.TemplateResponse(request, "community/contributors.html", context)


@ROUTER_GENERAL.get("/about", response_class=HTMLResponse)
async def about(
    request: Request,
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
):
    """About page."""
    context["primary_collections"] = repo_data.get_collections_by_category(
        CollectionCategory.PRIMARY
    )
    return templates.TemplateResponse(request, "about/about.html", context)


# Webhook endpoint for data cache updates
@ROUTER_GENERAL.post("/api/webhook/data-update")
async def data_update_webhook(
    request: Request,
    x_webhook_signature: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Webhook endpoint to receive data cache update notifications.

    Expected to be called by GitHub Actions after building new cache.
    Validates signature, reloads repo_data, and runs the project importer.
    """
    settings = get_settings()

    # Read the request body
    body = await request.body()

    # Verify webhook signature if secret is configured
    if settings.webhook_secret:
        if not x_webhook_signature:
            logger.warning("Webhook request missing signature")
            raise HTTPException(status_code=401, detail="Missing webhook signature")

        # Compute expected signature
        expected_signature = hmac.new(
            settings.webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(x_webhook_signature, expected_signature):
            logger.warning("Webhook signature validation failed")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    logger.info("Received data update webhook notification")

    # Pull latest changes and reload
    if settings.data_repo_url:
        try:
            logger.info("Pulling latest changes from git repository")

            # Pull latest changes
            await pull_latest(settings.data_repo_path, settings.data_repo_branch)

            # Reload from local git repo
            data_file = settings.data_repo_path / "data_cache" / "data.pkl.gz"
            request.app.state.repo_data = load_repository_data(data_file)
            request.app.state.base_context = generate_base_context(settings, request.app.state.repo_data)

            logger.info(
                f"Data reloaded successfully. New last_updated: {request.app.state.repo_data.last_updated}"
            )

            # Migrate updated project files from the freshly-pulled repo into the DB
            storage = LocalFileStorage(settings.user_projects_root)
            pulled_projects_dir = settings.data_repo_path / "projects"
            summary = await run_full_migration(db, storage, pulled_projects_dir)
            logger.info(
                "Post-webhook import: %d imported, %d skipped, %d failed",
                summary.imported, summary.skipped, summary.failed,
            )

            return JSONResponse(
                {
                    "status": "success",
                    "message": "Data reloaded successfully from git",
                    "last_updated": request.app.state.repo_data.last_updated.isoformat()
                    if request.app.state.repo_data.last_updated
                    else None,
                    "import": {
                        "imported": summary.imported,
                        "skipped": summary.skipped,
                        "failed": summary.failed,
                    },
                }
            )
        except Exception as e:
            logger.error(f"Failed to reload data from git: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to reload data: {str(e)}"
            )
    else:
        logger.warning("Webhook received but no data_repo_url configured")
        raise HTTPException(status_code=400, detail="No git repository configured")


# Health check
@ROUTER_GENERAL.get("/health")
async def health(
    request: Request,
    context: dict = Depends(get_base_context),
):
    """Health check endpoint."""
    db_status = await check_db()
    status = "healthy"
    if db_status["status"] != "ok":
        status = "degraded"
    settings = get_settings()
    return {
        "status": status,
        "services": {
            "database": db_status
        },
        "session": context,
        "url_scheme": request.url.scheme,
        "git_commit": settings.git_commit,
        "build_date": settings.build_date
    }
