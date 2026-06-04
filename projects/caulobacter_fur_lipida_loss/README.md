# Caulobacter Fur–Lipid A Loss

## Research Question
Why does inactivation of *fur* (the ferric uptake regulator) permit the loss of lipid A in *Caulobacter crescentus*, when no equivalent connection to Fur or iron homeostasis is reported in the other three Gram-negative species known to tolerate lipid A loss (*N. meningitidis*, *A. baumannii*, *M. catarrhalis*)?

## Status
Analysis — report drafted, awaiting `/submit` review. All 7 analysis notebooks (NB00–NB07) executed; H1–H4 + comparative-species arm covered. See [REPORT.md](REPORT.md). Primary BERDL data sources: `kescience_fitnessbrowser` (198 Caulobacter RB-TnSeq experiments) and `kescience_paperblast` (cross-species presence/absence + SigU literature scout).

## Overview
Lipid A is an essential component of the outer membrane in nearly all Gram-negative bacteria. *Caulobacter crescentus* can survive complete loss of lipid A only when *fur* is also inactivated. The published mechanism (Zik et al. 2022, PMID 35649364) shows the rescue requires anionic sphingolipids (CPG) and a Δ*sspB* co-deletion. This project characterizes the *regulatory and proteomic architecture* of that rescue using RNA-seq + OM proteome of the rescued and intermediate strains, BERDL Caulobacter RB-TnSeq fitness data (198 experiments), a re-analysis of Leaden 2018 (SRP136695) for a clean Fur-only signature, and a cross-species comparative arm covering the three other Gram-negative species known to tolerate lipid A loss (*N. meningitidis*, *A. baumannii*, *M. catarrhalis*). Four hypotheses are tested — see [RESEARCH_PLAN.md](RESEARCH_PLAN.md).

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — *TBD: written at the end of Phase A.*
- [Report](REPORT.md) — *TBD: written after analysis.*
- [User Data](user_data/kr_caulobacter_envelope) — symlink to the experimental dataset

## Reproduction

### Environment

- **BERDL JupyterHub on-cluster** (validated). Off-cluster execution requires the `--berdl-proxy` chain; not validated for this project.
- Python ≥3.13 with `berdl_notebook_utils` (BERDL kernel default), `pandas ≥2.0`, `numpy`, `scipy`, `seaborn`, `matplotlib`, `openpyxl`, `pypdf`, `nbformat`.
- BERDL access tokens for `kescience_fitnessbrowser` (NB02) and `kescience_paperblast` (NB03, NB06).

### External inputs (user-provided)

- `~/data/kr-caulobacter-envelope/clean/*.csv` — pre-cleaned RNA-seq + OM proteome (provided by K.R. Ryan lab; symlinked into `user_data/kr_caulobacter_envelope/`).
- `~/data/kr-caulobacter-envelope/raw/Table 2.XLSX` — Leaden 2018 *Frontiers in Microbiology* supplementary Table 2 (download from https://www.frontiersin.org/articles/10.3389/fmicb.2018.02014/full#supplementary-material). NB01 will fail without this file.
- `~/data/kr-caulobacter-envelope/raw/2026.04.12.717747v1.full.pdf` — Uchendu et al. 2026 bioRxiv preprint (download from https://www.biorxiv.org/content/10.1101/2026.04.12.717747v1). Used for documenting transporter gene identifiers; NB04 can run without it but the documentation would be less complete.

### Execution order

```bash
# From projects/caulobacter_fur_lipida_loss/
jupyter nbconvert --to notebook --execute --inplace notebooks/00_orientation.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/01_leaden2018_fur_signature.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/02_caulo_fitness_ranking.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/03_chvi_phase_partition_sigU.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/04_sphingolipid_lpt_panel.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/05_pg_remodeling.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/06_comparative_species.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/07_synthesis.ipynb
```

Each notebook writes derived CSVs to `data/` and PNGs to `figures/`. The `data/` directory contents are excluded from git by the repo's `.gitignore` (notebook outputs are the canonical source); they regenerate from the notebook on each execution. Figures and notebook outputs ARE committed.

### Known reproduction caveats

- NB06 PaperBLAST queries can return slightly different counts between runs as the underlying database is updated. The presence/absence pattern (1000 for sphingolipid genes etc.) is stable.
- NB02 requires the `kescience_fitnessbrowser` orgId=`Caulo` data set with the schema documented in `docs/pitfalls.md` (`fit` and `t` columns are STRING-typed and must be cast).
- The planned NCBI BLAST fallback for NB06 has not yet been executed; the analytical fallback rests on independent literature (see REPORT.md Limitations).

## Authors
- Adam Arkin (University of California, Berkeley) — ORCID [0000-0002-4999-2931](https://orcid.org/0000-0002-4999-2931)
