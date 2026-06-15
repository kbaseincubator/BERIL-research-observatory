---
name: kg-reconcile
description: Global autonomous second pass that builds compendium/registry.yaml. Reads every raw about.entities/about.topics slug across all kg/*.kg.yaml and emits canonical topics + entities with aliases. No human approval gate; acceptance is the deterministic plan + check pass.
---

# kg-reconcile

Run this once, globally, after all per-project `kg/*.kg.yaml` exist (and re-run when new projects
are added). It owns the topic vocabulary and ships **autonomously** — there is no human approval
step (D3). Its only output is `compendium/registry.yaml`, an **additive** lookup layer that the
deterministic `plan` consults via `compendium.registry.Registry`. Cards are never rewritten (D2):
the registry maps raw per-project slugs onto canonical keys through `aliases`.

## Inputs

- All `compendium/kg/*.kg.yaml` — read every card's `about.entities` and `about.topics`, dedupe to
  one flat list of raw slugs (a few hundred strings).
- The §5 seed topic themes from `docs/kg-wiki/2026-06-15-kg-wiki-redesign.md` — an **optional
  prior** the LLM may revise, merge, split, or rename. Not a fixed vocabulary.
- The existing `compendium/registry.yaml` if present — extend it append-only.

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
      kind: organism            # organism | dataset | gene | method
      aliases: [entity:adp1, a_baylyi_adp1, acinetobacter_baylyi, adp1]
  ```

`projects:` lists are filled deterministically by `plan`; you do not need to populate them.

## Workflow

1. Collect the deduped raw-slug list from every KG file. A quick way to enumerate:
   ```bash
   cd compendium
   for f in kg/*.kg.yaml; do uv run compendium plan-pages "$f" --out /tmp/_r.plan.json >/dev/null; done
   ```
   (any traversal of the YAML works; the goal is the full deduped `about.entities` +
   `about.topics` set.)
2. For **topics**: cluster the raw topic slugs into canonical themes guided by D5 (a topic spans
   ≥2, ideally ≥3 projects; aim for ~12 topics across the corpus). Use the §5 seed list as a prior.
   Each raw topic slug must map into exactly one canonical theme via that theme's `aliases`. Give
   each canonical topic a one-line `definition`.
3. For **entities**: group obvious synonyms of the same organism/dataset/gene/method under one
   canonical key with `kind` and an `aliases` list. Leave a slug unmapped (no entry) when it has no
   confident canonical home — `Registry` passes unknown slugs through unchanged, which is safe.
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
- Do not author wiki pages, page plans, or statement cards. Output is `registry.yaml` only.
- Do not edit Python code, tests, schema, or docs.
