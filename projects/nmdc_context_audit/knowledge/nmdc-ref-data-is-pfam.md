---
name: nmdc-ref-data-is-pfam
description: nmdc.ref_data holds Pfam vocabulary terms, not NMDC data
metadata:
  type: reference
  provenance: Pfam (external reference, re-hosted under nmdc tenant)
  tenant: nmdc
  databases: [nmdc.ref_data]
  currency: "2026-05-20"
  authority: pfam.xfam.org / InterPro
related: [nmdc-tenant-inventory, nmdc-label-is-overloaded]
---

# `nmdc.ref_data` is Pfam reference data

A single-table database, `nmdc.ref_data.pfam_terms` (**27,481** rows), holding the **Pfam**
protein-family controlled vocabulary. It is external reference data co-located in the
`nmdc` tenant to support annotation joins (e.g. against
`nmdc.results.pfam_annotation_gff`) — **not** an NMDC-generated dataset.

## Use
- Join `pfam_terms` to Pfam accessions in annotation tables to attach human-readable family
  names/descriptions.
- Do not cite it as "NMDC reference data" — cite **Pfam/InterPro** as the authority.

## Provenance summary
Origin: **Pfam** consortium. Re-host: `nmdc` tenant, owner `tgu2`. Class-3 ("external
reference re-host") in [[nmdc-label-is-overloaded]]. Note the parallel mislabel in the data
atlas, where Rhea/GO reference ontologies under `kbase.nmdc_arkin` are tagged "NMDC
integrated" — same provenance-blur pattern (see [[nmdc-arkin-derived-product]]).
