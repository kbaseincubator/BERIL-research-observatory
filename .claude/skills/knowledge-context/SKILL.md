---
name: knowledge-context
description: Use when searching BERIL project/docs context through OpenViking or refreshing the indexed context layer before research, synthesis, or pitfall work.
allowed-tools: Bash, Read
user-invocable: true
---

# Knowledge Context Skill

Use the OpenViking context layer for fast recall across project reports, research plans, reviews, references, and central docs. Treat results as a map to source files: when facts matter, read the underlying file before editing or citing.

## Query Workflow

Use `knowledge/scripts/knowledge_query.py` from the repo root:

```bash
uv run --env-file .env knowledge/scripts/knowledge_query.py find "query terms"
uv run --env-file .env knowledge/scripts/knowledge_query.py overview viking://resources/projects/<project_id>/
uv run --env-file .env knowledge/scripts/knowledge_query.py read viking://resources/projects/<project_id>/REPORT.md
```

- `find` searches for relevant context before manual file reads.
- `overview` summarizes a project, docs resource, or metadata-oriented slice.
- `read` retrieves the selected OpenViking result so you can follow up in the source file.

Scope queries narrowly when possible:

```bash
uv run --env-file .env knowledge/scripts/knowledge_query.py find "query terms" --project <project_id>
uv run --env-file .env knowledge/scripts/knowledge_query.py find "query terms" --docs
uv run --env-file .env knowledge/scripts/knowledge_query.py find "query terms" --metadata
```

Use project scope for `projects/{id}` context, docs scope for central docs like pitfalls/discoveries/research ideas, and metadata scope when you need project status, authors, titles, branches, or manifest-level facts.

## Refreshing Context

Run ingestion after durable context changes so OpenViking stays current:

```bash
uv run --env-file .env knowledge/scripts/ingest_context.py --project <project_id>
uv run --env-file .env knowledge/scripts/ingest_context.py --changed
uv run --env-file .env knowledge/scripts/ingest_context.py --all
```

- Use `--project <project_id>` after updating one project.
- Use `--changed` after mixed project/docs edits.
- Use `--all` when the index may be stale or was never initialized.

Configure the OpenViking endpoint via `.env` (copy from `.env.example`): `OPENVIKING_URL` defaults to `http://127.0.0.1:1933`, and `OPENVIKING_API_KEY` is only needed when the server enforces auth (typically remote deployments). The scripts above read the file via `--env-file .env`.

For a local OpenViking server, copy `knowledge/openviking/ov.conf.example` to `knowledge/openviking/ov.conf` and set the OpenRouter key in the embedding and VLM sections. The local `ov.conf` is ignored by git. Set `OPENVIKING_API_KEY` only when the OpenViking server itself is configured to require a client/user key.

Validate local server configuration before ingesting (the `openviking-server` binary is provided by the `knowledge` dependency group, so it must be run via `uv run --group knowledge`):

```bash
uv run --group knowledge openviking-server doctor --config knowledge/openviking/ov.conf
uv run --group knowledge openviking-server --config knowledge/openviking/ov.conf
```

After the server is running, use the smoke test to ingest and query the five
most recently modified projects:

```bash
uv run knowledge/scripts/smoke_ingest_openviking.py
```
