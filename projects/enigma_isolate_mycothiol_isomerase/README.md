# ENIGMA Isolate Survey: Mycothiol-Dependent Malonylpyruvate Isomerase

## Research Question

Do any ENIGMA lab isolates carry the mycothiol-dependent malonylpyruvate isomerase
identified as phylogenetically enriched in Actinobacteria, and if so, which strains
are tractable candidates for experimental testing of adaptive metal function?

## Status

Reviewed — REVIEW_3.md drafted; awaiting /submit.

## Background

Pangenomic enrichment analysis (`projects/mycothiol_detox_module`) established that
a mycothiol-dependent detoxification module — including malonylpyruvate isomerase — is
present in ~71% of Actinomycetota but <1% of Pseudomonadota and Bacillota. Subsequent
phylogenetically corrected enrichment analysis (subsampling to one genome per genus)
confirmed the isomerase is the most robust enrichment signal remaining, specific to
Actinobacteria.

The Enigma Genome Depot (`enigma.genome_depot_enigma`) contains genomes of ENIGMA lab
isolates from metal-contaminated Oak Ridge sites. These strains are available for
laboratory experiments. This project confirms whether any isolates carry the gene and
ranks them by experimental tractability.

## Approach

1. Query `enigma.genome_depot_enigma` for Actinobacteria isolates.
2. Search for malonylpyruvate isomerase via product name, InterPro domain, and KO
   (cross-reference annotations from `kbase.ke_pangenome`).
3. Obtain the canonical ENIGMA isolate list from Jen to confirm which hits are
   available as cultured strains.
4. Rank candidate isolates by: gene presence, genome completeness, growth conditions
   known, and metal tolerance phenotype if documented.
5. Output a shortlist of isolates for experimental follow-up.

## Data Sources

| Source | Table/Resource | Purpose |
|---|---|---|
| Enigma Genome Depot | `enigma.genome_depot_enigma` | Isolate genomes and annotations |
| KBase pangenome | `kbase.ke_pangenome` | Annotation cross-reference for InterPro/KO |
| Jen's isolate list | External (contact Jen) | Canonical ENIGMA cultured strains |

## Notebooks

| NB | File | Description |
|---|---|---|
| 01 | `01_enigma_depot_query.ipynb` | Query genome depot; identify isomerase-positive isolates |
| 02 | `02_candidate_ranking.ipynb` | Merge with isolate metadata; rank experimental candidates |

## Quick Links

- [Research Plan](RESEARCH_PLAN.md)
- [Review 1](REVIEW_1.md)
- [Review 2](REVIEW_2.md)

## Reproduction

NB01 (`01_enigma_depot_query.ipynb`) requires a live Spark session via
`get_spark_session()`. Run in JupyterHub:

```bash
jupyter nbconvert --to notebook --execute 01_enigma_depot_query.ipynb --output 01_enigma_depot_query.ipynb
```

After NB01 has produced the cached parquets in `data/`, NB02 runs locally
(reads CSV — no Spark required):

```bash
jupyter nbconvert --to notebook --execute 02_candidate_ranking.ipynb --output 02_candidate_ranking.ipynb
```

Note: use `--output <name>` not `--inplace` — the latter silently drops all
cell outputs on this JupyterHub.

## Authors

Heather MacGregor, Lawrence Berkeley National Laboratory

## Related Projects

- [`mycothiol_detox_module`](../mycothiol_detox_module/) — pangenomic enrichment analysis that generated this lead
- [`enigma_contamination_functional_potential`](../enigma_contamination_functional_potential/) — prior ENIGMA field ecology work
