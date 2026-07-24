---
name: nmdc-mags-catalog
description: kbase.nmdc_mags is the NMDC-derived MAG catalog and the freshest NMDC-labeled resource
metadata:
  type: reference
  provenance: NMDC-derived MAGs, hosted in kbase tenant
  tenant: kbase
  databases: [kbase.nmdc_mags]
  currency: "2026-07-02"
  authority: KBase / NMDC
related: [nmdc-data-outside-nmdc-tenant, nmdc-neon-namesake-collision, nmdc-completeness-and-currency]
---

# `kbase.nmdc_mags` — the MAG catalog

Metagenome-assembled genomes derived from NMDC data, in the `kbase` tenant. **Freshest**
NMDC-labeled resource (Iceberg snapshots 2026-07-01 → 2026-07-02, i.e. days old at audit).

## Contents (5 tables)
- `mag_catalog` (**62,346**) — the MAGs.
- `bin_catalog` (**17,218**) — bins.
- `study_sample` (**1,405**), `biosample_metadata` (**1,349**) — sample/study linkage.
- `data_object` — file/object references.

## Use
- **Use** for NMDC-consortium MAG-level analyses (genome catalogs, bin quality, sample
  provenance). Distinct from [[nmdc-neon-namesake-collision]] (`kbase.nmdc_neon`, NEON MAGs)
  and from the read-based taxonomy in [[nmdc-arkin-derived-product]].
- Because it is refreshed most recently, prefer it when currency matters and cross-check
  its snapshot date against the other resources in [[nmdc-completeness-and-currency]].

## Provenance summary
Origin: NMDC-derived (MAG assembly/curation). Host: `kbase` tenant. Class-5
("NMDC-derived, kbase tenant") in [[nmdc-label-is-overloaded]].
