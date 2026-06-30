---
name: kg-reconcile
description: Global autonomous second pass that builds compendium/registry.yaml. Reads every raw entities/topics slug across all kg/*.kg.yaml and emits canonical topics + broad recurring entities with aliases and plain definitions. No human approval gate; acceptance is the deterministic plan + check pass.
---

# kg-reconcile

Run this once, globally, after all per-project `kg/*.kg.yaml` exist (and re-run when new projects
are added). It owns the topic vocabulary and ships **autonomously** — there is no human approval
step (D3). Its only output is `compendium/registry.yaml`, an **additive** lookup layer that the
deterministic `plan` consults via `compendium.registry.Registry`. Cards are never rewritten (D2):
the registry maps raw per-project slugs onto canonical keys through `aliases`.

## Inputs

- All `compendium/kg/*.kg.yaml` — read every card's `entities` and `topics`, dedupe to
  one flat list of raw slugs (a few hundred strings).
- The seed topic themes below — an **optional prior** the LLM may revise, merge, split, or rename.
  Not a fixed vocabulary. (Canonical source: `../docs/kg-wiki/2026-06-15-kg-wiki-redesign.md` §5,
  relative to the repo root.)
- The existing `compendium/registry.yaml` if present — extend it append-only.

### Seed topics (prior, ~12 for ~70 projects)

AMR & the Resistome · Metal Resistance & Critical Minerals · Pangenome Architecture (Core/Accessory
& Openness) · Gene Fitness & Genotype→Phenotype · Functional Dark Matter & Annotation Gaps ·
Microbial Ecotypes & Niche Differentiation · Subsurface & Clay-Confined Genomics (ENIGMA) · Mobile
Genetic Elements & HGT · Metabolic Capability, Pathways & Dependency · *A. baylyi* ADP1 Model System
· Environment, Biogeography & Geospatial Embeddings · Microbiome Engineering & Health Applications.

A project belongs to 1–3 topics; the overlap is the cross-project connection structure.

## Outputs

- `compendium/registry.yaml` only, shaped:
  ```yaml
  topics:
    metal-resistance:
      label: Metal Resistance & Critical Minerals
      definition: <one line>
      aliases: [metal_fitness, topic:metal-resistance, critical-minerals, ...]
  entities:
    adp1:
      label: Acinetobacter baylyi ADP1
      kind: organism
      definition: A naturally competent soil bacterium used as a model system for metabolism and genetics.
      aliases: [entity:adp1, a_baylyi_adp1, acinetobacter_baylyi, adp1]
      url: https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=62977
  ```

`projects:` lists are filled deterministically by `plan`; you do not need to populate them.

## Workflow

1. Collect the deduped raw-slug list from every KG file. A quick way to enumerate:
   ```bash
   cd compendium
   for f in kg/*.kg.yaml; do uv run compendium plan-pages "$f" --out /tmp/_r.plan.json >/dev/null; done
   ```
   (any traversal of the YAML works; the goal is the full deduped `entities` + `topics` set.)
2. For **topics**: cluster the raw topic slugs into canonical themes guided by D5 (a topic spans
   ≥2, ideally ≥3 projects; aim for ~12 topics across the corpus). Use the §5 seed list as a prior.
   Each raw topic slug must map into exactly one canonical theme via that theme's `aliases`. Give
   each canonical topic a one-line `definition`.
3. For **entities**: keep only broad, recurring, page-useful nodes. Prefer concepts that help the
   writer define the page subject or connect pages. Use this small kind set: `organism`,
   `compound`, `gene_or_pathway`, `method`, `dataset`, `place`, `concept`. Add a one-sentence
   plain-language `definition` for every entity. Add `url` only when a stable public page is obvious.
   Leave a slug unmapped (no entry) when it has no confident canonical home — `Registry` passes
   unknown slugs through unchanged, which is safe.
4. When extending an existing `registry.yaml`: keep every existing canonical key and its current
   aliases; only add new keys or append new aliases. Never rename or remove a canonical key.
5. Write `compendium/registry.yaml`.
6. Acceptance is deterministic (no human gate). Build the merged corpus KG (the union of all
   `kg/*.kg.yaml` statements, as `kg-wiki` does), then run plan + render + check; there must be no
   broken links and no unresolved-topic problems:
   ```bash
   cd compendium
   uv run compendium plan-pages <merged-kg> --source-root ../projects --out /tmp/plan.json
   uv run compendium render-markdown <merged-kg> --source-root ../projects --out wiki   # via kg-write pages
   uv run compendium check --wiki wiki
   ```
   In practice the `kg-wiki` orchestrator runs this acceptance loop; this skill is done once
   `registry.yaml` is written and a fresh `plan` resolves every topic.

## Prohibitions

- Never edit `kg/*.kg.yaml`. The registry is additive; cards stay immutable.
- Never delete or rename an existing canonical key (append/extend only, so keys stay stable across
  runs).
- Never invent an entity or topic that is absent from the input slug list.
- Do not create exhaustive ontology-like entity lists. The registry should stay small enough to read.
- Do not author wiki pages, page plans, or statement cards. Output is `registry.yaml` only.
- Do not edit Python code, tests, or docs.
