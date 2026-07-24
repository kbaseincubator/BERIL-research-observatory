# Research Plan: NMDC Context Audit

## Research Question
The label "NMDC" is attached to BERDL resources spanning **three tenants** and **four
provenance classes** (genuine NMDC, re-hosted external data, other-group derivations,
and namesake collisions), with row counts spanning 5 orders of magnitude and data
currency ranging from days to months old. None of this context is carried in the
lakehouse catalog (tables have no `Comment`), the static docs (broken `schemas/nmdc.md`
link; NMDC absent from `overview.md`), or the dynamic discovery tooling (zero NMDC
content in the berdl skill; inventory files `kbase.nmdc_*` under "kbase").

**Does this labeling cause BERIL users to select sub-optimal NMDC resources late in a
session — and can a linked, provenance-aware knowledge base let them choose the right
resource early, yielding stronger conclusions at lower time/compute cost?**

## Hypothesis
- **H0**: The existing "NMDC" naming and documentation are sufficient; users can already
  determine each resource's provenance, scope, completeness, currency, and added value,
  and select optimally without additional context artifacts.
- **H1**: The "NMDC" label is systematically overloaded and under-documented; a
  provenance-aware knowledge layer measurably reduces the risk of a user (a) mistaking
  re-hosted NCBI/Pfam data for NMDC outputs, (b) missing NMDC-derived data that lives in
  the `kbase` tenant, (c) conflating NEON with NMDC, or (d) relying on a stale snapshot
  unaware of its age.

*This is a knowledge-engineering audit, not a statistical test. H0/H1 are evaluated by
enumerated, evidence-backed confusion modes (below), each of which either does or does
not survive scrutiny against the live catalog.*

## Literature Context
- **NMDC** (National Microbiome Data Collaborative, microbiomedata.org) — DOE-BER program;
  authoritative source for the genuine `nmdc.metadata` / `nmdc.results` schema
  (`biosample_set`, `study_set`, `workflow_execution_set`, etc.).
- **NEON** (National Ecological Observatory Network) — a *distinct* NSF program; its
  metagenomes are re-hosted as `kbase.nmdc_neon`, creating an acronym collision.
- Prior in-repo knowledge: `docs/pitfalls.md` (`## nmdc_arkin`, `## NMDC (nmdc_arkin)
  Pitfalls`), `docs/discoveries.md:629–685`, and 10 prior projects that consumed NMDC
  data (see `knowledge/nmdc-prior-project-usage.md`). Existing docs cover `nmdc_arkin`
  well but `nmdc_metadata`, `nmdc_results`, `nmdc_ncbi_biosamples`, `nmdc_mags`,
  `nmdc_neon`, `nmdc_ref_data` thinly or not at all.

## Approach
An evidence-first audit of every "NMDC"-labeled resource, captured as a directory of
Open-Knowledge-Format (OKF) markdown files under `projects/nmdc_context_audit/knowledge/`,
followed by a `REPORT.md` recommending (but not yet applying) fixes to the static docs
and dynamic tooling.

### Provenance classification (evidence gathered in Phase A)
| Class | Resources | Scale (rows) | Last commit |
|---|---|---|---|
| Genuine NMDC | `nmdc.metadata` (16,640 biosamples / 84 studies), `nmdc.results` (1.83B KEGG rows) | 10^1–10^9 | 2026-05-20 |
| External, re-hosted under `nmdc` tenant | `nmdc.ncbi_biosamples` (51.7M biosamples, 756M attrs), `nmdc.ref_data` (Pfam, 27k) | 10^4–10^8 | 2026-03-09 / 05-20 |
| NMDC-related, in `kbase` tenant | `kbase.nmdc_mags` (62k MAGs), `kbase.nmdc_arkin` (Arkin-lab embeddings/traits) | 10^3–10^7 | 2026-05-27 / 07-02 |
| Namesake / cruft | `kbase.nmdc_neon` (NEON program), `globalusers.nmdc_core_test*`, phantom `kbase_nmdc_neon`, broken `mamillerpa/my.nmdc_flattened_biosamples`, dual `.`/`_` aliases | — | — |

## Data Sources
All read-only, on-cluster. Evidence already captured in `data/provenance_probe.md`
(descriptions, row counts, Iceberg `snapshots.committed_at`) and
`data/probe_identifiers.py` (full database/table enumeration).

| Resource | Purpose | Rows verified | Filter/notes |
|---|---|---|---|
| `nmdc.metadata.*` | Genuine NMDC metadata | biosample_set 16,640 | LinkML-derived `*_set` tables |
| `nmdc.results.*` | NMDC pipeline outputs | KEGG 1.83B | large — filter before scan |
| `nmdc.ncbi_biosamples.*` | NCBI harvest (NOT NMDC) | attrs 756M | staler (2026-03-09) |
| `nmdc.ref_data.pfam_terms` | Pfam reference (NOT NMDC) | 27,481 | external |
| `kbase.nmdc_arkin.*` | Arkin-lab derived product | taxonomy 2.6M | file_id≠sample_id pitfalls |
| `kbase.nmdc_mags.*` | MAG catalog | 62,346 | freshest (2026-07-02) |
| `kbase.nmdc_neon.*` | NEON metagenomes | mags 16,093 | namesake collision |

### Performance Plan
- **Tier**: JupyterHub Spark SQL (on-cluster). Counts use Iceberg metadata (cheap).
- **Complexity**: simple — metadata/count/snapshot queries only; no heavy joins.
- **Known pitfalls**: `nmdc_arkin` STRING-typed numerics; `file_id` vs `sample_id` join
  keys; dual `.`/`_` aliases; `kbase.nmdc_*` DESCRIBE DATABASE is Forbidden (counts OK).

## Analysis Plan

### Notebook 00: Evidence consolidation (`notebooks/00_nmdc_landscape.ipynb`)
- **Goal**: Reproducibly regenerate the identifier map + provenance/scale/currency table
  from the two probe scripts, so every claim in the knowledge base is backed by a cell.
- **Expected output**: `data/nmdc_landscape.csv`, currency chart in `figures/`.

### Deliverable: `knowledge/` — Open-Knowledge-Format directory
Repo-native schema (`name`, `description`, `metadata.{type,provenance,tenant,databases,
currency,authority}`, `related`), one topic per file, cross-linked with `[[slug]]`:

1. `README.md` — index / map of the knowledge base (hub, links all files)
2. `nmdc-program-what-it-is.md` — NMDC the program; authority microbiomedata.org
3. `nmdc-label-is-overloaded.md` — the thesis: 3 tenants × 4 provenance classes
4. `nmdc-tenant-inventory.md` — the real `nmdc` tenant: metadata / results / ncbi / ref_data
5. `ncbi-biosamples-not-nmdc.md` — `nmdc.ncbi_biosamples` is an NCBI harvest; when to use
6. `nmdc-ref-data-is-pfam.md` — `nmdc.ref_data` is Pfam, not NMDC
7. `nmdc-data-outside-nmdc-tenant.md` — the `kbase.nmdc_*` blind spot
8. `nmdc-arkin-derived-product.md` — Arkin-lab enrichment; value-add + join pitfalls
9. `nmdc-neon-namesake-collision.md` — NEON ≠ NMDC
10. `nmdc-mags-catalog.md` — `kbase.nmdc_mags`, freshest resource
11. `nmdc-completeness-and-currency.md` — per-resource counts + snapshot ages
12. `nmdc-value-added-by-berdl.md` — flattening/harmonization/Iceberg/embeddings
13. `nmdc-naming-aliases-and-cruft.md` — dual aliases, test dbs, phantom/broken dbs
14. `nmdc-choosing-the-right-resource.md` — decision guide ("I want X → use Y")
15. `nmdc-prior-project-usage.md` — reuse map across 10 prior projects

### Deliverable: `REPORT.md` — findings + recommendations (no live edits yet)
Recommends specific, reviewable fixes: repair the `docs/schemas/` 404, add a berdl-skill
NMDC module, cross-link `kbase.nmdc_*` in the inventory output, relabel Rhea/GO in the
data atlas, surface currency/provenance in discovery. Drafted for `/berdl-review`.

## Expected Outcomes
- **If H1 supported** (expected): ≥4 distinct, evidence-backed confusion modes confirmed;
  the knowledge base + decision guide resolves each; recommendations are actionable.
- **If H0 not rejected**: existing naming/docs already disambiguate — knowledge base would
  be redundant. (Contradicted by Phase A: broken schema link, no skill content, no table
  comments, split tenant homes.)
- **Potential confounders**: some "confusion" may be intended (e.g., co-hosting NCBI under
  `nmdc` for join convenience); the knowledge base must explain rationale, not just flag.
  Access differences (`kbase.nmdc_*` DESCRIBE Forbidden) may limit some metadata capture.

## Revision History
- **v1** (2026-07-10): Initial plan. Phase A exploration already complete (identifier map,
  provenance/scale/currency probes, docs+tooling sweep); design decisions fixed with the
  author (repo-native OKF schema; knowledge dir + recommendations, no live doc/tool edits;
  project-local `knowledge/`).

## Authors
Mark Andrew Miller — LBL — ORCID [0000-0001-9076-6066](https://orcid.org/0000-0001-9076-6066)
