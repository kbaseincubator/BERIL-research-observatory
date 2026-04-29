"""
Setup for chasing the 57 missing papers in target_gene_paperblast_summaries.tsv.

For each missing pmid:
  - Categorize: pmc_no_tsv / pmc_tsv_partial / no_pmc_no_abs / no_pmc_abs_*
  - Delete partial/empty TSVs so the runners will re-attempt
  - Build a fallback fetcher list for no-PMC + no-abstract papers
"""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"

TARGET_TSV = PROJECT_DATA / "training_set" / "target_gene_paperblast_summaries.tsv"
GAPFILL_DIR = PROJECT_DATA / "codex_summaries_gapfill"
ABSTRACTS_DIR = PROJECT_DATA / "codex_summaries_abstracts"
ALT_DIR = PROJECT_DATA / "codex_summaries_altsource"
ALT_DIR.mkdir(exist_ok=True)


def main() -> None:
    # 1. Identify missing pmids
    missing = set()
    with open(TARGET_TSV) as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for r in reader:
            if r["summary_status"] == "missing":
                pmid = r["paperblast_manuscript_id"]
                if pmid and pmid != "None":
                    missing.add(pmid)
    print(f"Unique missing pmids (excluding 'None'): {len(missing)}", file=sys.stderr)

    # 2. PMC availability
    pmc_yes = set()
    with open(GAPFILL_DIR / "pmc_index.tsv") as fh:
        next(fh)
        for line in fh:
            parts = line.strip().split("\t")
            if len(parts) >= 3 and parts[2] == "1":
                pmc_yes.add(parts[0])

    abs_yes = set()
    if (ABSTRACTS_DIR / "abstract_index.tsv").exists():
        with open(ABSTRACTS_DIR / "abstract_index.tsv") as fh:
            next(fh)
            for line in fh:
                parts = line.strip().split("\t")
                if len(parts) >= 2 and parts[1] == "1":
                    abs_yes.add(parts[0])

    # 3. Categorize + force re-run for partial PMC TSVs
    have_pmc = sorted(missing & pmc_yes)
    have_abs_only = sorted(missing & abs_yes - pmc_yes)
    no_text = sorted(missing - pmc_yes - abs_yes)

    print(f"  have PMC (re-run gapfill):              {len(have_pmc)}", file=sys.stderr)
    print(f"  have abstract only (re-run abstract):   {len(have_abs_only)}", file=sys.stderr)
    print(f"  no PMC, no abstract (need alt source):  {len(no_text)}", file=sys.stderr)

    # Force re-run by deleting any existing partial TSVs in gapfill
    n_deleted_gapfill = 0
    for pmid in have_pmc:
        tsv = GAPFILL_DIR / "per_paper" / f"{pmid}.tsv"
        if tsv.exists():
            tsv.unlink()
            n_deleted_gapfill += 1
    print(f"  deleted {n_deleted_gapfill} partial gapfill TSVs to force re-run", file=sys.stderr)

    # Force re-run for abstract-only
    n_deleted_abs = 0
    for pmid in have_abs_only:
        tsv = ABSTRACTS_DIR / "per_paper" / f"{pmid}.tsv"
        if tsv.exists():
            tsv.unlink()
            n_deleted_abs += 1
    print(f"  deleted {n_deleted_abs} partial abstract TSVs to force re-run", file=sys.stderr)

    # 4. For no-PMC + no-abstract: build a tasks.jsonl in altsource dir
    # Pull task records (with gene_identifiers, title, etc.) from gapfill tasks
    altsource_tasks = []
    with open(GAPFILL_DIR / "tasks.jsonl") as fh:
        for line in fh:
            t = json.loads(line)
            if t["pmId"] in no_text:
                altsource_tasks.append(t)

    altsource_tasks_path = ALT_DIR / "tasks.jsonl"
    with open(altsource_tasks_path, "w") as fh:
        for t in altsource_tasks:
            fh.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(f"  wrote {len(altsource_tasks)} no-text tasks to {altsource_tasks_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
