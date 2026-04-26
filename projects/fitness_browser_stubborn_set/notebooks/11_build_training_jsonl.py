"""
Build training-ready JSONL for the recalcitrant negative training set.

Each row combines:
  - orgId, locusId
  - Claude verdict (recalcitrant), confidence, rationale, papers_consulted
  - Full dossier markdown (8 evidence layers)
  - PaperBLAST DIAMOND hits joined to per-paper Codex summaries

Output: data/training_recalcitrant.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
NB_DIR = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "notebooks"
sys.path.insert(0, str(NB_DIR))
import dossier as dossier_mod  # noqa: E402

DEFAULT_VERDICTS = PROJECT_DATA / "random_sample_verdicts.jsonl"
DEFAULT_HITS = PROJECT_DATA / "fb_paperblast_hit_papers.parquet"
DEFAULT_SUMMARIES = PROJECT_DATA / "manuscript-summaries.tsv"
DEFAULT_OUT = PROJECT_DATA / "training_recalcitrant.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verdicts-file", default=str(DEFAULT_VERDICTS))
    parser.add_argument("--hits-file", default=str(DEFAULT_HITS))
    parser.add_argument("--summaries-file", default=str(DEFAULT_SUMMARIES))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--verdict", default="recalcitrant")
    args = parser.parse_args()

    # 1. Load Claude verdicts
    keys = []
    verdicts = {}
    with open(args.verdicts_file) as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("verdict") == args.verdict:
                k = (r["orgId"], r["locusId"])
                keys.append(k)
                verdicts[k] = r
    print(f"{args.verdict} genes: {len(keys)}", file=sys.stderr)

    # 2. Load DIAMOND hits, filter to recalcitrant set, group by gene
    hits = pd.read_parquet(args.hits_file)
    keyset = set(keys)
    mask = hits.apply(lambda r: (r["orgId"], r["locusId"]) in keyset, axis=1)
    hits = hits[mask].copy()
    hits["pmId"] = hits["pmId"].astype(str)
    print(f"DIAMOND hits for recalcitrant: {len(hits):,}", file=sys.stderr)

    # 3. Load summaries (geneId, pmId) -> summary text
    summary_lookup: dict[tuple[str, str], str] = {}
    with open(args.summaries_file) as fh:
        header = fh.readline()  # skip header
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            mid, _src, gid, summ = parts[0], parts[1], parts[2], "\t".join(parts[3:])
            summary_lookup[(gid, mid)] = summ
    print(f"Loaded summaries: {len(summary_lookup):,}", file=sys.stderr)

    # 4. Build per-gene PaperBLAST evidence block
    out_path = Path(args.out)
    n_written = 0
    n_with_hits = 0
    n_with_summaries = 0
    with open(out_path, "w") as out:
        for orgId, locusId in keys:
            v = verdicts[(orgId, locusId)]
            sub = hits[(hits["orgId"] == orgId) & (hits["locusId"] == locusId)]

            paperblast_hits = []
            has_any_summary = False
            if len(sub) > 0:
                # Group by geneId (PaperBLAST homolog)
                for gid, group in sub.groupby("geneId"):
                    g0 = group.iloc[0]
                    papers = []
                    for _, hr in group.iterrows():
                        pmid = str(hr["pmId"])
                        summ = summary_lookup.get((gid, pmid))
                        papers.append({
                            "pmId": pmid,
                            "title": (hr.get("title") or ""),
                            "year": int(hr["year"]) if pd.notna(hr.get("year")) else None,
                            "journal": hr.get("journal") or "",
                            "summary": summ,  # may be None
                        })
                        if summ:
                            has_any_summary = True
                    paperblast_hits.append({
                        "geneId": gid,
                        "pb_organism": g0.get("pb_organism") or "",
                        "pb_desc": g0.get("pb_desc") or "",
                        "best_pident": float(group["pident"].max()),
                        "best_evalue": float(group["evalue"].min()),
                        "best_qcovhsp": float(group["qcovhsp"].max()),
                        "n_papers": len(group),
                        "papers": papers,
                    })

            # Build dossier markdown
            try:
                d = dossier_mod.build_dossier(orgId, locusId)
                dossier_md = dossier_mod.dossier_to_markdown(d)
            except Exception as e:
                dossier_md = f"<dossier build failed: {e}>"

            row = {
                "orgId": orgId,
                "locusId": locusId,
                "verdict": v["verdict"],
                "confidence": v.get("confidence", ""),
                "proposed_annotation": v.get("proposed_annotation", "") or "",
                "rationale": v.get("rationale", ""),
                "papers_consulted": v.get("papers_consulted", []),
                "dossier_md": dossier_md,
                "n_paperblast_hits": len(paperblast_hits),
                "n_papers_with_summaries": sum(1 for h in paperblast_hits for p in h["papers"] if p["summary"]),
                "paperblast_hits": paperblast_hits,
            }
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            n_written += 1
            if paperblast_hits:
                n_with_hits += 1
            if has_any_summary:
                n_with_summaries += 1

    print(f"\nWrote {out_path}", file=sys.stderr)
    print(f"  Total rows: {n_written}", file=sys.stderr)
    print(f"  With ≥1 PaperBLAST hit: {n_with_hits}", file=sys.stderr)
    print(f"  With ≥1 paper summary: {n_with_summaries}", file=sys.stderr)
    print(f"  Orphan (no hits): {n_written - n_with_hits}", file=sys.stderr)


if __name__ == "__main__":
    main()
