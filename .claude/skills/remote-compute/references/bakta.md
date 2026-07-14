# Bakta — Genome annotation (nucleotide assemblies)

**What it does**: Comprehensive annotation of bacterial genome assemblies. Produces GFF3, GenBank, FASTA of annotated features, and summary TSV. Input: nucleotide assembly FASTA files (`.fna` or `.fna.gz`). One genome per container.

**Entrypoint**: `bakta`

**Refdata**: Yes — Bakta database mounted at `/ref_data/db`. The image sets the environment variable `BAKTA_DB=/ref_data/db` automatically, so **you do not need to pass `--db`** on the command line.

```python
tscli = get_task_service_client()

job = tscli.submit_job(
    "ghcr.io/kbaseincubator/cdm_bakta:0.1.3",
    input_files,                          # nucleotide assembly FASTA files (.fna or .fna.gz)
    "cts/io/<username>/output/bakta_run",
    cluster="kbase",
    output_mount_point="/out",            # bakta writes all output files here
    args=[
        "--output", "/out",               # tell bakta where to write results;
                                          # must match output_mount_point so CTS can collect them
        "--threads", "4",                 # CPU threads; match cpus below
        "--force",                        # REQUIRED: CTS pre-creates /out before the job starts;
                                          # bakta refuses to write to an existing directory without --force
        # --db is NOT needed: the image sets BAKTA_DB=/ref_data/db automatically
        tscli.insert_files(),             # input genome FASTA path injected by CTS at runtime
    ],
    num_containers=len(input_files),  # one container per genome — bakta annotates one assembly per run
    cpus=4,               # match --threads above
    memory="8GB",         # typical; increase to 16GB for large or complex assemblies
    runtime="PT30M",      # ~10-20 min per genome; scale for large assemblies
)

print(f"Job ID: {job.id}")
```

**Typical resource guidance**:
- `cpus`: 4 (matches `--threads 4`)
- `memory`: 8–16 GB
- `num_containers`: equals number of input genomes
- `runtime`: 15–30 min per genome
