# References

## Primary

Price MN, Wetmore KM, Waters RJ, Callaghan M, Ray J, Liu H, Kuehl JV, Melnyk RA, Lamson JS, Suh Y, Carlson HK, Esquivel Z, Sadeeshkumar H, Chakraborty R, Zane GM, Rubin BE, Wall JD, Visel A, Bristow J, Blow MJ, Arkin AP, Deutschbauer AM. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature* 557(7706):503-509. DOI: [10.1038/s41586-018-0124-0](https://doi.org/10.1038/s41586-018-0124-0). PMID: 29769716.

## Supporting documentation (Fitness Browser / LBL supplement)

- **LBL bigfit supplemental site**: https://genomics.lbl.gov/supplemental/bigfit/ — source of `FEBA_anno_withrefseq.tab` (paper TableS12, 456 reannotations: 238 transporters + 218 catabolism), `AllConsLinks.tab` (conserved functional associations), `high_fitness_feba.tab`, and `Supplementary_Tables_final.xlsx` (22 supplementary tables S1–S22).
- **Fitness Browser help page (authoritative thresholds)**: https://fit.genomics.lbl.gov/cgi-bin/help.cgi — defines specific phenotype (`|fit| > 1 AND |t| > 5 AND |fit|_95 < 1 AND |fit| > |fit|_95 + 0.5`), strong phenotype (`|fit| > 2`), significant cofitness (`cofit > 0.75, rank ∈ {1,2}`), conserved cofitness (both pair and orthologs `cofit > 0.6`), usable t-score (`|t| ≥ 4`).
- **Fitness Browser**: https://fit.genomics.lbl.gov/ — per-organism reannotation downloads at `downloadReanno.cgi?orgId=<id>`.
- **Figshare data deposit**: [doi.org/10.6084/m9.figshare.5134840](https://doi.org/10.6084/m9.figshare.5134840)

## Related BERDL projects in this repo

- `projects/truly_dark_genes/` — bakta v1.12.0 re-annotation of FB dark genes (new-compute approach; complementary framing)
- `projects/functional_dark_matter/` — GapMind pathway-gap matching for 17,344 dark-and-phenotyped genes
- `projects/fitness_effects_conservation/` — fitness importance vs. core/accessory conservation
- `projects/cofitness_coinheritance/` — cofitness structure

## BERDL data sources used

- `kescience_fitnessbrowser.reannotation` — 1,762 curator-accumulated reannotations (36 organisms, 1,756 unique loci). Reference set.
- `kescience_fitnessbrowser.genefitness`, `.experiment`, `.specificphenotype`, `.specog`, `.cofit`, `.ortholog`, `.genedomain`, `.besthitkegg`, `.keggmember`, `.kgroupdesc`, `.kgroupec`, `.seedannotation`, `.metacycpathway`, `.metacycreaction` — see [docs/schemas/fitnessbrowser.md](../../docs/schemas/fitnessbrowser.md).
