#!/usr/bin/env python3
"""
Download extended PDB metadata: taxonomy, ligands, citations, Pfam, sequence clusters.

Complements download_pdb_data.py (which handles entries, SIFTS mapping, and validation).
All downloads are restartable — existing TSV files are detected and skipped unless --force.

Usage:
  python download_pdb_extended.py --output-dir /pscratch/sd/p/psdehal/pdb_collection/
  python download_pdb_extended.py --output-dir /path/ --only ligands citations
  python download_pdb_extended.py --output-dir /path/ --only pfam clusters
  python download_pdb_extended.py --output-dir /path/ --only taxonomy --force
  python download_pdb_extended.py --output-dir /path/ --sample 100

Data sources:
  - Taxonomy + ligands + citations: RCSB GraphQL API (batch 1000/request)
  - Pfam: SIFTS pdb_chain_pfam.tsv.gz (EBI FTP)
  - Sequence clusters: RCSB CDN (pre-computed, 30/50/70/90/95/100% identity)
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
SIFTS_PFAM_URL = "https://ftp.ebi.ac.uk/pub/databases/msd/sifts/flatfiles/tsv/pdb_chain_pfam.tsv.gz"
RCSB_CLUSTERS_URL = "https://cdn.rcsb.org/resources/sequence/clusters/clusters-by-entity-%d.txt"

# --- GraphQL queries ---

TAXONOMY_LIGANDS_QUERY = """{
  entries(entry_ids: %s) {
    rcsb_id
    polymer_entities {
      rcsb_entity_source_organism {
        ncbi_scientific_name
        taxonomy_lineage { id name depth }
      }
    }
    nonpolymer_entities {
      nonpolymer_comp {
        chem_comp { id name type formula formula_weight }
      }
    }
  }
}"""

CITATIONS_QUERY = """{
  entries(entry_ids: %s) {
    rcsb_id
    citation {
      id title year journal_abbrev journal_volume page_first
      pdbx_database_id_DOI pdbx_database_id_PubMed
      rcsb_is_primary rcsb_authors
    }
  }
}"""

# --- Column definitions ---

TAXONOMY_COLUMNS = ["pdb_id", "taxonomy_id", "organism"]

LIGAND_COLUMNS = [
    "pdb_id", "ligand_id", "ligand_name", "ligand_type",
    "formula", "formula_weight",
]

CITATION_COLUMNS = [
    "pdb_id", "citation_id", "is_primary", "title", "year",
    "journal", "volume", "page_first", "doi", "pubmed_id", "authors",
]

PFAM_COLUMNS = ["pdb_id", "chain_id", "uniprot_accession", "pfam_id", "coverage"]

CLUSTER_COLUMNS = ["cluster_id", "pdb_entity_id", "identity_level"]


# --- Utility functions ---

def fetch_all_pdb_ids():
    """Fetch all current PDB IDs from RCSB holdings API."""
    print("Fetching all PDB IDs from RCSB holdings API...")
    req = urllib.request.Request(RCSB_HOLDINGS_URL)
    with urllib.request.urlopen(req, timeout=30) as resp:
        ids = json.loads(resp.read())
    print(f"  Found {len(ids):,} PDB entries")
    return ids


def batch_graphql(pdb_ids, query_template, batch_size=1000):
    """Query RCSB GraphQL API in batches. Yields parsed entry dicts.

    Handles retries and network errors gracefully.
    """
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

        entries = None
        for attempt in range(5):
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    result = json.loads(resp.read())
                entries = result.get("data", {}).get("entries", [])
                break
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                wait = 2 ** attempt
                print(f" retry {attempt + 1} (wait {wait}s)...", end="", flush=True)
                time.sleep(wait)

        if entries is None:
            print(f" FAILED after 5 retries, skipping batch")
            continue

        print(f" {len(entries)} entries")
        for entry in entries:
            if entry is not None:
                yield entry

        if i + batch_size < total:
            time.sleep(0.1)


def _fmt(val):
    """Format a value for TSV output."""
    if val is None:
        return ""
    if isinstance(val, float):
        return f"{val:.6g}"
    return str(val).replace("\t", " ").replace("\n", " ")


def _should_download(path, force):
    """Check if a file should be downloaded (doesn't exist or --force)."""
    if force:
        return True
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"  SKIP {os.path.basename(path)} (exists, {size:,} bytes). Use --force to re-download.")
        return False
    return True


# --- Download functions ---

def download_taxonomy(pdb_ids, output_path, batch_size=1000):
    """Download taxonomy IDs for all PDB entries."""
    print(f"\nDownloading taxonomy data ({len(pdb_ids):,} entries)...")
    t0 = time.time()

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(TAXONOMY_COLUMNS)
        count = 0

        for entry in batch_graphql(pdb_ids, TAXONOMY_LIGANDS_QUERY, batch_size):
            pdb_id = entry.get("rcsb_id", "")
            tax_id = None
            organism = ""

            for pe in (entry.get("polymer_entities") or []):
                for org in (pe.get("rcsb_entity_source_organism") or []):
                    organism = org.get("ncbi_scientific_name") or ""
                    lineage = org.get("taxonomy_lineage") or []
                    # depth=0 is the species level
                    for t in lineage:
                        if t.get("depth") == 0:
                            tax_id = t.get("id")
                            break
                    if tax_id:
                        break
                if tax_id:
                    break

            writer.writerow([pdb_id, _fmt(tax_id), _fmt(organism)])
            count += 1

    dt = time.time() - t0
    print(f"  Wrote {count:,} taxonomy rows to {output_path} in {dt:.1f}s")
    return count


def download_ligands(pdb_ids, output_path, batch_size=1000):
    """Download ligand/small molecule data for all PDB entries."""
    print(f"\nDownloading ligand data ({len(pdb_ids):,} entries)...")
    t0 = time.time()

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(LIGAND_COLUMNS)
        count = 0

        for entry in batch_graphql(pdb_ids, TAXONOMY_LIGANDS_QUERY, batch_size):
            pdb_id = entry.get("rcsb_id", "")
            for ne in (entry.get("nonpolymer_entities") or []):
                comp = (ne.get("nonpolymer_comp") or {}).get("chem_comp") or {}
                if not comp.get("id"):
                    continue
                writer.writerow([
                    pdb_id,
                    _fmt(comp.get("id")),
                    _fmt(comp.get("name")),
                    _fmt(comp.get("type")),
                    _fmt(comp.get("formula")),
                    _fmt(comp.get("formula_weight")),
                ])
                count += 1

    dt = time.time() - t0
    print(f"  Wrote {count:,} ligand rows to {output_path} in {dt:.1f}s")
    return count


def download_citations(pdb_ids, output_path, batch_size=1000):
    """Download citation data for all PDB entries."""
    print(f"\nDownloading citation data ({len(pdb_ids):,} entries)...")
    t0 = time.time()

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(CITATION_COLUMNS)
        count = 0

        for entry in batch_graphql(pdb_ids, CITATIONS_QUERY, batch_size):
            pdb_id = entry.get("rcsb_id", "")
            for c in (entry.get("citation") or []):
                authors = c.get("rcsb_authors") or []
                if isinstance(authors, list):
                    authors = "; ".join(str(a) for a in authors)
                writer.writerow([
                    pdb_id,
                    _fmt(c.get("id")),
                    _fmt(c.get("rcsb_is_primary")),
                    _fmt(c.get("title")),
                    _fmt(c.get("year")),
                    _fmt(c.get("journal_abbrev")),
                    _fmt(c.get("journal_volume")),
                    _fmt(c.get("page_first")),
                    _fmt(c.get("pdbx_database_id_DOI")),
                    _fmt(c.get("pdbx_database_id_PubMed")),
                    _fmt(authors),
                ])
                count += 1

    dt = time.time() - t0
    print(f"  Wrote {count:,} citation rows to {output_path} in {dt:.1f}s")
    return count


def download_pfam(output_path):
    """Download and parse SIFTS PDB→Pfam mapping."""
    print(f"\nDownloading SIFTS PDB→Pfam mapping...")
    gz_path = output_path + ".gz"

    urllib.request.urlretrieve(SIFTS_PFAM_URL, gz_path)
    gz_size = os.path.getsize(gz_path)
    print(f"  Downloaded {gz_path} ({gz_size:,} bytes)")

    print(f"  Parsing Pfam mapping...")
    count = 0
    with gzip.open(gz_path, "rt") as fin, \
         open(output_path, "w", newline="") as fout:
        writer = csv.writer(fout, delimiter="\t", lineterminator="\n")
        writer.writerow(PFAM_COLUMNS)

        for line in fin:
            if line.startswith("#") or line.startswith("PDB"):
                continue
            parts = line.strip().split("\t")
            if len(parts) < 5:
                continue
            writer.writerow([
                parts[0].upper(),   # pdb_id
                parts[1],           # chain_id
                parts[2],           # uniprot_accession
                parts[3],           # pfam_id
                parts[4],           # coverage
            ])
            count += 1

    os.remove(gz_path)
    print(f"  Wrote {count:,} Pfam mapping rows to {output_path}")
    return count


def download_clusters(output_path, identity_levels=None):
    """Download RCSB pre-computed sequence clusters."""
    if identity_levels is None:
        identity_levels = [30, 50, 70, 90, 95, 100]

    print(f"\nDownloading RCSB sequence clusters ({identity_levels})...")

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(CLUSTER_COLUMNS)
        total_count = 0

        for level in identity_levels:
            url = RCSB_CLUSTERS_URL % level
            print(f"  Downloading {level}% clusters...", end="", flush=True)

            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=30) as resp:
                    content = resp.read().decode("utf-8")
            except Exception as e:
                print(f" FAILED: {e}")
                continue

            cluster_count = 0
            for line in content.strip().split("\n"):
                if not line.strip():
                    continue
                members = line.strip().split()
                cluster_id = f"cl{level}_{cluster_count}"
                for member in members:
                    writer.writerow([cluster_id, member, level])
                    total_count += 1
                cluster_count += 1

            print(f" {cluster_count:,} clusters")

    print(f"  Wrote {total_count:,} cluster membership rows to {output_path}")
    return total_count


# --- Main ---

DATASETS = {
    "taxonomy": ("pdb_taxonomy.tsv", download_taxonomy, True),
    "ligands": ("pdb_ligands.tsv", download_ligands, True),
    "citations": ("pdb_citations.tsv", download_citations, True),
    "pfam": ("pdb_pfam.tsv", download_pfam, False),
    "clusters": ("pdb_sequence_clusters.tsv", download_clusters, False),
}


def main():
    parser = argparse.ArgumentParser(
        description="Download extended PDB metadata (taxonomy, ligands, citations, Pfam, clusters)"
    )
    parser.add_argument(
        "--output-dir",
        default="/pscratch/sd/p/psdehal/pdb_collection",
        help="Output directory for TSV files",
    )
    parser.add_argument(
        "--only", nargs="+",
        choices=list(DATASETS.keys()),
        help="Only download specific datasets",
    )
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--sample", type=int, default=0,
                        help="Only process first N entries (for testing)")
    parser.add_argument("--force", action="store_true",
                        help="Re-download even if files exist")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    datasets_to_run = args.only or list(DATASETS.keys())

    # Fetch PDB IDs if any GraphQL-based datasets are requested
    needs_ids = any(DATASETS[d][2] for d in datasets_to_run)
    pdb_ids = None
    if needs_ids:
        pdb_ids = fetch_all_pdb_ids()
        if args.sample:
            pdb_ids = pdb_ids[:args.sample]
            print(f"  Sampling first {args.sample} entries")

    results = {}
    for name in datasets_to_run:
        filename, func, needs_pdb_ids = DATASETS[name]
        output_path = os.path.join(args.output_dir, filename)

        if not _should_download(output_path, args.force):
            results[name] = -1  # skipped
            continue

        if needs_pdb_ids:
            results[name] = func(pdb_ids, output_path, args.batch_size)
        elif name == "pfam":
            results[name] = func(output_path)
        elif name == "clusters":
            results[name] = func(output_path)

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    for name in datasets_to_run:
        filename = DATASETS[name][0]
        count = results.get(name, 0)
        status = "SKIPPED" if count == -1 else f"{count:>10,} rows"
        print(f"  {filename:35s} {status}")
    print(f"  Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
