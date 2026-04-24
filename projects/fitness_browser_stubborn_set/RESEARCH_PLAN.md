# Research Plan: The Fitness Browser Stubborn Set — Genes with Strong Phenotypes but No Price-2018 Re-annotation

## Research Question

Price et al. (2018) generated genome-wide mutant fitness data across 48 bacteria and used it, together with comparative genomics evidence, to propose improved functional annotations for a subset of genes. Their curator-accumulated re-annotation set (as loaded in `kescience_fitnessbrowser.reannotation`) currently contains **1,762 gene assignments across 36 organisms (1,756 unique loci)**. However, many additional genes in the Fitness Browser show strong and/or condition-specific fitness phenotypes that satisfy Price's own significance thresholds — yet received no curator re-annotation. This project asks:

> **Among Fitness Browser genes with strong, specific fitness phenotypes that were NOT re-annotated by Price et al., can the evidence already present in BERDL distinguish genes where an improved annotation is plausible from genes where existing evidence is genuinely insufficient?**

In other words: can we reconstruct (and critique) the curator decision boundary using only the evidence sources the Fitness Browser itself exposes?

## Hypothesis

- **H0**: The "stubborn set" (strong-phenotype genes not in the `reannotation` table) is indistinguishable from a random sample of poorly-annotated Fitness Browser genes across BERDL-native evidence sources (conserved cofitness, ortholog phenotype agreement, domain predictions, KEGG/SEED/MetaCyc coverage). No principled partition into "improvable" vs. "unresolvable" can be made from existing evidence alone.

- **H1**: The stubborn set is separable into two sub-populations using only BERDL-native evidence:
  1. **Improvable-now**: genes with a conserved specific phenotype or conserved cofitness link ≥ 0.6 AND at least one additional BERDL-native functional signal (Pfam/TIGRFam domain with EC or clear functional family, KEGG KO with functional group description, SEED annotation with functional subsystem, or MetaCyc pathway hit via EC). These are candidates where Price's curators were conservative or where the paper's scope (transporters + catabolism) excluded them.
  2. **Unresolvable-from-evidence**: genes with a strong or specific phenotype but **no** conserved cross-organism support and **no** informative domain/KEGG/SEED/MetaCyc signal. Genuine evidence-limited dark matter.

## Literature Context

**Primary reference**: Price MN et al. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature* 557(7706):503-509. [DOI: 10.1038/s41586-018-0124-0](https://doi.org/10.1038/s41586-018-0124-0). PMID: 29769716.

**Key facts extracted from the paper, the [LBL bigfit supplement](https://genomics.lbl.gov/supplemental/bigfit/), and the [Fitness Browser help page](https://fit.genomics.lbl.gov/cgi-bin/help.cgi):**

- **Significance thresholds** (authoritative, from Fitness Browser help):
  - Usable t-score: `|t| ≥ 4`
  - Strong phenotype: `|fit| > 2`
  - **Specific phenotype**: `|fit| > 1 AND |t| > 5 AND |fit|_95 < 1 AND |fit| > |fit|_95 + 0.5` (strong in *this* condition, not generally)
  - Significant cofitness: `cofit > 0.75 AND rank ∈ {1, 2}`
  - Conserved cofitness: `cofit > 0.6 AND cofit_ortholog > 0.6`
- **Evidence sources the FEBA pipeline uses**: specific phenotypes, cofitness, conserved cofitness / conserved specific phenotypes across orthologs, comparative genomics (operon context), TIGRFam/Pfam domain predictions, Swiss-Prot best hits via RAPSearch2 (≥80% coverage, ≥30% identity), KEGG, SEED, MetaCyc pathway lookups via EC numbers.
- **Counts**:
  - 11,779 genes with mutant phenotypes not previously annotated with specific function
  - 2,316 genes with high-confidence conserved associations (TableS8: 13,202 gene-link rows)
  - **456 genes formally re-annotated in the paper** (TableS12: 238 transporters + 218 catabolism enzymes — `FEBA_anno_withrefseq.tab`)
  - **1,762 re-annotations currently in BERDL** (`kescience_fitnessbrowser.reannotation`) — curator-accumulated since 2018; this is the reference set we will use
- **What the paper does NOT give us**: no explicit confidence tiers, no "left-alone" list, no characterization of the candidates that received strong phenotypes but no new annotation. **This is the gap this project addresses.**

**Adjacent prior work in this repo (distinct framings; we leverage some data but do not duplicate):**
- [projects/truly_dark_genes](../truly_dark_genes/) — used bakta v1.12.0 to re-annotate FB dark genes (new compute). Different framing: brings in modern annotation tools.
- [projects/functional_dark_matter](../functional_dark_matter/) — prioritized experimentally actionable dark genes using GapMind pathway gaps and EC/Pfam matching.
- [projects/fitness_effects_conservation](../fitness_effects_conservation/) — correlates fitness importance with core/accessory conservation.
- [projects/cofitness_coinheritance](../cofitness_coinheritance/) — cofitness structure analysis.

Our project is distinct in that it (a) uses the Price `reannotation` set as the explicit reference boundary, (b) reasons only over BERDL-native evidence Price 2018 could have used (no bakta, no new HMMs), and (c) frames the question as a **curator-decision-boundary** reconstruction rather than a dark-matter characterization.

## Query Strategy

### Tables Required (all in `kescience_fitnessbrowser` unless noted)

| Table | Purpose | Est. Rows | Filter Strategy |
|---|---|---|---|
| `gene` | Locus → organism + current description/gene symbol | 228,709 | Filter to loci in candidate pool |
| `genefitness` | Fitness + t-stat per (gene, experiment) | 27,410,721 | Filter by `CAST(fit AS FLOAT)`, `CAST(t AS FLOAT)` |
| `experiment` | Condition metadata for phenotype interpretation | 7,552 | Join for expGroup + condition_1 |
| `specificphenotype` | Genes flagged as having specific phenotype in a condition | 38,525 | Join key for candidate pool definition |
| `specog` | Specific phenotypes aggregated by ortholog group | varies | Cross-organism phenotype consistency |
| `cofit` | Cofitness between gene pairs within an organism | 13,656,145 | Filter by `orgId` + locus |
| `ortholog` | BBH orthologs across organisms | millions | Join for cross-organism phenotype conservation |
| `genedomain` | TIGRFam / Pfam / CDD / etc. domain hits per locus | millions | Filter by candidate loci |
| `besthitkegg` | Best BLAST hit to KEGG gene | 200,074 | Join via (orgId, locusId) |
| `keggmember` | KEGG gene → KO ortholog group | 82,687 | Second hop of KO mapping (see pitfalls.md) |
| `kgroupdesc` | KO → description | 4,938 | KO functional description |
| `kgroupec` | KO → EC number | 2,513 | EC linkage |
| `seedannotation` | SEED/RAST annotation per locus | 177,519 | Functional signal |
| `metacycpathway`, `metacycreaction` | MetaCyc pathway / EC lookups | 3,512 / 20,793 | Pathway consistency via EC |
| **`reannotation`** | **Price-curator re-annotation set (reference)** | **1,762** | Subtract from candidate pool |

### Candidate Pool Definition (Price-faithful specific phenotype)

A gene enters the candidate pool if it has **at least one experiment meeting the specific-phenotype criterion** (the Price-authoritative definition):

```
|fit| > 1  AND  |t| > 5  AND  |fit|_95 < 1  AND  |fit| > |fit|_95 + 0.5
```

We will implement this as a Spark DataFrame op after casting `fit` and `t` to double (see pitfall: "fit/t are strings"). We will **also** record a secondary "strong phenotype" flag (`|fit| > 2 AND |t| > 5`) so each candidate carries both labels.

### Stubborn Set

```
stubborn_set = candidate_pool  SET MINUS  reannotation
```

Join on `(orgId, locusId)`.

### Key Analyses

1. **Count + distribution** of the stubborn set by organism, by condition class (`expGroup`), and by original annotation (hypothetical / DUF / named but wrong / named + reasonable).

2. **Evidence-scoring per stubborn gene** — a reproducible, curator-free scoring of the evidence Price would have seen:
   - `conserved_cofit`: any (locusId, hitId) pair with `cofit > 0.6` whose orthologs also have `cofit > 0.6` (via `ortholog`)?
   - `conserved_specific_phenotype`: does `specog` contain this gene with multiple orgs in the same `expGroup` / `condition`?
   - `domain_informative`: any `genedomain` hit with `ec IS NOT NULL` or with a `definition` that is not "domain of unknown function"?
   - `kegg_ko_informative`: KO with non-"uncharacterized" `kgroupdesc.desc`?
   - `seed_informative`: `seedannotation` description that is not "hypothetical"?
   - `metacyc_pathway_hit`: any MetaCyc pathway reachable via EC numbers from the above?

3. **Partition** the stubborn set by total evidence score: "Improvable" (≥1 conservation signal AND ≥1 informative functional signal) vs. "Unresolvable" (no conservation + no informative signal). Report an intermediate "Mixed" bucket for transparency.

4. **Validation spot-check**: sample ~20 "Improvable" genes and manually compare what Price's curators *could* have seen to what they wrote (or didn't). This is a qualitative sanity check, not a scaled validation.

5. **Characterization**: for both partitions, describe length, conservation breadth (ortholog count), whether they're in the functional_dark_matter 17,344 strong-phenotype dark set, and whether they're in truly_dark_genes' 6,427 bakta-resistant set. This connects to prior work without duplicating it.

### Performance Plan

- **Tier**: JupyterHub Spark (via `/berdl-query` proxy chain locally for iterative work). All primary compute stays in Spark DataFrames; `.toPandas()` only for final small summary tables.
- **Estimated complexity**: Moderate. The 27M-row `genefitness` scan + `fit|_95` computation per gene is the heaviest step but is a groupBy over `(orgId, locusId)`.
- **Known pitfalls** (from [docs/pitfalls.md](../../docs/pitfalls.md)):
  - `fit`, `t` are stored as strings → `CAST(... AS DOUBLE)` before `ABS` or comparison.
  - FB KO mapping is a two-hop join (`besthitkegg` → `keggmember`).
  - `kgroupdesc` column is `desc`, not `description`.
  - `experiment.expGroup` (not `Group`).
  - Always filter `cofit` by `orgId` and either `locusId` or `hitId`.

## Analysis Plan

### Notebook 01: Candidate pool + stubborn set definition
- **Goal**: Compute the specific-phenotype candidate pool, subtract the BERDL `reannotation` set, produce the stubborn-set gene list as a Delta/Parquet artifact under `data/`.
- **Expected output**: `data/stubborn_set.parquet` (orgId, locusId, strong_flag, specific_flag, n_specific_experiments, representative_condition), summary counts table, figure: stubborn-set size per organism.

### Notebook 02: Evidence scoring
- **Goal**: For each gene in the stubborn set, compute the six evidence flags above. Preserve the per-flag booleans so reviewers can audit the partition.
- **Expected output**: `data/stubborn_set_scored.parquet`, figure: evidence-flag combinatorial distribution (upset-plot style).

### Notebook 03: Partition + characterization
- **Goal**: Apply the partition rule, characterize the two buckets (length, conservation breadth, condition class, original annotation wording, overlap with `truly_dark_genes` and `functional_dark_matter` sets). Produce the headline figures.
- **Expected output**: `data/stubborn_set_partitioned.parquet` (adds `bucket` column), headline figures, numeric summaries.

### Notebook 04: Spot-check and narrative
- **Goal**: Pull ~20 Improvable candidates (selected to cover multiple organisms and functional classes) and render a per-gene dossier (fitness heatmap for the driving condition, top cofitness partners and their annotations, best ortholog + its phenotype, domain hits). This is qualitative evidence that the partition is sensible.
- **Expected output**: `data/spot_check_dossiers/*.md` or a single notebook-rendered table, plus a short narrative feeding into REPORT.md.

## Expected Outcomes

- **If H1 supported**: We produce a principled partition: a set of ~N "Improvable" genes (likely a few hundred) where evidence already in BERDL would support a proposed annotation, and a set of ~M "Unresolvable" genes where even the strong phenotype is not enough to propose a function from existing evidence. The Improvable list is an immediately actionable follow-up (send to a curator, seed a proposal-generation run, target for experiment).
- **If H0 not rejected**: The stubborn set looks like random poorly-annotated genes across all evidence flags — meaning curator decisions are not well-reconstructed from this evidence alone, or the decisions were driven by scope (transporter/catabolism focus) and timing rather than evidence strength. That's still an informative negative result.
- **Potential confounders**:
  - The paper's 2018 re-annotation set is narrower than the current `reannotation` table (which includes post-publication curator additions). Using the current table means we're asking "what did curators leave alone *through 2026*", not "what did curators leave alone *in 2018*". We'll note this explicitly.
  - Some loci in the candidate pool may be in organisms that were added to the Fitness Browser after the paper (the table covers 36 of 48 orgs, suggesting newer organisms haven't been curated yet). We'll check.
  - `genedomain.ec` and `kgroupec` coverage are sparse; absence of an EC doesn't always mean absence of function.
  - Specific-phenotype definition is an intersection of four criteria — some true-positive functional phenotypes will fail (e.g., pleiotropic but strong). This conservativism is intentional (we mirror Price) but worth stating.

## Revision History
- **v1** (2026-04-24): Initial plan.

## Authors
- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
