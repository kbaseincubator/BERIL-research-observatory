# In-Cluster `/berdl-ingest` Bypass Pattern

The `/berdl-ingest` skill's `scripts/ingest_lib.initialize()` requires SSH
tunnels, pproxy, and `berdl-remote login`/`spawn` - all specific to running from
a laptop. Inside BERDL JupyterHub, those preconditions don't apply: Spark
Connect is reachable directly at
`sc://jupyter-<user>.jupyterhub-prod:15002` and MinIO env vars are pre-set.

**On-cluster pattern**: Build your own Spark + MinIO clients and reuse the rest
of `ingest_lib` unchanged. The library's helpers (`detect_source_files`,
`parse_sql_schema`, `build_table_stats`, `upload_files`, `run_ingest`,
`verify_ingest`) are infrastructure-agnostic - only `initialize()` is
off-cluster-only.

```python
import os, sys
sys.path.insert(0, "/home/aparkin/BERIL-research-observatory/scripts")
import ingest_lib
from ingest_lib import (detect_source_files, parse_sql_schema, build_table_stats,
                       upload_files, run_ingest, verify_ingest)
from pyspark.sql import SparkSession
from minio import Minio

# Direct Spark Connect (on-cluster URL, no tunnels/pproxy)
token = os.environ["KBASE_AUTH_TOKEN"]
spark_url = f"sc://jupyter-{os.environ['USER']}.jupyterhub-prod:15002/;use_ssl=false;x-kbase-token={token}"
spark = SparkSession.builder.remote(spark_url).getOrCreate()

# Direct MinIO (env vars are pre-set on-cluster)
endpoint = os.environ["MINIO_ENDPOINT_URL"].replace("https://","").replace("http://","")
minio_client = Minio(endpoint,
    access_key=os.environ["MINIO_ACCESS_KEY"],
    secret_key=os.environ["MINIO_SECRET_KEY"],
    secure=os.environ.get("MINIO_SECURE","true").lower()=="true")

# Register with the berdl_notebook_utils stubs that ingest_lib sets up on import
sys.modules["berdl_notebook_utils.setup_spark_session"].get_spark_session = lambda **kw: spark
sys.modules["berdl_notebook_utils.clients"].get_minio_client = lambda **kw: minio_client

# Then use the rest of ingest_lib helpers exactly as off-cluster.
```

After this bypass runs, the rest of the ingest workflow - schema parsing, plan,
upload, ingest, verify - works unchanged.
