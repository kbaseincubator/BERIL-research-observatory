# Off-Cluster Mechanics

Reference notes for off-cluster BERDL access from a local machine. Companion to
`proxy-setup.md`, which covers SSH tunnels and pproxy. This file collects extra
mechanics that come up during off-cluster work: MinIO `mc` proxy variables, the
Spark Connect sidecar startup race after kernel restart, and the local-machine
Spark session pattern.

---

## MinIO `mc` Proxy Setup

When uploading projects to the lakehouse via `python tools/lakehouse_upload.py`,
the `mc` (MinIO client) commands will timeout if proxy environment variables are
not set.

**Symptom**: Upload fails with:
```
Get 'https://minio.berdl.kbase.us/cdm-lake/?location=': dial tcp 140.221.43.167:443: i/o timeout
```

**Root cause**: MinIO server (minio.berdl.kbase.us:443) is only reachable from
within the BERDL cluster or through the proxy chain.

**Solution**: Set proxy environment variables before running the upload script:
```bash
export https_proxy=http://127.0.0.1:8123
export no_proxy=localhost,127.0.0.1
python3 tools/lakehouse_upload.py <project_id>
```

**Prerequisites**: SSH tunnels (ports 1337, 1338) and pproxy (port 8123) must be
running. See `proxy-setup.md` and `.claude/skills/berdl-minio/SKILL.md` for setup.

**Note**: This applies to ALL `mc` commands when off-cluster, not just uploads.
The `lakehouse_upload.py` script should be updated to set these variables
automatically, but for now they must be set manually.

---

## Spark Connect Sidecar Startup Race (After Kernel Restart)

| **Local machine** | `from get_spark_session import get_spark_session` | Uses `scripts/get_spark_session.py`, requires `.venv-berdl` + proxy chain |

**Common mistakes**:
- Using `from get_spark_session import get_spark_session` on the BERDL cluster -> `ImportError` (that module is `scripts/get_spark_session.py`, only on local machines)
- Using `from berdl_notebook_utils.setup_spark_session import get_spark_session` locally -> `ImportError` (that package is only on the BERDL cluster)
- Using the bare `get_spark_session()` (no import) in a CLI script on JupyterHub -> `NameError` (auto-import only applies to notebook kernels)

### Don't Kill Java Processes

The Spark Connect service runs as a Java process on port 15002. Killing Java
processes (e.g., when cleaning up stale notebook processes) will take down Spark
Connect, and `get_spark_session()` will fail with `RETRIES_EXCEEDED` /
`Connection refused`.

**Recovery**: Log out of JupyterHub and start a new session. Then run
`get_spark_session()` from a notebook to restart the Spark Connect daemon. You
cannot restart it from the CLI.

### Spark Connect Sidecar Startup Race (Off-Cluster Access)

**Context**: Off-cluster access via `scripts/get_spark_session.py` + proxy chain.

**Problem**: After restarting the JupyterHub kernel, the Python kernel becomes
ready almost immediately, but the Spark Connect gRPC sidecar (the Java process
on port 15002) takes an additional 20-60 seconds to start and register with the
BERDL gateway. During this window, any connection attempt from outside the
cluster fails with:

```
SparkConnectGrpcException: FAILED_PRECONDITION
  "Spark Connect server at jupyter-<username>.jupyterhub-prod.svc.cluster.local:15002
   is not reachable. Please ensure you have logged in to BERDL JupyterHub and your
   notebook's Spark Connect service is running."
```

This is misleading - the session *is* running, the sidecar just hasn't finished
starting. The error looks identical to a "not logged in" error, so it's easy to
mistake for an authentication problem and keep resetting the kernel
unnecessarily.

**Solution**: After restarting the kernel, wait ~30-60 seconds before attempting
off-cluster connections, or poll with retries:

```bash
source .venv-berdl/bin/activate
for i in $(seq 1 10); do
    echo "Attempt $i at $(date +%H:%M:%S)..."
    result=$(uv run scripts/run_sql.py --berdl-proxy --query "SELECT 1 AS ok" 2>&1)
    if echo "$result" | grep -q '"ok"'; then
        echo "Connected!"
        break
    fi
    sleep 10
done
```

---

## Local-Machine Spark Session

**3. Local machine** (requires `.venv-berdl` + proxy chain):

```python
from get_spark_session import get_spark_session  # scripts/get_spark_session.py
spark = get_spark_session()
```

The local `scripts/get_spark_session.py` creates a remote Spark Connect session
through the proxy chain. See `scripts/README.md` and
`.claude/skills/berdl-query/SKILL.md` for setup.
