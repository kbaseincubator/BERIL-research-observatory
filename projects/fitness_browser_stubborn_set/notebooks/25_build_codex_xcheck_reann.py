"""
Build Codex cross-check batches for the reannotation calibration set, using
augmented dossiers (8-layer evidence with original_description + per-paper
PaperBLAST literature summaries from the merged corpus).

Reads:
  data/reannotation_set.parquet
  data/batches_reann/batch_RA*/output.jsonl   — Claude verdicts (one per gene)
  data/manuscript-summaries-merged.tsv

Output:
  data/codex_xcheck_reann/batch_RA{NNN}/input.md
  data/codex_xcheck_reann/batch_RA{NNN}/manifest.csv
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
NB_DIR = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "notebooks"
sys.path.insert(0, str(NB_DIR))
import dossier as dossier_mod  # noqa: E402

REANN = PROJECT_DATA / "reannotation_set.parquet"
HITS = PROJECT_DATA / "fb_paperblast_hit_papers.parquet"
SUMMARIES = PROJECT_DATA / "manuscript-summaries-merged.tsv"
CLAUDE_BATCHES = PROJECT_DATA / "batches_reann"
OUT_DIR = PROJECT_DATA / "codex_xcheck_reann"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=25)
    args = parser.parse_args()

    reann = pd.read_parquet(REANN).dropna(subset=["orgId", "locusId"]).reset_index(drop=True)
    keys_in_order = list(reann[["orgId", "locusId"]].itertuples(index=False, name=None))
    print(f"Reannotation rows: {len(keys_in_order)}", file=sys.stderr)

    orig_lookup = {
        (r["orgId"], r["locusId"]): (r.get("original_description") or "").strip() or "(blank)"
        for _, r in reann.iterrows()
    }

    hits = pd.read_parquet(HITS)
    keyset = set(keys_in_order)
    hits = hits[hits.apply(lambda h: (h["orgId"], h["locusId"]) in keyset, axis=1)].copy()
    hits["pmId"] = hits["pmId"].astype(str)
    print(f"PaperBLAST hits joined to reannotation set: {len(hits):,}", file=sys.stderr)

    summary_lookup: dict[tuple[str, str], str] = {}
    with open(SUMMARIES) as fh:
        next(fh, None)
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            mid, _src, gid = parts[0], parts[1], parts[2]
            summ = "\t".join(parts[3:])
            summary_lookup[(gid, mid)] = summ
    print(f"Merged summaries loaded: {len(summary_lookup):,}", file=sys.stderr)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    n_with_summ = 0
    n = args.n
    batches = (len(keys_in_order) + n - 1) // n
    for bi in range(batches):
        chunk = keys_in_order[bi * n : (bi + 1) * n]
        bid = f"RA{bi+1:03d}"
        bdir = OUT_DIR / f"batch_{bid}"
        bdir.mkdir(parents=True, exist_ok=True)
        input_path = bdir / "input.md"
        manifest_path = bdir / "manifest.csv"

        with open(input_path, "w") as fh:
            fh.write(f"# Codex cross-check (reannotation calibration) batch {bid} — {len(chunk)} dossiers\n\n")
            fh.write("> Dossiers built with `original_description` (pre-curation). PaperBLAST literature summaries appended where available.\n\n")
            for i, (orgId, locusId) in enumerate(chunk, 1):
                fh.write(f"## Dossier {i}/{len(chunk)} — {orgId}::{locusId}\n\n")
                d = dossier_mod.build_dossier(orgId, locusId, desc_override=orig_lookup[(orgId, locusId)])
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
            w.writerow(["orgId", "locusId"])
            for k in chunk:
                w.writerow(list(k))

    print(f"Built {batches} batches in {OUT_DIR}", file=sys.stderr)
    print(f"  Genes with ≥1 non-null summary: {n_with_summ}", file=sys.stderr)


if __name__ == "__main__":
    main()
