# IQ-TREE 2 — Phylogenetic tree inference

**What it does**: Maximum-likelihood phylogenetic tree inference from multiple sequence alignments. Input: aligned FASTA or PHYLIP format alignment file. Output: `.treefile` (Newick), log, and model selection report.

**Entrypoint**: `iqtree2` (via `/usr/local/env-execute iqtree2`)

**Refdata**: No — operates entirely on your input alignment.

**Note on multiple jobs**: If you run multiple IQ-TREE jobs, ensure each writes to a distinct output prefix (`--prefix`) or output directory, otherwise containers may overwrite each other's files.

```python
tscli = get_task_service_client()

job = tscli.submit_job(
    "ghcr.io/kbaseincubator/cdm_iqtree:2.3.6-0.1.0",
    input_files,                          # one aligned FASTA or PHYLIP alignment file
    "cts/io/<username>/output/iqtree_run",
    cluster="kbase",
    input_mount_point="/in",              # CTS stages the alignment file here
    output_mount_point="/out",            # IQ-TREE writes all output files here
    args=[
        "-s", tscli.insert_files(),       # input alignment file path, injected by CTS;
                                          # IQ-TREE reads the alignment from this path
        "--prefix", "/out/tree",          # output prefix: IQ-TREE writes tree.treefile, tree.log, etc.
                                          # must be under output_mount_point so CTS can collect files
        "-m", "TEST",                     # substitution model: TEST=auto-select by ModelFinder (recommended);
                                          # or specify directly, e.g. GTR+G, WAG+I+G
        "-T", "8",                        # number of CPU threads; match cpus below;
                                          # use AUTO to let IQ-TREE pick (less predictable)
        "-B", "1000",                     # number of ultrafast bootstrap replicates (UFBoot);
                                          # set to 0 or omit to skip bootstrap
        "--redo",                         # overwrite any existing output files with the same prefix;
                                          # safe to include since CTS creates a fresh container each time
    ],
    num_containers=1,     # one alignment → one tree; IQ-TREE is not split across containers
    cpus=8,               # match -T above; IQ-TREE scales well with cores
    memory="32GB",        # depends on alignment size (taxa × columns); 32GB for typical phylogenomics
    runtime="PT4H",       # highly variable: minutes for small alignments, hours for thousands of taxa
)

print(f"Job ID: {job.id}")
```

**Typical resource guidance**:
- `cpus`: 8–32 (IQ-TREE scales well)
- `memory`: 16–128 GB depending on alignment dimensions
- `num_containers`: 1 per alignment
- `runtime`: minutes to hours; profile with a small test alignment first
