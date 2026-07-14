# GTDB-Tk — Phylogenetic classification against GTDB

**What it does**: Places bacterial and archaeal genome assemblies on the GTDB reference tree, producing taxonomy assignments (domain through species) and quality metrics. Input: nucleotide genome assemblies (`.fna` or `.fna.gz`).

**Entrypoint**: `gtdbtk`

**Refdata**: Yes — GTDB release232 data mounted at `/ref_data`. The image sets `GTDBTK_DATA_PATH=/ref_data/release232` automatically. **You do not pass `--db`.**

**Critical memory requirement**: GTDB-Tk's `skani` step loads the entire sketch database (~75 GB) into memory. **You must request at least 128 GB**, or the job will crash with an OOM error.

**Critical parallelism note**: Use **`num_containers=1`**. The `classify_wf` subcommand builds a shared marker-gene alignment and places all input genomes on a single tree. Splitting across containers breaks this — each container would only see its subset of genomes and produce a tree from an incomplete set.

```python
tscli = get_task_service_client()

job = tscli.submit_job(
    "ghcr.io/kbaseincubator/cdm_gtdbtk:0.1.1",
    input_files,                          # nucleotide assembly FASTA files (.fna or .fna.gz)
    "cts/io/<username>/output/gtdbtk_run",
    cluster="kbase",
    input_mount_point="/in",              # CTS stages all genome files into this directory
    output_mount_point="/out",            # gtdbtk writes all output here (taxonomy TSVs, trees, etc.)
    # refdata_mount_point is NOT needed: the image default /ref_data is used automatically
    args=[
        "classify_wf",                    # GTDB-Tk workflow: classifies genomes against the GTDB tree
        "--genome_dir", "/in",            # directory containing all input genomes;
                                          # matches input_mount_point — CTS places all inputs here
        "--out_dir", "/out",              # output directory; matches output_mount_point
        "--cpus", "16",                   # CPU threads; match cpus below
        "--extension", "fna.gz",          # file extension of input assemblies;
                                          # change to "fna" if your files are not gzip-compressed
        # GTDBTK_DATA_PATH=/ref_data/release232 is set automatically — do NOT pass --db
    ],
    num_containers=1,     # REQUIRED: classify_wf must see all genomes at once to build one tree
    cpus=16,              # match --cpus above; GTDB-Tk benefits from many cores
    memory="128GB",       # skani loads the ~75 GB GTDB sketch database into RAM; 128 GB is the safe floor
    runtime="PT4H",       # 1-4 hours for a small set of genomes; scale up for hundreds
)

print(f"Job ID: {job.id}")
```

**Typical resource guidance**:
- `cpus`: 16
- `memory`: 128 GB minimum (the ~75 GB GTDB sketch database must fit in RAM)
- `num_containers`: always 1
- `runtime`: 1–4 hours; increase for large input sets
