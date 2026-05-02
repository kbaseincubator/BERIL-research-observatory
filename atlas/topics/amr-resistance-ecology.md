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
source_docs:
  - docs/discoveries.md
related_collections:
  - kbase_ke_pangenome
  - kescience_fitnessbrowser
  - enigma_coral
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-28
related_pages:
  - claim.amr-is-environment-structured
  - claim.metal-specific-genes-core-enriched
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

### Layer 5 - Mobile Context And Strain Variation

Mobile elements, plasmids, phage, and strain-specific accessory regions can make AMR look environment-structured even when the immediate driver is horizontal transfer. The mobile context should therefore be a required follow-up for strong AMR claims, especially claims about contaminated environments.

This layer should connect AMR pages to phage/mobile-element topics as those pages mature. Until then, AMR claims should keep mobility as an explicit caveat.

## What Would Change This Synthesis

- A controlled DOE-site analysis showing no association between metal contamination and AMR after taxonomy and habitat controls would weaken the co-selection direction.
- A mobile-element analysis showing that the strongest environment signals are entirely plasmid or phage driven would shift emphasis from environmental selection to transfer ecology.
- Fitness screens showing that common AMR determinants have no measurable burden in relevant hosts would weaken cost-based prioritization.

## High-Value Directions

- [Metal-AMR co-selection at contaminated DOE sites](/atlas/directions/metal-amr-co-selection)
- Build a resistance-support module catalog from cofitness neighborhoods.
- Compare clinical, soil, aquatic, and contaminated-site resistance architectures after phylogenetic control.

## Open Caveats

- AMR annotations can mix mechanistic resistance, stress response, transport, and mobile-element context.
- Environment metadata remains uneven across genomes.
- Co-selection is plausible but must be tested against nulls and confounders.
- Strain variation can create strong signals even when species-level summaries look stable.

## Open Tensions

- [Metal-AMR co-selection readiness](/atlas/conflicts/metal-amr-co-selection-readiness) keeps the metal co-selection idea framed as an unresolved analysis rather than a proven result.

## Reusable Claims

- [AMR mechanism composition is environment-structured](/atlas/claims/amr-is-environment-structured) is the core claim for this topic.
- [Metal-specific genes remain core-enriched](/atlas/claims/metal-specific-genes-core-enriched) becomes relevant when resistance is evaluated alongside metal tolerance.

## Data Dependencies

- Pangenome collection pages provide genome and gene-family context for AMR clusters.
- Fitness Browser provides costs and cofitness signals that distinguish present genes from functional burden.
- ENIGMA and environmental metadata provide the contamination and habitat context needed for co-selection tests.

## Opportunity Hooks

- [Metal-AMR Site Co-Selection Analysis](/atlas/opportunities/metal-amr-site-analysis) is the most direct next analysis for this topic because it tests whether AMR environment structure overlaps with metal contamination after controlling for taxonomy and habitat.

## Drill-Down Path

Start with the environment-structured AMR claim, then open the metal-AMR direction and the metal contamination co-selection hypothesis. From there, inspect the AMR fitness profiles and metal tolerance scores before treating co-selection as a project proposal.

## How Agents Should Use This Page

Use this topic when proposing AMR, resistance ecology, mobile-element resistance, or contaminated-site co-selection work. Preserve confound controls for taxonomy, environment, mobile context, and annotation uncertainty.
