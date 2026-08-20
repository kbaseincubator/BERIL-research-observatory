# Microbial Metal Ecology: Turnover vs Gene Gain

## Status

Analysis — RESEARCH_PLAN.md and REPORT.md drafted; six sub-analyses complete.

## Research Question

Does metal contamination select for metal-tolerant lineages through **community turnover** (specific taxa replacing others), or through **gene gain** within resident lineages (horizontal transfer of resistance genes)?

Or more precisely: **which genomic and ecological signals — resistance genes, metabolic genes, or phylogenetic composition — reliably reflect metal exposure at field scales, and at what resolution do they work?**

## Authors

Heather MacGregor (Lawrence Berkeley National Laboratory)
ORCID: 0000-0003-1112-3009

## Thesis Chapter

All parts (synthesis project)

## Thesis Arc

This project synthesizes six completed analyses into a coherent thesis narrative. Each sub-analysis was designed to test a distinct piece of the resistance-gene-as-bioindicator hypothesis from a different angle:

| Sub-analysis | Scale | Question | Main finding |
|---|---|---|---|
| [comprehensive_metal_ecology](../comprehensive_metal_ecology/) | 1,574 genera, global | Does metal gene density predict niche breadth? | Cofactor β=−0.033 (p=10⁻⁹); resistance β≈0. Constitutive genes specialize; resistance genes don't. |
| [per_ko_metal_associations](../per_ko_metal_associations/) | 8,585 MAGs, 6,451 KOs | Which specific genes associate with metal gradients? | 219 baseline sig → 31 pH-robust. DNA repair and cofactor genes dominate; resistance genes are 1/84 field-strict. |
| [community_composition_prediction](../community_composition_prediction/) | 16S communities | Can taxa predict metal contamination? | Within-region AUC=0.99; cross-region AUC=0.18. Geography dominates; no universal indicator taxon. |
| [enigma_stress_phenotype_ml](../enigma_stress_phenotype_ml/) | ENIGMA isolates | Does sequence predict lab metal fitness? | Hg AUC=0.774 from amino acid sequence alone. Metals generalize poorly across genera (LOGO AUC 0.53–0.62). |
| [metagenomic_environment_prediction](../metagenomic_environment_prediction/) | SPIRE+MGnify MAGs | Can MAG KO density predict site metal? | H1 NOT SUPPORTED (MAG density RMSE > baseline). MAG+environment combined best. |
| [mwas_confound_analysis](../mwas_confound_analysis/) | SPIRE/MGnify MAGs | Are MWAS hits collinearity artifacts? | 1,097 raw hits → 4 (kitchen-sink) or 2 (+ community). Most published soil metal MWAS results are artifacts. |

## Companion projects (bioindicator application layer)

- [metal_contamination_bioindicators](../metal_contamination_bioindicators/) — Global genus-level contamination indicators (278K samples; REVIEWED)
- [usa_env_bioindicators](../usa_env_bioindicators/) — USA-specific env-PCA fingerprinting (companion to above)
- [lanthanide_xoxf_ecology](../lanthanide_xoxf_ecology/) — xoxF methanol dehydrogenase × lanthanides (separate story)
- [orfrc_metal_ecology](../orfrc_metal_ecology/) — ORFRC N-cycling × metal gradient (supporting)

## Quick Links

- [RESEARCH_PLAN.md](RESEARCH_PLAN.md) — Pre-registered analysis plan with all hypotheses
- [REPORT.md](REPORT.md) — Synthesis of findings across all six sub-analyses

## Reproduction

Each sub-analysis is fully reproducible via its own project. See `projects/<sub_id>/README.md` for reproduction instructions. This synthesis project adds no new computations — it provides the pre-registered plan and cross-project synthesis document.
