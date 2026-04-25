"""
Produce the publication-ready outputs from the LLM verdict set:

  - data/improvable_genes.tsv         curator hand-off list (improvable_new + correction)
  - data/recalcitrant_genes.tsv       project's "stubborn" answer set
  - data/already_named_genes.tsv      for completeness (genes the curator was right to skip)
  - data/cited_pmids.tsv              PMID -> # genes citing it -> sample gene list
  - data/cross_gene_clusters.md       PMIDs cited by 3+ genes (cluster signal)
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DIR = REPO_ROOT / "projects" / "fitness_browser_stubborn_set"
PROJECT_DATA = PROJECT_DIR / "data"

VERDICTS_PATH = PROJECT_DATA / "verdicts_with_context.parquet"

OUT_IMPROVABLE = PROJECT_DATA / "improvable_genes.tsv"
OUT_RECALCITRANT = PROJECT_DATA / "recalcitrant_genes.tsv"
OUT_NAMED = PROJECT_DATA / "already_named_genes.tsv"
OUT_PMIDS = PROJECT_DATA / "cited_pmids.tsv"
OUT_CLUSTERS = PROJECT_DATA / "cross_gene_clusters.md"


def main() -> None:
    df = pd.read_parquet(VERDICTS_PATH)
    print(f"Loaded {len(df)} verdicts")

    # Common columns
    cols_common = ["rank", "orgId", "locusId", "gene_desc", "annotation_category",
                   "in_specificphenotype", "max_abs_fit", "max_abs_t", "fit_x_t",
                   "confidence", "rationale"]

    # 1. Improvable list — for human curator hand-off
    imp = df[df["verdict"].isin(["improvable_new", "improvable_correction"])].copy()
    imp_cols = cols_common + ["verdict", "proposed_annotation", "ec_number", "papers_consulted"]
    imp = imp[imp_cols].sort_values("rank")
    # Convert papers list to comma-separated string for TSV
    imp["papers_consulted"] = imp["papers_consulted"].apply(
        lambda x: ",".join(str(p) for p in x) if x is not None and hasattr(x, "__iter__") else ""
    )
    imp.to_csv(OUT_IMPROVABLE, sep="\t", index=False)
    print(f"Wrote {OUT_IMPROVABLE}  ({len(imp)} improvable genes)")

    # 2. Recalcitrant list — project's answer set
    rec = df[df["verdict"] == "recalcitrant"].copy()
    rec_cols = cols_common + ["proposed_annotation", "papers_consulted"]
    rec = rec[rec_cols].sort_values("rank")
    rec["papers_consulted"] = rec["papers_consulted"].apply(
        lambda x: ",".join(str(p) for p in x) if x is not None and hasattr(x, "__iter__") else ""
    )
    rec.to_csv(OUT_RECALCITRANT, sep="\t", index=False)
    print(f"Wrote {OUT_RECALCITRANT}  ({len(rec)} recalcitrant genes)")

    # 3. Already-named list — for completeness
    nam = df[df["verdict"] == "already_correctly_named"].copy()
    nam_cols = cols_common + ["papers_consulted"]
    nam = nam[nam_cols].sort_values("rank")
    nam["papers_consulted"] = nam["papers_consulted"].apply(
        lambda x: ",".join(str(p) for p in x) if x is not None and hasattr(x, "__iter__") else ""
    )
    nam.to_csv(OUT_NAMED, sep="\t", index=False)
    print(f"Wrote {OUT_NAMED}  ({len(nam)} named-well genes)")

    # 4. PMID citation table
    pmid_to_genes = defaultdict(list)
    for _, r in df.iterrows():
        ps = r.get("papers_consulted")
        # papers_consulted comes back as numpy array from parquet; treat as iterable
        if ps is None:
            continue
        try:
            ps_list = list(ps)
        except TypeError:
            continue
        for p in ps_list:
            if p is None or str(p) == "" or str(p) == "nan":
                continue
            pmid_to_genes[str(p)].append((r["rank"], r["orgId"], r["locusId"], r["verdict"]))
    pmid_rows = []
    for pmid, genes in sorted(pmid_to_genes.items(), key=lambda x: -len(x[1])):
        pmid_rows.append({
            "pmid": pmid,
            "n_genes_citing": len(genes),
            "verdicts": ",".join(sorted(set(g[3] for g in genes))),
            "example_genes": "; ".join(f"{g[1]}::{g[2]}" for g in sorted(genes)[:5]),
        })
    pmids_df = pd.DataFrame(pmid_rows)
    pmids_df.to_csv(OUT_PMIDS, sep="\t", index=False)
    print(f"Wrote {OUT_PMIDS}  ({len(pmids_df)} unique PMIDs)")

    # 5. Cross-gene clusters — PMIDs cited by 3+ genes (signal of cross-gene functional coherence)
    cluster_md = ["# Cross-gene clusters — PMIDs cited by ≥3 genes\n",
                  "These are papers consulted by multiple subagents reasoning over different",
                  "genes; they often resolve a *cluster* of genes (operon, pathway, regulon)",
                  "into a coherent functional story.\n"]
    multi = pmids_df[pmids_df["n_genes_citing"] >= 3]
    if len(multi):
        for _, r in multi.iterrows():
            cluster_md.append(f"\n## PMID {r['pmid']} — cited by {r['n_genes_citing']} genes")
            cluster_md.append(f"verdicts: {r['verdicts']}")
            cluster_md.append("")
            cluster_md.append("Genes:")
            for rank, org, loc, verdict in sorted(pmid_to_genes[r['pmid']]):
                # Look up the proposed annotation for this gene
                row = df[(df["orgId"] == org) & (df["locusId"] == loc)].iloc[0]
                prop = row.get("proposed_annotation") or "—"
                cluster_md.append(f"- rank {rank} {org}::{loc} ({verdict}) → {prop}")
    else:
        cluster_md.append("\nNo PMID is cited by ≥3 genes yet.")
    with open(OUT_CLUSTERS, "w") as fh:
        fh.write("\n".join(cluster_md))
    print(f"Wrote {OUT_CLUSTERS}  ({len(multi)} cross-gene cluster PMIDs)")

    # Headline summary to stdout
    print("\n=== HEADLINE NUMBERS ===")
    n = len(df)
    counts = df["verdict"].value_counts()
    print(f"Total: {n}")
    for v in ["already_correctly_named", "improvable_correction", "improvable_new", "recalcitrant"]:
        c = int(counts.get(v, 0))
        print(f"  {v:30}: {c} ({c/n*100:.0f}%)")
    print(f"Improvable total: {int(counts.get('improvable_new', 0)) + int(counts.get('improvable_correction', 0))}")
    print(f"Cited PMIDs: {len(pmids_df)} ({len(multi)} cited by ≥3 genes)")


if __name__ == "__main__":
    main()
