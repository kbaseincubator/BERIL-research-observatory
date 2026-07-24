# References — NMDC Context Audit

Authoritative sources for the data providers and programs disambiguated in this audit.

- **National Microbiome Data Collaborative (NMDC)** — DOE-BER. https://microbiomedata.org/
- Eloe-Fadrosh, E.A., et al. (2022). "The National Microbiome Data Collaborative Data
  Portal: an integrated multi-omics microbiome data resource." *Nucleic Acids Research*
  50(D1):D828–D836.
- **National Ecological Observatory Network (NEON)** — NSF. https://www.neonscience.org/
  (source of `kbase.nmdc_neon`; distinct from NMDC).
- Barrett, T., et al. (2012). "BioSample database at the National Center for Biotechnology
  Information." *Nucleic Acids Research* 40(D1):D57–D63. (source of `nmdc.ncbi_biosamples`).
- Mistry, J., et al. (2021). "Pfam: The protein families database in 2021." *Nucleic Acids
  Research* 49(D1):D412–D419. (source of `nmdc.ref_data.pfam_terms`).
- Arkin, A.P., et al. (2018). "KBase: The United States Department of Energy Systems Biology
  Knowledgebase." *Nature Biotechnology* 36:566–569.

## In-repo prior knowledge
- `docs/pitfalls.md` — `## nmdc_arkin` and `## NMDC (nmdc_arkin) Pitfalls` sections.
- `docs/discoveries.md` — NMDC community-ecology discoveries (~lines 629–685).
- `projects/nmdc_community_metabolic_ecology/` — richest prior `kbase.nmdc_arkin` worked example.
- `projects/harvard_forest_warming/` — genuine-NMDC (`nmdc.metadata` + `nmdc.results`) exemplar.
