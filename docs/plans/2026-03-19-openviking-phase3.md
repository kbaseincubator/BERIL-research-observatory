# OpenViking Phase 3 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Materialize deterministic Git review artifacts from OpenViking project and figure resources without changing the repository's source-of-truth boundaries.

**Architecture:** Add a dedicated materialization layer that reads normalized resources from the Phase 2 service and emits deterministic YAML exports for `docs/project_registry.yaml` and `docs/figure_catalog.yaml`. Keep the service read/write contract unchanged, keep Git authoritative for authored assets, and treat generated YAML as single-writer materialized output.

**Tech Stack:** Python 3.12, pydantic, PyYAML, pytest, existing observatory_context service/manifest/render helpers

---

### Task 1: Add failing export parity tests

**Files:**
- Create: `scripts/tests/test_viking_phase3.py`

**Step 1: Write the failing test**

Add tests that cover:
- deterministic project registry export from project resources
- deterministic figure catalog export from figure resources
- failure when required export metadata is missing
- parity comparison against fixture YAML generated from current repository shape

**Step 2: Run test to verify it fails**

Run: `uv run --with pytest pytest scripts/tests/test_viking_phase3.py -q`
Expected: FAIL because the Phase 3 materialization modules do not exist yet

### Task 2: Add export models and materializers

**Files:**
- Create: `observatory_context/materialize/__init__.py`
- Create: `observatory_context/materialize/exports.py`
- Create: `observatory_context/materialize/serialize.py`
- Modify: `observatory_context/service/context_service.py`

**Step 1: Write minimal implementation**

Implement:
- normalized export builders for project registry rows
- normalized export builders for figure catalog rows
- deterministic sort order and YAML serialization helpers
- minimal service hooks only if the materializer needs existing workspace reads

**Step 2: Run test to verify it passes**

Run: `uv run --with pytest pytest scripts/tests/test_viking_phase3.py -q`
Expected: PASS

### Task 3: Add export scripts

**Files:**
- Create: `scripts/viking_materialize_exports.py`
- Create: `scripts/viking_validate_exports.py`

**Step 1: Write the failing script-level test**

Extend `scripts/tests/test_viking_phase3.py` to cover:
- materializing both YAML files into a temp output directory
- parity validation succeeding for matching outputs
- parity validation failing with a clear message for mismatched outputs

**Step 2: Run script-level test to verify it fails**

Run: `uv run --with pytest pytest scripts/tests/test_viking_phase3.py -q`
Expected: FAIL because script entry points do not exist yet

**Step 3: Write minimal implementation**

Implement:
- export materialization script with explicit output paths
- export validation script comparing generated YAML to tracked files

**Step 4: Run script-level test to verify it passes**

Run: `uv run --with pytest pytest scripts/tests/test_viking_phase3.py -q`
Expected: PASS

### Task 4: Run repository regression verification

**Files:**
- No new files

**Step 1: Run relevant tests**

Run:
- `uv run --with pytest pytest scripts/tests/test_viking_phase3.py -q`
- `uv run --with pytest pytest scripts/tests/test_viking_phase2.py -q`
- `uv run --with pytest pytest scripts/tests/test_viking_phase1.py -q`

Expected: PASS

**Step 2: Run validators**

Run:
- `uv run scripts/validate_provenance.py`
- `uv run scripts/validate_knowledge_graph.py`
- `uv run scripts/validate_registry_freshness.py`

Expected: PASS

### Task 5: Document Phase 3 outputs and cutover guardrails

**Files:**
- Modify: `docs/openviking_phase3_plan.md`
- Modify: `docs/openviking_phase2.md`
- Modify: `docs/openviking_setup.md`

**Step 1: Update docs**

Document:
- export commands and output paths
- single-writer rule for generated YAML
- what remains deferred after Phase 3

**Step 2: Verify docs references**

Run: `rg -n "viking_materialize_exports|viking_validate_exports|openviking_phase3" docs scripts observatory_context`
Expected: references are current and internally consistent
