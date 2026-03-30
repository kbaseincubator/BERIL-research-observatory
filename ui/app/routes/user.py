"""User profile routes."""

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

import app.context as ctx
from app.context import get_base_context, get_repo_data
from app.models import RepositoryData

logger = logging.getLogger(__name__)

ROUTER_USER = APIRouter(tags=["User"])


@ROUTER_USER.get("/user_profile", response_class=HTMLResponse)
async def user_profile(
    request: Request,
    repo_data: RepositoryData = Depends(get_repo_data),
    context: dict = Depends(get_base_context),
):
    """Logged-in user's profile page."""
    user = context.get("current_user")
    if user is None:
        return ctx.templates.TemplateResponse(request, "unauthenticated.html", context)

    # Find the matching Contributor record by ORCiD
    contributor = next(
        (c for c in repo_data.contributors if c.orcid == user.orcid_id),
        None,
    )

    # Gather owned projects — matched by contributor ORCiD or name fallback
    owned_projects = []
    for project in repo_data.projects:
        for contrib in project.contributors:
            if contrib.orcid and contrib.orcid == user.orcid_id:
                owned_projects.append(project)
                break
            if contributor and contrib.name == contributor.name:
                owned_projects.append(project)
                break

    # Collections used across owned projects
    collections_used_ids: set[str] = set()
    for project in owned_projects:
        collections_used_ids.update(project.related_collections)
    collections_used = [
        c for c in repo_data.collections if c.id in collections_used_ids
    ]

    # Review status breakdown
    review_counts = {"reviewed": 0, "needs_re_review": 0, "not_reviewed": 0}
    for project in owned_projects:
        status = project.review_status.value
        if status == "Reviewed":
            review_counts["reviewed"] += 1
        elif status == "Needs Re-review":
            review_counts["needs_re_review"] += 1
        else:
            review_counts["not_reviewed"] += 1

    context.update(
        {
            "contributor": contributor,
            "owned_projects": owned_projects,
            "collections_used": collections_used,
            "review_counts": review_counts,
        }
    )
    return ctx.templates.TemplateResponse(request, "profile.html", context)
