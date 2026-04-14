# Instructions: Flatten NMDC Workflow Collections for BERDL Ingestion

## Goal

Extend `flatten_nmdc_collections.py` in `~/gitrepos/external-metadata-awareness/` to flatten
three additional NMDC MongoDB collections: `data_generation_set`, `workflow_execution_set`,
and `data_object_set`. These contain the provenance chain that shows *how* NMDC data was
produced — exactly where OBI terms should be used but currently aren't.

This is for the OBI meeting on Monday 2026-04-07. The flattened tables will be ingested into
the BERDL lakehouse to demonstrate the gap between NMDC's internal type system and OBI.

## Why These Collections

Study and biosample metadata is already in the lakehouse. The missing layer is:

```
data_generation_set (sequencing events)
  → workflow_execution_set (computational pipelines, via was_informed_by)
    → data_object_set (output files, via was_generated_by)
```

These documents have fields like `type: nmdc:MagsAnalysis` and `processing_institution: JGI`
where OBI terms could add cross-project interoperability.

## Document Structures (from API, 2026-04-03)

### data_generation_set

```json
{
  "id": "nmdc:dgns-11-3ajjfh90",
  "type": "nmdc:NucleotideSequencing",
  "name": "Populus rhizosphere ... - Rhizosphere MetaG P. deltoides SRZDD2",
  "analyte_category": "metagenome",
  "associated_studies": ["nmdc:sty-11-1t150432"],
  "has_input": ["nmdc:bsm-11-7v0s5h20"],
  "instrument_used": ["nmdc:inst-14-nn4b6k72"],
  "processing_institution": "JGI",
  "gold_sequencing_project_identifiers": ["gold:Gp0116341"],
  "insdc_bioproject_identifiers": ["bioproject:PRJNA375667"],
  "ncbi_project_name": "...",
  "principal_investigator": {
    "email": "pelletierda@ornl.gov",
    "has_raw_value": "Dale Pelletier",
    "name": "Dale Pelletier",
    "type": "nmdc:PersonValue"
  },
  "provenance_metadata": {
    "type": "nmdc:ProvenanceMetadata",
    "add_date": "2015-06-23T00:00:00Z",
    "mod_date": "2025-05-05T00:00:00Z"
  }
}
```

**Flattening notes:**
- `associated_studies`, `has_input`, `instrument_used`, `gold_sequencing_project_identifiers`,
  `insdc_bioproject_identifiers` are arrays → pipe-separate
- `principal_investigator` is a dict → flatten to `principal_investigator_name`,
  `principal_investigator_email`, etc. (same pattern as ControlledTermValue)
- `provenance_metadata` is a dict → flatten to `provenance_metadata_add_date`, etc.
- `type` should be KEPT (not skipped) for this collection — it's the workflow type
  (e.g., `nmdc:NucleotideSequencing`) and is the key field for OBI mapping

### workflow_execution_set

```json
{
  "id": "nmdc:wfmag-11-002wf438.1",
  "type": "nmdc:MagsAnalysis",
  "name": "Metagenome Assembled Genomes Analysis for ...",
  "has_input": ["nmdc:dobj-11-zdrpgv45", ...],
  "has_output": ["nmdc:dobj-11-1218k979", ...],
  "processing_institution": "NMDC",
  "git_url": "https://github.com/microbiomedata/metaMAGs",
  "started_at_time": "2025-12-19 15:59:45",
  "ended_at_time": "2025-12-19 17:27:03",
  "was_informed_by": ["nmdc:omprc-11-39q8ar32"],
  "execution_resource": "NERSC-Perlmutter",
  "version": "v1.3.16",
  "binned_contig_num": 12040,
  "input_contig_num": 536294,
  "mags_list": [{ "bin_name": "bins.25", "completeness": 94.06, ... }, ...]
}
```

**Flattening notes:**
- `has_input`, `has_output`, `was_informed_by` are arrays of IDs → pipe-separate
- `mags_list` is a complex nested array → either stringify as JSON or extract to a
  separate `flattened_workflow_execution_mags` collection (preferred, same pattern as
  `extract_associated_dois`)
- `type` should be KEPT — it's `nmdc:MagsAnalysis`, `nmdc:MetagenomeAnnotation`, etc.
- Scalar fields (`git_url`, `version`, `execution_resource`, `started_at_time`, etc.)
  flatten directly
- `binned_contig_num`, `input_contig_num` etc. are workflow-type-specific numeric fields —
  keep as-is

### data_object_set

```json
{
  "id": "nmdc:dobj-11-00017y47",
  "type": "nmdc:DataObject",
  "name": "nmdc_wfmgan-11-yq9z3n21.1_proteins.faa",
  "description": "FASTA Amino Acid File for ...",
  "data_category": "processed_data",
  "data_object_type": "Annotation Amino Acid FASTA",
  "file_size_bytes": 85905216,
  "md5_checksum": "39e6b7faa4e79fd903383771583b7c4b",
  "url": "https://data.microbiomedata.org/data/nmdc:dgns-11-1enrtv50/...",
  "was_generated_by": "nmdc:wfmgan-11-yq9z3n21.1"
}
```

**Flattening notes:**
- Almost entirely flat already — no complex nesting
- `type` is always `nmdc:DataObject` (less interesting than the others)
- Keep `data_object_type` (e.g., "CheckM Statistics") — this is the field that classifies
  what kind of output it is
- `url` contains the download URL
- `was_generated_by` links to a WorkflowExecution ID

## Implementation Plan

### Option A: Extend flatten_nmdc_collections.py (preferred)

Add to `main()` after the biosample processing block:

1. **Fetch and flatten data_generation_set:**
   - Keep `type` field (don't skip it — rename to `nmdc_type` to avoid confusion)
   - Flatten `principal_investigator` dict
   - Flatten `provenance_metadata` dict
   - Pipe-separate array fields
   - No ontology enhancement needed (no env fields)

2. **Fetch and flatten workflow_execution_set:**
   - Keep `type` field (rename to `nmdc_type`)
   - Pipe-separate `has_input`, `has_output`, `was_informed_by`
   - Extract `mags_list` to separate `flattened_workflow_execution_mags` collection
   - Keep numeric fields as-is
   - No ontology enhancement needed

3. **Fetch and flatten data_object_set:**
   - Almost flat already — minimal transformation
   - Keep all fields

4. **Add to NMDC_FLATTENED_COLLECTIONS list:**
   ```python
   NMDC_FLATTENED_COLLECTIONS = \
       flattened_biosample \
       ...existing... \
       flattened_data_generation \
       flattened_workflow_execution \
       flattened_workflow_execution_mags \
       flattened_data_object
   ```

### Option B: Fetch from API instead of MongoDB

If local MongoDB doesn't have these collections (check first), fetch from the API:

```bash
# data_generation_set (for one study)
curl -s "https://api.microbiomedata.org/nmdcschema/data_generation_set?\
filter=%7B%22associated_studies%22%3A%22nmdc%3Asty-11-1t150432%22%7D&max_page_size=999"

# workflow_execution_set (need to chain from data_generation IDs)
# Use linked_instances endpoint per biosample, or fetch all and filter

# data_object_set (use the study endpoint)
curl -s "https://api.microbiomedata.org/data_objects/study/nmdc:sty-11-1t150432"
```

Note: Option B is study-scoped. Option A from MongoDB gets all studies at once.

### Key Difference from Biosample/Study Flattening

The `type` field matters here. For biosamples and studies, `type` is always the same
(`nmdc:Biosample`, `nmdc:Study`) so the script skips it. For workflow collections,
`type` varies and carries semantic meaning:

| Collection | type values |
|---|---|
| data_generation_set | `nmdc:NucleotideSequencing`, `nmdc:MassSpectrometry`, etc. |
| workflow_execution_set | `nmdc:MagsAnalysis`, `nmdc:MetagenomeAnnotation`, `nmdc:ReadQcAnalysis`, `nmdc:MetagenomeAssembly`, `nmdc:ReadBasedTaxonomyAnalysis`, etc. |
| data_object_set | always `nmdc:DataObject` |

**The `type` field on workflow_execution_set is THE field where OBI terms should go.**
Currently it uses NMDC's own type system. The OBI meeting story is: "here's what we use
now, and here's the OBI planned process term that could replace or augment it."

## Testing

1. Check if local MongoDB has these collections:
   ```bash
   mongosh mongodb://localhost:27017/nmdc --quiet --eval \
     "db.getCollectionNames().filter(n => n.match(/data_gen|workflow|data_obj/))"
   ```

2. If yes, run the extended script locally and verify the flattened collections

3. Export to parquet:
   ```bash
   make -f Makefiles/nmdc_metadata.Makefile export-flattened-parquet
   ```

4. Ingest to BERDL via `/berdl-ingest` on the notebook server

## For the OBI Meeting

Once the flattened `workflow_execution` table is in the lakehouse, you can run a Spark
query like:

```sql
SELECT nmdc_type, COUNT(*) as cnt
FROM nmdc_flattened_workflow_executions.flattened_workflow_execution
GROUP BY nmdc_type
ORDER BY cnt DESC
```

And show: "Here are 24,698 workflow executions using NMDC's own type system. OBI has
`OBI:0200000` (data transformation) but no subtypes for metagenome assembly, genome
binning, or taxonomic classification. We're proposing 5-7 lightweight terms to fill
this gap."

## Scope Warning

Don't try to flatten ALL of workflow_execution_set (24,698 documents) if going through
the API — it will be slow. For the Monday demo, just the Populus study
(`nmdc:sty-11-1t150432`, 29 biosamples) is enough. From MongoDB, all studies is fine.
