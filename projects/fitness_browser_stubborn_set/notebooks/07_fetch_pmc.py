"""
Fetch PMC full-text XML for each pmId in tasks.jsonl that has a PMC counterpart.

Steps per pmId:
  1. ID conversion via NCBI idconv to find PMCID
  2. If PMCID exists, fetch PMC XML via efetch
  3. Cache to data/codex_summaries/pmc/<pmcid>.xml
  4. Write data/codex_summaries/pmc_index.tsv: pmId, pmcId (or empty if not in PMC)

Polite: 5 concurrent workers, NCBI tool/email param, retry on 429/5xx.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

import os
REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
SUM_DIR = Path(os.environ.get("SUM_DIR", str(PROJECT_DATA / "codex_summaries")))
# pmc/ cache is shared across runs (same papers across both sets)
PMC_DIR = Path(os.environ.get("PMC_DIR", str(PROJECT_DATA / "codex_summaries" / "pmc")))
INDEX_PATH = SUM_DIR / "pmc_index.tsv"
TASKS_PATH = SUM_DIR / "tasks.jsonl"

NCBI_TOOL = "kbase-fb-stubborn"
NCBI_EMAIL = "psdehal@gmail.com"
IDCONV_URL = "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def idconv_batch(pmids: list[str]) -> dict[str, str]:
    """Convert a batch of PMIDs to PMCIDs (max 200 per call). Returns {pmid: pmcid_or_empty}."""
    out = {p: "" for p in pmids}
    for chunk_start in range(0, len(pmids), 100):
        chunk = pmids[chunk_start : chunk_start + 100]
        params = {
            "ids": ",".join(chunk),
            "format": "json",
            "tool": NCBI_TOOL,
            "email": NCBI_EMAIL,
        }
        for attempt in range(4):
            try:
                r = requests.get(IDCONV_URL, params=params, timeout=30)
                if r.status_code == 200:
                    j = r.json()
                    for rec in j.get("records", []):
                        # Response uses requested-id (string we sent); pmid field is int
                        pmid = str(rec.get("requested-id") or rec.get("pmid") or "")
                        pmcid = rec.get("pmcid", "") or ""
                        if pmid:
                            out[pmid] = pmcid
                    break
                else:
                    time.sleep(2 ** attempt)
            except Exception:
                time.sleep(2 ** attempt)
        time.sleep(0.4)  # polite
    return out


def fetch_pmc_xml(pmcid: str) -> bytes | None:
    """Fetch full PMC XML for a single PMCID. Returns bytes or None on failure."""
    pmcid_num = pmcid.replace("PMC", "")
    params = {
        "db": "pmc",
        "id": pmcid_num,
        "rettype": "full",
        "retmode": "xml",
        "tool": NCBI_TOOL,
        "email": NCBI_EMAIL,
    }
    for attempt in range(3):
        try:
            r = requests.get(EFETCH_URL, params=params, timeout=60)
            if r.status_code == 200 and len(r.content) > 200:
                return r.content
            elif r.status_code in (429, 500, 502, 503):
                time.sleep(2 ** attempt + 1)
            else:
                return None
        except Exception:
            time.sleep(2 ** attempt + 1)
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=None, help="cap papers (debug)")
    parser.add_argument("--workers", type=int, default=5)
    args = parser.parse_args()

    PMC_DIR.mkdir(parents=True, exist_ok=True)

    pmids = []
    with open(TASKS_PATH) as fh:
        for line in fh:
            r = json.loads(line)
            pmids.append(str(r["pmId"]))
    if args.max:
        pmids = pmids[: args.max]
    print(f"Total pmIds: {len(pmids)}", file=sys.stderr)

    # Resume: load existing index
    existing = {}
    if INDEX_PATH.exists():
        with open(INDEX_PATH) as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                existing[row["pmId"]] = row.get("pmcId", "")

    # Step 1: ID conversion (skip already-resolved)
    todo_idconv = [p for p in pmids if p not in existing]
    print(f"PMIDs needing idconv: {len(todo_idconv)}", file=sys.stderr)
    pmid_to_pmcid = dict(existing)
    if todo_idconv:
        result = idconv_batch(todo_idconv)
        pmid_to_pmcid.update(result)

    # Step 2: fetch PMC XML for those with a PMCID, skip if cached on disk
    pmcids_to_fetch = []
    for pmid, pmcid in pmid_to_pmcid.items():
        if not pmcid:
            continue
        xml_path = PMC_DIR / f"{pmcid}.xml"
        if xml_path.exists() and xml_path.stat().st_size > 200:
            continue
        pmcids_to_fetch.append((pmid, pmcid))
    print(f"PMC XMLs to fetch: {len(pmcids_to_fetch)}", file=sys.stderr)

    fetched = 0
    failed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fetch_pmc_xml, pmcid): (pmid, pmcid) for pmid, pmcid in pmcids_to_fetch}
        for i, fut in enumerate(as_completed(futs), 1):
            pmid, pmcid = futs[fut]
            xml = fut.result()
            if xml:
                (PMC_DIR / f"{pmcid}.xml").write_bytes(xml)
                fetched += 1
            else:
                failed += 1
            if i % 50 == 0:
                print(f"  ...fetched {fetched}, failed {failed} ({i}/{len(pmcids_to_fetch)})", file=sys.stderr)
            time.sleep(0.15)  # politeness

    # Write index
    with open(INDEX_PATH, "w") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["pmId", "pmcId", "has_xml"])
        for pmid in pmids:
            pmcid = pmid_to_pmcid.get(pmid, "")
            has = "1" if pmcid and (PMC_DIR / f"{pmcid}.xml").exists() else "0"
            w.writerow([pmid, pmcid, has])
    print(f"Wrote {INDEX_PATH}", file=sys.stderr)

    n_pmc = sum(1 for p in pmids if pmid_to_pmcid.get(p))
    n_xml = sum(1 for p in pmids if pmid_to_pmcid.get(p) and (PMC_DIR / f"{pmid_to_pmcid[p]}.xml").exists())
    print(f"Summary: {n_pmc}/{len(pmids)} have PMC IDs; {n_xml} XMLs cached", file=sys.stderr)


if __name__ == "__main__":
    main()
