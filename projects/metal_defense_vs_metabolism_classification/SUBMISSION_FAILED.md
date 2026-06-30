# Submission Pending

The lakehouse upload for this project failed.

- **Project**: metal_defense_vs_metabolism_classification
- **Last attempt**: 2026-06-29T01:10:49Z
- **Error**: Insufficient permissions — `mc cp` returned non-zero for all files. The `berdl-minio` alias credentials may be expired or misconfigured.
- **Approved at**: 2026-06-29T01:10:49Z

Status is `complete` (the approval is recorded in `beril.yaml`).
Re-run `/submit` to retry the upload — it will skip the approval step and only retry the upload.

To fix: run `mc alias set berdl-minio $MINIO_ENDPOINT_URL $MINIO_ACCESS_KEY $MINIO_SECRET_KEY` to refresh credentials, then re-run `/submit metal_defense_vs_metabolism_classification`.
