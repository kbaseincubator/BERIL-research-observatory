# OpenViking Phase 2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the Phase 2 Observatory Context Service with deterministic read APIs, lexical fallback, and live note/observation writes on top of the existing Phase 0/1 manifest and render foundations.

**Architecture:** Add a root-level service layer that indexes authored resources from the Phase 1 manifest and augments them with live note and observation resources stored in OpenViking. Keep deterministic L0/L1/L2 rendering in the existing renderer, use metadata/link-driven related-resource logic, and fall back to lexical/path/metadata retrieval when semantic search is unavailable.

**Tech Stack:** Python 3.12, pydantic, pytest, OpenViking SyncHTTPClient, existing observatory_context manifest/render helpers

---

### Task 1: Add failing Phase 2 service tests

**Files:**
- Create: `scripts/tests/test_viking_phase2.py`

**Step 1: Write the failing test**

Add tests that cover:
- `get_resource(...)` resolving a project resource by id and URI with deterministic `L0/L1/L2`
- `get_project_workspace(...)` and `list_project_resources(...)`
- `search_context(...)` with lexical fallback when semantic search fails
- `related_resources(...)` using project membership, tags, source refs, and explicit links
- `add_note(...)` and `add_observation(...)` creating live resources visible to subsequent reads

**Step 2: Run test to verify it fails**

Run: `uv run pytest scripts/tests/test_viking_phase2.py -q`
Expected: FAIL because the new service modules do not exist yet

### Task 2: Add minimal service and retrieval implementation

**Files:**
- Create: `observatory_context/service/__init__.py`
- Create: `observatory_context/service/models.py`
- Create: `observatory_context/service/context_service.py`
- Create: `observatory_context/retrieval/__init__.py`
- Create: `observatory_context/retrieval/index.py`
- Create: `observatory_context/retrieval/search.py`
- Create: `observatory_context/retrieval/related.py`
- Create: `observatory_context/notes/__init__.py`
- Create: `observatory_context/notes/store.py`
- Modify: `observatory_context/client.py`
- Modify: `observatory_context/uris.py`
- Modify: `observatory_context/__init__.py`

**Step 1: Write minimal implementation**

Implement:
- typed resource/result/workspace models
- manifest-backed authored resource index
- live note/observation serialization and parsing
- project-scoped workspace listing
- semantic-first search with lexical/path/metadata fallback
- metadata/link-driven related-resource ranking
- note and observation write helpers with append-only URIs

**Step 2: Run targeted tests**

Run: `uv run pytest scripts/tests/test_viking_phase2.py -q`
Expected: PASS

### Task 3: Run regression verification

**Files:**
- No new files

**Step 1: Run existing Phase 1 tests**

Run: `uv run pytest scripts/tests/test_viking_phase1.py -q`
Expected: PASS

**Step 2: Run existing validators**

Run:
- `uv run scripts/validate_provenance.py`
- `uv run scripts/validate_knowledge_graph.py`
- `uv run scripts/validate_registry_freshness.py`

Expected: PASS

### Task 4: Refresh implementation docs for the next phase

**Files:**
- Create: `docs/openviking_phase2.md`
- Create: `docs/openviking_phase3_plan.md`
- Modify: `docs/openviking_setup.md`
- Modify: `docs/viking_sql_migration.md`

**Step 1: Replace stale phase docs**

Document:
- what Phase 2 now implements
- how to smoke test the service
- what remains for Phase 3 only

**Step 2: Verify docs references**

Run: `rg -n "openviking_phase" docs observatory_context scripts`
Expected: no stale references remain
