# OpenViking Knowledge Context

This branch uses OpenViking as the BERIL knowledge context layer. It ingests
curated project reports and central docs, then exposes `find`, `overview`, and
`read` queries for agents and humans.

## Local Setup

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
uv run --group knowledge python knowledge/scripts/smoke_ingest_openviking.py
```

By default this ingests the five most recently modified projects and prints up
to three query results for each.

## Ingestion

Run from the repo root:

```bash
uv run --group knowledge python knowledge/scripts/ingest_context.py --all
uv run --group knowledge python knowledge/scripts/ingest_context.py --changed
uv run --group knowledge python knowledge/scripts/ingest_context.py --project <project_id>
uv run --group knowledge python knowledge/scripts/ingest_context.py --docs
```

Use `--all` for initial setup, `--changed` for routine refreshes, `--project`
after editing one project, and `--docs` after central docs edits.

The ingest path uses batch-style OpenViking calls: resources are queued with
`wait=False`, then processing is awaited once.

## Querying

```bash
uv run --group knowledge python knowledge/scripts/knowledge_query.py find "query terms"
uv run --group knowledge python knowledge/scripts/knowledge_query.py find "query terms" --project <project_id>
uv run --group knowledge python knowledge/scripts/knowledge_query.py find "query terms" --docs
uv run --group knowledge python knowledge/scripts/knowledge_query.py find "query terms" --metadata
uv run --group knowledge python knowledge/scripts/knowledge_query.py overview viking://resources/projects/<project_id>/
uv run --group knowledge python knowledge/scripts/knowledge_query.py read viking://resources/projects/<project_id>/REPORT.md
```

Target layout:

- Projects: `viking://resources/projects/<project_id>/`
- Central docs: `viking://resources/docs/<doc_slug>/`
- Project metadata/index: `viking://resources/project_index/`

`OPENVIKING_URL` defaults to `http://localhost:1933`. Set `OPENVIKING_API_KEY`
only when the OpenViking server itself requires client authentication.

