"""
Finalize the v3 deliverable.

Step 1: extract per-gene augmented dossier_md from the batch input.md
files (the exact text Opus + Codex saw at classification time) and
attach to v3 JSONL rows.

Step 2: tag every row in the v1 negatives.jsonl with its v3 relabel
outcome (confirmed_stubborn | flipped_agree | inconclusive | missing)
so consumers can filter v1 to only the rows whose label survived
augmented-dossier scrutiny by capability-matched LLMs.

Inputs:
  data/relabel_negatives/batches_claude/batch_RN*/input.md
  data/expansion/batches_claude/batch_EX*/input.md
  data/relabel_negatives/relabel_results.tsv
  data/training_set/{negatives,positives}_v3.jsonl   (built by notebook 68)
  data/training_set/negatives.jsonl                  (v1)

Outputs (in place):
  data/training_set/negatives_v3.jsonl  (now with dossier_md)
  data/training_set/positives_v3.jsonl  (now with dossier_md)
  data/training_set/negatives.jsonl     (now with relabel_outcome field)
"""
from __future__ import annotations

import csv
import glob
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PD = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
TS = PD / "training_set"

RELABEL_INPUTS = PD / "relabel_negatives" / "batches_claude"
EXPANSION_INPUTS = PD / "expansion" / "batches_claude"
RELABEL_RESULTS = PD / "relabel_negatives" / "relabel_results.tsv"
NEG_V3 = TS / "negatives_v3.jsonl"
POS_V3 = TS / "positives_v3.jsonl"
NEG_V1 = TS / "negatives.jsonl"


# Regex to split an input.md into (header, body) per dossier
DOSSIER_SPLIT = re.compile(r'(^## Dossier \d+/\d+ — [^\n]+\n)', re.M)


def parse_input_md(text: str) -> dict[tuple[str, str], str]:
    """Return {(orgId, locusId): full_dossier_text_block}.

    The block includes everything from the `## Dossier ...` header up
    to (but not including) the next `---` separator (the per-gene
    delimiter the batch builder writes between dossiers)."""
    parts = DOSSIER_SPLIT.split(text)
    out: dict[tuple[str, str], str] = {}
    i = 1
    while i < len(parts) - 1:
        header = parts[i]
        body = parts[i+1]
        # Header looks like "## Dossier 3/25 — orgId::locusId\n"
        m = re.match(r'## Dossier \d+/\d+ — (\S+?)::(\S+?)\s*$', header.strip())
        if m:
            org, loc = m.group(1), m.group(2)
            # Trim body at the next `---` separator (the inter-dossier divider)
            full = header + body
            sep_idx = full.find("\n---\n")
            if sep_idx != -1:
                full = full[:sep_idx].rstrip() + "\n"
            out[(org, loc)] = full
        i += 2
    return out


def build_lookup(glob_pat: str) -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    for f in sorted(glob.glob(glob_pat)):
        text = Path(f).read_text()
        for k, v in parse_input_md(text).items():
            out[k] = v
    return out


def main() -> None:
    print("Building dossier lookup from relabel + expansion input.md files...",
          file=sys.stderr)
    lookup = {}
    relabel_lookup = build_lookup(str(RELABEL_INPUTS / "batch_RN*" / "input.md"))
    print(f"  relabel dossiers (RN batches): {len(relabel_lookup)}", file=sys.stderr)
    expansion_lookup = build_lookup(str(EXPANSION_INPUTS / "batch_EX*" / "input.md"))
    print(f"  expansion dossiers (EX batches): {len(expansion_lookup)}", file=sys.stderr)
    # Both dossiers exist for some genes (sub-batches duplicate EX070's 25);
    # prefer expansion dossier (full unified prompt, what Opus saw last)
    lookup.update(relabel_lookup)
    lookup.update(expansion_lookup)
    print(f"  combined unique dossiers: {len(lookup)}", file=sys.stderr)

    # Step 1: enrich v3 negatives + positives with dossier_md
    for path, kind in [(NEG_V3, "negatives_v3"), (POS_V3, "positives_v3")]:
        rows = []
        n_filled = n_missing = 0
        with open(path) as fh:
            for line in fh:
                r = json.loads(line)
                k = (r["orgId"], r["locusId"])
                if not r.get("dossier_md"):
                    if k in lookup:
                        r["dossier_md"] = lookup[k]
                        n_filled += 1
                    else:
                        n_missing += 1
                rows.append(r)
        with open(path, "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        print(f"\n{kind}: {len(rows)} total; filled dossier_md on {n_filled}, "
              f"{n_missing} still missing", file=sys.stderr)

    # Step 2: tag v1 negatives with relabel_outcome
    print("\nTagging v1 negatives.jsonl with relabel_outcome...", file=sys.stderr)
    relabel_cat: dict[tuple[str, str], str] = {}
    with open(RELABEL_RESULTS) as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            relabel_cat[(r["orgId"], r["locusId"])] = r["category"]
    print(f"  loaded {len(relabel_cat)} relabel outcomes", file=sys.stderr)

    rows = []
    cat_counter: dict[str, int] = {}
    with open(NEG_V1) as fh:
        for line in fh:
            r = json.loads(line)
            k = (r["orgId"], r["locusId"])
            cat = relabel_cat.get(k, "not_relabeled")
            r["relabel_outcome"] = cat
            cat_counter[cat] = cat_counter.get(cat, 0) + 1
            rows.append(r)
    with open(NEG_V1, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print(f"  v1 negatives: {len(rows)}", file=sys.stderr)
    for k, v in sorted(cat_counter.items(), key=lambda x: -x[1]):
        print(f"    {k:<22} {v:>5}", file=sys.stderr)


if __name__ == "__main__":
    main()
