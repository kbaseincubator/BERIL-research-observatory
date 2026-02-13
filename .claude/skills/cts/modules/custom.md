# Custom Tool Template

Guide for running any containerized bioinformatics tool on CTS. Use this template when a new image has been approved and there is no dedicated module file for it yet.

## Container Requirements Checklist

Before requesting image approval, verify the container meets these requirements:

- [ ] **Public image** — must be pullable without credentials
- [ ] **Non-root** — container must not run as root
- [ ] **Includes `/bin/bash`** — required by CTS for job setup
- [ ] **Has an entrypoint** — CTS invokes the container via its entrypoint
- [ ] **Writes output only to the output mount point** — no writing outside the designated output directory
- [ ] **No hardlinks** between input and output directories

To request image approval, contact the CTS admin. See the [admin image setup docs](https://github.com/kbase/cdm-task-service/blob/main/docs/admin_image_setup.md) for full details.

## Generic Job Template (curl)

```json
{
  "cluster": "kbase",
  "image": "REGISTRY/ORG/IMAGE:TAG",
  "params": {
    "args": [
      "--flag", "value",
      {"type": "input_files", "input_files_format": "space_separated_list"},
      "-o", "/output_files"
    ],
    "input_mount_point": "/input_files",
    "output_mount_point": "/output_files",
    "declobber": true
  },
  "input_files": [
    "cts/io/username/input/file1.ext",
    "cts/io/username/input/file2.ext"
  ],
  "output_dir": "cts/io/username/output/run_name",
  "num_containers": 1,
  "cpus": 4,
  "memory": "8GB",
  "runtime": 3600
}
```

### Field-by-field guide

**`cluster`**: Currently only `"kbase"` is active. NERSC clusters (`perlmutter`, `lawrencium`) are blocked by ANL networking.

**`image`**: The full Docker image reference. Must be pre-approved -- run `GET /images` to check. Example: `"ghcr.io/kbasetest/cdm_checkm2:0.3.0"`.

**`params.args`**: Array of strings and special objects passed to the container entrypoint. The special object `{"type": "input_files", "input_files_format": "space_separated_list"}` is replaced at runtime with the actual input file paths assigned to the container. Place it where the tool expects its input file arguments.

**`params.input_mount_point`**: Directory where input files are mounted inside the container. Default: `/input_files`. The tool must read inputs from this path.

**`params.output_mount_point`**: Directory where the container must write output. Default: `/output_files`. CTS uploads everything in this directory to S3 after the job completes.

**`params.declobber`**: Set `true` for multi-container jobs. Prepends the container number (e.g., `0/`, `1/`) to output file paths so containers don't overwrite each other's results.

**`input_files`**: Array of S3 paths in `bucket/key` format. All files must be in the `cts` bucket with CRC64NVME checksums.

**`output_dir`**: S3 destination for output files. Format: `cts/io/username/output/descriptive_name`.

**`num_containers`**: How many containers to run (1-1000). CTS splits `input_files` evenly across containers.

**`cpus`**: CPUs allocated per container.

**`memory`**: Memory per container (e.g., `"8GB"`, `"16GB"`).

**`runtime`**: Maximum runtime in seconds per container. Job is killed if exceeded.

## Generic Job Template (Python client — JupyterHub)

```python
tscli = get_task_service_client()

job = tscli.submit_job(
    cluster="kbase",
    image="REGISTRY/ORG/IMAGE:TAG",
    args=[
        "--flag", "value",
        {"type": "input_files", "input_files_format": "space_separated_list"},
        "-o", "/output_files"
    ],
    input_mount_point="/input_files",
    output_mount_point="/output_files",
    declobber=True,
    input_files=[
        "cts/io/username/input/file1.ext",
        "cts/io/username/input/file2.ext",
    ],
    output_dir="cts/io/username/output/run_name",
    num_containers=1,
    cpus=4,
    memory="8GB",
    runtime=3600,
)

print(f"Job ID: {job.job_id}")

# Monitor
job.wait_for_completion()
job.get_exit_codes()
job.print_logs(container_num=0, stderr=True)
```

## Single-File vs Multi-File per Container

### Single file per container
Each container gets exactly one input file. Set `num_containers` equal to the number of input files:

```json
{
  "input_files": ["cts/io/user/file1.fna", "cts/io/user/file2.fna", "cts/io/user/file3.fna"],
  "num_containers": 3
}
```

### Multiple files per container
Multiple input files are split across fewer containers. CTS distributes them evenly:

```json
{
  "input_files": ["cts/io/user/file1.fna", "cts/io/user/file2.fna", ..., "cts/io/user/file100.fna"],
  "num_containers": 10
}
```
Each container gets ~10 files. Use the `{"type": "input_files"}` placeholder in `args` to pass them to the tool.

## How `input_files` Placeholder Works

The special arg object:
```json
{"type": "input_files", "input_files_format": "space_separated_list"}
```

At runtime, CTS replaces this with the actual paths of input files assigned to that container. For example, if container 0 gets `file1.fna` and `file2.fna`, the args become:

```
["--flag", "value", "/input_files/file1.fna /input_files/file2.fna", "-o", "/output_files"]
```

The tool must accept a space-separated list of file paths at that position in its argument list.

## Declobber for Multi-Container Output

When `declobber: true`, each container's output is prefixed with its container number:

```
output_dir/
  0/quality_report.tsv    # Container 0's output
  1/quality_report.tsv    # Container 1's output
  2/quality_report.tsv    # Container 2's output
```

Without declobber, containers writing files with the same name would overwrite each other. Always use `declobber: true` when `num_containers > 1`.

## Requesting Image Approval

1. Verify the container meets all requirements in the checklist above
2. Test the container locally to confirm it works as expected
3. Contact the CTS admin with:
   - Full image reference (registry/org/image:tag)
   - Description of what the tool does
   - Example command line invocation
   - Expected input/output formats
4. See [CTS admin image setup documentation](https://github.com/kbase/cdm-task-service/blob/main/docs/admin_image_setup.md) for full details
