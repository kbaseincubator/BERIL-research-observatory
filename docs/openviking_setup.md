# OpenViking Setup

Use the current end-to-end workflow in
[docs/openviking_tutorial.md](openviking_tutorial.md).

The shortest runnable path is:

```bash
uv sync --extra dev
uv run scripts/viking_setup.py --write-config
export OPENVIKING_CONFIG_FILE="$PWD/config/openviking/ov.conf"
openviking-server --config "$OPENVIKING_CONFIG_FILE"
uv run scripts/viking_server_healthcheck.py
uv run scripts/viking_ingest.py
```

`uv run scripts/viking_setup.py --write-config` now generates a runnable
`ov.conf` from your shell environment first, then falls back to repo-local
`.env`. Set `OPENAI_API_KEY` in either place before running it.

Use `uv run scripts/viking_ingest.py --check` to verify all resources are
present and `--fix` to re-ingest any that are missing.
