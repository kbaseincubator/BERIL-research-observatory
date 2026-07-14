"""ORCiD OAuth2 authentication routes."""

import logging

from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.crud import get_or_create_user
from app.db.session import get_db

logger = logging.getLogger(__name__)

ROUTER_AUTH = APIRouter(prefix="/auth", tags=["Auth"])


@ROUTER_AUTH.get("/login")
async def login(request: Request):
    """Redirect the user to ORCiD's authorization page."""
    settings = get_settings()
    if not settings.orcid_client_id:
        return RedirectResponse(url="/", status_code=302)

    authorize_url = f"{settings.orcid_base_url}/oauth/authorize"

    async with AsyncOAuth2Client(
        client_id=settings.orcid_client_id,
        redirect_uri=settings.orcid_redirect_uri,
        scope="/authenticate",
    ) as client:
        url, state = client.create_authorization_url(authorize_url)

    request.session["oauth_state"] = state
    request.session["login_next"] = request.query_params.get("next", "/")

    return RedirectResponse(url=url, status_code=302)


@ROUTER_AUTH.get("/orcid/callback")
async def orcid_callback(
    request: Request,
    code: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle the ORCiD OAuth2 callback."""
    if error or not code:
        err_text = f"ORCiD OAuth error: {error}"
        if not code:
            err_text = "ORCiD OAuth return code not given"
        logger.warning(err_text)
        # TODO: show an error message (toast?) to the user
        return RedirectResponse(url="/?auth_error=1", status_code=302)

    settings = get_settings()
    token_url = f"{settings.orcid_base_url}/oauth/token"

    try:
        async with AsyncOAuth2Client(
            client_id=settings.orcid_client_id,
            client_secret=settings.orcid_client_secret,
            redirect_uri=settings.orcid_redirect_uri,
        ) as client:
            token = await client.fetch_token(
                token_url,
                code=code,
                grant_type="authorization_code",
            )

        orcid_id = token.get("orcid")
        name = token.get("name")
        access_token = token.get("access_token")

        if not orcid_id:
            logger.error("ORCiD token response missing 'orcid' field")
            return RedirectResponse(url="/?auth_error=1", status_code=302)

        # Upsert the BERIL user record
        user, created = await get_or_create_user(db, orcid_id=orcid_id, display_name=name)
        if created:
            logger.info(f"New BERIL user created: {orcid_id} ({name}) → {user.id}")

        request.session["orcid_id"] = orcid_id
        request.session["orcid_name"] = name
        request.session["orcid_access_token"] = access_token
        request.session["beril_user_id"] = user.id
        request.session.pop("oauth_state", None)

        next_url = request.session.pop("login_next", "/")
        logger.info(f"User logged in: {orcid_id} ({name})")
        return RedirectResponse(url=next_url, status_code=302)

    except Exception as e:
        logger.error(f"ORCiD token exchange failed: {e}")
        return RedirectResponse(url="/?auth_error=1", status_code=302)


@ROUTER_AUTH.get("/logout")
async def logout(request: Request):
    """Clear the session and redirect home."""
    orcid_id = request.session.get("orcid_id", "unknown")
    request.session.clear()
    logger.info(f"User logged out: {orcid_id}")
    return RedirectResponse(url="/", status_code=302)
