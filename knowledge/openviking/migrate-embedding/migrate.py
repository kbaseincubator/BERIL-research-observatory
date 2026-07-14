#!/usr/bin/env python3
"""Migrate the OpenViking embedding model without losing ingested source content.

Why a plain config swap crashes
--------------------------------
OpenViking stamps the embedding identity (provider/model/dimension) into the
vector collection's description metadata. On startup init_context_collection
compares that stamp to the live config; with OLD vectors present and a NEW model
configured it raises EmbeddingRebuildRequiredError and the process os._exit(1)s
before the HTTP server is usable. There is no env-var bypass.

The migration
-------------
Vectors are derived data: the source markdown / abstracts / overviews live in a
separate dir under the workspace and survive deleting the vector collection.
OpenViking ships a non-destructive re-embed path (POST /api/v1/content/reindex)
that reads retained source back out and re-embeds with the current config. So:

    reset   delete ONLY the vector collection (keep sources)
    (start container with the NEW model -> boots clean: 0 vectors -> re-stamp)
    reindex rebuild vectors from retained source, resumable + rate-limit paced
    verify  confirm the server booted and search returns hits

Subcommands
-----------
    migrate.py find    [WORKSPACE]
    migrate.py reset   [WORKSPACE] [--dry-run] [--force] [--backup-dir DIR]
    migrate.py reindex [--pacing N] [--mode ...] [--state FILE] [--roots ...]
    migrate.py verify  [--probe-query TEXT]

Dependencies: httpx + Python standard library only.
"""

# from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

import httpx

# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #

DEFAULT_WORKSPACE = "/ov/workspace"
DEFAULT_BASE = "http://0.0.0.0:1933"


def _env_base() -> str:
    return os.environ.get("OV_BASE", DEFAULT_BASE).rstrip("/")


def _server_key(required: bool = True) -> Optional[str]:
    key = os.environ.get("OV_SERVER_KEY")
    if required and not key:
        sys.exit("ERROR: OV_SERVER_KEY must be set to a ROOT or ADMIN X-API-Key")
    return key


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _client(key: Optional[str], timeout: float) -> httpx.Client:
    headers = {"Content-Type": "application/json"}
    if key:
        headers["X-API-Key"] = key
    return httpx.Client(base_url=_env_base(), headers=headers, timeout=timeout)


# --------------------------------------------------------------------------- #
# find / reset  (pure filesystem; no HTTP)
# --------------------------------------------------------------------------- #


def find_collections(workspace: Path) -> list[Path]:
    """Locate vector-collection directories under *workspace*.

    A vector collection is a directory that directly contains
    ``collection_meta.json`` AND a ``store/`` or ``index/`` subdir. The AGFS
    source tree never has this shape, so the match is specific to vectors and
    will not pick up source content. We search by the meta file rather than a
    hard-coded name so a non-default storage.vectordb.name still resolves.
    """
    if not workspace.is_dir():
        sys.exit(f"ERROR: workspace not found: {workspace}")

    found: list[Path] = []
    # maxdepth 3 equivalent: workspace/<a>/<b>/collection_meta.json
    for meta in workspace.glob("*/collection_meta.json"):
        _maybe_add(meta, found)
    for meta in workspace.glob("*/*/collection_meta.json"):
        _maybe_add(meta, found)
    return found


def _maybe_add(meta: Path, acc: list[Path]) -> None:
    d = meta.parent
    if (d / "store").is_dir() or (d / "index").is_dir():
        if d not in acc:
            acc.append(d)


def _backup_then_delete(src: Path, dest: Path) -> None:
    """Back up *src* to *dest*, then delete *src* — safe across mounts.

    shutil.move() does os.rename() first, which raises EXDEV (Errno 18) when the
    backup dir is a different mount than the workspace. Its copy+rmtree fallback
    can also leave a half-moved state. Instead we copytree into a temporary
    sibling, then atomically rename it into place (same dir, so rename is local
    and atomic), and only then rmtree the original. If anything fails before the
    rename, the partial copy is cleaned up and the original is left intact.
    """
    if dest.exists():
        raise SystemExit(f"ERROR: backup destination already exists: {dest}")

    staging = dest.with_name(dest.name + ".partial")
    if staging.exists():
        print(f"  removing stale partial backup: {staging}")
        shutil.rmtree(staging)

    print(f"Backing up {src} -> {dest}")
    try:
        shutil.copytree(src, staging, symlinks=True)
    except BaseException:
        # Clean up the partial copy so a re-run starts fresh; leave src untouched.
        shutil.rmtree(staging, ignore_errors=True)
        raise

    # Verify the copy is non-empty before we trust it enough to delete the source.
    if not any(staging.rglob("*")) and any(src.rglob("*")):
        shutil.rmtree(staging, ignore_errors=True)
        raise SystemExit(f"ERROR: backup copy of {src} came out empty; source left intact")

    os.replace(staging, dest)  # atomic within the backup dir
    print(f"  backup complete: {dest}")
    print(f"Deleting original {src}")
    shutil.rmtree(src)


def _dir_size_human(path: Path) -> str:
    total = 0
    for p in path.rglob("*"):
        try:
            if p.is_file():
                total += p.stat().st_size
        except OSError:
            pass
    size = float(total)
    for unit in ("B", "K", "M", "G", "T"):
        if size < 1024 or unit == "T":
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}T"


def cmd_find(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser()
    cols = find_collections(workspace)
    if not cols:
        print(
            f"ERROR: no vector collection directory found under {workspace}\n"
            "       (looked for collection_meta.json next to a store/ or index/ dir)",
            file=sys.stderr,
        )
        return 2
    for d in cols:
        print(d)
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser()
    cols = find_collections(workspace)
    if not cols:
        print(
            f"ERROR: no vector collection directory found under {workspace}",
            file=sys.stderr,
        )
        return 2

    print(f"Workspace:         {workspace}")
    print(f"Collection dir(s): {', '.join(str(c) for c in cols)}\n")
    for d in cols:
        print(f"  - {d}  ({_dir_size_human(d)})")
    print()

    if args.dry_run:
        print("--dry-run set: nothing deleted.")
        return 0

    if not args.force:
        ans = input(
            "Delete the vector collection above? Source docs are NOT touched. [y/N] "
        ).strip().lower()
        if ans not in ("y", "yes"):
            print("Aborted.")
            return 1

    backup_dir = Path(args.backup_dir).expanduser() if args.backup_dir else None
    for d in cols:
        if backup_dir:
            backup_dir.mkdir(parents=True, exist_ok=True)
            dest = backup_dir / f"{d.name}.{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
            _backup_then_delete(d, dest)
        else:
            print(f"Deleting {d}")
            shutil.rmtree(d)

    print("Done. Next: start the container with the NEW embedding model, then run: migrate.py reindex")
    return 0


# --------------------------------------------------------------------------- #
# reindex  (HTTP; resumable + rate-limit paced)
# --------------------------------------------------------------------------- #


def _discover_roots(client: httpx.Client, override: Optional[list[str]]) -> list[str]:
    """Return the subtrees to reindex.

    Reindexing each top-level child separately (rather than one giant viking://
    call) keeps any single request bounded and gives finer-grained checkpoints,
    so a rate-limit stall localizes to one subtree.
    """
    if override:
        return list(override)

    roots: list[str] = []

    def children(uri: str, pattern_prefix: str, allow_nested: bool) -> list[str]:
        try:
            r = client.get("/api/v1/fs/ls", params={"uri": uri, "simple": "true"})
            r.raise_for_status()
        except httpx.HTTPError:
            return []
        out: set[str] = set()
        for item in _iter_uris(r.json()):
            if not item.startswith(pattern_prefix):
                continue
            tail = item[len(pattern_prefix):]
            if not tail:
                continue
            if allow_nested:
                out.add(item)
            else:
                # only the immediate child segment (e.g. viking://user/<id>)
                out.add(pattern_prefix + tail.split("/", 1)[0])
        return sorted(out)

    roots += children("viking://resources", "viking://resources/", allow_nested=True)
    roots += children("viking://user", "viking://user/", allow_nested=False)
    # de-dupe preserving order
    seen: set[str] = set()
    deduped = [r for r in roots if not (r in seen or seen.add(r))]
    return deduped


def _iter_uris(payload: object) -> Iterable[str]:
    """Yield viking:// URIs from an fs/ls response, tolerant of shape.

    `simple=true` may return a list of strings, or the envelope may wrap a
    result list/dict. We pull any string that looks like a viking URI, plus any
    dict 'uri' fields, so we don't depend on one exact schema.
    """
    def walk(obj: object) -> Iterable[str]:
        if isinstance(obj, str):
            if obj.startswith("viking://"):
                yield obj
        elif isinstance(obj, dict):
            u = obj.get("uri")
            if isinstance(u, str) and u.startswith("viking://"):
                yield u
            for v in obj.values():
                yield from walk(v)
        elif isinstance(obj, list):
            for v in obj:
                yield from walk(v)

    yield from walk(payload)


class _State:
    """TSV checkpoint: completed subtrees are skipped on re-run."""

    def __init__(self, path: Path):
        self.path = path
        self._done: set[str] = set()
        if path.exists():
            for line in path.read_text().splitlines():
                parts = line.split("\t")
                if len(parts) >= 3 and parts[2] == "DONE":
                    self._done.add(parts[1])

    def is_done(self, uri: str) -> bool:
        return uri in self._done

    def mark(self, uri: str, status: str) -> None:
        with self.path.open("a") as f:
            f.write(f"{_now()}\t{uri}\t{status}\n")
        if status == "DONE":
            self._done.add(uri)


def cmd_reindex(args: argparse.Namespace) -> int:
    key = _server_key(required=True)
    pacing = args.pacing
    mode = args.mode
    state = _State(Path(args.state).expanduser())

    # wait=true reindex of a subtree can run long; give it a generous timeout.
    with _client(key, timeout=args.timeout) as client:
        roots = _discover_roots(client, args.roots)
        if not roots:
            print("Discovery returned no subtrees; falling back to a single viking:// reindex.")
            roots = ["viking://"]

        print(f"Base:    {_env_base()}")
        print(f"Mode:    {mode}")
        print(f"Pacing:  {pacing}s between subtrees")
        print(f"State:   {state.path}")
        print(f"Subtrees ({len(roots)}):")
        for r in roots:
            print(f"  {r}")
        print()

        fail_total = 0
        for uri in roots:
            if state.is_done(uri):
                print(f"SKIP (already done): {uri}")
                continue

            print(f"Reindexing: {uri}")
            body = {"uri": uri, "mode": mode, "wait": True}
            try:
                resp = client.post("/api/v1/content/reindex", content=json.dumps(body))
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPError as exc:
                print(f"  REQUEST FAILED for {uri}: {exc} (will retry on next run)")
                state.mark(uri, "ERROR")
                fail_total += 1
                time.sleep(pacing)
                continue

            result = data.get("result", data) if isinstance(data, dict) else {}
            scanned = int(result.get("scanned_records", 0) or 0)
            rebuilt = int(result.get("rebuilt_records", 0) or 0)
            failed = int(result.get("failed_records", 0) or 0)
            warnings = result.get("warnings") or []

            print(f"  scanned={scanned} rebuilt={rebuilt} failed={failed}")
            for w in warnings[:5]:
                print(f"    warning: {w}")
            if len(warnings) > 5:
                print(f"    ... and {len(warnings) - 5} more warning(s)")

            if failed > 0:
                print(f"  -> {failed} failures (likely rate limit); NOT marking done, retry next run.")
                state.mark(uri, f"PARTIAL:{failed}")
                fail_total += failed
            else:
                state.mark(uri, "DONE")

            time.sleep(pacing)

    print()
    if fail_total > 0:
        print(
            f"Completed with {fail_total} failed record(s). "
            "Re-run reindex to retry the PARTIAL/ERROR subtrees."
        )
        return 1
    print("All subtrees reindexed cleanly. Run: migrate.py verify")
    return 0


# --------------------------------------------------------------------------- #
# verify  (HTTP)
# --------------------------------------------------------------------------- #


def cmd_verify(args: argparse.Namespace) -> int:
    key = _server_key(required=False)

    print("== 1. Liveness ==")
    # If the embedding guard had tripped, the process would os._exit(1) and this
    # would refuse to connect. A success here means the new model booted clean.
    alive = False
    with _client(key, timeout=args.timeout) as client:
        for path in ("/api/v1/system/health", "/health"):
            try:
                r = client.get(path)
                if r.status_code < 500:
                    alive = True
                    break
            except httpx.HTTPError:
                continue
    if alive:
        print("  OK: server is up (boot passed the embedding-rebuild guard).")
    else:
        print(
            "  FAIL: server not responding. Check container logs for "
            "EmbeddingRebuildRequiredError.",
            file=sys.stderr,
        )
        return 1

    print("== 2. Search probe ==")
    if not key:
        print("  SKIP: set OV_SERVER_KEY to run a search probe.")
        return 0
    with _client(key, timeout=args.timeout) as client:
        try:
            # Endpoint is /api/v1/search/search: the search router has prefix
            # /api/v1/search AND a /search route. (/api/v1/search alone 404s.)
            r = client.post(
                "/api/v1/search/search",
                content=json.dumps({"query": args.probe_query, "limit": 5}),
            )
            r.raise_for_status()
            payload = r.json()
        except httpx.HTTPError as exc:
            print(f"  WARN: search probe failed: {exc}")
            return 0

    hits = sum(1 for _ in _iter_uris(payload))
    print(f'  query="{args.probe_query}" -> {hits} hit(s)')
    if hits > 0:
        print("  OK: search returned vectors under the new embedding model.")
    else:
        print(
            "  WARN: zero hits. If reindex just finished, the embedding queue may\n"
            "        still be draining. Re-run after it settles, or check reindex state."
        )
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="migrate.py",
        description="Migrate the OpenViking embedding model (reset collection + reindex).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    pf = sub.add_parser("find", help="Locate the vector collection dir(s).")
    pf.add_argument("workspace", nargs="?", default=DEFAULT_WORKSPACE)
    pf.set_defaults(func=cmd_find)

    pr = sub.add_parser("reset", help="Delete ONLY the vector collection (keep sources).")
    pr.add_argument("workspace", nargs="?", default=DEFAULT_WORKSPACE)
    pr.add_argument("--dry-run", action="store_true", help="Show what would be deleted, then exit.")
    pr.add_argument("--force", action="store_true", help="Skip the confirmation prompt.")
    pr.add_argument("--backup-dir", default=None, help="Move the collection here instead of deleting.")
    pr.set_defaults(func=cmd_reset)

    pi = sub.add_parser("reindex", help="Rebuild vectors from retained source (resumable).")
    pi.add_argument("--pacing", type=float, default=float(os.environ.get("PACING_SECONDS", "15")),
                    help="Seconds to sleep between subtrees (default 15).")
    pi.add_argument("--mode", default=os.environ.get("MODE", "vectors_only"),
                    choices=["vectors_only", "semantic_and_vectors"])
    pi.add_argument("--state", default=os.environ.get("STATE_FILE", "./reindex-state.tsv"),
                    help="Checkpoint file (default ./reindex-state.tsv).")
    pi.add_argument("--roots", nargs="*", default=None,
                    help="Override the subtrees to reindex (space-separated viking:// URIs).")
    pi.add_argument("--timeout", type=float, default=float(os.environ.get("OV_TIMEOUT", "600")),
                    help="Per-request HTTP timeout in seconds (default 600).")
    pi.set_defaults(func=cmd_reindex)

    pv = sub.add_parser("verify", help="Confirm liveness + that search returns hits.")
    pv.add_argument("--probe-query", default=os.environ.get("PROBE_QUERY", "overview"))
    pv.add_argument("--timeout", type=float, default=float(os.environ.get("OV_TIMEOUT", "30")))
    pv.set_defaults(func=cmd_verify)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
