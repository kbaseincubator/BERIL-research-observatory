"""
NB02 — Walk the priority queue top-down, classify each gene against the
secondary evidence, stop when the recalcitrant count reaches 2,000.

Three outcomes per visited gene:
  - already_named_well : existing annotation is already concrete
                         (named_enzyme / named_other) — curators justifiably
                         left it alone; not a reannotation candidate
  - improvable         : poor existing annotation (hypothetical / DUF / vague)
                         AND BERDL-native evidence supports a concrete proposal
                         (≥1 functional signal AND ≥1 conservation/literature signal)
  - recalcitrant       : poor existing annotation AND insufficient secondary
                         evidence to propose a meaningful new annotation —
                         these are the project's "answer" set.

Stop rule: recalcitrant tally == 2,000.

Outputs:
  - data/walk_log.parquet     one row per visited gene, with the
                              classification, signals fired, and rank/score
  - data/improvable.parquet   subset of walk_log (improvable)
  - data/recalcitrant.parquet subset of walk_log (recalcitrant) — exactly 2,000
                              rows when the target is reached
  - data/dossiers/improvable_top100.md, recalcitrant_top100.md
                              human-readable dossier renders for the first
                              100 of each bucket
"""
import json
import sys
import time
from pathlib import Path

import pandas as pd

# Allow `import dossier` from the same directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

import dossier as dossier_mod  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
DOSSIER_DIR = PROJECT_DATA / "dossiers"
DOSSIER_DIR.mkdir(parents=True, exist_ok=True)

TARGET_RECALCITRANT = 2_000
DUMP_TOP_N_DOSSIERS = 100

ALREADY_NAMED_CATEGORIES = {"named_enzyme", "named_other"}


def has_functional_evidence(d: dict) -> tuple[bool, list[str]]:
    fired = []
    sf = d.get("secondary_flags", {})
    if sf.get("informative_domain"):
        fired.append("informative_domain")
    if sf.get("informative_kegg_ko"):
        fired.append("informative_kegg_ko")
    if sf.get("informative_kegg_ec"):
        fired.append("informative_kegg_ec")
    if sf.get("informative_seed"):
        fired.append("informative_seed")
    sw = d.get("swissprot")
    if sw and sw.get("identity") and sw["identity"] >= 40:
        fired.append(f"swissprot_id_{sw['identity']}%")
    return (len(fired) > 0), fired


def has_corroboration(d: dict) -> tuple[bool, list[str]]:
    fired = []
    sf = d.get("secondary_flags", {})
    if sf.get("conserved_cofit"):
        fired.append("conserved_cofit")
    if sf.get("conserved_spec_phenotype"):
        fired.append("conserved_spec_phenotype")
    pb1 = d.get("paperblast_stage1")
    if pb1 and pb1.get("n_papers") and pb1["n_papers"] >= 1:
        fired.append(f"paperblast_swissprot_{pb1['n_papers']}p")
    pb2 = d.get("paperblast_stage2")
    if pb2 and pb2.get("n_papers") and pb2["n_papers"] >= 3:
        fired.append(f"paperblast_diamond_{pb2['n_papers']}p")
    return (len(fired) > 0), fired


def classify(d: dict) -> dict:
    cat = d["annotation"]["category"]
    if cat in ALREADY_NAMED_CATEGORIES:
        return {
            "outcome": "already_named_well",
            "category": cat,
            "functional_evidence": [],
            "corroboration": [],
            "rule": f"existing annotation already concrete (category={cat})",
        }
    has_func, func_signals = has_functional_evidence(d)
    has_corr, corr_signals = has_corroboration(d)
    if has_func and has_corr:
        return {
            "outcome": "improvable",
            "category": cat,
            "functional_evidence": func_signals,
            "corroboration": corr_signals,
            "rule": ">=1 functional + >=1 corroboration",
        }
    return {
        "outcome": "recalcitrant",
        "category": cat,
        "functional_evidence": func_signals,
        "corroboration": corr_signals,
        "rule": ("missing functional evidence" if not has_func
                 else "missing corroboration"),
    }


def main() -> None:
    t0 = time.time()
    ev = dossier_mod.load_evidence()
    queue = ev["queue"].reset_index(drop=True).sort_values("rank")
    print(f"[{time.time()-t0:5.1f}s] Priority queue: {len(queue):,} non-reannotated genes")

    log_rows = []
    counts = {"already_named_well": 0, "improvable": 0, "recalcitrant": 0}
    improvable_dossiers = []
    recalcitrant_dossiers = []

    last_status = 0
    for _, row in queue.iterrows():
        d = dossier_mod.build_dossier(row["orgId"], row["locusId"])
        verdict = classify(d)
        log_rows.append({
            "rank": int(row["rank"]),
            "score": float(row["score"]),
            "orgId": row["orgId"],
            "locusId": row["locusId"],
            "outcome": verdict["outcome"],
            "category": verdict["category"],
            "n_functional": len(verdict["functional_evidence"]),
            "n_corroboration": len(verdict["corroboration"]),
            "functional_evidence": ",".join(verdict["functional_evidence"]),
            "corroboration": ",".join(verdict["corroboration"]),
            "rule": verdict["rule"],
            "max_abs_fit": d["primary"]["max_abs_fit"],
            "max_cofit": d["primary"]["max_cofit"],
            "gene_desc": d["annotation"]["gene_desc"],
        })
        counts[verdict["outcome"]] += 1

        if verdict["outcome"] == "improvable" and len(improvable_dossiers) < DUMP_TOP_N_DOSSIERS:
            improvable_dossiers.append((row["orgId"], row["locusId"], dossier_mod.dossier_to_markdown(d)))
        elif verdict["outcome"] == "recalcitrant" and len(recalcitrant_dossiers) < DUMP_TOP_N_DOSSIERS:
            recalcitrant_dossiers.append((row["orgId"], row["locusId"], dossier_mod.dossier_to_markdown(d)))

        if len(log_rows) - last_status >= 1000:
            last_status = len(log_rows)
            print(f"[{time.time()-t0:5.1f}s] visited={len(log_rows):,} "
                  f"named_well={counts['already_named_well']:,} "
                  f"improvable={counts['improvable']:,} "
                  f"recalcitrant={counts['recalcitrant']:,}")

        if counts["recalcitrant"] >= TARGET_RECALCITRANT:
            print(f"[{time.time()-t0:5.1f}s] STOP — recalcitrant count = "
                  f"{counts['recalcitrant']} at rank {row['rank']}")
            break

    log_df = pd.DataFrame(log_rows)
    print(f"\nWalk summary:")
    print(f"  Visited:           {len(log_df):,}")
    print(f"  already_named_well:{counts['already_named_well']:,}")
    print(f"  improvable:        {counts['improvable']:,}")
    print(f"  recalcitrant:      {counts['recalcitrant']:,}")
    print(f"  Stopping rank:     {int(log_df['rank'].iloc[-1]):,}")

    log_df.to_parquet(PROJECT_DATA / "walk_log.parquet", index=False)
    log_df[log_df.outcome == "improvable"].to_parquet(PROJECT_DATA / "improvable.parquet", index=False)
    log_df[log_df.outcome == "recalcitrant"].to_parquet(PROJECT_DATA / "recalcitrant.parquet", index=False)

    def write_dossier_file(name: str, dossiers: list) -> None:
        path = DOSSIER_DIR / f"{name}_top{len(dossiers)}.md"
        with open(path, "w") as fh:
            fh.write(f"# {name.title()} — top {len(dossiers)} dossiers (priority order)\n\n")
            for org, loc, md in dossiers:
                fh.write(md + "\n\n---\n\n")
        print(f"Wrote {path}  ({len(dossiers)} dossiers)")

    write_dossier_file("improvable", improvable_dossiers)
    write_dossier_file("recalcitrant", recalcitrant_dossiers)

    print("\nOutcome × annotation category:")
    pivot = (log_df.groupby(["outcome", "category"]).size()
             .unstack(fill_value=0))
    print(pivot)


if __name__ == "__main__":
    main()
