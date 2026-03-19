# OpenViking Local Setup

This repository uses one shared local OpenViking HTTP server for the migration
work. Keep the runtime data directory outside Git and point the server at a
repo-managed config file.

For implementation details of the currently landed migration slice, see
[`docs/openviking_phase2.md`](openviking_phase2.md).
For the next implementation slice, see
[`docs/openviking_phase3_plan.md`](openviking_phase3_plan.md).

## 1. Install the local package environment

```bash
uv sync --extra dev
```

## 2. Copy the server config template

```bash
cp config/openviking/ov.conf.example config/openviking/ov.conf
```

`openviking-server` resolves configuration in this order:

1. `--config`
2. `OPENVIKING_CONFIG_FILE`
3. `~/.openviking/ov.conf`

For this repo, prefer the explicit environment variable:

```bash
export OPENVIKING_CONFIG_FILE="$PWD/config/openviking/ov.conf"
```

## 3. Start the local server

```bash
openviking-server --config "$OPENVIKING_CONFIG_FILE"
```

If you add `server.root_api_key`, the same value should be exported as
`BERIL_OPENVIKING_API_KEY` for the ingest scripts. If you do not set
`server.root_api_key`, OpenViking runs in localhost dev mode with auth disabled.

## 4. Capture the repository baseline

```bash
uv run scripts/viking_capture_baseline.py
```

This writes `docs/migration_baseline/2026-03-19/baseline_snapshot.json` and
`.yaml`.

## 5. Preview or upload the Phase 1 manifest

```bash
uv run scripts/viking_ingest.py --dry-run --limit 5
uv run scripts/viking_materialize_renders.py
uv run scripts/viking_validate_parity.py
```

Only drop `--dry-run` from `scripts/viking_ingest.py` when the server is
running and you want to upload the full manifest.
