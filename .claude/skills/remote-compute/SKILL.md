---
name: remote-compute
description: Run arbitrary scripts on KBase compute nodes via the CDM Task Service (CTS). Use when the user needs to move compute off their notebook or local machine — e.g., running bioinformatics tools, heavy data processing, or anything that benefits from dedicated CPU/memory on a remote node.
allowed-tools: Bash, Read
user-invocable: true
---

# Remote Compute Skill

Run arbitrary bash scripts on KBase compute nodes via the CDM Task Service (CTS).

## Overview

CTS runs containerized jobs on remote compute clusters. The `cts_ubuntu_test` image provides a generic Ubuntu environment where your script can install packages (pip, apt), run tools, and process data — effectively a remote shell with dedicated resources.

**When to use remote-compute vs JupyterHub**:
- **JupyterHub**: Interactive analysis, Spark SQL queries, exploratory work
- **Remote compute**: Batch processing, CPU/memory-intensive tasks, long-running jobs, anything that would block your notebook

## The Script Pattern

The core workflow is:

1. **Write a bash script** that does your analysis
2. **Upload it + input data** to MinIO (S3-compatible storage) with CRC64NVME checksums
3. **Submit the job** — the script runs in a container on a compute node
4. **Retrieve results** from MinIO

The generic ubuntu image (`ghcr.io/kbasetest/cts_ubuntu_test:0.1.0`) runs your script as the entrypoint, so the script can do anything: install Python packages, download references, run pipelines, etc.

## Preconditions

1. `KBASE_AUTH_TOKEN` set in environment or `.env`
2. **MinIO client (`mc`) installed** — see berdl-minio skill for installation
3. **Proxy running** (when off-cluster) — MinIO is not directly reachable from external networks. See the berdl-query skill's `references/proxy-setup.md`. The CTS API itself (`https://berdl.kbase.us/apis/cts`) does NOT require a proxy, only MinIO data staging does.
4. **CTS access** — requires KBase staff role. Verify with `tscli.whoami()` (JupyterHub) or the whoami curl below.

## Two Interfaces

### REST API (curl) — from local machine or Claude

All endpoints at `https://berdl.kbase.us/apis/cts`. Auth via Bearer token:

```bash
AUTH_TOKEN=$(grep "KBASE_AUTH_TOKEN" .env | cut -d'"' -f2)
```

### Python client — JupyterHub only

```python
cts = get_task_service_client()
minio = get_minio_client()
```

The Python client is more convenient for notebook workflows.

## Complete Workflow

### Step 1: Write your script

```bash
#!/bin/bash
# my-analysis.sh — runs on the compute node

# Install dependencies if needed
pip install biopython pandas

# $1 = output directory
# $2... = input files
OUTPUT_DIR="$1"
shift

# Process each input file
for FILE in "$@"; do
    BASENAME=$(basename "$FILE")
    # Your analysis here...
    python3 -c "
import Bio.SeqIO
records = list(Bio.SeqIO.parse('$FILE', 'fasta'))
print(f'{len(records)} sequences in $BASENAME')
" > "${OUTPUT_DIR}/${BASENAME}.result.txt"
done
```

### Step 2: Upload script and data to MinIO

All input files **must have CRC64NVME checksums** or the CTS will reject the job.

```bash
# Ensure proxy is set for MinIO access
export https_proxy=http://127.0.0.1:8123
export no_proxy=localhost,127.0.0.1

# Upload script
mc cp --checksum crc64nvme my-analysis.sh berdl-minio/cts/io/<username>/scripts/

# Upload input data
mc cp --checksum crc64nvme input_data/*.fna.gz berdl-minio/cts/io/<username>/input/
```

### Step 3: Submit the job

#### Python client (JupyterHub)

```python
cts = get_task_service_client()

job = cts.submit_job(
    "ghcr.io/kbasetest/cts_ubuntu_test:0.1.0",
    [
        "cts/io/<username>/scripts/my-analysis.sh",
        "cts/io/<username>/input/genome1.fna.gz",
        "cts/io/<username>/input/genome2.fna.gz",
    ],
    "cts/io/<username>/output/run_name",
    cluster="kbase",
    input_mount_point="/in",
    output_mount_point="/out",
    args=[
        "/in/my-analysis.sh",    # script to execute
        "/out/",                  # 1st arg: output directory
        cts.insert_files(),       # remaining input files injected here
    ],
    num_containers=1,
    cpus=4,
    memory="8GB",
    runtime="PT30M"
)

print(f"Job ID: {job.id}")
```

#### REST API (curl)

```bash
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cluster": "kbase",
    "image": "ghcr.io/kbasetest/cts_ubuntu_test:0.1.0",
    "params": {
      "args": [
        "/in/my-analysis.sh",
        "/out/",
        {"type": "input_files", "input_files_format": "space_separated_list"}
      ],
      "input_mount_point": "/in",
      "output_mount_point": "/out"
    },
    "input_files": [
      "cts/io/<username>/scripts/my-analysis.sh",
      "cts/io/<username>/input/genome1.fna.gz",
      "cts/io/<username>/input/genome2.fna.gz"
    ],
    "output_dir": "cts/io/<username>/output/run_name",
    "num_containers": 1,
    "cpus": 4,
    "memory": "8GB",
    "runtime": "PT30M"
  }' \
  https://berdl.kbase.us/apis/cts/jobs
```

### Step 4: Monitor the job

```python
# Python
job.get_job_status()          # Lightweight status check
job.wait_for_completion()     # Block until done
job.get_exit_codes()          # Per-container exit codes
job.print_logs(container_num=0, stderr=True)  # View logs
```

```bash
# curl
curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/jobs/{job_id}/status

# Logs
curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/jobs/{job_id}/log/0/stdout
curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/jobs/{job_id}/log/0/stderr
```

### Step 5: Retrieve results

```bash
# List outputs
mc ls berdl-minio/cts/io/<username>/output/run_name/

# Download results
mc cp --recursive berdl-minio/cts/io/<username>/output/run_name/ ./results/
```

```python
# Python (JupyterHub)
minio = get_minio_client()
objects = list(minio.list_objects("cts", prefix="io/<username>/output/run_name/", recursive=True))
for obj in objects:
    print(obj.object_name)

# Read a result file
response = minio.get_object("cts", "io/<username>/output/run_name/output.txt")
print(response.read().decode("utf-8"))
response.close()
response.release_conn()
```

## Key Concepts

### The `insert_files()` placeholder

In the Python client, `cts.insert_files()` is a special marker in the `args` list. At runtime, CTS replaces it with the paths of all input files assigned to that container (excluding the script itself if you position it before the placeholder). In the REST API, use:

```json
{"type": "input_files", "input_files_format": "space_separated_list"}
```

### Script is an input file

Your bash script is listed in `input_files` AND referenced in `args`. CTS stages it to the compute node alongside your data files, then the container executes it.

### CRC64NVME checksums

Every file uploaded to MinIO for CTS must have a CRC64NVME checksum. Always use `mc cp --checksum crc64nvme` when uploading. Files without checksums will be rejected at job submission.

### Multi-container parallelism

Set `num_containers > 1` to split input files across multiple containers. CTS distributes files evenly. Each container gets a subset of the files via `insert_files()`. Use `declobber: true` in params to prevent output filename collisions:

```python
job = cts.submit_job(
    "ghcr.io/kbasetest/cts_ubuntu_test:0.1.0",
    input_files,
    output_dir,
    cluster="kbase",
    input_mount_point="/in",
    output_mount_point="/out",
    args=["/in/my-script.sh", "/out/", cts.insert_files()],
    num_containers=10,
    cpus=2,
    memory="4GB",
    runtime="PT1H",
    declobber=True,
)
```

### Runtime format

Use ISO 8601 duration strings: `"PT5M"` (5 minutes), `"PT1H"` (1 hour), `"PT2H30M"` (2.5 hours).

## API Reference

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/` | GET | Yes | Service info |
| `/images` | GET | Yes | List approved container images |
| `/sites` | GET | No | Available compute clusters |
| `/jobs` | POST | Yes | Submit a job |
| `/jobs` | GET | Yes | List your jobs |
| `/jobs/{id}` | GET | Yes | Full job details (includes output files) |
| `/jobs/{id}/status` | GET | Yes | Lightweight status check |
| `/jobs/{id}/log/{n}/stdout` | GET | Yes | Container N stdout |
| `/jobs/{id}/log/{n}/stderr` | GET | Yes | Container N stderr |
| `/jobs/{id}/cancel` | PUT | Yes | Cancel a running job |

Base URL: `https://berdl.kbase.us/apis/cts`

## Job Lifecycle

```
created → download_submitted → job_submitting → job_submitted
    → upload_submitting → upload_submitted → complete
                                                OR → error
(cancel at any point → canceling → canceled)
```

## Error Handling

| Error | Meaning | Solution |
|-------|---------|----------|
| Job state `error` | Container failed | Check exit codes and stderr logs |
| Non-zero exit code | Script or tool failure | Read stderr: `GET /jobs/{id}/log/0/stderr` |
| Auth error | Invalid/expired token | Refresh `KBASE_AUTH_TOKEN` in `.env` |
| `"you must be a KBase staff member"` | Missing role for cluster | Ask CTS admin to grant staff role |
| Image not found | Image not approved | Run `GET /images` to see approved images |
| S3 file rejected | Missing CRC64NVME checksum | Re-upload with `mc cp --checksum crc64nvme` |
| `"Connect call failed"` on MinIO | Proxy not running | Start SSH tunnels + pproxy (see berdl-query proxy-setup) |

## Instructions for Claude

1. **Read auth token** from `.env` (`KBASE_AUTH_TOKEN`)
2. Help user **write their analysis script** — keep it self-contained, install deps at the top if needed
3. Help user **upload script and data** to MinIO with checksums (use berdl-minio skill for credentials if needed)
4. **Build and submit the job** — use the ubuntu image and script pattern above
5. **Prominently display the job ID** — the user needs this to check status later
6. **Monitor status** when asked — use lightweight status endpoint
7. On completion, help **retrieve and interpret results**
8. On error, check **exit codes and stderr logs** to diagnose

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.
