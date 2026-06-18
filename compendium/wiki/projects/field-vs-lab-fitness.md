# Field Vs Lab Fitness

This project examined whether genes important for field-relevant conditions (uranium, mercury, nitrate stress) versus lab conditions in *Desulfovibrio vulgaris* show different patterns of pangenome conservation. The central finding was unexpected: fitness importance predicts conservation regardless of condition type, with lab-specific genes actually more conserved (96% core) than field-specific genes (88.5%), suggesting the core genome reflects general functional essentiality rather than ecological niche-specific selection. Antibiotic and heavy-metal resistance genes, however, are predominantly accessory and likely recently acquired on mobile genetic elements, revealing a functional partition aligned with evolutionary mechanisms of adaptation.

## Key findings

- Gene length is confounded with both fitness measurement quality and core status, since short genes receive fewer transposon insertions and core genes tend to be longer. *(confidence: medium)*
- Results are limited to a single organism (DvH) whose pangenome has few genomes, producing a coarse core/auxiliary classification with a high 76.3% baseline core fraction that compresses effect sizes. *(confidence: high)*
- The field-specific and lab-specific gene sets are small (n=50-52), limiting statistical power for the key field-versus-lab comparison. *(confidence: high)*
- Antibiotic-resistance (73.4% core) and heavy-metal-resistance (71.2% core) genes are the least conserved and fall below baseline, suggesting these resistance functions are disproportionately accessory traits carried on mobile genetic elements. *(confidence: medium)*
- The dominant signal is that any fitness importance, regardless of condition type, predicts pangenome conservation: universally important genes are significantly more core than neutral genes (OR=1.35, p=0.033). *(confidence: medium)*
- This is the first analysis to stratify RB-TnSeq fitness effects by ecological relevance, finding that condition type matters less than fitness magnitude for predicting conservation, implying the core genome reflects general functional importance rather than niche-specific selection. *(confidence: medium)*
- At the module level, ICA fitness module conservation shows no significant correlation with field condition activity (Spearman rho=0.071, p=0.62), so module-level conservation does not separate field from lab conditions. *(confidence: high)*
- Counter to the hypothesis, genes with fitness defects only under lab conditions are 96.0% core, slightly higher than field-specific genes at 88.5%, indicating that fitness importance predicts conservation regardless of ecological context. *(confidence: medium)*
- DvH's 757 RB-TnSeq experiments were classified into six ecological-relevance categories, yielding a broad split of 337 field (44.5%) versus 420 lab (55.5%) conditions. *(confidence: high)*
- Field-stress genes consistently show the highest conservation and heavy-metals genes the lowest across fitness thresholds from -1 to -3, confirming the pattern is robust to threshold choice. *(confidence: high)*
- Genes important under field-stress, field-core, and lab-nutrient conditions are significantly enriched in the core genome after BH-FDR correction, with field-stress genes the most conserved (83.6% core, OR=1.58, q=0.026). *(confidence: high)*
- In logistic regression, gene length is a much stronger predictor of core-genome status (CV-AUC 0.645) than field or lab fitness effects, neither of which alone is informative (CV-AUC near 0.5). *(confidence: high)*
- Nine low-field-activity "lab" ICA modules are notably less conserved (mean core fraction 0.516), showing that accessory-genome fitness modules exist and tend to respond to lab-type conditions. *(confidence: medium)*
- The ENIGMA CORAL database contains no Desulfovibrio vulgaris Hildenborough fitness data, so all gene-level fitness analysis relies on the Fitness Browser RB-TnSeq dataset. *(confidence: high)*
- Replacing the binary core/auxiliary label with a quantitative conservation metric (fraction of genomes carrying each gene cluster) could increase statistical power for the fitness-conservation relationship. *(confidence: medium)*
- The 21 conserved "ecological" ICA modules contain 239 member genes, of which 52 are unannotated and are candidate novel functions for environmental adaptation. *(confidence: medium)*

## Topics

- [Topic: Amr Resistome](../topics/amr-resistome.md)
- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metal Resistance](../topics/metal-resistance.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)
- [Topic: Subsurface Genomics](../topics/subsurface-genomics.md)

## Data

- [Enigma Coral](../data/enigma-coral.md)
- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/field_vs_lab_fitness/REPORT.md)
