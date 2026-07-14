# CheckM2 — Genome quality assessment

**What it does**: Predicts genome completeness and contamination using machine-learning on marker genes. Input: nucleotide assembly FASTA files (`.fna` or `.fna.gz`). Output: `quality_report.tsv` with completeness/contamination per genome.

**Entrypoint**: `checkm2 predict` (the `predict` subcommand is already part of the entrypoint — do not include it in `args`)

**Refdata**: Yes — marker gene database mounted at `/ref_data` automatically. The tool finds it via its own config; you do not need to pass `--database` or any path argument.

```python
tscli = get_task_service_client()

job = tscli.submit_job(
    "ghcr.io/kbasetest/cdm_checkm2:0.3.0",
    input_files,                          # .fna or .fna.gz nucleotide assemblies
    "cts/io/<username>/output/checkm2_run",
    cluster="kbase",
    output_mount_point="/out",            # checkm2 writes quality_report.tsv here
    args=[
        "--output-directory", "/out",     # tell checkm2 to write results to the output mount point
        "--threads", "4",                 # number of CPU threads; match the cpus parameter below
        "--input", tscli.insert_files(),  # CTS replaces this with the input file paths at runtime,
                                          # splitting them evenly across containers
    ],
    num_containers=2,     # split input files across N containers for parallelism;
                          # each container processes its share independently
    cpus=4,               # cores per container; match --threads above
    memory="20GB",        # CheckM2 loads ML models into memory; 20GB is the recommended floor
    runtime="PT30M",      # ~5-10 min per genome; scale up for large batches
    declobber=True,       # prepend container number to output paths so containers
                          # don't overwrite each other's quality_report.tsv
)

print(f"Job ID: {job.id}")
```

**Typical resource guidance**:
- `cpus`: 4 (matches `--threads 4`)
- `memory`: 20 GB minimum; increase to 32 GB for very large genomes
- `num_containers`: scale with input count — 1 container per 5-10 genomes is reasonable
- `runtime`: 10 min/genome; 30 min for a batch of ≤20 genomes

**Spark auto-import**: CheckM2 has a registered event importer. When the job completes, a
CTS-side pipeline automatically reads `quality_report.tsv` and loads the results into the
BERDL table `u_<username>__autoimport.checkm2`, tagged with `cts_job_id`.

The auto-import target database must exist before the job completes or results will be
silently lost. **Ensure it exists before submitting the job:**

```python
from berdl_notebook_utils.setup_spark_session import get_spark_session
spark = get_spark_session()
spark.sql("CREATE DATABASE IF NOT EXISTS u_<username>__autoimport")
```

Use `wait_for_completion(wait_for_event_importer=True)` to wait for both the job and the
import to finish, then query directly without downloading:

```python
df = spark.sql(f"""
    SELECT * FROM u_<username>__autoimport.checkm2
    WHERE cts_job_id = '{job.id}'
""")
df.show()
```

If you are unsure whether another image has an importer, ask the CTS team or omit
`wait_for_event_importer=True` and download results manually.
