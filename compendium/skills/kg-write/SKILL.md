---
name: kg-write
description: Author ONE wiki page (topic/data/author/home) from a single deterministic page context. The LLM writes clean human-readable markdown; provenance goes in one consolidated Sources section using [stmt:id; project] footnote refs. Publishes via page-artifact, which validates the citations.
---

# kg-write

Author one page per run from a fixed, bounded page context produced deterministically by
`compendium page-context`. Page membership, links, and source excerpts are chosen by Python — this
skill only writes the prose and publishes it through the validator. It is an internal helper the
`kg-wiki` orchestrator dispatches per changed page; it is not the user-facing entry point. Write
clean academic prose like the Atlas, **not** inline machine citations in every paragraph.

## Inputs

- Required: a page id (e.g. `home`, `topic:metal-resistance`, `data:kescience_fitnessbrowser`,
  `author:0000-0001-5810-2497`) and the merged corpus KG file used by the orchestrator.
- Required: the deterministic page context `out/page-contexts/**/<id>.context.json` (+ `.prompt.md`)
  from `page-context`. It carries `page`, `statements`, `projects`, `topics`, `entities`,
  `adjacent_pages`, `narrative`, and `allowed_citations`.

Stop if the page context references statements absent from `statements` or the context cannot
be built.

## Outputs

- `compendium/wiki/<page_path>.md` — `index.md` (home), `topics/<slug>.md`, `data/<slug>.md`, or
  `authors/<slug>.md`.
- `compendium/wiki/.manifests/<page_path>.manifest.json` — provenance + `cited_statement_ids`,
  written by `page-artifact`.

## Workflow

1. Build the bounded page context (no model):
   ```bash
   cd compendium
   uv run compendium page-context <merged-kg> --page-id <page-id> --source-root ../projects --out out/page-contexts
   ```
2. Read the `<id>.context.json`. Write the page markdown from **only** that context, using
   `statements` text + `source_excerpt` for framing, `narrative.section_plan` for page shape,
   and `adjacent_pages` paths for navigation.

   Reader contract:
   - Write for a scientist-engineer who understands biology and data analysis but may not know this
     exact project niche.
   - The page must read as synthesized prose, not a list of extracted claims.
   - The first paragraph must define the page subject in plain language and state why the page exists
     in the wiki.
   - Each body section must combine related statements into a reasoned paragraph. Do not make one
     bullet per statement.
   - When an entity in the page context has a `definition`, use that definition naturally the first
     time the entity matters.
   - Define specialist terms in prose when they first appear. Examples: FBA, gapfilling, quinate,
     condition-dependent essentiality, TnSeq.
   - Explain connections: when linking another page, say why that page is adjacent.
   - Include caveats or uncertainty when the page context contains caveats, contradictions, low
     confidence statements, or thin evidence.

   Topic pages follow the MOC template (clean human-readable prose, not bullet dumps):
   - `# <title>`
   - `## Overview`
   - `## What the Corpus Shows`
   - `## Projects and Evidence`
   - `## Connections`
   - `## Caveats and Open Directions`

   Data / author / home pages use their natural sections (e.g. home: topic map, author map, data
   map; data: projects using this collection; author: projects, topics).
3. Provenance style: do NOT scatter `[stmt:id; project]` through the prose. Put every citation in a
   single consolidated `## Sources` section at the end as footnote-style refs, e.g.
   `- [stmt:adp1-deletion-continuum-claim; adp1_deletion_phenotypes]`. The validator (`page-artifact`
   / `check`) matches `[stmt:id; project]` anywhere in the page, so a consolidated Sources section
   satisfies it. A page with member statements MUST cite at least one of them, and may cite ONLY
   ids present in `allowed_citations`.
4. Insert relative Markdown links to related pages using the `adjacent_pages` paths (so `check`'s
   dangling-link guard passes).
5. Publish and validate (this is where citations are enforced):
   ```bash
   cd compendium
   uv run compendium page-artifact <merged-kg> --page-id <page-id> \
       --markdown <draft.md> --out wiki --source-root ../projects \
       --model <model-id> --prompt-hash <prompt-hash>
   ```
   `page-artifact` rejects the page if it cites a non-member id or (when members exist) cites none.
6. On rejection, retry the page at most twice using the validator error and the exact
   `statements` id list; never change membership to force prose through. If the page/member
   hash matches an existing manifest, reuse the cached page instead of regenerating.
7. Summarize the published page path, cited statement ids, and any uncertainty.

## Prohibitions

- Cite only allowed statements; never cite a statement id absent from this page's context.
- A `[stmt:...; project]` ref must name a real project; do not cite a project without a statement
  id.
- One page per run.
- Make no new scientific claims and add no statements, entities, topics, links, or page members.
- Use no source documents, literature, or web facts outside the deterministic page context.
- Do not edit `kg/*.kg.yaml`, `registry.yaml`, page plans, Python code, tests, or docs.
