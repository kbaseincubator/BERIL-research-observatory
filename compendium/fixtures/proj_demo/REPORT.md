# Report: Acinetobacter baylyi ADP1 Demo Study

## Key Findings

### 1. Acinetobacter baylyi ADP1 shows strong fitness under quinate
The organism grows robustly on quinate as a sole carbon source. (Notebook: 01_demo.ipynb)

### 2. Gene K00845 is essential for glucose metabolism
Knockout of K00845 abolishes growth on glucose, implicating it in early glycolysis.

### 3. COG0791 is conserved across the pangenome
Found in 14 of 14 genomes examined.

## Results

### Database Structure
The dataset integrates six modalities.

## Interpretation

### Novel Contribution
First integrated view for ADP1.

### Limitations
Single-condition fitness.

## Data

### Sources
- `kescience_fitnessbrowser` fitness table
- BERDL collection `kbase_ke_pangenome`

### Generated Data
- `data/fitness_summary.tsv`

## Supporting Evidence

### Notebooks
- 01_demo.ipynb
- 02_pangenome.ipynb

### Figures
- figures/fitness_overview.png

## Future Directions

- Test quinate fitness across related Acinetobacter species.
- Validate K00845 essentiality with a clean deletion.

## References

- PMID:12345678
- PMID:23456789
