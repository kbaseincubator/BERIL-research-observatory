# KofamScan — KEGG Orthology annotation via HMM

**What it does**: Annotates protein sequences with KEGG Orthology (KO) identifiers by scanning against KEGG HMM profiles. Input: protein FASTA files (`.faa`). Output: tab-separated annotation file with KO assignments and scores.

**Entrypoint**: `exec_annotation`

**Refdata**: Yes — KEGG HMM profiles (`/ref_data/profiles`) and KO list (`/ref_data/ko_list`) mounted at `/ref_data`. **You must pass these paths explicitly in args** — unlike Bakta, KofamScan does not read them from an environment variable.

```python
tscli = get_task_service_client()

job = tscli.submit_job(
    "ghcr.io/kbaseincubator/cdm_kofamscan:0.1.0",
    input_files,                          # protein FASTA files (.faa)
    "cts/io/<username>/output/kofamscan_run",
    cluster="kbase",
    input_mount_point="/in",              # where CTS stages your input files inside the container
    output_mount_point="/out",            # exec_annotation writes results here
    args=[
        "-p", "/ref_data/profiles",       # path to KEGG HMM profiles inside the container;
                                          # /ref_data is the refdata mount point baked into the image
        "-k", "/ref_data/ko_list",        # path to the KEGG KO definition list inside the container
        "-o", "/out/kofamscan_results.tsv", # output file path; must be under the output_mount_point
        "--cpu", "8",                     # number of CPU threads; match cpus below
        tscli.insert_files(),             # input protein FASTA path(s) injected by CTS at runtime
    ],
    num_containers=2,     # each container independently annotates its share of input files
    cpus=8,               # match --cpu above
    memory="16GB",        # HMM profiles are large; 16GB is the recommended floor
    runtime="PT1H",       # ~30 min per proteome; scale with input count
    declobber=True,       # prevent containers from overwriting each other's output TSV
)

print(f"Job ID: {job.id}")
```

**Typical resource guidance**:
- `cpus`: 8 (matches `--cpu 8`)
- `memory`: 16–32 GB
- `num_containers`: 1 per input file for maximum parallelism
- `runtime`: 30–60 min per proteome
