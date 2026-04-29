"""
Build a target-gene-aware paperblast-summary TSV in the format the
gene-annotation-agent already consumes. One row per
(target_gene, paperblast_homolog, paper) triple, with the per-(homolog,
paper) summary text inlined.

This collapses the runtime join the agent would otherwise need to do across:
  - data/fb_paperblast_hit_papers.parquet      (target → homolog → paper)
  - data/manuscript-summaries-merged.tsv       (homolog × paper → summary)
  - data/reannotation_set.parquet              (target → human annotation)
  - data/gene_evidence_features.parquet        (target → original desc)
  - data/fitness_browser/fb_aaseqs_all.fasta   (target → protein sequence)

Output:
  data/training_set/target_gene_paperblast_summaries.tsv

Schema:
  benchmark_index            ordinal across the file
  orgId                      FB organism ID
  locusId                    FB locus ID
  source_file                which training_set file the target gene appears in
                             (one of: human_validated, llm_vs_human_disagreements,
                              negatives, positives; ; -separated when the gene is in
                              multiple files — disagreements is always also in
                              human_validated)
  reannotation               curator's annotation (human_validated only; "" for others)
  original_desc              pre-curation gene_desc shown in the dossier
  aaseq                      target protein sequence
  paperblast_target_id       PaperBLAST homolog identifier (= geneId / sseqid)
  paperblast_query_term      FB target (orgId::locusId) — the query for the BLAST
  paperblast_manuscript_id   PMID of the cited paper
  source_type                "pubmed" (constant for this corpus)
  paperblast_organism        organism of the homolog
  paperblast_homolog_desc    PaperBLAST description of the homolog
  pident                     % identity
  evalue                     BLAST e-value
  qcovhsp                    query coverage of HSP
  scovhsp                    subject coverage of HSP
  paper_title                title of the paper
  paper_year                 publication year
  paper_journal              journal name
  summary                    per-(homolog, paper) summary text (null if missing)
  summary_status             "homolog_match" / "paper_only" / "missing"
                             — homolog_match: summary is for THIS homolog × THIS paper
                             — paper_only:    we have a summary of this paper, but
                                              for a different homolog (paper context only)
                             — missing:       no summary for this paper anywhere
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
SUMMARIES = PROJECT_DATA / "manuscript-summaries-merged.tsv"
FEATURES = PROJECT_DATA / "gene_evidence_features.parquet"
REANN = PROJECT_DATA / "reannotation_set.parquet"
ORG_NAMES = PROJECT_DATA / "fb_organism_names.tsv"
AASEQ_FASTA = REPO_ROOT / "data" / "fitness_browser" / "fb_aaseqs_all.fasta"
TRAINING_SET = PROJECT_DATA / "training_set"

OUT = TRAINING_SET / "target_gene_paperblast_summaries.tsv"


def load_aaseqs(path: Path) -> dict[tuple[str, str], str]:
    """Parse FB FASTA. Headers are like '>orgId:locusId description'."""
    if not path.exists():
        print(f"  aaseq fasta missing at {path}, aaseq column will be empty", file=sys.stderr)
        return {}
    aaseqs: dict[tuple[str, str], str] = {}
    cur_key = None
    cur_buf: list[str] = []
    with open(path) as fh:
        for line in fh:
            line = line.rstrip()
            if line.startswith(">"):
                if cur_key is not None:
                    aaseqs[cur_key] = "".join(cur_buf)
                head = line[1:].split()[0]
                if ":" in head:
                    org, loc = head.split(":", 1)
                    cur_key = (org, loc)
                else:
                    cur_key = None
                cur_buf = []
            elif cur_key is not None:
                cur_buf.append(line)
        if cur_key is not None:
            aaseqs[cur_key] = "".join(cur_buf)
    print(f"  loaded {len(aaseqs):,} aaseqs", file=sys.stderr)
    return aaseqs


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
        label = fname.replace(".jsonl", "")
        if not path.exists():
            continue
        with open(path) as fh:
            for line in fh:
                r = json.loads(line)
                k = (r["orgId"], r["locusId"])
                file_membership.setdefault(k, []).append(label)
    print(f"Target genes across training files: {len(file_membership):,}", file=sys.stderr)

    # 2. Per-target lookups
    print("Loading metadata...", file=sys.stderr)
    feat = pd.read_parquet(FEATURES)[["orgId", "locusId", "gene_desc"]]
    feat_lookup = {(r["orgId"], r["locusId"]): r["gene_desc"] for _, r in feat.iterrows()}

    reann = pd.read_parquet(REANN)
    reann_lookup = {(r["orgId"], r["locusId"]): r for _, r in reann.iterrows()}

    aaseqs = load_aaseqs(AASEQ_FASTA)

    org_name_lookup: dict[str, str] = {}
    if ORG_NAMES.exists():
        with open(ORG_NAMES) as fh:
            next(fh)
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 2:
                    org_name_lookup[parts[0]] = parts[1]
        print(f"  loaded {len(org_name_lookup)} orgId→organism names", file=sys.stderr)

    # 3. Pre-curation desc per gene (matches what the dossier shows)
    desc_for_target: dict[tuple[str, str], str] = {}
    for k in file_membership:
        if k in reann_lookup:
            cur = reann_lookup[k].get("current_gene_desc_in_berdl") or ""
            new_ann = reann_lookup[k].get("new_annotation") or ""
            # If BERDL gene.desc was updated to the curator's name, fall back to
            # placeholder (matches the contamination-controlled training set).
            if cur.strip().lower() == new_ann.strip().lower():
                desc_for_target[k] = "uncharacterized protein"
            else:
                desc_for_target[k] = cur
        else:
            desc_for_target[k] = feat_lookup.get(k) or ""

    # 4. Load merged summaries — keyed by (gene_identifier, manuscript_id)
    print("Loading merged summaries...", file=sys.stderr)
    summary_by_pair: dict[tuple[str, str], str] = {}
    summary_by_pmid: dict[str, str] = {}  # any summary for this paper, for fallback
    with open(SUMMARIES) as fh:
        next(fh)
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            mid, _, gid = parts[0], parts[1], parts[2]
            summ = "\t".join(parts[3:])
            if summ.strip().lower() in ("null", ""):
                continue
            summary_by_pair[(gid, mid)] = summ
            if mid not in summary_by_pmid:
                summary_by_pmid[mid] = summ

    # 5. PaperBLAST hits restricted to training-set targets
    print("Loading PaperBLAST hits...", file=sys.stderr)
    hits = pd.read_parquet(HITS)
    hits["pmId"] = hits["pmId"].astype(str)
    target_set = set(file_membership.keys())
    sub = hits[hits.apply(lambda r: (r["orgId"], r["locusId"]) in target_set, axis=1)].copy()
    print(f"  PaperBLAST hits joined to training set: {len(sub):,}", file=sys.stderr)

    # 6. Write
    print("Writing TSV...", file=sys.stderr)
    n_hm = n_paper = n_miss = 0
    with open(OUT, "w", newline="") as out:
        w = csv.writer(out, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        w.writerow([
            "benchmark_index", "orgId", "locusId", "organism", "source_file",
            "reannotation", "original_desc", "aaseq",
            "paperblast_target_id", "paperblast_query_term",
            "paperblast_manuscript_id", "source_type",
            "paperblast_organism", "paperblast_homolog_desc",
            "pident", "evalue", "qcovhsp", "scovhsp",
            "paper_title", "paper_year", "paper_journal",
            "summary", "summary_status",
        ])
        idx = 0
        for _, r in sub.iterrows():
            k = (r["orgId"], r["locusId"])
            gid = r["geneId"]
            pmid = str(r["pmId"])
            pair_summ = summary_by_pair.get((gid, pmid))
            paper_summ = summary_by_pmid.get(pmid)
            if pair_summ is not None:
                summary = pair_summ
                status = "homolog_match"
                n_hm += 1
            elif paper_summ is not None:
                summary = paper_summ
                status = "paper_only"
                n_paper += 1
            else:
                summary = ""
                status = "missing"
                n_miss += 1

            human_ann = ""
            if k in reann_lookup:
                human_ann = (reann_lookup[k].get("new_annotation") or "")

            w.writerow([
                idx, r["orgId"], r["locusId"],
                org_name_lookup.get(r["orgId"], ""),
                ";".join(file_membership.get(k, [])),
                human_ann,
                desc_for_target.get(k, ""),
                aaseqs.get(k, ""),
                gid,
                f"{r['orgId']}::{r['locusId']}",
                pmid,
                "pubmed",
                r.get("pb_organism") or "",
                r.get("pb_desc") or "",
                r["pident"], r["evalue"], r["qcovhsp"], r["scovhsp"],
                r.get("title") or "",
                int(r["year"]) if pd.notna(r.get("year")) else "",
                r.get("journal") or "",
                summary,
                status,
            ])
            idx += 1

    n_total = n_hm + n_paper + n_miss
    print(f"\nWrote {OUT}", file=sys.stderr)
    print(f"  total rows:                 {n_total:,}", file=sys.stderr)
    print(f"  homolog_match (best):       {n_hm:,}  ({100*n_hm/n_total:.1f}%)", file=sys.stderr)
    print(f"  paper_only (paper context): {n_paper:,}  ({100*n_paper/n_total:.1f}%)", file=sys.stderr)
    print(f"  missing (title only):       {n_miss:,}  ({100*n_miss/n_total:.1f}%)", file=sys.stderr)


if __name__ == "__main__":
    main()
