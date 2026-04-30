---
id: method.reuse-and-tension-workflow
title: Reuse and Tension Workflow
type: method
status: draft
summary: Manual workflow for promoting derived products, routing review, and recording conflicts without an always-on LLM agent.
source_projects: []
source_docs:
  - docs/discoveries.md
  - docs/pitfalls.md
related_collections: []
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-30
related_pages:
  - data.reuse
  - conflicts.index
  - opportunities.index
  - person.index
order: 50
---

# Reuse and Tension Workflow

## Promote A Derived Product

Promote an output when it has a name, producer, artifact, caveat trail, and likely downstream use. Add a `derived_product` page with `product_kind`, `reuse_status`, `produced_by_projects`, `used_by_projects`, `output_artifacts`, and `review_routes`.

## Record A Tension

Create a `conflict` page when two results appear to disagree, when a caveat changes interpretation, or when a direction is plausible but unresolved. The page must record evidence on multiple sides and the analysis or experiment that would resolve the tension.

## Record An Opportunity

Create an `opportunity` page when a tension, data gap, or reusable product has a concrete next analysis. The page must record status, kind, impact, feasibility, readiness, evidence strength, target outputs, linked products or tensions when relevant, and review routes.

## Route Review

Use source projects and producer projects first. If a page combines multiple project families, route review to at least one owner of the most load-bearing product and one neighboring reviewer from an affected topic.

## Maintenance Commands

Run `python -m app.wiki_lint ..` and `python -m app.wiki_inventory .. --format markdown` after every Atlas maintenance pass.
