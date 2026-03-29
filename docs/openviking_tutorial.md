# OpenViking Tutorial

OpenViking is the single source of truth for all observatory knowledge data.
This tutorial walks through setting up and running a local OpenViking server.

## Prerequisites

- `uv`
- Python 3.11+
- `openviking-server` available in the project environment

Install the project environment:

```bash
uv sync --extra dev
```

## 1. Create the repo-local server config

```bash
export OPENAI_API_KEY="your-openai-api-key"
uv run scripts/viking_setup.py --write-config
export OPENVIKING_CONFIG_FILE="$PWD/config/openviking/ov.conf"
```

The setup script validates that:

- `config/openviking/ov.conf.example` exists
- `config/openviking/ov.conf` can be generated from shell env or `.env`
- `openviking-server` is installed in the active environment

It resolves settings in this order:

1. Shell environment variables
2. Repo-local `.env`

Supported variables:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL` (optional, defaults to `https://api.openai.com/v1`)
- `OPENVIKING_EMBEDDING_MODEL` (optional, defaults to `text-embedding-3-large`)
- `OPENVIKING_EMBEDDING_DIMENSION` (optional, defaults to `3072`)
- `OPENVIKING_VLM_MODEL` (optional, defaults to `gpt-4o-mini`)

OpenViking itself does not read `.env` or expand env vars inside `ov.conf`; the
setup script writes a concrete JSON file using those values.

## 2. Start the local server

```bash
openviking-server --config "$OPENVIKING_CONFIG_FILE"
```

If you add `server.root_api_key` to the config, also export:

```bash
export BERIL_OPENVIKING_API_KEY="your-api-key"
```

## 3. Check server health

```bash
uv run scripts/viking_server_healthcheck.py
```

Expected: a Rich dashboard showing HEALTHY status, processing queue progress,
vector store stats, and component badges. Use `--watch` to auto-refresh until
queues drain:

```bash
uv run scripts/viking_server_healthcheck.py --watch --interval 10
```

## 4. Ingest observatory resources

Preview the manifest first:

```bash
uv run scripts/viking_ingest.py --dry-run --limit 5
```

Full ingest with knowledge graph (recommended for first run):

```bash
uv run scripts/viking_ingest.py --no-resume --rebuild-graph --clean --wait
```

This runs three phases:
1. **Phase 1** — Uploads project documents (README, REPORT, provenance, figures)
2. **Phase 2** — Extracts entities, relations, hypotheses, and timeline events from
   each project's REPORT.md via CBORG (default model: `gpt-5.4-mini`). Requires
   `CBORG_API_KEY` env var. Extractions are cached locally in `.kg_cache/` so
   subsequent runs only re-extract changed projects.
3. **Phase 3** — Generates L0/L1 tier summaries for knowledge graph directories.

The knowledge graph is written to a local temp directory and uploaded as a single
`add_resource` call (batch upload). Entities and hypotheses are deduplicated and
merged across projects before upload.

Incremental update (after editing a project):

```bash
uv run scripts/viking_ingest.py --graph-only --wait
```

Only projects whose REPORT.md or provenance.yaml changed since the last extraction
are sent to CBORG. All other projects use cached results. The merged graph replaces
the previous one atomically.

Use `--check` to verify all expected resources are present, and `--fix` to
re-ingest any that are missing.

## 5. Use the live context service

All knowledge access goes through `ContextDelivery` — the unified service
layer between skills and OpenViking. Skills declare *what* they need; the
service layer handles tier selection, memory blending, and graph traversal.

### ContextDelivery service layer

`ContextDelivery` is a synchronous Python class (using `httpx.Client`)
exposed via `query_knowledge_unified.py`. Every skill in `.claude/skills/`
calls it through CLI subcommands rather than talking to OpenViking directly.

Core operations:

```python
# Search across all resources
cd.search("pangenome fitness", tier=Tier.L2, with_memory=True)

# Direct fetch
cd.get("viking://resources/observatory/projects/phage_fitness_001", tier=Tier.L2)

# Directory listing (L1 default — overviews, not full content)
cd.browse("viking://resources/observatory/knowledge-graph/entities/", tier=Tier.L1)

# Graph traversal
cd.traverse("viking://resources/observatory/knowledge-graph/entities/organisms/ecoli", hops=2)

# Memory recall
cd.recall("normalization pitfalls", store=MemoryStore.PATTERNS)
```

Scope constants control which part of the URI tree is searched:

| Scope | URIs searched |
|---|---|
| `RESOURCES` | `projects/` + `notes/` — authored documents |
| `GRAPH` | `knowledge-graph/` — extracted entities, hypotheses, timeline |
| `MEMORY` | `memories/` — journal, patterns, conversations |
| `ALL` | All three (default for broad search) |

### Knowledge graph directory structure

The knowledge graph lives under
`viking://resources/observatory/knowledge-graph/` as a navigable directory
tree. Each entity is a directory; relations are YAML files.

```
viking://resources/observatory/
├── projects/{id}/authored/          # project documents (existing)
├── knowledge-graph/
│   ├── entities/{type}/{id}/        # entity directories
│   │   ├── .abstract.md             # L0: one-line summary
│   │   ├── .overview.md             # L1: key findings + relation table
│   │   ├── profile.yaml             # L2: full metadata
│   │   └── relations/
│   │       ├── .overview.md         # L1: relation summary
│   │       ├── has-core-genome-of_cluster_001.yaml
│   │       └── compared-with_klebsiella-pneumoniae.yaml
│   ├── hypotheses/{id}/             # hypothesis directories
│   └── timeline/                    # timeline events
├── memories/
│   ├── research-journal/            # decisions, hypothesis refinements
│   ├── patterns/                    # cross-project heuristics
│   └── conversations/               # data surprises, debugging insights
└── notes/                           # live session notes (existing)
```

Each relation YAML stores subject, predicate, object, evidence, and
confidence. An inverse copy lives in the target entity's `relations/`
directory so the graph is traversable from either end:

```yaml
predicate: "has-core-genome-of"
subject: entities/organisms/escherichia-coli
object: entities/genes/cluster_001
evidence:
  project: phage_fitness_001
  source: "REPORT.md §3.2"
confidence: high
```

### L0/L1/L2 tier system

Every resource has up to three content tiers. `ContextDelivery` selects the
tier per operation; skills never request more than they need.

| Tier | Size | Content | Generated by |
|---|---|---|---|
| L0 | ~80 tokens | One-line abstract | CBORG at ingest time |
| L1 | ~300 tokens | Overview / summary table | CBORG at ingest time |
| L2 | Full | Complete content | Source file (authoritative) |

Default tiers per operation:

| Operation | Default | Rationale |
|---|---|---|
| `search()` | L2 | Full content — generous budget |
| `get()` | L2 | Direct fetch = full content |
| `browse()` | L1 | Directory listings use overviews |
| `traverse()` | L2 | Full entity profiles + relations |
| `recall()` | L2 | Full memory content |

Pass `--tier L0` or `--tier L1` to reduce token usage when scanning many
results. A missing L0/L1 (e.g., CBORG was unavailable at ingest) does not
block access — OpenViking falls back to L2 content.

### Memory system

Three memory stores under `viking://resources/observatory/memories/`,
written by `/synthesize` at project milestones. Memory entries are regular
OpenViking resources — the URI prefix is what marks them as memory.

| Store | URI | Written by | Used by |
|---|---|---|---|
| `research-journal` | `memories/research-journal/` | `/synthesize` at milestones | `/status`, `/berdl_start` |
| `patterns` | `memories/patterns/` | `/synthesize` for cross-project heuristics | `/interpret`, `/suggest-research` |
| `conversations` | `memories/conversations/` | `/synthesize` reviewing session notes | `/knowledge`, `/interpret` |

Each entry is a dated directory (`{YYYY-MM-DD}_{slug}/`) with the body as
`entry.md`, `pattern.yaml`, or `insight.yaml` depending on the store.

Memory blending works by appending `--with-memory` to any search: the
service queries both `RESOURCES`/`GRAPH` and `MEMORIES`, merges and ranks
results, and tags each item with `source_type="memory"` so skills can
distinguish remembered context from project documents.

### Common CLI operations

```bash
# Tiered search with memory blending
uv run scripts/query_knowledge_unified.py search "topic" --tier L1 --with-memory

# Browse knowledge graph entity index
uv run scripts/query_knowledge_unified.py browse \
  viking://resources/observatory/knowledge-graph/entities/ --tier L1

# Graph traversal (2 hops from E. coli)
uv run scripts/query_knowledge_unified.py traverse \
  viking://resources/observatory/knowledge-graph/entities/organisms/ecoli --hops 2

# Memory recall scoped to patterns store
uv run scripts/query_knowledge_unified.py recall "normalization" --store patterns

# Full ingest with knowledge graph rebuild (Phases 1 + 2 + 3)
uv run scripts/viking_ingest.py --rebuild-graph --wait

# Incremental graph rebuild (skip resource upload, use cache)
uv run scripts/viking_ingest.py --graph-only --wait

# Full rebuild from scratch (wipe graph + cache)
uv run scripts/viking_ingest.py --no-resume --rebuild-graph --clean --wait

# Check server health (Rich dashboard with queue progress)
uv run scripts/viking_server_healthcheck.py
uv run scripts/viking_server_healthcheck.py --watch  # auto-refresh
```

### CBORG extraction pipeline

`viking_ingest.py --rebuild-graph` runs three phases:

1. **Phase 1 — Resource upload**: scans `projects/`, uploads
   README/REPORT/provenance/figures with stable URIs. Skips existing resources
   by default (`--resume`).
2. **Phase 2 — Knowledge graph extraction**: for each project with
   `REPORT.md` + `provenance.yaml`, checks the local extraction cache
   (`.kg_cache/`). If the project files haven't changed since last extraction,
   the cached result is loaded instantly. Otherwise, sends content to the CBORG
   API (default: `gpt-5.4-mini`). The `CBORGExtractor` returns a structured
   `EntityExtraction` (entities, relations, hypotheses, timeline events).
   Entities and hypotheses are deduplicated and merged across projects — same
   entity from multiple projects accumulates project lists, metadata, and
   relations. The merged graph is written to a local temp directory.
3. **Phase 3 — Tier generation**: generates L0/L1 abstracts for every entity
   type directory, roll-up summaries for parent directories, and hypotheses.
   These are also written to the staging directory.

After Phase 3, the entire knowledge graph directory is uploaded to OpenViking
in a single `add_resource` call (batch upload), replacing the previous graph
atomically. This avoids the lock contention and queue overload that occurs
with individual resource uploads.

The extraction includes retry logic for CBORG rate limits (HTTP 429) with
exponential backoff, and skips reports that exceed the model's max input
token limit.

Cost is low: ~2K input + ~500 output tokens per project for extraction, plus
~200 tokens per entity for tier generation.

## 6. Run repository verification

```bash
uv run --with pytest pytest scripts/tests -q
uv run scripts/validate_provenance.py
uv run scripts/viking_ingest.py --check
uv run scripts/viking_validate_parity.py
```

## Troubleshooting

- `FAIL: OpenViking server is not reachable.`:
  Start the server first or verify `BERIL_OPENVIKING_URL`.
- `FAIL: config not found .../config/openviking/ov.conf`:
  Run `uv run scripts/viking_setup.py --write-config`.
- `Missing OPENAI_API_KEY`:
  Export it in your shell or add it to `.env`, then rerun the setup script.
- `--check` reports missing resources:
  Run `uv run scripts/viking_ingest.py --fix` to re-ingest them.
