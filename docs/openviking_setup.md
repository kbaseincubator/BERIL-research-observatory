# OpenViking Setup

Use the current end-to-end workflow in
[docs/openviking_tutorial.md](openviking_tutorial.md).

The shortest runnable path is:

```bash
uv sync --extra dev
uv run scripts/viking_setup.py --write-config
export OPENVIKING_CONFIG_FILE="$PWD/config/openviking/ov.conf"

# Start server (in a separate terminal)
uv run openviking-server --config "$OPENVIKING_CONFIG_FILE"

# Verify health
uv run scripts/viking_server_healthcheck.py

# Full ingest with knowledge graph (first time)
uv run scripts/viking_ingest.py --no-resume --rebuild-graph --clean --wait

# Incremental update (after editing projects)
uv run scripts/viking_ingest.py --graph-only --wait
```

`uv run scripts/viking_setup.py --write-config` generates a runnable
`ov.conf` from your shell environment first, then falls back to repo-local
`.env`. Set `OPENAI_API_KEY` in either place before running it.

Knowledge graph extraction requires `CBORG_API_KEY` (default model:
`gpt-5.4-mini`). Extractions are cached locally in `.kg_cache/` so
subsequent runs only re-extract changed projects.

Use `uv run scripts/viking_ingest.py --check` to verify all resources are
present and `--fix` to re-ingest any that are missing.

Use `uv run scripts/viking_server_healthcheck.py --watch` to monitor
processing queue progress in real time.
