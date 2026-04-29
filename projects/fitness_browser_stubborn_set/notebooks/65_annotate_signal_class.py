"""
Add a `signal_class` field to the four labeled JSONL files in the
training set so downstream consumers can distinguish:

  stubborn   : n_strong_experiments >= 1 OR in_specificphenotype == 1
               (Price-2018 strong-fitness threshold; the population the
               project is named after)
  no_signal  : neither — gene was measured but no condition crossed the
               strong-fitness threshold and no specific phenotype was
               flagged. The agent labels these "I don't know" because
               there is genuinely nothing to be stubborn about.

Why this matters: the original v1 random sample drew uniformly from the
full 137,798-gene pool of "FB genes with at least one fitness measurement,"
not from the stubborn-grade subset. As a result 95% of negatives.jsonl
are no-signal genes, not the strong-phenotype-but-stubborn cases the
project was originally aimed at. Tagging them lets consumers train
selectively without reshuffling the corpus.

Inputs:
  data/ranked_genes.parquet                                  (per-gene fitness features)
  data/training_set/{negatives,positives,human_validated,
                      llm_vs_human_disagreements}.jsonl

Outputs (in place):
  same JSONL files, with one extra field `signal_class` per row.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
TS = PROJECT_DATA / "training_set"
RANKED = PROJECT_DATA / "ranked_genes.parquet"
FEATURES_FULL = PROJECT_DATA / "gene_evidence_features.parquet"  # pre-reannotation-filter; covers human_validated genes too

FILES = [
    "negatives.jsonl",
    "positives.jsonl",
    "human_validated.jsonl",
    "llm_vs_human_disagreements.jsonl",
]


def main() -> None:
    # Use the pre-reannotation-filter feature file so reannotated genes
    # (human_validated + llm_vs_human_disagreements) get classified too.
    print("loading gene_evidence_features (pre-filter)...", file=sys.stderr)
    feats = pd.read_parquet(FEATURES_FULL)
    feats["_strong"] = ((feats["n_strong_experiments"] >= 1)
                        | (feats["in_specificphenotype"] == 1))
    sig_lookup: dict[tuple[str, str], str] = {}
    for _, r in feats.iterrows():
        sig_lookup[(r["orgId"], r["locusId"])] = "stubborn" if r["_strong"] else "no_signal"
    print(f"  signal map: {len(sig_lookup):,} keys", file=sys.stderr)

    for fn in FILES:
        path = TS / fn
        if not path.exists():
            print(f"  SKIP {fn} (not present)", file=sys.stderr)
            continue
        rows = []
        n_stubborn = n_no_sig = n_unknown = 0
        with open(path) as fh:
            for line in fh:
                r = json.loads(line)
                k = (r["orgId"], r["locusId"])
                cls = sig_lookup.get(k, "unknown")
                if cls == "stubborn": n_stubborn += 1
                elif cls == "no_signal": n_no_sig += 1
                else: n_unknown += 1
                r["signal_class"] = cls
                rows.append(r)

        with open(path, "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        total = len(rows)
        print(f"\n{fn}: {total:,} rows", file=sys.stderr)
        if total > 0:
            print(f"  stubborn: {n_stubborn:>5,} ({100*n_stubborn/total:5.1f}%)", file=sys.stderr)
            print(f"  no_signal:{n_no_sig:>5,} ({100*n_no_sig/total:5.1f}%)", file=sys.stderr)
            if n_unknown:
                print(f"  unknown : {n_unknown:>5,} ({100*n_unknown/total:5.1f}%)  "
                      f"(not in ranked_genes — usually genes from the reannotation "
                      f"set whose fitness features weren't in the v1 extract)",
                      file=sys.stderr)


if __name__ == "__main__":
    main()
