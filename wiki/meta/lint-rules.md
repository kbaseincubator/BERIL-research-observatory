---
id: meta.lint-rules
title: Atlas Lint Rules
type: meta
status: draft
summary: Structural rules that keep the markdown Atlas navigable, provenance-backed, and agent-usable.
source_projects: []
source_docs:
  - README.md
related_collections: []
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-28
related_pages:
  - method.agent-maintenance
order: 10
---

# Atlas Lint Rules

## Required Frontmatter

Every markdown page needs `id`, `title`, `type`, `status`, `summary`, `source_projects`, `source_docs`, `related_collections`, `confidence`, `generated_by`, and `last_reviewed`.

## Provenance Rules

- `source_projects` must match project directories.
- `related_collections` must match configured UI collections.
- Topic pages need breadth.
- Claims, directions, hypotheses, and derived products need provenance and evidence metadata.

## Link Rules

Internal Atlas links should resolve to existing markdown pages, and page IDs should be unique.
