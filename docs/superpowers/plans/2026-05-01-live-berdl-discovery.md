# Live BERDL Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix upstream issues #229 and #240 by making BERDL database/table access discovery use live `berdl_notebook_utils` helpers, removing stale static collection inventory authority, and ensuring the PR body explicitly says it fixes both issues.

**Architecture:** Keep `ui/config/collections.yaml` as curated display metadata only. Use `berdl_notebook_utils.get_databases()`, `get_tables()`, and `get_table_schema()` for access-sensitive discovery, and use `spark.sql(query)` for SQL execution. Remove committed static collection inventory files and update agent/docs guidance so `docs/collections.md`, raw `SHOW DATABASES`/`SHOW TABLES`, and MCP query endpoints are no longer recommended as the source of truth.

**Tech Stack:** Python 3.11, PySpark/Spark Connect, BERDL JupyterHub helpers from `berdl_notebook_utils`, FastAPI/Jinja UI parser tests, pytest, uv.

---

## Upstream Context

- Issue #229: "Use BERDL specific function for spark queries"
  - Replace raw metadata discovery such as `spark.sql("SHOW DATABASES")` and `spark.sql("SHOW TABLES IN ...")` with access-aware helpers:

```python
from berdl_notebook_utils import get_databases, get_tables, get_table_schema

databases = get_databases()
tables = get_tables("my_db")
schema = get_table_schema("my_db", "my_table")
```

  - Avoid MCP query operations. Use native Spark SQL for actual queries:

```python
spark.sql(query)
```

- Issue #240: "Remove collections.md and related files in favor of live Spark queries for tenant/table access"
  - `docs/collections.md` should not be treated as the source of truth for tenant/table access.
  - Committed static collection snapshots should not drive access-sensitive behavior.
    The UI may keep a snapshot as a display/fallback artifact, but live helpers
    remain the source of truth for tenant/table access.

## File Structure

- Modify `scripts/discover_berdl_collections.py`: replace REST/MCP and raw Spark SQL metadata discovery with `berdl_notebook_utils` helper-based discovery. Keep the JSON writer for optional generated UI snapshots.
- Modify `ui/tests/test_discover_berdl_collections.py`: replace REST-focused tests with helper-focused tests.
- Modify `ui/tests/test_dataloader.py`: keep coverage that curated metadata works and that generated snapshots are optional UI artifacts.
- Delete `docs/collections.md`: remove stale inventory authority.
- Keep `ui/config/berdl_collections_snapshot.json` as a UI display/fallback snapshot, but document that it is not authoritative for access-sensitive discovery.
- Modify `README.md`, `PROJECT.md`, `DIRECTORY_STRUCTURE.md`, `docs/workflow.md`, `docs/getting_started.md`, `docs/pitfalls.md`, `tools/review.sh`: replace links to `docs/collections.md` and `SHOW ...` examples with live helper guidance or schema docs.
- Modify `.claude/skills/berdl/SKILL.md`, `.claude/skills/berdl-query/SKILL.md`, `.claude/skills/berdl-discover/SKILL.md`, `.claude/skills/berdl-ingest/SKILL.md`, `.claude/skills/berdl_start/SKILL.md`, `.claude/skills/suggest-research/SKILL.md`, `.claude/reviewer/PLAN_REVIEW_PROMPT.md`: update agent guidance to use live helper discovery and Spark SQL execution.

---

### Task 1: Lock Helper-Based Discovery Behavior In Tests

**Files:**
- Modify: `ui/tests/test_discover_berdl_collections.py`

- [ ] **Step 1: Replace the REST discovery test with a helper discovery test**

Replace `test_discovery_groups_databases_and_keeps_schema_errors` with:

```python
def test_discovery_uses_berdl_notebook_helpers(monkeypatch):
    module = _load_script_module()
    calls = []

    def fake_get_databases():
        calls.append(("get_databases",))
        return [
            {"name": "kbase_ke_pangenome", "description": "Pangenome data"},
            "kescience_fitnessbrowser",
        ]

    def fake_get_tables(database):
        calls.append(("get_tables", database))
        if database == "kbase_ke_pangenome":
            return [{"name": "genome", "description": "Genome table"}]
        return ["organism"]

    def fake_get_table_schema(database, table):
        calls.append(("get_table_schema", database, table))
        if table == "organism":
            raise RuntimeError("schema timeout")
        return [
            {
                "name": "genome_id",
                "type": "string",
                "description": "Genome identifier.",
            }
        ]

    monkeypatch.setattr(module, "_load_berdl_helpers", lambda: (
        fake_get_databases,
        fake_get_tables,
        fake_get_table_schema,
    ))

    snapshot = module.discover_collections(include_schemas=True)

    assert snapshot["discovery_method"] == "berdl_notebook_utils"
    assert snapshot["source_url"] == "berdl-notebook-utils"
    assert [tenant["id"] for tenant in snapshot["tenants"]] == ["kbase", "kescience"]
    kbase_collection = snapshot["tenants"][0]["collections"][0]
    assert kbase_collection["id"] == "kbase_ke_pangenome"
    assert kbase_collection["tables"][0]["columns"][0]["name"] == "genome_id"
    fitness_collection = snapshot["tenants"][1]["collections"][0]
    assert "organism schema failed" in fitness_collection["discovery_errors"][0]
    assert ("get_databases",) in calls
    assert ("get_tables", "kbase_ke_pangenome") in calls
    assert ("get_table_schema", "kbase_ke_pangenome", "genome") in calls
```

- [ ] **Step 2: Add a test for `--skip-schemas`**

Add this test below the helper discovery test:

```python
def test_skip_schemas_does_not_call_get_table_schema(monkeypatch):
    module = _load_script_module()

    def fail_get_table_schema(database, table):
        raise AssertionError("get_table_schema should not be called")

    monkeypatch.setattr(module, "_load_berdl_helpers", lambda: (
        lambda: ["kbase_ke_pangenome"],
        lambda database: ["genome"],
        fail_get_table_schema,
    ))

    snapshot = module.discover_collections(include_schemas=False)

    collection = snapshot["tenants"][0]["collections"][0]
    assert collection["tables"] == [
        {
            "name": "genome",
            "description": "",
            "row_count": None,
            "columns": [],
        }
    ]
```

- [ ] **Step 3: Add a CLI test for the new default source**

Add this test below `test_missing_auth_returns_clear_failure`:

```python
def test_main_uses_live_helpers_by_default(tmp_path, monkeypatch, capsys):
    module = _load_script_module()
    output = tmp_path / "snapshot.json"
    monkeypatch.delenv("KBASE_AUTH_TOKEN", raising=False)
    monkeypatch.setattr(module, "_load_berdl_helpers", lambda: (
        lambda: ["kbase_ke_pangenome"],
        lambda database: ["genome"],
        lambda database, table: [],
    ))

    code = module.main(["--output", str(output), "--skip-schemas"])

    assert code == 0
    snapshot = json.loads(output.read_text())
    assert snapshot["discovery_method"] == "berdl_notebook_utils"
    assert snapshot["tenants"][0]["collections"][0]["id"] == "kbase_ke_pangenome"
    assert "Wrote 1 collections" in capsys.readouterr().out
```

- [ ] **Step 4: Run the focused test to verify it fails before implementation**

Run:

```bash
cd ui
uv run pytest tests/test_discover_berdl_collections.py -q
```

Expected: FAIL because `_load_berdl_helpers` and the new `discover_collections(include_schemas=...)` signature do not exist yet.

---

### Task 2: Refactor Collection Discovery To Use BERDL Helpers

**Files:**
- Modify: `scripts/discover_berdl_collections.py`

- [ ] **Step 1: Remove obsolete imports and constants**

Remove these imports:

```python
import os
import urllib.error
import urllib.request
```

Remove these constants:

```python
DEFAULT_BASE_URL = "https://hub.berdl.kbase.us/apis/mcp"
DEFAULT_SPARK_HOST = "metrics.berdl.kbase.us"
DEFAULT_SPARK_PORT = 443
```

- [ ] **Step 2: Delete token and REST/Spark metadata helpers**

Delete these functions:

```python
read_auth_token
discover_collections_from_spark
_spark_row_dict
_spark_database_name
_spark_table_name
_extract_spark_describe_columns
_post_json
_first_list
```

Keep `_extract_databases`, `_extract_tables`, and `_extract_columns`, but repurpose them to normalize helper return values.

- [ ] **Step 3: Add a helper loader**

Add this function above `discover_collections`:

```python
def _load_berdl_helpers():
    try:
        from berdl_notebook_utils import get_databases, get_tables, get_table_schema
    except Exception as exc:  # pragma: no cover - exercised by BERDL runtime setup
        raise RuntimeError(
            "Cannot import berdl_notebook_utils. Run this on BERDL JupyterHub "
            "or in a client environment where berdl_notebook_utils is installed."
        ) from exc
    return get_databases, get_tables, get_table_schema
```

- [ ] **Step 4: Replace `discover_collections` implementation**

Replace the current `discover_collections(token, base_url, timeout)` function with:

```python
def discover_collections(
    *,
    max_databases: int | None = None,
    include_schemas: bool = True,
) -> dict[str, Any]:
    """Discover accessible BERDL databases through access-aware notebook helpers."""
    get_databases, get_tables, get_table_schema = _load_berdl_helpers()
    databases = _extract_databases(get_databases())
    databases = sorted(databases, key=lambda item: item["id"])
    if max_databases is not None:
        databases = databases[:max_databases]

    tenants: dict[str, dict[str, Any]] = {}
    for database in databases:
        tenant_id = database.get("tenant_id") or infer_tenant_id(database["id"])
        tenant = tenants.setdefault(
            tenant_id,
            {
                "id": tenant_id,
                "name": TENANT_NAMES.get(tenant_id, tenant_id.replace("_", " ").title()),
                "collections": [],
            },
        )
        collection = {
            "id": database["id"],
            "name": database.get("name") or title_from_id(database["id"]),
            "description": database.get("description", ""),
            "provider": database.get("provider") or tenant["name"],
            "tables": [],
            "discovery_errors": [],
        }
        try:
            tables = _extract_tables(get_tables(database["id"]))
        except Exception as exc:  # pragma: no cover - depends on live BERDL state
            collection["discovery_errors"].append(
                f"table list failed: {_format_error(exc)}"
            )
            tables = []

        for table in tables:
            table_record = {
                "name": table["name"],
                "description": table.get("description", ""),
                "row_count": table.get("row_count"),
                "columns": [],
            }
            if not include_schemas:
                collection["tables"].append(table_record)
                continue
            try:
                table_record["columns"] = _extract_columns(
                    get_table_schema(database["id"], table["name"])
                )
            except Exception as exc:  # pragma: no cover - depends on live BERDL state
                collection["discovery_errors"].append(
                    f"{table['name']} schema failed: {_format_error(exc)}"
                )
            collection["tables"].append(table_record)

        tenant["collections"].append(collection)

    return {
        "schema_version": 1,
        "source_url": "berdl-notebook-utils",
        "discovery_method": "berdl_notebook_utils",
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "tenants": list(tenants.values()),
    }
```

- [ ] **Step 5: Make normalization support helper shapes**

Ensure `_extract_databases`, `_extract_tables`, and `_extract_columns` accept lists returned directly by helper functions. Replace `_first_list` usage with inline normalization:

```python
def _items_from_payload(payload: Any, keys: tuple[str, ...]) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, tuple):
        return list(payload)
    if not isinstance(payload, dict):
        return []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, dict):
            nested = _items_from_payload(value, keys)
            if nested:
                return nested
    return []
```

Then call `_items_from_payload(...)` in the extractors. Keep support for dict keys such as `database`, `database_name`, `namespace`, `table`, `table_name`, `name`, `type`, and `data_type`.

- [ ] **Step 6: Simplify CLI options**

In `main`, remove:

```python
--base-url
--source
--timeout
--spark-host
--spark-port
--no-berdl-proxy
--no-ensure-hub
--env-file
```

Keep:

```python
--output
--max-databases
--skip-schemas
--include-non-user-facing
```

Update the call site to:

```python
try:
    snapshot = discover_collections(
        max_databases=args.max_databases,
        include_schemas=not args.skip_schemas,
    )
except RuntimeError as exc:
    print(str(exc), file=sys.stderr)
    return 2
```

- [ ] **Step 7: Run the focused discovery tests**

Run:

```bash
cd ui
uv run pytest tests/test_discover_berdl_collections.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit the discovery refactor**

Run:

```bash
git add scripts/discover_berdl_collections.py ui/tests/test_discover_berdl_collections.py
git commit -m "fix: use BERDL helpers for discovery"
```

---

### Task 3: Remove Static Collection Inventory Authority

**Files:**
- Delete: `docs/collections.md`
- Keep: `ui/config/berdl_collections_snapshot.json`
- Modify: `ui/tests/test_dataloader.py`

- [ ] **Step 1: Delete the static Markdown inventory**

Run:

```bash
git rm docs/collections.md
```

- [ ] **Step 2: Keep parser fallback behavior explicit**

In `ui/tests/test_dataloader.py`, keep `test_missing_snapshot_falls_back_to_curated_config` unchanged. It documents that curated UI metadata remains usable without a generated snapshot.

- [ ] **Step 3: Rename snapshot tests to make optional generated snapshots clear**

Rename:

```python
def test_snapshot_loads_before_curated_overlay(self, tmp_path):
```

to:

```python
def test_generated_snapshot_loads_before_curated_overlay(self, tmp_path):
```

Rename:

```python
def test_snapshot_tables_are_available_as_schema_tables(self, tmp_path):
```

to:

```python
def test_generated_snapshot_tables_are_available_as_schema_tables(self, tmp_path):
```

- [ ] **Step 4: Run parser tests**

Run:

```bash
cd ui
uv run pytest tests/test_dataloader.py::TestParseCollections -q
```

Expected: PASS.

- [ ] **Step 5: Commit static inventory removal**

Run:

```bash
git add ui/tests/test_dataloader.py
git commit -m "fix: remove static BERDL inventory files"
```

Expected: commit includes the deleted Markdown inventory and the test rename. `ui/config/berdl_collections_snapshot.json` remains tracked as a UI display/fallback artifact.

---

### Task 4: Update Repository Documentation

**Files:**
- Modify: `README.md`
- Modify: `PROJECT.md`
- Modify: `DIRECTORY_STRUCTURE.md`
- Modify: `docs/workflow.md`
- Modify: `docs/getting_started.md`
- Modify: `docs/discoveries.md`
- Modify: `docs/pitfalls.md`
- Modify: `docs/performance.md`
- Modify: `scripts/README.md`
- Modify: `tools/review.sh`

- [ ] **Step 1: Replace `docs/collections.md` references**

Use this search to find remaining references:

```bash
rg -n "docs/collections\\.md|collections\\.md|SHOW DATABASES|SHOW TABLES" README.md PROJECT.md DIRECTORY_STRUCTURE.md docs scripts tools -S
```

For user-facing docs, replace references to `docs/collections.md` with language like:

````markdown
Use live BERDL helper discovery for the databases and tables your identity can access:

```python
from berdl_notebook_utils import get_databases, get_tables, get_table_schema

databases = get_databases()
tables = get_tables("kbase_ke_pangenome")
schema = get_table_schema("kbase_ke_pangenome", "genome")
```

Curated schema notes remain in `docs/schemas/`, but live helper results are the source of truth for tenant/table access.
````

- [ ] **Step 2: Update local query examples**

Replace `SHOW DATABASES` probe examples with a bounded native Spark SQL query:

```bash
python scripts/run_sql.py --berdl-proxy --query "SELECT 1 AS ok"
```

Add a note beside `scripts/run_sql.py` examples:

```markdown
Use `scripts/run_sql.py` for actual SQL execution. Do not use `SHOW DATABASES`
or `SHOW TABLES` for access discovery; use `berdl_notebook_utils` helper
functions instead.
```

- [ ] **Step 3: Update `scripts/README.md` collection snapshot section**

Replace the "Refresh the UI collection snapshot" section with:

````markdown
### 5. Refresh the UI collection snapshot

```bash
.venv-berdl/bin/python scripts/discover_berdl_collections.py \
  --skip-schemas \
  --output ui/config/berdl_collections_snapshot.json
```

The script uses `berdl_notebook_utils.get_databases()`, `get_tables()`, and
`get_table_schema()` so discovery is filtered to what the active BERDL identity
can access. The committed snapshot is a UI display/fallback artifact; do not
treat it as the source of truth for tenant/table access.
````

- [ ] **Step 4: Update `tools/review.sh` prompt**

In the `REVIEW_PROMPT`, replace:

```bash
docs/collections.md
```

with:

```bash
live BERDL helper discovery via get_databases(), get_tables(), and get_table_schema()
```

Keep `docs/schemas/` in the review prompt for table/column documentation.

- [ ] **Step 5: Run docs reference scan**

Run:

```bash
rg -n "docs/collections\\.md|collections\\.md|SHOW DATABASES|SHOW TABLES|/delta/tables/query|mcp_query_table|mcp_select_table|mcp_count_table" README.md PROJECT.md DIRECTORY_STRUCTURE.md docs scripts tools -S
```

Expected: no active guidance remains that treats `docs/collections.md`, `SHOW DATABASES`, `SHOW TABLES`, or MCP query endpoints as preferred BERDL discovery/query paths. Historical notes in `docs/discoveries.md` may remain only if rewritten to say they are outdated historical context.

- [ ] **Step 6: Commit documentation updates**

Run:

```bash
git add README.md PROJECT.md DIRECTORY_STRUCTURE.md docs scripts/README.md tools/review.sh
git commit -m "docs: prefer live BERDL discovery helpers"
```

---

### Task 5: Update Agent Skills

**Files:**
- Modify: `.claude/skills/berdl/SKILL.md`
- Modify: `.claude/skills/berdl-query/SKILL.md`
- Modify: `.claude/skills/berdl-discover/SKILL.md`
- Modify: `.claude/skills/berdl-ingest/SKILL.md`
- Modify: `.claude/skills/berdl_start/SKILL.md`
- Modify: `.claude/skills/suggest-research/SKILL.md`
- Modify: `.claude/reviewer/PLAN_REVIEW_PROMPT.md`

- [ ] **Step 1: Update `.claude/skills/berdl/SKILL.md`**

Replace the "API Endpoints" section with:

````markdown
## Access-Aware Discovery

Use `berdl_notebook_utils` helpers to discover the databases, tables, and
schemas visible to the active BERDL identity:

```python
from berdl_notebook_utils import get_databases, get_tables, get_table_schema

databases = get_databases()
tables = get_tables("my_db")
schema = get_table_schema("my_db", "my_table")
```

Avoid raw Spark metadata discovery:

```python
spark.sql("SHOW DATABASES")
spark.sql("SHOW TABLES IN my_db")
```

`SHOW DATABASES` can list namespaces regardless of whether the active user has
access. The helper methods filter by the active user's identity and tenant
membership.
````

Replace the SQL endpoint guidance with:

````markdown
## Query Execution

Use native Spark SQL for actual queries:

```python
spark.sql(query)
```

Do not use MCP query operations such as `mcp_query_table`, `mcp_select_table`,
`mcp_count_table`, or the REST `/delta/tables/query` endpoint for BERDL SQL
execution.
````

- [ ] **Step 2: Update `.claude/skills/berdl-query/SKILL.md`**

Replace the probe query step:

```markdown
3. Execute a probe query:
   - `python scripts/run_sql.py --berdl-proxy --query "SHOW DATABASES"`
```

with:

```markdown
3. Execute a lightweight Spark SQL probe:
   - `python scripts/run_sql.py --berdl-proxy --query "SELECT 1 AS ok"`
```

Add this rule under "Safety Rules":

```markdown
4. Do not use `SHOW DATABASES` or `SHOW TABLES` for access discovery. Use
   `berdl_notebook_utils.get_databases()`, `get_tables()`, and
   `get_table_schema()` instead.
```

- [ ] **Step 3: Update `.claude/skills/berdl-discover/SKILL.md`**

Replace the curl-based discovery workflow with:

````markdown
## Discovery Workflow

Use BERDL notebook helper functions for access-aware discovery:

```python
from berdl_notebook_utils import get_databases, get_tables, get_table_schema

databases = get_databases()
tables = get_tables("DATABASE_NAME")
schema = get_table_schema("DATABASE_NAME", "TABLE_NAME")
```

For sample rows and analytical queries, create or reuse a Spark session and run
native Spark SQL:

```python
spark.sql("SELECT * FROM DATABASE_NAME.TABLE_NAME LIMIT 5")
```
````

Remove instructions that use `/delta/databases/list`, `/delta/databases/tables/list`, `/delta/databases/tables/schema`, `/delta/tables/count`, `/delta/tables/sample`, or `/delta/tables/query`.

- [ ] **Step 4: Update ingest/start/reviewer/suggest skills**

Apply these replacements wherever they appear:

```markdown
docs/collections.md
```

to:

```markdown
live BERDL helper discovery with `get_databases()`, `get_tables()`, and `get_table_schema()`
```

Replace any `SHOW DATABASES`/`SHOW TABLES` examples with either helper discovery or `SELECT 1 AS ok` for connectivity checks.

- [ ] **Step 5: Run skill reference scan**

Run:

```bash
rg -n "docs/collections\\.md|collections\\.md|SHOW DATABASES|SHOW TABLES|/delta/tables/query|mcp_query_table|mcp_select_table|mcp_count_table|mcp_sample_table" .claude -S
```

Expected: no active guidance remains that prefers stale collection docs, raw Spark metadata discovery, or MCP query operations. If a mention remains as an "avoid this" example, the surrounding text must clearly say not to use it.

- [ ] **Step 6: Commit agent skill updates**

Run:

```bash
git add .claude
git commit -m "docs: update BERDL agent discovery guidance"
```

---

### Task 6: Verify Full Behavior

**Files:**
- No planned edits.

- [ ] **Step 1: Run focused tests**

Run:

```bash
cd ui
uv run pytest tests/test_discover_berdl_collections.py tests/test_dataloader.py::TestParseCollections -q
```

Expected: PASS.

- [ ] **Step 2: Run broader UI tests likely affected by collection parsing**

Run:

```bash
cd ui
uv run pytest tests/test_main.py::TestCollectionsRoute tests/test_wiki_lint.py -q
```

Expected: PASS. If tests fail because they assume a committed snapshot, update only those tests to create temporary snapshots or rely on curated `collections.yaml`.

- [ ] **Step 3: Run formatting/lint check if configured**

Run:

```bash
cd ui
uv run ruff check app tests
```

Expected: PASS.

- [ ] **Step 4: Run final reference scan**

Run:

```bash
rg -n "docs/collections\\.md|collections\\.md|SHOW DATABASES|SHOW TABLES|/delta/tables/query|mcp_query_table|mcp_select_table|mcp_count_table|mcp_sample_table" README.md PROJECT.md DIRECTORY_STRUCTURE.md docs scripts tools .claude ui -S --glob '!**/*.ipynb'
```

Expected: only "avoid this" examples or historical notes remain. There should be no active instruction to use deleted `docs/collections.md`, raw `SHOW ...` discovery, or MCP query operations.

- [ ] **Step 5: Check git state**

Run:

```bash
git status --short
```

Expected: clean working tree after commits, or only intentionally uncommitted files if the implementer is batching commits differently.

---

### Task 7: Prepare PR With Required Fixes Lines

**Files:**
- No code edits.

- [ ] **Step 1: Push the branch**

Run:

```bash
git push -u origin fix/spark-collection
```

Expected: branch pushes successfully.

- [ ] **Step 2: Open the PR**

Use this PR body:

```markdown
## Summary

- switch BERDL discovery guidance to `berdl_notebook_utils` access-aware helpers
- refactor collection snapshot generation to use `get_databases()`, `get_tables()`, and `get_table_schema()`
- remove stale Markdown collection inventory as an access source of truth
- update docs and agent skills to use native Spark SQL for query execution

## Testing

- `cd ui && uv run pytest tests/test_discover_berdl_collections.py tests/test_dataloader.py::TestParseCollections -q`
- `cd ui && uv run pytest tests/test_main.py::TestCollectionsRoute tests/test_wiki_lint.py -q`
- `cd ui && uv run ruff check app tests`

Fixes #229
Fixes #240
```

Run:

```bash
gh pr create \
  --repo kbaseincubator/BERIL-research-observatory \
  --base main \
  --head dileep-kishore:fix/spark-collection \
  --title "fix: use live BERDL discovery helpers" \
  --body-file /tmp/berdl-live-discovery-pr.md
```

Expected: PR opens against upstream and the body includes exactly:

```markdown
Fixes #229
Fixes #240
```

## Self-Review

- Spec coverage: #229 is covered by helper-based discovery, Spark SQL execution guidance, and removal of MCP query guidance. #240 is covered by deleting `docs/collections.md` and documenting the committed UI snapshot as a display/fallback artifact rather than an access source of truth.
- Placeholder scan: no task contains unresolved placeholder markers.
- Type consistency: the planned helper names match the upstream exports: `get_databases`, `get_tables`, `get_table_schema`; query execution uses `spark.sql(query)`.
