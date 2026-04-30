---
id: meta.metrics-to-watch
title: Metrics To Watch
type: meta
status: draft
summary: Maintenance signals for evaluating whether the Atlas is becoming more useful to humans and agents.
source_projects: []
source_docs:
  - ui/config/berdl_collections_snapshot.json
  - docs/collections.md
related_collections: []
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-29
related_pages:
  - meta.roadmap
  - method.agent-maintenance
order: 2
---

# Metrics To Watch

## Why This Page Exists

The Atlas should become more useful as the observatory grows. Maintenance metrics help agents notice where the corpus is strong, where coverage is thin, and where claims are accumulating caveats.

## Signals

- **Collection coverage**: canonical BERDL databases with `data_collection` pages.
- **Cross-collection reuse**: projects that combine two or more collections.
- **Under-explored collections**: discovered databases with no parsed project references.
- **Dark-matter metadata**: collections with weak curation, missing schemas, or discovery caveats.
- **Caveat load**: low-confidence pages that need review before supporting major claims.
- **Evidence coverage**: claims, directions, hypotheses, and derived products with evidence metadata.
- **Topic drill-down depth**: topic pages with enough structure and links to support progressive disclosure.
- **Derived product reuse**: promoted derived products with at least one declared downstream project.
- **Unresolved tensions**: conflict pages still requiring resolving analysis or experiments.
- **Topic visual coverage**: topic pages with enough metadata to render generated overview maps.

## How Agents Should Use This

Agents should run `python -m app.wiki_inventory .. --format markdown` before proposing updates. The Atlas inventory report should guide whether the next edit should add a collection page, improve a data-type lens, record a missing join, promote a reusable derived product, or document a tension that needs resolving work.
