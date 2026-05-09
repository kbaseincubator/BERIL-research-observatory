# Data Provenance

CSV files in this directory are gitignored due to size. They are derived from
`kescience_mgnify` (via JupyterHub Spark) and the ENA Portal API (via NB01).

## Populating `data/` from the shared store

```bash
EXP="/home/hmacgregor/BERIL-research-observatory/projects/misc_exploratory/exploratory/data"
DEST="/home/hmacgregor/BERIL-research-observatory/projects/metal_resistance_global_biogeography/data"

cp "$EXP/final_mags_geospatial_traits.csv" "$DEST/"
cp "$EXP/ena_sample_coordinates.csv"       "$DEST/"
```

## File descriptions

| File | Description | Source |
|---|---|---|
| `final_mags_geospatial_traits.csv` | MAGs with lat/lon, `n_metal_types`, `biome_name`, `genome_id`, optionally `sample_accession` | `kescience_mgnify` + ENA API via NB01 |
| `ena_sample_coordinates.csv` | ENA sample records with lat/lon coordinates (24,511 samples; 16,964 valid pairs) | ENA Portal API batch POST via NB01 |

## Note

The NB02 spatial analysis script reads from the shared store by default. Set
`BERDL_DATA_DIR` to point to this directory once files are copied:

```bash
export BERDL_DATA_DIR="$DEST"
python scripts/nb02_spatial_analysis.py
```
