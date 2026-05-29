"""Auto-detect user identity from JupyterHub env, KBase auth, and ORCID public API.

All functions are best-effort: any network failure, missing field, or private
record returns an empty string. Designed for non-blocking use in `beril setup`.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

ORCID_PUB_API = "https://pub.orcid.org/v3.0"
KBASE_ME_PATH = "/api/V2/me"
HTTP_TIMEOUT = 5.0

_ORCID_RE = re.compile(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]")


def _http_get_json(url: str, headers: dict[str, str] | None = None) -> dict | None:
    """Best-effort GET returning parsed JSON, or None on any failure."""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            if resp.status != 200:
                return None
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def _normalize_orcid(value: str) -> str:
    """Extract the bare ORCID id from a string (env var or URL form)."""
    match = _ORCID_RE.search(value or "")
    return match.group(0) if match else ""


def detect_orcid() -> str:
    """Return ORCID from $ORCID, falling back to KBase auth /me. Empty if not found."""
    env_orcid = _normalize_orcid(os.environ.get("ORCID", ""))
    if env_orcid:
        return env_orcid

    token = (os.environ.get("KBASE_AUTH_TOKEN") or "").strip()
    auth_url = (os.environ.get("KBASE_AUTH_URL") or "").rstrip("/")
    if not (token and auth_url):
        return ""

    me = _http_get_json(f"{auth_url}{KBASE_ME_PATH}", {"Authorization": token})
    if not me:
        return ""

    for ident in me.get("idents") or []:
        if ident.get("provider") == "OrcID":
            return _normalize_orcid(ident.get("provusername") or "")
    return ""


def detect_name_from_kbase() -> str:
    """Return display name from KBase auth /me, or empty string."""
    token = (os.environ.get("KBASE_AUTH_TOKEN") or "").strip()
    auth_url = (os.environ.get("KBASE_AUTH_URL") or "").rstrip("/")
    if not (token and auth_url):
        return ""
    me = _http_get_json(f"{auth_url}{KBASE_ME_PATH}", {"Authorization": token})
    if not me:
        return ""
    return (me.get("display") or "").strip()


def detect_name_from_orcid(orcid: str) -> str:
    """Return canonical credit-name from ORCID /person, or empty string."""
    if not orcid:
        return ""
    data = _http_get_json(f"{ORCID_PUB_API}/{orcid}/person", {"Accept": "application/json"})
    if not data:
        return ""
    name = data.get("name") or {}
    credit = ((name.get("credit-name") or {}).get("value") or "").strip()
    if credit:
        return credit
    given = ((name.get("given-names") or {}).get("value") or "").strip()
    family = ((name.get("family-name") or {}).get("value") or "").strip()
    return f"{given} {family}".strip()


def detect_affiliation_from_orcid(orcid: str) -> str:
    """Return organization name of the current preferred employment, or empty."""
    if not orcid:
        return ""
    data = _http_get_json(f"{ORCID_PUB_API}/{orcid}/employments", {"Accept": "application/json"})
    if not data:
        return ""

    candidates: list[tuple[int, dict]] = []
    for group in data.get("affiliation-group") or []:
        for summary in group.get("summaries") or []:
            emp = summary.get("employment-summary")
            if not emp:
                continue
            if emp.get("end-date") is not None:
                continue
            try:
                idx = int(emp.get("display-index") or 0)
            except (TypeError, ValueError):
                idx = 0
            candidates.append((idx, emp))

    if not candidates:
        return ""
    # ORCID renders highest display-index at the top — pick the user's preferred entry.
    candidates.sort(key=lambda x: x[0], reverse=True)
    org = candidates[0][1].get("organization") or {}
    return (org.get("name") or "").strip()


def detect_user_identity() -> dict[str, str]:
    """Best-effort detection of name, affiliation, ORCID. Empty strings on miss."""
    orcid = detect_orcid()
    name = detect_name_from_orcid(orcid) or detect_name_from_kbase()
    affiliation = detect_affiliation_from_orcid(orcid)
    return {"name": name, "affiliation": affiliation, "orcid": orcid}


def is_on_jupyterhub() -> bool:
    """True when running inside a JupyterHub-spawned single-user session."""
    return bool(os.environ.get("JUPYTERHUB_USER"))


def print_jupyterhub_path_hint(repo_root) -> None:
    """If on JupyterHub, print a path/navigation hint so users know where to
    look in the JupyterLab file browser. No-op off-hub.

    Users on JupyterHub commonly miss that they need to navigate the left-side
    file browser to actually see their work. The clone path is in their home
    directory, but the file browser opens at home by default and shows many
    sibling files; the BERIL repo isn't visually obvious. A path-with-arrows
    hint costs nothing and saves a real support burden.
    """
    if not is_on_jupyterhub():
        return
    repo_root = Path(repo_root)
    home = Path.home()
    try:
        rel = repo_root.relative_to(home)
        display_path = f"~/{rel}"
        breadcrumb_parts = list(rel.parts)
    except ValueError:
        display_path = str(repo_root)
        breadcrumb_parts = list(repo_root.parts)
    breadcrumb = "  →  ".join([*breadcrumb_parts, "projects", "<your_project>"])
    print()
    print("  You're on JupyterHub. Your work lives at:")
    print(f"    {display_path}")
    print()
    print("  In the JupyterLab file browser (left sidebar), navigate to:")
    print(f"    {breadcrumb}")
    print()
