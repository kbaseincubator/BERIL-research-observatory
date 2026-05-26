#!/usr/bin/env python3
"""Parse the raw ENIGMA publications markdown table into a clean CSV."""

import csv
import re
import sys

INPUT = "data/enigma_publications_raw.md"
OUTPUT = "data/enigma_papers.csv"

rows = []
with open(INPUT) as f:
    for line in f:
        line = line.strip()
        if not line.startswith("|") or line.startswith("| Authors") or line.startswith("|---"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 4:
            continue
        authors, year, title, journal, *rest = parts + [""] * 5
        notes = rest[0] if rest else ""

        # Skip rows where year is not a 4-digit number
        year_clean = re.search(r"\b(20\d\d|19\d\d)\b", year)
        if not year_clean:
            continue
        year_val = year_clean.group(1)

        # Extract DOI if embedded in journal field
        doi_match = re.search(r"\[DOI\]:(\S+)", journal) or re.search(r"doi[:\s]+(\S+)", journal, re.I)
        doi = doi_match.group(1).strip(".") if doi_match else ""

        # Extract PMID if present
        pmid_match = re.search(r"\{PMID\}:(\d+)", journal) or re.search(r"PMID:?\s*(\d+)", journal, re.I)
        pmid = pmid_match.group(1) if pmid_match else ""

        # Clean journal: strip trailing DOI/OSTI/PMID noise
        journal_clean = re.split(r"\[DOI\]|\{PMID\}|OSTI:|PMCID:", journal)[0].strip().rstrip(".")

        rows.append({
            "authors": authors,
            "year": year_val,
            "title": title,
            "journal": journal_clean,
            "doi": doi,
            "pmid": pmid,
            "notes": notes,
        })

with open(OUTPUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["authors", "year", "title", "journal", "doi", "pmid", "notes"])
    w.writeheader()
    w.writerows(rows)

print(f"Wrote {len(rows)} papers to {OUTPUT}")

# Year distribution
from collections import Counter
years = Counter(r["year"] for r in rows)
for y in sorted(years):
    print(f"  {y}: {years[y]}")
