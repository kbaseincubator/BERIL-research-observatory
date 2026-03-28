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

Expected success:

```text
PASS: OpenViking server is reachable.
```

## 4. Preview and ingest observatory resources

Preview the deterministic manifest first:

```bash
uv run scripts/viking_ingest.py --dry-run --limit 5
```

Upload the full manifest to the live server:

```bash
uv run scripts/viking_ingest.py
```

This uploads authored project documents and figure metadata resources with
stable URIs and deterministic metadata. Use `--check` to verify all expected
resources are present, and `--fix` to re-ingest any that are missing.

## 5. Use the live context service

The service layer queries OpenViking for all knowledge data. Notes and
observations are written directly into OpenViking.

Current write surfaces:

- `add_note(project_id?, title, body, tags?, links?)`
- `add_observation(project_id?, source_ref?, body, tags?, links?)`

Current read surfaces:

- `search_context(query, kind?, project?, tags?, detail_level?)`
- `get_resource(id_or_uri, detail_level?)`
- `get_project_workspace(project_id, detail_level?)`
- `list_project_resources(project_id, kind?, path?)`
- `related_resources(id_or_uri, mode?, limit?)`

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
