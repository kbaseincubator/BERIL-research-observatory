---
id: topic.amr-resistance-ecology
title: AMR, Resistance Ecology, and Co-selection
type: topic
status: draft
summary: Synthesis of AMR gene distribution, fitness cost, cofitness support networks, environment structure, and metal co-selection opportunities.
source_projects:
  - amr_environmental_resistome
  - amr_pangenome_atlas
  - amr_fitness_cost
  - amr_cofitness_networks
  - amr_strain_variation
  - resistance_hotspots
  - prophage_amr_comobilization
  - microbeatlas_metal_ecology
source_docs:
  - docs/discoveries.md
  - projects/prophage_amr_comobilization/REPORT.md
  - projects/microbeatlas_metal_ecology/REPORT.md
related_collections:
  - kbase_ke_pangenome
  - kescience_fitnessbrowser
  - enigma_coral
  - arkinlab_microbeatlas
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - claim.amr-is-environment-structured
  - claim.metal-specific-genes-core-enriched
  - claim.prophage-density-predicts-amr-breadth
  - claim.metal-type-diversity-predicts-niche-breadth
  - direction.metal-amr-co-selection
  - hypothesis.metal-amr-co-selection
  - data.amr-fitness-profiles
  - data.metal-tolerance-scores
  - conflict.metal-amr-co-selection-readiness
  - opportunity.metal-amr-site-analysis
order: 20
---

# AMR, Resistance Ecology, and Co-selection

## Synthesis Takeaway

BERIL treats antimicrobial resistance as an ecological system, not a flat clinical annotation list. Across the current AMR projects, resistance genes become more interpretable when they are placed in genome background, environment, mobile context, and measured fitness cost. That makes metal co-selection a concrete DOE-site analysis rather than a loose analogy.

## Review Brief

What changed: prophage density and metal type diversity are now explicit covariates for AMR ecology. That makes the co-selection question more testable, but also harder to interpret without mobile-element and taxonomy controls.

Why review matters: this topic can easily overstate co-selection. Human feedback should decide whether the page is appropriately framed as "ready to test" rather than "already proven."

Evidence to inspect:

- `amr_environmental_resistome`, `amr_pangenome_atlas`, and `resistance_hotspots` for environment-structured AMR.
- `amr_fitness_cost` and `amr_cofitness_networks` for functional burden and support modules.
- `prophage_amr_comobilization` for the difference between species-level prophage burden and gene-level proximity.
- `microbeatlas_metal_ecology` for metal type diversity and ecological breadth.

Questions for reviewers:

- Are taxonomy, habitat, genome count, and mobile-element burden the right minimum controls before claiming metal-AMR co-selection?
- Should prophage density be treated as a confound, a mechanism candidate, or both?
- Are AMR burden, AMR mechanism composition, and metal type diversity being kept distinct enough?
- What result would move the co-selection hypothesis from draft to reviewed?

## Why This Topic Exists

AMR appears in projects that do not start as AMR projects: metal tolerance, environmental resistomes, mobile elements, pangenomes, and cofitness analyses all touch the same biological space. This topic gives humans and agents a place to connect those views while keeping the strongest caveats visible.

## What We Have Learned

### Layer 1 - Pangenome Distribution

`amr_pangenome_atlas` and `amr_strain_variation` frame AMR genes as core, accessory, and strain-variable genome features. The important shift is that resistance is no longer only "gene present in genome." It can be asked as: is the resistance determinant conserved in a lineage, recently acquired, strain-variable, or part of a broader accessory-gene package?

This layer supports provenance questions. If an AMR signal is mostly accessory, mobile context and sampling become load-bearing. If it is core or clade-stable, ecology and lineage history become harder to separate.

### Layer 2 - Environment Structure

`amr_environmental_resistome` reports strong environmental structure in resistance mechanism composition. Soil and aquatic contexts are especially important because they carry both antibiotic-resistance and metal-resistance mechanisms. The Atlas should treat that pattern as a map of where to look next, not as proof that any one contaminant caused the distribution.

Environment structure becomes actionable when it is joined to taxonomy, collection provenance, and contamination metadata. Without those controls, habitat and phylogeny can look like selection even when they are acting as confounders.

### Layer 3 - Fitness And Support Networks

`amr_fitness_cost` and `amr_cofitness_networks` connect AMR to measurable burden and support neighborhoods. This is the difference between "gene is present" and "gene matters in this biological context." It also changes what should be promoted as reusable data: a resistance gene with a repeatable cost profile or cofitness support module is more useful than a gene call alone.

This layer is where AMR starts to overlap with engineering. If costs are predictable, agents can propose compensatory modules, strain-design constraints, or conditions where resistance is likely to be unstable.

### Layer 4 - Co-selection Opportunity

The overlap between metal biology and AMR ecology is a high-value research direction. Contaminated sites may select metal tolerance and AMR together, but BERIL should only state that as a tested result after the analysis controls for taxonomy, environment class, sampling, and mobile-element burden.

The current evidence supports readiness, not closure: the Atlas has metal tolerance scores, AMR clusters, environmental metadata, and DOE-site context. The next useful product is a co-selection model that can say where metal tolerance and AMR move together after the obvious confounders are removed.

### Layer 5 - Prophage Context And Strain Variation

Mobile elements, plasmids, phage, and strain-specific accessory regions can make AMR look environment-structured even when the immediate driver is horizontal transfer. `prophage_amr_comobilization` turns that caveat into a measurable covariate: prophage density strongly predicts AMR repertoire breadth across species, while direct AMR-prophage proximity is weaker and threshold-sensitive.

The synthesis should therefore distinguish two statements. First, prophage burden marks genomes and species with broader AMR repertoires. Second, the evidence for direct phage cargo transfer is more nuanced and still needs dedicated prophage callers, base-pair distances, and plasmid/ICE partitioning.

### Layer 6 - Metal Resistance Breadth And Niche Breadth

`microbeatlas_metal_ecology` adds a field-ecology layer to AMR. Metal type diversity, not raw AMR burden, predicts genus-level niche breadth after phylogenetic correction. This supports the idea that the breadth of resistance mechanisms matters for ecological range and for contaminated-site co-selection analyses.

## Evidence Detail For Review

The strongest reusable AMR evidence is not a single gene table. It is the agreement between mechanism composition, pangenome context, measured cost, cofitness support, and environmental structure. If those layers point in different directions, the Atlas should record the disagreement rather than collapsing it into a broad resistance claim.

The prophage result is especially useful for review because it names a measurable covariate that can explain AMR breadth without proving direct gene transfer. A reviewer should check whether any future co-selection model includes prophage density or a better mobile-element partition before interpreting AMR-environment associations as selection by metal exposure.

The metal type diversity result is similarly useful but observational. It supports the idea that resistance-spectrum breadth matters, while leaving open whether breadth is caused by environmental exposure, lineage history, mobile elements, or sampling coverage.

## What Would Change This Synthesis

- A controlled DOE-site analysis showing no association between metal contamination and AMR after taxonomy and habitat controls would weaken the co-selection direction.
- A mobile-element analysis showing that the strongest environment signals are entirely plasmid or phage driven would shift emphasis from environmental selection to transfer ecology.
- Fitness screens showing that common AMR determinants have no measurable burden in relevant hosts would weaken cost-based prioritization.
- A dedicated prophage/plasmid/ICE partition showing that prophage density is only a proxy for general genome openness would narrow the prophage-AMR claim.

## High-Value Directions

- [Metal-AMR co-selection at contaminated DOE sites](/atlas/directions/metal-amr-co-selection)
- Build a resistance-support module catalog from cofitness neighborhoods.
- Compare clinical, soil, aquatic, and contaminated-site resistance architectures after phylogenetic control.
- Add prophage density, metal type diversity, and mobile-element burden as explicit covariates in co-selection models.

## Open Caveats

- AMR annotations can mix mechanistic resistance, stress response, transport, and mobile-element context.
- Environment metadata remains uneven across genomes.
- Co-selection is plausible but must be tested against nulls and confounders.
- Strain variation can create strong signals even when species-level summaries look stable.
- Prophage marker density is not the same as proven phage-mediated AMR transfer.

## Open Tensions

- [Metal-AMR co-selection readiness](/atlas/conflicts/metal-amr-co-selection-readiness) keeps the metal co-selection idea framed as an unresolved analysis rather than a proven result.

## Reusable Claims

- [AMR mechanism composition is environment-structured](/atlas/claims/amr-is-environment-structured) is the core claim for this topic.
- [Metal-specific genes remain core-enriched](/atlas/claims/metal-specific-genes-core-enriched) becomes relevant when resistance is evaluated alongside metal tolerance.
- [Prophage density predicts AMR repertoire breadth](/atlas/claims/prophage-density-predicts-amr-breadth) makes mobile context a concrete AMR covariate.
- [Metal type diversity predicts ecological niche breadth](/atlas/claims/metal-type-diversity-predicts-niche-breadth) connects resistance breadth to field ecology.

## Data Dependencies

- Pangenome collection pages provide genome and gene-family context for AMR clusters.
- Fitness Browser provides costs and cofitness signals that distinguish present genes from functional burden.
- ENIGMA and environmental metadata provide the contamination and habitat context needed for co-selection tests.
- Mobile-element and phage markers provide a transfer-context layer that should be joined before interpreting environment structure as direct selection.

## Opportunity Hooks

- [Metal-AMR Site Co-Selection Analysis](/atlas/opportunities/metal-amr-site-analysis) is the most direct next analysis for this topic because it tests whether AMR environment structure overlaps with metal contamination after controlling for taxonomy and habitat.

## Drill-Down Path

Start with the environment-structured AMR claim, then open the prophage-density claim, the metal-AMR direction, and the metal contamination co-selection hypothesis. From there, inspect AMR fitness profiles, metal tolerance scores, and mobile-element covariates before treating co-selection as a project proposal.

## How Agents Should Use This Page

Use this topic when proposing AMR, resistance ecology, mobile-element resistance, or contaminated-site co-selection work. Preserve confound controls for taxonomy, environment, mobile context, and annotation uncertainty.
