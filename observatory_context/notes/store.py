"""Live note and observation serialization helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import yaml

from observatory_context._text import compact_text, slugify, split_frontmatter
from observatory_context.uris import build_project_live_note_uri, build_shared_live_note_uri


def build_live_resource(
    kind: str,
    now: str | datetime,
    title: str,
    body: str,
    project_id: str | None = None,
    source_ref: str | None = None,
    tags: list[str] | None = None,
    links: list[str] | None = None,
) -> dict[str, Any]:
    """Build deterministic metadata and content for a live note resource."""
    timestamp = _coerce_timestamp(now)
    date = timestamp[:10]
    token = timestamp.replace("-", "").replace(":", "")
    slug = slugify(title or body.split(".", 1)[0] or kind)
    resource_id = f"{kind}-{token}-{slug}"
    uri = (
        build_project_live_note_uri(project_id, resource_id, date)
        if project_id
        else build_shared_live_note_uri(resource_id, date)
    )
    metadata = {
        "id": resource_id,
        "kind": kind,
        "title": title,
        "project_ids": [project_id] if project_id else [],
        "tags": list(tags or []),
        "source_refs": [source_ref] if source_ref else [],
        "links": list(links or []),
        "created_at": timestamp,
        "updated_at": timestamp,
        "author_or_actor": "observatory_context",
        "provenance": {"origin": "openviking-live-context"},
        "summary": compact_text(body) or "",
    }
    content = serialize_live_resource(metadata, body)
    return {"uri": uri, "metadata": metadata, "content": content}


def serialize_live_resource(metadata: dict[str, Any], body: str) -> str:
    """Serialize live resource content with YAML front matter."""
    front_matter = yaml.safe_dump(metadata, sort_keys=True).strip()
    return f"---\n{front_matter}\n---\n\n{body.strip()}\n"


def parse_live_resource(uri: str, content: str, fallback_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Parse live resource content from YAML front matter plus markdown body."""
    metadata, body = split_frontmatter(content, dict(fallback_metadata or {}))
    return {
        "id": metadata["id"],
        "uri": uri,
        "kind": metadata["kind"],
        "title": metadata.get("title") or metadata["id"],
        "project_ids": list(metadata.get("project_ids") or []),
        "tags": list(metadata.get("tags") or []),
        "source_refs": list(metadata.get("source_refs") or []),
        "links": list(metadata.get("links") or []),
        "summary": metadata.get("summary") or compact_text(body) or "",
        "body": body.strip(),
        "metadata": metadata,
    }


def _coerce_timestamp(value: str | datetime) -> str:
    if isinstance(value, datetime):
        text = value.isoformat()
    else:
        text = value
    if text.endswith("Z"):
        return text
    if "+" in text:
        return text.replace("+00:00", "Z")
    return f"{text}Z"


