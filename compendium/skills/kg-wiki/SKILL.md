---
name: kg-wiki
description: Orchestrator and single entry point for the BERIL KG-wiki. Chains the whole pipeline over projects/ — context-pack + kg-extract per project, one global kg-reconcile, plan + wiki-contexts, kg-write per changed page (parallel, reusing unchanged pages), render-markdown, a final check gate, and export-cosma + cosma modelize for the graph+wiki viewer. This is the only skill a user normally invokes.
---

# kg-wiki

The user-facing orchestrator. It chains the deterministic `compendium` CLI steps and dispatches the
three LLM skills (`kg-extract`, `kg-reconcile`, `kg-write`) end-to-end:

```
projects/* ─pack─▶ context-packs/  ─kg-extract─▶ kg/<id>.kg.yaml
   all cards ─kg-reconcile─▶ registry.yaml
   merged kg + registry ─plan─▶ out/page-contexts/  ─kg-write─▶ wiki/*.md
                       ─render-markdown─▶ wiki/  ─check─▶ exit 0/nonzero
```

`pack`, `plan-pages`, `wiki-contexts`, `render-markdown`, and `check` are deterministic (no model).
`render-markdown` does **not** generate prose — it validates and publishes the pages `kg-write`
already authored, so `kg-write` must run before it. This skill absorbs the old batch/backfill loop.

## Inputs

- Required: the `projects/` corpus (default `../projects` from inside `compendium/`). May be filtered
  to a subset of project ids.
- Optional: existing `compendium/kg/*.kg.yaml`, `compendium/registry.yaml`, and `compendium/wiki/`
  for incremental reuse.

## Outputs

- `compendium/context-packs/<id>.json`, `compendium/kg/<id>.kg.yaml` (per project).
- `compendium/registry.yaml` (global, from `kg-reconcile`).
- `compendium/out/page-contexts/**` (deterministic page contexts/prompts).
- `compendium/wiki/**/*.md` + `compendium/wiki/.manifests/**` (the human-facing wiki).
- A clean `compendium check` (exit 0) as the final gate.

## Workflow

1. **Extract per project.** For each project in scope, run the deterministic pack then dispatch
   `kg-extract`. Parallelize across projects (independent inputs):
   ```bash
   cd compendium
   uv run compendium context-pack ../projects/<id> --out context-packs/<id>.json
   # then dispatch kg-extract for <id> -> writes kg/<id>.kg.yaml
   ```
   Skip a project whose `kg/<id>.kg.yaml` is current (same context-pack hash) unless re-extraction
   is requested.

2. **Reconcile once (global).** After all in-scope `kg/*.kg.yaml` exist, dispatch `kg-reconcile`
   exactly once. It reads every raw `entities`/`topics` slug and writes/extends
   `compendium/registry.yaml` (append-only). No human gate.

3. **Build the merged corpus KG.** `plan-pages`/`wiki-contexts`/`render-markdown` take a single KG
   file, so concatenate every `kg/*.kg.yaml`'s `statements` into one mapping (dedupe by `id`):
   ```bash
   cd compendium
   uv run python3 - <<'PY'
   import glob, yaml, pathlib
   seen = {}
   for f in sorted(glob.glob("kg/*.kg.yaml")):
       for s in (yaml.safe_load(open(f)) or {}).get("statements", []):
           seen.setdefault(s["id"], s)
   pathlib.Path("out/corpus.kg.yaml").write_text(
       yaml.safe_dump({"project": {"id": "corpus", "title": "BERIL corpus"},
                       "statements": list(seen.values())}, sort_keys=False))
   print("merged statements:", len(seen))
   PY
   ```
   Use `out/corpus.kg.yaml` as `<kg>` in the steps below.

4. **Plan + build page contexts** (deterministic; both load `registry.yaml` + author/data indexes
   from `--source-root`):
   ```bash
   cd compendium
   uv run compendium plan-pages <kg> --source-root ../projects --out out/page-plans.json
   uv run compendium wiki-contexts <kg> --source-root ../projects --out out/page-contexts
   ```

5. **Write changed pages.** Determine changed pages by comparing each page plan / context
   `member_hash` with the existing `wiki/.manifests/**/*.manifest.json`. Reuse pages whose member
   hash still matches; for each changed page dispatch `kg-write` (parallel subagents where
   possible — give each one page id + one `.context.json`). `kg-write` publishes via `page-artifact`
   into `wiki/`. The page set now includes one `project:<id>` page per project (published under
   `wiki/projects/`); their `kg-write` subagent writes only a short lead, and `page-artifact`
   assembles the stub. Topic/data/author/home pages carry inline `[stmt:id; project]` citations that
   `page-artifact` rewrites into a linked `## References` list.

   **Model selection.** The deterministic harness owns all structure (membership, the
   inline-citation → References rewrite, project links, the project-page stub, and validation), so
   the subagent model only affects prose quality and cannot corrupt the output. Dispatch each
   `kg-write` subagent with:
   - **Haiku** for `project:<id>` pages — they are a 2-3 sentence lead, so the smallest model is
     plenty and much faster/cheaper.
   - **Sonnet** for `topic` / `data` / `author` / `home` synthesis pages — capable of the
     multi-section synthesis and far faster than Opus.
   - **Opus** only if the user explicitly wants maximum polish on the showcase pages (the 12 topic
     pages + `home`); otherwise Sonnet is the default.
   Pass the chosen model id through to `page-artifact --model` so the manifest records it.

6. **Render + final gate** (deterministic). `render-markdown` validates/assembles the published
   pages; `check` is the integrity gate:
   ```bash
   cd compendium
   uv run compendium render-markdown <kg> --source-root ../projects --out wiki
   uv run compendium check --wiki wiki
   ```
   `check` exits nonzero on any dangling link (citation integrity is enforced earlier, at
   `page-artifact` publish time). If it fails, fix the offending page (re-dispatch `kg-write`) or
   re-run `kg-reconcile` (e.g. an unresolved topic) and repeat steps 4–6 until `check` exits 0.

7. **Export the graph + wiki viewer** (deterministic export + one Node build). After `check`
   passes, emit the Cosma reader graph (topic/project/data/author records + config) and build the
   self-contained cosmoscope:
   ```bash
   uv run compendium export-cosma <kg> --source-root ../projects --wiki wiki --out cosma
   (cd cosma && npx -y @graphlab-fr/cosma modelize)   # → cosma/cosmoscope.html
   ```
   `export-cosma` is deterministic (no model); `cosma modelize` is the only Node build step.
   `cosma/` is a generated artifact (gitignored).

8. Summarize: projects extracted/skipped, registry topics/entities, pages written vs reused, the
   final `check` status, and the cosmoscope path. The entry point for readers is
   `compendium/wiki/index.md`.

## Subagent contract

When dispatching `kg-extract` give the subagent one project id. When dispatching `kg-write` give the
subagent one page id + the path to its single `.context.json` (+ `.prompt.md`) and the merged-kg
path. Subagents return only their written artifact path + a short note; they must not edit other
projects' KGs, `registry.yaml`, manifests, tests, or unrelated wiki pages.

## Prohibitions

- Do not author prose from Python; prose comes only from `kg-write` subagents.
- Do not skip the final `compendium check` — it is the acceptance gate.
- Do not run `kg-reconcile` more than once per orchestration pass.
- Do not edit Python code, tests, or docs from this skill.
