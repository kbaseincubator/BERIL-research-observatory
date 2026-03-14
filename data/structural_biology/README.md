# Structural Biology Data Collection

Status: **In development**. Skill framework created 2026-03-13. No tables ingested yet.

## What This Is

Structural biology project metadata and workflow outputs for BERDL. Managed by the `/phenix` agent skill, which orchestrates Phenix structural biology tools for X-ray crystallography and cryo-EM structure determination.

## Database

**Database**: `kescience_structural_biology`

| Table | Rows | Description |
|-------|------|-------------|
| `structure_projects` | 0 | One row per structure determination project |
| `refinement_cycles` | 0 | Full refinement history with metrics per cycle |
| `validation_reports` | 0 | MolProbity validations (experimental + AlphaFold) |
| `alphafold_structures` | 0 | Retrieved AlphaFold structure file metadata |

Schema documentation: [docs/schemas/structural_biology.md](../../docs/schemas/structural_biology.md)

## MinIO Storage

```
s3a://cdm-lake/tenant-general-warehouse/kescience/structural-biology/
├── alphafold-structures/{accession}/     # Retrieved AF structures
└── projects/{project_id}/               # Structure determination projects
```

## Agent Skill

The `/phenix` skill is at `.claude/skills/phenix/SKILL.md`. It provides:

| Command | Purpose |
|---------|---------|
| `/phenix retrieve <accession>` | Retrieve AlphaFold structures from EBI |
| `/phenix validate <model>` | Run MolProbity validation |
| `/phenix xray <data.mtz> <seq.fa>` | X-ray structure determination |
| `/phenix cryoem <map.mrc> <seq.fa>` | Cryo-EM structure determination |
| `/phenix refine` | Run next refinement cycle |
| `/phenix inspect` | Generate visualization scripts |
| `/phenix status` | Show project status |

## Cross-Collection Links

- **AlphaFold metadata**: `kescience_alphafold` (241M entries) — join on `uniprot_accession`
- **Pangenome annotations**: `kbase_ke_pangenome.bakta_annotations` (132.5M rows) — join via UniRef100 accession

## Software Requirements

| Software | Purpose | License |
|----------|---------|---------|
| Phenix | Structure determination + refinement | Free academic (registration required) |
| Coot | Manual model rebuilding (user's local machine) | GPLv3 |
| PyMOL | Publication figures | BSD / Schrodinger |
| ChimeraX | Map visualization (user's local machine) | Free academic |

## Implementation Roadmap

- [x] Milestone 1: Skill framework, schema design, AlphaFold retrieval, validation
- [ ] Milestone 2: X-ray and cryo-EM automated pipelines, SLURM templates
- [ ] Milestone 3: Human-in-the-loop refinement management, provenance capture
- [ ] Milestone 4: Cross-project intelligence, batch validation, figure generation

## Scripts

| Script | Purpose |
|--------|---------|
| _(none yet)_ | Ingestion scripts will be added when tables are first populated |
