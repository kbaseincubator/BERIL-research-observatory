#!/usr/bin/env python3
"""
Retroactive-load a completed Claude Code .jsonl transcript into Langfuse.

Reuses the turn-reconstruction and backdated-span logic from Langfuse's own
official Claude Code hook (langfuse_hook_official.py, vendored unmodified
alongside this file from
https://langfuse.com/integrations/developer-tools/claude-code) rather than
reimplementing it. The only things this script does differently from the
live hook:

  - reads the ENTIRE transcript file in one pass (no incremental offset /
    state-file tracking — the hook's SessionState mechanism exists to avoid
    re-processing on every Stop event; a one-shot retro-load has no "next
    time" to be incremental for)
  - no TRACE_TO_LANGFUSE gate, no stdin hook payload — session_id and
    transcript_path are given directly
  - tags every emitted trace with "retro-load" (+ whatever --tag values are
    passed) so these are filterable apart from live-captured traces
  - keeps its own idempotency marker, in ~/.retro_load_markers/ (keyed by a
    hash of the source path, NOT a sibling file next to the source -- the
    frozen workshop corpus is read-only from our account) so re-running
    against the same transcript does not duplicate traces in Langfuse, since
    Langfuse itself has no create-time dedupe

Dev/test usage (local transcripts only -- see README.md's governance section
before ever pointing this at a pod-resident transcript: retro-loading pod
.jsonl requires running THIS SCRIPT ON THE POD, never copying the raw file
off it):

    export LANGFUSE_PUBLIC_KEY=pk-lf-...
    export LANGFUSE_SECRET_KEY=sk-lf-...
    export LANGFUSE_HOST=https://us.cloud.langfuse.com
    python3 retro_load.py --dry-run /path/to/session.jsonl
    python3 retro_load.py --tag beril-hackathon-2026-05-07 /path/to/session.jsonl
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")  # must run before langfuse is imported anywhere

sys.path.insert(0, str(Path(__file__).parent))
try:
    from langfuse_hook_official import (  # noqa: E402
        build_turns,
        emit_turn,
        parse_ts,
    )
except SystemExit:
    # The vendored hook does sys.exit(0) on import if langfuse/opentelemetry aren't
    # installed (its own "fail-open" design, since it runs as a best-effort Claude Code
    # hook where silence is preferred over breaking a session). That's the wrong default
    # here: a silent 0 exit is indistinguishable from a real, successful --dry-run, and
    # would defeat build_manifest.py's return-code check on this script. Turn it loud.
    print("langfuse_hook_official.py failed to import (likely missing the langfuse/"
          "opentelemetry packages) -- treating that as a hard failure, not a silent no-op.",
          file=sys.stderr)
    sys.exit(1)


def load_all_jsonl(transcript_path: Path):
    msgs = []
    with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                msgs.append(json.loads(line))
            except Exception as e:
                print(f"  ! skipping unparseable line: {e}", file=sys.stderr)
    return msgs


MARKER_DIR = Path.home() / ".retro_load_markers"


def marker_path(transcript_path: Path) -> Path:
    # A sibling file next to the source transcript fails with PermissionError whenever
    # the source lives in a read-only/shared location we don't own (e.g. the frozen
    # workshop corpus, symlinked into another user's global_share storage). Keep markers
    # in our own home instead, keyed by a hash of the resolved source path so re-running
    # against the same file is still idempotent regardless of where it lives.
    MARKER_DIR.mkdir(exist_ok=True)
    key = hashlib.sha256(str(transcript_path).encode("utf-8")).hexdigest()
    return MARKER_DIR / f"{key}.json"


def already_loaded(transcript_path: Path) -> dict | None:
    p = marker_path(transcript_path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def write_marker(transcript_path: Path, session_id: str, turn_count: int, tags: list[str]) -> None:
    marker_path(transcript_path).write_text(
        json.dumps(
            {
                "session_id": session_id,
                "turns_emitted": turn_count,
                "tags": tags,
                "loaded_at_utc": None,  # not stamped from the script's own clock: it says nothing
                                         # about when the underlying conversation happened, which
                                         # is the whole point of a marker for a *retroactive* load
            },
            indent=2,
        )
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript", type=Path, help="path to a Claude Code .jsonl transcript")
    ap.add_argument("--session-id", help="override session id (default: derived from filename stem)")
    ap.add_argument("--tag", action="append", default=[], help="extra tag to attach (repeatable)")
    ap.add_argument("--user-id", help="pseudonymous user_id for Langfuse (the pod account name, e.g. "
                                       "'mamillerpa' or 'dkishore') -- deliberately NOT a real name, since "
                                       "Langfuse's Sessions/Users views are a re-identification surface")
    ap.add_argument("--dry-run", action="store_true", help="parse and print turn summary, do not call Langfuse")
    ap.add_argument("--force", action="store_true", help="ignore an existing marker in ~/.retro_load_markers/")
    args = ap.parse_args()

    transcript_path = args.transcript.expanduser().resolve()
    if not transcript_path.exists():
        print(f"transcript not found: {transcript_path}", file=sys.stderr)
        return 1

    session_id = args.session_id or transcript_path.stem
    tags = ["claude-code", "retro-load"] + args.tag

    prior = already_loaded(transcript_path)
    if prior and not args.force:
        print(f"already retro-loaded ({prior['turns_emitted']} turns, tags={prior['tags']}); "
              f"pass --force to reload. marker: {marker_path(transcript_path)}")
        return 0

    msgs = load_all_jsonl(transcript_path)
    turns = build_turns(msgs)
    print(f"{transcript_path.name}: {len(msgs)} jsonl lines -> {len(turns)} turns")

    if args.dry_run:
        for i, t in enumerate(turns, 1):
            ts = parse_ts(t.user_msg)
            print(f"  turn {i}: {ts.isoformat() if ts else '(no timestamp)'} "
                  f"assistant_msgs={len(t.assistant_msgs)}")
        print("(dry run — nothing sent to Langfuse)")
        return 0

    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    host = os.environ.get("LANGFUSE_HOST") or os.environ.get("LANGFUSE_BASE_URL") or "https://cloud.langfuse.com"
    if not public_key or not secret_key:
        print("LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY not set in environment", file=sys.stderr)
        return 1

    from langfuse import Langfuse, propagate_attributes  # noqa: E402  (import after env check)

    langfuse = Langfuse(public_key=public_key, secret_key=secret_key, host=host)

    # emit_turn() itself sets tags=["claude-code"] via propagate_attributes; wrap in our own
    # propagate_attributes with the full tag set (and user_id, if given) so ours take effect
    # for this call stack.
    propagate_kwargs = {"tags": tags}
    if args.user_id:
        propagate_kwargs["user_id"] = args.user_id

    # emit_turn() stores str(transcript_path) verbatim into Langfuse metadata. The real
    # resolved path can carry real filesystem structure -- including, for the frozen
    # workshop corpus, another account's username where it's symlinked from -- which
    # undermines the pseudonymization this tool is otherwise careful about. Pass a
    # synthetic path built from session_id (already the trace's own identifier) instead
    # of the real one.
    safe_transcript_path = Path(f"{session_id}.jsonl")

    emitted = 0
    for i, t in enumerate(turns, 1):
        try:
            with propagate_attributes(**propagate_kwargs):
                emit_turn(langfuse, session_id, i, t, safe_transcript_path)
            emitted += 1
        except Exception as e:
            print(f"  ! turn {i} failed: {type(e).__name__}: {e}", file=sys.stderr)

    langfuse.flush()
    langfuse.shutdown()

    if emitted < len(turns):
        print(f"FAILED: only {emitted}/{len(turns)} turns emitted to {host} as session_id={session_id}; "
              f"not writing a marker so this counts as not-yet-loaded. A re-run re-emits all "
              f"turns from scratch (no per-turn state is kept, and Langfuse has no create-time "
              f"dedupe), it does not retry only the missing ones.", file=sys.stderr)
        return 1

    write_marker(transcript_path, session_id, emitted, tags)
    print(f"emitted {emitted}/{len(turns)} turns to {host} as session_id={session_id}, tags={tags}")
    print(f"marker written: {marker_path(transcript_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
