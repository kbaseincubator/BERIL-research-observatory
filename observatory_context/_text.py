"""Shared text helpers for frontmatter parsing and text compaction."""

from __future__ import annotations

import re
from typing import Any

import yaml


def slugify(text: str, *, max_length: int = 48) -> str:
    """Convert *text* to a URL-safe slug.

    Parameters
    ----------
    text:
        Input string.
    max_length:
        Truncate the slug to this many characters.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower().strip()).strip("-")
    return slug[:max_length] or "entry"


def compact_text(text: str | None, limit: int = 240) -> str | None:
    """Normalize whitespace and truncate to *limit* characters."""
    if not text:
        return None
    compact = " ".join(text.split())
    return compact[:limit]


def split_frontmatter(
    content: str,
    fallback_metadata: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    """Split YAML front-matter from body text.

    Returns
    -------
    tuple
        (metadata dict, stripped body string).  If no valid front-matter
        delimiters are found the full content is returned as the body.
    """
    metadata = dict(fallback_metadata)
    body = content
    if content.startswith("---\n") and "\n---\n" in content:
        _, remainder = content.split("---\n", 1)
        front_matter, body = remainder.split("\n---\n", 1)
        metadata.update(yaml.safe_load(front_matter) or {})
    return metadata, body.strip()
