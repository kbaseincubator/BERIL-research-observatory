# Data Provenance

CSV files in this directory are gitignored due to size. They are derived from
`arkinlab_microbeatlas` and `kbase_ke_pangenome` via JupyterHub Spark (NB01–NB04)
and stored in the shared exploratory data store.

## Populating `data/` from the shared store

```bash
EXP="/home/hmacgregor/BERIL-research-observatory/projects/misc_exploratory/exploratory/data"
DEST="/home/hmacgregor/BERIL-research-observatory/projects/soil_metal_functional_genomics/data"

cp "$EXP/mgnify_geochemistry_mags.csv" "$DEST/"
cp "$EXP/mgnify_mag_metal_traits.csv"  "$DEST/"
```

## File descriptions

| File | Description | Source |
|---|---|---|
| `mgnify_geochemistry_mags.csv` | Sample-level soil geochemistry (metal concentrations) linked to MAG IDs | `arkinlab_microbeatlas` sample_metadata via NB01 |
| `mgnify_mag_metal_traits.csv` | MAG-level COG annotation counts and metal trait flags | `kbase_ke_pangenome` bakta_amr via NB01 |

## Intermediate outputs

Once NB01–NB04 have been run, export Spearman ρ values and db-RDA residuals as
local CSVs so that NB05 (validation) can run without Spark re-execution:

- `data/spearman_rho_all_cog_metal.csv` — ρ and FDR for all 3,915 COG × metal pairs
- `data/dbrda_residuals.csv` — residuals from conditioned db-RDA model

These intermediate files are also gitignored and should be regenerated from notebooks
or obtained from the project collaborator.
