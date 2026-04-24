"""
Stage 2 of PaperBLAST integration. Take DIAMOND hits from
`data/paperblast/fb_vs_paperblast.tsv` and join (pure pandas) to local
parquets of paperblast.{Gene, SeqToDuplicate, GenePaper, Snippet} downloaded
from BERDL MinIO under data/paperblast/.

Outputs:
  - data/paperblast_via_diamond.parquet
        per-FB-gene aggregate: hit count, paper count, top hit + top paper
  - data/fb_paperblast_hit_papers.parquet
        long-format (orgId, locusId, sseqid, identity, evalue, qcov, scov,
        geneId, pmId, title, year, journal) for downstream reasoning step

Run:
    python projects/fitness_browser_stubborn_set/notebooks/05_paperblast_via_diamond.py
"""
import time
from pathlib import Path
import pandas as pd
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
PB_DIR = REPO_ROOT / "data" / "paperblast"

DIAMOND_TSV = PB_DIR / "fb_vs_paperblast.tsv"
GENE_DIR = PB_DIR / "Gene"
SEQDUP_DIR = PB_DIR / "SeqToDuplicate"
GENEPAPER_DIR = PB_DIR / "GenePaper"

OUT_AGG = PROJECT_DATA / "paperblast_via_diamond.parquet"
OUT_PAPERS = PROJECT_DATA / "fb_paperblast_hit_papers.parquet"

DIAMOND_COLUMNS = [
    "qseqid", "sseqid", "pident", "length", "qlen", "slen",
    "evalue", "bitscore", "qcovhsp", "scovhsp",
]


def read_delta_dir(d: Path, columns=None) -> pd.DataFrame:
    """Read a Delta table directory by concatenating all .parquet parts.
    The _delta_log/ entries are metadata; we ignore them and just read the data files.
    For these tables there are no overwrites/deletes (they're write-once Delta tables),
    so reading the parquet parts directly is correct.
    """
    parts = sorted(p for p in d.glob("*.parquet"))
    return pd.concat([pd.read_parquet(p, columns=columns) for p in parts], ignore_index=True)


def main() -> None:
    t0 = time.time()
    print(f"[{time.time()-t0:5.1f}s] Loading DIAMOND hits from {DIAMOND_TSV}")
    hits = pd.read_csv(DIAMOND_TSV, sep="\t", header=None, names=DIAMOND_COLUMNS)
    qsplit = hits["qseqid"].str.split(":", n=1, expand=True)
    hits["orgId"] = qsplit[0]
    hits["locusId"] = qsplit[1]
    print(f"  {len(hits):,} hits | {hits['qseqid'].nunique():,} FB queries | "
          f"{hits['sseqid'].nunique():,} distinct sseqids")

    print(f"[{time.time()-t0:5.1f}s] Loading PaperBLAST tables from local parquets")
    gene = read_delta_dir(GENE_DIR, columns=["geneId", "organism", "desc"])
    seqdup = read_delta_dir(SEQDUP_DIR, columns=["sequence_id", "duplicate_id"])
    genepaper = read_delta_dir(GENEPAPER_DIR, columns=["geneId", "pmId", "title", "year", "journal"])
    print(f"  Gene: {len(gene):,} | SeqToDuplicate: {len(seqdup):,} | GenePaper: {len(genepaper):,}")

    # Resolve sseqid -> geneId(s)
    print(f"[{time.time()-t0:5.1f}s] Resolving sseqid -> geneId")
    unique_sseqids = pd.DataFrame({"sseqid": hits["sseqid"].unique()})

    # (a) sseqid is itself a Gene.geneId
    direct = unique_sseqids.merge(gene, left_on="sseqid", right_on="geneId", how="inner")
    direct = direct[["sseqid", "geneId", "organism", "desc"]]
    # (b) sseqid -> seqdup.sequence_id, duplicate_id is a Gene.geneId
    via = unique_sseqids.merge(seqdup, left_on="sseqid", right_on="sequence_id", how="inner")
    via = via.merge(gene, left_on="duplicate_id", right_on="geneId", how="inner")
    via = via[["sseqid", "geneId", "organism", "desc"]]
    resolved = pd.concat([direct, via], ignore_index=True).drop_duplicates(subset=["sseqid", "geneId"])
    resolved.rename(columns={"organism": "pb_organism", "desc": "pb_desc"}, inplace=True)
    print(f"  Resolved {len(resolved):,} (sseqid, geneId) rows | "
          f"{resolved['sseqid'].nunique():,} sseqids matched a geneId")

    # Convert year to int (some are strings)
    genepaper["year"] = pd.to_numeric(genepaper["year"], errors="coerce")

    # Pull papers per resolved geneId (filter to only those we need)
    needed_geneids = pd.DataFrame({"geneId": resolved["geneId"].unique()})
    print(f"[{time.time()-t0:5.1f}s] Joining {len(needed_geneids):,} geneIds to genepaper")
    papers = genepaper.merge(needed_geneids, on="geneId", how="inner")
    print(f"  {len(papers):,} (geneId, paper) rows | {papers['pmId'].nunique():,} unique pmIds")

    # Long format: per-hit + paper rows (one FB gene may have many)
    print(f"[{time.time()-t0:5.1f}s] Building long-format hits-and-papers table")
    long_df = (
        hits[["orgId", "locusId", "sseqid", "pident", "evalue", "qcovhsp", "scovhsp"]]
        .merge(resolved, on="sseqid", how="left")
        .merge(papers, on="geneId", how="left")
    )
    long_df.to_parquet(OUT_PAPERS, index=False)
    print(f"  Wrote {OUT_PAPERS}  ({len(long_df):,} rows, {OUT_PAPERS.stat().st_size/1e6:.1f} MB)")

    # Per-FB-gene aggregate
    print(f"[{time.time()-t0:5.1f}s] Aggregating per FB gene")
    by_gene_basic = (
        hits.sort_values("evalue")
            .groupby(["orgId", "locusId"], sort=False)
            .agg(
                n_hits=("sseqid", "nunique"),
                best_sseqid=("sseqid", "first"),
                best_pident=("pident", "first"),
                best_evalue=("evalue", "first"),
                best_qcov=("qcovhsp", "first"),
            )
            .reset_index()
    )
    paper_counts = (
        long_df.dropna(subset=["pmId"])
        .groupby(["orgId", "locusId"], sort=False)
        .agg(n_papers=("pmId", "nunique"))
        .reset_index()
    )
    by_gene = by_gene_basic.merge(paper_counts, on=["orgId", "locusId"], how="left")
    by_gene["n_papers"] = by_gene["n_papers"].fillna(0).astype(int)

    top_per = (
        long_df.dropna(subset=["pmId"])
        .sort_values(["orgId", "locusId", "evalue"], ascending=[True, True, True])
        .groupby(["orgId", "locusId"], sort=False)
        .agg(top_pmid=("pmId", "first"), top_paper_title=("title", "first"))
        .reset_index()
    )
    by_gene = by_gene.merge(top_per, on=["orgId", "locusId"], how="left")
    by_gene["paperblast_via_diamond"] = (by_gene["n_papers"] > 0).astype(int)

    by_gene.to_parquet(OUT_AGG, index=False)
    print(f"  Wrote {OUT_AGG}  ({len(by_gene):,} rows)")

    n_with_paper = int((by_gene["n_papers"] > 0).sum())
    print(f"\nSummary:")
    print(f"  FB genes with DIAMOND hit:     {len(by_gene):,}")
    print(f"  FB genes with PaperBLAST paper: {n_with_paper:,} "
          f"({n_with_paper/len(by_gene)*100:.1f}%)")
    if n_with_paper:
        nonzero = by_gene[by_gene['n_papers'] > 0]['n_papers']
        print(f"  Median papers (when >0):        {int(nonzero.median())}")
        print(f"  p75 papers:                     {int(nonzero.quantile(0.75))}")
        print(f"  Max papers:                     {int(nonzero.max())}")


if __name__ == "__main__":
    main()
