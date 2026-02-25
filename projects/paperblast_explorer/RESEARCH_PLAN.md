# Research Plan: PaperBLAST Data Explorer

## Research Question
What does the `kescience_paperblast` collection contain, how current is it, and what are the coverage patterns and biases across organisms, domains of life, genes, and curated databases?

## Hypothesis
This is a data characterization project, not a hypothesis-driven analysis. The goal is to produce a reference document describing the PaperBLAST collection on BERDL.

## Literature Context
- **Price & Arkin (2017)** created PaperBLAST to link protein sequences to published literature via text mining of PubMed Central full-text articles. *mSystems* 2:e00039-17. PMID: 28845461.
- A growing body of work documents the extreme concentration of biological research on a few model organisms. **Stork et al. (2024)** showed that the top 10 microbes account for a disproportionate share of microbiology publications.
- The "long tail" of understudied genes is a well-known problem — **Stoeger et al. (2018)** showed that the most-studied human genes continue to attract the most new research, creating a self-reinforcing bias. *PLoS Biol* 16:e2006643. PMID: 30226837.

## Data Sources
- `kescience_paperblast` — all 14 tables (genepaper, gene, snippet, curatedgene, curatedpaper, generif, uniq, site, hassites, seqhassite, pdbligand, pdbclustinfo, paperaccess, seqtoduplicate)

## Analysis Plan

### Notebook 1: Database Overview
- Table inventory with row counts and column schemas
- Temporal coverage: publication year distribution, most recent data
- Taxonomic coverage: organisms by domain, top organisms per domain
- Literature coverage: papers per gene distribution
- Curated vs text-mined data: breakdown by source database
- Structural data: PDB sites, ligands
- Cross-database ID mappings (VIMSS → Fitness Browser link)

### Notebook 2: Coverage Skew Analysis
- Organism concentration: cumulative coverage curves (top N organisms = X% of literature)
- Gene concentration: papers-per-gene distribution, top 50 genes
- Lorenz inequality curves and Gini coefficients for organisms and genes
- Bacterial focus: top microbes by literature coverage
- SwissProt coverage analysis
- Top 50 tables for organisms and genes

### Notebook 3: Sequence Clustering Analysis
*Added after initial plan — motivated by exploring sequence diversity in the collection.*
- Extract all 815,571 unique protein sequences from `uniq` table
- Cluster with MMseqs2 at 90%, 50%, and 30% identity via CTS remote compute
- Analyze cluster size distributions, identify largest protein families
- Cross-reference clustering with literature coverage to identify "dark" protein families
- Quantify sequence space reduction at each identity threshold

## Expected Outcomes
- Reference document characterizing PaperBLAST scale, currency, and biases
- Figures suitable for presentations showing the "long tail" of understudied biology
- Understanding of cross-collection linkage potential (PaperBLAST ↔ Fitness Browser ↔ pangenome)

## Revision History
- **v2** (2026-02-22): Added Notebook 3 (sequence clustering) to plan
- **v1** (2026-02-22): Initial plan and analysis complete

## Authors
- Paramvir Dehal (https://orcid.org/0000-0002-3495-1240), Lawrence Berkeley National Laboratory, US Department of Energy
