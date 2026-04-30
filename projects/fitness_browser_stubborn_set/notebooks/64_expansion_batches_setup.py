"""
Build classification batches for the expansion candidate pool
(data/random_sample_genes_expansion.parquet, 2,000 genes), with the FULL
augmented dossier:
  - basic 8-layer dossier
  - per-gene per-paper PaperBLAST summaries
  - extended InterPro / pathway annotations
  - cross-organism ortholog fitness

The batches are ready to run through Opus + Codex 5.5 (capability-matched
frontier pair) once the v1 negatives relabel finishes and we know how
many candidates to actually push through.

Output:
  data/expansion/
    batches_claude/batch_EX{NNN}/   - 25 dossiers per batch (80 batches)
    batches_codex/batch_EX{NNN}/    - same input
    expansion_keys.tsv               - orgId, locusId, gene_desc
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
NB_DIR = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "notebooks"
sys.path.insert(0, str(NB_DIR))
import dossier as dossier_mod  # noqa: E402

from importlib import import_module
sr2 = import_module("60_sample_reclass_v2_setup")

POOL = PROJECT_DATA / "random_sample_genes_expansion.parquet"
HITS = PROJECT_DATA / "fb_paperblast_hit_papers.parquet"
SUMMARIES = PROJECT_DATA / "manuscript-summaries-merged.tsv"
# Expansion-specific InterPro + ortholog fitness extracts (notebook 63b)
INTERPRO = PROJECT_DATA / "expansion" / "target_gene_interpro_union.tsv"
ORTHO = PROJECT_DATA / "expansion" / "target_gene_ortholog_fitness.tsv"

OUT_DIR = PROJECT_DATA / "expansion"
CLAUDE_DIR = OUT_DIR / "batches_claude"
CODEX_DIR = OUT_DIR / "batches_codex"
KEYS_TSV = OUT_DIR / "expansion_keys.tsv"

BATCH_N = 25


def main() -> None:
    pool = pd.read_parquet(POOL)
    sample = pool[["orgId", "locusId", "gene_desc", "max_abs_fit", "rank"]].to_dict("records")
    print(f"expansion pool: {len(sample):,} genes", file=sys.stderr)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = list(sample[0].keys())
    with open(KEYS_TSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        w.writeheader()
        w.writerows(sample)

    # InterPro union + ortholog fitness for the expansion keys were
    # extracted by notebook 63b and live under data/expansion/.

    print("loading corpora...", file=sys.stderr)
    keyset = {(s["orgId"], s["locusId"]) for s in sample}

    hits = pd.read_parquet(HITS)
    hits["pmId"] = hits["pmId"].astype(str)
    hits = hits[hits.apply(lambda r: (r["orgId"], r["locusId"]) in keyset, axis=1)].copy()

    summary_lookup: dict[tuple[str, str], str] = {}
    with open(SUMMARIES) as fh:
        next(fh)
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4: continue
            mid, _, gid = parts[0], parts[1], parts[2]
            summ = "\t".join(parts[3:])
            if summ.strip().lower() not in ("null", ""):
                summary_lookup[(gid, mid)] = summ
    print(f"  merged summaries (non-null): {len(summary_lookup):,}", file=sys.stderr)

    interpro = pd.read_csv(INTERPRO, sep="\t", dtype=str, keep_default_na=False)
    interpro = interpro[interpro.apply(lambda r: (r["orgId"], r["locusId"]) in keyset, axis=1)]
    interpro_grp = {(o,l): g for (o,l), g in interpro.groupby(["orgId","locusId"])}
    print(f"  interpro union rows for expansion: {len(interpro):,}", file=sys.stderr)

    ortho = pd.read_csv(ORTHO, sep="\t", dtype=str, keep_default_na=False)
    ortho = ortho[ortho.apply(
        lambda r: (r["target_orgId"], r["target_locusId"]) in keyset, axis=1)]
    ortho_grp = {(o,l): g for (o,l), g in ortho.groupby(["target_orgId","target_locusId"])}
    print(f"  ortholog fitness rows for expansion: {len(ortho):,}", file=sys.stderr)

    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    CODEX_DIR.mkdir(parents=True, exist_ok=True)

    n_batches = (len(sample) + BATCH_N - 1) // BATCH_N
    n_with_summ = n_with_ipr = n_with_ortho = 0

    for bi in range(n_batches):
        chunk = sample[bi*BATCH_N : (bi+1)*BATCH_N]
        bid = f"EX{bi+1:03d}"
        cdir = CLAUDE_DIR / f"batch_{bid}"; cdir.mkdir(parents=True, exist_ok=True)
        xdir = CODEX_DIR  / f"batch_{bid}"; xdir.mkdir(parents=True, exist_ok=True)

        body_lines = [f"# Expansion batch {bid} — {len(chunk)} dossiers "
                      f"(augmented: literature + InterPro union + ortholog fitness)\n"]
        for i, s in enumerate(chunk, 1):
            orgId, locusId = s["orgId"], s["locusId"]
            d = dossier_mod.build_dossier(orgId, locusId)
            body_lines.append(f"## Dossier {i}/{len(chunk)} — {orgId}::{locusId}\n")
            body_lines.append(dossier_mod.dossier_to_markdown(d))
            body_lines.append("\n")

            sub = hits[(hits["orgId"] == orgId) & (hits["locusId"] == locusId)]
            sgs = []
            for _, hr in sub.iterrows():
                gid, pmid = hr["geneId"], str(hr["pmId"])
                if not gid or gid == "None" or pmid == "None": continue
                summ = summary_lookup.get((gid, pmid))
                if summ:
                    sgs.append({"geneId": gid, "pb_organism": hr.get("pb_organism") or "",
                                "pb_desc": hr.get("pb_desc") or "",
                                "pident": float(hr["pident"]),
                                "pmId": pmid, "title": hr.get("title") or "",
                                "year": hr.get("year"), "summary": summ})
            if sgs:
                n_with_summ += 1
                body_lines.append("### PaperBLAST literature summaries (per-gene per-paper)\n")
                for j, sr in enumerate(sgs, 1):
                    yr = f" ({int(sr['year'])})" if pd.notna(sr.get('year')) else ""
                    body_lines.append(
                        f"**[{j}] {sr['geneId']}** — {sr['pb_organism']} — {sr['pb_desc']} "
                        f"({sr['pident']:.1f}% id)\n"
                        f"  Paper PMID:{sr['pmId']}{yr} — {sr['title']}\n"
                        f"  Summary: {sr['summary']}\n"
                    )
            else:
                body_lines.append("### PaperBLAST literature summaries\n\n"
                                  "*(no per-paper summaries available)*\n")

            ipr_rows = interpro_grp.get((orgId, locusId))
            if ipr_rows is not None and len(ipr_rows) > 0: n_with_ipr += 1
            body_lines.append("\n" + sr2._render_interpro_section(ipr_rows))

            o_rows = ortho_grp.get((orgId, locusId))
            if o_rows is not None and len(o_rows) > 0: n_with_ortho += 1
            body_lines.append("\n" + sr2._render_ortholog_section(o_rows))

            body_lines.append("\n---\n\n")

        body = "\n".join(body_lines)
        (cdir / "input.md").write_text(body)
        (xdir / "input.md").write_text(body)
        for d in (cdir, xdir):
            with open(d / "manifest.csv", "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=fields, delimiter=",")
                w.writeheader()
                w.writerows(chunk)

    print(f"\nBuilt {n_batches} batches in {CLAUDE_DIR} and {CODEX_DIR}", file=sys.stderr)
    print(f"  genes with >=1 paper summary: {n_with_summ}/{len(sample)}", file=sys.stderr)
    print(f"  genes with >=1 InterPro hit: {n_with_ipr}/{len(sample)}", file=sys.stderr)
    print(f"  genes with >=1 BBH ortholog: {n_with_ortho}/{len(sample)}", file=sys.stderr)


if __name__ == "__main__":
    main()
