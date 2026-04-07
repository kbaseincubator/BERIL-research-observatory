"""Run data_lakehouse_ingest for ontology2 via berdl-remote.

Passes the MinIO config path to ingest() on the cluster, where
berdl_notebook_utils is natively available. No local stubs needed.
"""
import subprocess
import sys

CONFIG_PATH = "s3a://cdm-lake/users-general-warehouse/amkhan/datasets/ontology2/ontology2.json"

code = (
    "from data_lakehouse_ingest import ingest; "
    f"report = ingest('{CONFIG_PATH}'); "
    "print(report)"
)

result = subprocess.run(
    ["berdl-remote", "python", code],
    text=True,
)
sys.exit(result.returncode)
