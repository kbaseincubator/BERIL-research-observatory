"""
Build the deduplicated (FB target gene → PaperBLAST homolog) mapping file.

Distinct from target_gene_paperblast_summaries.tsv which is denormalized at the
paper level. This file has exactly one row per (target_gene, homolog) pair,
useful for:
  - "what homologs does this FB gene have?" lookups
  - filtering homologs by identity / e-value before pulling literature
  - feeding the autoresearch loop a homolog list it can rank-cut

Output:
  data/training_set/target_gene_homologs.tsv
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"

HITS = PROJECT_DATA / "fb_paperblast_hit_papers.parquet"
ORG_NAMES = PROJECT_DATA / "fb_organism_names.tsv"
TRAINING_SET = PROJECT_DATA / "training_set"
OUT = TRAINING_SET / "target_gene_homologs.tsv"


def main() -> None:
    # 1. Collect target genes from each training file
    file_membership: dict[tuple[str, str], list[str]] = {}
    for fname in (
        "human_validated.jsonl",
        "llm_vs_human_disagreements.jsonl",
        "negatives.jsonl",
        "positives.jsonl",
    ):
        path = TRAINING_SET / fname
        if not path.exists():
            continue
        label = fname.replace(".jsonl", "")
        with open(path) as fh:
            for line in fh:
                r = json.loads(line)
                k = (r["orgId"], r["locusId"])
                file_membership.setdefault(k, []).append(label)
    print(f"Target genes across training files: {len(file_membership):,}", file=sys.stderr)

    # 2. orgId → organism lookup
    org_name: dict[str, str] = {}
    if ORG_NAMES.exists():
        with open(ORG_NAMES) as fh:
            next(fh)
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 2:
                    org_name[parts[0]] = parts[1]

    # 3. Load PaperBLAST hits, restrict to training-set targets
    hits = pd.read_parquet(HITS)
    target_set = set(file_membership.keys())
    sub = hits[hits.apply(lambda r: (r["orgId"], r["locusId"]) in target_set, axis=1)].copy()
    # Drop orphan placeholder rows where geneId is None (no PaperBLAST hit)
    sub = sub[sub["geneId"].notna() & (sub["geneId"].astype(str) != "None")]

    # 4. Aggregate to one row per (target, homolog)
    grouped = (
        sub.groupby(["orgId", "locusId", "geneId", "pb_organism", "pb_desc"])
        .agg(
            pident=("pident", "max"),
            evalue=("evalue", "min"),
            qcovhsp=("qcovhsp", "max"),
            scovhsp=("scovhsp", "max"),
            n_papers_cited=("pmId", "nunique"),
        )
        .reset_index()
    )
    grouped["organism"] = grouped["orgId"].map(org_name).fillna("")
    grouped["source_file"] = grouped.apply(
        lambda r: ";".join(file_membership[(r["orgId"], r["locusId"])]), axis=1
    )
    print(f"Distinct (target, homolog) rows: {len(grouped):,}", file=sys.stderr)

    cols = [
        "orgId", "locusId", "organism", "source_file",
        "paperblast_homolog_id", "paperblast_homolog_organism",
        "paperblast_homolog_desc",
        "pident", "evalue", "qcovhsp", "scovhsp",
        "n_papers_cited",
    ]
    out_rows = grouped.rename(columns={
        "geneId": "paperblast_homolog_id",
        "pb_organism": "paperblast_homolog_organism",
        "pb_desc": "paperblast_homolog_desc",
    })[cols]

    # Sort: by target, then by pident descending (best homolog first)
    out_rows = out_rows.sort_values(
        ["orgId", "locusId", "pident"], ascending=[True, True, False]
    )

    out_rows.to_csv(OUT, sep="\t", index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"Wrote {OUT}", file=sys.stderr)
    print(f"  unique target genes:                  {out_rows[['orgId','locusId']].drop_duplicates().shape[0]:,}", file=sys.stderr)
    print(f"  total (target, homolog) pairs:        {len(out_rows):,}", file=sys.stderr)
    print(f"  median homologs per target:           {out_rows.groupby(['orgId','locusId']).size().median():.0f}", file=sys.stderr)
    print(f"  max homologs for a target:            {out_rows.groupby(['orgId','locusId']).size().max()}", file=sys.stderr)
    print(f"  targets with zero homologs (orphans): {len(target_set) - out_rows[['orgId','locusId']].drop_duplicates().shape[0]:,}", file=sys.stderr)


if __name__ == "__main__":
    main()
