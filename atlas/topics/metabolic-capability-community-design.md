---
id: topic.metabolic-capability-community-design
title: Metabolic Capability, Dependency, and Community Design
type: topic
status: draft
summary: Synthesis of GapMind capability, fitness dependency, metabolic models, community ecology, and design-ready derived data.
source_projects:
  - metabolic_capability_dependency
  - pathway_capability_dependency
  - essential_metabolome
  - fw300_metabolic_consistency
  - nmdc_community_metabolic_ecology
  - pseudomonas_carbon_ecology
  - harvard_forest_warming
source_docs:
  - docs/discoveries.md
  - docs/schema.md
  - projects/harvard_forest_warming/REPORT.md
related_collections:
  - kbase_ke_pangenome
  - kbase_msd_biochemistry
  - kescience_fitnessbrowser
  - nmdc_arkin
  - nmdc_metadata
  - nmdc_results
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - claim.lab-fitness-predicts-field-ecology
  - claim.pangenome-openness-shapes-function
  - direction.fitness-validated-community-design
  - data.fitness-phenotypes
  - data.genomes-and-pangenomes
  - data.multi-omics-embeddings
  - opportunity.cf-formulation-reuse
  - opportunity.functional-innovation-ko-reuse
order: 90
---

# Metabolic Capability, Dependency, and Community Design

## Synthesis Takeaway

Encoded metabolic capability is not the same as active dependency; the observatory can turn that distinction into community design rules and reusable metabolic derived products.

## Review Brief

What changed: this page now links capability, measured dependency, multi-omics interpretation, and community design in one review surface.

Why review matters: community design can look rigorous while still depending on unvalidated capability calls. Reviewers should check whether design proposals separate encoded potential, measured dependency, activity, compatibility, and ecological risk.

Evidence to inspect:

- `metabolic_capability_dependency`, `pathway_capability_dependency`, and `essential_metabolome` for capability versus dependency.
- `nmdc_community_metabolic_ecology`, `pseudomonas_carbon_ecology`, and `harvard_forest_warming` for community and perturbation context.
- [CF Formulation Scores](/atlas/data/derived-products/cf-formulation-scores) and [Functional Innovation KO Atlas](/atlas/data/derived-products/functional-innovation-ko-atlas) for reusable design substrates.
- [Multi-omics, embeddings, and molecular profiles](/atlas/data/types/multi-omics-embeddings) for activity and sample-context caveats.

Questions for reviewers:

- Which design claims rely only on encoded capability and need measured dependency or activity evidence?
- Are condition-specific fitness dependencies being generalized too broadly?
- What minimal validation should be required before recommending a community or formulation?
- Which derived product would most improve repeatable community-design decisions?

## What We Have Learned

### Layer 1 - Predicted Capability

GapMind and ModelSEED-derived resources describe what genomes appear capable of doing.

### Layer 2 - Measured Dependency

Fitness data distinguishes pathways that matter under tested conditions from latent capabilities that are present but not currently limiting.

### Layer 3 - Community Context

NMDC and environmental projects add community composition, pathway potential, and site context.

`harvard_forest_warming` adds a useful caution: encoded or observed functional shifts should be interpreted with sample design and omics layer in view. In that project, long-term warming produces comparable DNA and RNA functional-pool treatment effects after a horizon-by-incubation confound is removed, while specific C-cycling signals such as pmoA/pmoB and glyoxylate-cycle genes remain biologically informative.

### Layer 4 - Design

The applied target is minimal or robust communities chosen for tolerance, metabolism, low risk, and complementary function.

## High-Value Directions

- Create reusable pathway-dependency matrices.
- Build site-specific community design recipes for remediation or formulation.
- Link dependency profiles to pangenome openness and ecological breadth.

## Open Caveats

- GapMind pathway completeness does not prove expression or flux.
- Fitness dependency is condition-specific.
- Community design needs interaction validation, not only genome capability.
- Omics-layer functional profiles can converge or diverge depending on time scale and design confounds.

## Reusable Claims

- [Lab fitness can predict field ecology](/atlas/claims/lab-fitness-predicts-field-ecology) supports cautious translation from measured dependency to environment.
- [Pangenome openness shapes functional opportunity](/atlas/claims/pangenome-openness-shapes-function) helps explain why capability breadth varies by lineage.

## Data Dependencies

- [Metabolism, biochemistry, and pathways](/atlas/data/types/metabolism-biochemistry-pathways) provide pathway definitions and biochemical context.
- [Fitness and phenotypes](/atlas/data/types/fitness-phenotypes) provide measured dependency and essentiality.
- [Genome and pangenome data](/atlas/data/types/genomes-pangenomes) provide species and gene-family context for design candidates.
- [Multi-omics, embeddings, and molecular profiles](/atlas/data/types/multi-omics-embeddings) provide sample-level context for deciding whether a capability is present, active, or changing with perturbation.

## Opportunity Hooks

- [CF Formulation Score Reuse Test](/atlas/opportunities/cf-formulation-reuse) tests whether formulation scores improve a concrete design decision.
- [Functional Innovation KO Atlas Reuse Test](/atlas/opportunities/functional-innovation-ko-reuse) checks whether KO innovation signals explain pathway and capability variation beyond generic annotation summaries.

## Drill-Down Path

Start with the fitness-validated community design direction, then follow the fitness-phenotype data type and genome-fitness-pangenome join. That path moves from design concept to executable data joins.

## How Agents Should Use This Page

Use this topic when proposing remediation, formulation, or synthetic-community work. Separate encoded capability, measured dependency, environmental compatibility, and ecological risk before recommending organisms.
