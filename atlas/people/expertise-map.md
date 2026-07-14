---
id: person.expertise-map
title: Expertise Map
type: person
status: draft
summary: Topic-to-reviewer routing scaffold based on project ownership and source provenance.
source_projects:
  - metal_specificity
  - ibd_phage_targeting
  - plant_microbiome_ecotypes
source_docs:
  - README.md
  - docs/discoveries.md
related_collections:
  - kbase_ke_pangenome
  - kescience_fitnessbrowser
confidence: low
generated_by: Codex GPT-5
last_reviewed: 2026-04-28
related_pages:
  - person.index
  - method.agent-maintenance
order: 10
---

# Expertise Map

## Routing Rules

Use source-project authorship as the first reviewer signal. If a page integrates multiple source projects, route review to at least one owner of the most load-bearing project and one reviewer from a neighboring topic.

## Atlas Topic Routing

| Atlas Area | Likely Review Basis |
|---|---|
| Critical minerals | Metal fitness, metal specificity, BacDive validation |
| AMR ecology | AMR pangenome, environmental resistome, fitness cost |
| Pangenome architecture | Pangenome openness, COG analysis, conservation-fitness synthesis |
| Fitness function | Essential genome, fitness modules, metabolic dependency |
| Host microbiome translation | IBD phage targeting and rigor memories |
| Data products | Producing project plus downstream reuse project |

## Agent Rule

Do not mark a high-impact page as reviewed only because it linted cleanly. Lint checks structure; people review interpretation.
