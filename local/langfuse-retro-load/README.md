# BERIL Langfuse retro-load

Loads already-completed Claude Code sessions into BERIL's Langfuse org,
backdating each step to when the conversation actually happened instead of
only capturing new sessions going forward.

## Before anything else: this has to run on the pod, not your laptop

The source transcripts live on the BERDL pod, and some of them (the frozen
2026-05-07 hackathon corpus) are other people's data. **Never copy raw
`.jsonl` off the pod**: it can contain anything anyone pasted into a
session. Every script here reads transcripts and talks to Langfuse's API
directly from wherever it runs; it never needs to move a transcript
anywhere. Push these files to the pod (`labctl pod put`, or however you
transfer files there) and run everything from a pod terminal.

## The four pieces

- **`langfuse_hook_official.py`**: Langfuse's own official Claude Code
  integration hook, vendored unmodified from
  [their integration page](https://langfuse.com/integrations/developer-tools/claude-code).
  Does the actual turn-reconstruction and timestamp-backdating. Depends on
  `langfuse>=4.0,<5` internals (`_otel_tracer`,
  `_create_observation_from_otel_span`) that aren't in the public SDK API,
  so pin the version: a future major release could rename them.
- **`retro_load.py`**: loads one transcript file, given its path directly.
  `--dry-run` prints turn count and per-turn timestamps only, never message
  content, so it's safe to run against anyone's data, including the frozen corpus.
  Real runs write an idempotency marker to `~/.retro_load_markers/` (keyed
  by a hash of the resolved source path, not a sibling file, since the frozen
  corpus isn't writable by any individual account) so re-running against an
  already-loaded file reports "already retro-loaded" instead of duplicating
  it in Langfuse.
- **`people.json`**: the only file you edit to add a new person or source.
  See below.
- **`build_manifest.py`** / **`run_manifest.py`**: `build_manifest.py`
  reads `people.json`, discovers every session under each source's
  `find_root`, and runs `retro_load.py --dry-run` on each to work out turn
  counts and tags automatically, writing `manifest.json`. `run_manifest.py`
  reads that manifest and drives the real loads. This replaces hand-typing
  `--tag` flags per file, which doesn't scale and is easy to get wrong.

## Adding a person or a new source

Edit `people.json`, not the Python. One entry per person, one `sources`
entry per place their traces live:

```json
{
  "person": "someuser",
  "user_id": "someuser",
  "role": "Observe",
  "group": "SomeGroup",
  "sources": [
    {
      "type": "workshop-frozen-corpus",
      "find_root": "~/justin-trace-analysis/data/claudefiles/someuser/.claude/projects",
      "consent_bin": "opt_in",
      "force_event_day": []
    }
  ]
}
```

`consent_bin` should reflect a real, checked consent status
(`opt_in`/`opt_out`/`no_reply`/`team`): see the coverage-gaps issue below
before adding anyone whose consent hasn't actually been verified.
`force_event_day` is a list of session IDs to count as the 2026-05-07
event day even if the session started the day before (see issue #392 for
why that's a real, non-hypothetical case). `role`/`group` come from the
workshop invite-list sheet if applicable; leave them `null` for sources
where that doesn't apply (e.g. someone's own ongoing pod-home work).

`user_id` is deliberately the pod account name, never a real name. Langfuse
Sessions/Users views are a re-identification surface, and consent was
tracked pseudonymously. Don't change that without a real reason.

## Running it

```bash
# 1. Regenerate the manifest from current state (content-safe, no Langfuse calls)
python3 build_manifest.py

# 2. Sanity check before spending anything for real
python3 run_manifest.py --dry-run

# 3. Credentials -- .env next to these scripts, LANGFUSE_PUBLIC_KEY /
#    LANGFUSE_SECRET_KEY / LANGFUSE_HOST, for whichever Langfuse project
#    should receive this load. Never paste real key values through a chat
#    session -- set this up directly in a pod terminal.

# 4. The real thing. Backgrounded, since a browser/terminal hiccup shouldn't
#    kill a run partway through -- it's resumable via the markers either way.
nohup python3 run_manifest.py > full_load_run.txt 2>&1 &

# 5. Verify independently against Langfuse's own API, not just this
#    script's own "OK" output. Compare the run's own emitted-file count against
#    Langfuse directly, e.g. for one tag:
curl -s "$LANGFUSE_HOST/api/public/observations?tag=<your-batch-tag>&limit=1" \
  -u "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" | python3 -c \
  "import json,sys; print(json.load(sys.stdin)['meta']['totalItems'])"
```

## Known gaps (tracked as issues, not fixed here)

- [#391](https://github.com/kbaseincubator/BERIL-research-observatory/issues/391):
  which LLM backend (direct Anthropic / CBORG / Vertex) served a given
  trace isn't recoverable from the transcript itself.
- [#393](https://github.com/kbaseincubator/BERIL-research-observatory/issues/393):
  loading someone's traces only covers what's in `people.json`; the other
  ~80 hackathon participants have directories in the corpus with no
  consent checked. Don't read "we loaded the corpus" as "we loaded
  everyone."
- A live `.credentials.json` was found swept into the shared frozen corpus
  for every participant during this work. Not this tool's problem to fix,
  but flagged so it isn't lost: ask before assuming it's been handled.
- [#397](https://github.com/kbaseincubator/BERIL-research-observatory/issues/397):
  the real load run before this fix may have written a real filesystem
  path (not just the pseudonymous parts of it) into already-loaded traces'
  metadata. Fixed going forward; the historical data hasn't been checked
  or corrected.

A full session-by-session working log exists outside this repo (not
committed here, since it's a working log rather than documentation). Ask a
maintainer for it if you want the full story behind a decision, including
two real bugs found building this the first time (a capture-group indexing
error and an idempotency marker that didn't survive a later fix).
