"""
Consolidate the three InterPro evidence layers into a single union table
keyed by (orgId, locusId, ipr_acc | signature_acc).

Inputs
  data/training_set/target_gene_interpro.tsv          (UniProt route, 66.3%)
  data/training_set/target_gene_interproscan.tsv      (MD5 route,     39.1%)
  data/training_set/target_gene_interpro_cluster.tsv  (Cluster route, 70.8%)

Output
  data/training_set/target_gene_interpro_union.tsv

Grain: one row per (orgId, locusId, ipr_acc).  When ipr_acc is empty
(some signatures — e.g. Gene3D, MobiDBLite — have no IPR mapping in the
InterProScan run), we fall back to signature_acc so those hits are not
lost.

Source priority for the descriptive columns is cluster > md5 > uniprot,
because the cluster route carries conservation context and DIAMOND
quality, and md5 and cluster pull from the same InterProScan run while
the uniprot route reads a different InterProScan index keyed by UniProt
accession.

Aggregations:
  sources       comma-joined subset of {uniprot, md5, cluster}
  n_sources     1..3
  go_ids        union of GO ids across sources, semicolon-delimited
  pathways      union of pathways across sources, semicolon-delimited
  start/stop    from highest-priority source (cluster > md5 > uniprot)
  signature_*   from highest-priority source
  score         from highest-priority source carrying a score
  cluster_*     from cluster route if hit
  uniprot_acc   from uniprot route if hit
  md5           from md5/cluster route if hit
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
TS = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data" / "training_set"

UNIPROT_TSV = TS / "target_gene_interpro.tsv"
MD5_TSV     = TS / "target_gene_interproscan.tsv"
CLUSTER_TSV = TS / "target_gene_interpro_cluster.tsv"
LINK_TSV    = TS.parent / "fb_pangenome_link.tsv"
OUT_PATH    = TS / "target_gene_interpro_union.tsv"

# Final column order
COLS = [
    "orgId", "locusId",
    "ipr_acc", "ipr_desc",
    "analysis", "signature_acc", "signature_desc",
    "start", "stop", "score",
    "go_ids", "pathways",
    "sources", "n_sources",
    "gene_cluster_id", "gtdb_species_clade_id",
    "is_core", "is_auxiliary", "is_singleton",
    "pident", "evalue", "bitscore",
    "uniprot_acc", "md5",
]


def _split_gos(s: str) -> list[str]:
    if not isinstance(s, str) or not s.strip():
        return []
    out = []
    for tok in s.replace(",", ";").split(";"):
        tok = tok.strip()
        if not tok:
            continue
        # uniprot route stored "GO:0003677:DNA binding"; keep only the GO id
        out.append(tok.split(":", 2)[0] + ":" + tok.split(":", 2)[1] if tok.startswith("GO:") else tok)
    return out


def _split_simple(s: str) -> list[str]:
    if not isinstance(s, str) or not s.strip():
        return []
    return [t.strip() for t in s.replace(",", ";").split(";") if t.strip()]


def load_uniprot() -> pd.DataFrame:
    df = pd.read_csv(UNIPROT_TSV, sep="\t", dtype=str, keep_default_na=False)
    df = df.rename(columns={
        "ipr_id":      "ipr_acc",
        "source_acc":  "signature_acc",
        "entry_name":  "signature_desc",
        "entry_type":  "analysis",
        "go_terms":    "_go_raw",
    })
    df["go_ids"]   = df["_go_raw"].map(_split_gos).map(lambda xs: ";".join(sorted(set(xs))))
    df["pathways"] = ""
    df["score"]    = ""
    df["md5"]      = ""
    df["gene_cluster_id"] = ""
    df["source"]   = "uniprot"
    keep = ["orgId", "locusId", "ipr_acc", "ipr_desc", "analysis",
            "signature_acc", "signature_desc", "start", "stop", "score",
            "go_ids", "pathways", "uniprot_acc", "md5", "gene_cluster_id",
            "source"]
    return df[keep]


def load_md5() -> pd.DataFrame:
    df = pd.read_csv(MD5_TSV, sep="\t", dtype=str, keep_default_na=False)
    df["go_ids"]   = df["go_ids"].map(_split_simple).map(lambda xs: ";".join(sorted(set(xs))))
    df["pathways"] = df["pathways"].map(_split_simple).map(lambda xs: ";".join(sorted(set(xs))))
    df["uniprot_acc"] = ""
    df["source"]   = "md5"
    keep = ["orgId", "locusId", "ipr_acc", "ipr_desc", "analysis",
            "signature_acc", "signature_desc", "start", "stop", "score",
            "go_ids", "pathways", "uniprot_acc", "md5", "gene_cluster_id",
            "source"]
    return df[keep]


def load_cluster() -> pd.DataFrame:
    df = pd.read_csv(CLUSTER_TSV, sep="\t", dtype=str, keep_default_na=False)
    df["go_ids"]   = df["go_ids"].map(_split_simple).map(lambda xs: ";".join(sorted(set(xs))))
    df["pathways"] = df["pathways"].map(_split_simple).map(lambda xs: ";".join(sorted(set(xs))))
    df["uniprot_acc"] = ""
    df["md5"] = ""  # cluster file has md5 in interproscan_domains; not propagated here
    df["source"]   = "cluster"
    keep = ["orgId", "locusId", "ipr_acc", "ipr_desc", "analysis",
            "signature_acc", "signature_desc", "start", "stop", "score",
            "go_ids", "pathways", "uniprot_acc", "md5", "gene_cluster_id",
            "gtdb_species_clade_id", "is_core", "is_auxiliary", "is_singleton",
            "pident", "evalue", "bitscore",
            "source"]
    return df[keep]


def main() -> None:
    up = load_uniprot()
    md5 = load_md5()
    cl = load_cluster()
    print(f"uniprot route : {len(up):>7,} rows  ({up[['orgId','locusId']].drop_duplicates().shape[0]:,} genes)", file=sys.stderr)
    print(f"md5 route     : {len(md5):>7,} rows  ({md5[['orgId','locusId']].drop_duplicates().shape[0]:,} genes)", file=sys.stderr)
    print(f"cluster route : {len(cl):>7,} rows  ({cl[['orgId','locusId']].drop_duplicates().shape[0]:,} genes)", file=sys.stderr)

    stacked = pd.concat([up, md5, cl], ignore_index=True, sort=False).fillna("")

    # Use signature_acc as fallback grain when ipr_acc is blank — we don't want
    # to drop Gene3D / MobiDBLite hits that lack an IPR mapping.
    stacked["_grain_acc"] = stacked["ipr_acc"].where(stacked["ipr_acc"].astype(bool), stacked["signature_acc"])
    stacked = stacked[stacked["_grain_acc"].astype(bool)]
    print(f"stacked       : {len(stacked):>7,} rows", file=sys.stderr)

    # Source priority for "first non-empty" columns: cluster > md5 > uniprot
    PRIORITY = {"cluster": 0, "md5": 1, "uniprot": 2}
    stacked["_prio"] = stacked["source"].map(PRIORITY)
    stacked = stacked.sort_values(["orgId", "locusId", "_grain_acc", "_prio"])

    def _first_nonempty(s: pd.Series) -> str:
        for v in s:
            if isinstance(v, str) and v:
                return v
        return ""

    def _union_semi(s: pd.Series) -> str:
        out: set[str] = set()
        for v in s:
            if isinstance(v, str) and v:
                out.update(t for t in v.split(";") if t)
        return ";".join(sorted(out))

    agg = {
        "ipr_acc":        _first_nonempty,
        "ipr_desc":       _first_nonempty,
        "analysis":       _first_nonempty,
        "signature_acc":  _first_nonempty,
        "signature_desc": _first_nonempty,
        "start":          _first_nonempty,
        "stop":           _first_nonempty,
        "score":          _first_nonempty,
        "go_ids":         _union_semi,
        "pathways":       _union_semi,
        "uniprot_acc":    _first_nonempty,
        "md5":            _first_nonempty,
        "gene_cluster_id":      _first_nonempty,
        "gtdb_species_clade_id": _first_nonempty,
        "is_core":        _first_nonempty,
        "is_auxiliary":   _first_nonempty,
        "is_singleton":   _first_nonempty,
        "pident":         _first_nonempty,
        "evalue":         _first_nonempty,
        "bitscore":       _first_nonempty,
        "source":         lambda s: ",".join(sorted(set(s))),
    }
    # Ensure all agg keys exist
    for k in agg:
        if k not in stacked.columns:
            stacked[k] = ""

    grouped = stacked.groupby(["orgId", "locusId", "_grain_acc"], as_index=False).agg(agg)
    grouped = grouped.rename(columns={"source": "sources"})
    grouped["n_sources"] = grouped["sources"].map(lambda s: len(s.split(",")) if s else 0)
    grouped = grouped.drop(columns=["_grain_acc"])

    # Authoritative cluster membership comes from the FB <-> pangenome link
    # table (per-gene DIAMOND best hit), not from whether any InterPro hit
    # happened to land via the cluster route. Genes missing from the link
    # table get "unknown" for the conservation flags so downstream code can
    # treat them as a distinct tier rather than confusing them with False.
    link = pd.read_csv(
        LINK_TSV, sep="\t", dtype=str, keep_default_na=False,
        usecols=["orgId", "locusId", "gene_cluster_id", "gtdb_species_clade_id",
                 "is_core", "is_auxiliary", "is_singleton"],
    )
    link = link.drop_duplicates(subset=["orgId", "locusId"], keep="first")

    grouped = grouped.drop(columns=["gene_cluster_id", "gtdb_species_clade_id",
                                    "is_core", "is_auxiliary", "is_singleton"])
    grouped = grouped.merge(link, on=["orgId", "locusId"], how="left")
    fill_unknown = ["gene_cluster_id", "gtdb_species_clade_id",
                    "is_core", "is_auxiliary", "is_singleton"]
    for c in fill_unknown:
        grouped[c] = grouped[c].fillna("unknown").replace("", "unknown")

    grouped = grouped[COLS]
    grouped.to_csv(OUT_PATH, sep="\t", index=False)
    size_mb = OUT_PATH.stat().st_size / 1e6
    print(f"\nwrote {OUT_PATH}  ({size_mb:.1f} MB, {len(grouped):,} rows)", file=sys.stderr)

    # Quick stats
    n_genes = grouped[["orgId", "locusId"]].drop_duplicates().shape[0]
    print(f"  unique training genes covered: {n_genes:,}", file=sys.stderr)
    print(f"  source breakdown (rows):", file=sys.stderr)
    for src in ["uniprot", "md5", "cluster"]:
        n = grouped["sources"].str.contains(src, regex=False).sum()
        print(f"    {src:10s}: {n:>7,}", file=sys.stderr)
    print(f"  rows by n_sources:", file=sys.stderr)
    print(grouped["n_sources"].value_counts().sort_index().to_string(), file=sys.stderr)


if __name__ == "__main__":
    main()
