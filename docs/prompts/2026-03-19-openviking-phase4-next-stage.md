# Prompt: OpenViking Phase 4 Next Stage

Use this prompt for the next implementation session.

## Prompt

Implement OpenViking Phase 4 only: deterministic overlay materialization for
the current tracked `knowledge/*.yaml` family.

Read these docs first, in order:

1. [`docs/viking_sql_migration.md`](/Users/g8k/Documents/Work/Collaborations/BERIL-research-observatory/docs/viking_sql_migration.md)
2. [`docs/openviking_phase2.md`](/Users/g8k/Documents/Work/Collaborations/BERIL-research-observatory/docs/openviking_phase2.md)
3. [`docs/openviking_phase3.md`](/Users/g8k/Documents/Work/Collaborations/BERIL-research-observatory/docs/openviking_phase3.md)
4. [`docs/openviking_phase4.md`](/Users/g8k/Documents/Work/Collaborations/BERIL-research-observatory/docs/openviking_phase4.md)
5. [`docs/openviking_phase4_plan.md`](/Users/g8k/Documents/Work/Collaborations/BERIL-research-observatory/docs/openviking_phase4_plan.md)
6. [`docs/plans/2026-03-19-openviking-phase4.md`](/Users/g8k/Documents/Work/Collaborations/BERIL-research-observatory/docs/plans/2026-03-19-openviking-phase4.md)
7. [`docs/openviking_resource_model.md`](/Users/g8k/Documents/Work/Collaborations/BERIL-research-observatory/docs/openviking_resource_model.md)

Then inspect the current implementation:

- [`observatory_context`](/Users/g8k/Documents/Work/Collaborations/BERIL-research-observatory/observatory_context)
- [`scripts/tests/test_viking_phase1.py`](/Users/g8k/Documents/Work/Collaborations/BERIL-research-observatory/scripts/tests/test_viking_phase1.py)
- [`scripts/tests/test_viking_phase2.py`](/Users/g8k/Documents/Work/Collaborations/BERIL-research-observatory/scripts/tests/test_viking_phase2.py)
- [`scripts/tests/test_viking_phase3.py`](/Users/g8k/Documents/Work/Collaborations/BERIL-research-observatory/scripts/tests/test_viking_phase3.py)
- [`scripts/viking_ingest.py`](/Users/g8k/Documents/Work/Collaborations/BERIL-research-observatory/scripts/viking_ingest.py)
- [`scripts/viking_materialize_exports.py`](/Users/g8k/Documents/Work/Collaborations/BERIL-research-observatory/scripts/viking_materialize_exports.py)
- [`scripts/viking_validate_exports.py`](/Users/g8k/Documents/Work/Collaborations/BERIL-research-observatory/scripts/viking_validate_exports.py)

Task scope:

- Implement Phase 4 only: deterministic overlay materialization for the current
  tracked `knowledge/*.yaml` files.
- Reuse the Phase 2 service and the Phase 3 materialization patterns where
  directly useful.
- Keep Git authoritative for tracked knowledge YAML outputs.
- Keep overlays derived and deterministic.

Required capabilities:

- Add `observatory_context/overlays/`
- Add deterministic materialization for the current tracked knowledge YAML
  family
- Add:
  - `scripts/viking_materialize_overlays.py`
  - `scripts/viking_validate_overlays.py`
- Add targeted Phase 4 tests for:
  - overlay materialization
  - deterministic ordering
  - missing required metadata failures
  - parity validation against tracked knowledge YAML outputs

Out of scope:

- SQLite
- tenancy
- memory design
- UI integration
- generic graph traversal
- exporting live notes or observations into authored Git files

Execution requirements:

- Follow TDD strictly: write failing Phase 4 tests first, run them and confirm
  failure, then implement minimal code.
- Prefer simple, explicit code over abstractions.
- Preserve deterministic behavior and identifier stability.

Minimum verification before finishing:

- `uv run --with pytest pytest scripts/tests/test_viking_phase4.py -q`
- `uv run --with pytest pytest scripts/tests/test_viking_phase3.py -q`
- `uv run --with pytest pytest scripts/tests/test_viking_phase2.py -q`
- `uv run --with pytest pytest scripts/tests/test_viking_phase1.py -q`
- `uv run scripts/validate_provenance.py`
- `uv run scripts/validate_knowledge_graph.py`
- `uv run scripts/validate_registry_freshness.py`

When done, summarize:

- what Phase 4 was implemented
- which overlay/public interfaces were added
- exact verification commands run and exact outcomes
- any remaining deferred work after this slice
