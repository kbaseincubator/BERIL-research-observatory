"""OpenViking (OV) integration routes.

Lets an authenticated BERIL user provision an account for themselves in the
configured OpenViking instance and retrieve the resulting credentials. BERIL
acts as the ADMIN of the configured OV account (see ``settings.ov_admin_key``);
a user's OV ``user_id`` is their raw ORCiD. The OV ``user_key`` is stored
encrypted at rest and only the owning user can fetch its plaintext.
"""

import logging

from app.auth import BerilUser, require_user_api
from app.config import get_settings
from app.crypto import encrypt_secret, decrypt_secret
from app.db.crud import get_ov_credential, upsert_ov_credential
from app.db.session import get_db
from app.clients.openviking import (
    OpenVikingError,
    ov_health,
    register_ov_user,
    regenerate_ov_user_key,
)
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

ROUTER_OV = APIRouter(tags=["openviking"])


@ROUTER_OV.get("/api/ov/user")
async def get_ov_user_info(
    request: Request,
    user: BerilUser = Depends(require_user_api),
):
    """Return the BERIL-side identity for the current user."""
    return {
        "id": user.id,
        "orcid": user.orcid_id,
        "display": user.display_name,
        "last_login": user.last_login_at,
    }


@ROUTER_OV.get("/api/ov/health")
async def ov_health_check(
    user: BerilUser = Depends(require_user_api),
):
    """Report whether the configured OpenViking instance is reachable."""
    settings = get_settings()
    try:
        body = await ov_health()
        return {"status": "ok", "ov": body, "ov_url": settings.ov_url}
    except OpenVikingError as exc:
        return {"status": "unreachable", "detail": str(exc), "ov_url": settings.ov_url}


@ROUTER_OV.post("/api/ov/user", status_code=status.HTTP_201_CREATED)
async def create_ov_user(
    user: BerilUser = Depends(require_user_api),
    db: AsyncSession = Depends(get_db),
):
    """Create the user's OpenViking account if it doesn't already exist.

    Idempotent: if BERIL already holds a credential for this user, returns it
    without contacting OpenViking. If OpenViking reports the user already exists
    but BERIL has no stored key, returns 409 — the user must explicitly call the
    regenerate endpoint to mint and store a fresh key (we never silently
    invalidate an existing key that may be in use elsewhere).
    """
    settings = get_settings()

    existing = await get_ov_credential(db, user.id)
    if existing is not None:
        return {
            "account_id": existing.account_id,
            "ov_user_id": existing.ov_user_id,
            "ov_url": settings.ov_url,
            "created": False,
        }

    # ov_user_id is always the authenticated user's ORCiD — never request input.
    ov_user_id = user.orcid_id
    try:
        result = await register_ov_user(ov_user_id)
    except OpenVikingError as exc:
        if exc.status_code == status.HTTP_409_CONFLICT or exc.code == "ALREADY_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "An OpenViking user already exists for your ORCiD, but BERIL "
                    "holds no copy of its key. Call POST /api/ov/user/regenerate "
                    "to mint and store a fresh key (this invalidates the old one)."
                ),
            )
        logger.warning("OpenViking register_user failed for %s: %s", user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenViking user creation failed: {exc}",
        )

    user_key = (result or {}).get("user_key")
    if not user_key:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenViking did not return a user key on creation.",
        )

    await upsert_ov_credential(
        db,
        user.id,
        account_id=settings.ov_account_id,
        ov_user_id=ov_user_id,
        encrypted_key=encrypt_secret(user_key, settings.ov_credential_key),
    )
    logger.info("Created OpenViking user for BERIL user %s (orcid %s)", user.id, user.orcid_id)
    return {
        "account_id": settings.ov_account_id,
        "ov_user_id": ov_user_id,
        "ov_url": settings.ov_url,
        "created": True,
    }


@ROUTER_OV.post("/api/ov/user/regenerate")
async def regenerate_ov_user(
    user: BerilUser = Depends(require_user_api),
    db: AsyncSession = Depends(get_db),
):
    """Mint a fresh OpenViking key for the user and store it (destructive).

    This immediately invalidates any prior OV key for the user. It is the
    explicit recovery path for the 409 case in ``POST /api/ov/user`` and the
    rotation path for an existing credential. The new key is not returned here —
    fetch it via ``GET /api/ov/credentials``.
    """
    settings = get_settings()
    ov_user_id = user.orcid_id
    try:
        result = await regenerate_ov_user_key(ov_user_id)
    except OpenVikingError as exc:
        logger.warning("OpenViking regenerate_key failed for %s: %s", user.id, exc)
        status_code = (
            status.HTTP_404_NOT_FOUND
            if exc.code == "NOT_FOUND"
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(status_code=status_code, detail=f"OpenViking key regeneration failed: {exc}")

    user_key = (result or {}).get("user_key")
    if not user_key:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenViking did not return a user key on regeneration.",
        )

    await upsert_ov_credential(
        db,
        user.id,
        account_id=settings.ov_account_id,
        ov_user_id=ov_user_id,
        encrypted_key=encrypt_secret(user_key, settings.ov_credential_key),
    )
    logger.info("Regenerated OpenViking key for BERIL user %s (orcid %s)", user.id, user.orcid_id)
    return {
        "account_id": settings.ov_account_id,
        "ov_user_id": ov_user_id,
        "ov_url": settings.ov_url,
        "regenerated": True,
    }


@ROUTER_OV.get("/api/ov/credentials")
async def get_ov_credentials(
    user: BerilUser = Depends(require_user_api),
    db: AsyncSession = Depends(get_db),
):
    """Return the decrypted OpenViking credentials for the current user."""
    settings = get_settings()
    cred = await get_ov_credential(db, user.id)
    if cred is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No OpenViking credential for this user. Create one via POST /api/ov/user.",
        )
    return {
        "account_id": cred.account_id,
        "ov_user_id": cred.ov_user_id,
        "ov_url": settings.ov_url,
        "user_key": decrypt_secret(cred.encrypted_key, settings.ov_credential_key),
        "created_at": cred.created_at,
        "updated_at": cred.updated_at,
    }
