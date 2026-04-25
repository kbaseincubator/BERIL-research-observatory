"""
Per-gene evidence dossier builder.

Imports the local parquet artifacts produced by extracts 00, 02-08 and
exposes:
  - load_evidence() -> dict[str, pd.DataFrame] — lazily indexed by
    (orgId, locusId)
  - build_dossier(orgId, locusId) -> dict — full evidence dossier for one
    gene, suitable for rule-based classification or LLM reasoning
  - dossier_to_markdown(dossier) -> str — human-readable rendering

Used by NB02 (priority-queue walk).

Run as a script for a sample gene:
    python projects/fitness_browser_stubborn_set/notebooks/dossier.py [orgId] [locusId]
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"


_EVIDENCE: dict[str, pd.DataFrame] | None = None


def load_evidence() -> dict[str, pd.DataFrame]:
    """Lazily load and index all evidence parquets by (orgId, locusId)."""
    global _EVIDENCE
    if _EVIDENCE is not None:
        return _EVIDENCE

    def _load(name: str) -> pd.DataFrame:
        p = PROJECT_DATA / name
        if not p.exists():
            raise FileNotFoundError(f"Missing artifact {p} — run preceding extract scripts")
        return pd.read_parquet(p)

    print("Loading evidence artifacts...", file=sys.stderr)
    features  = _load("gene_evidence_features.parquet")
    secondary = _load("gene_secondary_evidence.parquet")
    queue     = _load("priority_queue.parquet")
    phenos    = _load("phenotype_conditions.parquet")
    partners  = _load("cofit_partners_top10.parquet")
    neighbors = _load("gene_neighborhood.parquet")
    swiss     = _load("swissprot_hits.parquet")
    domains   = _load("domain_hits.parquet")
    kegg      = _load("kegg_hits.parquet")
    seed      = _load("seed_hits.parquet")
    pb_swiss  = _load("paperblast_via_swissprot.parquet")
    pb_diamond = _load("paperblast_via_diamond.parquet")
    pb_papers  = _load("fb_paperblast_hit_papers.parquet")

    # Index everything by (orgId, locusId) for quick per-gene lookup.
    print("Indexing...", file=sys.stderr)
    for df in [features, secondary, queue, phenos, partners, neighbors, swiss,
               domains, kegg, seed, pb_swiss, pb_diamond, pb_papers]:
        if {"orgId", "locusId"}.issubset(df.columns):
            df.set_index(["orgId", "locusId"], inplace=True, drop=False)
    _EVIDENCE = {
        "features": features,
        "secondary": secondary,
        "queue": queue,
        "phenos": phenos,
        "partners": partners,
        "neighbors": neighbors,
        "swiss": swiss,
        "domains": domains,
        "kegg": kegg,
        "seed": seed,
        "pb_swiss": pb_swiss,
        "pb_diamond": pb_diamond,
        "pb_papers": pb_papers,
    }
    print("Evidence loaded.", file=sys.stderr)
    return _EVIDENCE


def _safe_get(df: pd.DataFrame, key: tuple[str, str]) -> pd.DataFrame:
    """Return rows matching the (orgId, locusId) MultiIndex key, or empty frame."""
    try:
        result = df.loc[[key]]
    except (KeyError, ValueError):
        return df.iloc[0:0]
    return result if isinstance(result, pd.DataFrame) else result.to_frame().T


def _clean(v: Any) -> str:
    """Coerce NaN/None to empty string; pandas string columns sometimes have NaN floats."""
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except (TypeError, ValueError):
        pass
    s = str(v)
    return "" if s in {"nan", "None", "NaN"} else s


def categorise_desc(desc: str) -> str:
    """Mirror of the categoriser in NB01 — annotation category from gene.desc.
    Kept here so the dossier is self-contained even when features parquet
    does not carry the annotation_category column."""
    d = (desc or "").strip().lower()
    if not d or d.startswith("locus ") or d in {"-", ""}:
        return "hypothetical"
    if "hypothetical" in d or "uncharacterized" in d or "unknown function" in d:
        if "duf" in d or "upf" in d:
            return "DUF"
        return "hypothetical"
    if "duf" in d or "upf" in d:
        return "DUF"
    if any(tok in d for tok in ("putative", "predicted", "probable", "possible")):
        return "vague"
    enz_tokens = ("ase ", "ase,", "ase/", "ase-", "ligase", "reductase", "transporter",
                  "kinase", "synthase", "dehydrogenase", "permease", "oxidase", "transferase",
                  "hydrolase", "isomerase", "mutase", "polymerase")
    if any(tok in d for tok in enz_tokens) or d.endswith("ase"):
        return "named_enzyme"
    return "named_other"


def build_dossier(orgId: str, locusId: str) -> dict[str, Any]:
    """Pull a full evidence dossier for one gene."""
    ev = load_evidence()
    key = (orgId, locusId)

    feat_rows = _safe_get(ev["features"], key)
    if len(feat_rows) == 0:
        return {"orgId": orgId, "locusId": locusId, "found": False}
    feat = feat_rows.iloc[0].to_dict()

    sec_rows = _safe_get(ev["secondary"], key)
    sec = sec_rows.iloc[0].to_dict() if len(sec_rows) else {}

    q_rows = _safe_get(ev["queue"], key)
    queue_info = (
        {"rank": int(q_rows.iloc[0]["rank"]),
         "score": float(q_rows.iloc[0]["score"]),
         "chunk": int(q_rows.iloc[0]["chunk"])}
        if len(q_rows) else None
    )

    # Phenotypes with conditions (top 10 by |fit|)
    p = _safe_get(ev["phenos"], key).copy()
    if len(p):
        p["abs_fit"] = p["fit"].abs()
        p = p.nlargest(10, "abs_fit")
    phenotypes = [
        {
            "expGroup": r.get("expGroup"),
            "condition_1": r.get("condition_1"),
            "expDesc": r.get("expDesc"),
            "fit": round(float(r["fit"]), 2) if pd.notna(r.get("fit")) else None,
            "t": round(float(r["t"]), 1) if pd.notna(r.get("t")) else None,
            "specific": r.get("record_type") == "specific",
        }
        for _, r in p.iterrows()
    ]

    # Cofit partners (already top 10)
    pa = _safe_get(ev["partners"], key)
    cofit_partners = [
        {
            "hitId": r["hitId"],
            "cofit": round(float(r["cofit"]), 3),
            "partner_gene_symbol": _clean(r.get("partner_gene_symbol")),
            "partner_gene_desc": _clean(r.get("partner_gene_desc")),
        }
        for _, r in pa.iterrows()
    ]

    # Neighborhood (±5 positions; sort by offset)
    nb = _safe_get(ev["neighbors"], key).sort_values("offset")
    neighborhood = [
        {
            "offset": int(r["offset"]),
            "neighbor_locusId": r["neighbor_locusId"],
            "neighbor_gene_symbol": _clean(r.get("neighbor_gene_symbol")),
            "neighbor_gene_desc": _clean(r.get("neighbor_gene_desc")),
            "neighbor_strand": _clean(r.get("neighbor_strand")),
        }
        for _, r in nb.iterrows()
    ]

    # SwissProt hit (single best)
    sw = _safe_get(ev["swiss"], key)
    swissprot = (
        {
            "sprotAccession": sw.iloc[0]["sprotAccession"],
            "sprotId": sw.iloc[0]["sprotId"],
            "identity": round(float(sw.iloc[0]["identity"]), 1) if pd.notna(sw.iloc[0]["identity"]) else None,
            "sprot_gene": _clean(sw.iloc[0].get("sprot_gene")),
            "sprot_desc": _clean(sw.iloc[0].get("sprot_desc")),
            "sprot_organism": _clean(sw.iloc[0].get("sprot_organism")),
        }
        if len(sw) else None
    )

    # Domain hits (top 5 already)
    dom = _safe_get(ev["domains"], key)
    domains = [
        {
            "domainDb": _clean(r.get("domainDb")),
            "domainId": _clean(r.get("domainId")),
            "domainName": _clean(r.get("domainName")),
            "definition": _clean(r.get("definition")),
            "ec": _clean(r.get("ec")),
            "score": round(float(r["score"]), 1) if pd.notna(r.get("score")) else None,
        }
        for _, r in dom.iterrows()
    ]

    # KEGG KO
    k = _safe_get(ev["kegg"], key)
    kegg = (
        {
            "kgroup": k.iloc[0]["kgroup"],
            "ko_desc": _clean(k.iloc[0].get("ko_desc")),
            "ko_ecnum": _clean(k.iloc[0].get("ko_ecnum")),
            "identity": round(float(k.iloc[0]["identity"]), 1) if pd.notna(k.iloc[0]["identity"]) else None,
        }
        if len(k) else None
    )

    # SEED descriptions (list)
    sd = _safe_get(ev["seed"], key)
    seed_descs = [r["seed_desc"] for _, r in sd.iterrows() if pd.notna(r["seed_desc"]) and r["seed_desc"]]

    # PaperBLAST Stage 1 (SwissProt-direct)
    ps = _safe_get(ev["pb_swiss"], key)
    pb_stage1 = (
        {
            "n_papers": int(ps.iloc[0]["n_papers"]),
            "top_pmid": ps.iloc[0].get("top_pmid"),
            "top_title": ps.iloc[0].get("top_title"),
        }
        if len(ps) else None
    )

    # PaperBLAST Stage 2 (DIAMOND) — aggregate row + top homologs with papers
    pd2 = _safe_get(ev["pb_diamond"], key)
    pb_stage2_summary = pd2.iloc[0].to_dict() if len(pd2) else None
    if pb_stage2_summary:
        pb_stage2_summary = {
            "n_hits": int(pb_stage2_summary["n_hits"]),
            "n_papers": int(pb_stage2_summary["n_papers"]),
            "best_sseqid": pb_stage2_summary.get("best_sseqid"),
            "best_pident": round(float(pb_stage2_summary["best_pident"]), 1) if pd.notna(pb_stage2_summary.get("best_pident")) else None,
            "best_evalue": pb_stage2_summary.get("best_evalue"),
            "top_pmid": pb_stage2_summary.get("top_pmid"),
            "top_paper_title": pb_stage2_summary.get("top_paper_title"),
        }

    # Top homologs+papers from the long-format file (top 5 by evalue)
    pp = _safe_get(ev["pb_papers"], key)
    if len(pp):
        # Get top homologs (lowest evalue), and top papers per homolog
        top_homologs = (
            pp.dropna(subset=["geneId"])
              .sort_values("evalue")
              .drop_duplicates("geneId")
              .head(5)
        )
        homologs_with_papers = []
        for _, r in top_homologs.iterrows():
            gid = r["geneId"]
            papers_for_gid = pp[pp["geneId"] == gid].dropna(subset=["pmId"]).drop_duplicates("pmId").head(3)
            homologs_with_papers.append({
                "geneId": gid,
                "pb_organism": _clean(r.get("pb_organism")),
                "pb_desc": _clean(r.get("pb_desc")),
                "pident": round(float(r["pident"]), 1) if pd.notna(r.get("pident")) else None,
                "evalue": float(r["evalue"]) if pd.notna(r.get("evalue")) else None,
                "papers": [
                    {"pmid": str(pr["pmId"]), "year": int(pr["year"]) if pd.notna(pr.get("year")) else None,
                     "title": _clean(pr.get("title"))}
                    for _, pr in papers_for_gid.iterrows()
                ],
            })
    else:
        homologs_with_papers = []

    return {
        "orgId": orgId,
        "locusId": locusId,
        "found": True,
        "is_reannotated": int(feat.get("is_reannotated", 0)),
        "queue": queue_info,
        "annotation": {
            "gene_symbol": _clean(feat.get("gene_symbol")),
            "gene_desc": _clean(feat.get("gene_desc")),
            # features parquet does not carry annotation_category; derive on the fly
            "category": _clean(feat.get("annotation_category"))
                        or categorise_desc(_clean(feat.get("gene_desc"))),
        },
        "primary": {
            "in_specificphenotype": int(feat.get("in_specificphenotype", 0)),
            "max_abs_fit": round(float(feat.get("max_abs_fit", 0)), 2),
            "max_abs_t": round(float(feat.get("max_abs_t", 0)), 1),
            "n_strong_experiments": int(feat.get("n_strong_experiments", 0)),
            "n_moderate_experiments": int(feat.get("n_moderate_experiments", 0)),
            "max_cofit": round(float(feat.get("max_cofit", 0)), 3),
        },
        "secondary_flags": {k: int(sec.get(k, 0)) for k in [
            "informative_domain", "informative_kegg_ko", "informative_kegg_ec",
            "informative_seed", "conserved_spec_phenotype", "conserved_cofit",
        ]},
        "phenotypes_with_conditions": phenotypes,
        "cofit_partners": cofit_partners,
        "neighborhood": neighborhood,
        "swissprot": swissprot,
        "domains": domains,
        "kegg": kegg,
        "seed_descs": seed_descs,
        "paperblast_stage1": pb_stage1,
        "paperblast_stage2": pb_stage2_summary,
        "paperblast_homologs": homologs_with_papers,
    }


def dossier_to_markdown(d: dict[str, Any]) -> str:
    """Render a dossier as a compact markdown blob suitable for review or
    LLM-prompt input."""
    if not d.get("found"):
        return f"### {d['orgId']}::{d['locusId']} — NOT FOUND\n"

    lines: list[str] = []
    a = d["annotation"]
    p = d["primary"]
    s = d["secondary_flags"]
    qi = d["queue"]
    rank_str = f" rank {qi['rank']:,}, score {qi['score']:.3f}" if qi else ""
    reann = " **[REANNOTATED]**" if d["is_reannotated"] else ""
    lines.append(f"### {d['orgId']}::{d['locusId']}{rank_str}{reann}")
    lines.append(f"**Existing annotation**: `{a['gene_symbol']}` — *{a['gene_desc']}* (cat: {a['category']})\n")

    lines.append(f"**Primary fitness/cofit**: in_specificphenotype={p['in_specificphenotype']} | "
                 f"max|fit|={p['max_abs_fit']} | max|t|={p['max_abs_t']} | "
                 f"strong_exps={p['n_strong_experiments']} | max_cofit={p['max_cofit']}")
    lines.append(f"**Secondary flags**: " +
                 " ".join(f"{k}={v}" for k, v in s.items()))

    if d["phenotypes_with_conditions"]:
        lines.append("\n**Phenotypes with conditions** (top by |fit|):")
        for ph in d["phenotypes_with_conditions"]:
            spec = " *(specific)*" if ph.get("specific") else ""
            lines.append(f"  - {ph['expGroup']}: {ph['condition_1']}  fit={ph['fit']}, t={ph['t']}{spec}")

    if d["cofit_partners"]:
        lines.append("\n**Top cofit partners**:")
        for cp in d["cofit_partners"]:
            sym = f" `{cp['partner_gene_symbol']}`" if cp['partner_gene_symbol'] else ""
            lines.append(f"  - {cp['hitId']}{sym} (cofit={cp['cofit']}): {cp['partner_gene_desc']}")

    if d["neighborhood"]:
        lines.append("\n**Genomic neighborhood (±5 positions)**:")
        for n in d["neighborhood"]:
            sym = f" `{n['neighbor_gene_symbol']}`" if n['neighbor_gene_symbol'] else ""
            lines.append(f"  - offset {n['offset']:+d} ({n['neighbor_strand']}){sym}: {n['neighbor_gene_desc']}")

    if d["swissprot"]:
        sp = d["swissprot"]
        lines.append(f"\n**SwissProt hit**: {sp['sprotId']} ({sp['sprotAccession']}) "
                     f"@ {sp['identity']}% identity — *{sp['sprot_desc']}* "
                     f"({sp['sprot_organism']})")

    if d["domains"]:
        lines.append("\n**Domain hits** (top by score):")
        for dm in d["domains"]:
            ec = f" [EC {dm['ec']}]" if dm["ec"] else ""
            lines.append(f"  - {dm['domainDb']} {dm['domainId']} {dm['domainName']}{ec}: {dm['definition']}")

    if d["kegg"]:
        k = d["kegg"]
        ec = f" [EC {k['ko_ecnum']}]" if k.get("ko_ecnum") else ""
        lines.append(f"\n**KEGG KO**: {k['kgroup']}{ec} — *{k['ko_desc']}* @ {k['identity']}% id")

    if d["seed_descs"]:
        lines.append("\n**SEED descriptions**:")
        for sd in d["seed_descs"][:5]:
            lines.append(f"  - {sd}")

    if d["paperblast_stage1"]:
        lines.append(f"\n**PaperBLAST (SwissProt direct)**: {d['paperblast_stage1']['n_papers']} papers")
    if d["paperblast_stage2"]:
        ps2 = d["paperblast_stage2"]
        lines.append(f"\n**PaperBLAST (DIAMOND)**: {ps2['n_hits']} homologs, {ps2['n_papers']} papers; "
                     f"best hit {ps2['best_sseqid']} @ {ps2['best_pident']}%")
    if d["paperblast_homologs"]:
        lines.append("\n**Top PaperBLAST homologs + papers**:")
        for h in d["paperblast_homologs"]:
            lines.append(f"  - {h['geneId']} ({h['pb_organism']}) @ {h['pident']}% — *{h['pb_desc']}*")
            for pp in h["papers"][:2]:
                lines.append(f"    - PMID {pp['pmid']} ({pp['year']}): {pp['title']}")
    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) < 3:
        # Demo: pick a reannotated gene with rich evidence
        ev = load_evidence()
        # Find a reannotated gene with lots of evidence to show off the dossier
        feats = ev["features"].reset_index(drop=True)
        sample = feats[(feats.is_reannotated == 1) & (feats.max_abs_fit >= 3)
                       & (feats.max_cofit >= 0.85)].head(1)
        if len(sample):
            org = sample.iloc[0]["orgId"]
            loc = sample.iloc[0]["locusId"]
            print(f"Demo: rich-evidence reannotated gene {org}::{loc}", file=sys.stderr)
        else:
            org, loc = "acidovorax_3H11", "Ac3H11_2078"
    else:
        org, loc = sys.argv[1], sys.argv[2]
    d = build_dossier(org, loc)
    print(dossier_to_markdown(d))


if __name__ == "__main__":
    main()
