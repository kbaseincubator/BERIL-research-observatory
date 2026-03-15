#!/usr/bin/env python3
"""
Probe the InterProScan pre-calculated match lookup service for all
unmatched pangenome cluster reps.

Two-phase approach for 94M sequences:
  Phase 1 (extract): Compute MD5 hashes via Spark → local TSV (~3 GB)
  Phase 2 (probe):   Query EBI lookup API from the MD5 file, high concurrency

Usage:
  # Phase 1: Extract MD5s for all unmatched clusters
  python 06_probe_lookup_service.py extract

  # Phase 2: Probe the lookup service (resumable, default 25 workers)
  python 06_probe_lookup_service.py probe --concurrency 25

  # Check progress
  python 06_probe_lookup_service.py status

  # Quick test with 10K sample
  python 06_probe_lookup_service.py probe --sample 10000
"""

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent
PROBE_DIR = DATA_DIR / "lookup_probe"

LOOKUP_URL = "http://www.ebi.ac.uk/interpro/match-lookup"

# Files
MD5_FILE = PROBE_DIR / "unmatched_md5s.tsv"       # Phase 1 output
RESULTS_FILE = PROBE_DIR / "lookup_results.tsv"    # Phase 2 output
PROGRESS_FILE = PROBE_DIR / "progress.json"        # Phase 2 checkpoint

REQUEST_TIMEOUT = 30
RETRY_MAX = 3
RETRY_BACKOFF = 2

# Write results every N sequences
FLUSH_INTERVAL = 500
# Print progress every N sequences
REPORT_INTERVAL = 5000

IPR = "kescience_interpro"
PAN = "kbase_ke_pangenome"


def md5_sequence(seq: str) -> str:
    """MD5 of amino acid sequence (InterPro convention: upper, no trailing *)."""
    cleaned = seq.strip().upper().rstrip("*")
    return hashlib.md5(cleaned.encode("utf-8")).hexdigest().upper()


def query_lookup(session: requests.Session, md5: str) -> tuple[bool, int, str]:
    """
    Query EBI lookup for one MD5.
    Returns (hit, n_matches, error_or_empty).
    """
    url = f"{LOOKUP_URL}/matches?md5={md5}"
    for attempt in range(RETRY_MAX):
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                content = resp.text
                if "<hit>" in content:
                    return (True, content.count("<hit>"), "")
                return (False, 0, "")
            elif resp.status_code in (204, 404):
                return (False, 0, "")
            else:
                if attempt < RETRY_MAX - 1:
                    time.sleep(RETRY_BACKOFF * (2 ** attempt))
                    continue
                return (False, 0, f"HTTP {resp.status_code}")
        except requests.RequestException as e:
            if attempt < RETRY_MAX - 1:
                time.sleep(RETRY_BACKOFF * (2 ** attempt))
                continue
            return (False, 0, str(e))
    return (False, 0, "max retries")


# ── Phase 1: Extract ────────────────────────────────────────────────

def cmd_extract(args):
    """Extract MD5 hashes for all unmatched cluster reps via Spark."""
    from berdl_notebook_utils.setup_spark_session import get_spark_session

    PROBE_DIR.mkdir(parents=True, exist_ok=True)

    if MD5_FILE.exists() and not args.force:
        n_lines = sum(1 for _ in open(MD5_FILE)) - 1  # subtract header
        print(f"MD5 file already exists: {MD5_FILE} ({n_lines:,} entries)")
        print("Use --force to regenerate.")
        return

    print("Connecting to Spark...")
    spark = get_spark_session()

    print("Computing MD5s for unmatched cluster reps (this takes ~10-20 min)...")
    print("  Query: gene_cluster LEFT JOIN protein2ipr → keep NULLs")

    # Compute MD5 directly in Spark SQL — much faster than pulling sequences
    df = spark.sql(f"""
        SELECT
            gc.gene_cluster_id,
            UPPER(MD5(UPPER(RTRIM('*', RTRIM(gc.faa_sequence))))) AS seq_md5,
            LENGTH(RTRIM('*', RTRIM(gc.faa_sequence))) AS seq_len
        FROM {PAN}.gene_cluster gc
        JOIN {PAN}.bakta_annotations ba
          ON gc.gene_cluster_id = ba.gene_cluster_id
        LEFT JOIN (
            SELECT DISTINCT uniprot_acc FROM {IPR}.protein2ipr
        ) ip100
          ON REPLACE(ba.uniref100, 'UniRef100_', '') = ip100.uniprot_acc
        LEFT JOIN (
            SELECT DISTINCT uniprot_acc FROM {IPR}.protein2ipr
        ) ip50
          ON REPLACE(ba.uniref50, 'UniRef50_', '') = ip50.uniprot_acc
        WHERE ip100.uniprot_acc IS NULL
          AND ip50.uniprot_acc IS NULL
          AND gc.faa_sequence IS NOT NULL
          AND gc.faa_sequence <> ''
    """)

    # Write to S3 as CSV (avoids driver maxResultSize limit)
    s3_path = "s3a://cdm-lake/tenant-general-warehouse/kescience/datasets/interpro/unmatched_md5s"
    print(f"  Writing MD5s to S3: {s3_path}")
    t0 = time.time()

    # Coalesce to fewer partitions for manageable output files
    df.coalesce(16).write.mode("overwrite").option("header", "true").csv(s3_path)

    n_written = spark.read.option("header", "true").csv(s3_path).count()
    spark.stop()

    write_elapsed = time.time() - t0
    print(f"  Wrote {n_written:,} rows to S3 in {write_elapsed:.0f}s")

    # Download from S3 to local
    print("  Downloading from S3 to local...")
    _download_md5s_from_s3(s3_path, n_written)

    elapsed = time.time() - t0
    size_mb = MD5_FILE.stat().st_size / 1e6
    print(f"\nExtraction complete:")
    print(f"  {n_written:,} unmatched clusters → {MD5_FILE}")
    print(f"  File size: {size_mb:.0f} MB")
    print(f"  Time: {elapsed:.0f}s ({elapsed/60:.1f} min)")


def _download_md5s_from_s3(s3_path: str, expected_rows: int):
    """Download CSV part files from S3 and merge into a single local TSV."""
    from berdl_notebook_utils.berdl_settings import get_settings
    from berdl_notebook_utils.minio_governance import get_minio_credentials
    from minio import Minio

    settings = get_settings()
    creds = get_minio_credentials()
    endpoint = settings.MINIO_ENDPOINT_URL.replace("https://", "").replace("http://", "")
    client = Minio(
        endpoint=endpoint,
        access_key=creds.access_key,
        secret_key=creds.secret_key,
        secure=True,
    )

    # Parse bucket and prefix from s3a:// path
    path = s3_path.replace("s3a://", "")
    bucket = path.split("/")[0]
    prefix = "/".join(path.split("/")[1:])

    # List part files
    objects = list(client.list_objects(bucket, prefix=prefix + "/", recursive=True))
    part_files = [o for o in objects if o.object_name.endswith(".csv")]
    print(f"    Found {len(part_files)} part files on S3")

    # Download and merge
    tmp_file = PROBE_DIR / "unmatched_md5s.tsv.tmp"
    n_rows = 0
    with open(tmp_file, "w") as out:
        out.write("gene_cluster_id\tseq_md5\tseq_len\n")
        for pf in sorted(part_files, key=lambda o: o.object_name):
            resp = client.get_object(bucket, pf.object_name)
            first_line = True
            for line in resp.read().decode().splitlines():
                if first_line:
                    first_line = False  # skip CSV header from each part
                    continue
                if line.strip():
                    # CSV → TSV conversion
                    parts = line.split(",")
                    out.write("\t".join(parts) + "\n")
                    n_rows += 1
            resp.close()

    tmp_file.rename(MD5_FILE)
    print(f"    Merged {n_rows:,} rows into {MD5_FILE}")


# ── Phase 2: Probe ──────────────────────────────────────────────────

def load_progress() -> dict:
    """Load probe progress."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"lines_done": 0, "hits": 0, "misses": 0, "errors": 0}


def save_progress(prog: dict):
    """Save probe progress."""
    with open(PROGRESS_FILE, "w") as f:
        json.dump(prog, f)


def cmd_probe(args):
    """Probe the EBI lookup service using the extracted MD5 file."""
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    concurrency = args.concurrency

    # Handle --sample mode: extract a small sample directly
    if args.sample:
        return cmd_probe_sample(args.sample, concurrency)

    if not MD5_FILE.exists():
        print(f"MD5 file not found: {MD5_FILE}")
        print("Run 'extract' first.")
        sys.exit(1)

    # Count total lines
    total_lines = sum(1 for _ in open(MD5_FILE)) - 1  # subtract header
    print(f"MD5 file: {total_lines:,} entries")

    # Load progress
    prog = load_progress()
    start_line = prog["lines_done"]
    if start_line > 0:
        print(f"Resuming from line {start_line:,} ({start_line/total_lines*100:.1f}% done)")
        print(f"  Previous: {prog['hits']:,} hits, {prog['misses']:,} misses, {prog['errors']:,} errors")

    # Test connectivity
    session = requests.Session()
    session.headers.update({"Accept": "application/xml"})
    try:
        resp = session.get(f"{LOOKUP_URL}/version", timeout=10)
        print(f"EBI lookup service: HTTP {resp.status_code} — {resp.text.strip()}")
    except Exception as e:
        print(f"ERROR: Cannot reach lookup service: {e}")
        sys.exit(1)

    print(f"Starting probe with {concurrency} concurrent workers...")
    t0 = time.time()

    # Open results file for appending
    results_mode = "a" if start_line > 0 and RESULTS_FILE.exists() else "w"
    results_f = open(RESULTS_FILE, results_mode, newline="")
    writer = csv.writer(results_f, delimiter="\t")
    if results_mode == "w":
        writer.writerow(["gene_cluster_id", "seq_md5", "hit", "n_matches", "error"])

    hits = prog["hits"]
    misses = prog["misses"]
    errors = prog["errors"]
    lines_done = start_line
    batch_start = time.time()

    with open(MD5_FILE) as f:
        reader = csv.DictReader(f, delimiter="\t")

        # Skip already-done lines
        for _ in range(start_line):
            next(reader, None)

        # Process in batches using thread pool
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            # Submit work in windows to control memory
            WINDOW = concurrency * 20  # keep ~20 requests queued per worker
            window_entries = []
            futures = {}

            for row in reader:
                gcid = row["gene_cluster_id"]
                md5 = row["seq_md5"]

                future = executor.submit(query_lookup, session, md5)
                futures[future] = (gcid, md5)

                if len(futures) >= WINDOW:
                    # Drain completed futures
                    _drain_futures(futures, writer, prog, results_f)
                    lines_done = prog["lines_done"]
                    hits = prog["hits"]
                    misses = prog["misses"]
                    errors = prog["errors"]

                    if lines_done % REPORT_INTERVAL < WINDOW:
                        elapsed = time.time() - t0
                        recent_rate = REPORT_INTERVAL / (time.time() - batch_start) if time.time() > batch_start else 0
                        total_rate = (lines_done - start_line) / elapsed if elapsed > 0 else 0
                        pct = lines_done / total_lines * 100
                        hit_rate = hits / lines_done * 100 if lines_done > 0 else 0
                        eta_h = (total_lines - lines_done) / total_rate / 3600 if total_rate > 0 else 0
                        print(f"  {lines_done:>12,}/{total_lines:,} ({pct:.1f}%) | "
                              f"rate: {recent_rate:.0f}/s (avg {total_rate:.0f}/s) | "
                              f"hits: {hit_rate:.1f}% | "
                              f"ETA: {eta_h:.1f}h | "
                              f"errors: {errors}")
                        batch_start = time.time()

            # Drain remaining
            if futures:
                _drain_futures(futures, writer, prog, results_f)

    results_f.close()
    elapsed = time.time() - t0

    # Final save
    save_progress(prog)

    lines_done = prog["lines_done"]
    hits = prog["hits"]
    misses = prog["misses"]
    errors = prog["errors"]

    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min, {elapsed/3600:.1f}h)")
    total_rate = (lines_done - start_line) / elapsed if elapsed > 0 else 0
    print(f"Throughput: {total_rate:.0f} sequences/second")
    _print_report(prog, total_lines)


def _drain_futures(futures, writer, prog, results_f):
    """Drain all completed futures, write results, update progress."""
    done_futures = []
    for future in as_completed(futures):
        gcid, md5 = futures[future]
        hit, n_matches, error = future.result()
        writer.writerow([gcid, md5, hit, n_matches, error])

        if hit:
            prog["hits"] += 1
        elif error:
            prog["errors"] += 1
        else:
            prog["misses"] += 1
        prog["lines_done"] += 1
        done_futures.append(future)

    for f in done_futures:
        del futures[f]

    results_f.flush()
    save_progress(prog)


def cmd_probe_sample(n_sample, concurrency):
    """Quick sample probe — extracts sequences from Spark inline."""
    from berdl_notebook_utils.setup_spark_session import get_spark_session

    print(f"Extracting {n_sample:,} unmatched sequences from Spark...")
    spark = get_spark_session()
    rows = spark.sql(f"""
        SELECT gc.gene_cluster_id, gc.faa_sequence
        FROM {PAN}.gene_cluster gc
        JOIN {PAN}.bakta_annotations ba
          ON gc.gene_cluster_id = ba.gene_cluster_id
        LEFT JOIN (SELECT DISTINCT uniprot_acc FROM {IPR}.protein2ipr) ip100
          ON REPLACE(ba.uniref100, 'UniRef100_', '') = ip100.uniprot_acc
        LEFT JOIN (SELECT DISTINCT uniprot_acc FROM {IPR}.protein2ipr) ip50
          ON REPLACE(ba.uniref50, 'UniRef50_', '') = ip50.uniprot_acc
        WHERE ip100.uniprot_acc IS NULL AND ip50.uniprot_acc IS NULL
          AND gc.faa_sequence IS NOT NULL AND gc.faa_sequence <> ''
        LIMIT {n_sample}
    """).collect()
    spark.stop()
    print(f"  Got {len(rows):,} sequences")

    session = requests.Session()
    session.headers.update({"Accept": "application/xml"})
    resp = session.get(f"{LOOKUP_URL}/version", timeout=10)
    print(f"EBI lookup: {resp.text.strip()}")

    hits = misses = errors = 0
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_map = {}
        for row in rows:
            md5 = md5_sequence(row["faa_sequence"])
            future = executor.submit(query_lookup, session, md5)
            future_map[future] = row["gene_cluster_id"]

        for i, future in enumerate(as_completed(future_map)):
            hit, n_matches, error = future.result()
            if hit:
                hits += 1
            elif error:
                errors += 1
            else:
                misses += 1
            if (i + 1) % 1000 == 0:
                print(f"  {i+1:,} done, hit rate: {hits/(i+1)*100:.1f}%")

    elapsed = time.time() - t0
    total = hits + misses + errors
    print(f"\nSample of {total:,} in {elapsed:.0f}s ({total/elapsed:.0f}/s)")
    print(f"  Hits:   {hits:>8,} ({hits/total*100:.1f}%)")
    print(f"  Misses: {misses:>8,} ({misses/total*100:.1f}%)")
    print(f"  Errors: {errors:>8,}")

    full_n = 94_039_704
    print(f"\n  Extrapolation to {full_n:,}:")
    print(f"    Cache hits:  {int(full_n * hits/total):>12,}")
    print(f"    Need IPS:    {int(full_n * misses/total):>12,}")


# ── Status ───────────────────────────────────────────────────────────

def cmd_status(args):
    """Show current progress."""
    if not PROGRESS_FILE.exists():
        print("No probe in progress. Run 'extract' then 'probe'.")
        return

    prog = load_progress()
    total_lines = 0
    if MD5_FILE.exists():
        total_lines = sum(1 for _ in open(MD5_FILE)) - 1

    _print_report(prog, total_lines)


def _print_report(prog, total_lines):
    """Print summary."""
    done = prog["lines_done"]
    hits = prog["hits"]
    misses = prog["misses"]
    errors = prog["errors"]

    print()
    print("=" * 60)
    print("LOOKUP PROBE STATUS")
    print("=" * 60)
    if total_lines:
        print(f"  Progress:      {done:>12,} / {total_lines:,} ({done/total_lines*100:.1f}%)")
    else:
        print(f"  Lines done:    {done:>12,}")
    print(f"  Cache hits:    {hits:>12,} ({hits/done*100:.1f}%)" if done else "")
    print(f"  Cache misses:  {misses:>12,} ({misses/done*100:.1f}%)" if done else "")
    print(f"  Errors:        {errors:>12,}" if done else "")

    if done > 0 and total_lines > 0:
        full_n = total_lines
        est_hits = int(full_n * hits / done)
        est_miss = full_n - est_hits
        print()
        print(f"  --- Projected final ({full_n:,} total) ---")
        print(f"  Projected hits:    {est_hits:>12,} ({est_hits/full_n*100:.1f}%)")
        print(f"  Projected misses:  {est_miss:>12,} ({est_miss/full_n*100:.1f}%)")

    if RESULTS_FILE.exists():
        size_mb = RESULTS_FILE.stat().st_size / 1e6
        print(f"\n  Results: {RESULTS_FILE} ({size_mb:.0f} MB)")


# ── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Probe InterProScan lookup service for unmatched pangenome clusters")
    sub = parser.add_subparsers(dest="command")

    # extract
    p_ext = sub.add_parser("extract", help="Phase 1: Extract MD5s via Spark")
    p_ext.add_argument("--force", action="store_true", help="Overwrite existing MD5 file")

    # probe
    p_probe = sub.add_parser("probe", help="Phase 2: Query EBI lookup service")
    p_probe.add_argument("--concurrency", type=int, default=25,
                         help="Concurrent API requests (default: 25)")
    p_probe.add_argument("--sample", type=int, metavar="N",
                         help="Quick sample of N sequences (skips extract)")

    # status
    sub.add_parser("status", help="Show current progress")

    args = parser.parse_args()
    PROBE_DIR.mkdir(parents=True, exist_ok=True)

    if args.command == "extract":
        cmd_extract(args)
    elif args.command == "probe":
        cmd_probe(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
