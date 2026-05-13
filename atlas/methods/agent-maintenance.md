---
id: method.agent-maintenance
title: Agent Maintenance Workflow
type: method
status: draft
summary: Rules for future agents maintaining the markdown Atlas without turning it into an unstructured data dump.
source_projects: []
source_docs:
  - docs/discoveries.md
  - docs/pitfalls.md
  - docs/performance.md
  - ui/config/collections.yaml
related_collections: []
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-28
related_pages:
  - method.progressive-disclosure
  - method.reuse-and-tension-workflow
  - meta.lint-rules
  - meta.review-queue
order: 20
---

# Agent Maintenance Workflow

## Update Loop

1. Read changed project reports, discoveries, pitfalls, collection docs, and derived outputs.
2. Decide whether the change affects a topic, claim, data page, direction, or hypothesis.
3. Update the smallest page that captures the new knowledge.
4. Preserve provenance and caveats.
5. Run Atlas lint.
6. Compare inventory output to the [Atlas Review Queue](/atlas/meta/review-queue).
7. Flag pages needing human review.

## Creativity Rule

Agents may create new page types within the allowed taxonomy when they improve reuse, discovery, or scientific reasoning. Every new page must justify its existence.

## Review Rule

Lint passing means the graph is structurally valid. It does not mean the science is correct.

## Queue Rule

Prefer one complete update packet over scattered shallow edits. A useful packet deepens synthesis, updates provenance, records caveats, and leaves a reviewer with a clear next decision.
