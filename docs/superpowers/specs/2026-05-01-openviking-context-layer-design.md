# OpenViking Context Layer Design

Date: 2026-05-01

## Scope

This design covers only the first branch goal: creating an OpenViking-backed
knowledge context layer for BERIL project information. The knowledge graph and
generated wiki layers are intentionally out of scope for this iteration.

The implementation should use OpenViking's Python SDK directly, keep code small,
and place context-related code under `knowledge/` at the repository root.

## Goals

- Ingest curated project context from `projects/` into OpenViking.
- Ingest selected central docs from `docs/` for now.
- Support both initial ingestion and incremental updates.
- Expose a thin query CLI usable by agents.
- Add Claude skills that explain how to query and update the context layer.
- Preserve a clean path for local OpenViking during development and remote
  OpenViking in production.

## Non-Goals

- Do not implement the knowledge graph layer.
- Do not implement generated wiki output.
- Do not ingest project figures or raw/generated data files in this iteration.
- Do not rewrite existing project Markdown files to add frontmatter.
- Do not build a custom retrieval engine around OpenViking.

## OpenViking Behavior Used

OpenViking will provide the L0/L1/L2 tiering:

- L0: short abstracts returned by search results.
- L1: directory/project overviews loaded with `overview(uri)`.
- L2: original file content loaded with `read(uri)`.

The ingestion code will reuse stable `to` URIs. OpenViking performs incremental
updates when `add_resource(..., to=<existing-uri>)` is called for an existing
target, reusing unchanged file summaries and vector records and recomputing
changed files plus affected directory summaries.

The query code will use:

- `find(query, target_uri=..., limit=...)` for L0 retrieval.
- `overview(uri)` for L1 project or docs overviews.
- `read(uri)` for L2 full content.

## Resource Layout

Use per-project stable targets:

```text
viking://resources/projects/{project_id}/
viking://resources/docs/{doc_slug}/
viking://resources/project_index/
```

This keeps incremental updates small and makes project-scoped queries explicit.

Examples:

```text
viking://resources/projects/metal_cross_resistance/
viking://resources/projects/metal_cross_resistance/REPORT.md
viking://resources/docs/pitfalls/
```

## Source Selection

For each `projects/{project_id}/`, include these files when present:

- `README.md`
- `RESEARCH_PLAN.md`
- `REPORT.md`
- `REVIEW.md`
- `references.md`
- `FINDINGS.md`
- `EXECUTIVE_SUMMARY.md`
- `FAILURE_ANALYSIS.md`
- `DESIGN_NOTES.md`
- `CORRECTIONS.md`
- `beril.yaml`

Exclude:

- `data/**`
- `figures/**`
- `notebooks/**`
- `.adversarial-debug/**`
- `ADVERSARIAL_REVIEW*.md`
- `PLAN_REVIEW*.md`
- `REVIEW_*.md`
- `QUICK*.md`
- `START_HERE.md`
- `WORKFLOW_TEST_RESULTS.md`
- `running_notes.md`
- validation, checklist, and setup-only documents unless later promoted into the
  include list.

For central docs, include these files for now:

- `docs/pitfalls.md`
- `docs/discoveries.md`
- `docs/performance.md`
- `docs/research_ideas.md`

Future updates to the pitfalls, discoveries, performance, and research idea
skills should write durable project-specific knowledge into the relevant
`projects/{project_id}/` directory when possible. Until then, these central docs
are ingested directly.

## Generated Metadata Context

OpenViking can ingest `beril.yaml`, but exact questions such as "which projects
are by this author?" are better served by a concentrated generated Markdown
metadata layer.

The staging process will generate, but not commit, these files:

```text
knowledge/staging/projects/{project_id}/PROJECT_METADATA.md
knowledge/staging/projects/PROJECT_INDEX.md
```

`PROJECT_METADATA.md` is generated from `beril.yaml` when present and from
simple README status/title fallbacks when needed. It should contain compact,
human-readable fields:

- Project ID
- Title
- Authors
- Status
- Created at
- Last session at
- Branch
- Engine
- Source metadata files

Current `beril.yaml` files use fields such as `project_id`, `status`,
`created_at`, `last_session_at`, `branch`, `engine.name`, `authors[].name`,
`authors[].affiliation`, `authors[].orcid`, and `artifacts`. The metadata
generator should read those names directly and tolerate missing fields by
leaving them blank in the generated Markdown.

`PROJECT_INDEX.md` contains one compact table across all staged projects:

```markdown
| Project | Title | Authors | Status |
|---|---|---|---|
```

The index is ingested to `viking://resources/project_index/` so broad metadata
queries can retrieve a concentrated source before searching every project. This
keeps the generated index target separate from `viking://resources/projects/`
and avoids parent/child subtree lock overlap during batch ingestion.

The source project files are not modified.

## Architecture

Place implementation under `knowledge/`:

```text
knowledge/
  openviking/
    ov.conf.example
  observatory_context/
    __init__.py
    config.py
    openviking_client.py
    selection.py
    staging.py
    ingest.py
    query.py
  scripts/
    ingest_context.py
    knowledge_query.py
  state/
    .gitkeep
  staging/
    .gitignore
```

Common code responsibilities:

- `config.py`: read `OPENVIKING_URL`, `OPENVIKING_API_KEY`, default target URIs,
  and repository paths.
- `openviking_client.py`: create and close a `SyncHTTPClient`.
- `selection.py`: decide which project/docs files belong in the context layer.
- `staging.py`: create the filtered staging tree and generated metadata docs.
- `ingest.py`: initial and incremental ingestion orchestration.
- `query.py`: format `find`, `overview`, and `read` results.

The code should remain intentionally small. OpenViking owns parsing, L0/L1
generation, vector indexing, semantic search, and incremental resource diffing.

## OpenViking Server Configuration

OpenViking server configuration lives in `knowledge/openviking/ov.conf` for
local branch development. This file should not be committed with real API keys.
The implementation should commit a template at:

```text
knowledge/openviking/ov.conf.example
```

The template should document the required settings and provide a working local
shape that users can copy to `knowledge/openviking/ov.conf`.
The real `knowledge/openviking/ov.conf` and generated
`knowledge/openviking/workspace/` should be ignored by git.

OpenViking needs two model capabilities:

- Dense embedding model: vectorizes resources for semantic retrieval.
- VLM/LLM model: parses rich inputs and generates L0/L1 semantic summaries.

Even though this iteration excludes figures and data, OpenViking still uses the
configured embedding model for search and the configured VLM/LLM for resource
understanding and L0/L1 generation.

The planned example for this repository should use OpenRouter through
OpenViking's OpenAI-compatible provider support:

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 1933
  },
  "storage": {
    "workspace": "knowledge/openviking/workspace"
  },
  "embedding": {
    "dense": {
      "provider": "openai",
      "api_key": "replace-with-api-key",
      "api_base": "https://openrouter.ai/api/v1",
      "model": "openai/text-embedding-3-large",
      "dimension": 3072
    }
  },
  "vlm": {
    "provider": "openai",
    "api_key": "replace-with-api-key",
    "api_base": "https://openrouter.ai/api/v1",
    "model": "google/gemini-3-flash-preview",
    "temperature": 0.0,
    "max_retries": 2,
    "extra_headers": {
      "HTTP-Referer": "https://github.com/kbaseincubator/BERIL-research-observatory",
      "X-Title": "BERIL Research Observatory"
    }
  },
  "log": {
    "level": "INFO"
  }
}
```

Other OpenViking-supported providers can be used instead, including direct
OpenAI, Volcengine Doubao, or local models configured by `openviking-server
init`. The scripts in this repository should not assume a specific provider.
They should only require that an OpenViking server is reachable and has a
working `ov.conf`.

For local development:

```bash
cp knowledge/openviking/ov.conf.example knowledge/openviking/ov.conf
openviking-server doctor --config knowledge/openviking/ov.conf
openviking-server --config knowledge/openviking/ov.conf
export OPENVIKING_URL=http://localhost:1933
```

For production, OpenViking may run remotely. In that case, `ov.conf` belongs on
the remote OpenViking host, and local agents only need:

```bash
export OPENVIKING_URL=https://openviking.example.org
export OPENVIKING_API_KEY=...
```

The Claude skill should mention that `openviking-server doctor` validates local
server prerequisites and model connectivity before ingestion.

## Ingestion CLI

`knowledge/scripts/ingest_context.py` supports:

```bash
uv run python knowledge/scripts/ingest_context.py --all
uv run python knowledge/scripts/ingest_context.py --changed
uv run python knowledge/scripts/ingest_context.py --project metal_cross_resistance
uv run python knowledge/scripts/ingest_context.py --docs
```

Behavior:

- `--all`: stage and ingest all selected projects and selected central docs.
- `--changed`: restage and ingest only projects/docs whose selected source files
  changed since the last manifest.
- `--project`: restage and ingest one project.
- `--docs`: restage and ingest selected central docs.

The script writes a small manifest under `knowledge/state/` recording selected
source paths, hashes, and their target URIs. This manifest supports the local
`--changed` decision; OpenViking still performs the deeper resource-tree
incremental update.

## Query CLI

`knowledge/scripts/knowledge_query.py` supports:

```bash
uv run python knowledge/scripts/knowledge_query.py find "metal resistance fitness cost"
uv run python knowledge/scripts/knowledge_query.py find "projects by Paramvir" --metadata
uv run python knowledge/scripts/knowledge_query.py find "BacDive validation issues" --project metal_cross_resistance
uv run python knowledge/scripts/knowledge_query.py overview viking://resources/projects/metal_cross_resistance/
uv run python knowledge/scripts/knowledge_query.py read viking://resources/projects/metal_cross_resistance/REPORT.md
```

Defaults:

- `find` targets `viking://resources/projects/`.
- `--project {project_id}` targets `viking://resources/projects/{project_id}/`.
- `--docs` targets `viking://resources/docs/`.
- `--metadata` prioritizes `viking://resources/project_index/` or the
  project metadata layer where possible.
- `--target-uri` allows raw OpenViking URI targeting.

Output should be plain text or JSON via a `--json` flag. Plain text should show
URI, score, abstract, and match reason when available.

## Dependencies

Add a separate knowledge dependency group or section in `pyproject.toml`, using
the repository's Python package manager preference:

```toml
[dependency-groups]
knowledge = [
  "openviking",
  "pyyaml",
]
```

If the repository chooses a different valid `uv` dependency structure before
implementation, use that structure while keeping knowledge dependencies separate
from the base CLI dependencies.

## Claude Skills

Add `.claude/skills/knowledge-context/SKILL.md` with:

- When to query the OpenViking context before answering project-scientific
  questions.
- How to run `knowledge_query.py find`, `overview`, and `read`.
- How to scope by project, docs, metadata, or raw target URI.
- How to run initial and incremental ingestion after project Markdown changes.
- Local versus remote OpenViking configuration via environment variables.

Update relevant existing skills in a narrow way:

- `pitfall-capture`: prefer writing durable project-specific pitfalls into the
  relevant project directory when a project context exists; otherwise keep using
  `docs/pitfalls.md`.
- `suggest-research`: note that the OpenViking context can be queried before
  scanning many project files manually.
- `synthesize`: after updating project reports, run or suggest incremental
  context ingestion for that project.

These updates should be documentation-only for this iteration.

## Error Handling

Keep error handling minimal:

- If OpenViking is unreachable, print the URL and fail clearly.
- If an expected selected source file disappears between scan and staging, skip
  it and let the next manifest reflect that.
- If `beril.yaml` cannot be parsed, include the raw file but omit generated
  structured metadata fields for that project and report the parse failure.

Do not add speculative recovery paths or a second storage backend.

## Testing

Add focused tests for:

- Project file selection include/exclude rules.
- Central docs selection.
- Stable URI mapping.
- Metadata Markdown generation from representative `beril.yaml`.
- Manifest change detection.
- Query output formatting with mocked OpenViking result objects.

Tests should not require a running OpenViking server. A manual smoke test should
be documented for local OpenViking:

```bash
openviking-server doctor --config knowledge/openviking/ov.conf
openviking-server --config knowledge/openviking/ov.conf
uv run python knowledge/scripts/smoke_ingest_openviking.py
uv run python knowledge/scripts/ingest_context.py --project metal_cross_resistance
uv run python knowledge/scripts/knowledge_query.py find "metal cross resistance" --project metal_cross_resistance
```

## Implementation Decisions

- `beril.yaml` metadata extraction should support the field names already present
  in current projects and should not require a schema migration.
- Dependency changes should keep knowledge dependencies separate from base CLI
  dependencies. If the repository later adopts lockfile management at the root,
  update that lockfile as part of implementation verification.
