# OpenViking Live Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Finish the OpenViking migration so the repository can run against a real local OpenViking server, materialize deterministic outputs from live server-backed resources, and provide one current setup/tutorial path.

**Architecture:** Keep Git authoritative for authored project artifacts and tracked generated outputs, but make OpenViking the live read/write layer for service operations and materialization workflows. Add a small bootstrap/runtime helper for consistent client construction and live-mode checks, then update export and overlay scripts to read through OpenViking-backed service paths instead of repo-only mode by default. Clean up phase-specific docs/tests that are no longer the right public interface and replace them with one current tutorial.

**Tech Stack:** Python 3.11+, OpenViking SyncHTTPClient, pydantic-settings, pytest, PyYAML, uv

---

### Task 1: Add failing live-runtime tests

**Files:**
- Create: `scripts/tests/test_viking_runtime.py`
- Modify: `scripts/tests/test_viking_exports.py`
- Modify: `scripts/tests/test_viking_overlays.py`

**Step 1: Write the failing test**

Add tests that cover:
- building a configured live client/bootstrap helper from env/config
- failing clearly when a live-only command is used without a reachable server
- export and overlay materializers using a passed live client/service instead of hard-coded `client=None`

**Step 2: Run test to verify it fails**

Run: `uv run --with pytest pytest scripts/tests/test_viking_runtime.py -q`
Expected: FAIL because the runtime/bootstrap helpers do not exist yet

**Step 3: Write minimal implementation**

Implement only the bootstrap/runtime helpers needed by the failing tests.

**Step 4: Run test to verify it passes**

Run: `uv run --with pytest pytest scripts/tests/test_viking_runtime.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/tests/test_viking_runtime.py observatory_context/runtime.py observatory_context/config.py observatory_context/client.py
git commit -m "feat: add openviking runtime bootstrap"
```

### Task 2: Switch materializers to live-backed mode

**Files:**
- Modify: `scripts/viking_materialize_exports.py`
- Modify: `scripts/viking_validate_exports.py`
- Modify: `scripts/viking_materialize_overlays.py`
- Modify: `scripts/viking_validate_overlays.py`
- Modify: `observatory_context/service/context_service.py`
- Test: `scripts/tests/test_viking_exports.py`
- Test: `scripts/tests/test_viking_overlays.py`

**Step 1: Extend the failing tests**

Add coverage for:
- live-backed service construction in export/overlay scripts
- explicit offline fallback mode where needed
- parity checks comparing generated outputs against tracked Git files while reading the source payloads through the live-backed service path

**Step 2: Run tests to verify they fail**

Run:
- `uv run --with pytest pytest scripts/tests/test_viking_exports.py -q`
- `uv run --with pytest pytest scripts/tests/test_viking_overlays.py -q`
Expected: FAIL because scripts still instantiate repo-only service paths

**Step 3: Write minimal implementation**

Update the scripts and service wiring so:
- live mode is the default for migration commands
- offline mode is explicit
- read/materialize flows use OpenViking-backed resources when configured

**Step 4: Run tests to verify they pass**

Run:
- `uv run --with pytest pytest scripts/tests/test_viking_exports.py -q`
- `uv run --with pytest pytest scripts/tests/test_viking_overlays.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/viking_materialize_exports.py scripts/viking_validate_exports.py scripts/viking_materialize_overlays.py scripts/viking_validate_overlays.py observatory_context/service/context_service.py scripts/tests/test_viking_exports.py scripts/tests/test_viking_overlays.py
git commit -m "feat: use live server for materialization"
```

### Task 3: Add real setup operations

**Files:**
- Create: `scripts/viking_server_healthcheck.py`
- Create: `scripts/viking_setup.py`
- Modify: `config/openviking/ov.conf.example`
- Test: `scripts/tests/test_viking_runtime.py`

**Step 1: Write the failing test**

Add tests that cover:
- generating or validating repo-local config/runtime paths
- checking OpenViking server reachability
- printing a concise operator workflow for first-time setup

**Step 2: Run test to verify it fails**

Run: `uv run --with pytest pytest scripts/tests/test_viking_runtime.py -q`
Expected: FAIL because the setup/healthcheck scripts do not exist yet

**Step 3: Write minimal implementation**

Implement:
- a healthcheck script for the configured server
- a setup script that validates config, environment, and expected workflow prerequisites

**Step 4: Run test to verify it passes**

Run: `uv run --with pytest pytest scripts/tests/test_viking_runtime.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/viking_server_healthcheck.py scripts/viking_setup.py config/openviking/ov.conf.example scripts/tests/test_viking_runtime.py
git commit -m "feat: add real openviking setup commands"
```

### Task 4: Clean up migration-era docs and tests

**Files:**
- Remove or rename: phase-numbered tests under `scripts/tests/`
- Remove or archive: stale phase-only docs under `docs/` and `docs/plans/`
- Create: `scripts/tests/test_viking_manifest.py`
- Create: `scripts/tests/test_viking_service.py`
- Create: `scripts/tests/test_viking_exports.py`
- Create: `scripts/tests/test_viking_overlays.py`

**Step 1: Write the failing test**

Port the existing behavior coverage into stable, behavior-named test files before deleting the old phase-numbered files.

**Step 2: Run tests to verify they fail**

Run: `uv run --with pytest pytest scripts/tests/test_viking_manifest.py scripts/tests/test_viking_service.py scripts/tests/test_viking_exports.py scripts/tests/test_viking_overlays.py -q`
Expected: FAIL until the migrated test files exist and are wired correctly

**Step 3: Write minimal implementation**

Create the new test files by moving the existing coverage, then remove the obsolete phase-numbered files and stale planning/prompt docs that are no longer the right operator-facing documentation.

**Step 4: Run tests to verify they pass**

Run: `uv run --with pytest pytest scripts/tests/test_viking_manifest.py scripts/tests/test_viking_service.py scripts/tests/test_viking_exports.py scripts/tests/test_viking_overlays.py scripts/tests/test_viking_runtime.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/tests docs
git commit -m "refactor: clean up migration phase artifacts"
```

### Task 5: Write the current tutorial and verify the full workflow

**Files:**
- Create: `docs/openviking_tutorial.md`
- Modify: `README.md`
- Modify: `docs/openviking_setup.md`

**Step 1: Write the failing test**

Add or update a lightweight doc-oriented test only if there is existing doc validation. Otherwise skip test creation and verify via command execution.

**Step 2: Write minimal implementation**

Document:
- environment setup
- config creation
- server start
- healthcheck
- ingest
- live-context usage
- export and overlay materialization
- validation
- offline fallback notes

**Step 3: Run verification**

Run:
- `uv run scripts/viking_setup.py`
- `uv run scripts/viking_server_healthcheck.py` or document the exact failure mode if server is not running
- `uv run --with pytest pytest scripts/tests -q`

Expected:
- setup script succeeds in validating local prerequisites
- healthcheck reports server state clearly
- tests pass

**Step 4: Commit**

```bash
git add docs/openviking_tutorial.md docs/openviking_setup.md README.md
git commit -m "docs: add current openviking tutorial"
```

### Task 6: Final migration verification

**Files:**
- No new files

**Step 1: Run the full verification set**

Run:
- `uv run --with pytest pytest scripts/tests -q`
- `uv run scripts/validate_provenance.py`
- `uv run scripts/validate_knowledge_graph.py`
- `uv run scripts/validate_registry_freshness.py`
- `uv run scripts/viking_validate_parity.py`

**Step 2: Run operator workflow checks**

Run:
- `uv run scripts/viking_ingest.py --dry-run --limit 5`
- `uv run scripts/viking_materialize_exports.py --offline`
- `uv run scripts/viking_validate_exports.py --generated-dir docs --offline`
- `uv run scripts/viking_materialize_overlays.py --offline`
- `uv run scripts/viking_validate_overlays.py --generated-dir knowledge --offline`

**Step 3: Summarize gaps**

If a real OpenViking server is not available in the local environment, report exactly which live-server checks were validated by automated tests versus which remain ready-but-unexercised operationally.
