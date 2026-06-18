# Inline citations, project pages, and Cosma connectivity

**Date:** 2026-06-18
**Status:** approved (proceed to implementation)

## Problem

The KG wiki ends every page with a `## Sources` block of raw
`[stmt:<slug>; <project>]` references. For a scientist reader these are
unreadable identifiers that link to nothing. In the Cosma graph view the
problem is worse: 1,487 of these slug lines leak into node bodies as dead
bracket-text (Cosma only converts real `[label](page.md)` links into graph
edges), so the graph shows raw, disconnected references. Projects named in
prose are backtick code spans, not links, so the richest text never connects
to the project graph nodes.

The user wants: citations placed **inline at the claim** (scientific-paper
style), **readable**, and resolving to **per-project pages**.

## Design

### 1. Inline citations (publish-time transform)

`kg-write` stops emitting a trailing `## Sources` block and instead places its
existing `[stmt:id; project]` tokens **inline, immediately after the clause each
statement backs**. The only LLM behavior change is placement.

`write_page_artifact` (publish) then transforms each draft deterministically
(new module `pages/citations.py`):

- strip any author-written `## Sources` section,
- collect inline `[stmt:id; project]` tokens in first-appearance order, dedupe
  by id (same claim cited twice → same number), validate every id is a page
  member (raise otherwise; raise if a page with members cites none),
- rewrite each token to a numbered marker `[\[N\]](#references)`,
- append a `## References` section: `N. [Project Title](<rel>/projects/<slug>.md) — REPORT.md › "Section".`

The project link in each reference is a real Markdown link, so Cosma's existing
`.md`-link → `[[wikilink]]` rewrite turns it into a graph edge. The marker
target `#references` is an in-page anchor (`check` skips `#` targets).

### 2. Project pages (new `project` page type)

- `models.PAGE_TYPES` gains `"project"`; `artifact._PAGE_DIRS` gains
  `"project": "projects"` → published at `wiki/projects/<slug>.md`.
- `plan.py` emits one `project:<id>` plan per project that has statements,
  members = that project's cards, wired out to its topics / data / authors.
  Project pages are **excluded** from the home page's blanket link set and from
  topic/data/author adjacency (projects are reached via citations, not nav
  clutter).
- Body = **deterministic stub + short LLM lead** (new module
  `pages/project_page.py`):
  - `# <Project Title>`
  - LLM-written 2–3 sentence lead (the only prose `kg-write` produces here),
  - `## Key findings` = the project's statement texts, verbatim, with confidence,
  - `## Topics` / `## Data` / `## Authors` links,
  - `[Open the full report →](../../../projects/<id>/REPORT.md)`.
- Project pages skip the citation transform (they list their own statements).

### 3. Backtick project mentions → links

A publish-time pass (`pages/citations.link_project_mentions`) rewrites
`` `<project_id>` `` in prose to `[`<project_id>`](<rel>/projects/<slug>.md)` for
known projects, so prose connects to project pages in both Obsidian and Cosma.

### 4. Cosma cleanup

`render/cosma.py` drops the synthetic `_project_links`/`_project_record` stubs.
Project nodes now come from the real `projects_<slug>.md` page records. The
existing link rewriter handles the new References + mention links automatically.

### 5. check.py

- Drop the now-inert orphan-citation check (integrity is enforced at publish).
- `_dangling_links` skips link targets that resolve outside the wiki root
  (e.g. the source `REPORT.md`), treating them as external.

## Touch points

`models.py`, `pages/plan.py`, `pages/artifact.py`, new `pages/citations.py`,
new `pages/project_page.py`, `render/cosma.py`, `check.py`, `cli.py` (pass
`page_plans` to `write_page_artifact`), `skills/kg-write/SKILL.md`,
`skills/kg-wiki/SKILL.md`, and the corresponding tests.

## Out of scope

Regenerating the published `wiki/**` and `cosma/**` — that is a pipeline run via
the `kg-wiki` orchestrator after the code lands. No hand-editing of the wiki.
