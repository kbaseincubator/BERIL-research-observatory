"""
Build Codex cross-check batches for the 500-gene positive set, augmented with
the per-paper summaries from codex_summaries_positive.

Output: data/codex_xcheck_positive/batch_P{NNN}/input.md  (25 dossiers per batch)
        data/codex_xcheck_positive/batch_P{NNN}/manifest.csv

Mirror of 12_build_codex_xcheck_batches.py but reads positive_sample_500.jsonl
and manuscript-summaries-positive.tsv.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
NB_DIR = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "notebooks"
sys.path.insert(0, str(NB_DIR))
import dossier as dossier_mod  # noqa: E402

DEFAULT_VERDICTS = PROJECT_DATA / "positive_sample_500.jsonl"
DEFAULT_HITS = PROJECT_DATA / "fb_paperblast_hit_papers.parquet"
DEFAULT_SUMMARIES = PROJECT_DATA / "manuscript-summaries-positive.tsv"
OUT_DIR = PROJECT_DATA / "codex_xcheck_positive"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=25, help="genes per batch")
    args = parser.parse_args()

    rows = []
    with open(DEFAULT_VERDICTS) as fh:
        for line in fh:
            r = json.loads(line)
            rows.append(r)
    print(f"Positive genes: {len(rows)}", file=sys.stderr)

    hits = pd.read_parquet(DEFAULT_HITS)
    keyset = {(r["orgId"], r["locusId"]) for r in rows}
    hits = hits[hits.apply(lambda h: (h["orgId"], h["locusId"]) in keyset, axis=1)].copy()
    hits["pmId"] = hits["pmId"].astype(str)

    summary_lookup: dict[tuple[str, str], str] = {}
    with open(DEFAULT_SUMMARIES) as fh:
        next(fh, None)
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            mid, _src, gid = parts[0], parts[1], parts[2]
            summ = "\t".join(parts[3:])
            summary_lookup[(gid, mid)] = summ
    print(f"Loaded {len(summary_lookup):,} summaries", file=sys.stderr)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    n_with_summ = 0
    batches = (len(rows) + args.n - 1) // args.n
    for bidx in range(batches):
        chunk = rows[bidx * args.n : (bidx + 1) * args.n]
        bid = f"P{bidx+1:03d}"
        batch_dir = OUT_DIR / f"batch_{bid}"
        batch_dir.mkdir(parents=True, exist_ok=True)

        input_path = batch_dir / "input.md"
        manifest_path = batch_dir / "manifest.csv"

        with open(input_path, "w") as fh:
            fh.write(f"# Codex cross-check batch {bid} — {len(chunk)} dossiers (positive set, augmented with PaperBLAST summaries)\n\n")
            for i, r in enumerate(chunk, 1):
                orgId, locusId = r["orgId"], r["locusId"]
                fh.write(f"## Dossier {i}/{len(chunk)} — {orgId}::{locusId}\n\n")
                d = dossier_mod.build_dossier(orgId, locusId)
                fh.write(dossier_mod.dossier_to_markdown(d))
                fh.write("\n\n")

                sub = hits[(hits["orgId"] == orgId) & (hits["locusId"] == locusId)]
                summaries_for_gene = []
                for _, hr in sub.iterrows():
                    gid = hr["geneId"]
                    pmid = str(hr["pmId"])
                    summ = summary_lookup.get((gid, pmid))
                    if summ and summ.strip().lower() not in ("null", ""):
                        summaries_for_gene.append({
                            "geneId": gid,
                            "pb_organism": hr.get("pb_organism") or "",
                            "pb_desc": hr.get("pb_desc") or "",
                            "pident": float(hr["pident"]),
                            "pmId": pmid,
                            "title": hr.get("title") or "",
                            "year": hr.get("year"),
                            "summary": summ,
                        })

                if summaries_for_gene:
                    n_with_summ += 1
                    fh.write("### PaperBLAST literature summaries (per-gene per-paper)\n\n")
                    for j, s in enumerate(summaries_for_gene, 1):
                        yr = f" ({int(s['year'])})" if pd.notna(s.get('year')) else ""
                        fh.write(f"**[{j}] {s['geneId']}** — {s['pb_organism']} — {s['pb_desc']} ({s['pident']:.1f}% id)\n")
                        fh.write(f"  Paper PMID:{s['pmId']}{yr} — {s['title']}\n")
                        fh.write(f"  Summary: {s['summary']}\n\n")
                else:
                    fh.write("### PaperBLAST literature summaries\n\n*(no per-paper summaries available — orphan or all summaries returned null)*\n\n")

                fh.write("\n---\n\n")

        with open(manifest_path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["orgId", "locusId", "claude_verdict", "claude_confidence", "claude_proposed"])
            for r in chunk:
                w.writerow([r["orgId"], r["locusId"], r["verdict"], r.get("confidence", ""), r.get("proposed_annotation", "")])

    print(f"Built {batches} batches in {OUT_DIR}", file=sys.stderr)
    print(f"  Genes with ≥1 non-null summary: {n_with_summ}", file=sys.stderr)


if __name__ == "__main__":
    main()
