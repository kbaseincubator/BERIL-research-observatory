# References

## Foundational Theory

**Morris JJ, Lenski RE, Zinser ER (2012).** "The Black Queen Hypothesis: Evolution of
Dependencies through Adaptive Gene Loss." *mBio*. 3(2):e00036-12.
DOI: 10.1128/mBio.00036-12
*Proposes that biosynthetic gene loss is selectively favoured when community members
supply the product, predicting negative correlation between community biosynthetic
completeness and ambient metabolite pools — the central H1 prediction of this project.*

**Danczak RE, Chu RK, Fansler SJ, Goldman AE, Graham EB, Tfaily MM, Toyoda J,
Stegen JC (2020).** "Using metacommunity ecology to understand environmental
metabolomes." *Nature Communications*. 11(1):6369. PMID: 33311510.
DOI: 10.1038/s41467-020-19989-y
*Establishes meta-metabolome ecology framework: community assembly processes govern
which metabolites accumulate or are consumed; stochastic processes drive molecular
properties while biochemical transformations are deterministically assembled.*

---

## Methods and Tools

**Price MN, Deutschbauer AM, Arkin AP (2020).** "GapMind: Automated Annotation of
Amino Acid Biosynthesis." *mSystems*. 5(3):e00291-20.
DOI: 10.1128/mSystems.00291-20
*Introduces GapMind for rapid identification of amino acid biosynthesis pathway
completeness in microbial genomes; source of the 305M-row `gapmind_pathways` table
used in NB03.*

**Price MN, Deutschbauer AM, Arkin AP (2022).** "Filling gaps in bacterial catabolic
pathways with computation and high-throughput genetics." *PLOS Genetics*.
18(7):e1010156. DOI: 10.1371/journal.pgen.1010156
*Extends GapMind to 62 carbon source catabolic pathways with systematic experimental
validation; source of the carbon pathway completeness scores in the 80-pathway matrix.*

**Arkin AP, Cottingham RW, Henry CS, Harris NL, Stevens RL, Maslov S, et al. (2018).**
"KBase: The United States Department of Energy Systems Biology Knowledgebase."
*Nature Biotechnology*. 36(7):566-569. DOI: 10.1038/nbt.4163
*Describes KBase infrastructure underpinning the BERDL pangenome collections
(`kbase_ke_pangenome`) and NMDC data integration (`nmdc_arkin`) used throughout.*

---

## Community Metabolomics Prediction

**Noecker C, Eng A, Srinivasan S, Theriot CM, Young VB, Jansson JK, et al. (2016).**
"Metabolic model-based integration of microbiome taxonomic and metabolomic profiles
elucidates mechanistic links between ecological and metabolic variation." *mSystems*.
1(1):e00013-15. DOI: 10.1128/mSystems.00013-15
*Shows that genome-scale metabolic reconstructions integrated with microbiome taxonomy
predict metabolomic variation; uses full flux models rather than pathway completeness
scores (methodological precedent for H1).*

**Mallick H, Franzosa EA, McIver LJ, Banerjee S, Sirota-Madi A, Kostic AD, et al.
(2019).** "Predictive metabolomic profiling of microbial communities using amplicon or
metagenomic sequences." *Nature Communications*. 10(1):3136. PMID: 31316056.
DOI: 10.1038/s41467-019-11052-9
*Demonstrates that >50% of metabolites in new communities are predictable from
metagenomes/amplicon data, supporting the general feasibility of genomics-to-metabolomics
inference across body sites.*

**Gowda K, Ping D, Mani M, Kuehn S (2022).** "Genomic structure predicts metabolite
dynamics in microbial communities." *Cell*. 185(3):530-546. PMID: 35085485.
DOI: 10.1016/j.cell.2021.12.036
*Shows that metabolite dynamics of denitrification model communities are predictable
from gene content via simple linear regression — strongest published support for
gene-to-metabolite prediction in controlled communities.*

---

## Amino Acid Auxotrophies and Biosynthesis Evolution

**Ramoneda J, Jensen TBN, Price MN, Fierer N, Braendle C (2023).** "Taxonomic and
environmental distribution of bacterial amino acid auxotrophies." *Nature
Communications*. 14(1):7608. DOI: 10.1038/s41467-023-43435-4
*Uses GapMind on representative genomes to show amino acid auxotrophy rates are
non-random across bacterial phyla and environments; directly establishes that ecosystem
type shapes community biosynthesis completeness (aligned with our H2 result).*

---

## Ecosystem Metabolic Differentiation

**Danczak RE, Goldman AE, Chu RK, Toyoda JG, Borton MA, et al. (2021).** "Ecological
theory applied to environmental metabolomes reveals compositional divergence despite
conserved molecular properties." *Science of the Total Environment*. 788:147409.
DOI: 10.1016/j.scitotenv.2021.147409
*Extends meta-metabolome ecology showing cross-ecosystem compositional divergence of
metabolomes despite conserved molecular properties; conceptual support for H2.*

---

## Other Related Work

**Hesse E, O'Brien S (2024).** "Ecological dependencies and the illusion of cooperation
in microbial communities." *Microbiology Research*. (in press)
*Reviews how BQH-type genome streamlining shapes metabolic interdependency networks,
with examples from spatially structured communities.*
