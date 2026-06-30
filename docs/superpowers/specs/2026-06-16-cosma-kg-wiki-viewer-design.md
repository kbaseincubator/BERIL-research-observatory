# Cosma KG + Wiki Viewer — Design

Status: draft for review · 2026-06-16 · owner: Dileep Kishore

## 1. Context and decision

The compendium produces a topic-MOC synthesis wiki (Markdown under `compendium/wiki/`)
backed by a lightweight context graph (statement cards + `registry.yaml`). We want to
**visualize the knowledge graph and the wiki together** — an Obsidian-style interactive
graph beside readable content.

After a web survey and two working spikes over the real wiki (see
`compendium/spike/`), we chose **Cosma** (`graphlab-fr/cosma`, GPL-3.0/CeCILL-2.1,
actively maintained, v2.6.1) over building a custom viewer or adopting Quartz. Cosma
exports a **single self-contained `cosmoscope.html`** — a three-column UI (filters ·
interactive force graph · rendered record) with click-to-open, typed/colored node
types, search, backlinks, and a neighborhood "focus" mode — that any static server can
serve with no runtime or bundler. The spike confirmed the UX is what we want.

Locked decisions (from brainstorming):

- **Scope:** the **reader graph** — `topic · project · data · author` nodes. Statement-level
  edges (`supports`/`contradicts`/`refines`) are out of scope for v1.
- **Projects are nodes.** Synthesize a lightweight Cosma record per project. Projects are
  the connective tissue that makes the topic↔topic structure visible.
- **v1 is artifact-only.** Produce `cosmoscope.html` as a build artifact plus a regenerate
  command. Wiring a FastAPI route into the UI is a deferred follow-up.
- **Theme:** light/white.

## 2. Goals and non-goals

**Goals**

- A deterministic `compendium export-cosma` step that emits a Cosma project (`src/` records
  + `config.yml`) from the same inputs the page planner already uses.
- A documented one-command build (`cosma modelize`) that turns that project into
  `cosmoscope.html`, folded into the `kg-wiki` orchestrator so the graph never drifts from
  the wiki.
- The reader graph includes project nodes wired to their topics, authors, and collections.

**Non-goals (v1)**

- No FastAPI route / iframe / app-chrome integration (deferred).
- No statement-level "tensions" graph (`supports`/`contradicts`/`refines`).
- No Cosma CSV mode, no typed/colored edges, no custom CSS theming beyond the light palette.
- No committed `node_modules`; Cosma runs via `npx`.

## 3. Where it fits in the pipeline

`export-cosma` is a new **deterministic** step (no LLM), a sibling of `render-markdown`. It
runs after the wiki is published, consuming the published wiki Markdown plus the same
indexes the planner uses.

```
… ─[LLM] kg-write ─▶ wiki/*.md ─[D] render-markdown ─▶ published wiki
                                          │
                       cards + registry + authors + collections + wiki/*.md
                                          │
                          ─[D] export-cosma ─▶ cosma/src/*.md + cosma/config.yml
                                          │
                          ─[build] cosma modelize ─▶ cosma/cosmoscope.html
```

The deterministic Python step owns *what the graph is*; the `cosma modelize` build owns
*rendering it to one HTML file*. This keeps the no-LLM/reproducible boundary the rest of
the system follows.

## 4. The `export-cosma` step

New module `src/compendium/render/cosma.py` (sibling of `render/markdown.py`), a CLI
subparser in `cli.py`, and a dispatch branch in `pipeline.py`.

```
# run from compendium/ (like the other CLI commands)
uv run compendium export-cosma <kg-path> \
  --source-root ../projects \
  --wiki wiki \
  --out cosma
```

Inputs (all already available to the planner):

- statement cards (`kg/*.kg.yaml`) — give projects, canonical topics per project.
- `registry.yaml` via `compendium.registry.Registry` — canonical topic/entity keys + labels.
- author index via `people.py` (ORCID → projects).
- collection index via `data_index.py` (collection → projects), from `ui/config/collections.yaml`.
- published wiki Markdown (`wiki/*.md`) — the authored prose for page records.

Output (`compendium/cosma/`):

- `src/*.md` — one Cosma record per node.
- `config.yml` — generated, with the light theme + typed `record_types`.

### 4.1 Records (nodes)

**Page records** (home / topic / data / author) — reuse the **authored wiki prose** so the
right-hand content pane shows the real wiki. Conversion (proven in the spike):

- Add YAML frontmatter: `title` (from the page H1), `type` (`home`/`topic`/`data`/`author`).
- Rewrite `[Label](relpath.md)` cross-links to `[[Target Title|Label]]` wikilinks. These
  reproduce the existing page↔page edges (topic↔adjacent-topic, topic→data, etc.).
- Strip the leading H1 (Cosma renders the title from frontmatter).

**Project records** (the new nodes) — synthesized stubs, since projects deliberately have no
wiki page (they are shown by their own reports). Each project record carries:

- frontmatter `title` (project title) + `type: project`.
- a short deterministic body: a one-line descriptor + a "Related" block of `[[wikilinks]]`
  to the project's canonical **topics**, **authors**, and **data collections**, derived from
  `plan_pages` joins (`project_topics`, author/collection indexes). These wikilinks are the
  project→{topic,author,data} edges.
- optionally a link to the project's report (path under `--source-root`) for provenance.

Edges are therefore a union of: page↔page (from rewritten prose links) and project→page
(from plan-derived `[[wikilinks]]` in project stubs). All derivation is deterministic and
order-independent (sorted), matching the system's reproducibility guarantee.

### 4.2 Config

Generated `config.yml` (the spike's, with the light theme):

- `select_origin: directory`, `files_origin: ./src`, `export_target: ./`.
- `record_types`: `home`/`topic`/`data`/`author`/`project`, each with a `fill`/`stroke` color.
- `focus_max: 1` — neighborhood "local graph" by default (keeps ~70 project nodes navigable).
- `graph_background_color: "#ffffff"`, `graph_highlight_color: "#ff6a6a"`, light palette.
- `generate_id: always` (Cosma assigns internal ids; links resolve by title).
- `title`, `description`, `lang: en`.

### 4.3 Build

`cosma modelize` (run in `compendium/cosma/`, via `npx @graphlab-fr/cosma`) reads
`config.yml` + `src/` and writes `cosmoscope.html`. Documented in `compendium/README.md`
and invoked by the `kg-wiki` orchestrator after `render-markdown`/`check`.

## 5. Determinism, files, and versioning

- The Python step is deterministic: same cards + registry + wiki ⇒ byte-identical `src/` and
  `config.yml` (sorted records, sorted links).
- `compendium/cosma/src/` and `compendium/cosma/cosmoscope.html` are **generated artifacts**
  → add to `compendium/.gitignore` (alongside `kg/`, `out/`). `config.yml` is generated by the
  step too, so it is also gitignored; the generator is the source of truth.
- Cosma itself is a build-time dependency invoked via `npx` (no committed `node_modules`).

## 6. Testing

Follows the existing deterministic-core test style (no LLM, no network):

- Unit: page-record conversion (frontmatter + link rewrite) on a fixture wiki page.
- Unit: project-stub synthesis emits correct `[[topic]]/[[author]]/[[data]]` links from a
  fixture card set + author/collection indexes.
- Determinism: running `export-cosma` twice on the `fixtures/statement_cards/` set yields
  identical `src/` bytes.
- Smoke: `cosma modelize` is **not** run in CI (Node dependency); instead assert the emitted
  `config.yml` validates against the documented Cosma schema and `src/*.md` parse as records
  (frontmatter present, wikilinks resolvable to emitted record titles).

## 7. Integration and docs

- `kg-wiki` orchestrator (skill): add the `export-cosma` + `cosma modelize` steps after the
  wiki render/check, reusing unchanged-page logic.
- `compendium/README.md`: document the new step + build command in the pipeline section.
- `docs/kg-wiki/methodology.md` / redesign doc: a short note that the cosmoscope is the
  reader-facing graph view (infrastructure for navigation, consistent with "the wiki is the
  product").

## 8. Risks / open points

- **Graph readability at ~70 projects.** Mitigated by `focus_max: 1` (local graph) + Cosma's
  type filters (deselect `project` to see the topic/data/author backbone). Revisit node sizing.
- **Project content is thin** (stubs by design). Acceptable: projects are shown by their full
  reports; the stub links out. If richer project records are wanted later, pull the report's
  summary section deterministically.
- **Title-based linking** requires unique record titles. Topic/data/author/project titles are
  unique today; if a collision appears, fall back to explicit Cosma `id:` per record.
- **GPL/CeCILL copyleft** applies to the Cosma tool, not to the generated `cosmoscope.html`
  artifact we serve. Building a *modified* Cosma would inherit copyleft; we don't.

## 9. Deferred follow-ups

- FastAPI route serving `cosmoscope.html` (iframe in app chrome), linked from wiki/atlas nav.
- Statement-level "tensions" lens (typed `supports`/`contradicts`/`refines` edges), likely via
  Cosma typed `link_types` or a separate view.
- Custom CSS to match the app's typography/colors.
