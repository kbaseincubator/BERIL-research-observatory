# OBI ↔ NMDC Workflow Type Mapping (from BERDL ontology store queries)

Date: 2026-04-03

## Corrected Assessment

Initial exploration reported OBI had "zero computational workflow terms." This was wrong.
A deeper search found OBI has several, but they're leaf nodes with no children — the hierarchy
is shallow and the terms are generic rather than metagenomics-specific.

## Mapping Table

| NMDC Workflow Type | NMDC Files | OBI Term | OBI ID | Gap? |
|---|---|---|---|---|
| `nmdc:NucleotideSequencing` (data_generation) | — | DNA sequencing assay | OBI:0000626 | No |
| ↳ whole metagenome | — | whole metagenome sequencing assay | OBI:0002623 | No |
| ↳ amplicon | — | amplicon sequencing assay | OBI:0002767 | No |
| `nmdc:ReadQcAnalysis` | 18,951 | (no match) | — | **Yes** |
| `nmdc:MetagenomeAssembly` | 41,149 | sequence assembly process | OBI:0001872 | **Partial** — exists but no metagenome-specific subclass |
| `nmdc:MetagenomeAnnotation` | 182,060 | sequence annotation | OBI:0001944 | **Partial** — exists but no metagenome-specific subclass |
| `nmdc:ReadBasedTaxonomyAnalysis` | 63,650 | (no match) | — | **Yes** |
| `nmdc:MagsAnalysis` | 47,606 | (no match) | — | **Yes** — genome binning is not modeled |
| `nmdc:MetabolomicsAnalysis` | 4,823 | mass spectrometry assay (likely) | OBI:0000470 | Probably no |
| `nmdc:MetaproteomicsAnalysis` | 774 | (mass spec subtypes) | — | Probably no |
| `nmdc:NomAnalysis` | 2,583 | (no match) | — | **Yes** |
| `nmdc:MetatranscriptomeAssembly` | 345 | sequence assembly process | OBI:0001872 | **Partial** |
| `nmdc:MetatranscriptomeAnnotation` | 1,725 | sequence annotation | OBI:0001944 | **Partial** |
| `nmdc:MetatranscriptomeExpressionAnalysis` | 138 | (no match) | — | **Yes** |

## OBI Computational Terms Found (with hierarchy)

```
OBI:0000011 planned process
├── OBI:0200000 data transformation
│   ├── OBI:0200187 sequence analysis data transformation
│   │   ├── OBI:0002567 sequence alignment
│   │   └── OBI:0002568 sequence data feature count tabulation
│   ├── OBI:0200170 averaging data transformation
│   ├── OBI:0200169 normalization data transformation
│   ├── OBI:0000650 differential expression analysis
│   ├── ... (~50 more statistical/analytical subtypes)
│   └── (NO: metagenome assembly, genome binning, taxonomic classification, read QC)
├── OBI:0001872 sequence assembly process  ← EXISTS but no children
├── OBI:0001944 sequence annotation  ← EXISTS but no children
├── OBI:0002587 machine learning
│   ├── OBI:0002588 supervised machine learning
│   └── OBI:0002589 unsupervised machine learning
├── OBI:0000094 material processing
│   └── OBI:0666667 nucleic acid extraction
├── OBI:0000711 library preparation
│   └── OBI:0001852 paired-end library preparation
└── OBI:0000070 assay
    ├── OBI:0000626 DNA sequencing assay
    ├── OBI:0002623 whole metagenome sequencing assay
    ├── OBI:0001177 RNA sequencing assay
    └── OBI:0002767 amplicon sequencing assay
```

## Related OBI Terms (assembly/annotation metadata)

| OBI ID | Label | Notes |
|---|---|---|
| OBI:0001522 | sequence assembly algorithm | "An algorithm used to assemble individual sequence reads into larger contiguous sequences" |
| OBI:0001625 | sequence annotation algorithm | "An algorithm used to identify sequence features" |
| OBI:0001948 | sequence assembly name | Textual entity denoting a sequence assembly |
| OBI:0001947 | sequence annotation provider | Person or org reporting annotation results |
| OBI:0001941 | contig N50 | N50 statistic for contigs |
| OBI:0001945 | scaffold N50 | N50 statistic for scaffolds |

## What This Means for the OBI Meeting

The story is more nuanced than "OBI has nothing":

1. **Sequence assembly and annotation exist** — but as generic leaf nodes. No metagenome-specific children.
   - "sequence assembly process" covers both single-genome assembly and metagenome assembly
   - "sequence annotation" covers both manual curation and automated pipelines like Prodigal
   
2. **The real gaps are**:
   - **Read QC / quality filtering** — no OBI term at all
   - **Genome binning** (MAGs) — completely unmodeled
   - **Taxonomic classification from sequences** — no OBI term
   - **Expression quantification** — no OBI term for metatranscriptomics

3. **Proposed 5 new terms** (refined from earlier):
   - `metagenome assembly` (child of OBI:0001872)
   - `metagenome-assembled genome binning` (child of OBI:0200000?)
   - `read quality assessment` (child of OBI:0200000)
   - `sequence-based taxonomic classification` (child of OBI:0200187)
   - `transcript expression quantification` (child of OBI:0200187)

4. **Don't propose**: metagenome annotation or metatranscriptome annotation as separate terms —
   OBI:0001944 "sequence annotation" already covers these adequately.

## Data Sources

- Ontology terms: `kbase_ontology_source.statements` (BERDL Spark SQL)
- Workflow file counts: `nmdc_arkin.omics_files_table` (385,562 files, 16 studies)
- Workflow executions: `nmdc_func_annot_freshwater_rivers.workflow_execution_set` (168 rows)
