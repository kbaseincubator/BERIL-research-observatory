# Query Size Guidance

Use this table to choose between inline return and export.

| Expected output size | Pattern | Recommended action |
|---|---|---|
| <= 10K rows | Interactive | Return inline JSON (bounded `LIMIT`) |
| 10K-250K rows | Semi-interactive | Return summary + small sample, then offer export |
| > 250K rows | Batch | Use `scripts/export_sql.py` and store output in MinIO |

## Notes

- Prefer `ORDER BY` when paging with `LIMIT/OFFSET`.
- Avoid unbounded `collect()` calls for unknown table sizes.
- For expensive queries, first run `SELECT COUNT(*)` or a filtered preview.
