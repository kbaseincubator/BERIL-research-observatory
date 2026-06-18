import logging

from app.auth import BerilUser, require_user_page
from app.context import get_base_context
from app.db.session import get_db
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

ROUTER_OV = APIRouter(tags=["openviking"])



@ROUTER_OV.get("/api/ov/user")
async def get_ov_user_info(
    request: Request,
    user: BerilUser = Depends(require_user_page),
    context: dict = Depends(get_base_context),
    db: AsyncSession = Depends(get_db)
):
    return {
        "id": user.id,
        "orcid": user.orcid_id,
        "display": user.display_name,
        "last_login": user.last_login_at
    }
