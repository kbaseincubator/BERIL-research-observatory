# PSORTb — Protein subcellular localization prediction

**What it does**: Predicts the subcellular localization (cytoplasm, membrane, periplasm, extracellular, etc.) of bacterial proteins. Input: protein FASTA files (`.faa`). Output: TSV with one localization prediction per protein.

**Entrypoint**: `/usr/local/bin/run-psort` — a wrapper script around PSORTb.

**Refdata**: No.

**Important**: PSORTb processes **one FASTA file per invocation**. Set `num_containers` equal to the number of input files.

```python
tscli = get_task_service_client()

job = tscli.submit_job(
    "ghcr.io/kbaseincubator/cdm_psortb:0.1.2",
    input_files,                          # protein FASTA files (.faa); one per container
    "cts/io/<username>/output/psortb_run",
    cluster="kbase",
    input_mount_point="/in",              # where CTS stages your input files inside the container
    output_mount_point="/out",            # wrapper writes <input-basename>.psortb.tsv here automatically
    args=[
        "--negative",                     # organism flag — choose ONE:
                                          #   --positive  : gram-positive bacteria
                                          #   --negative  : gram-negative bacteria
                                          #   --archaea   : archaea
        "--output", "terse",              # output format — choose ONE:
                                          #   terse  : one line per protein (easiest for downstream parsing)
                                          #   normal : includes scores and details
                                          #   long   : full verbose output
        tscli.insert_files(),             # input protein FASTA path injected by CTS;
                                          # only one file is processed per container
    ],
    num_containers=len(input_files),  # one container per input FASTA — PSORTb cannot batch
    cpus=2,               # PSORTb is not heavily multithreaded; 2 cores is sufficient
    memory="4GB",         # low memory footprint
    runtime="PT30M",      # typically fast; scale for very large proteomes
)

print(f"Job ID: {job.id}")
```

**Typical resource guidance**:
- `cpus`: 2
- `memory`: 4 GB
- `num_containers`: equals the number of input FASTA files (one invocation per file)
- `runtime`: 5–30 min per file depending on proteome size
