# Research Plan: Metal Resistance Ecology

## Hypothesis

Bacterial genera with broader metal-resistance repertoires (higher metal-type AMR diversity)
will occupy a wider range of environmental niches globally, because metal resistance functions
as a gateway trait that expands the range of habitats a lineage can colonise.

**Primary prediction**: A positive association between per-genus metal-type AMR count and
Levins' B_std (standardised niche breadth) will survive correction for phylogenetic
non-independence (PGLS with Pagel's λ).

**Null**: Metal resistance diversity is phylogenetically conserved but not associated with
ecological breadth after controlling for shared ancestry.

**Positive control**: Nitrification (obligate environmental restriction) should show
strong phylogenetic signal (λ ≈ 1) and *narrow* niche breadth — the opposite direction.

## Pre-Analysis Decisions

- **Unit of analysis**: Genus level. Justification: GTDB r214 species trees available at
  genus resolution; species-level niche breadth estimates would be dominated by sampling
  artefacts given sparse per-species MicrobeAtlas coverage.
- **Niche breadth metric**: Levins' B_std = (B − 1)/(J − 1), corrected for unequal numbers
  of environments (J = 13). More conservative than raw Levins' B.
- **AMR predictor**: Number of distinct metal types with ≥1 AMR gene in the genus pangenome
  (AMRFinderPlus annotations from `kbase_ke_pangenome`).
- **Phylogenetic correction**: PGLS via `nlme::gls` + `ape::corPagel`, with λ estimated
  jointly by ML. This avoids the two-step bias of fixing λ from a separate estimate.
- **Multiple testing**: Bonferroni correction for 6 pre-specified confirmatory PGLS models;
  BH-FDR for the full 47-test exploratory family.
- **Falsification threshold**: Effect must survive Bonferroni at α = 0.05 across all 6
  confirmatory tests.

## Analytical Plan

| Phase | Notebook | Description |
|---|---|---|
| 1. Data extraction | NB01 (JupyterHub) | Extract per-species AMR metal type counts from `kbase_ke_pangenome` |
| 2. Niche breadth | NB02 (JupyterHub) | Compute Levins' B_std across 260M OTU × sample observations |
| 3. Taxonomy bridge | NB03 (local) | Link OTU genera to GTDB species for AMR proxy assignment |
| 4. Phylogenetic signal | NB04 (local R) | Estimate Pagel's λ for each metal type and niche breadth |
| 5. PGLS | NB05 (local) | Test niche breadth ~ metal diversity; 6 confirmatory + 47 exploratory |
| 6. Synthesis | NB06 (local) | Publication-quality figures |

## Validation Plan

- **Track A (BERDL groundwater)**: Test whether community-level metal AMR diversity
  predicts prevalence in ENIGMA contamination-gradient samples (independent dataset).
- **Track B (PRJNA1084851)**: Test CWM metal diversity dynamics in a field carbon-amendment
  experiment — does microbial response to perturbation track metal resistance capacity?

## Known Risks

- Genus-level taxonomy bridge coverage may be <100% (OTUs with no GTDB-matching genera).
- AMRFinderPlus "other metal" category (~17% of annotations) may include false positives.
- Archaeal PGLS will be underpowered given low n.
- ape::corPagel row-ordering is a known silent-error pitfall — mitigation: unit test in
  `scripts/test_pgls_ordering.py`.
