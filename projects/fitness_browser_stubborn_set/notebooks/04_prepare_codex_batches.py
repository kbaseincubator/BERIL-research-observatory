"""
Build Codex cross-check batches from Claude's recalcitrant set.

Reads random_sample_verdicts.jsonl, filters to recalcitrant entries, and writes
N dossiers per batch into data/codex_check/batch_C{ID}/input.md for independent
Codex review.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dossier as dossier_mod  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
DEFAULT_VERDICTS_PATH = PROJECT_DATA / "random_sample_verdicts.jsonl"
CODEX_DIR = PROJECT_DATA / "codex_check"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verdicts-file", default=str(DEFAULT_VERDICTS_PATH))
    parser.add_argument("--n", type=int, default=25, help="genes per batch")
    parser.add_argument("--verdict", default="recalcitrant",
                        help="filter to this verdict (default: recalcitrant)")
    args = parser.parse_args()

    verdicts_path = Path(args.verdicts_file)
    if not verdicts_path.is_absolute():
        verdicts_path = PROJECT_DATA / verdicts_path

    rows = []
    with open(verdicts_path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("verdict") == args.verdict:
                rows.append(r)
    print(f"Found {len(rows)} {args.verdict} verdicts in {verdicts_path.name}", file=sys.stderr)

    CODEX_DIR.mkdir(parents=True, exist_ok=True)

    batches = (len(rows) + args.n - 1) // args.n
    for bidx in range(batches):
        chunk = rows[bidx * args.n : (bidx + 1) * args.n]
        bid = f"C{bidx+1:03d}"
        batch_dir = CODEX_DIR / f"batch_{bid}"
        batch_dir.mkdir(parents=True, exist_ok=True)

        input_path = batch_dir / "input.md"
        manifest_path = batch_dir / "manifest.csv"
        with open(input_path, "w") as fh:
            fh.write(f"# Codex cross-check batch {bid} — {len(chunk)} dossiers\n\n")
            for i, r in enumerate(chunk, 1):
                d = dossier_mod.build_dossier(r["orgId"], r["locusId"])
                fh.write(f"## Dossier {i}/{len(chunk)} — {r['orgId']}::{r['locusId']}\n\n")
                fh.write(dossier_mod.dossier_to_markdown(d))
                fh.write("\n\n---\n\n")
        manifest = pd.DataFrame([
            {"orgId": r["orgId"], "locusId": r["locusId"],
             "claude_verdict": r["verdict"], "claude_confidence": r.get("confidence", "")}
            for r in chunk
        ])
        manifest.to_csv(manifest_path, index=False)
        print(f"Wrote {input_path}  ({input_path.stat().st_size/1024:.1f} KB)", file=sys.stderr)


if __name__ == "__main__":
    main()
