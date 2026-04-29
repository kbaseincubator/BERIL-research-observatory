"""
Setup for re-classifying a SAMPLE of negatives and positives with the
augmented dossier (now using the full merged literature corpus).

Picks 20 random rows from each of negatives.jsonl and positives.jsonl,
builds augmented batches (basic dossier + per-(homolog, paper) summaries
inlined). Uses N=10 batches (same as reann calibration).

Output:
  data/sample_reclass/
    batches_claude/batch_SC{NNN}/   — input.md + manifest.csv (for Claude)
    batches_codex/batch_SC{NNN}/    — input.md + manifest.csv (for Codex,
                                       with the codex-prompt-suffix added)
    sample_keys.tsv                 — orgId, locusId, original_label, source
"""
from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
NB_DIR = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "notebooks"
sys.path.insert(0, str(NB_DIR))
import dossier as dossier_mod  # noqa: E402

NEGATIVES = PROJECT_DATA / "training_set" / "negatives.jsonl"
POSITIVES = PROJECT_DATA / "training_set" / "positives.jsonl"
HITS = PROJECT_DATA / "fb_paperblast_hit_papers.parquet"
SUMMARIES = PROJECT_DATA / "manuscript-summaries-merged.tsv"

OUT_DIR = PROJECT_DATA / "sample_reclass"
CLAUDE_DIR = OUT_DIR / "batches_claude"
CODEX_DIR = OUT_DIR / "batches_codex"
SAMPLE_KEYS = OUT_DIR / "sample_keys.tsv"

SAMPLE_N = 20
BATCH_N = 10


def main() -> None:
    random.seed(0xfb)  # reproducible

    # Load both label sets
    negatives = []
    with open(NEGATIVES) as fh:
        for line in fh:
            r = json.loads(line)
            negatives.append({
                "orgId": r["orgId"],
                "locusId": r["locusId"],
                "original_verdict": r.get("verdict") or "",
                "original_proposed": r.get("proposed_annotation") or "",
                "original_confidence": r.get("confidence") or "",
                "original_codex_verdict": r.get("codex_verdict") or "",
                "source": "negatives",
            })
    positives = []
    with open(POSITIVES) as fh:
        for line in fh:
            r = json.loads(line)
            positives.append({
                "orgId": r["orgId"],
                "locusId": r["locusId"],
                "original_verdict": r.get("verdict") or "",
                "original_proposed": r.get("proposed_annotation") or "",
                "original_confidence": r.get("confidence") or "",
                "original_codex_verdict": r.get("codex_verdict") or "",
                "source": "positives",
            })
    print(f"negatives: {len(negatives)}, positives: {len(positives)}", file=sys.stderr)

    sample = random.sample(negatives, SAMPLE_N) + random.sample(positives, SAMPLE_N)
    print(f"sampled: {len(sample)} ({SAMPLE_N} negatives + {SAMPLE_N} positives)", file=sys.stderr)

    # Save sample manifest
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = list(sample[0].keys())
    with open(SAMPLE_KEYS, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        w.writeheader()
        w.writerows(sample)

    # Load full corpus once
    hits = pd.read_parquet(HITS)
    hits["pmId"] = hits["pmId"].astype(str)
    keyset = {(s["orgId"], s["locusId"]) for s in sample}
    hits = hits[hits.apply(lambda r: (r["orgId"], r["locusId"]) in keyset, axis=1)].copy()

    summary_lookup: dict[tuple[str, str], str] = {}
    with open(SUMMARIES) as fh:
        next(fh)
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            mid, _, gid = parts[0], parts[1], parts[2]
            summ = "\t".join(parts[3:])
            if summ.strip().lower() not in ("null", ""):
                summary_lookup[(gid, mid)] = summ
    print(f"merged summaries (non-null): {len(summary_lookup):,}", file=sys.stderr)

    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    CODEX_DIR.mkdir(parents=True, exist_ok=True)

    n_with_summ = 0
    n_total = len(sample)
    n_batches = (n_total + BATCH_N - 1) // BATCH_N
    for bi in range(n_batches):
        chunk = sample[bi * BATCH_N : (bi + 1) * BATCH_N]
        bid = f"SC{bi+1:03d}"
        # Claude batch: dossier + summaries (no codex prompt suffix)
        cdir = CLAUDE_DIR / f"batch_{bid}"
        cdir.mkdir(parents=True, exist_ok=True)
        # Codex batch: same content (xcheck.sh adds prompt suffix at runtime)
        xdir = CODEX_DIR / f"batch_{bid}"
        xdir.mkdir(parents=True, exist_ok=True)

        body_lines = [f"# Sample reclassification batch {bid} — {len(chunk)} dossiers (augmented w/ literature)\n"]
        for i, s in enumerate(chunk, 1):
            orgId, locusId = s["orgId"], s["locusId"]
            d = dossier_mod.build_dossier(orgId, locusId)
            body_lines.append(f"## Dossier {i}/{len(chunk)} — {orgId}::{locusId}\n")
            body_lines.append(dossier_mod.dossier_to_markdown(d))
            body_lines.append("\n")

            sub = hits[(hits["orgId"] == orgId) & (hits["locusId"] == locusId)]
            summaries_for_gene = []
            for _, hr in sub.iterrows():
                gid = hr["geneId"]
                pmid = str(hr["pmId"])
                if not gid or gid == "None" or pmid == "None":
                    continue
                summ = summary_lookup.get((gid, pmid))
                if summ:
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
                body_lines.append("### PaperBLAST literature summaries (per-gene per-paper)\n")
                for j, summ_rec in enumerate(summaries_for_gene, 1):
                    yr = f" ({int(summ_rec['year'])})" if pd.notna(summ_rec.get('year')) else ""
                    body_lines.append(
                        f"**[{j}] {summ_rec['geneId']}** — {summ_rec['pb_organism']} — {summ_rec['pb_desc']} ({summ_rec['pident']:.1f}% id)\n"
                        f"  Paper PMID:{summ_rec['pmId']}{yr} — {summ_rec['title']}\n"
                        f"  Summary: {summ_rec['summary']}\n"
                    )
            else:
                body_lines.append("### PaperBLAST literature summaries\n\n*(no per-paper summaries available)*\n")
            body_lines.append("\n---\n\n")

        body = "\n".join(body_lines)
        # Both dirs get the same input.md
        (cdir / "input.md").write_text(body)
        (xdir / "input.md").write_text(body)

        # Manifest with original labels for scoring
        for d in (cdir, xdir):
            with open(d / "manifest.csv", "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=fields, delimiter=",")
                w.writeheader()
                w.writerows(chunk)

    print(f"Built {n_batches} batches in {CLAUDE_DIR} and {CODEX_DIR}", file=sys.stderr)
    print(f"  genes with ≥1 summary: {n_with_summ}/{n_total}", file=sys.stderr)


if __name__ == "__main__":
    main()
