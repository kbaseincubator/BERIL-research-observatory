---
id: opportunity.dark-gene-structure-prioritization
title: Dark Gene Structure Prioritization
type: opportunity
status: draft
summary: Prioritize dark gene families for mechanistic review by joining fitness, cofitness, annotation novelty, and AlphaFold structure signals.
source_projects:
  - truly_dark_genes
  - functional_dark_matter
  - cofitness_coinheritance
  - metal_specificity
source_docs:
  - docs/discoveries.md
  - docs/structural_biology_memory.md
related_collections:
  - kbase_uniprot
  - kescience_alphafold
  - kbase_ke_pangenome
  - kescience_interpro
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - topic.fitness-validated-function
  - data.dark-gene-prioritization
  - data.genes-proteins-annotations
  - hypothesis.structure-supports-metal-binding
opportunity_status: candidate
opportunity_kind: analysis
impact: high
feasibility: medium
readiness: medium
evidence_strength: medium
linked_conflicts:
  - conflict.metal-specificity-vs-general-stress
linked_products:
  - data.dark-gene-prioritization
target_outputs:
  - Ranked dark-family review queue with fitness, cofitness, annotation, and structure evidence.
  - Reviewer-facing packets for high-value unknown families.
  - Caveat labels separating structural plausibility from validated function.
review_routes:
  - truly_dark_genes
  - functional_dark_matter
  - cofitness_coinheritance
evidence:
  - source: data.dark-gene-prioritization
    support: Dark gene prioritization is already promoted as a reusable candidate-list product.
  - source: cofitness_coinheritance
    support: Cofitness and coinheritance help separate isolated hits from functional modules.
order: 70
---

# Dark Gene Structure Prioritization

## Why It Matters

Dark genes are where the Atlas can create new biological value, but only if prioritization is disciplined. This opportunity turns a broad unknown set into a ranked review queue that combines multiple evidence modes.

## Review Brief

What changed: the dark-gene derived product now has a broader review brief, so this opportunity should specify the first actionable characterization packet.

Why review matters: reviewers should decide which dark-gene candidates deserve scarce structural, genetic, or biochemical follow-up.

Evidence to inspect:

- [Dark Gene Prioritization Tables](/atlas/data/derived-products/dark-gene-prioritization) for candidate rankings.
- `functional_dark_matter`, `truly_dark_genes`, and `cofitness_coinheritance` for evidence components.
- AlphaFold, InterPro, UniProt, and pangenome context for annotation and structural priors.

Questions for reviewers:

- Which evidence mix is sufficient for a first characterization packet?
- Are structural hints being presented as hypotheses rather than function calls?
- Which candidates are likely annotation lag and should be routed to curation?
- What experiment or analysis would resolve the top candidate's function?

## Evidence Base

The strongest candidates should have fitness relevance, cofitness or coinheritance support, annotation novelty, and structural features that make a mechanism plausible. Structural hints alone are not function, but they can route scarce review effort.

## Work Package

Join dark-family candidates with cofitness modules, annotation databases, AlphaFold structures, topology predictions, and any metal-specific signals. Package each high-priority family with evidence, caveats, and suggested validation.

## Decision Use

This creates a reusable queue for structural biology and functional annotation work. It also provides a template for how Atlas opportunities should move from large candidate lists to reviewer-sized decisions.
