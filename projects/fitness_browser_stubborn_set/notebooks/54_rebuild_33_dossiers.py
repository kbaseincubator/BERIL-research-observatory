"""
Rebuild dossier_md for the 33 reannotation-set genes that were NOT FOUND in
the original features parquet (now patched in via notebook 53/53b), and
update the corresponding rows in human_validated.jsonl and
llm_vs_human_disagreements.jsonl.

Contamination control is applied: if BERDL gene.desc equals the curator's
new_annotation for a gene, substitute "uncharacterized protein" for the
focal gene's description.
"""
from __future__ import annotations

import csv
import importlib
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
NB_DIR = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "notebooks"
sys.path.insert(0, str(NB_DIR))

# Force reload of evidence (since we just patched the parquets)
import dossier as dossier_mod  # noqa: E402
importlib.reload(dossier_mod)

REANN = PROJECT_DATA / "reannotation_set.parquet"
HV = PROJECT_DATA / "training_set" / "human_validated.jsonl"
DIS = PROJECT_DATA / "training_set" / "llm_vs_human_disagreements.jsonl"


def main() -> None:
    # 33 missing genes
    keys = []
    with open("/tmp/missing_33_genes.tsv") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            keys.append((r["orgId"], r["locusId"]))
    keys_set = set(keys)
    print(f"rebuilding dossiers for {len(keys)} genes", file=sys.stderr)

    # Pull contamination info for these 33
    reann = pd.read_parquet(REANN)
    reann_lookup = {(r["orgId"], r["locusId"]): r for _, r in reann.iterrows()}

    new_dossiers: dict[tuple[str, str], str] = {}
    n_clean = n_placeholder = 0
    for k in keys:
        cur = (reann_lookup[k].get("current_gene_desc_in_berdl") or "").strip()
        new_ann = (reann_lookup[k].get("new_annotation") or "").strip()
        if cur.lower() == new_ann.lower():
            desc_override = "uncharacterized protein"
            n_placeholder += 1
        else:
            desc_override = None  # use BERDL's current gene_desc
            n_clean += 1
        try:
            d = dossier_mod.build_dossier(k[0], k[1], desc_override=desc_override)
            md = dossier_mod.dossier_to_markdown(d)
            if "NOT FOUND" in md:
                print(f"  WARNING: {k} still NOT FOUND after patch", file=sys.stderr)
            new_dossiers[k] = md
        except Exception as e:
            print(f"  build failed for {k}: {e}", file=sys.stderr)
            new_dossiers[k] = f"<dossier build failed: {e}>"

    print(f"  desc sources: {n_clean} clean (BERDL gene.desc), {n_placeholder} placeholder", file=sys.stderr)
    print(f"  built dossiers: {sum(1 for d in new_dossiers.values() if 'NOT FOUND' not in d)}/{len(keys)}", file=sys.stderr)

    # Update both JSONL files
    for path in (HV, DIS):
        rows = []
        n_updated = 0
        with open(path) as fh:
            for line in fh:
                r = json.loads(line)
                k = (r["orgId"], r["locusId"])
                if k in keys_set and k in new_dossiers:
                    r["dossier_md"] = new_dossiers[k]
                    n_updated += 1
                rows.append(r)
        with open(path, "w") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  {path.name}: updated {n_updated} rows", file=sys.stderr)


if __name__ == "__main__":
    main()
