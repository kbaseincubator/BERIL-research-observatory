"""
Prepare classification batches for the 1,762-gene reannotation calibration set.

Contamination control: in BERDL's `gene` table, 100/1,762 reannotated genes
have `gene.desc` already updated to the curator's `new_annotation` (i.e. the
answer leaks into the dossier). Strategy:
  - clean rows (1,662): BERDL `gene.desc` is the pre-curation description.
    Validated: of 439 clean rows in both BERDL and the local FEBA 456-gene
    file, FEBA's `original_description` matches BERDL `gene.desc` 99.8% of
    the time.
  - contaminated rows (100):
      6 are in FEBA -> substitute FEBA's `original_description`.
      94 not in FEBA -> substitute generic "uncharacterized protein" so the
        leaked answer is masked. Other evidence layers (KEGG, SwissProt,
        SEED, Pfam, PaperBLAST) are sequence-derived and unaffected.

Each per-gene record records its `desc_source` so the scoring step can
optionally exclude the 94 placeholder rows from headline metrics.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
NB_DIR = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "notebooks"
sys.path.insert(0, str(NB_DIR))
import dossier as dossier_mod  # noqa: E402

REANN = PROJECT_DATA / "reannotation_set.parquet"
FEBA = REPO_ROOT / "data" / "fitness_browser" / "FEBA_anno_withrefseq.tab"
OUT_DIR = PROJECT_DATA / "batches_reann"

PLACEHOLDER_DESC = "uncharacterized protein"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=25, help="genes per batch")
    args = parser.parse_args()

    reann = pd.read_parquet(REANN).dropna(subset=["orgId", "locusId"]).reset_index(drop=True)
    print(f"Reannotation rows: {len(reann)}", file=sys.stderr)

    # FEBA fallback (456 genes from the 2018 paper TableS12)
    feba_orig: dict[tuple[str, str], str] = {}
    if FEBA.exists():
        f = pd.read_csv(FEBA, sep="\t", quoting=csv.QUOTE_NONE, dtype=str,
                        on_bad_lines="warn")
        for _, r in f.iterrows():
            feba_orig[(r["orgId"], r["locusId"])] = (r.get("original_description") or "").strip()
        print(f"FEBA fallback rows: {len(feba_orig)}", file=sys.stderr)

    # Resolve dossier desc per gene
    a = reann["current_gene_desc_in_berdl"].fillna("").str.strip()
    b = reann["new_annotation"].fillna("").str.strip()
    contaminated_mask = a.str.lower() == b.str.lower()
    print(f"Contaminated (gene.desc == new_annotation): {contaminated_mask.sum()}", file=sys.stderr)

    desc_for_dossier = []
    desc_source = []
    for i, row in reann.iterrows():
        if not contaminated_mask.iat[i]:
            desc_for_dossier.append(a.iat[i])
            desc_source.append("berdl_clean")
        else:
            k = (row["orgId"], row["locusId"])
            feba_d = feba_orig.get(k, "")
            if feba_d and feba_d.lower() != b.iat[i].lower():
                desc_for_dossier.append(feba_d)
                desc_source.append("feba_original")
            else:
                desc_for_dossier.append(PLACEHOLDER_DESC)
                desc_source.append("placeholder")
    reann = reann.assign(desc_for_dossier=desc_for_dossier, desc_source=desc_source)
    print("desc_source counts:", reann["desc_source"].value_counts().to_dict(), file=sys.stderr)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = reann.to_dict("records")
    n = args.n
    batches = (len(rows) + n - 1) // n
    for bi in range(batches):
        chunk = rows[bi * n : (bi + 1) * n]
        bid = f"RA{bi+1:03d}"
        bdir = OUT_DIR / f"batch_{bid}"
        bdir.mkdir(parents=True, exist_ok=True)
        input_path = bdir / "input.md"
        manifest_path = bdir / "manifest.csv"

        with open(input_path, "w") as fh:
            fh.write(f"# Reannotation calibration batch {bid} — {len(chunk)} dossiers\n\n")
            fh.write("> Each dossier is built with the pre-curation gene description "
                     "(BERDL `gene.desc` for the 94% clean rows; FEBA `original_description` "
                     "for 6 rows where BERDL was contaminated; `\"uncharacterized protein\"` "
                     "placeholder for 94 rows where neither pre-curation source was "
                     "available). Other evidence layers are unmodified. The curator's "
                     "`new_annotation` is held out for scoring and is NOT shown.\n\n")
            for i, r in enumerate(chunk, 1):
                orgId = r["orgId"]
                locusId = r["locusId"]
                d = dossier_mod.build_dossier(orgId, locusId, desc_override=r["desc_for_dossier"])
                fh.write(f"## Dossier {i}/{len(chunk)} — {orgId}::{locusId}\n\n")
                fh.write(dossier_mod.dossier_to_markdown(d))
                fh.write("\n\n---\n\n")

        with open(manifest_path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow([
                "orgId", "locusId", "desc_for_dossier", "desc_source",
                "human_new_annotation", "human_comment",
                "current_gene_desc_in_berdl",
            ])
            for r in chunk:
                w.writerow([
                    r["orgId"], r["locusId"],
                    r["desc_for_dossier"], r["desc_source"],
                    r.get("new_annotation") or "",
                    (r.get("comment") or "").replace("\n", " ").replace("\r", " "),
                    r.get("current_gene_desc_in_berdl") or "",
                ])

    print(f"Built {batches} batches in {OUT_DIR}", file=sys.stderr)


if __name__ == "__main__":
    main()
