# OpenScientist Parallel Investigation: OBI for Environmental Microbiology

## Context

This is a companion to the BERDL-side OBI coverage analysis (see [RESEARCH_PLAN.md](RESEARCH_PLAN.md)).
While the BERDL investigation queries the lakehouse directly to measure OBI adoption in NMDC metadata,
this OpenScientist investigation takes a literature- and ontology-driven approach to assess OBI's
suitability for the environmental microbiology domain more broadly.

## Platform

- **OpenScientist** (formerly SHANDY): https://www.openscientist.io/
- Developed by Justin Reese (LBNL/BBOP)
- Settings: Hypothesis Generation ON, Coinvestigate Mode ON, Max Iterations 10

## Research Question (submitted to OpenScientist)

How well does the Ontology for Biomedical Investigations (OBI) model the study designs, assays, and
data transformations used in environmental microbiology — particularly metagenomic assembly, genome
binning (CheckM), taxonomic identification, gene finding, and functional annotation? Where does OBI
provide good coverage, where are the gaps, and what complementary ontologies (e.g., ENVO, MIxS,
NMDC Schema, OBI's own planned terms) could fill them?

Context: The NMDC (National Microbiome Data Collaborative) captures study-level and biosample-level
metadata for environmental microbiome projects, plus downstream bioinformatics outputs (assemblies,
MAGs, read QC, annotation). NMDC currently uses ENVO for environmental context, MIxS for sample
metadata, and its own schema for workflow provenance — but does not systematically use OBI for assay
or study design modeling. Investigate:

1. What OBI terms already cover NMDC-style workflows (nucleic acid extraction, library preparation,
   sequencing, assembly, binning, annotation)?
2. What projects beyond NMDC use OBI for environmental or microbial genomics, and what patterns
   have they established?
3. Where would adopting OBI improve interoperability, discoverability, or scale-up toward
   biotechnology applications (e.g., linking discovery of novel organisms to cultivation or
   bioprocess design)?
4. What are OBI's limitations for this domain — missing assay types, poor modeling of computational
   workflows, or conflicts with existing NMDC/MIxS terminology?

## Why OpenScientist (not BERDL)

OpenScientist does not have direct access to NMDC metadata or BERDL lakehouse tables. Its strengths
are literature search, ontology structure analysis, and cross-project pattern discovery. This
complements the BERDL investigation, which measures actual OBI term usage in real datasets but
cannot easily survey how other projects use OBI or what the ontology community considers best
practice.

## Expected Outputs

- Assessment of OBI's coverage of environmental microbiology workflows
- Survey of OBI adoption by projects comparable to NMDC
- Gap analysis: which assay types, computational steps, or study designs lack OBI terms
- Recommendations for complementary ontologies or OBI term requests

## Relationship to BERDL Investigation

| Aspect | BERDL (lakehouse queries) | OpenScientist (literature/ontology) |
|---|---|---|
| OBI term inventory | Direct query of `kbase_ontology_source` | OBI structure analysis from OWL/OBO |
| NMDC usage patterns | Regex search across biosample attributes | Literature on NMDC + MIxS OBI recommendations |
| Gap analysis | Fields that could use OBI but don't | Workflow steps OBI doesn't model at all |
| Cross-project survey | Limited to BERDL tenants | Broad literature + ontology registry search |
| Biotechnology bridge | Not in scope | Assess OBI's role in discovery-to-application |

## Status

- **2026-04-03**: Submitted to OpenScientist. Awaiting results.

## Authors

- Mark Andrew Miller (ORCID: [0000-0001-9076-6066](https://orcid.org/0000-0001-9076-6066)), Lawrence Berkeley National Laboratory
