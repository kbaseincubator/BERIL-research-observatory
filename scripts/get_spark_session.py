"""Drop-in local replacement for the BERDL JupyterHub get_spark_session.

On JupyterHub, get_spark_session() is injected into the kernel and creates
a local Spark session on the compute node.  This version creates a remote
Spark Connect session through the BERDL proxy chain, so the same notebooks
work on a local machine without code changes.

Prerequisites (see .claude/skills/berdl-query/references/proxy-setup.md):
  - KBASE_AUTH_TOKEN in environment or .env
  - SSH SOCKS tunnels on ports 1337/1338
  - pproxy on port 8123
  - JupyterHub session active
"""

from __future__ import annotations

import os
from pathlib import Path


def _load_env() -> None:
    """Load .env from repo root if vars are not already set."""
    # Walk up from this file to find .env at the repo root
    candidate = Path(__file__).resolve().parent.parent / ".env"
    if not candidate.exists():
        return
    for raw_line in candidate.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def get_spark_session(
    *,
    app_name: str = "berdl-local-notebook",
    berdl_proxy: bool = True,
    host_template: str | None = None,
    port: int | None = None,
    use_ssl: bool = True,
) -> "pyspark.sql.SparkSession":
    """Return a remote Spark session connected to the BERDL cluster.

    Called with no arguments, this matches the JupyterHub interface::

        spark = get_spark_session()

    Keyword arguments are available for advanced use but not required.
    """
    _load_env()

    token = os.getenv("KBASE_AUTH_TOKEN")
    if not token:
        raise RuntimeError(
            "KBASE_AUTH_TOKEN is required. Set it in your environment or .env file."
        )

    if berdl_proxy:
        os.environ.setdefault("grpc_proxy", "http://127.0.0.1:8123")
        os.environ.setdefault("https_proxy", "http://127.0.0.1:8123")
        os.environ.setdefault("no_proxy", "localhost,127.0.0.1")
        if host_template is None:
            host_template = "metrics.berdl.kbase.us"

    if host_template is None:
        host_template = os.getenv("BERDL_SPARK_HOST_TEMPLATE", "spark.berdl.kbase.us")
    if port is None:
        port = int(os.getenv("BERDL_SPARK_PORT", "443"))

    from spark_connect_remote import create_spark_session

    return create_spark_session(
        host_template=host_template,
        port=port,
        use_ssl=use_ssl,
        kbase_token=token,
        app_name=app_name,
    )
