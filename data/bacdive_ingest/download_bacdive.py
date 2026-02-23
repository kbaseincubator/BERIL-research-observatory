#!/usr/bin/env python3
"""
Download the full BacDive database via the REST API.

Iterates BacDive IDs in batches of 100, saves raw JSON per batch.
No authentication needed (v2 API). Estimated: ~2,000 calls for ~100K strains.

Usage:
    python download_bacdive.py [--start START_ID] [--end END_ID] [--batch-size 100]
"""

import argparse
import json
import os
import sys
import time
import requests

API_BASE = "https://api.bacdive.dsmz.de/v2"
RAW_DIR = os.path.join(os.path.dirname(__file__), "raw")
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "download_progress.json")


def fetch_batch(ids: list[int], session: requests.Session) -> dict:
    """Fetch a batch of BacDive IDs. Returns {id: record} dict."""
    id_str = ";".join(str(i) for i in ids)
    url = f"{API_BASE}/fetch/{id_str}"
    resp = session.get(url, timeout=60)
    if resp.status_code == 404:
        return {}
    resp.raise_for_status()
    data = resp.json()
    # API returns {"count": N, "results": {id_str: record, ...}} for batch queries
    results = {}
    if "results" in data and isinstance(data["results"], dict):
        for id_str, record in data["results"].items():
            if isinstance(record, dict):
                results[int(id_str)] = record
    elif data.get("count", 0) == 1 and "General" in data:
        # Single result - record is the top-level dict
        bid = data.get("General", {}).get("BacDive-ID")
        if bid:
            results[bid] = data
    return results


def save_progress(last_id: int, total_strains: int):
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"last_id": last_id, "total_strains": total_strains,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}, f)


def load_progress() -> tuple[int, int]:
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            data = json.load(f)
        return data["last_id"], data["total_strains"]
    return 0, 0


def main():
    parser = argparse.ArgumentParser(description="Download BacDive database")
    parser.add_argument("--start", type=int, default=None, help="Start ID (default: resume from last)")
    parser.add_argument("--end", type=int, default=210000, help="End ID (default: 210000)")
    parser.add_argument("--batch-size", type=int, default=100, help="IDs per API call")
    parser.add_argument("--sleep", type=float, default=0.3, help="Seconds between API calls")
    args = parser.parse_args()

    os.makedirs(RAW_DIR, exist_ok=True)

    # Resume from last progress
    last_id, total_strains = load_progress()
    start_id = args.start if args.start is not None else last_id + 1
    end_id = args.end

    print(f"BacDive download: IDs {start_id} to {end_id}, batch size {args.batch_size}")
    print(f"Resuming with {total_strains} strains already downloaded")

    session = requests.Session()
    batch_num = 0
    empty_streak = 0

    for batch_start in range(start_id, end_id + 1, args.batch_size):
        batch_ids = list(range(batch_start, min(batch_start + args.batch_size, end_id + 1)))
        batch_num += 1

        try:
            results = fetch_batch(batch_ids, session)
        except requests.exceptions.RequestException as e:
            print(f"  ERROR at batch {batch_start}: {e}. Retrying in 5s...")
            time.sleep(5)
            try:
                results = fetch_batch(batch_ids, session)
            except requests.exceptions.RequestException as e2:
                print(f"  RETRY FAILED: {e2}. Skipping batch.")
                continue

        if results:
            # Save batch
            out_file = os.path.join(RAW_DIR, f"batch_{batch_start:06d}.json")
            with open(out_file, "w") as f:
                json.dump(results, f)
            total_strains += len(results)
            empty_streak = 0
        else:
            empty_streak += 1

        # Progress
        if batch_num % 20 == 0 or results:
            pct = (batch_start - start_id) / max(end_id - start_id, 1) * 100
            print(f"  ID {batch_start:>6d} ({pct:5.1f}%) — {len(results):>3d} strains this batch, {total_strains:>6d} total")
            save_progress(batch_start + args.batch_size - 1, total_strains)

        # Early stop if we've hit a long stretch of empty IDs
        if empty_streak > 100:
            print(f"  100 consecutive empty batches at ID {batch_start}. Stopping.")
            break

        time.sleep(args.sleep)

    save_progress(end_id, total_strains)
    print(f"\nDone! Downloaded {total_strains} strains to {RAW_DIR}/")
    print(f"Raw files: {len(os.listdir(RAW_DIR))} batch files")


if __name__ == "__main__":
    main()
