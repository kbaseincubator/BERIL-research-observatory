---
name: nmdc-data-outside-nmdc-tenant
description: NMDC-derived data that lives in the kbase tenant and is easy to miss
metadata:
  type: reference
  provenance: NMDC-derived, hosted in kbase tenant
  tenant: kbase
  databases: [kbase.nmdc_arkin, kbase.nmdc_mags, kbase.nmdc_neon]
  currency: "2026-07-02"
  authority: KBase / LBNL Arkin Lab / NEON
related: [nmdc-arkin-derived-product, nmdc-mags-catalog, nmdc-neon-namesake-collision, nmdc-label-is-overloaded]
---

# NMDC data also lives in the `kbase` tenant (the blind spot)

A user browsing the `nmdc` tenant sees four databases and reasonably concludes that is
"all the NMDC data." It is not. Three more `nmdc_*` databases live in the **`kbase`**
tenant and are **filed under "kbase"** by the inventory tooling — because grouping splits
on the catalog prefix (`kbase.` ), the `nmdc_` namespace substring is invisible to it.

## The three kbase-tenant NMDC databases
- **`kbase.nmdc_arkin`** (63 tables) — LBNL Arkin Lab's heavily enriched product:
  taxonomy, metabolomics/lipidomics/proteomics "gold" tables, embeddings, inferred traits,
  unified annotation hierarchies. See [[nmdc-arkin-derived-product]].
- **`kbase.nmdc_mags`** (5 tables) — MAG catalog (**62,346** MAGs), freshest of all
  NMDC-labeled data (2026-07-02). See [[nmdc-mags-catalog]].
- **`kbase.nmdc_neon`** (8 tables) — **NEON** metagenomes; a *different* program despite
  the `nmdc_` prefix. See [[nmdc-neon-namesake-collision]].

## Why this matters
- **Discovery gap**: neither `berdl_notebook_utils.get_databases()` grouping nor the
  inventory summary links these back to NMDC. A currency- or provenance-aware search over
  the `nmdc` tenant alone will silently exclude them.
- **Access nuance**: `DESCRIBE DATABASE EXTENDED kbase.nmdc_*` returns `ForbiddenException`
  for a `kesciencero`/`microbialdiscoveryforge` principal, even though `COUNT(*)` on the
  tables succeeds. So even metadata introspection behaves differently than for the `nmdc`
  tenant (owner `tgu2`, readable descriptions but empty properties).

## Practical rule
When you want "all NMDC-related data," search **both** `nmdc.*` **and** `kbase.nmdc_*` —
and remember `kbase.nmdc_neon` is NEON, not NMDC. The decision guide
[[nmdc-choosing-the-right-resource]] encodes this.
