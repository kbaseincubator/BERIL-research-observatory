"""
Sample reclass v2: same 40-gene sample as 50_sample_reclass_setup.py, but
with the two new evidence layers inlined into the dossier:
  - target_gene_interpro_union.tsv  (consolidated InterPro/InterProScan +
                                     GO IDs + KEGG/Reactome/MetaCyc pathways)
  - target_gene_ortholog_fitness.tsv (cross-organism BBH ortholog
                                      fitness profiles + shared GTDB ranks)

The original v1 reclass measured the marginal effect of the *richer paper
summaries* alone; we found a 2.5% both-LLM flip rate (under the 5% relabel
threshold). This v2 reclass measures the *cumulative* effect of richer
summaries + InterPro union + ortholog fitness on the same 40 genes.

Decision rule: if both-LLM flip rate against original labels stays under
5%, the LLM-derived label files (positives.jsonl, negatives.jsonl) ship
as-is. If >= 5%, regenerate the full 1,200 LLM labels.

Output:
  data/sample_reclass_v2/
    batches_claude/batch_SV{NNN}/   - input.md + manifest.csv
    batches_codex/batch_SV{NNN}/    - input.md + manifest.csv
    sample_keys.tsv                  - identical to v1, for traceability
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

INTERPRO_UNION = PROJECT_DATA / "training_set" / "target_gene_interpro_union.tsv"
ORTHO_FITNESS  = PROJECT_DATA / "training_set" / "target_gene_ortholog_fitness.tsv"

OUT_DIR = PROJECT_DATA / "sample_reclass_v2"
CLAUDE_DIR = OUT_DIR / "batches_claude"
CODEX_DIR = OUT_DIR / "batches_codex"
SAMPLE_KEYS = OUT_DIR / "sample_keys.tsv"

SAMPLE_N = 20
BATCH_N = 10
TOP_INTERPRO = 12      # most rows have ~6 hits; cap at 12 keeps section bounded
TOP_ORTHOLOGS = 10     # most rows have <= 35; cap at 10 keeps section bounded
MIN_BBH_FOR_DISPLAY = 0.30  # discount very-distant orthologs


def _render_interpro_section(rows: pd.DataFrame) -> str:
    """Render a per-gene InterPro union section as compact markdown."""
    if rows is None or rows.empty:
        return "### Extended InterPro / pathway annotations\n\n*(no entries)*"
    rows = rows.copy()
    # Sort: prefer entries with more corroborating sources, then by analysis kind
    rows["_n_sources"] = pd.to_numeric(rows["n_sources"], errors="coerce").fillna(1).astype(int)
    rows = rows.sort_values(["_n_sources", "analysis"], ascending=[False, True]).head(TOP_INTERPRO)
    lines = [f"### Extended InterPro / pathway annotations ({len(rows)} of "
             f"{len(rows)} shown — top by source-corroboration)\n"]
    for _, r in rows.iterrows():
        ipr = r.get("ipr_acc") or ""
        ipr_d = r.get("ipr_desc") or ""
        sig_a = r.get("signature_acc") or ""
        sig_d = r.get("signature_desc") or ""
        an = r.get("analysis") or ""
        srcs = r.get("sources") or ""
        # core/auxiliary/singleton tier (per-gene from FB-pangenome link)
        tier_bits = []
        if str(r.get("is_core")).lower() == "true": tier_bits.append("core")
        if str(r.get("is_auxiliary")).lower() == "true": tier_bits.append("auxiliary")
        if str(r.get("is_singleton")).lower() == "true": tier_bits.append("singleton")
        tier = "/".join(tier_bits) or "unknown"
        head = f"- **{ipr or sig_a}** ({an} {sig_a})"
        if ipr_d:
            head += f" — *{ipr_d}*"
        elif sig_d:
            head += f" — *{sig_d}*"
        head += f"  [sources: {srcs}; tier: {tier}]"
        lines.append(head)
        gos = r.get("go_ids") or ""
        if gos:
            # Keep terms compact; an agent can resolve GO IDs at inference
            top = ";".join(gos.split(";")[:8])
            more = "" if len(gos.split(";")) <= 8 else f" (+{len(gos.split(';'))-8} more)"
            lines.append(f"  - GO: {top}{more}")
        ps = r.get("pathways") or ""
        if ps:
            top = ";".join(ps.split(";")[:6])
            more = "" if len(ps.split(";")) <= 6 else f" (+{len(ps.split(';'))-6} more)"
            lines.append(f"  - Pathways: {top}{more}")
    return "\n".join(lines)


def _render_ortholog_section(rows: pd.DataFrame) -> str:
    """Render top-N BBH orthologs with their own fitness profile."""
    if rows is None or rows.empty:
        return "### Cross-organism ortholog fitness\n\n*(no FB BBH orthologs)*"
    rows = rows.copy()
    rows["_bbh"] = pd.to_numeric(rows["bbh_ratio"], errors="coerce").fillna(0.0)
    rows["_strong"] = pd.to_numeric(rows["ortholog_n_strong"], errors="coerce").fillna(0)
    rows["_specific"] = pd.to_numeric(rows["ortholog_n_specific_phenotype"],
                                       errors="coerce").fillna(0)
    # Discount very-distant pairs
    rows = rows[rows["_bbh"] >= MIN_BBH_FOR_DISPLAY]
    if rows.empty:
        return "### Cross-organism ortholog fitness\n\n*(orthologs exist but all bbh_ratio < 0.30)*"
    # Rank: BBH first, but break ties on strength of phenotype evidence
    rows = rows.sort_values(["_bbh", "_strong", "_specific"],
                            ascending=[False, False, False]).head(TOP_ORTHOLOGS)
    lines = [f"### Cross-organism ortholog fitness "
             f"(top {len(rows)} of all BBH orthologs with bbh_ratio >= 0.30)\n"]
    for _, r in rows.iterrows():
        oo = r.get("ortholog_orgId") or ""
        ol = r.get("ortholog_locusId") or ""
        sym = r.get("ortholog_symbol") or ""
        d = r.get("ortholog_gene_desc") or ""
        bbh = float(r["_bbh"])
        sr = r.get("shared_taxonomic_ranks") or ""
        mfit = r.get("ortholog_max_abs_fit") or ""
        mt = r.get("ortholog_max_abs_t") or ""
        nst = int(r["_strong"]) if pd.notna(r["_strong"]) else 0
        nsp = int(r["_specific"]) if pd.notna(r["_specific"]) else 0
        cond = r.get("ortholog_top_conditions") or ""
        head = f"- **{oo}::{ol}**"
        if sym: head += f" `{sym}`"
        head += f" (bbh={bbh:.2f}, shared_ranks={sr}) — *{d}*"
        lines.append(head)
        stats = (f"  - max|fit|={mfit}, max|t|={mt}, n_strong={nst}, "
                 f"n_specific_phenotype={nsp}")
        lines.append(stats)
        if cond:
            lines.append(f"  - top conditions: {cond}")
    return "\n".join(lines)


def main() -> None:
    random.seed(0xfb)  # SAME seed as v1 -> SAME 40 genes

    negatives = []
    with open(NEGATIVES) as fh:
        for line in fh:
            r = json.loads(line)
            negatives.append({
                "orgId": r["orgId"], "locusId": r["locusId"],
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
                "orgId": r["orgId"], "locusId": r["locusId"],
                "original_verdict": r.get("verdict") or "",
                "original_proposed": r.get("proposed_annotation") or "",
                "original_confidence": r.get("confidence") or "",
                "original_codex_verdict": r.get("codex_verdict") or "",
                "source": "positives",
            })
    sample = random.sample(negatives, SAMPLE_N) + random.sample(positives, SAMPLE_N)
    print(f"sampled: {len(sample)} ({SAMPLE_N} negatives + {SAMPLE_N} positives)",
          file=sys.stderr)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = list(sample[0].keys())
    with open(SAMPLE_KEYS, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        w.writeheader()
        w.writerows(sample)

    # Load full corpora
    print("loading corpora...", file=sys.stderr)
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
    print(f"  merged summaries (non-null): {len(summary_lookup):,}", file=sys.stderr)

    interpro = pd.read_csv(INTERPRO_UNION, sep="\t", dtype=str, keep_default_na=False)
    interpro = interpro[interpro.apply(lambda r: (r["orgId"], r["locusId"]) in keyset, axis=1)]
    print(f"  interpro union rows for sample: {len(interpro):,}", file=sys.stderr)
    interpro_grp = {(o,l): g for (o,l), g in interpro.groupby(["orgId","locusId"])}

    ortho = pd.read_csv(ORTHO_FITNESS, sep="\t", dtype=str, keep_default_na=False)
    ortho = ortho[ortho.apply(
        lambda r: (r["target_orgId"], r["target_locusId"]) in keyset, axis=1)]
    print(f"  ortholog fitness rows for sample: {len(ortho):,}", file=sys.stderr)
    ortho_grp = {(o,l): g for (o,l), g in ortho.groupby(["target_orgId","target_locusId"])}

    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    CODEX_DIR.mkdir(parents=True, exist_ok=True)

    n_with_summ = 0
    n_with_interpro = 0
    n_with_ortho = 0
    n_total = len(sample)
    n_batches = (n_total + BATCH_N - 1) // BATCH_N

    for bi in range(n_batches):
        chunk = sample[bi*BATCH_N : (bi+1)*BATCH_N]
        bid = f"SV{bi+1:03d}"
        cdir = CLAUDE_DIR / f"batch_{bid}"; cdir.mkdir(parents=True, exist_ok=True)
        xdir = CODEX_DIR  / f"batch_{bid}"; xdir.mkdir(parents=True, exist_ok=True)

        body_lines = [f"# Sample reclassification v2 batch {bid} — {len(chunk)} dossiers "
                      f"(augmented w/ literature + InterPro union + ortholog fitness)\n"]
        for i, s in enumerate(chunk, 1):
            orgId, locusId = s["orgId"], s["locusId"]
            d = dossier_mod.build_dossier(orgId, locusId)
            body_lines.append(f"## Dossier {i}/{len(chunk)} — {orgId}::{locusId}\n")
            body_lines.append(dossier_mod.dossier_to_markdown(d))
            body_lines.append("\n")

            # 1. Inline paper summaries (v1 augmentation)
            sub = hits[(hits["orgId"] == orgId) & (hits["locusId"] == locusId)]
            summaries_for_gene = []
            for _, hr in sub.iterrows():
                gid, pmid = hr["geneId"], str(hr["pmId"])
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
                for j, sr in enumerate(summaries_for_gene, 1):
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

            # 2. Inline extended InterPro / pathway annotations (v2 NEW)
            ipr_rows = interpro_grp.get((orgId, locusId))
            if ipr_rows is not None and len(ipr_rows) > 0:
                n_with_interpro += 1
            body_lines.append("\n" + _render_interpro_section(ipr_rows))

            # 3. Inline cross-organism ortholog fitness (v2 NEW)
            o_rows = ortho_grp.get((orgId, locusId))
            if o_rows is not None and len(o_rows) > 0:
                n_with_ortho += 1
            body_lines.append("\n" + _render_ortholog_section(o_rows))

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
    print(f"  genes with >=1 paper summary: {n_with_summ}/{n_total}", file=sys.stderr)
    print(f"  genes with >=1 InterPro hit: {n_with_interpro}/{n_total}", file=sys.stderr)
    print(f"  genes with >=1 BBH ortholog: {n_with_ortho}/{n_total}", file=sys.stderr)


if __name__ == "__main__":
    main()
