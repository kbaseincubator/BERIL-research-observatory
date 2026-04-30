"""
Score the 2,000-gene Opus + Codex expansion run, then merge with the
relabeled v1 negatives to produce the v3 deliverable files:

  data/training_set/negatives_v3.jsonl
  data/training_set/positives_v3.jsonl

v3 sourcing:
  v3 confirmed-stubborn negatives = relabel-confirmed v1 stubborn (32)
                                  + expansion both-LLM agreed "recalcitrant" (stubborn-grade)
  v3 no-signal negatives          = relabel-confirmed v1 no-signal (482)
  v3 stubborn positives            = expansion both-LLM agreed "already_correctly_named"
                                      (signal_class for expansion is always "stubborn"
                                       because that's the sampling frame)

Deduplication: when EX070 (full batch) and EX070A-E (bisection sub-batches)
cover the same 25 genes, prefer the full batch verdict (most recent
unified prompt).

Inputs:
  data/expansion/batches_claude/batch_EX*/output.jsonl
  data/expansion/batches_codex/batch_EX*/output.jsonl
  data/relabel_negatives/relabel_results.tsv   (the v1 relabel outcome)
  data/training_set/negatives.jsonl            (v1 with signal_class)
  data/random_sample_genes_expansion.parquet   (expansion pool with gene_desc, fitness)
"""
from __future__ import annotations

import csv
import glob
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PD = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
TS = PD / "training_set"

EXP_OPUS = PD / "expansion" / "batches_claude"
EXP_CODEX = PD / "expansion" / "batches_codex"
EXP_POOL = PD / "random_sample_genes_expansion.parquet"
RELABEL_TSV = PD / "relabel_negatives" / "relabel_results.tsv"

OUT_NEG = TS / "negatives_v3.jsonl"
OUT_POS = TS / "positives_v3.jsonl"


def load_verdicts(glob_pat: str, prefer_full_over_sub: bool = True) -> dict:
    """Load JSONL verdicts. When same (orgId, locusId) appears in both a
    full batch (EX070) and a sub-batch (EX070A-E), keep the full-batch
    verdict (most recent unified prompt)."""
    out = {}
    seen_in_full: set[tuple[str, str]] = set()
    # First pass: full batches (EX001..EX080, no letter suffix)
    for f in sorted(glob.glob(glob_pat)):
        # batch dir name like batch_EX070 or batch_EX070A
        dir_name = Path(f).parent.name  # batch_EX070
        bid = dir_name.replace("batch_", "")
        is_sub = (len(bid) > 5) and bid[-1].isalpha()  # EX070A
        if is_sub: continue
        for line in open(f):
            line = line.strip()
            if not line: continue
            try: r = json.loads(line)
            except json.JSONDecodeError: continue
            if "orgId" in r and "locusId" in r:
                k = (r["orgId"], r["locusId"])
                out[k] = r
                seen_in_full.add(k)
    # Second pass: sub-batches, only fill what's missing
    for f in sorted(glob.glob(glob_pat)):
        dir_name = Path(f).parent.name
        bid = dir_name.replace("batch_", "")
        is_sub = (len(bid) > 5) and bid[-1].isalpha()
        if not is_sub: continue
        for line in open(f):
            line = line.strip()
            if not line: continue
            try: r = json.loads(line)
            except json.JSONDecodeError: continue
            if "orgId" in r and "locusId" in r:
                k = (r["orgId"], r["locusId"])
                if k not in out:
                    out[k] = r
    return out


def _build_dossier_lookup() -> dict:
    """Pre-build a lookup so we can attach gene_desc and dossier metadata
    to expansion verdicts without recomputing."""
    pool = pd.read_parquet(EXP_POOL)
    return {(r["orgId"], r["locusId"]): r for _, r in pool.iterrows()}


def main() -> None:
    print("loading expansion Opus verdicts...", file=sys.stderr)
    opus = load_verdicts(str(EXP_OPUS / "batch_EX*" / "output.jsonl"))
    print(f"  {len(opus)} unique (orgId, locusId) keys", file=sys.stderr)

    print("loading expansion Codex verdicts...", file=sys.stderr)
    codex = load_verdicts(str(EXP_CODEX / "batch_EX*" / "output.jsonl"))
    print(f"  {len(codex)} unique (orgId, locusId) keys", file=sys.stderr)

    pool_lookup = _build_dossier_lookup()
    print(f"  expansion pool: {len(pool_lookup)} genes", file=sys.stderr)

    # Categorize each expansion gene by both-LLM agreement
    cat_counts: Counter = Counter()
    confirmed_neg = []   # both LLMs say recalcitrant
    confirmed_pos = []   # both LLMs say already_correctly_named
    agreed_improvable = []  # both LLMs say improvable_*  (interesting but not used yet)
    inconclusive = []
    missing = []

    for k, pool_row in pool_lookup.items():
        op = opus.get(k); cx = codex.get(k)
        if op is None or cx is None:
            missing.append(k)
            cat_counts["missing"] += 1
            continue
        op_v, cx_v = op.get("verdict"), cx.get("verdict")
        if op_v == "recalcitrant" and cx_v == "recalcitrant":
            cat_counts["both_recalcitrant"] += 1
            confirmed_neg.append((k, pool_row, op, cx))
        elif op_v == "already_correctly_named" and cx_v == "already_correctly_named":
            cat_counts["both_correctly_named"] += 1
            confirmed_pos.append((k, pool_row, op, cx))
        elif op_v == cx_v and op_v in ("improvable_new", "improvable_correction"):
            cat_counts[f"both_{op_v}"] += 1
            agreed_improvable.append((k, pool_row, op, cx))
        else:
            cat_counts["inconclusive"] += 1
            inconclusive.append((k, pool_row, op, cx))

    print("\n=== expansion 2000-gene scoring ===", file=sys.stderr)
    for k, v in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {k:<26} {v:>5}", file=sys.stderr)

    # ---- Build v3 negatives ----
    # Source 1: relabel-confirmed v1 negatives (still recalcitrant under Opus + Codex on augmented dossier)
    print("\nloading relabel-confirmed v1 negatives...", file=sys.stderr)
    relabel = pd.read_csv(RELABEL_TSV, sep="\t")
    confirmed_v1 = relabel[relabel["category"] == "confirmed_stubborn"]
    print(f"  v1 confirmed: {len(confirmed_v1)}", file=sys.stderr)
    print(f"    of which signal_class=stubborn:  {(confirmed_v1['signal_class']=='stubborn').sum()}", file=sys.stderr)
    print(f"    of which signal_class=no_signal: {(confirmed_v1['signal_class']=='no_signal').sum()}", file=sys.stderr)

    # Map v1 keys to original negatives.jsonl rows so we can carry dossier_md and rationales
    print("\nloading original v1 negatives.jsonl for dossier / rationale carryover...", file=sys.stderr)
    v1_full: dict[tuple[str, str], dict] = {}
    with open(TS / "negatives.jsonl") as fh:
        for line in fh:
            r = json.loads(line)
            v1_full[(r["orgId"], r["locusId"])] = r
    print(f"  v1 full rows: {len(v1_full)}", file=sys.stderr)

    # Build v3 negatives JSONL
    n_v3_stub = n_v3_nosig = 0
    with open(OUT_NEG, "w") as fh:
        # v1-confirmed
        for _, row in confirmed_v1.iterrows():
            k = (row["orgId"], row["locusId"])
            v1 = v1_full.get(k)
            if v1 is None: continue
            entry = dict(v1)  # carry forward dossier_md, original verdict/rationale
            entry["source"] = "v1_confirmed_via_relabel"
            entry["signal_class"] = row["signal_class"]
            entry["v2_opus_verdict"] = row["opus_verdict"]
            entry["v2_codex_verdict"] = row["codex_verdict"]
            entry["v2_opus_rationale"] = ""    # rationale not loaded above; skip
            entry["v2_codex_rationale"] = ""
            fh.write(json.dumps(entry) + "\n")
            if row["signal_class"] == "stubborn": n_v3_stub += 1
            else: n_v3_nosig += 1

        # expansion-confirmed (all signal_class=stubborn by construction)
        for k, pool_row, op, cx in confirmed_neg:
            entry = {
                "orgId": k[0], "locusId": k[1],
                "gene_desc": pool_row.get("gene_desc", ""),
                "max_abs_fit": float(pool_row.get("max_abs_fit") or 0),
                "in_specificphenotype": float(pool_row.get("in_specificphenotype") or 0),
                "verdict": "recalcitrant",
                "confidence": op.get("confidence"),
                "proposed_annotation": "",
                "rationale": op.get("rationale", ""),
                "papers_consulted": op.get("papers_consulted", []),
                "codex_verdict": cx.get("verdict"),
                "codex_confidence": cx.get("confidence"),
                "codex_rationale": cx.get("rationale", ""),
                "signal_class": "stubborn",
                "source": "v3_expansion",
                # NB: dossier_md not inlined here — would require rebuilding
                # via dossier.py + augmented sections. For now downstream
                # code can rebuild it from (orgId, locusId).
                "dossier_md": "",
            }
            fh.write(json.dumps(entry) + "\n")
            n_v3_stub += 1

    print(f"\nwrote {OUT_NEG.name}", file=sys.stderr)
    print(f"  total: {n_v3_stub + n_v3_nosig}", file=sys.stderr)
    print(f"  stubborn:  {n_v3_stub}", file=sys.stderr)
    print(f"  no_signal: {n_v3_nosig}", file=sys.stderr)

    # ---- Build v3 positives ----
    n_pos = 0
    with open(OUT_POS, "w") as fh:
        for k, pool_row, op, cx in confirmed_pos:
            entry = {
                "orgId": k[0], "locusId": k[1],
                "gene_desc": pool_row.get("gene_desc", ""),
                "max_abs_fit": float(pool_row.get("max_abs_fit") or 0),
                "in_specificphenotype": float(pool_row.get("in_specificphenotype") or 0),
                "verdict": "already_correctly_named",
                "confidence": op.get("confidence"),
                "proposed_annotation": op.get("proposed_annotation", pool_row.get("gene_desc", "")),
                "rationale": op.get("rationale", ""),
                "papers_consulted": op.get("papers_consulted", []),
                "codex_verdict": cx.get("verdict"),
                "codex_confidence": cx.get("confidence"),
                "codex_rationale": cx.get("rationale", ""),
                "signal_class": "stubborn",
                "source": "v3_expansion",
                "dossier_md": "",
            }
            fh.write(json.dumps(entry) + "\n")
            n_pos += 1
    print(f"\nwrote {OUT_POS.name}", file=sys.stderr)
    print(f"  total: {n_pos} (all signal_class=stubborn)", file=sys.stderr)

    # ---- Summary ----
    print("\n=== v3 deliverable summary ===", file=sys.stderr)
    print(f"v3 negatives: {n_v3_stub + n_v3_nosig}  ({n_v3_stub} stubborn + {n_v3_nosig} no_signal)", file=sys.stderr)
    print(f"v3 positives: {n_pos}  (all stubborn)", file=sys.stderr)
    print(f"v3 stubborn-only training cohort:", file=sys.stderr)
    print(f"   negatives: {n_v3_stub}", file=sys.stderr)
    print(f"   positives: {n_pos}", file=sys.stderr)
    if missing:
        print(f"\nNOTE: {len(missing)} expansion genes lacked verdicts from one or both LLMs",
              file=sys.stderr)
    if inconclusive:
        print(f"NOTE: {len(inconclusive)} expansion genes were inconclusive (LLMs disagreed)",
              file=sys.stderr)
    if agreed_improvable:
        print(f"NOTE: {len(agreed_improvable)} expansion genes both-LLM-agreed on improvable_*",
              file=sys.stderr)
        print(f"      (could be a future positive corpus seed; not shipping in v3 by default)",
              file=sys.stderr)


if __name__ == "__main__":
    main()
