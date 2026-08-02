# References — cultivability_index

## Primary data and tooling

- **Price MN, Deutschbauer AM, Arkin AP (2018).** "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature* 557:503-509. PMID: 29769716. — Fitness Browser foundation; used for the BERIL anchor projects.
- **Price MN, Deutschbauer AM, Arkin AP (2022).** "Filling gaps in bacterial catabolic pathways with computation and high-throughput genetics." *PLoS Genetics* 18(5):e1010156. — GapMind methodology paper for carbon utilization pathway scoring.
- **Price MN, Shiver AL, Day LA, Torres M, Lesea HP, et al. (2024).** "Improving the annotation of amino acid biosynthesis pathways: GapMind2024." *bioRxiv* 2024.10.14.618325. — GapMind 2024 update with 26 auxotrophic bacteria validation set (106 measured auxotrophies). Anchors the reliability of the per-genome pathway-completeness features.
- **Parks DH, Chuvochina M, Waite DW, et al. (2022).** "GTDB: an ongoing census of bacterial and archaeal diversity through a phylogenetically consistent, rank-normalized, and complete genome-based taxonomy." *Nucleic Acids Research* 50(D1):D199-D207. PMID: 34520557. — GTDB taxonomy used for the family-stratified holdout.

## Closely related work

- **Oduwole I, Babjac A, Royalty TM, Hibbs M, Lloyd KG, et al. (2025).** "Functional genomic signatures predict microbial culturability across the tree of life." *bioRxiv* 2025.08.18.670795. — Closest competing work. Analyzed 52,515 GEM-catalog MAGs; tested whether uncultured genomes encode more functionally novel genes. Our work differs by including isolates in the cohort (235K total vs MAGs-only), using GapMind binary pathway-completeness as a specific feature set, applying family-stratified holdout, and surfacing the AA-vs-carbon reversal.
- **Ramoneda J, Jensen TBN, Price MN, et al. (2023).** "Taxonomic and environmental distribution of bacterial amino acid auxotrophies." *Nature Communications* 14:7607. — Mapped bacterial AA auxotrophies across the tree of life. Provides the prior that "many bacterial taxa are not readily cultivated because of auxotrophy"; our work supports this from the inverse direction (cultured taxa are enriched in AA-auxotrophic content because lab media supplements).
- **Starke S, Harris DMM, Zimmermann J, et al. (2023).** "Amino acid auxotrophies in human gut bacteria are linked to higher microbiome diversity and long-term stability." *ISME Journal* 17(12):2370-2380. — Cross-feeding analog of lab-media supplementation in natural communities.
- **Pacheco AR, et al. (2025).** "Low anabolic independence emerges when cultivating more than three bacterial species together." *bioRxiv* 2025.04.28.650956. — Demonstrates that auxotrophy is selected for under cross-feeding (3+ species co-cultures). The natural-environment analog of lab-media AA supply.
- **Jiménez DJ, Marasco R, Schultz J, et al. (2025).** "Discovery and cultivation of prokaryotic taxa in the age of metagenomics and artificial intelligence." *ISME Journal* 20(1):wrag012. — Review explicitly noting that growth-enhancing metabolite supplementation works for auxotrophic taxa. Our strict candidate list operationalizes this strategy.

## Methodological / single-clade context

- **Gtari M, Maaoui R, Ghodhbane F (2024).** "MAGs-centric crack: how long will spore-positive Frankia and most Protofrankia microsymbionts remain recalcitrant to axenic growth?" *Frontiers in Microbiology* 15:1367490. — Used GapMind to identify auxotrophies in Frankia/Protofrankia MAGs. Single-clade complementary work to our pan-bacterial scale.
- **Ryback B, Bortfeld M (2022).** "Metabolic adaptation to vitamin auxotrophy by leaf-associated bacteria." *ISME Journal* 16(12):2712-2724. — Vitamin auxotrophy axis we do not currently include in features but recommend adding (Future Direction).
- **Ferrario C, Duranti S, Milani C, et al. (2015).** "Exploring Amino Acid Auxotrophy in *Bifidobacterium bifidum* PRL2010." *Frontiers in Microbiology* 6:1331. — Single-strain empirical AA auxotrophy in a cultured Bifidobacterium, illustrating the same mechanism at single-strain resolution.
- **Müller J, Beckers M, Mußmann N, Bongaerts J (2018).** "Elucidation of auxotrophic deficiencies of *Bacillus pumilus* DSM 18097 to develop a defined minimal medium." *Microbial Cell Factories* 17:158. — Concrete example of using genomically-predicted auxotrophies to design minimal cultivation media. Pattern our Future Direction #6 suggests scaling.

## BERDL anchor projects (cross-cited in REPORT.md)

- `projects/clay_confined_subsurface/REPORT.md` — Mont Terri cultivation-bias finding for Bacillota_B; anchor for Validation 1 in NB05.
- `projects/oak_ridge_cultivation_gap/REPORT.md` — Oak Ridge ORFRC cultured-vs-MAG gene-content gap; anchor for Validation 4 (subsurface-source proxy) in NB05.
- `projects/metabolic_capability_dependency/RESEARCH_PLAN.md` — GapMind pathway-completeness extraction patterns reused here.
- `projects/conservation_vs_fitness/REPORT.md` and `projects/fitness_effects_conservation/REPORT.md` — earlier fitness-conservation pangenome work in the BERIL series whose limitations motivated the cultivability framing.
