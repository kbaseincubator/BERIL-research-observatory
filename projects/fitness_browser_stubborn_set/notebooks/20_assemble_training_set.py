"""
Assemble the distributable training set for the gene-function annotation
agent. Produces a self-contained `data/training_set/` directory:

  data/training_set/
    README.md           — what this set is, how to use it, category breakdown
    negatives.jsonl     — 755 genes both LLMs agree are unannotatable
    positives.jsonl     — 445 genes both LLMs agree are correctly named today

Each row carries Claude's verdict + rationale and Codex's verdict + rationale,
so a downstream consumer can read the reasoning without rebuilding the
project.

Negatives are enriched with `evidence_tier` (orphan / hits_no_summaries /
hits_with_summaries) and `strong_phenotype` boolean from the stratification.
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"

NEG_IN = PROJECT_DATA / "training_recalcitrant_final.jsonl"
POS_IN = PROJECT_DATA / "training_positive_final.jsonl"
STRAT = PROJECT_DATA / "negatives_stratified.tsv"
OUT_DIR = PROJECT_DATA / "training_set"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load stratification labels
    strat = {}
    with open(STRAT) as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            strat[(r["orgId"], r["locusId"])] = {
                "evidence_tier": r["evidence_tier"],
                "strong_phenotype": int(r["strong_phenotype"]),
                "max_abs_fit": float(r["max_abs_fit"]),
                "max_abs_t": float(r["max_abs_t"]),
                "n_paperblast_hits": int(r["n_paperblast_hits"]),
                "n_papers_with_summaries": int(r["n_papers_with_summaries"]),
            }

    # Negatives — enrich each row with stratification fields
    n_neg = 0
    with open(NEG_IN) as fh, open(OUT_DIR / "negatives.jsonl", "w") as out:
        for line in fh:
            r = json.loads(line)
            extra = strat.get((r["orgId"], r["locusId"]), {})
            r.update(extra)
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
            n_neg += 1

    # Positives — copy as-is (already has Claude + Codex rationale)
    shutil.copyfile(POS_IN, OUT_DIR / "positives.jsonl")
    n_pos = sum(1 for _ in open(POS_IN))

    print(f"Wrote {OUT_DIR}/negatives.jsonl ({n_neg} rows)", file=sys.stderr)
    print(f"Wrote {OUT_DIR}/positives.jsonl ({n_pos} rows)", file=sys.stderr)


if __name__ == "__main__":
    main()
