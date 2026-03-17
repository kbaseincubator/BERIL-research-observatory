#!/usr/bin/env python3
"""
Extract structured tables from bakta_proteins JSON output.

Parses one bakta JSON file and produces 4 per-chunk TSVs:
  - bakta_annotations.tsv    (one row per protein)
  - bakta_db_xrefs.tsv       (one row per cross-reference)
  - bakta_pfam_domains.tsv   (one row per Pfam domain hit)
  - bakta_amr.tsv            (one row per AMR expert annotation)

Computes molecular_weight and isoelectric_point for ALL proteins
(bakta only computes these for hypothetical proteins).

Usage:
  python extract_bakta_tables.py <input.json> <output_dir>
"""

import argparse
import csv
import json
import os
import sys

from Bio.SeqUtils.ProtParam import ProteinAnalysis


def compute_seq_stats(aa_seq):
    """Compute molecular weight and isoelectric point for a protein sequence."""
    seq = aa_seq.rstrip("*")
    if not seq:
        return None, None
    try:
        pa = ProteinAnalysis(seq)
        mw = round(pa.molecular_weight(), 2)
        pi = round(pa.isoelectric_point(), 2)
        return mw, pi
    except Exception:
        return None, None


def extract_tables(json_path, output_dir):
    """Extract 4 tables from a bakta JSON file."""
    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading {json_path}...")
    with open(json_path) as f:
        data = json.load(f)
    features = data.get("features", [])
    print(f"  {len(features):,} features loaded")

    # Output file paths
    ann_path = os.path.join(output_dir, "bakta_annotations.tsv")
    xref_path = os.path.join(output_dir, "bakta_db_xrefs.tsv")
    pfam_path = os.path.join(output_dir, "bakta_pfam_domains.tsv")
    amr_path = os.path.join(output_dir, "bakta_amr.tsv")

    # Column definitions
    ann_fields = [
        "gene_cluster_id", "length", "gene", "product", "hypothetical",
        "ec", "go", "cog_id", "cog_category", "kegg_orthology_id",
        "refseq", "uniparc", "uniref100", "uniref90", "uniref50",
        "molecular_weight", "isoelectric_point",
    ]
    xref_fields = ["gene_cluster_id", "db", "accession"]
    pfam_fields = [
        "gene_cluster_id", "pfam_id", "pfam_name", "start", "stop",
        "score", "evalue", "aa_cov", "hmm_cov",
    ]
    amr_fields = [
        "gene_cluster_id", "amr_gene", "amr_product", "method",
        "identity", "query_cov", "subject_cov", "accession",
    ]

    with (
        open(ann_path, "w", newline="") as ann_f,
        open(xref_path, "w", newline="") as xref_f,
        open(pfam_path, "w", newline="") as pfam_f,
        open(amr_path, "w", newline="") as amr_f,
    ):
        ann_w = csv.DictWriter(ann_f, fieldnames=ann_fields, delimiter="\t")
        xref_w = csv.DictWriter(xref_f, fieldnames=xref_fields, delimiter="\t")
        pfam_w = csv.DictWriter(pfam_f, fieldnames=pfam_fields, delimiter="\t")
        amr_w = csv.DictWriter(amr_f, fieldnames=amr_fields, delimiter="\t")

        ann_w.writeheader()
        xref_w.writeheader()
        pfam_w.writeheader()
        amr_w.writeheader()

        counts = {"annotations": 0, "db_xrefs": 0, "pfam_domains": 0, "amr": 0}
        stats_computed = 0
        stats_from_json = 0

        for i, feat in enumerate(features):
            if (i + 1) % 100000 == 0:
                print(f"  Processing feature {i + 1:,}/{len(features):,}...")

            gene_cluster_id = feat["id"]
            psc = feat.get("psc") or {}
            pscc = feat.get("pscc") or {}
            ups = feat.get("ups") or {}
            ips = feat.get("ips") or {}

            # Molecular weight and isoelectric point
            seq_stats = feat.get("seq_stats")
            if seq_stats:
                mw = seq_stats.get("molecular_weight", "")
                pi = seq_stats.get("isoelectric_point", "")
                stats_from_json += 1
            else:
                mw, pi = compute_seq_stats(feat.get("aa", ""))
                if mw is None:
                    mw, pi = "", ""
                else:
                    stats_computed += 1

            # EC and GO from psc
            ec_ids = psc.get("ec_ids", [])
            go_ids = psc.get("go_ids", [])

            # UniRef50: prefer psc, fall back to pscc
            uniref50 = psc.get("uniref50_id", "") or pscc.get("uniref50_id", "")

            ann_w.writerow({
                "gene_cluster_id": gene_cluster_id,
                "length": feat["length"],
                "gene": feat.get("gene") or "",
                "product": feat.get("product", ""),
                "hypothetical": feat.get("hypothetical", False),
                "ec": ";".join(ec_ids) if ec_ids else "",
                "go": ";".join(go_ids) if go_ids else "",
                "cog_id": psc.get("cog_id", ""),
                "cog_category": psc.get("cog_category", ""),
                "kegg_orthology_id": psc.get("kegg_orthology_id", ""),
                "refseq": ups.get("ncbi_nrp_id", ""),
                "uniparc": ups.get("uniparc_id", ""),
                "uniref100": ups.get("uniref100_id", ""),
                "uniref90": ips.get("uniref90_id", ""),
                "uniref50": uniref50,
                "molecular_weight": mw,
                "isoelectric_point": pi,
            })
            counts["annotations"] += 1

            # db_xrefs
            for xref in feat.get("db_xrefs", []):
                parts = xref.split(":", 1)
                if len(parts) == 2:
                    xref_w.writerow({
                        "gene_cluster_id": gene_cluster_id,
                        "db": parts[0],
                        "accession": parts[1],
                    })
                    counts["db_xrefs"] += 1

            # Pfam domains
            for pfam in feat.get("pfams", []):
                pfam_w.writerow({
                    "gene_cluster_id": gene_cluster_id,
                    "pfam_id": pfam.get("id", ""),
                    "pfam_name": pfam.get("name", ""),
                    "start": pfam.get("start", ""),
                    "stop": pfam.get("stop", ""),
                    "score": pfam.get("score", ""),
                    "evalue": pfam.get("evalue", ""),
                    "aa_cov": pfam.get("aa_cov", ""),
                    "hmm_cov": pfam.get("hmm_cov", ""),
                })
                counts["pfam_domains"] += 1

            # AMR expert annotations (amrfinder only)
            for expert in feat.get("expert", []):
                if expert.get("type") == "amrfinder":
                    amr_w.writerow({
                        "gene_cluster_id": gene_cluster_id,
                        "amr_gene": expert.get("gene", ""),
                        "amr_product": expert.get("product", ""),
                        "method": expert.get("method", ""),
                        "identity": expert.get("identity", ""),
                        "query_cov": expert.get("query_cov", ""),
                        "subject_cov": expert.get("subject_cov", ""),
                        "accession": expert.get("id", ""),
                    })
                    counts["amr"] += 1

    print(f"\nResults written to {output_dir}/")
    print(f"  annotations:  {counts['annotations']:>12,} rows")
    print(f"  db_xrefs:     {counts['db_xrefs']:>12,} rows")
    print(f"  pfam_domains: {counts['pfam_domains']:>12,} rows")
    print(f"  amr:          {counts['amr']:>12,} rows")
    print(f"  seq_stats:    {stats_from_json:>12,} from JSON, {stats_computed:,} computed")


def main():
    parser = argparse.ArgumentParser(
        description="Extract bakta annotation tables from JSON"
    )
    parser.add_argument("json_file", help="Input bakta JSON file")
    parser.add_argument("output_dir", help="Output directory for TSV files")
    args = parser.parse_args()

    if not os.path.exists(args.json_file):
        print(f"ERROR: Input file not found: {args.json_file}", file=sys.stderr)
        sys.exit(1)

    extract_tables(args.json_file, args.output_dir)


if __name__ == "__main__":
    main()
