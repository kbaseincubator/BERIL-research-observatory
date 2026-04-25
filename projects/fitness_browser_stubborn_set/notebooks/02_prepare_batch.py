"""
Prepare a batch of N un-judged genes from the ranked list for subagent
review. Outputs:

  data/batches/batch_<id>/
    input.md      — concatenated dossiers separated by `---`
    manifest.csv  — (orgId, locusId, rank) for the genes in this batch

Resumability: skips genes whose (orgId, locusId) already appears in
data/llm_verdicts.jsonl.

Usage:
  python projects/fitness_browser_stubborn_set/notebooks/02_prepare_batch.py \\
      --batch-id 001 --n 10
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

RANKED_PATH = PROJECT_DATA / "ranked_genes.parquet"
VERDICTS_PATH = PROJECT_DATA / "llm_verdicts.jsonl"
BATCHES_DIR = PROJECT_DATA / "batches"


def load_already_judged() -> set:
    """Return set of (orgId, locusId) tuples already in the verdicts JSONL."""
    if not VERDICTS_PATH.exists():
        return set()
    judged = set()
    with open(VERDICTS_PATH) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "orgId" in r and "locusId" in r:
                judged.add((r["orgId"], r["locusId"]))
    return judged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", required=True, help="e.g. 001 or 001-A")
    parser.add_argument("--n", type=int, default=10, help="genes per batch")
    parser.add_argument("--start-rank", type=int, default=1,
                        help="optional: start from this rank instead of top")
    args = parser.parse_args()

    ranked = pd.read_parquet(RANKED_PATH).sort_values("rank")
    already = load_already_judged()
    print(f"Ranked: {len(ranked):,} | already judged: {len(already)}", file=sys.stderr)

    batch_dir = BATCHES_DIR / f"batch_{args.batch_id}"
    batch_dir.mkdir(parents=True, exist_ok=True)

    # Pick top N un-judged genes from start_rank onward
    candidates = ranked[ranked["rank"] >= args.start_rank].copy()
    candidates = candidates[
        ~candidates.apply(
            lambda r: (r["orgId"], r["locusId"]) in already, axis=1
        )
    ]
    chosen = candidates.head(args.n)
    print(f"Chosen {len(chosen)} genes for batch {args.batch_id}", file=sys.stderr)

    # Render dossiers and write
    input_path = batch_dir / "input.md"
    manifest_path = batch_dir / "manifest.csv"
    with open(input_path, "w") as fh:
        fh.write(f"# Batch {args.batch_id} — {len(chosen)} dossiers\n\n")
        for i, (_, row) in enumerate(chosen.iterrows(), 1):
            d = dossier_mod.build_dossier(row["orgId"], row["locusId"])
            fh.write(f"## Dossier {i}/{len(chosen)} — rank {int(row['rank'])}\n\n")
            fh.write(dossier_mod.dossier_to_markdown(d))
            fh.write("\n\n---\n\n")
    chosen[["rank", "orgId", "locusId", "max_abs_fit", "max_abs_t",
            "in_specificphenotype", "gene_desc"]].to_csv(manifest_path, index=False)

    print(f"Wrote {input_path}  ({input_path.stat().st_size/1024:.1f} KB)")
    print(f"Wrote {manifest_path}")
    print(f"Output JSONL goes to: {batch_dir / 'output.jsonl'}")


if __name__ == "__main__":
    main()
