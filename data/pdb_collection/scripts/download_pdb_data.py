#!/usr/bin/env python3
"""
Download PDB metadata from RCSB and SIFTS for Delta Lake ingestion.

Strategy:
  1. Fetch all current PDB IDs from RCSB holdings API (~250K IDs)
  2. Batch-query RCSB GraphQL API for metadata (1000 IDs per request, ~3 min total)
  3. Download SIFTS pdb_chain_uniprot.tsv.gz for PDB→UniProt mapping
  4. Output headerized TSVs: pdb_entries.tsv, pdb_uniprot_mapping.tsv

Usage:
  python download_pdb_data.py --output-dir /pscratch/sd/p/psdehal/pdb_collection/
  python download_pdb_data.py --output-dir ./pdb_data --batch-size 500
  python download_pdb_data.py --output-dir ./pdb_data --sifts-only
  python download_pdb_data.py --output-dir ./pdb_data --entries-only
"""

import argparse
import csv
import gzip
import json
import os
import sys
import time
import urllib.request
import urllib.error

RCSB_HOLDINGS_URL = "https://data.rcsb.org/rest/v1/holdings/current/entry_ids"
RCSB_GRAPHQL_URL = "https://data.rcsb.org/graphql"
SIFTS_URL = "https://ftp.ebi.ac.uk/pub/databases/msd/sifts/flatfiles/tsv/pdb_chain_uniprot.tsv.gz"

GRAPHQL_QUERY = """{
  entries(entry_ids: %s) {
    rcsb_id
    struct { title }
    rcsb_entry_info { resolution_combined experimental_method }
    exptl { method }
    refine { ls_R_factor_R_free ls_R_factor_R_work }
    rcsb_accession_info { deposit_date initial_release_date }
    rcsb_primary_citation { pdbx_database_id_DOI }
    polymer_entities {
      rcsb_entity_source_organism { ncbi_scientific_name }
    }
  }
}"""

ENTRIES_COLUMNS = [
    "pdb_id", "title", "method", "method_full", "resolution",
    "r_work", "r_free", "organism", "deposition_date", "release_date",
    "citation_doi",
]

MAPPING_COLUMNS = [
    "pdb_id", "chain_id", "uniprot_accession",
    "res_beg", "res_end", "pdb_beg", "pdb_end", "sp_beg", "sp_end",
]

VALIDATION_GRAPHQL_QUERY = """{
  entries(entry_ids: %s) {
    rcsb_id
    pdbx_vrpt_summary_geometry {
      clashscore
      percent_ramachandran_outliers
      percent_rotamer_outliers
      angles_RMSZ
      bonds_RMSZ
    }
  }
}"""

VALIDATION_COLUMNS = [
    "pdb_id", "clashscore", "percent_ramachandran_outliers",
    "percent_rotamer_outliers", "angles_rmsz", "bonds_rmsz",
]


def fetch_all_pdb_ids():
    """Fetch all current PDB IDs from RCSB holdings API."""
    print("Fetching all PDB IDs from RCSB holdings API...")
    req = urllib.request.Request(RCSB_HOLDINGS_URL)
    with urllib.request.urlopen(req, timeout=30) as resp:
        ids = json.loads(resp.read())
    print(f"  Found {len(ids):,} PDB entries")
    return ids


def batch_graphql_query(pdb_ids, batch_size=1000, query_template=None):
    """Query RCSB GraphQL API in batches. Yields parsed entry dicts."""
    if query_template is None:
        query_template = GRAPHQL_QUERY
    total = len(pdb_ids)
    n_batches = (total + batch_size - 1) // batch_size

    for i in range(0, total, batch_size):
        batch = pdb_ids[i:i + batch_size]
        batch_num = i // batch_size + 1
        print(f"  Batch {batch_num}/{n_batches} ({len(batch)} IDs)...", end="", flush=True)

        query = query_template % json.dumps(batch)
        data = json.dumps({"query": query}).encode("utf-8")
        req = urllib.request.Request(
            RCSB_GRAPHQL_URL, data=data,
            headers={"Content-Type": "application/json"},
        )

        retries = 3
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    result = json.loads(resp.read())
                break
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt < retries - 1:
                    print(f" retry {attempt + 1}...", end="", flush=True)
                    time.sleep(2 ** attempt)
                else:
                    print(f" FAILED: {e}")
                    continue

        entries = result.get("data", {}).get("entries", [])
        print(f" {len(entries)} entries")

        for entry in entries:
            if entry is None:
                continue
            yield entry

        # Brief pause between batches to be polite
        if i + batch_size < total:
            time.sleep(0.1)


def parse_entry(entry):
    """Parse a GraphQL entry response into a flat dict for TSV output."""
    rcsb_info = entry.get("rcsb_entry_info") or {}
    struct = entry.get("struct") or {}
    accession = entry.get("rcsb_accession_info") or {}
    citation = entry.get("rcsb_primary_citation") or {}

    # Resolution: rcsb_entry_info.resolution_combined is a list
    resolution_list = rcsb_info.get("resolution_combined") or []
    resolution = resolution_list[0] if resolution_list else None

    # Method
    method = rcsb_info.get("experimental_method", "")
    exptl = entry.get("exptl") or [{}]
    method_full = exptl[0].get("method", "") if exptl else ""

    # R-factors
    refine = entry.get("refine") or [{}]
    r_work = refine[0].get("ls_R_factor_R_work") if refine else None
    r_free = refine[0].get("ls_R_factor_R_free") if refine else None

    # Organism (from first polymer entity)
    organism = ""
    polymer_entities = entry.get("polymer_entities") or []
    for pe in polymer_entities:
        sources = pe.get("rcsb_entity_source_organism") or []
        if sources:
            organism = sources[0].get("ncbi_scientific_name", "")
            if organism:
                break

    # Dates
    dep_date = (accession.get("deposit_date") or "")[:10]
    rel_date = (accession.get("initial_release_date") or "")[:10]

    return {
        "pdb_id": entry.get("rcsb_id", ""),
        "title": (struct.get("title") or "").replace("\t", " ").replace("\n", " "),
        "method": method,
        "method_full": method_full,
        "resolution": resolution,
        "r_work": r_work,
        "r_free": r_free,
        "organism": (organism or "").replace("\t", " "),
        "deposition_date": dep_date,
        "release_date": rel_date,
        "citation_doi": citation.get("pdbx_database_id_DOI", ""),
    }


def download_entries(pdb_ids, output_path, batch_size=1000):
    """Download PDB entry metadata via GraphQL and write to TSV."""
    print(f"\nDownloading PDB entry metadata ({len(pdb_ids):,} entries)...")
    t0 = time.time()

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(ENTRIES_COLUMNS)

        count = 0
        for entry in batch_graphql_query(pdb_ids, batch_size):
            row = parse_entry(entry)
            writer.writerow([
                _fmt(row.get(col)) for col in ENTRIES_COLUMNS
            ])
            count += 1

    dt = time.time() - t0
    print(f"  Wrote {count:,} entries to {output_path} in {dt:.1f}s")
    return count


def download_sifts(output_path):
    """Download and parse SIFTS pdb_chain_uniprot.tsv.gz."""
    print(f"\nDownloading SIFTS PDB→UniProt mapping...")
    gz_path = output_path + ".gz"

    # Download
    urllib.request.urlretrieve(SIFTS_URL, gz_path)
    gz_size = os.path.getsize(gz_path)
    print(f"  Downloaded {gz_path} ({gz_size:,} bytes)")

    # Parse and write normalized TSV
    print(f"  Parsing SIFTS mapping...")
    count = 0
    with gzip.open(gz_path, "rt") as fin, \
         open(output_path, "w", newline="") as fout:
        writer = csv.writer(fout, delimiter="\t", lineterminator="\n")
        writer.writerow(MAPPING_COLUMNS)

        for line in fin:
            if line.startswith("#") or line.startswith("PDB"):
                continue  # skip comments and header
            parts = line.strip().split("\t")
            if len(parts) < 9:
                continue

            pdb_id = parts[0].upper()  # SIFTS uses lowercase
            chain_id = parts[1]
            uniprot = parts[2]

            writer.writerow([
                pdb_id, chain_id, uniprot,
                parts[3], parts[4],  # res_beg, res_end
                parts[5], parts[6],  # pdb_beg, pdb_end
                parts[7], parts[8],  # sp_beg, sp_end
            ])
            count += 1

    print(f"  Wrote {count:,} mapping rows to {output_path}")

    # Clean up gz
    os.remove(gz_path)
    return count


def parse_validation_entry(entry):
    """Parse a GraphQL validation entry into a flat dict."""
    geom = entry.get("pdbx_vrpt_summary_geometry") or [{}]
    g = geom[0] if geom else {}
    return {
        "pdb_id": entry.get("rcsb_id", ""),
        "clashscore": g.get("clashscore"),
        "percent_ramachandran_outliers": g.get("percent_ramachandran_outliers"),
        "percent_rotamer_outliers": g.get("percent_rotamer_outliers"),
        "angles_rmsz": g.get("angles_RMSZ"),
        "bonds_rmsz": g.get("bonds_RMSZ"),
    }


def download_validation(pdb_ids, output_path, batch_size=1000):
    """Download PDB validation metrics via GraphQL and write to TSV."""
    print(f"\nDownloading PDB validation metrics ({len(pdb_ids):,} entries)...")
    t0 = time.time()

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(VALIDATION_COLUMNS)

        count = 0
        for entry in batch_graphql_query(pdb_ids, batch_size,
                                          query_template=VALIDATION_GRAPHQL_QUERY):
            row = parse_validation_entry(entry)
            writer.writerow([_fmt(row.get(col)) for col in VALIDATION_COLUMNS])
            count += 1

    dt = time.time() - t0
    print(f"  Wrote {count:,} validation rows to {output_path} in {dt:.1f}s")
    return count


def _fmt(val):
    """Format a value for TSV output."""
    if val is None:
        return ""
    if isinstance(val, float):
        return f"{val:.6g}"
    return str(val)


def main():
    parser = argparse.ArgumentParser(
        description="Download PDB metadata from RCSB and SIFTS"
    )
    parser.add_argument(
        "--output-dir",
        default="/pscratch/sd/p/psdehal/pdb_collection",
        help="Output directory for TSV files",
    )
    parser.add_argument("--batch-size", type=int, default=1000,
                        help="GraphQL batch size (default: 1000)")
    parser.add_argument("--entries-only", action="store_true",
                        help="Only download PDB entries, skip SIFTS and validation")
    parser.add_argument("--sifts-only", action="store_true",
                        help="Only download SIFTS mapping")
    parser.add_argument("--validation-only", action="store_true",
                        help="Only download validation metrics")
    parser.add_argument("--sample", type=int, default=0,
                        help="Only download first N entries (for testing)")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    entries_path = os.path.join(args.output_dir, "pdb_entries.tsv")
    mapping_path = os.path.join(args.output_dir, "pdb_uniprot_mapping.tsv")
    validation_path = os.path.join(args.output_dir, "pdb_validation.tsv")

    n_entries = 0
    n_mappings = 0
    n_validation = 0

    # Determine what to download
    only_flags = [args.entries_only, args.sifts_only, args.validation_only]
    do_all = not any(only_flags)

    if do_all or args.entries_only or args.validation_only:
        pdb_ids = fetch_all_pdb_ids()
        if args.sample:
            pdb_ids = pdb_ids[:args.sample]
            print(f"  Sampling first {args.sample} entries")

    if do_all or args.entries_only:
        n_entries = download_entries(pdb_ids, entries_path, args.batch_size)

    if do_all or args.sifts_only:
        n_mappings = download_sifts(mapping_path)

    if do_all or args.validation_only:
        n_validation = download_validation(pdb_ids, validation_path, args.batch_size)

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"  pdb_entries.tsv:         {n_entries:>10,} rows")
    print(f"  pdb_uniprot_mapping.tsv: {n_mappings:>10,} rows")
    print(f"  pdb_validation.tsv:      {n_validation:>10,} rows")
    print(f"  Output directory:        {args.output_dir}")


if __name__ == "__main__":
    main()
