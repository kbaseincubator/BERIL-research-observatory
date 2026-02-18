# BERDL Scripts

Command-line tools for working with BERDL (BER Data Lakehouse) from your local machine.

## Quick Start

### 1. One-time setup

```bash
bash scripts/bootstrap_client.sh
```

Creates `.venv-berdl` with required packages (`spark_connect_remote`, `berdl_remote`, `boto3`, `pproxy`).

### 2. Check your environment

```bash
source .venv-berdl/bin/activate
python scripts/detect_berdl_environment.py
```

Automatically detects if you're on-cluster or off-cluster and checks all prerequisites.

### 3. Off-cluster only: Start proxy chain

**SSH tunnels** (requires your LBNL credentials):
```bash
ssh -f -N -o ServerAliveInterval=60 -D 1338 ac.<username>@login1.berkeley.kbase.us
ssh -f -N -o ServerAliveInterval=60 -D 1337 ac.<username>@login1.berkeley.kbase.us
```

**pproxy** (can be started by Claude or run manually):
```bash
bash scripts/start_pproxy.sh
```

Verify everything is running:
```bash
lsof -i :1337 -i :1338 -i :8123 | grep LISTEN
```

### 4. Run queries

```bash
source .venv-berdl/bin/activate
python scripts/run_sql.py --berdl-proxy --query "SHOW DATABASES"
python scripts/run_sql.py --berdl-proxy --query "SELECT * FROM kbase_ke_pangenome.pangenome LIMIT 10"
```

### 5. Export large results to MinIO

```bash
python scripts/export_sql.py \
  --berdl-proxy \
  --query "SELECT * FROM kbase_ke_pangenome.pangenome" \
  --path "s3a://cdm-lake/users-general-warehouse/<user>/exports/my-export" \
  --format parquet \
  --mode overwrite
```

### 6. Work with MinIO

```bash
# Get credentials
eval "$(python scripts/get_minio_creds.py --shell)"

# Configure mc client
bash scripts/configure_mc.sh --berdl-proxy

# Transfer files (remember to set proxy)
export https_proxy=http://127.0.0.1:8123
export no_proxy=localhost,127.0.0.1
mc ls berdl-minio/cdm-lake/users-general-warehouse/<user>/exports/
mc cp --recursive berdl-minio/cdm-lake/.../my-export ./local/
```

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `bootstrap_client.sh` | One-time setup: creates `.venv-berdl` and installs packages |
| `detect_berdl_environment.py` | Check prerequisites and get actionable next steps |
| `start_pproxy.sh` | Start the HTTP-to-SOCKS5 proxy bridge on port 8123 |
| `run_sql.py` | Run SQL queries, return results as JSON |
| `export_sql.py` | Run SQL queries, write results to MinIO (parquet/delta/csv/json) |
| `get_minio_creds.py` | Resolve MinIO credentials from `.env` or remote environment |
| `configure_mc.sh` | Configure MinIO `mc` client alias |
| `get_spark_session.py` | Drop-in replacement for JupyterHub `get_spark_session()` for local notebooks |

## Running Notebooks Locally

Once `.venv-berdl` is set up and the proxy chain is running, notebooks work identically on and off cluster:

```python
from get_spark_session import get_spark_session

spark = get_spark_session()
df = spark.sql("SELECT * FROM kbase_ke_pangenome.pangenome LIMIT 10")
pdf = df.toPandas()
```

No code changes needed. The `get_spark_session()` function automatically uses the proxy when off-cluster.

## Documentation

- Full proxy setup guide: `.claude/skills/berdl-query/references/proxy-setup.md`
- Query workflow: `.claude/skills/berdl-query/SKILL.md`
- MinIO workflow: `.claude/skills/berdl-minio/SKILL.md`
- Project docs: `PROJECT.md` (see "Local Spark Connect" section)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `connection refused` on :8123 | pproxy not running → run `bash scripts/start_pproxy.sh` |
| `Connect call failed ('127.0.0.1', 1338)` | SSH tunnel on 1338 is dead → restart it |
| `authentication service timed out` | SSH tunnel dropped → restart tunnels |
| `i/o timeout` on `spark.berdl.kbase.us:443` | Missing `--berdl-proxy` flag |

Run `python scripts/detect_berdl_environment.py` to diagnose issues automatically.
