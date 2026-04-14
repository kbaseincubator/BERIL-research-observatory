# Attribution and Provenance

This project has contributions from four distinct agents/systems. Findings
should be weighted differently depending on their source and what grounds them.

## Who Produced What

### 1. BERDL Claude (Claude on KBase JupyterHub, with Spark access)

**Grounded in:** Live Spark SQL queries against the BERDL ontology store,
NMDC biosamples, BacDive, Fitness Browser, and other lakehouse tables.

**What it produced:**
- `RESEARCH_PLAN.md` -- project scaffolding and hypothesis
- `notebooks/01_obi_census_and_usage.ipynb` -- Spark queries (executed, outputs saved)
- `figures/ontology_adoption_comparison.png` -- from notebook execution
- `BERDL_QUERY_ANSWERS.md` -- direct Spark query results
- `BERDL_INGESTION_CANDIDATES.md` -- datasets identified for ingestion
- `KG_MICROBE_METPO_QUESTIONS.md` -- trait data inventory from live queries
- `FLATTEN_WORKFLOW_COLLECTIONS.md` -- instructions for flattening NMDC data
- `NMDC_PEOPLE_QUESTIONS.md` -- questions about ontology governance
- `DOE_DATASETS_OBI_RELEVANCE.md` -- dataset relevance assessment
- `OBI_NMDC_WORKFLOW_MAPPING.md` -- workflow gap analysis (initial version)
- `NUC_SESSION_NOTES.md` -- corrections from NUC agent incorporated
- `SESSION_HANDOFF.txt` -- cross-instance communication (initial version)
- `data/nmdc_workflow_and_metadata_context.md` -- context for OpenScientist
- `OPENSCIENTIST_INVESTIGATION.md` -- tracking file for parallel investigation
- `README.md`, `requirements.txt`

**Reliability:** HIGH for quantitative claims (term counts, table sizes, format
inconsistencies). These come from SQL queries against live data. The finding that
OBI has 4,422 terms and <0.2% usage in method fields is empirical.

**Limitations:** The BERDL agent does not have access to nmdc-schema source code,
GitHub issues, Slack, Gmail, or Google Docs. Its understanding of the design
debates comes only from what the NUC agent writes into the handoff file.

### 2. NUC Claude (Claude Opus 4.6, 1M context, Mark's NUC desktop)

**Grounded in:** nmdc-schema source code (local clone), OLS4 API (lexical +
LLM embeddings), GitHub issues/PRs (via `gh` CLI), 10 Slack workspaces (via MCP),
Gmail and Google Drive (via MCP), desktop markdown files, hackathon draw.io
file (via Google Drive API), hackathon transcript (Google Doc).

**What it produced:**
- `data/entities-for-isolates.yaml` -- LinkML schema, validated with `gen-json-schema`
- `data/entities-for-isolates.jpg` -- copied from Downloads (Alicia's photo)
- `data/example-pseudomonas-putida-kt2440-pte314.yaml` -- hand-written example
- `isolate-schema-nmdc-mapping-analysis.md` -- class-by-class mapping to nmdc-schema
- `ISOLATE_SCHEMA_OBI_BRIDGE.md` -- bridge document
- `SESSION_2026-04-03_ISOLATE_SCHEMA.md` -- session log with source ranking
- `SESSION_HANDOFF.txt` -- updated with NUC findings and BERDL query suggestions
- `OBI_MEETING_STORY.md` -- expanded with OBI call prep, IEDB comparison, room dynamics
- `OBI_NMDC_WORKFLOW_MAPPING.md` -- corrected (initial BERDL version said "zero
  computational terms"; NUC agent found OBI:0001872 and OBI:0001944 via OLS4)
- `openscientist_results/` -- copied from Downloads, not produced by this agent

**Reliability:** HIGH for schema structure (LinkML-validated), ontology mappings
(OLS4 API responses cached and curated), and nmdc-schema analysis (read directly
from source YAML). MEDIUM for cross-source synthesis (Slack/Gmail/Drive searches
may miss results due to API limitations). The 120 OBI/OBO mappings were manually
curated from raw API results -- some judgment calls were made about exact vs close
vs broad mapping type.

**Limitations:** Cannot run Spark queries. Cannot execute notebooks on BERDL.
The P. putida example YAML is hand-written and has NOT been validated against
the schema (it uses a non-standard `class:` key format). The phenotype
decomposition (OBI+CHEBI+PATO slots) is theoretical -- not tested against real
BacDive data.

### 3. OpenScientist (autonomous research agent, 10 iterations)

**Grounded in:** PubMed literature search, Python code execution (matplotlib,
pandas, networkx for figures), and the context document uploaded to it
(`data/nmdc_workflow_and_metadata_context.md`, written by the BERDL agent).

**What it produced:**
- `openscientist_results/final_report.md` and `.pdf`
- `openscientist_results/*.png` -- 12 figures (coverage matrices, roadmaps, etc.)
- `openscientist_results/OPENSCIENTIST_INVESTIGATION.md`

**Reliability:** MEDIUM-LOW. OpenScientist is valuable for literature synthesis
and strategic framing, but has known issues:

**Verified findings:**
- The 5-layer ontology stack recommendation (OBI+ENVO+MIxS+EDAM+PROV) is sound
  and consistent with what the other agents found independently.
- The observation that MAG quality assessment is a cross-ontology gap is confirmed
  by both BERDL queries (no OBI term found in ontology store) and NUC analysis
  (no OBI term found via OLS4).
- The general wet-lab vs computational asymmetry is confirmed by all three agents.

**Unverified or potentially fabricated claims:**
- **OBI CURIEs need checking.** OpenScientist cites OBI:0000257 for DNA extraction;
  the actual term in nmdc-schema is OBI:0666667 (nucleic acid extraction). It also
  proposes parent class OBI:0200000 for several new terms -- this ID should be
  verified against OLS4 or the OBI source. Autonomous agents frequently hallucinate
  ontology identifiers.
- **Coverage percentages** ("25% to 52% with 9 mappings, 81% with 6 NTRs") are
  computed from OpenScientist's own denominator, which may not match the actual
  nmdc-schema element count. The BERDL agent found 44 OBI references; the NUC
  agent found 48; OpenScientist reports 44. These should be reconciled.
- **Literature citations** include PMIDs. These have not been spot-checked for
  existence or accurate representation of the cited papers' findings.
- **The figures are schematic, not data-driven.** The coverage matrices, roadmaps,
  and workflow diagrams were generated by matplotlib from OpenScientist's own
  internal model, not from live data queries. They illustrate the agent's
  interpretation, not empirical measurements.

**Recommendation:** Treat OpenScientist results as a literature review and
strategic framework. Do NOT cite its OBI CURIEs without verifying against OLS4
or the OBI GitHub. Do NOT treat its coverage percentages as authoritative without
reconciling the denominator with the actual schema.

### 4. Mark Miller (human)

**What he contributed:**
- The research question and strategic framing (OBI as vocabulary vs framework)
- Corrections to agent work (e.g., "zero computational terms" was wrong)
- Alicia's whiteboard photo
- Direction to connect isolate schema to OBI coverage project
- Direction to connect to OPAL/AMP2
- Decision to use OLS4 embeddings with full descriptions, not just class names
- The question about whether pTE314 is "engineering" (clarifying domain semantics)
- Prior desktop markdown research (6+ files on OBI, 6+ on isolate modeling)
- TURBO/Penn background knowledge informing the OBI framework assessment

**Mark's prior work that informs this project but lives elsewhere:**
- `~/Desktop/markdown/obi-april-6-nmdc-perspective-2026-03-30.md`
- `~/Desktop/markdown/obi-call-prep-2026-04-06.md`
- `~/Desktop/markdown/isolate-modeling-open-questions-2026-03-23.md`
- `~/Desktop/markdown/isolate-modeling-brief-2026-03-14.md`
- `~/Desktop/markdown/organism-sample-precedent-analysis-2026-03-18.md`
- `~/Desktop/markdown/organism-sample-authority-overlap-2026-03-18.md`
- nmdc-schema PR #2884 (OrganismSample class, ~143 slot assignments)

## Where the Agents Agree

All three agents independently concluded:

1. OBI covers wet-lab investigation steps well (extraction, library prep, sequencing)
2. OBI has critical gaps in computational bioinformatics (read QC, genome binning, taxonomic classification)
3. MAG quality assessment (CheckM/MIMAG) has no term in any OBO Foundry ontology
4. NMDC already uses 44-48 OBI references, concentrated in instruments and processes
5. NMDC method/instrument fields are overwhelmingly free text despite OBI terms existing
6. OBI is used as a vocabulary (bag of CURIEs), not as a modeling framework

## Where the Agents Diverge

| Topic | OpenScientist | BERDL Claude | NUC Claude |
|---|---|---|---|
| **OBI term for DNA extraction** | OBI:0000257 | (not addressed) | OBI:0666667 (from nmdc-schema source) |
| **Coverage denominator** | ~20 workflow steps | 4,422 OBI terms vs NMDC fields | 18 isolate classes, 2,326 schema elements |
| **Organism vs Sample** | Not addressed | Not addressed | Three competing models identified; central to isolate hackathon |
| **Engineered biology** | Not addressed | Not addressed | P. putida KT2440 + pTE314 example; OPAL/AMP2 connection |
| **Phenotype modeling** | Not addressed | 988K BacDive tests identified | OBI+CHEBI+PATO decomposition pattern designed |
| **Recommended next step** | Submit 6 NTRs to OBI | Run NB01 on JupyterHub | Use isolate schema as hackathon discussion artifact |
| **EDAM role** | Central to 5-layer stack | Not assessed | Not assessed (potential gap in our analysis) |

## Known Gaps in This Project

1. **EDAM coverage not assessed.** OpenScientist recommends EDAM for computational
   operations, but neither the BERDL nor NUC agent evaluated EDAM's actual coverage
   of metagenomics workflows. This should be checked.

2. **OpenScientist CURIEs not verified.** At least one OBI ID (OBI:0000257) appears
   to be wrong. A systematic check of all CURIEs in `final_report.md` against OLS4
   has not been done.

3. **P. putida example not validated.** The YAML uses a non-standard format and has
   not been run through `linkml-validate`.

4. **BacDive phenotype decomposition untested.** The OBI+CHEBI+PATO slots on the
   Phenotype class are designed but not tested against real data rows.

5. **submission-schema not examined.** The dual-schema question (nmdc-schema#2898)
   requires understanding what submission-schema currently models. Not done.

6. **Hackathon draw.io topology not extracted.** Page names and labels were extracted
   but not the full graph structure (edges, source/target relationships).

7. **METPO alignment not done.** The Phenotype class should map to METPO terms but
   METPO is not in OLS4 and was not checked via BioPortal or local files.
