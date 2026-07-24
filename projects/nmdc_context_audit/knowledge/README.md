---
name: nmdc-knowledge-index
description: Map of the NMDC context knowledge base — start here to pick the right NMDC resource
metadata:
  type: reference
  provenance: audit synthesis
  tenant: nmdc, kbase
  databases: [nmdc.metadata, nmdc.results, nmdc.ncbi_biosamples, nmdc.ref_data, kbase.nmdc_arkin, kbase.nmdc_mags, kbase.nmdc_neon]
  currency: "2026-07-10"
  authority: nmdc_context_audit project
related: [nmdc-label-is-overloaded, nmdc-choosing-the-right-resource]
---

# NMDC in BERDL — Context Knowledge Base

The label **"NMDC"** is attached to BERDL resources that differ enormously in what they
are, who made them, how big they are, and how current they are. This directory exists so
a BERIL user can answer *"which NMDC resource do I actually want?"* in the **first minutes**
of a session instead of discovering the pitfalls after burning time and compute.

Every fact here is backed by the live catalog (see `../notebooks/00_nmdc_landscape.ipynb`,
`../data/nmdc_landscape.csv`, `../data/provenance_probe.md`).

## Read this first
- **[[nmdc-label-is-overloaded]]** — the core problem: one label, three tenants, six provenance classes.
- **[[nmdc-choosing-the-right-resource]]** — decision guide: *"I want X → use Y."*

## What each thing actually is
- **[[nmdc-program-what-it-is]]** — NMDC the program (microbiomedata.org) vs "nmdc" the tenant.
- **[[nmdc-tenant-inventory]]** — the real `nmdc` tenant: `metadata`, `results`, `ncbi_biosamples`, `ref_data`.
- **[[ncbi-biosamples-not-nmdc]]** — `nmdc.ncbi_biosamples` is an **NCBI** harvest, not NMDC output.
- **[[nmdc-ref-data-is-pfam]]** — `nmdc.ref_data` is **Pfam**, not NMDC.
- **[[nmdc-data-outside-nmdc-tenant]]** — NMDC data hiding in the **`kbase`** tenant (you'll miss it).
- **[[nmdc-arkin-derived-product]]** — `kbase.nmdc_arkin`: Arkin-lab enrichment (embeddings/traits).
- **[[nmdc-mags-catalog]]** — `kbase.nmdc_mags`: the MAG catalog (freshest resource).
- **[[nmdc-neon-namesake-collision]]** — `kbase.nmdc_neon`: **NEON** ≠ NMDC.

## Cross-cutting
- **[[nmdc-completeness-and-currency]]** — scale (10^1–10^9 rows) and snapshot ages, per resource.
- **[[nmdc-value-added-by-berdl]]** — what BERDL added over upstream (flattening, harmonization, embeddings).
- **[[nmdc-naming-aliases-and-cruft]]** — dual `.`/`_` aliases, test DBs, phantom/broken DBs.
- **[[nmdc-prior-project-usage]]** — which prior BERIL projects used which resource (reuse map).

## One-glance summary
| Resource | Tenant | Really is | Signature rows | Currency |
|---|---|---|---:|---|
| `nmdc.metadata` | nmdc | **Genuine NMDC** metadata | 16,640 biosamples | 2026-05-20 |
| `nmdc.results` | nmdc | **Genuine NMDC** pipeline output | 1.83B KEGG rows | 2026-05-20 |
| `nmdc.ncbi_biosamples` | nmdc | **NCBI** harvest | 51.7M biosamples | 2026-03-09 |
| `nmdc.ref_data` | nmdc | **Pfam** reference | 27,481 terms | 2026-05-20 |
| `kbase.nmdc_arkin` | kbase | **Arkin-lab** derivation | 2.6M taxonomy rows | 2026-05-27 |
| `kbase.nmdc_mags` | kbase | NMDC-derived MAGs | 62,346 MAGs | 2026-07-02 |
| `kbase.nmdc_neon` | kbase | **NEON** program (not NMDC) | 16,093 MAGs | 2026-07-02 |
