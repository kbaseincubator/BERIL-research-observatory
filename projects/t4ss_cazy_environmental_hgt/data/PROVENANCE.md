# Data Provenance

CSV files in this directory are gitignored (`.gitignore` pattern: `projects/*/data/**/*.csv`)
but should be present locally. Populate by copying from the shared misc_exploratory data store:

```bash
REPO=/home/hmacgregor/BERIL-research-observatory
SRC=$REPO/projects/misc_exploratory/exploratory/data
DST=$REPO/projects/t4ss_cazy_environmental_hgt/data

cp $SRC/phylogeny/Detected_HGT_Events.csv        $DST/
cp $SRC/phylogeny/Normalized_Detected_HGT_Events.csv $DST/
cp $SRC/GT2_neighborhood_signatures.csv           $DST/
cp $SRC/phylogeny/tree_metadata.csv               $DST/
cp $SRC/Cytoscape_Edge_List.csv                   $DST/
cp $SRC/Cytoscape_Node_Table.csv                  $DST/
```

## File descriptions

| File | Rows | Description |
|------|------|-------------|
| `Detected_HGT_Events.csv` | 77 | Raw HGT events from GT2 gene tree; columns: Clade_ID, Total_Genes, Syntenic_Percentage, Distinct_Phyla, Max_Divergence, Phyla_Involved |
| `Normalized_Detected_HGT_Events.csv` | 32 | Cross-phylum events (≥2 distinct phyla) after normalisation |
| `GT2_neighborhood_signatures.csv` | 386 | Contig neighbourhoods for GT2-T4SS proximal genomes; columns: genome_id, contig_id, neighborhood_funcs |
| `tree_metadata.csv` | — | Phylum and biome annotations for 1,096 genomes in the GT2 gene tree |
| `Cytoscape_Edge_List.csv` | 3,100 | Bipartite gene↔genome network edges for Cytoscape visualisation |
| `Cytoscape_Node_Table.csv` | — | Node metadata (mobility quotient) for Cytoscape |
