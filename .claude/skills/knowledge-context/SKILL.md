---
name: knowledge-context
description: Use when searching BERIL project/docs context through OpenViking or refreshing the indexed context layer before research, synthesis, or pitfall work.
allowed-tools: Bash, Read
user-invocable: true
---

# Knowledge Context Skill

OpenViking holds an indexed context layer over BERIL projects and central docs. Use it for fast recall, then read the underlying file before editing or citing — search results are a map, not the source of truth.

## Resource layout

- Projects: `viking://resources/projects/<project_id>/`
  - Curated files: `README.md`, `RESEARCH_PLAN.md`, `REPORT.md`, `REVIEW.md`, `references.md`, `FINDINGS.md`, `EXECUTIVE_SUMMARY.md`, `FAILURE_ANALYSIS.md`, `DESIGN_NOTES.md`, `CORRECTIONS.md`, `beril.yaml`
  - `PROJECT_METADATA.md` — generated table with project_id, title, status, authors, dates, branch, engine. Use this for "by author / by status" lookups (search the project URI, not a global index — the index doesn't exist).
- Central docs: `viking://resources/docs/<slug>/` for `pitfalls`, `discoveries`, `performance`, `research_ideas`.

## Picking the right primitive

```
QUERY="uv run --env-file .env knowledge/scripts/knowledge_query.py"
```

| Question | Use | Why |
|---|---|---|
| Free-text / fuzzy ("anything about phage timing?") | `find` | Semantic top-K |
| Time-bounded ("changed in last 7d") | `find --since 7d --time-field updated_at` | Server-side time filter |
| Exact name / ID / ORCID ("all projects mentioning Ada Lovelace") | `grep` | Deterministic, exhaustive — `find` may cut off |
| Enumerate URIs ("list every project") | `glob` or `ls` | Embeddings can't enumerate; this is a filesystem question |
| Inspect a single resource | `stat`, `overview`, `read` | Direct access |
| Walk a subtree | `tree` | Hierarchical view |
| Cross-resource links | `relations` | See § Relations |

### `find` — semantic search

```bash
$QUERY find "query terms"
$QUERY find "query terms" --project <project_id>     # one project
$QUERY find "query terms" --docs                     # central docs only
$QUERY find "query terms" --target-uri viking://resources/projects/alpha/REPORT.md
$QUERY find "query terms" --since 7d --time-field updated_at
$QUERY find "query terms" --score-threshold 0.5 --limit 25
$QUERY find "query terms" --json
```

Power filter — pass an OV filter tree directly:

```bash
$QUERY find "query terms" --filter '{"op":"must","field":"uri","conds":["viking://resources/projects/alpha/"]}'
```

Filter ops the OV vector index supports: `must` (eq/in on a metadata field), `range` (gt/lt/gte/lte), `time_range`, `and` / `or` over `conds`. `--since`/`--until`/`--time-field` build the `time_range` for you.

### `grep` — exact-pattern search

Deterministic, exhaustive across **all ingested file content** under the `--uri` subtree. Best for keyword lookups where `find` ranking would silently drop matches. Note that matches include incidental mentions, not just structured fields — see § Workflows for the by-author caveat.

```bash
$QUERY grep "Ada Lovelace" --uri viking://resources/projects/
$QUERY grep "ORCID-0000" --uri viking://resources/ -i
$QUERY grep "TODO" --uri viking://resources/projects/alpha/ --node-limit 50
$QUERY grep "deprecated" --uri viking://resources/ --exclude-uri viking://resources/docs/
```

Flags: `-i/--case-insensitive`, `--node-limit N`, `--exclude-uri <uri>`.

### `glob` — URI pattern enumeration

Pattern is **relative** to `--uri`. Defaults to `viking://`.

```bash
$QUERY glob '*' --uri viking://resources/projects/                     # one project per row
$QUERY glob '**/*.md' --uri viking://resources/projects/alpha/         # all .md files in a project
$QUERY glob '**/REPORT.md' --uri viking://resources/projects/          # every project's REPORT.md
```

### `ls`, `tree`, `stat` — structural navigation

```bash
$QUERY ls viking://resources/projects/ --simple        # path list
$QUERY ls viking://resources/projects/alpha/ -r        # recursive
$QUERY tree viking://resources/projects/alpha/         # hierarchy
$QUERY stat viking://resources/projects/alpha/         # metadata for one URI
```

### `overview`, `read` — resource access

```bash
$QUERY overview viking://resources/projects/<id>/      # L1 summary
$QUERY read viking://resources/projects/<id>/REPORT.md # full content
```

## Relations

Relations are general OpenViking edges between any two URIs — they're not project-specific and not limited to projects-pointing-at-projects. Use them for any cross-resource linkage you want to recall later: project → relevant pitfall, project → related project, doc → exemplar project, etc.

```bash
$QUERY relations viking://resources/projects/<id>/                # outgoing edges
$QUERY link <from_uri> <to_uri> [<to_uri> ...] --reason "<why>"   # one or many targets
$QUERY unlink <from_uri> <to_uri>                                 # remove one edge
```

`link` accepts multiple target URIs in a single call — each becomes its own edge, all sharing the supplied `--reason`. `unlink` removes one edge at a time.

Examples:

```bash
# Link a project to a pitfall it ran into
$QUERY link viking://resources/projects/alpha/ \
  viking://resources/docs/pitfalls/ --reason "hit data-leak pitfall"

# Link two related projects bidirectionally (auto-link is one-way)
$QUERY link viking://resources/projects/alpha/ viking://resources/projects/beta/ --reason "shared cohort"
$QUERY link viking://resources/projects/beta/ viking://resources/projects/alpha/ --reason "shared cohort"

# Inspect
$QUERY relations viking://resources/projects/alpha/
```

### Auto-linking from `beril.yaml`

The only relation source ingest creates automatically is the optional `related_projects:` list in a project's `beril.yaml`:

```yaml
project_id: alpha
related_projects:
  - beta
  - gamma
```

During `ingest_context.py`, ingest emits `link(alpha, [beta, gamma], reason="beril.yaml related_projects")`. Caveats:

- One-way only — add a reciprocal entry in the other project, or `link` it manually.
- Missing target IDs are silently skipped (so a typo doesn't break ingest).
- Self-references are skipped.
- Re-ingesting re-applies the links (idempotent on the OV side).

For everything else (project→doc, doc→doc, file-level links), use the `link` command directly.

## Refreshing context

```bash
INGEST="uv run --env-file .env knowledge/scripts/ingest_context.py"
$INGEST --project <project_id>     # after editing one project
$INGEST --changed                  # after mixed edits — diffs against state manifest
$INGEST --all                      # full refresh
$INGEST --all --limit 5            # cap project count (rate-limited VLMs)
$INGEST --docs                     # central docs only
```

`--changed` and `--all` reconcile by manifest diff: removed projects are unlinked from OV automatically. `--limit` caps how many projects ingest in one run and writes a partial manifest so a follow-up `--changed` finishes the rest.

## Configuration

`.env` (copy from `.env.example`):

- `OPENVIKING_URL` — defaults to `http://127.0.0.1:1933`
- `OPENVIKING_API_KEY` — only when the server enforces auth (remote deployments)

Local server: copy `knowledge/openviking/ov.conf.example` → `knowledge/openviking/ov.conf` and set the OpenRouter key in `embedding` and the CBORG key in `vlm`. The local `ov.conf` is gitignored.

```bash
uv run --group knowledge openviking-server doctor --config knowledge/openviking/ov.conf
uv run --group knowledge openviking-server --config knowledge/openviking/ov.conf
```

Both `ingest_context.py` and `knowledge_query.py` probe `OPENVIKING_URL` before opening a client and exit cleanly with a hint when the server isn't reachable — no Python traceback.

After the server is running, smoke-test ingest + query for the five most-recently-modified projects:

```bash
uv run knowledge/scripts/smoke_ingest_openviking.py
```

## Common workflows

**"Find all projects by an author"** — `grep` is exhaustive but matches **all** file content, not just author rows. So expect false positives from incidental mentions in REPORT/README/references. To get an authoritative list, scope to the structured metadata file via post-filtering:

```bash
$QUERY grep "Ada Lovelace" --uri viking://resources/projects/ \
  | jq '[.matches[] | select(.uri | endswith("/PROJECT_METADATA.md")) | (.uri | capture("projects/(?<id>[^/]+)/").id)] | unique'
```

(`grep` always emits JSON, no `--json` flag needed.) The unfiltered `grep` is still useful as a starting set — the URI tells you whether the hit is in metadata vs prose.

**"What changed in the last week?"** — `find` requires a non-empty query (server rejects `""`). Use a topic word or a broad term:

```bash
$QUERY find "BERIL" --since 7d --time-field updated_at --limit 50 --json
```

For a truly content-agnostic recency view, prefer `ls` / `tree` / `stat` and read the `modTime` field.

**"List every project"** — filesystem question, not a search question:

```bash
$QUERY ls viking://resources/projects/ --simple
# or, glob (pattern is relative to --uri):
$QUERY glob '*' --uri viking://resources/projects/
```

**"What does this project relate to?"**

```bash
$QUERY relations viking://resources/projects/<id>/
$QUERY overview viking://resources/projects/<id>/
```

**"Link a project to its pitfall"** — durable cross-link, surfaces in future `relations` calls:

```bash
$QUERY link viking://resources/projects/<id>/ \
  viking://resources/docs/pitfalls/ --reason "<short why>"
```
