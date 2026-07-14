# Bakta (proteins) — Protein sequence annotation

**What it does**: Annotates protein sequences (rather than genome assemblies) using the Bakta database. Input: protein FASTA files (`.faa` or `.faa.gz`). Output: TSV with functional annotations per protein.

**Entrypoint**: `bakta_proteins`

**Refdata**: Yes — same Bakta database as `bakta` (`/ref_data/db`). The image sets `BAKTA_DB=/ref_data/db` automatically. **No `--db` argument needed.**

```python
tscli = get_task_service_client()

job = tscli.submit_job(
    "ghcr.io/kbaseincubator/cdm_bakta_proteins:0.1.0",
    input_files,                          # protein FASTA files (.faa or .faa.gz)
    "cts/io/<username>/output/bakta_proteins_run",
    cluster="kbase",
    output_mount_point="/out",            # bakta_proteins writes annotation output here
    args=[
        "--output", "/out",               # tell bakta_proteins where to write results;
                                          # must match output_mount_point
        "--threads", "4",                 # CPU threads; match cpus below
        "--force",                        # REQUIRED: same reason as Bakta above —
                                          # CTS pre-creates /out and bakta_proteins requires --force
        # --db is NOT needed: BAKTA_DB=/ref_data/db is set in the image automatically
        tscli.insert_files(),             # input protein FASTA path injected by CTS at runtime
    ],
    num_containers=len(input_files),  # one container per input FASTA
    cpus=4,               # match --threads above
    memory="8GB",         # typical; increase for very large protein sets
    runtime="PT30M",      # scale with proteome size
)

print(f"Job ID: {job.id}")
```

**Typical resource guidance**:
- `cpus`: 4
- `memory`: 8–16 GB
- `num_containers`: equals number of input files
- `runtime`: 15–30 min per file
