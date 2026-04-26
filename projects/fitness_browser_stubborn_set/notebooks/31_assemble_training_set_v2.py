"""
Assemble the v2 distributable training set for the gene-function annotation
agent. Produces a self-contained data/training_set/ directory:

  data/training_set/
    README.md
    negatives.jsonl                      —   755  (Claude ∩ Codex agree recalcitrant)
    positives.jsonl                      —   445  (Claude ∩ Codex agree already_correctly_named)
    human_validated.jsonl                — 1,762  (Price-lab curator-validated names + rationale)
    llm_vs_human_disagreements.jsonl     —   868  (subset where Claude said original was fine
                                                   or recalcitrant, but the human curator
                                                   went deeper)

All four files carry the full 8-layer dossier markdown so the consumer has
the input the labels were derived from. For the human-curated files, the
dossier uses the **pre-curation** gene description (BERDL gene.desc on the
1,662 clean rows; "uncharacterized protein" placeholder on the 100 rows
where BERDL had been updated to the curator's name) — same contamination
control used in the calibration run.
"""
from __future__ import annotations

import csv
import glob
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
NB_DIR = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "notebooks"
sys.path.insert(0, str(NB_DIR))
import dossier as dossier_mod  # noqa: E402

OUT_DIR = PROJECT_DATA / "training_set"
NEG_IN = PROJECT_DATA / "training_recalcitrant_final.jsonl"
POS_IN = PROJECT_DATA / "training_positive_final.jsonl"
STRAT = PROJECT_DATA / "negatives_stratified.tsv"
REANN = PROJECT_DATA / "reannotation_set.parquet"
CAL = PROJECT_DATA / "reann_calibration.tsv"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in open(path)]


def load_dossier_md(orgId: str, locusId: str, desc_override: str | None = None) -> str:
    try:
        d = dossier_mod.build_dossier(orgId, locusId, desc_override=desc_override)
        return dossier_mod.dossier_to_markdown(d)
    except Exception as e:
        return f"<dossier build failed: {e}>"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # === 1. Negatives ===
    print("Building negatives.jsonl ...", file=sys.stderr)
    strat = {}
    with open(STRAT) as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            strat[(r["orgId"], r["locusId"])] = {
                "evidence_tier": r["evidence_tier"],
                "strong_phenotype": int(r["strong_phenotype"]),
                "max_abs_fit": float(r["max_abs_fit"]),
                "max_abs_t": float(r["max_abs_t"]),
                "n_paperblast_hits": int(r["n_paperblast_hits"]),
                "n_papers_with_summaries": int(r["n_papers_with_summaries"]),
            }
    n_neg = 0
    with open(NEG_IN) as fh, open(OUT_DIR / "negatives.jsonl", "w") as out:
        for line in fh:
            r = json.loads(line)
            r.update(strat.get((r["orgId"], r["locusId"]), {}))
            r["dossier_md"] = load_dossier_md(r["orgId"], r["locusId"])
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
            n_neg += 1
    print(f"  wrote {n_neg} negative rows", file=sys.stderr)

    # === 2. Positives ===
    print("Building positives.jsonl ...", file=sys.stderr)
    n_pos = 0
    with open(POS_IN) as fh, open(OUT_DIR / "positives.jsonl", "w") as out:
        for line in fh:
            r = json.loads(line)
            r["dossier_md"] = load_dossier_md(r["orgId"], r["locusId"])
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
            n_pos += 1
    print(f"  wrote {n_pos} positive rows", file=sys.stderr)

    # === 3. Human validated (1,762) ===
    # Combine BERDL reannotation pull + manifests (for desc_for_dossier) + LLM outputs.
    print("Building human_validated.jsonl ...", file=sys.stderr)
    reann = pd.read_parquet(REANN).dropna(subset=["orgId", "locusId"]).reset_index(drop=True)
    reann_lookup = {(r["orgId"], r["locusId"]): r for _, r in reann.iterrows()}

    manifest_lookup = {}
    for mp in sorted((PROJECT_DATA / "batches_reann").glob("batch_RA*/manifest.csv")):
        m = pd.read_csv(mp, dtype={"orgId": str, "locusId": str})
        for _, mr in m.iterrows():
            manifest_lookup[(mr["orgId"], mr["locusId"])] = {
                "desc_for_dossier": mr.get("desc_for_dossier") or "",
                "desc_source": mr.get("desc_source") or "",
                "current_gene_desc_in_berdl": mr.get("current_gene_desc_in_berdl") or "",
            }

    # LLM outputs from calibration TSV
    cal = pd.read_csv(CAL, sep="\t").fillna("")
    cal_lookup = {(r["orgId"], r["locusId"]): r for _, r in cal.iterrows()}

    n_hv = 0
    n_dis = 0
    with open(OUT_DIR / "human_validated.jsonl", "w") as out, \
         open(OUT_DIR / "llm_vs_human_disagreements.jsonl", "w") as dis:
        for k, hr in reann_lookup.items():
            m = manifest_lookup.get(k, {})
            c = cal_lookup.get(k)
            desc = m.get("desc_for_dossier") or m.get("current_gene_desc_in_berdl") or ""
            row = {
                "orgId": k[0],
                "locusId": k[1],
                "original_description": desc,
                "desc_source": m.get("desc_source") or "berdl_clean",
                "human_annotation": hr.get("new_annotation") or "",
                "human_comment": (hr.get("comment") or "").replace("\r", " "),
                "human_category": c["human_category"] if c is not None else "",
                "claude_verdict": c["claude_verdict"] if c is not None else "",
                "claude_proposal": c["claude_proposal"] if c is not None else "",
                "claude_confidence": c["claude_confidence"] if c is not None else "",
                "claude_class": c["claude_class"] if c is not None else "",
                "codex_verdict": c["codex_verdict"] if c is not None else "",
                "codex_proposal": c["codex_proposal"] if c is not None else "",
                "codex_confidence": c["codex_confidence"] if c is not None else "",
                "codex_class": c["codex_class"] if c is not None else "",
                "dossier_md": load_dossier_md(k[0], k[1], desc_override=desc or None),
            }
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            n_hv += 1
            # Disagreement set: Claude said original was fine OR Claude gave up,
            # but human went deeper.
            if c is not None and c["claude_class"] in ("false_positive_named", "false_negative"):
                drow = dict(row)
                drow["disagreement_type"] = c["claude_class"]
                drow["both_llms_disagreed"] = int(
                    c["codex_class"] in ("false_positive_named", "false_negative")
                )
                dis.write(json.dumps(drow, ensure_ascii=False) + "\n")
                n_dis += 1

    print(f"  wrote {n_hv} human_validated rows", file=sys.stderr)
    print(f"  wrote {n_dis} llm_vs_human_disagreements rows", file=sys.stderr)


if __name__ == "__main__":
    main()
