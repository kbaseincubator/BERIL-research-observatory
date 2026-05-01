# Lanthanide Methylotrophy Atlas

## Research Question
Across BERDL's 293K-genome pangenome, what is the phylogenomic distribution and cassette-completeness of the lanthanide-dependent methanol/ethanol oxidation system (xoxF / xoxJ / PQQ / lanmodulin), and does its presence correspond to environments containing rare earth elements?

## Status
Complete — see [Report](REPORT.md) for findings. **H1 strongly supported** (xoxF:mxaF = 18.9 : 1, p = 7.6 × 10⁻²² vs 10:1 threshold). **H2 partially supported** — soil/sediment OR=1.92 (p_BH=6e-39); ree_impacted descriptively elevated (n=37, OR=3.51, p_BH=0.082). **H3a strongly supported** (lanmodulin 100% in target clades, p=9.8e-7); **H3b not formally supported** at the pre-registered 80% threshold (xoxF co-occurrence 79.0%, p=0.65).

## Data Collections
- `kbase_ke_pangenome` — eggnog_mapper_annotations, bakta_annotations, gene, gene_genecluster_junction, gene_cluster, genome, gtdb_taxonomy_r214v1, ncbi_env
- `kescience_bacdive` — culture_condition, strain, metabolite_utilization

## Overview
The lanthanide-dependent methanol dehydrogenase XoxF (Pol et al., *Nature*, 2014) and the REE-binding protein lanmodulin (Cotruvo et al., *JACS*, 2018) are central to bacterial use of rare earth elements as enzyme cofactors — yet existing surveys rarely span more than a few hundred genomes. This project leverages BERDL's pangenome (293K genomes, 27K species) to deliver the first large-scale atlas of the lanthanide-MDH cassette, asking three questions: (1) how dominant is xoxF (KEGG K00114) relative to the calcium-dependent mxaF (K14028); (2) where is the *full cassette* (xoxF + xoxJ + ≥1 PQQ-biosynthesis gene) found, and is it enriched in REE-impacted environments via the `ncbi_env` metadata and AlphaEarth embeddings; (3) is bakta-validated lanmodulin restricted to the canonical α-Proteobacterial methylotroph clades. The 37 MAGs from REE-AMD river-water samples in the pangenome serve as a small-N environmental anchor.

This project closes the **"Rare Earth Elements (Zero Coverage)" Priority 2 future direction** identified in the `metal_fitness_atlas` REPORT.

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence (TBD)

## Reproduction

**Prerequisites**:
- BERDL JupyterHub on-cluster access (NB01, NB02, NB04, NB06, NB07 query Spark directly via `get_spark_session()`)
- Python 3.10+ with packages in `requirements.txt`
- `KBASE_AUTH_TOKEN` in `.env` at repo root (auto-populated on JupyterHub)

**Pipeline** (run notebooks sequentially; each commits saved outputs in place):

1. `notebooks/01_marker_calibration.ipynb` — Spark queries for eggNOG and bakta marker presence per genome (~10 min). Produces `data/genome_marker_matrix.csv` and the lanmodulin true/false-positive taxonomy CSVs.
2. `notebooks/02_phylogenomic_atlas.ipynb` — Spark join of marker matrix with full GTDB taxonomy; phylum/family/genus rollups (~5 min). Produces `data/marker_taxonomy_rollup_*.csv` and `data/h1_xoxF_vs_mxaF_per_phylum.csv`.
3. `notebooks/03_h1_formal_test.ipynb` — Local pandas + scipy; BH-FDR correction, global ratio with 95% CI (~30 sec).
4. `notebooks/04_environmental_association.ipynb` — Spark for `ncbi_env` text mining + biosample→genome join; local Fisher's exact tests (~5 min).
5. `notebooks/05_lanmodulin_h3_test.ipynb` — Local; H3a/H3b binomial tests (~10 sec).
6. `notebooks/06_ree_amd_case_study.ipynb` — Spark for bakta product enrichment in 37 REE-AMD MAGs (~5 min).
7. `notebooks/07_pqq_supply_asymmetry.ipynb` — Spark for bakta PQQ cross-check on the xoxF-without-eggnog-PQQ subset (~3 min).

To re-execute via nbconvert (saves outputs in place):
```bash
cd projects/lanthanide_methylotrophy_atlas
for nb in notebooks/0*.ipynb; do
    jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=900 "$nb"
done
```

**Notes**:
- All BERDL data CSVs in `data/` are gitignored (regenerable from the notebooks). Figures in `figures/` are committed.
- The `genome_marker_matrix.csv` is ~10 MB.

## Authors
David Lyon (ORCID: [0000-0002-1927-3565](https://orcid.org/0000-0002-1927-3565)) — KBase
