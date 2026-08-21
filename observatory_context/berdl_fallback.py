"""BERDL lakehouse fallback for reading project files when OpenViking is down.

This is the *middle* tier of the query CLI's degraded path:

    OpenViking (semantic)  →  BERDL lakehouse archive  →  local project files

Projects are archived to the lakehouse object store by ``/submit`` (see
``tools/lakehouse_upload.py``) at ``s3://<bucket>/<tenant>/projects/<id>/...``,
mirroring the local ``projects/`` tree. When OpenViking is unreachable, a
``read``/``overview`` for a project resource can still be served from that
archive — a fresher and more complete source than the local checkout, which may
lag the submitted copy.

Only *direct file fetches* use this tier (``read``, ``overview``). Keyword search
(``find``/``grep``) is not routed here: it would mean downloading the whole
corpus per query, so it drops straight to the local keyword fallback instead.

Any of "no credentials", "endpoint unreachable", "access denied", or "object not
archived" raises :class:`BerdlUnavailable`, which the caller catches to fall
through to the local tier. Nothing here talks to the network at import time.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import fallback
from .config import (
    LAKEHOUSE_BUCKET,
    ContextConfig,
    lakehouse_projects_key,
    s3_settings,
)
from .selection import MEMORY_DIR_NAME, PROJECT_CURATED_NAMES

BANNER = (
    "⚠ knowledge layer unavailable — served from the BERDL lakehouse archive "
    "(submitted copy); it may differ from your local working tree."
)

# S3 error codes that mean "BERDL can't answer this" rather than "unexpected
# bug". AccessDenied → the user lacks permission (still degrade to local);
# NoSuchKey/NoSuchBucket → the project isn't archived (or wrong location).
_UNAVAILABLE_S3_CODES = frozenset(
    {"AccessDenied", "NoSuchKey", "NoSuchBucket", "403", "404"}
)

_RESOURCES_PREFIX = "viking://resources/"
_PROJECTS_PREFIX = f"{_RESOURCES_PREFIX}projects/"


class BerdlUnavailable(Exception):
    """The lakehouse tier cannot serve this request — caller should fall back.

    Raised for missing credentials, an unreachable endpoint, permission
    denial, or a resource that isn't archived. Carries a short human reason so
    the caller can surface *why* it degraded.
    """


def _resolve_credentials() -> dict[str, str | None] | None:
    """Return ``{endpoint_url, access_key, secret_key}`` or ``None`` if unusable.

    Env first (:func:`config.s3_settings`); if keys are absent, try the
    ``berdl-remote`` helper the same way ``scripts/get_minio_creds.py`` does.
    ``None`` means no usable credentials → the tier is unavailable.
    """
    settings = s3_settings()
    if settings["access_key"] and settings["secret_key"]:
        return settings

    remote = _credentials_from_berdl_remote()
    if remote is None:
        return None
    # Keep the resolved endpoint precedence (S3_ENDPOINT_URL/MINIO_ENDPOINT_URL)
    # unless berdl-remote supplied one explicitly. get_minio_creds returns the
    # canonical S3_* keys regardless of which spelling the pod actually had.
    return {
        "endpoint_url": remote.get("S3_ENDPOINT_URL") or settings["endpoint_url"],
        "access_key": remote.get("S3_ACCESS_KEY"),
        "secret_key": remote.get("S3_SECRET_KEY"),
    }


def _credentials_from_berdl_remote() -> dict[str, str] | None:
    """Reuse ``get_minio_creds.resolve_from_berdl_remote`` if it is importable.

    The helper lives under ``scripts/`` (not a package), so the import is
    guarded: if it can't be loaded we simply have no remote credentials.
    """
    try:
        import importlib.util

        script = Path(__file__).resolve().parents[1] / "scripts" / "get_minio_creds.py"
        spec = importlib.util.spec_from_file_location("get_minio_creds", script)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except (OSError, ImportError):
        return None
    # bootstrap_remote=False: never spawn a JupyterHub server on a degraded
    # read path — only use creds that are already available.
    return module.resolve_from_berdl_remote(False)


def _s3_client():
    """Build a boto3 S3 client for the lakehouse, or raise ``BerdlUnavailable``.

    ``boto3`` is an optional dependency (``knowledge`` group). If it or the
    credentials are missing, the tier is unavailable.
    """
    creds = _resolve_credentials()
    if creds is None or not creds["access_key"] or not creds["secret_key"]:
        raise BerdlUnavailable("no S3 credentials for the lakehouse")
    try:
        import boto3
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise BerdlUnavailable("boto3 is not installed") from exc
    return boto3.client(
        "s3",
        endpoint_url=creds["endpoint_url"],
        aws_access_key_id=creds["access_key"],
        aws_secret_access_key=creds["secret_key"],
    )


def uri_to_bucket_key(uri: str) -> tuple[str, str]:
    """Map a project resource URI to an ``(bucket, key)`` in the lakehouse.

    Only ``viking://resources/projects/<id>/<path>`` maps to the archive; docs
    and other resources are not stored there, so they raise
    :class:`BerdlUnavailable` (→ local fallback).
    """
    if not uri.startswith(_PROJECTS_PREFIX):
        raise BerdlUnavailable(f"no lakehouse archive for resource: {uri}")
    rest = uri[len(_PROJECTS_PREFIX):].strip("/")
    if not rest:
        raise BerdlUnavailable("cannot resolve the projects root to a single object")
    parts = rest.split("/", 1)
    project_id = parts[0]
    rel_path = parts[1] if len(parts) > 1 else ""
    return LAKEHOUSE_BUCKET, lakehouse_projects_key(project_id, rel_path)


def _get_object_text(client, bucket: str, key: str) -> str:
    """Fetch an object's UTF-8 body, translating S3 failures to unavailability."""
    try:
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise BerdlUnavailable("botocore is not installed") from exc
    try:
        response = client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read().decode("utf-8", errors="replace")
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        if code in _UNAVAILABLE_S3_CODES:
            raise BerdlUnavailable(f"lakehouse {code} for {key}") from exc
        raise BerdlUnavailable(f"lakehouse error for {key}: {code}") from exc
    except BotoCoreError as exc:  # endpoint unreachable, connection error, etc.
        raise BerdlUnavailable(f"lakehouse unreachable: {exc}") from exc


def berdl_available(config: ContextConfig) -> bool:
    """Cheap probe: can we reach the lakehouse and are we authorized?

    Lists a single object under the projects prefix. Returns ``False`` on any
    credential/reachability/permission problem, without raising — parallel to
    ``openviking_client.server_reachable``.
    """
    try:
        client = _s3_client()
        from botocore.exceptions import BotoCoreError, ClientError
    except (BerdlUnavailable, ImportError):
        return False
    try:
        client.list_objects_v2(
            Bucket=LAKEHOUSE_BUCKET,
            Prefix=lakehouse_projects_key("", ""),
            MaxKeys=1,
        )
        return True
    except (ClientError, BotoCoreError):
        return False


def berdl_read(config: ContextConfig, uri: str) -> str:
    """Read a project resource from the lakehouse archive.

    Raises :class:`BerdlUnavailable` if the tier can't serve it (no creds,
    unreachable, unauthorized, or not archived).
    """
    bucket, key = uri_to_bucket_key(uri)
    client = _s3_client()
    return _get_object_text(client, bucket, key)


def berdl_overview(config: ContextConfig, uri: str) -> str:
    """Overview of a project resource from the lakehouse.

    For a project directory URI (``.../projects/<id>/``) this returns the first
    lines of its archived ``README.md``, mirroring the local overview. For a
    file URI it returns the file's content.
    """
    bucket, key = uri_to_bucket_key(uri)
    client = _s3_client()
    # Directory form (``.../projects/<id>/``) overviews the archived README;
    # a file URI returns the file itself. `key` never has a trailing slash.
    if uri.endswith("/"):
        text = _get_object_text(client, bucket, f"{key}/README.md")
        return "\n".join(text.splitlines()[:40])
    return _get_object_text(client, bucket, key)


# --- find (keyword search over the archived corpus) -----------------------
#
# `find` fetches files to score them, so it pulls only the *curated* corpus —
# the same files local find searches (PROJECT_CURATED_NAMES, REFUTATION_*.md,
# and memories/*.md) — never data/ or notebooks. Scoping and ranking are shared
# with the local tier via ``fallback.score_corpus``.

_PROJECTS_KEY_PREFIX = lakehouse_projects_key("", "")  # ".../projects/"
_REFUTATION_KEY = re.compile(r"REFUTATION_[1-9][0-9]*\.md$")


def _key_to_uri(key: str) -> str | None:
    """Reverse ``lakehouse_projects_key`` → ``viking://resources/projects/...``."""
    if not key.startswith(_PROJECTS_KEY_PREFIX):
        return None
    rel = key[len(_PROJECTS_KEY_PREFIX):]
    return f"{_PROJECTS_PREFIX}{rel}" if rel else None


def _is_curated_key(key: str) -> bool:
    """True if ``key`` names a curated corpus file (mirrors ``selection.py``).

    Matches the top-level curated docs and numbered refutations, plus any file
    directly under a project's ``memories/`` directory. Anything deeper (data/,
    notebooks/, figures/) is excluded, exactly like the local corpus.
    """
    rel = key[len(_PROJECTS_KEY_PREFIX):]  # "<project_id>/<path...>"
    parts = rel.split("/")
    if len(parts) == 2:  # <project_id>/<name>
        name = parts[1]
        return name in PROJECT_CURATED_NAMES or bool(_REFUTATION_KEY.fullmatch(name))
    if len(parts) == 3 and parts[1] == MEMORY_DIR_NAME:  # <id>/memories/<name>.md
        return parts[2].endswith(".md")
    return False


def _scope_prefixes(target_uri: str) -> list[str]:
    """S3 key prefixes to enumerate for a find/grep, derived from a scope URI.

    The lakehouse holds only projects, so the resources root
    (``viking://resources/``, grep's default) and the projects root both map to
    the projects prefix; a single project maps to just its prefix. Docs (and any
    other non-project scope) aren't archived here, so an empty list signals "not
    servable by BERDL" → :class:`BerdlUnavailable`.
    """
    scope = target_uri.rstrip("/")
    if scope in (_RESOURCES_PREFIX.rstrip("/"), _PROJECTS_PREFIX.rstrip("/")):
        return [_PROJECTS_KEY_PREFIX]
    if target_uri.startswith(_PROJECTS_PREFIX):
        project_id = target_uri[len(_PROJECTS_PREFIX):].strip("/").split("/")[0]
        if project_id:
            return [f"{lakehouse_projects_key(project_id)}/"]
    return []


def _list_objects(client, prefixes: list[str]) -> list[dict]:
    """List raw S3 objects (``{Key, Size, LastModified}``) under the prefixes.

    Recursive (no delimiter): returns every object below each prefix. Translates
    S3/network failures to :class:`BerdlUnavailable`.
    """
    try:
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise BerdlUnavailable("botocore is not installed") from exc
    objects: list[dict] = []
    try:
        paginator = client.get_paginator("list_objects_v2")
        for prefix in prefixes:
            for page in paginator.paginate(Bucket=LAKEHOUSE_BUCKET, Prefix=prefix):
                objects.extend(page.get("Contents", []))
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        raise BerdlUnavailable(f"lakehouse {code} listing archive") from exc
    except BotoCoreError as exc:
        raise BerdlUnavailable(f"lakehouse unreachable: {exc}") from exc
    return objects


def _list_curated_keys(client, prefixes: list[str]) -> list[str]:
    """List curated corpus object keys under the given prefixes."""
    return [obj["Key"] for obj in _list_objects(client, prefixes) if _is_curated_key(obj["Key"])]


def _curated_documents(scope_uri: str) -> list[tuple[str, str]]:
    """Resolve a scope URI to ``(uri, text)`` pairs for its curated archive.

    Shared by ``berdl_find``/``berdl_grep``: maps the scope to project prefixes,
    lists the curated keys, and fetches each. Raises :class:`BerdlUnavailable`
    (→ local fallback) for a non-project scope, missing creds, or an
    unreachable/unauthorized lakehouse.
    """
    prefixes = _scope_prefixes(scope_uri)
    if not prefixes:
        raise BerdlUnavailable(f"no lakehouse archive for scope: {scope_uri}")
    client = _s3_client()
    documents: list[tuple[str, str]] = []
    for key in _list_curated_keys(client, prefixes):
        uri = _key_to_uri(key)
        if uri is None:
            continue
        documents.append((uri, _get_object_text(client, LAKEHOUSE_BUCKET, key)))
    return documents


def berdl_find(config: ContextConfig, query: str, target_uri: str, limit: int) -> dict:
    """Keyword search over the archived curated corpus.

    Enumerates curated files under ``target_uri`` in the lakehouse, fetches
    them, and ranks with the shared scorer. Raises :class:`BerdlUnavailable`
    (→ local fallback) if the tier can't serve the scope — no creds,
    unreachable, unauthorized, or a non-project scope (e.g. docs).
    """
    documents = _curated_documents(target_uri)
    return fallback.score_corpus(query, documents, limit, source="berdl")


def berdl_grep(
    config: ContextConfig,
    pattern: str,
    uri: str,
    *,
    case_insensitive: bool = False,
    exclude_uri: str | None = None,
    node_limit: int | None = None,
) -> dict:
    """Exact line-match search over the archived curated corpus.

    Same corpus and scoping as ``berdl_find``; matching/``exclude_uri``/
    ``node_limit`` are handled by the shared ``fallback.grep_documents``. Raises
    :class:`BerdlUnavailable` (→ local fallback) when the tier can't serve the
    scope — no creds, unreachable, unauthorized, or a non-project scope.
    """
    documents = _curated_documents(uri)
    return fallback.grep_documents(
        pattern,
        documents,
        case_insensitive=case_insensitive,
        exclude_uri=exclude_uri,
        node_limit=node_limit,
        source="berdl",
    )


# --- structural navigation (ls / glob / tree / stat) ----------------------
#
# These enumerate the archive's object layout rather than file contents, so —
# unlike find/grep — they are NOT limited to the curated corpus: they reflect
# every archived object (data/, notebooks/, figures/). They map a project URI to
# an S3 key prefix, list under it, and shape the objects into the structure the
# corresponding OpenViking command returns. Every result carries
# ``degraded: True`` / ``source: "berdl"`` so a caller can tell the tier apart.
#
# Scope is projects-only (the lakehouse holds nothing else): the resources root
# and projects root both map to the projects prefix; a docs/other scope raises
# BerdlUnavailable. There is no local equivalent for these commands, so the CLI
# router degrades them to an "unavailable" notice rather than to local search.


def _uri_to_prefix(uri: str) -> str:
    """Map any project (sub)tree URI to its S3 key prefix (trailing slash).

    Accepts the resources/projects roots and any depth beneath a project
    (``.../projects/alpha/memories/``). Raises :class:`BerdlUnavailable` for a
    non-project scope (docs, etc.), which has no lakehouse archive.
    """
    scope = uri.rstrip("/")
    if scope in (_RESOURCES_PREFIX.rstrip("/"), _PROJECTS_PREFIX.rstrip("/")):
        return _PROJECTS_KEY_PREFIX
    if uri.startswith(_PROJECTS_PREFIX):
        rel = uri[len(_PROJECTS_PREFIX):].strip("/")
        base = _PROJECTS_KEY_PREFIX + rel
        return base + "/" if rel else _PROJECTS_KEY_PREFIX
    raise BerdlUnavailable(f"no lakehouse archive for scope: {uri}")


# Entry field names mirror the OpenViking ls/tree output so a caller parses
# either identically. Object storage has no directory objects, so synthesized
# directory entries omit a real size/modTime (reported as 0/None). `mode` is a
# best-effort POSIX-ish constant (dir 0o755 / file 0o644) — it isn't tracked in
# the archive but the field is present for shape parity.
_DIR_MODE = 0o755
_FILE_MODE = 0o644


def _file_entry(obj: dict, *, rel_path: str | None = None) -> dict:
    entry = {
        "name": obj["Key"].rstrip("/").rsplit("/", 1)[-1],
        "size": obj.get("Size"),
        "mode": _FILE_MODE,
        "modTime": obj.get("LastModified"),
        "isDir": False,
        "uri": _key_to_uri(obj["Key"]),
    }
    if rel_path is not None:
        entry["rel_path"] = rel_path
    return entry


def _dir_entry(key_prefix: str, *, rel_path: str | None = None) -> dict:
    entry = {
        "name": key_prefix.rstrip("/").rsplit("/", 1)[-1],
        "size": 0,
        "mode": _DIR_MODE,
        "modTime": None,
        "isDir": True,
        "uri": _key_to_uri(key_prefix.rstrip("/")),
    }
    if rel_path is not None:
        entry["rel_path"] = rel_path
    return entry


def berdl_ls(
    config: ContextConfig, uri: str, *, simple: bool = False, recursive: bool = False
) -> list:
    """List archived resources under ``uri`` — one level, or recursively.

    Matches OpenViking ``ls``: returns a JSON array of entries
    (``{name, size, mode, modTime, isDir, uri}``). ``simple=True`` returns a flat
    list of URI strings ("path list"). Object storage has no directory objects,
    so immediate subdirectories are synthesized from shared key prefixes.
    """
    prefix = _uri_to_prefix(uri)
    client = _s3_client()
    objects = _list_objects(client, [prefix])

    if recursive:
        entries = [_file_entry(o) for o in objects]
    else:
        files: list[dict] = []
        subdirs: dict[str, dict] = {}
        for obj in objects:
            rel = obj["Key"][len(prefix):]
            if "/" not in rel:
                files.append(_file_entry(obj))
            else:
                child = rel.split("/", 1)[0]
                subdirs.setdefault(child, _dir_entry(prefix + child))
        entries = files + list(subdirs.values())

    entries.sort(key=lambda e: e["uri"] or "")
    if simple:
        return [e["uri"] for e in entries if e.get("uri")]
    return entries


def _glob_to_regex(pattern: str) -> "re.Pattern[str]":
    """Translate a ``*``/``**`` glob into a regex matching a relative key.

    ``**/`` matches any number of leading segments (including none); a bare
    ``**`` matches across segments; a single ``*`` matches non-slash runs.
    """
    out = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out))


def berdl_glob(config: ContextConfig, pattern: str, uri: str) -> dict:
    """Enumerate archived URIs under ``uri`` matching a glob ``pattern``.

    Matches OpenViking ``glob``: ``{"matches": [...], "count": N}``. ``pattern``
    is relative to ``uri``; ``*`` matches within a segment, ``**`` across
    segments.
    """
    prefix = _uri_to_prefix(uri)
    client = _s3_client()
    regex = _glob_to_regex(pattern)
    matches = []
    for obj in _list_objects(client, [prefix]):
        rel = obj["Key"][len(prefix):]
        if regex.fullmatch(rel):
            resource_uri = _key_to_uri(obj["Key"])
            if resource_uri:
                matches.append(resource_uri)
    matches.sort()
    return {"matches": matches, "count": len(matches)}


def berdl_tree(config: ContextConfig, uri: str, node_limit: int = 1000) -> list:
    """Return the archived resource hierarchy under ``uri``.

    Matches OpenViking ``tree``: a **flat**, pre-order JSON array of entries,
    each with a ``rel_path`` (relative to ``uri``) plus the standard entry
    fields. Synthesized directory entries appear before their contents; capped
    at ``node_limit`` entries.
    """
    prefix = _uri_to_prefix(uri)
    client = _s3_client()
    objects = sorted(_list_objects(client, [prefix]), key=lambda o: o["Key"])

    entries: list[dict] = []
    seen_dirs: set[str] = set()
    for obj in objects:
        rel = obj["Key"][len(prefix):]
        if not rel:
            continue
        # Emit any not-yet-seen ancestor directories in order, then the file.
        segments = rel.split("/")
        for depth in range(1, len(segments)):
            dir_rel = "/".join(segments[:depth])
            if dir_rel not in seen_dirs:
                seen_dirs.add(dir_rel)
                if len(entries) >= node_limit:
                    return entries
                entries.append(_dir_entry(prefix + dir_rel, rel_path=dir_rel))
        if len(entries) >= node_limit:
            return entries
        entries.append(_file_entry(obj, rel_path=rel))
    return entries


def berdl_stat(config: ContextConfig, uri: str) -> dict:
    """Return metadata for a single archived resource.

    Matches OpenViking ``stat``: ``{name, size, mode, modTime, isDir, count?}``.
    A file URI resolves via ``head_object``; a directory URI (trailing slash, or
    a prefix with no exact object) aggregates ``count`` and the latest
    ``modTime`` under it. Raises :class:`BerdlUnavailable` if nothing is
    archived at the URI.
    """
    try:
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise BerdlUnavailable("botocore is not installed") from exc

    client = _s3_client()
    name = uri.rstrip("/").rsplit("/", 1)[-1]

    # Try an exact object first (file form), unless the URI is clearly a dir.
    if not uri.endswith("/"):
        _, key = uri_to_bucket_key(uri)
        try:
            head = client.head_object(Bucket=LAKEHOUSE_BUCKET, Key=key)
            return {
                "name": name,
                "size": head.get("ContentLength"),
                "mode": _FILE_MODE,
                "modTime": head.get("LastModified"),
                "isDir": False,
                "uri": uri,
            }
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code", ""))
            if code not in ("404", "NoSuchKey", "NotFound"):
                raise BerdlUnavailable(f"lakehouse {code} for {key}") from exc
            # fall through: treat as a directory prefix
        except BotoCoreError as exc:
            raise BerdlUnavailable(f"lakehouse unreachable: {exc}") from exc

    prefix = _uri_to_prefix(uri)
    objects = _list_objects(client, [prefix])
    if not objects:
        raise BerdlUnavailable(f"no archived resource at {uri}")
    latest = max((o.get("LastModified") for o in objects if o.get("LastModified")), default=None)
    return {
        "name": name,
        "size": sum(o.get("Size", 0) for o in objects),
        "mode": _DIR_MODE,
        "modTime": latest,
        "isDir": True,
        "uri": uri.rstrip("/"),
        "count": len(objects),
    }
