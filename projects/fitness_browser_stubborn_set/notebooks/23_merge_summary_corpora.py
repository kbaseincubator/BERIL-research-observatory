"""
Merge three manuscript-summaries TSV corpora into one lookup, deduped by
(manuscript_id, gene_identifier), preferring non-null summaries.

Sources:
  ~/KBase/manuscript-summaries.tsv               — external (PaperBLAST_Jul2017)
  data/manuscript-summaries.tsv                  — recalcitrant set (this project)
  data/manuscript-summaries-positive.tsv         — positive set (this project)

Output:
  data/manuscript-summaries-merged.tsv           — same 4-col schema
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"

SOURCES = [
    Path(os.path.expanduser("~/KBase/manuscript-summaries.tsv")),
    PROJECT_DATA / "manuscript-summaries.tsv",
    PROJECT_DATA / "manuscript-summaries-positive.tsv",
    PROJECT_DATA / "manuscript-summaries-reann.tsv",
]
OUT = PROJECT_DATA / "manuscript-summaries-merged.tsv"


def is_null(s: str) -> bool:
    return s.strip().lower() in ("null", "")


def main() -> None:
    merged: dict[tuple[str, str], tuple[str, str]] = {}
    src_stats = []
    for src in SOURCES:
        if not src.exists():
            print(f"  skip (missing): {src}", file=sys.stderr)
            src_stats.append((src.name, 0, 0))
            continue
        n = n_kept = 0
        with open(src) as fh:
            next(fh, None)  # header
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 4:
                    continue
                mid, src_type, gid = parts[0], parts[1], parts[2]
                summary = "\t".join(parts[3:])
                key = (mid, gid)
                n += 1
                existing = merged.get(key)
                if existing is None:
                    merged[key] = (src_type, summary)
                    n_kept += 1
                else:
                    # Prefer non-null
                    if is_null(existing[1]) and not is_null(summary):
                        merged[key] = (src_type, summary)
        src_stats.append((src.name, n, n_kept))
        print(f"  {src.name}: read {n}, new keys {n_kept}", file=sys.stderr)

    n_total = len(merged)
    n_nonnull = sum(1 for _, (_, s) in merged.items() if not is_null(s))
    with open(OUT, "w") as out:
        w = csv.writer(out, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\")
        w.writerow(["manuscript_id", "source_type", "gene_identifier", "summary"])
        for (mid, gid), (src_type, summary) in merged.items():
            w.writerow([mid, src_type, gid, summary])

    print(f"\nMerged rows: {n_total}", file=sys.stderr)
    print(f"  non-null: {n_nonnull}", file=sys.stderr)
    print(f"  null:     {n_total - n_nonnull}", file=sys.stderr)
    print(f"Output: {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
