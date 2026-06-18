# Cf Formulation Design

This project investigated whether rationally designed commensal communities can suppress Pseudomonas aeruginosa in cystic fibrosis airways by metabolic competitive exclusion—"eating their lunch" on amino acids the pathogen depends on. Integrating planktonic inhibition assays, carbon source profiling, growth kinetics, patient metagenomics, and pangenome analysis across six species, researchers identified a five-organism FDA-safe formulation (Neisseria mucosa, Streptococcus salivarius, Micrococcus luteus, Rothia dentocariosa, Gemella sanguinis) that achieves 100% coverage of P. aeruginosa's amino acid niche with 78% mean inhibition. The most important finding: metabolic overlap significantly predicts inhibition but explains only about 27% of variance, meaning community-level resource depletion matters more than individual metabolic dominance, and the two lung-adapted anchor species are naturally suited for airway colonization despite the inherent tension that the metabolically essential keystone species (M. luteus) has zero engraftability in patient lungs.

## Key findings

- All inhibition assays measure planktonic competition, whereas PA14 grows primarily in CF-lung biofilms where metabolic dynamics, diffusion gradients, and spatial structure differ substantially. *(confidence: high)*
- All inhibition assays used PA14, an ExoU+ Pel-only strain representing under 5% of CF PA isolates, so the measured inhibition has not been validated against the dominant ExoS+/PAO1-type clinical strains. *(confidence: high)*
- Micrococcus luteus is the keystone species for full niche coverage yet has zero detected patient engraftability and no lung genomes, creating a design tension where the most metabolically important member is the least likely to persist in the lung. *(confidence: medium)*
- The multivariate metabolic-feature model of inhibition overfits the 142-isolate cohort, with cross-validated R-squared near 0.145 rather than the training R-squared of 0.274, so its true out-of-sample predictive power is closer to 15%. *(confidence: high)*
- A five-organism FDA-safe formulation (Neisseria mucosa, Streptococcus salivarius, Micrococcus luteus, Rothia dentocariosa, Gemella sanguinis) achieves 100% coverage of PA14's amino acid niche with 78% mean inhibition. *(confidence: high)*
- The amino-acid catabolic pathways the formulation targets are 97.4% conserved across 1,796 lung PA genomes, so one formulation is predicted to suppress PA equivalently across lung variants including CF-derived strains. *(confidence: high)*
- Across 175 patient samples, Neisseria mucosa has the highest engraftability score (prevalence times log activity ratio) among inhibition-tested species, marking it as the most promising colonization anchor. *(confidence: medium)*
- Although commensals rarely exceed PA14's maximum growth rate, they begin growing before PA14 on 43.1% of substrate comparisons, suggesting pre-establishing commensals before pathogen exposure may matter more than raw growth rate. *(confidence: medium)*
- Full amino-acid niche coverage of PA14 is first reached at a three-organism formulation (M. luteus, N. mucosa, S. salivarius), where at least one member grows on every amino acid PA14 can use. *(confidence: high)*
- GapMind pangenome analysis across 499 genomes confirms that the formulation species' metabolic capabilities are species-level traits conserved (>95%) across hundreds of genomes, supporting strain-agnostic formulation design. *(confidence: high)*
- Genomic pathway comparison identifies sugar alcohols (xylitol, myoinositol) and pentoses (xylose, arabinose, fucose, rhamnose) as candidate prebiotics that formulation commensals can metabolize but PA14 cannot. *(confidence: medium)*
- Lung-adapted P. aeruginosa undergoes metabolic streamlining, losing sugar-catabolism pathways under relaxed selection in the amino-acid-rich sputum environment, while its amino acid catabolism remains an invariant evolutionary adaptation. *(confidence: high)*
- Metabolic carbon-source overlap with Pseudomonas aeruginosa PA14 significantly predicts commensal planktonic inhibition (r = 0.384) but explains only about 27% of the variance. *(confidence: high)*
- No individual commensal outgrows PA14 on any tested carbon substrate, so competitive exclusion of P. aeruginosa requires community-level niche coverage rather than a single dominant strain. *(confidence: high)*
- PA14 outgrows the average commensal on every tested amino acid and simple sugar, so no single tested substrate works as a selective prebiotic that feeds commensals while starving the pathogen. *(confidence: high)*
- T3SS effector typing of 6,760 PA genomes shows CF isolates are overwhelmingly ExoS+ (94%), so the ExoU+ reference strain PA14 used in the inhibition assays represents only about 5% of CF P. aeruginosa. *(confidence: high)*
- Two formulation anchor species, Rothia dentocariosa and Neisseria mucosa, are naturally lung-adapted, with 33-38% of their pangenome genomes drawn from respiratory sources rather than being gut commensals repurposed for the airway. *(confidence: high)*
- Experimentally testing the five core species plus PA14 on xylitol, myoinositol, xylose, arabinose, fucose, and rhamnose as sole carbon sources would validate the genomically predicted selective sugar-alcohol prebiotic strategy. *(confidence: medium)*
- Measuring the complete 10-pair interaction matrix of the five core species in the PA14 competition assay is the highest-priority validation, since a single untested antagonistic pair could invalidate the additive formulation design. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Microbiome Engineering](../topics/microbiome-engineering.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kbase Msd Biochemistry](../data/kbase-msd-biochemistry.md)
- [Phagefoundry](../data/phagefoundry.md)
- [Protect Genomedepot](../data/protect-genomedepot.md)

## Authors

- [Adam P. Arkin](../authors/0000-0002-4999-2931.md)

[Open the full report →](../../../projects/cf_formulation_design/REPORT.md)
