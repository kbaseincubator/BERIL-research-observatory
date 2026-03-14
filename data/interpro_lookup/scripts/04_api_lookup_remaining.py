#!/usr/bin/env python3
"""
Look up InterPro results via REST API for accessions not found in bulk data.

For proteins that weren't matched by the bulk protein2ipr.dat file, this script
queries the InterPro REST API. Designed for robustness on flaky networks:

  - Processes in configurable batch sizes
  - Checkpoints after each batch (JSON state file)
  - Fully resumable from last checkpoint
  - Exponential backoff on errors (up to 5 min wait)
  - Rate limiting (configurable, default 10 req/sec)
  - Logs all errors for debugging

Input:
  data/interpro_lookup/gene_cluster_accessions.tsv
  data/interpro_lookup/interpro_matches.tsv  (to identify already-matched)

Output:
  data/interpro_lookup/api_matches.tsv
  data/interpro_lookup/api_no_results.tsv    (accessions with no InterPro hits)

Usage:
  python data/interpro_lookup/scripts/04_api_lookup_remaining.py
  python data/interpro_lookup/scripts/04_api_lookup_remaining.py --resume
  python data/interpro_lookup/scripts/04_api_lookup_remaining.py --batch-size 500 --max-rps 5
  python data/interpro_lookup/scripts/04_api_lookup_remaining.py --limit 10000  # test run
"""

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OUT_DIR = "data/interpro_lookup"
ACCESSIONS_FILE = os.path.join(OUT_DIR, "gene_cluster_accessions.tsv")
BULK_MATCHES_FILE = os.path.join(OUT_DIR, "interpro_matches.tsv")
API_MATCHES_FILE = os.path.join(OUT_DIR, "api_matches.tsv")
API_NO_RESULTS_FILE = os.path.join(OUT_DIR, "api_no_results.tsv")
CHECKPOINT_FILE = os.path.join(OUT_DIR, "checkpoints", "api_lookup_checkpoint.json")
ERROR_LOG = os.path.join(OUT_DIR, "api_errors.log")

INTERPRO_API = "https://www.ebi.ac.uk/interpro/api"
DEFAULT_BATCH_SIZE = 200
DEFAULT_MAX_RPS = 10  # requests per second
MAX_RETRIES = 5
INITIAL_BACKOFF = 2  # seconds


def load_already_matched():
    """Load accessions already matched from bulk data."""
    matched = set()
    if os.path.exists(BULK_MATCHES_FILE):
        with open(BULK_MATCHES_FILE) as f:
            next(f)  # skip header
            for line in f:
                parts = line.split("\t")
                if len(parts) >= 3:
                    matched.add(parts[2])  # uniprot_acc column
    print(f"  Already matched (bulk): {len(matched):,} accessions")
    return matched


def load_api_completed():
    """Load accessions already processed via API (both hits and misses)."""
    completed = set()
    for filepath in [API_MATCHES_FILE, API_NO_RESULTS_FILE]:
        if os.path.exists(filepath):
            with open(filepath) as f:
                next(f)  # skip header
                for line in f:
                    parts = line.split("\t")
                    if parts:
                        completed.add(parts[0])  # accession column
    return completed


def load_remaining_accessions(already_matched):
    """Load accessions that still need API lookup."""
    acc_to_clusters = defaultdict(list)

    with open(ACCESSIONS_FILE) as f:
        header = f.readline().strip().split("\t")
        col_idx = {name: i for i, name in enumerate(header)}

        for line in f:
            parts = line.strip().split("\t")
            gc_id = parts[col_idx["gene_cluster_id"]]

            # Check each tier, collect accessions not yet matched
            for tier, col in [("uniref100", "uniref100_acc"),
                              ("uniref90", "uniref90_acc"),
                              ("uniref50", "uniref50_acc")]:
                idx = col_idx.get(col)
                if idx is not None and idx < len(parts):
                    acc = parts[idx]
                    if acc and acc != "" and acc != "None" and acc not in already_matched:
                        acc_to_clusters[acc].append((gc_id, tier))
                        break  # use best available tier only

    return acc_to_clusters


def fetch_interpro_for_accession(accession, max_retries=MAX_RETRIES):
    """Fetch InterPro entries for a UniProt accession via REST API.

    Returns list of dicts with InterPro match info, or None on permanent failure.
    Empty list means protein exists but has no InterPro matches.
    """
    url = f"{INTERPRO_API}/protein/uniprot/{accession}/entry/?format=json"

    backoff = INITIAL_BACKOFF
    for attempt in range(max_retries):
        try:
            req = Request(url, headers={"Accept": "application/json"})
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())

            results = []
            for entry in data.get("results", []):
                # Each result has metadata and protein_locations
                entry_acc = entry.get("metadata", {}).get("accession", "")
                entry_name = entry.get("metadata", {}).get("name", {})
                if isinstance(entry_name, dict):
                    entry_name = entry_name.get("name", "") or entry_name.get("short", "")
                entry_type = entry.get("metadata", {}).get("type", "")
                source_db = entry.get("metadata", {}).get("source_database", "")

                # Extract domain boundaries from protein_locations
                for protein_loc in entry.get("proteins", []):
                    for loc_group in protein_loc.get("entry_protein_locations", []):
                        for frag in loc_group.get("fragments", []):
                            results.append({
                                "ipr_id": entry_acc,
                                "ipr_desc": entry_name if isinstance(entry_name, str) else str(entry_name),
                                "ipr_type": entry_type,
                                "source_db": source_db,
                                "start": frag.get("start", ""),
                                "end": frag.get("end", ""),
                            })

                # If no protein_locations, still record the entry
                if not entry.get("proteins"):
                    results.append({
                        "ipr_id": entry_acc,
                        "ipr_desc": entry_name if isinstance(entry_name, str) else str(entry_name),
                        "ipr_type": entry_type,
                        "source_db": source_db,
                        "start": "",
                        "end": "",
                    })

            return results

        except HTTPError as e:
            if e.code == 404:
                return []  # protein not in InterPro
            if e.code == 429:  # rate limited
                retry_after = int(e.headers.get("Retry-After", backoff))
                time.sleep(retry_after)
                backoff = min(backoff * 2, 300)
                continue
            if e.code >= 500:  # server error, retry
                time.sleep(backoff)
                backoff = min(backoff * 2, 300)
                continue
            _log_error(accession, f"HTTP {e.code}: {e.reason}")
            return None

        except (URLError, TimeoutError, OSError) as e:
            # Network errors — retry with backoff
            if attempt < max_retries - 1:
                time.sleep(backoff)
                backoff = min(backoff * 2, 300)
                continue
            _log_error(accession, f"Network error after {max_retries} retries: {e}")
            return None

        except json.JSONDecodeError as e:
            _log_error(accession, f"JSON parse error: {e}")
            return None

    _log_error(accession, f"Exhausted {max_retries} retries")
    return None


def _log_error(accession, message):
    """Append error to log file."""
    with open(ERROR_LOG, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\t{accession}\t{message}\n")


def save_checkpoint(state):
    """Save checkpoint state."""
    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    # Write to temp file first, then rename (atomic)
    tmp = CHECKPOINT_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.replace(tmp, CHECKPOINT_FILE)


def load_checkpoint():
    """Load checkpoint state."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return None


def main():
    parser = argparse.ArgumentParser(description="API lookup for unmatched InterPro accessions")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE,
                        help=f"Accessions per batch (default {DEFAULT_BATCH_SIZE})")
    parser.add_argument("--max-rps", type=float, default=DEFAULT_MAX_RPS,
                        help=f"Max requests per second (default {DEFAULT_MAX_RPS})")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max accessions to process (0 = all)")
    args = parser.parse_args()

    min_interval = 1.0 / args.max_rps  # seconds between requests

    if not os.path.exists(ACCESSIONS_FILE):
        print(f"ERROR: {ACCESSIONS_FILE} not found. Run 01_extract_identifiers.py first.")
        sys.exit(1)

    # Load state
    print("Loading already-matched accessions...")
    already_matched = load_already_matched()

    print("Loading accessions needing API lookup...")
    acc_to_clusters = load_remaining_accessions(already_matched)

    # Deduplicate: get unique accessions to look up
    all_accessions = sorted(acc_to_clusters.keys())
    print(f"  Total accessions for API lookup: {len(all_accessions):,}")

    if args.limit > 0:
        all_accessions = all_accessions[:args.limit]
        print(f"  Limited to first {args.limit:,}")

    # Filter out already-completed API lookups
    if args.resume:
        completed = load_api_completed()
        all_accessions = [a for a in all_accessions if a not in completed]
        print(f"  After filtering completed: {len(all_accessions):,} remaining")

    if not all_accessions:
        print("Nothing to do — all accessions already processed.")
        return

    # Initialize output files
    for filepath, header in [
        (API_MATCHES_FILE, "accession\tgene_cluster_id\ttier\tipr_id\tipr_desc\t"
                           "ipr_type\tsource_db\tstart\tend\n"),
        (API_NO_RESULTS_FILE, "accession\tgene_cluster_ids\n"),
    ]:
        if not os.path.exists(filepath):
            with open(filepath, "w") as f:
                f.write(header)

    # Process in batches
    total = len(all_accessions)
    processed = 0
    api_hits = 0
    api_misses = 0
    api_errors = 0
    t0 = time.time()

    print(f"\nProcessing {total:,} accessions via InterPro API...")
    print(f"  Rate limit: {args.max_rps} req/sec")
    print(f"  Batch size: {args.batch_size}")

    for batch_start in range(0, total, args.batch_size):
        batch = all_accessions[batch_start:batch_start + args.batch_size]
        batch_hits = 0
        batch_misses = 0
        batch_errors = 0

        for accession in batch:
            last_request = time.time()

            results = fetch_interpro_for_accession(accession)

            if results is None:
                # Permanent error
                batch_errors += 1
            elif len(results) == 0:
                # No InterPro results
                batch_misses += 1
                gc_ids = ",".join(gc for gc, _ in acc_to_clusters[accession])
                with open(API_NO_RESULTS_FILE, "a") as f:
                    f.write(f"{accession}\t{gc_ids}\n")
            else:
                # Got results
                batch_hits += 1
                with open(API_MATCHES_FILE, "a") as f:
                    for r in results:
                        for gc_id, tier in acc_to_clusters[accession]:
                            f.write(f"{accession}\t{gc_id}\t{tier}\t"
                                    f"{r['ipr_id']}\t{r['ipr_desc']}\t"
                                    f"{r['ipr_type']}\t{r['source_db']}\t"
                                    f"{r['start']}\t{r['end']}\n")

            processed += 1

            # Rate limiting
            elapsed = time.time() - last_request
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)

        api_hits += batch_hits
        api_misses += batch_misses
        api_errors += batch_errors

        # Progress
        elapsed = time.time() - t0
        rate = processed / elapsed if elapsed > 0 else 0
        eta = (total - processed) / rate if rate > 0 else 0
        print(f"  [{processed:,}/{total:,}] hits={api_hits:,} misses={api_misses:,} "
              f"errors={api_errors:,} | {rate:.1f} acc/sec | "
              f"ETA {eta/3600:.1f}h")

        # Checkpoint
        save_checkpoint({
            "processed": processed,
            "api_hits": api_hits,
            "api_misses": api_misses,
            "api_errors": api_errors,
            "last_accession": batch[-1],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

    # Final summary
    elapsed = time.time() - t0
    print(f"\n=== API Lookup Complete ===")
    print(f"Processed: {processed:,} accessions in {elapsed/3600:.1f}h")
    print(f"  Hits:   {api_hits:,} ({api_hits/max(processed,1)*100:.1f}%)")
    print(f"  Misses: {api_misses:,} ({api_misses/max(processed,1)*100:.1f}%)")
    print(f"  Errors: {api_errors:,}")
    print(f"Output: {API_MATCHES_FILE}")

    # Clean up checkpoint on success
    if api_errors == 0 and os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)


if __name__ == "__main__":
    main()
