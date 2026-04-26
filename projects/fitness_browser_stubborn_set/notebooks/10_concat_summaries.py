"""
Concatenate all per_paper/*.tsv into a single manuscript-summaries.tsv with
the agent's exact 4-column schema:
  manuscript_id  source_type  gene_identifier  summary

Skips empty per-paper files (papers with no PMC text or no relevant content).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
SUM_DIR = PROJECT_DATA / "codex_summaries"
PER_PAPER_DIR = SUM_DIR / "per_paper"
OUT_PATH = PROJECT_DATA / "manuscript-summaries.tsv"


def main() -> None:
    if not PER_PAPER_DIR.exists():
        print(f"No {PER_PAPER_DIR}", file=sys.stderr)
        sys.exit(1)

    n_files = 0
    n_rows = 0
    n_null = 0
    with open(OUT_PATH, "w") as out:
        w = csv.writer(out, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\")
        w.writerow(["manuscript_id", "source_type", "gene_identifier", "summary"])
        for tsv in sorted(PER_PAPER_DIR.glob("*.tsv")):
            n_files += 1
            try:
                content = tsv.read_text()
            except Exception:
                continue
            if not content.strip():
                continue
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Defensive: ensure 4 tab-separated columns
                fields = line.split("\t")
                if len(fields) < 4:
                    print(f"  SKIP malformed in {tsv.name}: {line[:80]!r}", file=sys.stderr)
                    continue
                # Take first 4 fields, join rest into summary if extras
                manuscript_id, source_type, gene_identifier = fields[0], fields[1], fields[2]
                summary = "\t".join(fields[3:]).strip()
                if summary.lower() in ("null", '"null"', ""):
                    n_null += 1
                    continue
                w.writerow([manuscript_id, source_type, gene_identifier, summary])
                n_rows += 1

    print(f"Per-paper TSVs read: {n_files}", file=sys.stderr)
    print(f"Non-null summary rows: {n_rows}", file=sys.stderr)
    print(f"Null/empty rows skipped: {n_null}", file=sys.stderr)
    print(f"Wrote {OUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
