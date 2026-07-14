# Alm, Huang & Arkin (2006) — Methodology Reference Memo

**Source paper**: Alm, E.J., Huang, K., Arkin, A.P. (2006). "The evolution of two-component systems in bacteria reveals different strategies for niche adaptation." *PLoS Computational Biology* 2(11):e143. doi:10.1371/journal.pcbi.0020143. PMC1630713.

**Memo author**: discovered during `gene_function_ecological_agora` project (Phase 1B, 2026-04-27); broadly relevant to any BERIL project that builds on Alm 2006 framing.

**Why this memo exists**: The Alm 2006 paper is widely cited as the canonical "producer/consumer asymmetry in HGT" study. In practice, the paper's actual claims and methodology are more circumscribed than the descriptions in many follow-up works (including, until this memo, our own). This memo is a careful read-through to set the record straight for any BERIL project that needs to build on Alm 2006.

## What Alm 2006 actually did

### Substrate

- **Detection**: histidine protein kinases (HPKs) identified by **InterPro IPR005467** (HisKA / phosphoacceptor) signature OR membership in **COG4582** (signal-transduction histidine kinase).
- **Aggregation level**: **single domain (IPR005467)**, not multi-domain architecture and not family aggregation. Quote: *"we are inferring histories for only the HPK domain of signaling proteins... can be very different from the evolutionary histories of associated signaling domains."*
- **Genomes**: 207 sequenced prokaryotic genomes (the corpus available in 2006).

### Methodology

- **Tree-aware reconciliation, not permutation null.** Alm 2006 inferred ancestral states with maximum-likelihood phylogenetic trees and assigned events as either:
  - **LSE (lineage-specific expansion)**: paralog duplication within a clade, identified by tree topology
  - **HGT (horizontal gene transfer)**: identified by phylogenetic incongruence between gene tree and species tree
- **HGT confirmation**: validated by checking upstream-domain conservation against tree-predicted partners — *if X transferred from clade A to clade B, the predicted donor's signaling domains should match the recipient's*.
- **Validation**: reproduced findings under a more conservative HGT definition (absence from three consecutive outgroups). No multiple-testing correction. No null simulations.

### Their actual claims

The paper does **NOT** use the labels "producer", "consumer", "pioneer", "sapper", or any four-quadrant taxonomy of clades. Those are downstream constructions by later work.

What Alm 2006 *did* claim:

1. **Correlation between HPK abundance and recent LSE fraction**: ordinary least-squares regression r = 0.74, p < 10⁻¹⁵. *"The fraction of HPKs in a genome involved in recent LSE correlates strongly with the total number of HPKs in that genome."*
2. **Threshold classification of "HPK-enriched" genomes**: genomes devoting ≥ 1.5% of genes to HPKs.
3. **Difference between HGT and LSE in domain conservation**: 47.4% of HGT-acquired HPKs retain identical upstream signaling domains vs 29.1% of recent LSE-acquired HPKs.
4. **Qualitative descriptions of HGT-rich vs LSE-rich genomes**, e.g., specific Cyanobacteria as LSE-rich, certain enterics as HGT-rich. These are described visually from figures, not assigned categorical quadrants.

### Effect-size grammar

- **Percentages and counts**: "47.4 % vs 29.1 %", "≥ 1.5 % HPK content", N HPKs per genome
- **Correlation r**: r = 0.74 for the central LSE-vs-count regression
- **No Cohen's d**, no z-scores, no fold-changes
- The 207-genome substrate constrained the kind of effect sizes they could meaningfully report

## What Alm 2006 did NOT do

- Did not name "producer" / "consumer" / "pioneer" / "sapper" categories
- Did not use a four-quadrant framework
- Did not propose that the asymmetry generalizes beyond HKs
- Did not test regulatory-vs-metabolic differences
- Did not use parent-rank dispersion or any rank-stratified permutation null
- Did not aggregate to KO / Pfam architecture / family-level beyond the IPR005467 domain
- Did not apply multiple-testing correction
- Did not provide quantitative thresholds for "pioneer" vs "sapper" (the labels aren't in the paper)

## Implications for BERIL projects building on Alm 2006

### Substrate-hierarchy claims

A project that says "we aggregate above UniRef50 because Alm 2006 worked at family level and we expect signal at coarser substrate" is misreading Alm 2006. They worked at the *single domain level* (IPR005467 ≈ Pfam PF00512 + variants). That's *directly comparable* to UniRef50 in granularity. Their methodology got clean signal at this resolution; if a project's methodology fails to reproduce at the same resolution, the *metric* is more likely the issue than the *substrate*.

### Tree-aware metric is the canonical approach

Alm 2006's central inference depended on phylogenetic-tree reconciliation — they had a species tree, they inferred ancestral states per HPK family, they classified each event as LSE or HGT by tree topology. Any "Alm-2006-style" methodology that doesn't include a tree-aware step is using a proxy. Cheap proxies (parent-rank dispersion, prevalence-based statistics) may not reproduce Alm 2006's findings even on the same data because they don't measure the same thing.

For BERIL projects at GTDB scale where full DTL reconciliation is infeasible:
- **Sankoff parsimony score** (binary gain/loss on a fixed tree) is the lightweight alternative
- **Mantel correlation between presence dissimilarity and tree distance** is even lighter
- Both use the GTDB-r214 newick (downloadable from `data.gtdb.ecogenomic.org/releases/release214/`)

### The four-quadrant framework is post-Alm

The "Open Innovator / Broker / Sink / Closed Innovator" / "pioneer / sapper" / etc. labels are *constructions of follow-up work*, not part of Alm 2006. A BERIL project using this framework should:
- Acknowledge the framework as its own construction
- Provide independent theoretical justification for the four-quadrant categorization
- Cite Alm 2006 only as inspiration, not as generalization target

### Effect-size grammar mismatch

If a BERIL project compares its findings to Alm 2006:
- Alm 2006 effect sizes are percentages and correlation r
- Modern norms favor Cohen's d, fold-changes, or odds ratios
- These are not directly interconvertible. *"Alm 2006 found a 47.4 % vs 29.1 % difference"* is not comparable to *"we found Cohen's d ≈ 0.07"* without translating to a common grammar.
- Best practice: report fold-change ratios alongside Cohen's d.

### Multiple-testing not in scope

Alm 2006 didn't apply any multiple-testing correction. A BERIL project that does (correctly, given modern norms and larger N) is *more rigorous than the original*, not less. But this also means follow-up work cannot use "Alm 2006 didn't apply MTC and got clean signal" as cover for omitting MTC at modern scale.

## Recommended citations for BERIL projects

When a BERIL project cites Alm 2006:
- For the canonical *correlation* between HPK count and LSE fraction: cite Alm 2006 directly with the r = 0.74 number
- For domain-level HGT detection: cite Alm 2006 with the 47.4 %/29.1 % numbers
- For "pioneer / sapper" or four-quadrant frameworks: **do not** cite Alm 2006 alone — these are downstream constructions and need independent justification
- For tree-aware reconciliation: cite Alm 2006 + Szöllősi 2013 + Morel 2024 (modern DTL methods)

## Memo history

- **2026-04-27**: Created during `gene_function_ecological_agora` Phase 1B post-gate review. Triggered by adversarial reviewer's correctly-flagged effect-size mismatch (Cohen's d ≈ 0.07 not comparable to Alm 2006's correlation r = 0.74). Author: Adam Arkin's `gene_function_ecological_agora` project, via close re-reading of the original paper.
