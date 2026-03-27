# OpenViking Knowledge Layer Enhancements

**Date**: 2026-03-27
**Status**: Approved
**Branch**: feature/viking-migration

## Goal

Leverage three unused OpenViking capabilities to improve the knowledge layer:
- **A) Richer search** — push kind/project/tag filters server-side, pass `limit` and `score_threshold`
- **B) Multi-level rendering** — use OpenViking `abstract()` (L0) and `overview()` (L1) instead of the local renderer when live
- **F) Content-level search** — expose `grep` and `glob` as new `/knowledge` subcommands

All changes are additive. Offline fallback paths remain untouched.

## Architecture

Changes flow bottom-up through four existing layers:

```
Client  →  Service  →  Script  →  Skill
```

No new files are created. Each layer gets targeted additions.

## Layer 1: Client (`observatory_context/client.py`)

### New methods

```python
def grep(self, uri: str, pattern: str, case_insensitive: bool = False) -> dict
def glob(self, pattern: str, uri: str = "viking://") -> dict
def abstract(self, uri: str) -> str
def overview(self, uri: str) -> str
```

Thin passthroughs to `self.client.grep(...)`, `self.client.glob(...)`, etc.

### Modified method

`search()` gains `filter`, `limit`, and `score_threshold` parameters:

```python
def search(
    self,
    query: str,
    target_uri: str | None = None,
    limit: int = 10,
    score_threshold: float | None = None,
    filter: dict | None = None,
) -> list[dict[str, Any]]
```

Delegates to `self.client.find(query, target_uri=..., limit=..., score_threshold=..., filter=...)`.

## Layer 2: Service (`observatory_context/service/context_service.py`)

### Server-side filtering in `search_context()`

Add `limit: int = 10` and `score_threshold: float | None = None` parameters to `search_context()`.

When the client is live, build a `filter` dict from existing `kind`, `project`, and `tags` parameters and pass everything to the client:

```python
ov_filter = {}
if kind:
    ov_filter["kind"] = kind
if project:
    ov_filter["project_ids"] = project
if tags:
    ov_filter["tags"] = tags

semantic_hits = self.client.search(
    query,
    target_uri=target_uri,
    limit=limit,
    score_threshold=score_threshold,
    filter=ov_filter or None,
)
```

Remove the client-side `results[:args.limit]` truncation in the script when server-side limiting is active — the server handles it.

Post-fetch Python filtering remains as the offline fallback when `self.client is None`.

### Server-side rendering in `_render_response()`

When the client is live and detail level is L0 or L1, try `self.client.abstract(uri)` or `self.client.overview(uri)` first. Fall back to the local renderer on failure or when offline. L2 always uses the local renderer (full content).

```python
def _render_response(self, resource, detail_level):
    level = self._coerce_level(detail_level)
    rendered = None
    if self.client is not None and level in (RenderLevel.L0, RenderLevel.L1):
        try:
            rendered = (
                self.client.abstract(resource.uri) if level == RenderLevel.L0
                else self.client.overview(resource.uri)
            )
        except Exception:
            rendered = None
    if not rendered:
        rendered = render_resource(resource.render_payload(), level)
    return ResourceResponse(resource=resource, detail_level=level, rendered=rendered)
```

### New methods

```python
def grep_resources(self, pattern: str, uri: str | None = None, case_insensitive: bool = False) -> dict
def glob_resources(self, pattern: str, uri: str | None = None) -> dict
```

Both require a live OpenViking connection and raise `RuntimeError` if the client is `None`. No offline fallback — these are OpenViking-only features.

`glob_resources` accepts an optional `uri` to scope the search; defaults to the observatory root URI.

**Note on `filter` parameter naming**: The client uses `filter` (shadowing the Python built-in) because it matches the OpenViking SDK's parameter name. The service layer uses `ov_filter` internally to avoid the shadowing.

**Return dict shapes** (passthrough from OpenViking SDK):
- `grep()` returns `{"matches": [{"uri": str, "lines": [{"number": int, "content": str}]}]}`
- `glob()` returns `{"matches": [{"uri": str}]}`

Exact shapes may vary by SDK version; the script layer handles formatting defensively.

## Layer 3: Script (`scripts/query_knowledge_unified.py`)

### New subcommands

```
grep <pattern> [--uri <scope>] [--ignore-case]
glob <pattern>
```

### Handlers

Both check `_is_openviking_live(service)` and print a clear message if the server is down. On success, format results as:

**grep output:**
```
### Content matches for "pattern"

**resource_uri_1**
  L42: matching line content here
  L108: another matching line

**resource_uri_2**
  L7: match in different resource
```

**glob output:**
```
### Resources matching "*.yaml"

- viking://resources/observatory/.../provenance.yaml
- viking://resources/observatory/.../organisms.yaml
  (N total)
```

### Argparse additions in `build_parser()`

```python
p_grep = sub.add_parser("grep", help="Content search across resources (requires OpenViking)")
p_grep.add_argument("pattern")
p_grep.add_argument("--uri", default=None, help="Scope search to a URI subtree")
p_grep.add_argument("--ignore-case", action="store_true")

p_glob = sub.add_parser("glob", help="File pattern matching (requires OpenViking)")
p_glob.add_argument("pattern")
```

Register in `_HANDLERS`: `"grep": _handle_grep, "glob": _handle_glob`.

### Existing handler changes

`_handle_search`: pass `args.limit` through to `service.search_context(limit=args.limit)` when using the OpenViking path. Remove the client-side `results[:args.limit]` truncation since the server now handles it. Currently `--limit` exists in the argparser but is not forwarded to the service layer for live queries.

Other handlers benefit transparently from server-side filtering and rendering.

## Layer 4: Skill (`.claude/skills/knowledge/SKILL.md`)

Add two new subcommand entries:

```
/knowledge grep <pattern> [--uri <scope>] [--ignore-case]  — content search (requires OpenViking)
/knowledge glob <pattern>                                   — file pattern match (requires OpenViking)
```

Document that these require a live OpenViking server. Existing subcommand docs unchanged — richer filtering and rendering happen transparently.

## Error Handling

- **Server-side filter failure**: catch exception, fall through to existing Python-side filtering
- **Server-side rendering failure**: catch exception, fall through to local renderer
- **grep/glob without server**: print user-friendly message, exit 1
- No new exception types introduced

## Testing

- Existing tests in `scripts/tests/` continue to pass (offline paths unchanged)
- New integration tests for grep/glob handlers that mock the service
- Verify `search_context()` builds correct `filter` dict
- Verify `_render_response()` prefers server summaries when available and falls back correctly

## Files Modified

| File | Changes |
|------|---------|
| `observatory_context/client.py` | Add `grep`, `glob`, `abstract`, `overview`; extend `search` signature |
| `observatory_context/service/context_service.py` | Server-side filters in `search_context`, server-side rendering in `_render_response`, add `grep_resources`/`glob_resources` |
| `scripts/query_knowledge_unified.py` | Add `grep`/`glob` subcommands and handlers; pass `limit` through in `_handle_search` |
| `.claude/skills/knowledge/SKILL.md` | Document new `grep`/`glob` subcommands |
