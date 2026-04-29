"""
Audit dossier completeness across the training set.

For each of the 8 evidence layers, count how many of the 2,962 unique
training-set genes have:
  - present (non-empty / non-trivial data for this layer)
  - missing  (no data — could be expected for orphans, but should not
              be widespread for non-orphan genes)
  - degenerate (data exists but flags an extraction problem, e.g. zero
                fitness in a gene labeled in_specificphenotype=1)

Reports per-layer coverage rates plus cross-layer correlation diagnostics
(e.g. "N genes have ZERO of the sequence-based hits — possible extraction
problem").
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
TRAINING = PROJECT_DATA / "training_set"

LAYERS = [
    "Existing annotation",
    "Primary fitness/cofit",
    "Secondary flags",
    "Phenotypes with conditions",
    "Top cofit partners",
    "Genomic neighborhood",
    "SwissProt hit",
    "Domain hits",
    "KEGG KO",
    "SEED descriptions",
    "PaperBLAST",
]


def parse(md: str) -> dict:
    info = {}
    info["has_existing_anno"] = bool(re.search(r"\*\*Existing annotation\*\*:\s*`[^`]*`\s*—", md))
    m = re.search(r"\*\*Existing annotation\*\*:\s*`[^`]*`\s*—\s*\*([^*]+)\*", md)
    info["existing_desc"] = m.group(1).strip() if m else ""
    info["existing_blank"] = info["existing_desc"] in ("", "(blank)")

    info["has_primary"] = bool(re.search(r"\*\*Primary fitness/cofit\*\*:", md))
    fit_m = re.search(r"max\|fit\|=([0-9.]+)", md)
    t_m = re.search(r"max\|t\|=([0-9.]+)", md)
    info["max_fit"] = float(fit_m.group(1)) if fit_m else 0.0
    info["max_t"] = float(t_m.group(1)) if t_m else 0.0

    info["has_secondary_flags"] = bool(re.search(r"\*\*Secondary flags\*\*:", md))

    pheno_section = re.search(r"\*\*Phenotypes with conditions\*\*[^*]*?\n((?:\s+- .+\n)+)", md)
    info["phenotype_count"] = len(re.findall(r"^\s+- ", pheno_section.group(1), re.M)) if pheno_section else 0

    cofit_section = re.search(r"\*\*Top cofit partners\*\*:?\n((?:\s+- .+\n)*)", md)
    info["cofit_count"] = len(re.findall(r"^\s+- ", cofit_section.group(1), re.M)) if cofit_section else 0

    neigh_section = re.search(r"\*\*Genomic neighborhood[^*]*?\*\*[^*]*?\n((?:\s+- offset .+\n)+)", md)
    info["neighbor_count"] = len(re.findall(r"^\s+- offset", neigh_section.group(1), re.M)) if neigh_section else 0

    info["has_swissprot"] = bool(re.search(r"\*\*SwissProt hit\*\*:", md)) and not bool(re.search(r"\*\*SwissProt hit\*\*: \(none", md))
    info["has_domain"] = bool(re.search(r"\*\*Domain hits\*\*", md)) and not bool(re.search(r"\*\*Domain hits\*\* \(top by score\):\n[^-]*\(none", md))
    info["domain_count"] = len(re.findall(r"^\s+- (PFam|TIGRFam) ", md, re.M))
    info["has_kegg"] = bool(re.search(r"\*\*KEGG KO\*\*:", md)) and not bool(re.search(r"\*\*KEGG KO\*\*: \(none", md))
    info["has_seed"] = bool(re.search(r"\*\*SEED descriptions\*\*", md)) and not bool(re.search(r"\*\*SEED descriptions\*\*:\n[^-]*\(none", md))

    info["has_paperblast"] = bool(re.search(r"\*\*PaperBLAST", md))
    pb_m = re.search(r"\*\*PaperBLAST \(DIAMOND\)\*\*: (\d+) homologs, (\d+) papers", md)
    info["pb_homologs"] = int(pb_m.group(1)) if pb_m else 0
    info["pb_papers"] = int(pb_m.group(2)) if pb_m else 0

    return info


def main() -> None:
    seen: dict = {}
    for fname in ("human_validated.jsonl", "negatives.jsonl", "positives.jsonl"):
        with open(TRAINING / fname) as fh:
            for line in fh:
                r = json.loads(line)
                k = (r["orgId"], r["locusId"])
                if k in seen:
                    continue
                d = parse(r.get("dossier_md", ""))
                d["_source"] = fname.replace(".jsonl", "")
                seen[k] = d
    n = len(seen)
    print(f"Audited {n:,} unique genes\n", file=sys.stderr)

    layers_check = [
        ("L1 Existing annotation",   "has_existing_anno"),
        ("L2 Primary fitness/cofit", "has_primary"),
        ("   ↳ Secondary flags",      "has_secondary_flags"),
        ("L3 Phenotype conditions",   "phenotype_count"),
        ("L4 Cofit partners",         "cofit_count"),
        ("L5 Genomic neighborhood",   "neighbor_count"),
        ("L6a SwissProt hit",         "has_swissprot"),
        ("L6b Domain hits",           "has_domain"),
        ("L6c KEGG KO",               "has_kegg"),
        ("L6d SEED descriptions",     "has_seed"),
        ("L8 PaperBLAST",             "has_paperblast"),
    ]
    print(f"{'Layer':<32}{'Present':>10}{'Empty':>10}{'%':>8}", file=sys.stderr)
    for label, key in layers_check:
        if key.endswith("_count"):
            present = sum(1 for d in seen.values() if d[key] > 0)
        else:
            present = sum(1 for d in seen.values() if d.get(key))
        missing = n - present
        pct = 100 * present / n
        print(f"  {label:<30}{present:>10,}{missing:>10,}{pct:>7.1f}%", file=sys.stderr)

    # Distributions for count-based layers
    print(f"\nLayer count distributions:", file=sys.stderr)
    for label, key in [("Phenotypes (top-10 cap)", "phenotype_count"),
                       ("Cofit partners (top-10)", "cofit_count"),
                       ("Neighborhood (±5 max 10)", "neighbor_count"),
                       ("Domain hits (top-5)",      "domain_count"),
                       ("PaperBLAST homologs",      "pb_homologs"),
                       ("PaperBLAST papers",        "pb_papers")]:
        c = Counter(min(d[key], 10) for d in seen.values())
        # Print as small histogram
        line = f"  {label:<28} "
        for v in range(0, 11):
            line += f"{v}={c.get(v,0):<5} "
        print(line, file=sys.stderr)

    # Cross-layer diagnostics
    print(f"\nCross-layer diagnostics:", file=sys.stderr)
    no_seq_evidence = sum(1 for d in seen.values()
                          if not d["has_swissprot"] and not d["has_domain"]
                          and not d["has_kegg"] and not d["has_seed"])
    print(f"  Genes with ZERO sequence-based evidence (no SwissProt/Domain/KEGG/SEED): {no_seq_evidence:,}  ({100*no_seq_evidence/n:.1f}%)", file=sys.stderr)
    no_phenotype = sum(1 for d in seen.values() if d["phenotype_count"] == 0)
    print(f"  Genes with ZERO phenotype condition rows:                                {no_phenotype:,}  ({100*no_phenotype/n:.1f}%)", file=sys.stderr)
    weak_fitness = sum(1 for d in seen.values() if d["max_fit"] < 0.5)
    print(f"  Genes with max|fit|<0.5 (essentially no fitness signal):                 {weak_fitness:,}  ({100*weak_fitness/n:.1f}%)", file=sys.stderr)
    blank_anno = sum(1 for d in seen.values() if d["existing_blank"])
    print(f"  Genes with blank existing annotation:                                    {blank_anno:,}  ({100*blank_anno/n:.1f}%)", file=sys.stderr)
    no_neighbors = sum(1 for d in seen.values() if d["neighbor_count"] == 0)
    print(f"  Genes with ZERO neighborhood entries:                                    {no_neighbors:,}  ({100*no_neighbors/n:.1f}%)", file=sys.stderr)
    no_paperblast = sum(1 for d in seen.values() if not d["has_paperblast"])
    print(f"  Genes with NO PaperBLAST section at all:                                 {no_paperblast:,}  ({100*no_paperblast/n:.1f}%)", file=sys.stderr)


if __name__ == "__main__":
    main()
