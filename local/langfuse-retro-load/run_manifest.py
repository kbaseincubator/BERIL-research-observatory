#!/usr/bin/env python3
"""
Drive retro_load.py over every entry in manifest.json, computing each file's
tags/user_id automatically from its manifest record instead of hand-typed
per-file commands (the gap issue #390 was filed for).

Resolves each entry's actual transcript path via `find <find_root> -name
'<session_id>.jsonl'` (the same lookup the real load already used
successfully), then subprocess-calls retro_load.py once per entry, reusing
its exact CLI
(credentials, tag/user_id handling, marker-writing) rather than
re-implementing that logic here.

Usage (run on the pod, next to retro_load.py / langfuse_hook_official.py):
    python3 run_manifest.py --dry-run          # prints planned tags, no Langfuse calls
    python3 run_manifest.py                    # real run, all entries
    python3 run_manifest.py --limit 5          # real run, first 5 only (smoke test)
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from retro_load import already_loaded  # noqa: E402


def resolve_path(find_root: str, session_id: str) -> Path | None:
    root = Path(find_root).expanduser()
    r = subprocess.run(
        ["find", str(root), "-type", "f", "-name", f"{session_id}.jsonl"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"  ! find failed under {root}: {r.stderr.strip()}", file=sys.stderr)
        return None
    hits = [line for line in r.stdout.splitlines() if line.strip()]
    if not hits:
        return None
    if len(hits) > 1:
        # Guessing which hit is right risks loading the wrong person's transcript into
        # Langfuse -- unacceptable for a consent-sensitive corpus. Refuse instead.
        print(f"  ! {session_id}: {len(hits)} matches under {root}, refusing to guess: {hits}", file=sys.stderr)
        return None
    return Path(hits[0]).resolve()


def compute_tags(entry: dict, batch_tag: str) -> list[str]:
    # "claude-code" and "retro-load" are NOT included here: retro_load.py's own main()
    # already prepends them unconditionally to whatever --tag values it's given, so
    # adding them here too would duplicate them in every emitted trace.
    tags = [f"source:{entry['source']}", batch_tag]
    if entry.get("consent_bin"):
        tags.append(f"consent:{entry['consent_bin']}")
    if entry.get("event_day"):
        tags.append(f"event_day:{entry.get('event_day_date', '2026-05-07')}")
    if entry.get("role"):
        tags.append(f"role:{entry['role']}")
    if entry.get("group"):
        tags.append(f"group:{entry['group']}")
    return tags


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="manifest.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--batch-tag", default="full-load-2026-08-20",
                     help="tag identifying this run as a batch, so it's filterable/auditable later "
                          "(default matches the 2026-08-20 full load; override for any later run)")
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text())
    if args.limit is not None:
        manifest = manifest[: args.limit]

    not_found, already, planned, files_emitted, failed = [], [], [], 0, []

    for entry in manifest:
        sid = entry["session_id"]
        path = resolve_path(entry["find_root"], sid)
        if path is None:
            not_found.append(sid)
            continue

        tags = compute_tags(entry, args.batch_tag)
        user_id = entry["user_id"]

        if args.dry_run:
            prior = already_loaded(path)
            status = f"ALREADY LOADED ({prior['turns_emitted']} turns)" if prior else "would load"
            # retro_load.py prepends claude-code/retro-load itself; show the real full set.
            print(f"{sid}: {status} | user_id={user_id} | tags={['claude-code', 'retro-load'] + tags}")
            planned.append(sid)
            continue

        prior = already_loaded(path)
        if prior and not args.force:
            already.append(sid)
            continue

        # Delegate the actual emission to retro_load.py as a subprocess, reusing
        # its exact CLI (credentials, propagate_attributes, marker-writing) rather
        # than re-implementing that logic here.
        cmd = [sys.executable, str(Path(__file__).parent / "retro_load.py"),
               "--user-id", user_id]
        for t in tags:
            cmd += ["--tag", t]
        if args.force:
            cmd.append("--force")
        cmd.append(str(path))
        r = subprocess.run(cmd, capture_output=True, text=True)
        ok = r.returncode == 0
        print(f"{sid}: {'OK' if ok else 'FAILED'}")
        if not ok:
            failed.append((sid, r.stdout[-500:], r.stderr[-500:]))
        else:
            files_emitted += 1

    print()
    print(f"summary: {len(manifest)} manifest entries")
    if args.dry_run:
        print(f"  {len(planned)} resolved and would run, {len(not_found)} not found on disk")
    else:
        print(f"  {files_emitted} files emitted, {len(already)} already loaded (skipped), "
              f"{len(not_found)} not found, {len(failed)} failed")
    if not_found:
        print("  NOT FOUND:", not_found)
    if failed:
        print("  FAILED:")
        for sid, out, err in failed:
            print(f"    {sid}: stdout_tail={out!r} stderr_tail={err!r}")
    return 1 if (not_found or failed) else 0


if __name__ == "__main__":
    sys.exit(main())
