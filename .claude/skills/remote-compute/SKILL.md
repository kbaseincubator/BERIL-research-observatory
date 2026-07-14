---
name: remote-compute
description: Run arbitrary scripts on KBase compute nodes via the CDM Task Service (CTS). Use when the user needs to move compute off their notebook or local machine — e.g., running bioinformatics tools, heavy data processing, or anything that benefits from dedicated CPU/memory on a remote node.
allowed-tools: Bash, Read
user-invocable: true
---

# Remote Compute Skill

Run containerized jobs on KBase compute nodes via the CDM Task Service (CTS).

## Overview

CTS runs containerized jobs on remote compute clusters. Two execution paths are available:

| Path | When to use |
|------|-------------|
| **Pre-built tool image** | The tool you need is already in the registry (CheckM2, Bakta, GTDB-Tk, etc.) — just pass args |
| **Generic ubuntu script** | Tool not in registry, or you need custom logic — write a bash script, install deps at runtime |

**Always discover the live image registry first** before deciding which path to take:

```python
# JupyterHub
tscli = get_task_service_client()
tscli.get_images()        # returns list of registered images
```

```bash
# curl (any environment)
AUTH_TOKEN=$(grep "KBASE_AUTH_TOKEN" .env | cut -d'"' -f2)
curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/images | python3 -m json.tool
```

The registry grows over time — always check live rather than relying on any static list in this document.

**When to use remote compute vs JupyterHub**:
- **JupyterHub**: Interactive analysis, Spark SQL queries, exploratory work
- **Remote compute**: Batch processing, CPU/memory-intensive tools (CheckM2, Bakta, GTDB-Tk), long-running jobs, anything that would block your notebook

---

## Preconditions

1. `KBASE_AUTH_TOKEN` set in environment or `.env`
2. **MinIO client (`mc`) installed** — see berdl-minio skill for installation
3. **Proxy running** (when off-cluster) — MinIO is not directly reachable from external networks. See the berdl-query skill's `references/proxy-setup.md`. The CTS API itself (`https://berdl.kbase.us/apis/cts`) does NOT require a proxy — only MinIO data staging does.
4. **CTS access and your S3 paths** — run `whoami` before staging any files. It confirms your
   role and tells you the exact S3 path prefixes you are allowed to use for `input_files` and
   `output_dir`. Every example in this skill uses `cts/io/<username>/...` as a placeholder —
   `whoami` tells you what to substitute.

```python
# JupyterHub
tscli = get_task_service_client()
tscli.whoami()
# Returns, e.g.:
# {
#   "user": "mcashman",                       ← your username; use this in place of <username>
#   "roles": ["cts_user"],                    ← confirms CTS access; must include "cts_user" or "full_admin"
#   "allowed_paths": [
#     {"path": "cts/io/mcashman", "perm": "write"},   ← you can read and write here
#     {"path": "cts/io/mcashman", "perm": "read"}
#   ]
# }
# The "path" values are the S3 prefixes you use for input_files and output_dir.
# Example: input_files=["cts/io/mcashman/input/genome.fna.gz"]
#          output_dir="cts/io/mcashman/output/bakta_run"
```

```bash
# curl equivalent
curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/whoami | python3 -m json.tool
```

If `roles` is empty or does not include `cts_user` or `full_admin`, you do not have CTS access —
ask a CTS admin to grant the `cts_user` role.

---

## Two Interfaces

### Python client — JupyterHub only

```python
tscli = get_task_service_client()    # CTS client
minio = get_minio_client()           # MinIO client for file staging
```

### REST API (curl) — any environment

All endpoints at `https://berdl.kbase.us/apis/cts`. Auth via Bearer token:

```bash
AUTH_TOKEN=$(grep "KBASE_AUTH_TOKEN" .env | cut -d'"' -f2)
```

---

## Stage Input Files to MinIO

**This step is required for both Path A and Path B.** CTS does not read files from your local
machine or from the BERDL Lakehouse directly — all input files must be pre-uploaded to MinIO
before job submission. Every file must carry a CRC64NVME checksum or the submission will be
rejected.

### Find your MinIO path prefix

Run `tscli.whoami()` (see Preconditions) to find your `allowed_paths`. Your input and output
directories should be nested under the writable path — typically `cts/io/<username>/`.

### Upload with the MinIO CLI (`mc`)

```bash
# Off-cluster only: set proxy so mc can reach MinIO
export https_proxy=http://127.0.0.1:8123
export no_proxy=localhost,127.0.0.1

# Upload a single file with a CRC64NVME checksum
mc cp --checksum crc64nvme genome.fna.gz berdl-minio/cts/io/<username>/input/

# Upload a directory of files (e.g. all .fna.gz in a folder)
mc cp --checksum crc64nvme --recursive ./input_genomes/ berdl-minio/cts/io/<username>/input/

# Verify what was staged
mc ls berdl-minio/cts/io/<username>/input/
```

The `berdl-minio` alias must be configured. See the berdl-minio skill for setup instructions.

### Upload from Python (JupyterHub)

```python
minio = get_minio_client()
import os

local_file = "genome.fna.gz"
minio_path = f"io/<username>/input/{local_file}"  # path within the "cts" bucket

# Upload a file — the MinIO client handles checksums automatically on JupyterHub
minio.fput_object("cts", minio_path, local_file)
print(f"Staged: cts/{minio_path}")

# List staged files to confirm
for obj in minio.list_objects("cts", prefix="io/<username>/input/", recursive=True):
    print(obj.object_name, obj.size)
```

### Build your input_files list

After staging, construct the `input_files` list for `submit_job` from the staged paths:

```python
# Option 1: list them explicitly
input_files = [
    "cts/io/<username>/input/genome1.fna.gz",
    "cts/io/<username>/input/genome2.fna.gz",
]

# Option 2: discover from MinIO (useful for large batches)
minio = get_minio_client()
objs = list(minio.list_objects("cts", prefix="io/<username>/input/", recursive=True))
input_files = [f"cts/{o.object_name}" for o in objs]
print(f"{len(input_files)} files staged and ready")
```

---

## Path A: Pre-built Tool Images

Pre-built images have the tool already installed and set as the container entrypoint. You do not write a bash script — you pass arguments directly to the tool. Some images include large reference databases (refdata) that CTS mounts automatically.

### What is refdata?

Some tools require large reference databases (e.g., CheckM2's marker gene sets, GTDB-Tk's genome sketches, Bakta's annotation database). These are pre-staged by the CTS admins and mounted read-only into the container at a fixed path. The image registration records which refdata bundle it needs and where to mount it (`default_refdata_mount_point`).

**You do not pass a `refdata_id` to `submit_job`** — it is determined by the image. You only need to know the mount path so you can reference it in your `args` if needed (e.g., `--db /ref_data`). Most images bake the path into the tool config or environment variables so you do not need to reference it at all — see the per-tool notes below.

If you want to override the default mount point, pass `refdata_mount_point="/your/path"` inside the `params` via the Python client's `submit_job` call. This is rarely needed.

### General pattern — pre-built image

```python
tscli = get_task_service_client()

job = tscli.submit_job(
    "<image>:<tag>",          # full image name from the registry
    input_files,              # list of MinIO paths: ["cts/io/<user>/input/file1.fna.gz", ...]
    "cts/io/<user>/output/run_name",  # MinIO output directory (bucket/prefix)
    cluster="kbase",          # compute site — "kbase" for on-prem KBase hardware
    output_mount_point="/out", # path inside the container where the tool must write output;
                               # CTS copies everything under this path to S3 after the job finishes
    args=[...],               # arguments appended after the image entrypoint command
    num_containers=1,         # how many parallel containers to run (see per-tool guidance)
    cpus=4,                   # CPU cores per container
    memory="8GB",             # RAM per container
    runtime="PT30M",          # ISO 8601 duration: PT5M=5min, PT1H=1hour, PT2H30M=2.5hours
)

print(f"Job ID: {job.id}")    # save this — needed to check status or retrieve results later
```

---

### Available pre-built images

| Tool | Image name pattern | Refdata | One container per file? | Special notes |
|------|--------------------|---------|-------------------------|---------------|
| CheckM2 | `cdm_checkm2` | Yes (`/ref_data`) | No — batch | Auto-imports to Spark table; use `declobber=True` |
| MMseqs2 | `cdm_mmseqs2` | No | No — all-at-once for clustering | Subcommand is first arg |
| KofamScan | `cdm_kofamscan` | Yes (`/ref_data/profiles`, `/ref_data/ko_list`) | No — batch | Must pass profile/ko_list paths explicitly |
| PSORTb | `cdm_psortb` | No | **Yes** | `num_containers=len(input_files)` |
| Bakta | `cdm_bakta` | Yes (`/ref_data/db`) | **Yes** | `--force` REQUIRED; `BAKTA_DB` auto-set |
| Bakta proteins | `cdm_bakta_proteins` | Yes (`/ref_data/db`) | **Yes** | `--force` REQUIRED; `BAKTA_DB` auto-set |
| GTDB-Tk | `cdm_gtdbtk` | Yes (`/ref_data/release232`) | **No — always 1** | `memory="128GB"` minimum; `num_containers=1` always |
| Skani | `cdm_skani` | No | No | Subcommand is first arg |
| Skani GTDB | `cdm_skani_gtdb` | Yes (`/ref_data/release232/skani/database/`) | No — batch | Must pass `-d` path explicitly |
| IQ-TREE 2 | `cdm_iqtree` | No | No — 1 per alignment | `--prefix /out/tree`; `--redo` recommended |

**Full per-tool examples, resource guidance, and special notes are in individual reference files under `references/`.** Each tool has its own file named after the image pattern without the `cdm_` prefix:

| Tool | Reference file |
|------|---------------|
| CheckM2 | `references/checkm2.md` |
| MMseqs2 | `references/mmseqs2.md` |
| KofamScan | `references/kofamscan.md` |
| PSORTb | `references/psortb.md` |
| Bakta | `references/bakta.md` |
| Bakta proteins | `references/bakta_proteins.md` |
| GTDB-Tk | `references/gtdbtk.md` |
| Skani | `references/skani.md` |
| Skani GTDB | `references/skani_gtdb.md` |
| IQ-TREE 2 | `references/iqtree.md` |

Claude should `Read` only the specific tool's reference file after identifying the user's tool from `get_images()`.

---

## Path B: Generic Ubuntu Script

Use this path when your tool is not in the pre-built registry, or when you need custom logic that doesn't fit a single tool invocation. You write a bash script, upload it alongside your data, and the container executes it.

The generic image (`ghcr.io/kbasetest/cts_ubuntu_test:0.1.0`) is a minimal Ubuntu — **Python, pip, and other tools are NOT pre-installed**. Your script installs what it needs at runtime.

### Step 1: Write your script

```bash
#!/bin/bash
# my-analysis.sh — runs on the compute node

# Install dependencies at runtime (nothing is pre-installed)
apt-get update -qq && apt-get install -y -qq python3 python3-pip > /dev/null 2>&1
pip install biopython pandas --quiet

# The script receives arguments from the CTS job submission args list.
# A common convention: first arg is the output directory, remaining args are input files.
OUTPUT_DIR="$1"
shift   # remove $1 so "$@" now contains only the input files

# Process each input file
for FILE in "$@"; do
    BASENAME=$(basename "$FILE")
    python3 -c "
import Bio.SeqIO
records = list(Bio.SeqIO.parse('$FILE', 'fasta'))
print(f'{len(records)} sequences in $BASENAME')
" > "${OUTPUT_DIR}/${BASENAME}.result.txt"
done
```

### Step 2: Upload script and data to MinIO

Stage your input data using the instructions in **Stage Input Files to MinIO** above.
Your bash script must also be uploaded — it is treated as an input file by CTS and staged
alongside your data.

```bash
# Upload the script (same checksum requirement as data files)
mc cp --checksum crc64nvme my-analysis.sh berdl-minio/cts/io/<username>/scripts/

# Upload input data
mc cp --checksum crc64nvme input_data/*.fna.gz berdl-minio/cts/io/<username>/input/
```

### Step 3: Submit the job

#### Python client (JupyterHub)

```python
tscli = get_task_service_client()

job = tscli.submit_job(
    "ghcr.io/kbasetest/cts_ubuntu_test:0.1.0",  # generic ubuntu image
    [
        "cts/io/<username>/scripts/my-analysis.sh",  # the script is an input file
        "cts/io/<username>/input/genome1.fna.gz",
        "cts/io/<username>/input/genome2.fna.gz",
    ],
    "cts/io/<username>/output/run_name",
    cluster="kbase",
    input_mount_point="/in",              # all input files (script + data) are staged here
    output_mount_point="/out",            # script must write all output under this path
    args=[
        "/in/my-analysis.sh",             # the script to execute; CTS stages it at this path
        "/out/",                          # first argument to the script: the output directory
        tscli.insert_files(),             # remaining input files (excluding the script) injected here
    ],
    num_containers=1,
    cpus=4,
    memory="8GB",
    runtime="PT30M",
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

---

## Job Management and Results

### Step 1: Save the job ID immediately after submission

The job ID is the only handle you have on a submitted job. Save it before doing anything else.

```python
job = tscli.submit_job(...)

print(f"Job ID: {job.id}")

# Also write it to a file so you can recover it if the notebook closes
with open("projects/<id>/data/cts_job_id.txt", "a") as f:
    f.write(f"{job.id}\n")
```

---

### Step 2: Check job status

```python
# Lightweight check — returns the current state string without loading full job details
job.get_job_status()
# Returns one of:
#   created, download_submitted, job_submitting, job_submitted,
#   upload_submitting, upload_submitted, complete,
#   recovering, canceling, canceled,
#   error_processing_submitting, error_processing_submitted, error
```

```bash
# curl equivalent
curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/jobs/{job_id}/status
```

To block until the job finishes (useful in a notebook thread):

```python
import threading, json

# Run in a background thread so the notebook stays responsive
thread = threading.Thread(
    target=lambda: print(json.dumps(job.wait_for_completion(), indent=4)),
    daemon=True
)
thread.start()
# job.wait_for_completion() returns the full job dict when the job reaches a terminal state
```

**Spark auto-import** — some images (currently confirmed: CheckM2) have a registered event
importer on the CTS side. When the job finishes, this pipeline automatically reads the output
files from MinIO and loads them into a BERDL Iceberg table, tagged by `cts_job_id`. You can
then query results directly with Spark instead of downloading files manually.

Pass `wait_for_event_importer=True` to block until both the job *and* the import pipeline are done:

```python
thread = threading.Thread(
    target=lambda: print(json.dumps(
        job.wait_for_completion(wait_for_event_importer=True), indent=4
    )),
    daemon=True
)
thread.start()
# After this completes, results are in the BERDL table — no download needed:
# spark.sql(f"SELECT * FROM u_<username>__autoimport.checkm2 WHERE cts_job_id = '{job.id}'")
```

If the image does not have an importer, omit `wait_for_event_importer=True` and retrieve
results from MinIO manually (see Step 4 below).

---

### Step 3: Check exit codes on failure

When `get_job_status()` returns `"error"`, check exit codes first — it tells you which containers failed without pulling full logs.

```python
job.get_exit_codes()
# Returns e.g. {'exit_codes': [0, 2]}
# One entry per container: 0=success, non-zero=failure
# Use container index to target log reads below
```

```bash
curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/jobs/{job_id}/exit_codes
```

---

### Step 4: Read logs (especially on failure)

```python
# View stderr — most useful for diagnosing tool failures
job.print_logs(container_num=0, stderr=True)

# View stdout — tool progress output
job.print_logs(container_num=0, stderr=False)

# For multi-container jobs, increment container_num: 0, 1, 2, ...
job.print_logs(container_num=1, stderr=True)
```

```bash
# curl equivalents
curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/jobs/{job_id}/log/0/stderr

curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/jobs/{job_id}/log/0/stdout
```

---

### Step 5: Find output files after completion

The output location is the `output_dir` you passed to `submit_job`. After the job completes, the
full list of output files (with checksums) is available from the job object:

```python
job_details = job.get_job()

# List every output file and its checksum
for output in job_details["outputs"]:
    print(output["file"])        # full S3 path, e.g. cts/io/<username>/output/run/quality_report.tsv
    print(output["crc64nvme"])   # CRC64NVME checksum for integrity verification

# Resource usage stats (available after completion)
print(f"CPU hours used:   {job_details.get('cpu_hours')}")
print(f"Max memory used:  {job_details.get('max_memory')} bytes")
print(f"Output file count: {job_details.get('output_file_count')}")
```

Download all outputs to a local directory:

```bash
# The output_dir you specified in submit_job is the MinIO path to download from
mc cp --recursive berdl-minio/cts/io/<username>/output/run_name/ ./results/
```

```python
# Python (JupyterHub) — list and read outputs via MinIO client
minio = get_minio_client()

# List all objects under the output directory
objects = list(minio.list_objects("cts", prefix="io/<username>/output/run_name/", recursive=True))
for obj in objects:
    print(obj.object_name)

# Read a specific result file into memory without downloading
response = minio.get_object("cts", "io/<username>/output/run_name/quality_report.tsv")
print(response.read().decode("utf-8"))
response.close()
response.release_conn()
```

---

### Recovering a lost job ID

If your notebook closed or you lost the job ID, use `list_jobs()` to find it.
Results are sorted newest-first. Maximum 1000 jobs returned.

```python
tscli = get_task_service_client()

# List your 20 most recent jobs
result = tscli.list_jobs(limit=20)
for j in result["jobs"]:
    image = f"{j['image']['name']}:{j['image']['tag']}"
    submitted = j["transition_times"][0]["time"]   # time job was created
    print(f"{j['id']}  {j['state']:<30}  {image:<55}  {submitted}")
```

Filter by state to find jobs that are still running or recently failed:

```python
# Only running jobs
result = tscli.list_jobs(state="job_submitted")

# Only completed jobs
result = tscli.list_jobs(state="complete")

# Only failed jobs
result = tscli.list_jobs(state="error")

# Jobs updated after a specific date (ISO 8601)
result = tscli.list_jobs(after="2026-06-01T00:00:00Z")

# Jobs updated before a specific date
result = tscli.list_jobs(before="2026-05-01T00:00:00Z")

# Time window: completed jobs between two dates
result = tscli.list_jobs(state="complete", after="2026-05-01T00:00:00Z", before="2026-06-01T00:00:00Z")

# Combine filters: completed jobs on the kbase cluster since June 2026
result = tscli.list_jobs(cluster="kbase", state="complete", after="2026-06-01T00:00:00Z")
```

```bash
# curl equivalents
curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  "https://berdl.kbase.us/apis/cts/jobs?limit=20"

curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  "https://berdl.kbase.us/apis/cts/jobs?state=error&limit=20"

curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  "https://berdl.kbase.us/apis/cts/jobs?state=complete&after=2026-06-01T00:00:00Z"
```

Once you have the job ID, reconstruct the job object:

```python
job = tscli.get_job_by_id("paste-job-id-here")

# Then use it as normal
job.get_job_status()
job.get_job()["outputs"]
job.print_logs(container_num=0, stderr=True)
```

---

### Coordinating multiple jobs

This skill focuses on individual job submission, but common patterns when running a pipeline across tools:

```python
# Submit jobs for independent tools in parallel, collect IDs
bakta_job   = tscli.submit_job("cdm_bakta:...",   ...)
checkm2_job = tscli.submit_job("cdm_checkm2:...", ...)

# Save both IDs
job_ids = {"bakta": bakta_job.id, "checkm2": checkm2_job.id}

# Wait for each in sequence (or use threads for true parallel wait)
bakta_result   = bakta_job.wait_for_completion()
checkm2_result = checkm2_job.wait_for_completion(wait_for_event_importer=True)

# Feed bakta outputs into a downstream job
bakta_outputs = [o["file"] for o in bakta_result["outputs"]]
downstream_job = tscli.submit_job("cdm_kofamscan:...", bakta_outputs, ...)
```

Track all job IDs in a file so the chain survives notebook restarts.

---

### Canceling a job

```python
job.cancel()
job.get_job_status()   # confirm — should transition to "canceling" then "canceled"
```

```bash
curl -s -X PUT -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/jobs/{job_id}/cancel
```

---

## Key Concepts

### Job lifecycle

```
created → download_submitted → job_submitting → job_submitted
    → upload_submitting → upload_submitted → complete
                                                OR → error
(cancel at any point → canceling → canceled)
```

### `insert_files()` / input_files placeholder

In the Python client, `tscli.insert_files()` is a sentinel in the `args` list. At job runtime, CTS replaces it with the paths of the input files assigned to that container (space-separated). In the REST API, use:

```json
{"type": "input_files", "input_files_format": "space_separated_list"}
```

### Script is an input file (generic path only)

Your bash script is listed in `input_files` alongside your data. CTS stages it to the compute node at the `input_mount_point`, then the container executes it. Reference it in `args` using the staged path (e.g., `/in/my-analysis.sh`).

### CRC64NVME checksums

Every file uploaded to MinIO for CTS must carry a CRC64NVME checksum. Always use `mc cp --checksum crc64nvme` when uploading. Files without checksums are rejected at job submission time.

### Multi-container parallelism

Set `num_containers > 1` to split input files across containers. CTS distributes files evenly. Each container receives its share via `insert_files()`. Use `declobber=True` when multiple containers could write output files with the same name (e.g., CheckM2 always writes `quality_report.tsv`). With `declobber=True`, CTS prepends the container index as a directory to every output path:

```
# declobber=True output layout (two containers):
cts/io/<username>/output/checkm2_run/0/quality_report.tsv
cts/io/<username>/output/checkm2_run/1/quality_report.tsv
```

Without `declobber=True`, container 1 would overwrite container 0's file.

### Runtime format

ISO 8601 duration strings: `"PT5M"` (5 minutes), `"PT1H"` (1 hour), `"PT2H30M"` (2.5 hours), `"PT4H"` (4 hours). The format is case-sensitive — `"PT1H"` works, `"pt1h"` does not.

### Image tags vs digest pinning

Every example in this skill uses `image:tag` format (e.g. `cdm_bakta:0.1.3`). Tags are
human-readable but **mutable** — a tag can be re-pushed to point to a different image without
warning. For reproducible science, pin to the digest instead:

```
ghcr.io/kbaseincubator/cdm_bakta:0.1.3@sha256:ab3d636d9381fdd57a8b21e3a2403663987f57f123027fa7a773474e66d9a827
```

This format uses both the tag (for readability) and the digest (for pinning). The container
runtime uses the digest to pull the exact image regardless of what the tag currently points to.

Get the current digest for any image from the live registry:

```python
images = tscli.get_images()
for img in images["data"]:
    if "bakta" in img["name"]:
        print(f"{img['name']}:{img['tag']}@{img['digest']}")
        # Use this full string as the image argument in submit_job
```

```bash
curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/images | python3 -c "
import sys, json
for img in json.load(sys.stdin)['data']:
    tag = img.get('tag', 'none')
    print(f\"{img['name']}:{tag}@{img['digest']}\")
"
```

Always retrieve the digest fresh from `get_images()` — do not rely on digests hardcoded in
notebooks or this skill, as they become stale when images are updated.

### Refdata and mount points

`refdata_id` identifies which pre-staged reference database bundle the image needs. It is registered with the image — you do not pass it to `submit_job`. CTS mounts the refdata read-only into the container at the `default_refdata_mount_point` specified in the image registration (always `/ref_data` for current BERDL images). To override the mount path, pass `refdata_mount_point="/your/path"` to `submit_job`. This is rarely needed since all current images use `/ref_data` as their default.

To verify a refdata bundle is registered and ready before submitting:

```python
tscli.get_images()   # the refdata_id and default_refdata_mount_point are in each image's metadata
```

```bash
# List all registered refdata bundles
curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
  https://berdl.kbase.us/apis/cts/refdata | python3 -m json.tool
```

### GPU support

GPU compute is not currently available on the kbase cluster. Do not pass GPU-related parameters — the `submit_job` call will succeed but no GPU will be allocated.

---

## API Reference

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/` | GET | Yes | Service info |
| `/whoami` | GET | Yes | Your username, roles, and allowed S3 paths |
| `/images` | GET | Yes | List approved container images (call this first) |
| `/refdata` | GET | Yes | List registered reference data bundles |
| `/sites` | GET | No | Available compute clusters |
| `/jobs` | POST | Yes | Submit a job |
| `/jobs` | GET | Yes | List your jobs (`state`, `after`, `before`, `cluster`, `limit`) |
| `/jobs/{id}` | GET | Yes | Full job details (includes output files list) |
| `/jobs/{id}/status` | GET | Yes | Lightweight status check |
| `/jobs/{id}/exit_codes` | GET | Yes | Exit code per container (first check on error) |
| `/jobs/{id}/log/{n}/stdout` | GET | Yes | Container N stdout |
| `/jobs/{id}/log/{n}/stderr` | GET | Yes | Container N stderr |
| `/jobs/{id}/cancel` | PUT | Yes | Cancel a running job |

Base URL: `https://berdl.kbase.us/apis/cts`

---

## Error Handling

| Error | Meaning | Fix |
|-------|---------|-----|
| Job state `error` | Container failed | Check exit codes and stderr logs |
| Non-zero exit code | Script or tool failure | Read stderr: `GET /jobs/{id}/log/0/stderr` |
| Auth error (401) | Invalid or expired token | Refresh `KBASE_AUTH_TOKEN` in `.env` |
| `"you must be a KBase staff member"` | Missing role for cluster | Ask CTS admin to grant staff role |
| Image not found / not approved | Image not in registry | Run `GET /images` to see approved images |
| S3 file rejected | Missing CRC64NVME checksum | Re-upload with `mc cp --checksum crc64nvme` |
| `"Connect call failed"` on MinIO | Proxy not running | Start SSH tunnels + pproxy (see berdl-query proxy-setup) |
| OOM / container killed | Insufficient memory | Increase `memory` in `submit_job` |
| Job stuck in `download_submitted` | Refdata staging in progress | Wait — large refdata bundles (GTDB-Tk, Bakta) take time to stage on first use |
| `bakta: error: directory ... already exists` | Missing `--force` flag | Add `"--force"` to your `args` list |

---

## Instructions for Claude

1. **Run `whoami` and `get_images` before anything else** — call `tscli.whoami()` to confirm CTS access and resolve the user's actual S3 path prefix (substituting it everywhere `<username>` appears in examples). Call `tscli.get_images()` to see currently registered images and retrieve their current digests. Do not rely on any static list in this skill.
2. **Determine the execution path** — if the user's tool is in the registry, use Path A (pre-built image). If not, use Path B (generic ubuntu script).
3. **Always use digest-pinned image references** — from the `get_images()` response, use `name:tag@sha256:digest` format in every `submit_job` call (e.g. `ghcr.io/kbaseincubator/cdm_bakta:0.1.3@sha256:ab3d...`). Tell the user which tag and digest you are using. Never hardcode a digest from memory or this skill — always fetch it live.
4. **Ensure input files are staged before submitting** — for both Path A and Path B, walk the user through uploading their input files to MinIO with `mc cp --checksum crc64nvme` (or the Python MinIO client on JupyterHub). Confirm files are staged before building the `submit_job` call. Build the `input_files` list from the staged MinIO paths.
5. **For pre-built images** — `Read` the tool's reference file at `.claude/skills/remote-compute/references/<toolname>.md` (e.g. `references/gtdbtk.md`, `references/bakta.md`). The filename matches the image name pattern without the `cdm_` prefix — the lookup table is in the "Available pre-built images" section above. Use the reference file as the starting template. Fill in the user's actual MinIO paths for `input_files` and `output_dir`. Help the user determine `num_containers` and resource parameters based on their input count and the per-tool guidance in that file.
6. **For the generic script path** — help the user write a self-contained bash script, upload it with checksums alongside their data, and submit. The script should install its dependencies at the top.
7. **Before submitting — confirm with the user** — summarize the job: tool, image+digest, input file count, `num_containers`, memory, runtime, and output path. Ask the user to confirm before calling `submit_job`. This prevents wasted cluster time from wrong arguments.
8. **After submission — display the job ID prominently and save it to a file** — print it clearly and write it to `projects/<id>/data/cts_job_id.txt` (or equivalent). The user needs it to check status or retrieve results, and may lose it if the notebook closes.
9. **Monitor when asked** — use `get_job_status()` for lightweight polling. For blocking waits, use `wait_for_completion()` in a background thread. For CheckM2 (confirmed auto-import), use `wait_for_completion(wait_for_event_importer=True)` and then query the Spark table directly. For other images, check with the user or the CTS team before assuming an importer exists.
10. **Help find previous jobs** — if the user lost their job ID or wants to check past runs, use `tscli.list_jobs()` with appropriate filters (`state`, `after`, `before`, `cluster`). Once found, reconstruct the job object with `tscli.get_job_by_id()`.
11. **On completion — tell the user where their results are** — state the output location explicitly (the `output_dir` passed to `submit_job`). List the actual output files from `job.get_job()["outputs"]`. Show the `mc cp --recursive` command to download them.
12. **On error** — call `job.get_exit_codes()` first to see which containers failed, then read stderr logs for those containers (`job.print_logs(container_num=N, stderr=True)`). The most common causes are wrong args, missing `--force` for Bakta, insufficient memory, or missing checksums.
13. **Retrieve and interpret results** — help the user download outputs from MinIO and explain what the tool produced.

---

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to the active project's `projects/<id>/memories/pitfalls.md`.
