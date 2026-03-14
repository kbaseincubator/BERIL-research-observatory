# Structural Biology Data Collection

Status: **In development**. All 4 milestones complete 2026-03-14. No tables ingested yet.

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
- [x] Milestone 2: Phenix installation, automated pipelines, SLURM templates, tests
- [x] Milestone 3: Human-in-the-loop refinement management, convergence detection, Delta Lake export
- [x] Milestone 4: Cross-project intelligence, batch validation, figure generation

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/install_phenix.sh` | Install Phenix via conda on NERSC Perlmutter |
| `scripts/retrieve_alphafold.py` | Retrieve AlphaFold structures from EBI API |
| `scripts/parse_validation.py` | Parse Phenix validation output into structured JSON |
| `scripts/run_pipeline.py` | Pipeline orchestrator (retrieve, validate, xray, cryoem, refine, process, accept, converge, finalize, status) |
| `scripts/refinement_state.py` | Project lifecycle state machine (new → xtriage → ... → complete) |
| `scripts/generate_scripts.py` | Coot/PyMOL/ChimeraX visualization script generator |
| `scripts/cycle_manager.py` | Post-refinement workflow, convergence detection, finalization |
| `scripts/export_tables.py` | Delta Lake TSV export matching ingestion config schema |
| `scripts/batch_validate.py` | Batch validation of AlphaFold/PDB structures |
| `scripts/strategy_advisor.py` | Resolution-based refinement strategy recommendations |
| `scripts/generate_figures.py` | Publication figure generation (pLDDT, convergence, quality summary) |
| `scripts/project_dashboard.py` | Multi-project status dashboard with stale detection |
| `scripts/structural_biology.json` | BERDL ingestion config for 4 Delta Lake tables |
| `scripts/slurm_templates/refine.sh` | SLURM template for phenix.refine (4h, 8 CPUs) |
| `scripts/slurm_templates/real_space_refine.sh` | SLURM template for phenix.real_space_refine (4h, 8 CPUs) |
| `scripts/slurm_templates/phaser.sh` | SLURM template for phenix.phaser (4h, 32 CPUs) |
| `scripts/slurm_templates/autobuild.sh` | SLURM template for phenix.autobuild (8h, 32 CPUs) |
| `scripts/slurm_templates/map_to_model.sh` | SLURM template for phenix.map_to_model (24h, 32 CPUs) |
| `scripts/slurm_templates/predict_and_build.sh` | SLURM template for phenix.predict_and_build (48h, 32 CPUs) |

## Tests

Run with: `module load python && python3 -m unittest discover -s tests -v`

| Test | What It Tests |
|------|--------------|
| `tests/test_retrieve_alphafold.py` | EBI API retrieval, file validation, pLDDT parsing |
| `tests/test_parse_validation.py` | Phenix output parsing with mock log files |
| `tests/test_slurm_templates.py` | Template structure, SBATCH directives, parameterization |
| `tests/test_run_pipeline.py` | Project state management, provenance, cycle tracking |
| `tests/test_refinement_state.py` | State transitions, validation, advance logic |
| `tests/test_generate_scripts.py` | Coot/PyMOL/ChimeraX script generation |
| `tests/test_cycle_manager.py` | Convergence detection, model acceptance |
| `tests/test_export_tables.py` | TSV export format, schema consistency |
| `tests/test_batch_validate.py` | Batch processing, summary generation |
| `tests/test_strategy_advisor.py` | Static recommendations, resolution matching, history |
| `tests/test_generate_figures.py` | Figure generation with mock data |
| `tests/test_project_dashboard.py` | Project scanning, stale detection, formatting |
