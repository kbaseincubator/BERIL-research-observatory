# Skani — ANI computation (generic)

**What it does**: Fast average nucleotide identity (ANI) computation between genome assemblies. Supports distance calculation (`dist`), all-vs-all triangle matrix (`triangle`), search against a database (`search`), and sketching (`sketch`). Input: nucleotide assembly FASTA files.

**Entrypoint**: `skani` — append the subcommand as the **first arg**.

**Refdata**: No — operates on your input files only.

```python
tscli = get_task_service_client()

# Example: pairwise distance between all input genomes
job = tscli.submit_job(
    "ghcr.io/kbaseincubator/cdm_skani:0.1.0",
    input_files,                          # nucleotide assembly FASTA files
    "cts/io/<username>/output/skani_run",
    cluster="kbase",
    input_mount_point="/in",              # CTS stages input files here
    output_mount_point="/out",            # skani writes output here
    args=[
        "dist",                           # subcommand — choose ONE:
                                          #   dist      : pairwise ANI between query and reference
                                          #   triangle  : all-vs-all ANI matrix (square matrix output)
                                          #   search    : query genomes against a reference database
                                          #   sketch    : pre-sketch genomes for later use
        tscli.insert_files(),             # input genome paths injected by CTS
        "-o", "/out/ani_results.tsv",     # output file; must be under output_mount_point
        "-t", "8",                        # number of threads; match cpus below
        "--min-af", "15",                 # minimum aligned fraction (%) to report a hit;
                                          # lower this (e.g. 5) for very distant genome comparisons
    ],
    num_containers=1,     # for dist/triangle, all genomes are compared together;
                          # for search with many queries, increase num_containers
    cpus=8,               # match -t above
    memory="16GB",        # typical; increase for large genome sets
    runtime="PT30M",      # skani is fast; scale with input count
)

print(f"Job ID: {job.id}")
```

**Typical resource guidance**:
- `cpus`: 8
- `memory`: 16 GB; increase for large genome sets
- `num_containers`: 1 for dist/triangle; more for independent search jobs
- `runtime`: fast; scale with input count
