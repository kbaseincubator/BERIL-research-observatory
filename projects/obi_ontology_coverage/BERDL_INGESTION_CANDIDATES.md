# NMDC Data Ingestion Candidates for BERDL Lakehouse

## Goal

Ingest a small, complete NMDC dataset into BERDL that tells a full biological story:
environment → sample → sequencing → assembly → binning → taxonomy → function.
Small enough to ingest quickly, rich enough to be scientifically interesting.

## API-Driven Study Survey (2026-04-03)

Scanned all 84 NMDC studies via `https://api.microbiomedata.org/data_objects/study/{id}`.
Only 20 studies have data objects; of those, 14 have the complete workflow chain
(QC → Assembly → Annotation → Taxonomy → MAGs).

### Complete-Chain Studies (sorted by biosample count)

| Study ID | Biosamples | Data Objects | Total Size | Name |
|---|---|---|---|---|
| `nmdc:sty-11-1t150432` | 29 | 1,479 | 4.1 TB | Populus root and rhizosphere (TN) |
| `nmdc:sty-11-8ws97026` | 42 | 3,659 | 6.6 TB | Switchgrass cropping systems |
| `nmdc:sty-11-dwsv7q78` | 54 | 2,736 | 1.6 TB | Soil water repellency microbes |
| `nmdc:sty-11-dcqce727` | 59 | 6,503 | 3.6 TB | East River watershed bulk soil |
| `nmdc:sty-11-hdd4bf83` | 61 | 3,733 | 569 GB | Colonization resistance (Candida) |
| `nmdc:sty-11-aygzgv51` | 85 | 4,330 | 670 GB | Riverbed sediment (Columbia River) |
| `nmdc:sty-11-547rwq94` | 679 | 7,927 | 379 GB | (unnamed study) |

### Recommended: `nmdc:sty-11-1t150432` (Populus rhizosphere)

**Why this study:**
- Smallest complete study (29 biosamples)
- Ecologically interesting: root/rhizosphere/bulk soil from Populus trees
- Has all workflow types: ReadQC, Assembly, Annotation, Taxonomy, MAGs
- DOE-relevant (bioenergy feedstock)

**Why not the full 4.1 TB:**
Even the smallest complete study is TB-scale because of raw reads, BAM files, and
full taxonomic classification outputs. For a BERDL demo, we want **metadata + summaries only**.

## What to Ingest (Not Raw Data)

For a "complete story" dataset under ~1 GB:

| Layer | What | Source | Approx Size |
|---|---|---|---|
| Study metadata | Study description, PI, DOIs | MongoDB `study_set` | KB |
| Biosample metadata | MIxS fields, ENVO terms, collection info | MongoDB `biosample_set` | KB |
| Sequencing metadata | Instrument, library, run info | MongoDB `data_generation_set` | KB |
| Assembly stats | N50, contig count, coverage | DataObject: "Assembly Coverage Stats" | KB/sample |
| CheckM stats | Completeness, contamination per MAG | DataObject: "CheckM Statistics" | KB/sample |
| GTDBTK summaries | Taxonomic assignment of MAGs | DataObject: "GTDBTK Bacterial/Archaeal Summary" | KB/sample |
| Annotation counts | KO, EC, COG functional profiles | DataObject: "Annotation Statistics" | KB/sample |
| Functional Annotation GFF | Full gene annotations | DataObject: "Functional Annotation GFF" | ~100 MB/sample |

**Skip**: Raw reads, Filtered reads, BAMs, full Kraken/Centrifuge classification files (these are 90%+ of the size).

## How to Get the Data

### Metadata (from API)

```bash
# Study
curl -s "https://api.microbiomedata.org/studies/nmdc:sty-11-1t150432"

# Biosamples
curl -s "https://api.microbiomedata.org/nmdcschema/biosample_set?filter=%7B%22associated_studies%22%3A%22nmdc:sty-11-1t150432%22%7D&max_page_size=100"

# All data objects for this study (returns biosample → data_object mapping)
curl -s "https://api.microbiomedata.org/data_objects/study/nmdc:sty-11-1t150432"

# Linked instances from a specific biosample
curl -s "https://api.microbiomedata.org/nmdcschema/linked_instances?ids=nmdc:bsm-XXXXX&types=nmdc:DataObject&hydrate=true"
```

### Data Files (from HTTPS)

DataObject documents contain a `url` field pointing to:
```
https://data.microbiomedata.org/data/{data_gen_id}/{workflow_id}/{filename}
```

Filter data objects by `data_object_type` to download only summary files.

### Ingestion into BERDL

1. Download summary files → convert to parquet (or use as TSV with schema file)
2. Use `/berdl-ingest` skill: bronze upload to MinIO, then Spark Delta table creation
3. Target tenant: `nmdc_arkin` (existing NMDC tenant) or new tenant

## Already in BERDL

Per `~/Desktop/markdown/berdl-nmdc-database-landscape-2026-03-24.md`:
- `nmdc_flattened_biosamples` — 14,938 rows (all studies)
- `nmdc_ncbi_biosamples` — 756M rows (NCBI cross-reference)
- `nmdc_func_annot_freshwater_rivers` — 2.56M rows (one study's functional annotations)
- `nmdc_arkin` — contig taxonomies (3.98B), embeddings, reference ontologies

**Gap**: No assembly stats, CheckM, GTDBTK, or per-study annotation summaries in the lakehouse yet.

## Alternative: Start With Just Metadata

If even summary files are too much for a first pass, ingest just the MongoDB metadata
(study + biosamples + data_generation + workflow_execution documents as flattened parquet).
This would be under 10 MB and would let us query the full provenance chain in Spark SQL.

## Authors

- Mark Andrew Miller (ORCID: [0000-0001-9076-6066](https://orcid.org/0000-0001-9076-6066)), Lawrence Berkeley National Laboratory
