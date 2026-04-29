"""
Concat per-paper alt-source codex TSVs into manuscript-summaries-altsource.tsv.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
SUM_DIR = PROJECT_DATA / "codex_summaries_altsource"
PER_PAPER_DIR = SUM_DIR / "per_paper"
OUT_PATH = PROJECT_DATA / "manuscript-summaries-altsource.tsv"


def main() -> None:
    if not PER_PAPER_DIR.exists():
        print(f"No {PER_PAPER_DIR}", file=sys.stderr); sys.exit(1)
    n_files = n_rows = n_null = 0
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
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 4: continue
                mid, src, gid = parts[0], parts[1], parts[2]
                summ = "\t".join(parts[3:])
                if summ.strip().lower() in ("null", ""): n_null += 1
                w.writerow([mid, src, gid, summ])
                n_rows += 1
    print(f"Files read: {n_files}, rows: {n_rows} ({n_null} null)", file=sys.stderr)
    print(f"Output: {OUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
