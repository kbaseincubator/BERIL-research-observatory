---
name: nmdc-label-is-overloaded
description: The core thesis — one "NMDC" label spans three tenants and six provenance classes
metadata:
  type: reference
  provenance: audit finding
  tenant: nmdc, kbase, globalusers, user
  databases: [nmdc.metadata, nmdc.results, nmdc.ncbi_biosamples, nmdc.ref_data, kbase.nmdc_arkin, kbase.nmdc_mags, kbase.nmdc_neon]
  currency: "2026-07-10"
  authority: nmdc_context_audit project
related: [nmdc-program-what-it-is, nmdc-data-outside-nmdc-tenant, nmdc-naming-aliases-and-cruft, nmdc-choosing-the-right-resource]
---

# The "NMDC" label is overloaded

Searching BERDL for "nmdc" returns resources that share **only the substring** — not
provenance, not scope, not scale, not currency. This is the central hazard: a user who
treats "the NMDC data" as one coherent thing will make wrong assumptions.

## Six provenance classes under one label
| Class | Resource(s) | Whose work | Signature scale |
|---|---|---|---|
| **Genuine NMDC** | `nmdc.metadata`, `nmdc.results` | NMDC program (DOE-BER) | 16.6k biosamples → 1.83B annotations |
| **External re-host (NCBI)** | `nmdc.ncbi_biosamples` | NCBI (harvested) | 51.7M biosamples, 756M attrs |
| **External re-host (Pfam)** | `nmdc.ref_data` | Pfam consortium | 27,481 terms |
| **Other-group derivation** | `kbase.nmdc_arkin` | LBNL Arkin Lab | 2.6M taxonomy, embeddings/traits |
| **NMDC-derived, kbase tenant** | `kbase.nmdc_mags` | KBase/NMDC | 62,346 MAGs |
| **Namesake collision** | `kbase.nmdc_neon` | NEON (NSF, *not* NMDC) | 16,093 MAGs |

Plus **cruft**: dual `.`/`_` aliases, `globalusers.nmdc_core_test*` test DBs, a phantom
`kbase_nmdc_neon` (0 tables), and broken `mamillerpa/my.nmdc_flattened_biosamples`. See
[[nmdc-naming-aliases-and-cruft]].

## Why it confuses (the four failure modes)
1. **Mistaking re-hosted external data for NMDC output** — pulling `nmdc.ncbi_biosamples`
   (an NCBI harvest) or `nmdc.ref_data` (Pfam) thinking it is NMDC-curated microbiome data.
2. **Missing NMDC data in another tenant** — browsing only the `nmdc` tenant and never
   finding `kbase.nmdc_mags` / `kbase.nmdc_arkin`. The inventory files those under "kbase".
3. **Conflating NEON with NMDC** — `kbase.nmdc_neon` is the National *Ecological*
   Observatory Network, a different agency and sampling design.
4. **Trusting a stale snapshot** — currency ranges from days (`kbase.nmdc_mags`, 2026-07-02)
   to months (`nmdc.ncbi_biosamples`, 2026-03-09) with nothing surfaced at discovery time.

## Why it isn't visible today
The lakehouse carries **no table `Comment`** and no database description (owner `tgu2`,
empty `Properties`). The static docs' canonical NMDC schema link (`docs/schemas/nmdc.md`)
is a **404**, `docs/overview.md` never mentions NMDC, and the berdl skill has **zero**
NMDC content. So none of the disambiguation above reaches a user through the normal
discovery path. This knowledge base is the missing layer.
