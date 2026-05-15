# Answers to NUC Agent Questions (from BERDL Spark queries)

Date: 2026-04-03

## Q1: Run the notebook and export CSVs?

Done. NB01 executed successfully. CSVs exported to `data/` (gitignored but available locally):
- `obi_terms_in_store.csv` — all 4,422 OBI terms with labels/definitions
- `obi_cross_db_resolved.csv` — OBI IDs from NMDC resolved to ontology definitions
- `obi_gap_analysis.csv` — OBI annotation rates for candidate fields
- `ontology_adoption_comparison.csv` — OBI vs ENVO vs UBERON etc.
- `ontology_sizes_in_store.csv` — all ontologies in the store by size

Figure: `figures/ontology_adoption_comparison.png`

## Q2: OBI terms for computational workflows?

**OBI covers wet-lab well but has zero computational bioinformatics terms.**

### What OBI HAS (loaded in BERDL):
- `OBI:0002623` — whole metagenome sequencing assay
- `OBI:0000626` — DNA sequencing assay
- `OBI:0001177` — RNA sequencing assay
- `OBI:0002767` — amplicon sequencing assay
- `OBI:0000711` — library preparation
- `OBI:0001852` — paired-end library preparation
- `OBI:0666667` — nucleic acid extraction
- `OBI:0000659` — specimen collection process
- `OBI:0200000` — data transformation (generic parent + 22 subtypes like normalization, clustering, differential expression)
- `OBI:0000011` — planned process
- ~20 Illumina instrument terms (MiSeq, HiSeq, NovaSeq, etc.)
- Oxford Nanopore MinION/GridION/PromethION
- PacBio RS II, Sequel, Sequel II

### What OBI LACKS:
- Metagenome assembly
- Genome annotation / gene finding
- MAG binning (MetaBAT2, CheckM)
- Read QC / quality filtering
- Taxonomic classification (Kraken2, Centrifuge, GOTTCHA)
- Metatranscriptome assembly
- Any specific bioinformatics tool modeling

### What about EDAM and SWO?
**Neither EDAM nor SWO are loaded in `kbase_ontology_source`.** Zero terms for both. If we want to cover the computational gap, these ontologies would need to be ingested.

## Q3: What's in nmdc_core?

**Essentially nothing.** The `nmdc_core` databases are test/staging:
- `globalusers_nmdc_core_test` — 0 tables (empty)
- `globalusers_nmdc_core_test2` — 0 tables (empty)
- `globalusers_nmdc_core_test3` — 1 table (`covstats_gold`)

Not a useful resource.

### Full NMDC database landscape in BERDL:

| Database | Tables | Owner | Scale |
|---|---|---|---|
| `nmdc_arkin` | 63 | Gazi (infra), group decision (content) | 3.98B rows (contig_taxonomy) |
| `nmdc_flattened_biosamples` | 6 | Mark | 14,938 biosamples, 48 studies |
| `nmdc_ncbi_biosamples` | 17 | Gazi + Mark | 756M rows |
| `nmdc_func_annot_freshwater_rivers` | 4 | Mark | 2.56M functional annotations |
| `u_mamillerpa__nmdc_flattened_biosamples` | 6 | Mark (user copy) | Same as above |

## Q4: Populus study complete workflow chains?

**All 29 biosamples have all 5 workflow types.** Perfect completeness.

Every biosample in `nmdc:sty-11-1t150432` has:
- `nmdc:ReadQcAnalysis`
- `nmdc:ReadBasedTaxonomyAnalysis`
- `nmdc:MetagenomeAssembly`
- `nmdc:MetagenomeAnnotation`
- `nmdc:MagsAnalysis`

Each biosample has exactly 51 files. Total: 29 × 51 = 1,479 files.

This confirms it's an ideal ingestion candidate — no missing workflows, uniform completeness.

## Bonus Findings

### Method fields in nmdc_flattened_biosamples are all free text

| Field | Top values | OBI IDs? |
|---|---|---|
| `samp_collec_device` | auger (2,368), brownie cutter (1,376), corer (635) | None |
| `samp_collec_method` | Seawater (115), Kit 1 (42), Kit 5 (20) | None |
| `dna_isolate_meth` | Qiagen DNeasy PowerWater Sterivex (176), PowerSoil (120), PowerBiofilm (49) | None |

These are exactly the fields OBI was designed for. OBI has `specimen collection device` (OBI:0002814), `nucleic acid extraction` (OBI:0666667), etc. — but the actual NMDC data uses free text like "auger" and "Qiagen DNeasy PowerSoil" without any ontology IDs.

### Existing ingested study has workflow provenance but no OBI

`nmdc_func_annot_freshwater_rivers.workflow_execution_set` (168 rows) has:
- `type`: uses NMDC schema types (e.g., `nmdc:MetagenomeAnnotation`), not OBI
- `git_url`: links to workflow code on GitHub
- `processing_institution`: JGI
- `version`, `started_at_time`, `ended_at_time`

This is where OBI's `planned process` hierarchy *could* add value — mapping `nmdc:MetagenomeAnnotation` to the OBI process ontology — but currently NMDC uses its own type system.
