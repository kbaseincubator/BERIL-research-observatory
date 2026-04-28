"""Bridge between our chat persistence and the Claude Agent SDK's on-disk
session store.

The SDK writes a JSONL transcript per session under
``$HOME/.claude/projects/<sanitized-cwd>/<session-id>.jsonl`` and reads it
back when ``resume=<session-id>`` is passed. Our DB stores the
``sdk_session_id`` as a resume handle plus its own transcript in
``ChatMessage`` rows. When the two diverge — file missing but DB still
holds the ID — resume fails with "No conversation found". This module
handles the divergence: detect it, and synthesize a DB-backed preamble so
a cold-started session starts with the prior context intact.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable

from app.db.models import ChatMessage

# Mirrors claude_agent_sdk._internal.sessions._SANITIZE_RE. The rule is
# stable across SDK versions; if it ever changes, the existence check will
# start missing and we'll cold-start more aggressively — which is the safe
# failure mode.
_SANITIZE_RE = re.compile(r"[^a-zA-Z0-9]")


def _claude_projects_dir() -> Path:
    """Mirrors the SDK's directory-resolution rule."""
    override = os.environ.get("CLAUDE_CONFIG_DIR")
    if override:
        return Path(override) / "projects"
    return Path.home() / ".claude" / "projects"


def session_file_path(cwd: str, session_id: str) -> Path:
    """Return the path the SDK would write/read for this session."""
    sanitized = _SANITIZE_RE.sub("-", cwd)
    return _claude_projects_dir() / sanitized / f"{session_id}.jsonl"


def session_file_exists(cwd: str, session_id: str | None) -> bool:
    if not session_id:
        return False
    return session_file_path(cwd, session_id).is_file()


def build_resume_preamble(messages: Iterable[ChatMessage]) -> str:
    """Render prior messages as a plain-text preamble for cold-start.

    Called when the SDK transcript is missing but we still have our own DB
    history. We replay the conversation as context in the next user prompt
    so the model isn't starting blind. This is a pragmatic reconstruction
    — not byte-identical to the SDK's format, so prompt-cache hits are
    forfeit for this turn, but subsequent turns resume normally from the
    newly-written SDK transcript.
    """
    lines: list[str] = []
    for msg in messages:
        content = msg.content or {}
        text = content.get("text") if isinstance(content, dict) else None
        if not text:
            continue
        label = "User" if msg.role == "user" else "Assistant"
        lines.append(f"{label}: {text}")
    if not lines:
        return ""
    return (
        "[Previous conversation, reconstructed from stored history]\n"
        + "\n\n".join(lines)
        + "\n\n[End of previous conversation]\n\n"
    )
