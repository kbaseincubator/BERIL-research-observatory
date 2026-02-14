# CheckM2 — Genome Quality Assessment

CheckM2 uses machine learning to assess the quality (completeness and contamination) of genome assemblies. It is the only currently approved image on CTS.

## Image

- **Image**: `ghcr.io/kbasetest/cdm_checkm2:0.3.0`
- **Entrypoint**: `checkm2 predict` (the `predict` subcommand is built into the entrypoint -- do not repeat it in args)
- **Reference data**: Pre-staged and mounted automatically by CTS

## Input

- Genome assembly files (`.fna.gz` or `.fna`) in S3 bucket `cts`
- Files must have CRC64NVME checksums

## Job Template (curl)

```json
{
  "cluster": "kbase",
  "image": "ghcr.io/kbasetest/cdm_checkm2:0.3.0",
  "params": {
    "args": [
      "--threads", "8",
      "--input",
      {"type": "input_files", "input_files_format": "space_separated_list"},
      "-x", "fna.gz",
      "--output-directory", "/output_files"
    ],
    "input_mount_point": "/input_files",
    "output_mount_point": "/output_files",
    "declobber": true
  },
  "input_files": [
    "cts/io/username/genomes/genome1.fna.gz",
    "cts/io/username/genomes/genome2.fna.gz"
  ],
  "output_dir": "cts/io/username/checkm2/run_name",
  "num_containers": 2,
  "cpus": 8,
  "memory": "10GB",
  "runtime": 3600
}
```

### Key args explained

| Arg | Purpose |
|-----|---------|
| `--threads 8` | Use 8 threads (match `cpus` value) |
| `--input` | Required flag before the input files placeholder |
| `{"type": "input_files", "input_files_format": "space_separated_list"}` | CTS replaces this with the actual input file paths assigned to each container |
| `-x fna.gz` | Input file extension (adjust if using `.fna`) |
| `--output-directory /output_files` | Output directory (must match `output_mount_point`) |

### Multi-container pattern

When running many genomes, split across containers:
- Set `num_containers` to the desired parallelism (up to 1000)
- CTS automatically distributes `input_files` across containers
- Set `declobber: true` to prepend container numbers to output paths, preventing overwrites

## Job Template (Python client — JupyterHub)

```python
tscli = get_task_service_client()

job = tscli.submit_job(
    cluster="kbase",
    image="ghcr.io/kbasetest/cdm_checkm2:0.3.0",
    args=[
        "--threads", "8",
        "--input",
        {"type": "input_files", "input_files_format": "space_separated_list"},
        "-x", "fna.gz",
        "--output-directory", "/output_files"
    ],
    input_mount_point="/input_files",
    output_mount_point="/output_files",
    declobber=True,
    input_files=[
        "cts/io/username/genomes/genome1.fna.gz",
        "cts/io/username/genomes/genome2.fna.gz",
    ],
    output_dir="cts/io/username/checkm2/run_name",
    num_containers=2,
    cpus=8,
    memory="10GB",
    runtime=3600,
)

print(f"Job ID: {job.id}")

# Wait for completion (blocks until done)
job.wait_for_completion(wait_for_event_importer=True)

# Check results
job.get_exit_codes()
job.print_logs(container_num=0, stderr=True)
```

## Output Files

CheckM2 produces the following in each container's output directory:

| File/Directory | Description |
|----------------|-------------|
| `quality_report.tsv` | Main results: completeness, contamination, and model info per genome |
| `protein_files/` | Predicted protein sequences |
| `diamond_output/` | DIAMOND alignment results |

## Auto-Import to Delta Tables

CheckM2 results are automatically imported into a user-specific Delta table:

- **Table**: `u_{username}__autoimport.checkm2`
- **Query**: `spark.sql("SELECT * FROM u_{username}__autoimport.checkm2 WHERE cts_job_id = '{job_id}'")`

### Columns

| Column | Type | Description |
|--------|------|-------------|
| `Name` | string | Genome assembly name |
| `Completeness` | double | Estimated genome completeness (%) |
| `Contamination` | double | Estimated contamination (%) |
| `Completeness_Model_Used` | string | ML model used for completeness prediction |
| `Translation_Table_Used` | string | Genetic code translation table |
| `Coding_Density` | double | Fraction of genome that is coding |
| `Contig_N50` | long | N50 contig length |
| `Average_Gene_Length` | double | Mean gene length in bp |
| `Genome_Size` | long | Total assembly size in bp |
| `GC_Content` | double | GC content fraction |
| `Total_Coding_Sequences` | long | Number of predicted CDS |
| `Total_Contigs` | long | Number of contigs |
| `Max_Contig_Length` | long | Length of longest contig |
| `cts_job_id` | string | CTS job ID (for linking results to jobs) |

## Example Workflow

1. **Find genomes** using `/berdl`:
   ```sql
   SELECT genome_id FROM kbase_ke_pangenome.genome
   WHERE species_id = 's__Escherichia_coli--RS_GCF_000005845.2'
   ```

2. **Locate assembly files** in S3 (JupyterHub):
   ```python
   mincli = get_minio_client()
   files = list(mincli.list_objects("cts", prefix="io/assemblies/", recursive=True))
   input_paths = [f"cts/{obj.object_name}" for obj in files if obj.object_name.endswith(".fna.gz")]
   ```

3. **Submit CheckM2 job** using the template above

4. **Query results** after completion:
   ```python
   spark.sql("""
       SELECT Name, Completeness, Contamination
       FROM u_myuser__autoimport.checkm2
       WHERE cts_job_id = 'the_job_id'
       ORDER BY Completeness DESC
   """).show()
   ```
