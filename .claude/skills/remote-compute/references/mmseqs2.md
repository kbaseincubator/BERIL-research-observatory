# MMseqs2 — Sequence clustering and search

**What it does**: Ultra-fast protein and nucleotide sequence clustering (`easy-cluster`, `easy-linclust`) and search (`easy-search`). Input: FASTA files. Output: cluster TSV or search hits TSV depending on subcommand.

**Entrypoint**: `mmseqs` — append the desired subcommand as the **first arg** (`easy-cluster`, `easy-search`, `easy-linclust`, etc.)

**Refdata**: No — operates entirely on your input files.

```python
tscli = get_task_service_client()

# Example: cluster protein sequences
job = tscli.submit_job(
    "ghcr.io/kbaseincubator/cdm_mmseqs2:0.1.0",
    input_files,                          # FASTA files to cluster or search
    "cts/io/<username>/output/mmseqs_run",
    cluster="kbase",
    input_mount_point="/in",              # where CTS stages your input files inside the container
    output_mount_point="/out",            # mmseqs writes results here
    args=[
        "easy-cluster",                   # mmseqs subcommand; alternatives: easy-search, easy-linclust
        tscli.insert_files(),             # input FASTA path(s) — CTS injects the staged file paths here
        "/out/clusters",                  # output prefix: mmseqs writes clusters.tsv, clusters_rep.fasta, etc.
        "/tmp/mmseqs_tmp",                # temporary working directory inside the container
        "--threads", "8",                 # CPU threads; match cpus below
        "--min-seq-id", "0.5",            # minimum sequence identity threshold (0.0–1.0); adjust for your use case
        "--cov-mode", "0",                # coverage mode: 0=bidirectional, 1=query, 2=target
        "-c", "0.8",                      # minimum coverage fraction; adjust for your use case
    ],
    num_containers=1,     # mmseqs operates on all inputs together for clustering;
                          # use num_containers>1 only for independent search jobs
    cpus=8,               # mmseqs scales well with cores; 8-16 is typical
    memory="32GB",        # depends on database size; start at 32GB, increase if OOM
    runtime="PT2H",       # varies widely with input size; adjust accordingly
)

print(f"Job ID: {job.id}")
```

**Typical resource guidance**:
- `cpus`: 8–16
- `memory`: 32–128 GB depending on sequence database size
- `num_containers`: 1 for clustering (all sequences must be seen together); more for independent search jobs
- `runtime`: highly variable — profile a small subset first
