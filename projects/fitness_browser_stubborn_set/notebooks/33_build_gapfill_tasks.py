"""
Build gap-fill summarization tasks: every (homolog, paper) pair that
appears in target_gene_paperblast_summaries.tsv but does NOT yet have a
homolog-specific non-null summary in the merged corpus.

Output:
  data/codex_summaries_gapfill/tasks.jsonl
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"

TARGET = PROJECT_DATA / "training_set" / "target_gene_paperblast_summaries.tsv"
HITS = PROJECT_DATA / "fb_paperblast_hit_papers.parquet"
MERGED = PROJECT_DATA / "manuscript-summaries-merged.tsv"
OUT_DIR = PROJECT_DATA / "codex_summaries_gapfill"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Already-have homolog-level summaries (from merged)
    have_pair: set[tuple[str, str]] = set()
    with open(MERGED) as fh:
        next(fh)
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            mid, _, gid = parts[0], parts[1], parts[2]
            summ = "\t".join(parts[3:])
            if summ.strip().lower() not in ("null", ""):
                have_pair.add((gid, mid))

    # 2. Iterate the target TSV. For each row needing summarization, add
    #    (homolog_id, paper_id) to a per-paper bucket.
    needed: dict[str, dict[str, dict]] = defaultdict(dict)
    paper_meta: dict[str, dict] = {}
    with open(TARGET) as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for r in reader:
            gid = r["paperblast_target_id"]
            pmid = r["paperblast_manuscript_id"]
            if not gid or not pmid:
                continue
            if (gid, pmid) in have_pair:
                continue
            if gid not in needed[pmid]:
                needed[pmid][gid] = {
                    "geneId": gid,
                    "pb_desc": r.get("paperblast_homolog_desc") or "",
                    "pb_organism": r.get("paperblast_organism") or "",
                }
            if pmid not in paper_meta:
                paper_meta[pmid] = {
                    "title": r.get("paper_title") or "",
                    "year": int(r["paper_year"]) if r.get("paper_year") else None,
                    "journal": r.get("paper_journal") or "",
                }

    out = OUT_DIR / "tasks.jsonl"
    n_papers = n_pairs = 0
    with open(out, "w") as fh:
        for pmid, gid_map in needed.items():
            row = {
                "pmId": pmid,
                "title": paper_meta[pmid]["title"],
                "year": paper_meta[pmid]["year"],
                "journal": paper_meta[pmid]["journal"],
                "gene_identifiers": list(gid_map.values()),
            }
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            n_papers += 1
            n_pairs += len(gid_map)
    print(f"  papers with gaps:         {n_papers:,}", file=sys.stderr)
    print(f"  total (homolog,pmid) pairs needing summary: {n_pairs:,}", file=sys.stderr)
    print(f"Wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
