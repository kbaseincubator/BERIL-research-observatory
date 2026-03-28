# OpenViking Resource Model

OpenViking is the single source of truth for all observatory knowledge data.

## URI layout

Project-authored assets:

```text
viking://resources/observatory/projects/{project_id}/authored/{relative_path}
```

Figure resources:

```text
viking://resources/observatory/projects/{project_id}/authored/figures/{figure_id}
```

## Resource kinds

- `project`: the project `README.md` entry point
- `project_document`: project `REPORT.md` and `provenance.yaml`
- `figure`: project figure files

## Deterministic metadata

Every manifest item carries these stable fields:

- `id`
- `kind`
- `title`
- `project_ids`
- `source_refs`
- `tags`

The renderer uses these fields to create deterministic `L0`, `L1`, and `L2`
views without model-generated summaries.

## Idempotency rule

Logical resources are identified by their deterministic URI. Re-ingest should
re-use the same URI for the same source artifact so parity checks can detect
duplicate logical resources by URI alone.
