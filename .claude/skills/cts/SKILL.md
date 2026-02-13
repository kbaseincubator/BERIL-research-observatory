---
name: cts
description: Submit and manage compute jobs on the KBase CTS (CDM Task Service). Use when the user needs to run compute-intensive bioinformatics tools (DIAMOND, CheckM2, etc.) on data from the lakehouse, or wants to check on running jobs.
allowed-tools: Bash, Read
user-invocable: true
---

# CTS (CDM Task Service) Skill

Submit, monitor, and retrieve results from batch compute jobs on the KBase CDM Task Service.

## Overview

CTS runs containerized bioinformatics tools on remote compute clusters (HTCondor on KBase, JAWS on NERSC). It handles data staging (S3 <-> compute), multi-container parallelism, and job lifecycle management via a REST API.

**When to use CTS vs JupyterHub**:
- **JupyterHub**: Interactive analysis, Spark SQL queries, exploratory work (minutes)
- **CTS**: Batch compute with containerized tools, multi-file parallelism, long-running jobs (minutes to hours)

## Available Tools

| Tool | Module | Description |
|------|--------|-------------|
| CheckM2 | [checkm2.md](modules/checkm2.md) | Genome quality assessment |
| Custom | [custom.md](modules/custom.md) | Template for any containerized tool |

**Read the appropriate module** for tool-specific job templates and parameters.

## Current Status

CTS is a **prototype service**. Current limitations:
- **Only `kbase` cluster** is active (NERSC connections blocked by ANL networking issue)
- **`kbase` cluster requires KBase staff role** — check with `tscli.whoami()` (Python) or ask a CTS admin to grant access
- **Only CheckM2** (`ghcr.io/kbasetest/cdm_checkm2:0.3.0`) is currently approved as an image
- New images require admin approval (see Container Requirements below)

## Two Interfaces

CTS can be used via two interfaces:

1. **REST API (curl)** -- usable from local machine or Claude. All endpoints documented below with curl examples.
2. **Python client (JupyterHub)** -- `get_task_service_client()` available in JupyterHub kernels. More convenient for notebook workflows. See Python Client Reference below.

## Authentication

All API requests require the token from `.env`:

```bash
AUTH_TOKEN=$(grep "KBASE_AUTH_TOKEN" .env | cut -d'"' -f2)
```

Note: The token variable in `.env` is `KBASE_AUTH_TOKEN` (not `KB_AUTH_TOKEN`).

## API Endpoints

**Base URL**: `https://berdl.kbase.us/apis/cts`

### Service Info
```bash
curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/
```

### List Approved Images
```bash
curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/images
```
Check what tools are available before building a job.

### List Compute Sites
```bash
curl -s https://berdl.kbase.us/apis/cts/sites
```
Returns available compute clusters and their resource specs. No auth required.

### Submit a Job
```bash
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d @job.json \
  https://berdl.kbase.us/apis/cts/jobs
```
See Job Spec Reference below for the JSON format.

### Check Job Status (lightweight)
```bash
curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/jobs/{job_id}/status
```

### Get Full Job Details
```bash
curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/jobs/{job_id}
```
Includes output file list after completion.

### List Jobs
```bash
curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  "https://berdl.kbase.us/apis/cts/jobs"
```
Returns the user's jobs. Filterable by state, cluster, date.

### View Container Logs
```bash
# stdout for container N (0-indexed)
curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/jobs/{job_id}/log/{n}/stdout

# stderr for container N
curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/jobs/{job_id}/log/{n}/stderr
```

### Cancel a Job
```bash
curl -s -X PUT \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/jobs/{job_id}/cancel
```

## Python Client Reference (JupyterHub only)

The Python client is available in JupyterHub kernels via a helper function:

```python
tscli = get_task_service_client()

# Discovery (print results directly to inspect structure)
tscli.get_images()          # List approved images
tscli.get_sites()           # Available clusters
tscli.whoami()              # User info, roles, and allowed S3 paths

# Job submission
tscli.submit_job(...)       # Submit a job (returns Job object)
tscli.insert_files()        # Auto-split input files across containers

# Job management
tscli.list_jobs()           # List user's jobs
job = tscli.get_job_by_id("job_id_here")

# Job monitoring
job.get_job_status()        # Lightweight status check
job.get_job()               # Full details including outputs
job.get_exit_codes()        # Per-container exit codes
job.print_logs(container_num=0, stderr=True)  # View logs
job.wait_for_completion(wait_for_event_importer=True)  # Block until done
job.cancel()                # Cancel job
```

## Job Lifecycle

Jobs progress through these states:

```
created --> download_submitted --> job_submitting --> job_submitted
  --> upload_submitting --> upload_submitted --> complete
                                                    OR --> error

(cancel at any point --> canceling --> canceled)
```

- `created`: Job accepted, waiting for data staging
- `download_submitted`: Input files being staged to compute cluster
- `job_submitting` / `job_submitted`: Containers submitted/running on cluster
- `upload_submitting` / `upload_submitted`: Output files being uploaded to S3
- `complete`: All outputs available
- `error`: One or more containers failed (check exit codes and logs)

## Job Spec Reference

Annotated JSON for `POST /jobs`:

```json
{
  "cluster": "kbase",
  "image": "ghcr.io/kbasetest/cdm_checkm2:0.3.0",
  "params": {
    "args": [
      "--threads_per_container", "8",
      {"type": "input_files", "input_files_format": "space_separated_list"},
      "-x", "fna.gz",
      "-o", "/output_files"
    ],
    "input_mount_point": "/input_files",
    "output_mount_point": "/output_files",
    "declobber": true
  },
  "input_files": [
    "cts/io/user/data/genome1.fna.gz",
    "cts/io/user/data/genome2.fna.gz"
  ],
  "output_dir": "cts/io/user/output/run_name",
  "num_containers": 2,
  "cpus": 8,
  "memory": "10GB",
  "runtime": 3600
}
```

### Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `cluster` | Yes | Compute cluster. Currently only `"kbase"` is active. **Requires KBase staff role** (check `whoami()` or ask admin) |
| `image` | Yes | Docker image (must be pre-approved, check `GET /images`) |
| `params.args` | Yes | Array of strings and special objects. `{"type": "input_files", "input_files_format": "space_separated_list"}` is replaced with the actual input file paths at runtime |
| `params.input_mount_point` | No | Default `/input_files`. Where input files are mounted in the container |
| `params.output_mount_point` | No | Default `/output_files`. Where the container must write output |
| `params.declobber` | No | Set `true` for multi-container jobs. Prepends container number to output paths to prevent overwrites |
| `input_files` | Yes | Array of S3 paths (bucket/path format, e.g., `"cts/io/user/data/file.fna.gz"`) |
| `output_dir` | Yes | S3 output path (e.g., `"cts/io/user/output/run_name"`) |
| `num_containers` | No | 1-1000. Splits input files across containers for parallelism |
| `cpus` | No | CPUs per container |
| `memory` | No | Memory per container (e.g., `"10GB"`) |
| `runtime` | No | Max runtime in seconds per container |

## Data Staging

BERDL stores data in Delta tables (Spark SQL), but CTS needs S3 file paths. This is the critical workflow gap.

### Workflow

1. **Find data**: Use `/berdl` or Spark SQL to identify relevant genomes/sequences
2. **Locate or export files**:
   - Some files already exist in S3 (e.g., genome assemblies under `cts/io/` paths)
   - Use `get_minio_client()` on JupyterHub to list available files:
     ```python
     mincli = get_minio_client()
     objects = list(mincli.list_objects("cts", prefix="io/path/", recursive=True))
     for obj in objects:
         print(obj.object_name)
     ```
   - If files don't exist in S3, export from Spark and upload with checksums:
     ```bash
     mc cp --checksum crc64nvme file.fasta cts/io/user/input/
     ```
3. **Build input file list**: Collect S3 paths as strings for the job spec's `input_files` array
4. **Submit job**: Via curl or Python client

### S3 Requirements

- Input files must be in the `cts` S3 bucket
- Files must have **CRC64NVME checksums** (upload with `mc cp --checksum crc64nvme`)
- Files without checksums will be rejected

## Results Retrieval

Two paths to access results after job completion:

### S3 Output Files
Listed in the job details after completion (via `GET /jobs/{id}` or `job.get_job()`). These are raw tool outputs (TSV, CSV, etc.) stored at the `output_dir` path.

### Auto-Imported Delta Tables
Some tools have importers that automatically load results into user-specific Delta tables:

- **Table naming**: `u_{username}__autoimport.{tool}` (e.g., `u_gaprice__autoimport.checkm2`)
- **Queryable via Spark SQL**: `spark.sql("SELECT * FROM u_gaprice__autoimport.checkm2")`
- **Job tracking**: Results include a `cts_job_id` column to link back to the originating job

Currently, only **CheckM2** has an auto-importer configured. See [checkm2.md](modules/checkm2.md) for column details.

To wait for auto-import to complete (Python client):
```python
job.wait_for_completion(wait_for_event_importer=True)
```

## Container Requirements

For requesting new image approvals:

- Must be a **public** container image
- Must run as **non-root**
- Must include `/bin/bash`
- Must have an **entrypoint**
- Must write output **only** to the output mount point
- No hardlinks between input/output directories
- Contact admin for image approval (see [CTS admin docs](https://github.com/kbase/cdm-task-service/blob/main/docs/admin_image_setup.md))

## Instructions for Claude

1. **Read auth token** from `.env`
2. **List available images** (`GET /images`) -- show user what tools are available
3. If user's tool isn't available, explain the image approval process and container requirements
4. **Read the appropriate tool module** for job templates (e.g., [checkm2.md](modules/checkm2.md))
5. Help user **identify input data** (use `/berdl` for data discovery if needed)
6. Help user **stage data to S3** if necessary (document JupyterHub steps using `get_minio_client()`)
7. **Build job JSON**, validate all fields against the spec
8. **Submit job** and **prominently display the job ID** -- the user needs this to check status later
9. **Check status** when user asks -- use lightweight `GET /jobs/{id}/status` endpoint
10. On completion, show **output file list** and **auto-imported table name** if applicable
11. Help user **access and interpret results** (download from S3 or query auto-imported table)

## Error Handling

| Error | Meaning | Solution |
|-------|---------|----------|
| Job state `error` | Container failed | Check exit codes and stderr logs |
| Non-zero exit code | Tool-specific failure | Read stderr: `GET /jobs/{id}/log/{n}/stderr` |
| `"At least one container exited with a non-zero error code"` | One or more containers failed | Check each container's exit code and logs individually |
| Auth error (invalid token) | Invalid/expired token | Refresh `KBASE_AUTH_TOKEN` in `.env` |
| `"you must be a KBase staff member"` | Account lacks required role for cluster | Ask CTS admin to grant staff role |
| Image not found | Image not approved | Run `GET /images` to see approved images |
| S3 file rejected | Missing CRC64NVME checksum | Re-upload with `mc cp --checksum crc64nvme` |

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.
