# Performance Notes — nmdc_context_audit

<!-- [nmdc_context_audit] 2026-07-10T18:07:52Z  approved-report extraction (REVIEW: REVIEW_3.md) -->

- Row counts on all NMDC tables — including `nmdc.results.annotation_kegg_orthology`
  (1.83B rows) — return instantly via Iceberg metadata (`SELECT COUNT(*)`), so cataloguing
  scale is cheap and need not be avoided.
- `DESCRIBE DATABASE EXTENDED kbase.nmdc_*` raises `ForbiddenException` for a
  `kesciencero`/`microbialdiscoveryforge` principal even though `COUNT(*)` on the same
  tables succeeds — metadata introspection and data reads have different access surfaces.
- `get_databases()` returns **both** the dotted Iceberg alias (`nmdc.metadata`) and the
  underscore Hive alias (`nmdc_metadata`) for every tenant DB, so de-dupe to the dotted form
  before iterating to avoid double-counting. (The broader dotted-vs-underscore namespace
  migration is already documented repo-wide in `docs/pitfalls.md`; this note is only the
  `get_databases()`-returns-both-forms delta.)
