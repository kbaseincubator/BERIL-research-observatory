# OpenViking Knowledge Context

This branch uses OpenViking as the BERIL knowledge context layer. It ingests
curated project reports and central docs, then exposes `find`, `overview`, and
`read` queries for agents and humans.

## Client Configuration

Copy the env template and edit if you need to point at a non-default server:

```bash
cp .env.example .env
```

The relevant entries:

- `OPENVIKING_URL` — defaults to `http://127.0.0.1:1933`, matching the host and
  port in `knowledge/openviking/ov.conf.example`.
- `OPENVIKING_API_KEY` — leave commented for local dev; set it only when the
  OpenViking server enforces client auth (typical for remote/prod deployments).

The three context scripts (`ingest_context.py`, `knowledge_query.py`,
`smoke_ingest_openviking.py`) are PEP 723 self-bootstrapping. Pass `.env` via
`uv run --env-file .env ...` and the scripts install their own deps in an
isolated venv — no `uv sync` or `--group knowledge` activation needed.

### Remote OpenViking

To query a remote server, point `OPENVIKING_URL` at it and set the API key the
server expects:

```bash
# .env
OPENVIKING_URL=https://openviking.prod.example
OPENVIKING_API_KEY=<token>
```

`config.py::ContextConfig.from_env()` reads both via `os.getenv`, so any
process loading `.env` (direnv, `--env-file`, `export`) routes the scripts to
the remote endpoint without code changes. Read-only queries (`find`,
`overview`, `read`) don't touch `knowledge/state/context_manifest.json`, so
multiple clients can share a remote server safely. For ingestion, the manifest
is per-machine; pick one host as the writer or accept that `--changed` may
re-push files the server already has (idempotent, just wasted work).

## Local Server Setup

Create the local config:

```bash
cp knowledge/openviking/ov.conf.example knowledge/openviking/ov.conf
```

Set the OpenRouter key in the ignored local config:

```bash
tmp=$(mktemp)
jq --arg key "$OPENROUTER_API_KEY" \
  '.embedding.dense.api_key=$key | .vlm.api_key=$key' \
  knowledge/openviking/ov.conf > "$tmp" && mv "$tmp" knowledge/openviking/ov.conf
```

Validate and start the server:

```bash
uv run --group knowledge openviking-server doctor --config knowledge/openviking/ov.conf
uv run --group knowledge openviking-server --config knowledge/openviking/ov.conf
```

`knowledge/openviking/ov.conf` and `knowledge/openviking/workspace/` are ignored
by git. The API key belongs only in the ignored local config, not in
`ov.conf.example`.

## Smoke Test

With the server running in another terminal:

```bash
uv run --env-file .env knowledge/scripts/smoke_ingest_openviking.py
```

By default this ingests the five most recently modified projects and prints up
to three query results for each.

## Ingestion

Run from the repo root:

```bash
uv run --env-file .env knowledge/scripts/ingest_context.py --all
uv run --env-file .env knowledge/scripts/ingest_context.py --changed
uv run --env-file .env knowledge/scripts/ingest_context.py --project <project_id>
uv run --env-file .env knowledge/scripts/ingest_context.py --docs
```

Use `--all` for initial setup, `--changed` for routine refreshes, `--project`
after editing one project, and `--docs` after central docs edits.

The ingest path uses batch-style OpenViking calls: resources are queued with
`wait=False`, then processing is awaited once.

## Querying

`knowledge_query.py` exposes the OpenViking surface needed for both fuzzy and
deterministic lookups:

```bash
# Semantic search
QUERY=knowledge/scripts/knowledge_query.py
uv run --env-file .env $QUERY find "query terms"
uv run --env-file .env $QUERY find "query terms" --project <project_id>
uv run --env-file .env $QUERY find "query terms" --docs

# Filter / time-bounded find (pass an OV filter tree as JSON)
uv run --env-file .env $QUERY find "query terms" --since 7d --time-field updated_at
uv run --env-file .env $QUERY find "query terms" \
  --filter '{"op":"must","field":"uri","conds":["viking://resources/projects/alpha/"]}'

# Exact pattern (e.g. all projects mentioning an author)
uv run --env-file .env $QUERY grep "Ada Lovelace" --uri viking://resources/projects/

# URI enumeration / structural navigation
uv run --env-file .env $QUERY glob "viking://resources/projects/*/"
uv run --env-file .env $QUERY ls viking://resources/projects/ --simple
uv run --env-file .env $QUERY tree viking://resources/projects/alpha/
uv run --env-file .env $QUERY stat viking://resources/projects/alpha/

# Relations between resources
uv run --env-file .env $QUERY relations viking://resources/projects/alpha/
uv run --env-file .env $QUERY link viking://resources/projects/alpha/ \
  viking://resources/projects/beta/ --reason "shared cohort"
uv run --env-file .env $QUERY unlink viking://resources/projects/alpha/ \
  viking://resources/projects/beta/

# Resource access
uv run --env-file .env $QUERY overview viking://resources/projects/<project_id>/
uv run --env-file .env $QUERY read viking://resources/projects/<project_id>/REPORT.md
```

Target layout:

- Projects: `viking://resources/projects/<project_id>/`
- Central docs: `viking://resources/docs/<doc_slug>/`

Per-project metadata (id, title, status, authors, branch, engine, dates) is
ingested as `PROJECT_METADATA.md` inside each project URI — search it with
`find` or `grep` rather than a global index.

## Project relations

Each project's `beril.yaml` may declare cross-project links:

```yaml
related_projects:
  - sister_project_id
  - another_project_id
```

During `ingest_context.py`, those entries become OpenViking relations from the
project's URI to the listed projects (missing IDs are skipped). Inspect with
`knowledge_query.py relations <uri>` or manage them manually with
`link`/`unlink`.
