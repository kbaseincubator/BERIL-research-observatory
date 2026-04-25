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

### `kescience_fitnessbrowser` (Fitness Browser)
- `reannotation` — 1,762 curator-accumulated reannotations (36 organisms, 1,756 unique loci). Reference set.
- Primary fitness/cofit: `genefitness`, `experiment`, `specificphenotype`, `specog`, `cofit`, `ortholog`, `gene`, `scaffoldseq`
- Functional annotation text: `besthitswissprot`, `swissprotdesc`, `besthitkegg`, `keggmember`, `kgroupdesc`, `kgroupec`, `seedannotation`, `genedomain`
- Schema: [docs/schemas/fitnessbrowser.md](../../docs/schemas/fitnessbrowser.md)

### `kescience_paperblast` (PaperBLAST literature mining)
- `uniq` — 815,571 unique protein sequences (used as DIAMOND target DB)
- `gene` — 1.1M gene records with curated descriptions
- `genepaper` — 3.2M (gene, paper) associations
- `seqtoduplicate` — 284K sequence ID synonyms
- Schema: see `.claude/skills/berdl/modules/paperblast.md`

### External resources
- **Fitness Browser AA sequences**: `https://fit.genomics.lbl.gov/cgi_data/aaseqs` (272K sequences, ~96 MB) — used as DIAMOND query set after filtering to 35 curated organisms
- **PaperBLAST DIAMOND DB build**: 815,571 sequences from `kescience_paperblast.uniq` parquet downloaded from BERDL MinIO

## Cited PMIDs

The 120 unique PMIDs cited by subagents during reasoning are listed in [data/cited_pmids.tsv](data/cited_pmids.tsv) with citation counts and verdicts. The 11 cross-gene cluster PMIDs (cited by ≥3 genes each) are detailed in [data/cross_gene_clusters.md](data/cross_gene_clusters.md). All paper full text was fetched via the PubMed MCP (`mcp__pubmed__convert_article_ids` + `mcp__pubmed__get_full_text_article`) from PubMed Central.
