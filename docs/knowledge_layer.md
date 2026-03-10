# Provenance & Knowledge Layer

This project has a 3-layer knowledge system:

1. **Layer 1: Project provenance (`provenance.yaml`)**
   - Per-project, structured metadata under `projects/<id>/provenance.yaml`
   - Captures references, BERDL data sources, cross-project deps, finding evidence, generated data

2. **Layer 2: Registry artifacts (`docs/`)**
   - `docs/project_registry.yaml` — project index
   - `docs/figure_catalog.yaml` — figure index
   - `docs/findings_digest.md` — findings summary

3. **Layer 3: Semantic graph (`knowledge/`)**
   - Entities, relations, hypotheses, timeline
   - Derived coverage + gap views in:
     - `docs/knowledge_graph_coverage.md`
     - `docs/knowledge_gaps.md`

## How to use

### 1) Generate/update provenance

```bash
uv run tools/generate_provenance.py <project_id>
# or all missing:
uv run tools/generate_provenance.py
```

### 2) Rebuild all registry + graph artifacts

```bash
uv run scripts/build_registry.py
```

### 3) Validate consistency

```bash
uv run scripts/validate_provenance.py
uv run scripts/validate_registry_freshness.py
```

### 4) Query knowledge deterministically

```bash
uv run scripts/query_knowledge.py search "metal stress"
uv run scripts/query_knowledge.py landscape
uv run scripts/query_knowledge.py gaps
```

## Typical update flow

1. Finish or edit a project report.
2. Generate/refresh that project's `provenance.yaml`.
3. Run `build_registry.py`.
4. Run both validators.

That keeps project-level evidence, global registry, and knowledge-graph views in sync.
