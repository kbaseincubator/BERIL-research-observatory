# Migrating the OpenViking embedding model

How to change the embedding model on a deployed OpenViking instance without
losing your ingested source content.

## Why a plain config swap crashes

OpenViking stamps the embedding identity — `provider`, `model`, `dimension`,
`model_identity` — into the vector collection's description metadata
(`openviking/storage/collection_schemas.py`, `_build_embedding_metadata`). On
every startup, `init_context_collection` compares that stamp against the live
config:

| Persisted stamp | Existing vectors | Result |
|---|---|---|
| matches | any | continue |
| differs | **0 vectors** | silently re-stamp, continue |
| differs | **> 0 vectors** | **`EmbeddingRebuildRequiredError`** |

That error is raised inside deferred init and `app.py` responds with
`os._exit(1)` — the **whole process dies before the HTTP server is usable**.
That's the crash you saw. There is no env-var escape hatch around the guard.

## The key facts that make migration safe

1. **Vectors are derived data.** The source documents (markdown, `.abstract.md`,
   `.overview.md`) live in the AGFS tree under the workspace, in a *separate*
   directory from the vector collection. Deleting the vector collection does not
   touch them.
2. **OpenViking ships a non-destructive re-embed path:** the reindex executor
   (`openviking/service/reindex_executor.py`), exposed at
   `POST /api/v1/content/reindex` (ROOT/ADMIN). It reads retained source content
   back out and re-enqueues embeddings with the *current* config —
   `mode=vectors_only` reuses existing VLM semantics, so no expensive
   overview/abstract regeneration.
3. The catch-22: you can't call that API while the new model conflicts with the
   old vectors, because the server won't boot. So we first remove the old
   vectors (making the boot take the "0 vectors → re-stamp" branch), then
   reindex.

## The plan (reset collection + reindex)

```
STOP container
  -> migrate.py reset    delete ONLY the vector collection (keep sources)
START container w/ NEW model  -> boots clean (sees 0 vectors, re-stamps)
  -> migrate.py reindex  rebuild vectors from retained source, resumable
  -> migrate.py verify   confirm liveness + search returns hits
```

Search returns empty between the reset and the end of reindex. `vectors_only`
reindex is the cheapest option (no VLM calls), but it still makes one embedding
call per record, so on a rate-limited provider (CBORG 20/min) it paces itself.

## `migrate.py`

A single CLI with four subcommands — `find`, `reset`, `reindex`, `verify`.
Dependencies: **`httpx` + the Python standard library only** (the image has no
curl). `find`/`reset` are pure filesystem; `reindex`/`verify` hit the HTTP API.

Run it with the project's `knowledge` dependency group so `httpx` is on the path:

```bash
uv run --group knowledge python3 knowledge/openviking/migrate-embedding/migrate.py <cmd> ...
```

Inside the OpenViking container (where `httpx` is already installed for the
server), `python3 migrate.py <cmd>` is enough — no uv needed.

Config via flags or env:

| Env | Flag | Default |
|---|---|---|
| `OV_BASE` | — | `http://localhost:1933` |
| `OV_SERVER_KEY` | — | (required for reindex; optional for verify) |
| `PACING_SECONDS` | `--pacing` | `15` |
| `MODE` | `--mode` | `vectors_only` |
| `STATE_FILE` | `--state` | `./reindex-state.tsv` |
| `OV_TIMEOUT` | `--timeout` | `600` (reindex) / `30` (verify) |
| `PROBE_QUERY` | `--probe-query` | `overview` |

## Step by step

Run against the workspace path and the OpenViking HTTP API. On SPIN, run inside
the container (or any host that can see the workspace volume and reach port 1933).

### 0. Back up first (recommended)

The reset is reversible only if you keep the deleted collection. Either pass
`--backup-dir` to `reset`, or snapshot the workspace volume out of band.

### 1. Stop the container, then reset the collection

```bash
python3 migrate.py find /ov/workspace                       # what will be targeted
python3 migrate.py reset /ov/workspace --dry-run            # inspect, change nothing
python3 migrate.py reset /ov/workspace --backup-dir /ov/backup
```

`find` locates the collection by its `collection_meta.json` (next to a
`store/`/`index/` dir), so a non-default `storage.vectordb.name` still resolves.
Source documents are never matched by that probe. `reset` prompts before
deleting unless you pass `--force`.

### 2. Start the container with the NEW embedding model

Update the config / env the same way you set the current model (the entrypoint
fills `OV_EMBEDDING_*` into `ov.conf`). Make sure the new model's `dimension`
matches what the provider returns. Start the container; it should now boot
without `EmbeddingRebuildRequiredError`.

### 3. Reindex (resumable)

```bash
OV_SERVER_KEY=<root-or-admin-key> python3 migrate.py reindex
# gentler on rate limits:
OV_SERVER_KEY=... python3 migrate.py reindex --pacing 30
# one subtree only, as a smoke test:
OV_SERVER_KEY=... python3 migrate.py reindex --roots viking://resources/<dir>
```

It reindexes per subtree, checkpoints each to `reindex-state.tsv`, and **skips
completed subtrees on re-run** — so if a batch stalls on rate limits, just run
it again until it reports a clean pass. A subtree with `failed_records > 0` is
left un-done and retried next run.

### 4. Verify

```bash
OV_SERVER_KEY=... python3 migrate.py verify
```

Confirms the server is live (proving the guard passed) and that a search returns
vector hits (proving vectors exist under the new model).

## Notes / gotchas

- **Dimension changes are fine** with this flow — the collection is recreated on
  first boot after the reset, so a new `dimension` is picked up cleanly. (An
  in-place reindex without the reset could not change dimension.)
- **Don't delete the workspace** — only the collection subdir. The whole point is
  to keep source content so reindex is cheap.
- If you ever *do* want a full clean slate (re-run VLM semantics too), that's the
  alternate "wipe + re-ingest" path: delete the workspace and re-run the
  entrypoint ingest. More expensive; not scripted here.
- The reindex executor requires the embedding queue (`has_queue_manager`); the
  default server config has it. If you disabled it, reindex returns
  `FAILED_PRECONDITION`.
```
