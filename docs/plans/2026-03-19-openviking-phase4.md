# OpenViking Phase 4 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Materialize deterministic overlay resources from the current knowledge-layer files without changing the Phase 2/3 source-of-truth boundaries.

**Architecture:** Reuse the existing OpenViking ingest/resource model and add a narrow overlay materialization layer for the current knowledge YAML family only. Keep overlays derived, deterministic, and reviewable, and avoid widening the service into a generic graph API.

**Tech Stack:** Python 3.12, pydantic, PyYAML, pytest, existing observatory_context manifest/materialize helpers

---

### Task 1: Add failing overlay parity tests

**Files:**
- Create: `scripts/tests/test_viking_phase4.py`

**Step 1: Write the failing test**

Add tests that cover:
- deterministic overlay resource construction from `knowledge/*.yaml`
- deterministic ordering of serialized overlay outputs
- parity comparison against tracked knowledge YAML payloads
- failure when required overlay metadata is missing

**Step 2: Run test to verify it fails**

Run: `uv run --with pytest pytest scripts/tests/test_viking_phase4.py -q`
Expected: FAIL because the Phase 4 overlay modules do not exist yet

### Task 2: Add overlay materializers

**Files:**
- Create: `observatory_context/overlays/__init__.py`
- Create: `observatory_context/overlays/materialize.py`
- Create: `observatory_context/overlays/serialize.py`

**Step 1: Write minimal implementation**

Implement:
- deterministic overlay builders for the current knowledge YAML families
- stable ordering and serialization helpers
- explicit metadata validation for overlay-critical fields

**Step 2: Run test to verify it passes**

Run: `uv run --with pytest pytest scripts/tests/test_viking_phase4.py -q`
Expected: PASS

### Task 3: Add overlay scripts

**Files:**
- Create: `scripts/viking_materialize_overlays.py`
- Create: `scripts/viking_validate_overlays.py`

**Step 1: Extend the failing test**

Cover:
- materializing overlays into a temp output directory
- parity validation succeeding for matching outputs
- parity validation failing with a clear message for mismatched outputs

**Step 2: Run test to verify it fails**

Run: `uv run --with pytest pytest scripts/tests/test_viking_phase4.py -q`
Expected: FAIL because the script entry points do not exist yet

**Step 3: Write minimal implementation**

Implement:
- overlay materialization script with explicit output paths
- overlay validation script comparing generated overlays to tracked files

**Step 4: Run test to verify it passes**

Run: `uv run --with pytest pytest scripts/tests/test_viking_phase4.py -q`
Expected: PASS

### Task 4: Run repository regression verification

**Files:**
- No new files

**Step 1: Run relevant tests**

Run:
- `uv run --with pytest pytest scripts/tests/test_viking_phase4.py -q`
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
