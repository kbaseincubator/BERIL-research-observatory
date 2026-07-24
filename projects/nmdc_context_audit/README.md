# NMDC Context Audit

## Research Question
Across the BERDL lakehouse, the label "NMDC" is attached to tenants, databases, and
tables whose provenance, depth, breadth, completeness, and added value vary widely.
Does this labeling confuse BERIL users about what each resource actually contains — and
can a linked knowledge base clarify the context so users select the optimal NMDC data
earlier in their sessions (stronger conclusions, less time, less cost)?

## Status
Completed — one "NMDC" label spans three tenants and six provenance classes (genuine NMDC, re-hosted NCBI/Pfam, Arkin-lab derivation, NEON namesake), with scale 10¹–10⁹ rows and currency days–months, none of it surfaced at discovery; captured as a 15-file knowledge base plus docs/tooling recommendations.

## Data Collections
Audited collections: `nmdc_metadata`, `nmdc_results`, `nmdc_ncbi_biosamples`,
`nmdc_ref_data`, `kbase_nmdc_arkin`, `kbase_nmdc_mags`, `kbase_nmdc_neon`.

## Overview
An audit of every "NMDC"-labeled resource in BERDL: which are genuinely National
Microbiome Data Collaborative outputs vs. external data (NCBI, NEON, Pfam) or
other-group derivations (e.g. Arkin lab); where NMDC data is duplicated across tenants;
whether each copy is complete and current; and what value BERDL has added over
upstream NMDC. Findings are captured as a directory of Open-Knowledge-Format markdown
files (`knowledge/`) — YAML front matter, descriptive filenames, and cross-links — plus
recommendations to improve the static docs and dynamic discovery tooling.

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, audit strategy
- [Report](REPORT.md) — findings, interpretation, and recommendations
- [Knowledge base](knowledge/README.md) — 15-file Open-Knowledge-Format context directory (primary deliverable)

## Reproduction

Prerequisites: on-cluster BERDL JupyterHub (or off-cluster with `.venv-berdl` + proxy),
read access to the `nmdc` and `kbase` tenants, `KBASE_AUTH_TOKEN` in `.env`.

1. **Enumerate every NMDC-labeled database and its tables:**
   ```bash
   python projects/nmdc_context_audit/data/probe_identifiers.py
   ```
2. **Characterize provenance, scale, and currency** (row counts + Iceberg snapshot ages):
   ```bash
   python projects/nmdc_context_audit/data/probe_provenance.py 2>/dev/null
   # writes projects/nmdc_context_audit/data/provenance_probe.md (next to the script,
   # regardless of the directory you run it from)
   ```
3. **Regenerate the landscape table and figures** from the notebook:
   ```bash
   cd projects/nmdc_context_audit/notebooks
   jupyter nbconvert --to notebook --execute --inplace 00_nmdc_landscape.ipynb \
     --ExecutePreprocessor.timeout=600
   # writes ../data/nmdc_landscape.csv, ../data/nmdc_naming_cruft.csv,
   #        ../figures/nmdc_currency.png, ../figures/nmdc_scale.png
   ```
4. **Read the findings** in [REPORT.md](REPORT.md) and the context knowledge base at
   [knowledge/README.md](knowledge/README.md). Counts/dates are point-in-time (audited
   2026-07-10); re-running refreshes them against the live catalog.

## Authors
Mark Andrew Miller — LBL — ORCID [0000-0001-9076-6066](https://orcid.org/0000-0001-9076-6066)
