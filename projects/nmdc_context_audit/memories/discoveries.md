# Discoveries — nmdc_context_audit

<!-- [nmdc_context_audit] 2026-07-10T18:07:52Z  approved-report extraction (REVIEW: REVIEW_3.md) -->

- The "nmdc" tenant co-hosts a 51.7M-row NCBI BioSample mirror and Pfam vocabulary
  alongside genuine NMDC data; substring ≠ provenance. Any project treating "the nmdc
  tenant" as one coherent NMDC dataset will mis-scope or mis-attribute.
- NMDC-derived data is split across two tenant homes (`nmdc.*` and `kbase.nmdc_*`) with no
  cross-link; the freshest NMDC resource (`kbase.nmdc_mags`, 62,346 MAGs) sits in the tenant
  a user is least likely to search for NMDC.
- `kbase.nmdc_neon` is NEON (NSF National Ecological Observatory Network), a different
  program — an acronym collision that would corrupt agency attribution.
- Iceberg `.snapshots.committed_at` is the only available data-currency signal (no table
  comments, no changelog); it should be surfaced in discovery tooling.
