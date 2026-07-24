---
name: nmdc-neon-namesake-collision
description: kbase.nmdc_neon is NEON (National Ecological Observatory Network), not NMDC
metadata:
  type: reference
  provenance: NEON (NSF program); processed via NMDC-style workflows, hosted in kbase
  tenant: kbase
  databases: [kbase.nmdc_neon]
  currency: "2026-07-02"
  authority: neonscience.org
related: [nmdc-data-outside-nmdc-tenant, nmdc-mags-catalog, nmdc-label-is-overloaded]
---

# `kbase.nmdc_neon` — NEON is not NMDC

Two national programs, one confusable acronym:
- **NMDC** = National Microbiome Data **Collaborative** (DOE-BER).
- **NEON** = National **Ecological** Observatory Network (NSF) — a continental-scale
  ecological monitoring network with standardized field sites.

`kbase.nmdc_neon` holds **NEON** soil/environmental metagenomes (processed through
NMDC-style workflows, hence the `nmdc_` prefix), **not** NMDC-consortium data. Treating it
as NMDC would mis-scope any sampling-design, geography, or agency-attribution claim.

## Contents (8 tables)
- `neon_mag_catalog` (**16,093**) — MAGs from NEON samples.
- `sample_data` (**340,871**), `sample_weather_10d` — NEON sample + 10-day weather context.
- `study_sample` (**5,917**), `hqmq_bin_catalog`, `contig_coverage`, `data_object`,
  `results_neon_map`.
- Currency: 2026-06-24 → 2026-07-02 (fresh).

## Use
- **Use** for NEON-site metagenomics with standardized ecological/weather covariates.
- **Attribute to NEON/NSF**, not NMDC/DOE-BER, in any writeup.
- If you want NMDC-consortium MAGs specifically, use [[nmdc-mags-catalog]]
  (`kbase.nmdc_mags`) instead — a separate catalog.

## Provenance summary
Origin: **NEON** (NSF). Host: `kbase` tenant. Class-6 ("namesake collision") in
[[nmdc-label-is-overloaded]]. The single clearest example of substring ≠ provenance.
