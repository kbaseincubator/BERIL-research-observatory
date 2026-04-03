# Notes from NUC Claude Session (2026-04-03)

These are concerns, questions, suggestions, and corrections from Mark's NUC-side Claude session,
intended for the BERDL Claude agent to incorporate.

## Corrections

### Gazi's Role
Gazi is the **system architect** — he built the lakehouse infrastructure and loaded data. But he
is not the decision-maker on what data goes where or what gets prioritized. Those decisions come
from PIs, the NMDC team, and group leads (Chris Mungall, Paramvir Dehal, etc.). Don't attribute
data curation choices to Gazi.

### NMDC Schema Maintainers
You asked "who maintains the NMDC schema?" — Mark can answer this directly:
- **Patrick Kalita** and **Sierra Moxon** are the primary nmdc-schema maintainers
- **Mark Miller** (the user) is also a contributor
- Schema governance discussions happen in the microbiomedata GitHub org and NMDC Slack

### env_triads Curation
You asked "who curated env_triads_flattened?" — Mark built `nmdc_flattened_biosamples` (including
env triads). The env_triads table uses ENVO/UBERON/NCBITaxon because that's what MIxS requires for
the `env_broad_scale`, `env_local_scale`, and `env_medium` fields. OBI's absence there is by
design — OBI describes investigations/assays, not environmental context. Not a gap.

## Namespace Landscape (Authoritative Source)

The BERDL NMDC namespace breakdown is documented in detail at:
`~/Desktop/markdown/berdl-nmdc-database-landscape-2026-03-24.md`

Key facts your files should reflect:

| Namespace | Owner/Builder | Content | Scale |
|---|---|---|---|
| `nmdc_arkin` | Gazi (infrastructure), group decision (content) | Multi-omics results, embeddings, reference ontologies | 3.98B rows (contig_taxonomy) |
| `nmdc_flattened_biosamples` | Mark | Biosample metadata, env triads, location, ecosystem | 14,938 rows |
| `nmdc_ncbi_biosamples` | Gazi + Mark | NCBI biosample cross-reference, harmonized attributes | 756M rows |
| `nmdc_func_annot_freshwater_rivers` | Mark | Functional annotation counts for 1 study | 2.56M rows |
| `nmdc_core` | Earlier KBase work | Core NMDC schema tables | Unknown |
| `kbase_ontology_source` | KBase | Where OBI lives (4,422 terms) — this project's primary query target | Millions of triples |
| `kescience_*` | Mikaela Cashman | External reference datasets (AlphaFold, BacDive, PDB, etc.) | Varies |
| `bervodata_*` | Chris Mungall, Harry Caufield | HWSD2 soils, FAO soils | 25 tables each |

### nmdc_arkin Has 4 Categories (Not All Equal)

1. **NMDC metadata** (~5 tables) — duplicated in other NMDC databases
2. **NMDC bioinformatics results** (~10 tables) — parsed from NMDC workflow outputs. Only **19 of 48 studies** have data here.
3. **Third-party reference data** (~20 tables) — KEGG, COG, EC, GO, MetaCyc. Available from public sources but co-located for joins.
4. **Unique to nmdc_arkin** (~15 tables) — Gazi's embeddings, feature matrices, tokenizations. **This is the irreplaceable value.** Not available from NMDC API or any public source.

### Data Access Has Changed
`data.microbiomedata.org` migrated from NERSC/Spin to **Google Cloud Storage** as of 2025-10-20.
DataObject URLs still resolve, but the backend is GCS, not NERSC filesystem.

## Ingestion Candidate Recommendation

We surveyed all 84 NMDC studies via the API. Key findings:

- Only 20 studies have data objects at all
- 14 have the complete workflow chain (QC → Assembly → Annotation → Taxonomy → MAGs)
- The **smallest complete study** is `nmdc:sty-11-1t150432` (Populus rhizosphere, 29 biosamples)
- But even that is 4.1 TB total — need to ingest **metadata + summary files only** (~1 GB)
- Target files: CheckM stats, GTDBTK summaries, annotation stats, assembly stats
- Skip: raw reads, filtered reads, BAMs, full taxonomic classification files (90%+ of size)
- Alternative: start with just MongoDB metadata (study + biosample + workflow documents as parquet) — under 10 MB

See `BERDL_INGESTION_CANDIDATES.md` for full details and API commands.

## OpenScientist Investigation

Submitted a research question to OpenScientist (formerly SHANDY) at https://www.openscientist.io/
about OBI's suitability for environmental microbiology workflows. This is a literature/ontology
approach that complements your lakehouse queries. See `OPENSCIENTIST_INVESTIGATION.md`.

We uploaded `data/nmdc_workflow_and_metadata_context.md` to give OpenScientist the NMDC-specific
context it can't query directly. Results pending.

## Key Insight from Desktop Markdown

From `~/Desktop/markdown/ro-crate-vs-croissant-nmdc-relevance-2026-02-24.md`:
- NMDC already has an **"OBI + PROV + PAV provenance model"** internally
- The provenance squad is working on **"OBI process modeling (PlannedProcess hierarchy)"**
- Chris Mungall considers NMDC's OBI-based provenance richer than generic alternatives
- This means OBI adoption isn't zero — it's in the schema design, just not enforced in submissions

## Questions for You (BERDL Agent)

1. Can you run the notebook (`01_obi_census_and_usage.ipynb`) and export the CSVs? The NUC can't
   run Spark queries directly.
2. Have you checked `kbase_ontology_source` for OBI terms related to computational workflows
   specifically? (e.g., `data transformation`, `sequence assembly`, `genome annotation`)
3. What does the `nmdc_core` namespace actually contain? It's listed but never characterized.
4. Can you query `nmdc_arkin.omics_files_table` to find which biosamples from
   `nmdc:sty-11-1t150432` have complete workflow chains (all 5 types)?

## OpenScientist Is Running

OpenScientist (https://www.openscientist.io/) is actively working on a related investigation
right now (submitted 2026-04-03). Hypothesis generation ON, coinvestigate mode ON, 10 iterations.
Track its progress and incorporate findings when available. See `OPENSCIENTIST_INVESTIGATION.md`
for the exact research question submitted.

## Broader Vision: OBI + METPO as Mark's Research Ontology Stack

This project isn't just about OBI coverage gaps in NMDC. Mark's longer-term goal is to get to a
state where **OBI + METPO** together provide strong support for his research projects:

- **OBI** covers study designs, assays, instruments, data transformations — the "how" of
  environmental microbiology research
- **METPO** (Microbial Traits and Phenotypes Ontology) covers microbial phenotypes — the "what"
  organisms can do. Mark considers METPO better than other high-profile microbial ontologies
  for phenotypes because it is easier to maintain, actively maintained, and passes OWL and
  most OBO expectations.
- **CHEBI, GO, etc.** are already used in kg-microbe and NMDC annotations — those are covered.
  The gap is in the OBI + METPO layer.

The framing for this project should be: **OBI is good at representing designs, assays, and
experimental processes. METPO is good at representing microbial phenotypes. Together they could
provide a more complete ontological foundation for environmental microbiology research than
either alone.** The OBI coverage investigation is one half of that picture.

Relevant repos:
- METPO: `turbomam/microbial-traits-and-phenotypes-ontology`
- kg-microbe: `CultureBotAI/KG-Microbe-search`
- microbial-trait-mappings: `turbomam/microbial-trait-mappings`

## Repo Access Request

Mark has requested contributor access to `kbaseincubator/BERIL-research-observatory` from
Paramvir Dehal in NMDC Slack `#ber_lakehouse` (2026-04-03T17:37:52Z). Currently push-only to
fork (`turbomam/BERIL-research-observatory`). Until resolved, continue using the explicit push:
```bash
git push fork HEAD:refs/heads/<branch-name>
```
