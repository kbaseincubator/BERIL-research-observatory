# Structural Biology Schema (`kescience_structural_biology`)

Database: `kescience_structural_biology`
Location: On-prem Delta Lakehouse (BERDL)
Tenant: kescience
Last Updated: 2026-03-13
Verified: Schema designed, tables not yet ingested

## Overview

Structural biology project metadata and refinement history. Tracks structure determination projects (X-ray crystallography, cryo-EM), refinement cycle metrics, standalone validation reports, and retrieved AlphaFold structure files. Designed to support cross-project learning — the phenix agent queries historical refinement data to recommend parameters for new projects.

**Database**: `kescience_structural_biology`
**Source**: Phenix agent workflow outputs
**Scale**: Grows with usage (starts empty)

## Tables

| Table | Rows | Description |
|-------|------|-------------|
| `structure_projects` | 0 (new) | One row per structure determination project |
| `refinement_cycles` | 0 (new) | Full refinement history with metrics per cycle |
| `validation_reports` | 0 (new) | Standalone MolProbity validations (experimental + AlphaFold) |
| `alphafold_structures` | 0 (new) | Retrieved AlphaFold structure file metadata |

## Key Table Schemas

### structure_projects

One row per structure determination project. Created when a user starts `/phenix xray` or `/phenix cryoem`.

| Column | Type | Description |
|--------|------|-------------|
| `project_id` | STRING | Unique project identifier (e.g., `struct_20260314_ecoli_dhfr`) — primary key |
| `uniprot_accession` | STRING | UniProt accession of the target protein; links to `kescience_alphafold.alphafold_entries` |
| `pdb_id` | STRING | PDB accession if deposited; NULL for in-progress projects |
| `method` | STRING | Structure determination method: `xray`, `cryo_em`, `neutron` |
| `resolution` | FLOAT | Final resolution in Angstroms |
| `space_group` | STRING | Crystallographic space group (X-ray only; NULL for cryo-EM) |
| `status` | STRING | Project status: `in_progress`, `completed`, `deposited` |
| `created_date` | STRING | Project start date (YYYY-MM-DD) |
| `completed_date` | STRING | Completion date (YYYY-MM-DD); NULL if in progress |

### refinement_cycles

Full refinement history. One row per refinement iteration. Enables cross-project queries like "what strategy works best at 3.0 A resolution?"

| Column | Type | Description |
|--------|------|-------------|
| `project_id` | STRING | FK to `structure_projects.project_id` |
| `cycle_number` | INT | Refinement iteration number (1-based) |
| `r_work` | FLOAT | R-work after this cycle (X-ray); NULL for cryo-EM |
| `r_free` | FLOAT | R-free after this cycle (X-ray); NULL for cryo-EM |
| `r_gap` | FLOAT | R-free minus R-work (overfitting indicator); NULL for cryo-EM |
| `map_model_cc` | FLOAT | Map-model correlation coefficient (cryo-EM); NULL for X-ray |
| `molprobity_score` | FLOAT | MolProbity overall score |
| `ramachandran_favored` | FLOAT | Percentage of residues in Ramachandran favored region |
| `ramachandran_outliers` | FLOAT | Percentage of Ramachandran outliers |
| `clash_score` | FLOAT | All-atom clashscore |
| `rotamer_outliers` | FLOAT | Percentage of rotamer outliers |
| `refinement_strategy` | STRING | Strategy used (e.g., `individual_sites+individual_adp+tls`) |
| `parameters_json` | STRING | JSON string of key Phenix parameters used |
| `model_path` | STRING | MinIO path to model PDB at this cycle |
| `notes` | STRING | Human or agent notes on what changed this cycle |
| `timestamp` | STRING | ISO 8601 timestamp of when this cycle was run |

### validation_reports

Standalone validations, including AlphaFold-only validations (no experimental data). Enables batch quality assessment across proteins.

| Column | Type | Description |
|--------|------|-------------|
| `uniprot_accession` | STRING | Protein identifier |
| `source` | STRING | Model source: `alphafold`, `experimental`, `refined` |
| `molprobity_score` | FLOAT | MolProbity overall score |
| `ramachandran_favored` | FLOAT | Percentage Ramachandran favored |
| `ramachandran_outliers` | FLOAT | Percentage Ramachandran outliers |
| `clash_score` | FLOAT | All-atom clashscore |
| `rotamer_outliers` | FLOAT | Percentage rotamer outliers |
| `cbeta_deviations` | INT | Number of C-beta deviations |
| `report_path` | STRING | MinIO path to full validation report JSON |
| `model_path` | STRING | MinIO path to the validated model |
| `validation_date` | STRING | Date validation was run (YYYY-MM-DD) |

### alphafold_structures

Metadata for AlphaFold structures retrieved from EBI and stored in MinIO. Links to `kescience_alphafold.alphafold_entries` for MSA depth and residue range.

| Column | Type | Description |
|--------|------|-------------|
| `uniprot_accession` | STRING | UniProt accession — primary key; joins to `kescience_alphafold.alphafold_entries` |
| `pdb_path` | STRING | MinIO path to retrieved PDB file |
| `cif_path` | STRING | MinIO path to retrieved mmCIF file |
| `pae_path` | STRING | MinIO path to PAE (Predicted Aligned Error) JSON |
| `n_residues` | INT | Total residues in the model |
| `n_domains` | INT | Number of domains identified after `process_predicted_model` (0 if not processed) |
| `mean_plddt` | FLOAT | Mean pLDDT score across all residues |
| `retrieval_date` | STRING | Date structure was fetched from EBI (YYYY-MM-DD) |

## Cross-Collection Links

| Target Collection | Join Key | Notes |
|-------------------|----------|-------|
| `kescience_alphafold.alphafold_entries` | `uniprot_accession` | AlphaFold entry metadata (residue range, model version) |
| `kescience_alphafold.alphafold_msa_depths` | `uniprot_accession` | MSA depth (prediction confidence proxy) |
| `kbase_ke_pangenome.bakta_annotations` | `REPLACE(uniref100, 'UniRef100_', '')` → `uniprot_accession` | Link pangenome clusters to structural data |
| `kbase_ke_pangenome.bakta_db_xrefs` | Via UniRef100 accession | Alternative join path |

## Example Queries

### Find all completed projects with their final R-factors

```sql
SELECT sp.project_id, sp.method, sp.resolution,
       rc.r_work, rc.r_free, rc.molprobity_score
FROM kescience_structural_biology.structure_projects sp
JOIN kescience_structural_biology.refinement_cycles rc
  ON rc.project_id = sp.project_id
  AND rc.cycle_number = (
    SELECT MAX(rc2.cycle_number)
    FROM kescience_structural_biology.refinement_cycles rc2
    WHERE rc2.project_id = sp.project_id
  )
WHERE sp.status = 'completed'
ORDER BY sp.resolution;
```

### Best refinement strategy by resolution range

```sql
SELECT
  CASE
    WHEN sp.resolution < 2.0 THEN '< 2.0 A'
    WHEN sp.resolution < 3.0 THEN '2.0-3.0 A'
    WHEN sp.resolution < 4.0 THEN '3.0-4.0 A'
    ELSE '> 4.0 A'
  END AS resolution_bin,
  rc.refinement_strategy,
  AVG(rc.r_free) AS avg_rfree,
  AVG(rc.molprobity_score) AS avg_molprobity,
  COUNT(*) AS n_projects
FROM kescience_structural_biology.refinement_cycles rc
JOIN kescience_structural_biology.structure_projects sp
  ON sp.project_id = rc.project_id
WHERE rc.cycle_number = (
    SELECT MAX(rc2.cycle_number)
    FROM kescience_structural_biology.refinement_cycles rc2
    WHERE rc2.project_id = rc.project_id
)
GROUP BY 1, rc.refinement_strategy
ORDER BY 1, avg_rfree;
```

### AlphaFold structures with validation data

```sql
SELECT afs.uniprot_accession, afs.mean_plddt, afs.n_residues,
       vr.molprobity_score, vr.ramachandran_favored, vr.clash_score
FROM kescience_structural_biology.alphafold_structures afs
LEFT JOIN kescience_structural_biology.validation_reports vr
  ON vr.uniprot_accession = afs.uniprot_accession
  AND vr.source = 'alphafold'
ORDER BY afs.mean_plddt DESC
LIMIT 20;
```

### Link pangenome annotations to structural biology projects

```sql
SELECT b.gene_cluster_id, b.product, b.species_id,
       sp.project_id, sp.method, sp.resolution, sp.status
FROM kbase_ke_pangenome.bakta_annotations b
JOIN kescience_structural_biology.structure_projects sp
  ON sp.uniprot_accession = REPLACE(b.uniref100, 'UniRef100_', '')
WHERE b.uniref100 IS NOT NULL
LIMIT 20;
```

## MinIO Storage Layout

```
s3a://cdm-lake/tenant-general-warehouse/kescience/structural-biology/
├── alphafold-structures/{accession}/
│   ├── model.pdb
│   ├── model.cif
│   └── pae.json
└── projects/{project_id}/
    ├── input/           # Experimental data (MTZ, MRC, FASTA)
    ├── cycles/          # Refinement cycle outputs
    ├── scripts/         # Visualization scripts (Coot, PyMOL, ChimeraX)
    ├── figures/         # Generated figures
    ├── final/           # Final depositable model
    └── provenance.jsonl # Action log
```

## Known Limitations

- Tables start empty — populated as structural biology projects are conducted
- Cross-project queries become useful only after multiple projects accumulate data
- `refinement_cycles` has nullable X-ray metrics (r_work, r_free) for cryo-EM projects and nullable cryo-EM metrics (map_model_cc) for X-ray projects
- `parameters_json` is a JSON string column, not a structured type — queries into parameters require JSON parsing
- AlphaFold structure files on MinIO are copies of EBI data; they may become outdated if EBI releases new model versions

## Changelog

- **2026-03-13**: Initial schema design (4 tables). Tables not yet ingested — schema ready for first project.
