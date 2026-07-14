# Skani (GTDB) — ANI search against GTDB reference

**What it does**: Searches your query genomes against the pre-built GTDB skani sketch database to find the closest reference genomes by ANI. Faster for taxonomy-by-ANI than running full GTDB-Tk. Input: nucleotide assembly FASTA files.

**Entrypoint**: `skani` (same binary as the generic skani image)

**Refdata**: Yes — GTDB release232 skani sketch database mounted at `/ref_data/release232/skani/database/`. **You must pass the database path explicitly in args** — it is not hardcoded in the image so that future GTDB releases only require a new refdata bundle, not a new image build.

```python
tscli = get_task_service_client()

job = tscli.submit_job(
    "ghcr.io/kbaseincubator/cdm_skani_gtdb:0.1.0",
    input_files,                          # query nucleotide assembly FASTA files
    "cts/io/<username>/output/skani_gtdb_run",
    cluster="kbase",
    input_mount_point="/in",              # CTS stages your query genomes here
    output_mount_point="/out",            # skani writes the hits TSV here
    # refdata_mount_point is NOT needed: the image default /ref_data is used automatically
    args=[
        "search",                         # subcommand: search queries against a pre-built database
        "-d", "/ref_data/release232/skani/database/",  # GTDB release232 skani sketch database;
                                                         # path is inside the refdata mount point
        "-o", "/out/hits.tsv",            # output: TSV with ANI, aligned fraction, and closest reference
        "-t", "4",                        # number of threads; match cpus below
        "-n", "10",                       # number of top hits to report per query genome
        "--short-header",                 # omit the full GTDB taxonomy string in column headers
                                          # (cleaner output for downstream parsing)
        "--min-af", "15",                 # minimum aligned fraction (%) to report a hit;
                                          # lower for very distant queries
        tscli.insert_files(),             # query genome paths injected by CTS at runtime
    ],
    num_containers=2,     # query genomes can be split across containers for parallelism;
                          # each container independently searches its genomes against the database
    cpus=4,               # match -t above
    memory="16GB",        # the GTDB sketch database is pre-built and compact; 16GB is sufficient
    runtime="PT30M",      # fast; scale with number of query genomes
    declobber=True,       # prevent containers from overwriting each other's hits.tsv
)

print(f"Job ID: {job.id}")
```

**Typical resource guidance**:
- `cpus`: 4
- `memory`: 16 GB
- `num_containers`: scale with number of query genomes
- `runtime`: fast; scale with input count
