"""
Lakehouse Upload Utility for BERIL Research Observatory

Upload project data and files to the microbialdiscoveryforge lakehouse tenant.
Designed to run on BERDL JupyterHub with Spark access.

Usage:
    from lakehouse_upload import upload_project, upload_all_projects

    spark = get_spark_session()
    upload_project(spark, "metal_fitness_atlas", "/path/to/BERIL-research-observatory")
"""

import base64
import json
import os
import re
from datetime import datetime
from pathlib import Path

DATABASE = "microbialdiscoveryforge_observatory"

# File extensions treated as tabular data (uploaded as individual Delta tables)
TABULAR_EXTENSIONS = {".csv", ".tsv"}

# File extensions treated as text (stored as string content in project_files)
TEXT_EXTENSIONS = {
    ".md", ".txt", ".py", ".sh", ".ipynb", ".json", ".fasta", ".faa", ".fna",
    ".gitignore", ".gitkeep", ".html",
}

# File extensions treated as binary (stored as base64 in project_files)
BINARY_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf", ".pkl", ".pyc"}

# Files/directories to skip
SKIP_PATTERNS = {
    "__pycache__", ".ipynb_checkpoints", ".DS_Store", "Thumbs.db",
}


def _sanitize_table_name(name):
    """Convert a filename to a valid Spark table name.

    Replaces non-alphanumeric characters (except underscores) with underscores,
    and ensures the name doesn't start with a digit.
    """
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    if name and name[0].isdigit():
        name = "t_" + name
    # Collapse multiple underscores
    name = re.sub(r"_+", "_", name).strip("_")
    return name.lower()


def _make_table_name(project_id, file_path, data_dir):
    """Create a Delta table name from project ID and data file path.

    For files directly in data/, uses: {project_id}__{filename_stem}
    For files in subdirs like data/matrices/, uses: {project_id}__{subdir}_{filename_stem}
    """
    rel = Path(file_path).relative_to(data_dir)
    parts = list(rel.parts)
    # Remove file extension from last part
    parts[-1] = Path(parts[-1]).stem
    combined = "_".join(parts)
    return f"{_sanitize_table_name(project_id)}__{_sanitize_table_name(combined)}"


def _should_skip(path):
    """Check if a file or directory should be skipped."""
    parts = Path(path).parts
    return any(p in SKIP_PATTERNS for p in parts)


def _classify_file(file_path):
    """Classify a file as 'tabular', 'text', 'binary', or 'skip'.

    Returns (classification, extension).
    """
    ext = Path(file_path).suffix.lower()
    if ext in TABULAR_EXTENSIONS:
        return "tabular", ext
    if ext in TEXT_EXTENSIONS:
        return "text", ext
    if ext in BINARY_EXTENSIONS:
        return "binary", ext
    # Default: try text for unknown extensions
    return "text", ext


def get_upload_manifest(project_path):
    """Scan a project directory and classify all files for upload.

    Returns a list of dicts with keys:
        file_path: absolute path
        relative_path: path relative to project directory
        classification: 'tabular', 'text', 'binary', or 'skip'
        extension: file extension
        size_bytes: file size
        in_data_dir: whether the file is under data/
    """
    project_path = Path(project_path)
    manifest = []

    for root, dirs, files in os.walk(project_path):
        # Filter out skip directories in-place
        dirs[:] = [d for d in dirs if d not in SKIP_PATTERNS]

        for fname in files:
            full_path = Path(root) / fname
            if _should_skip(full_path):
                continue

            rel_path = full_path.relative_to(project_path)
            classification, ext = _classify_file(full_path)
            in_data_dir = rel_path.parts[0] == "data" if len(rel_path.parts) > 1 else False

            # Only tabular files in data/ get their own tables
            if classification == "tabular" and not in_data_dir:
                classification = "text"  # treat non-data CSVs as text files

            manifest.append({
                "file_path": str(full_path),
                "relative_path": str(rel_path),
                "classification": classification,
                "extension": ext,
                "size_bytes": full_path.stat().st_size,
                "in_data_dir": in_data_dir,
                "modified_date": datetime.fromtimestamp(full_path.stat().st_mtime),
            })

    return manifest


def _extract_readme_metadata(project_path):
    """Extract title, status, and authors from a project's README.md."""
    readme_path = Path(project_path) / "README.md"
    if not readme_path.exists():
        return {"title": "", "status": "", "authors": ""}

    content = readme_path.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")

    title = ""
    status = ""
    authors = ""

    section = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# ") and not title:
            title = stripped[2:].strip()
        elif stripped.startswith("## Status"):
            section = "status"
            continue
        elif stripped.startswith("## Authors"):
            section = "authors"
            continue
        elif stripped.startswith("## "):
            section = None
            continue

        if section == "status" and stripped and not status:
            status = stripped
        elif section == "authors" and stripped:
            authors = (authors + "\n" + stripped).strip() if authors else stripped

    return {"title": title, "status": status, "authors": authors}


def _get_git_info(base_path):
    """Get current git branch and commit hash."""
    import subprocess
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=base_path, text=True
        ).strip()
    except Exception:
        branch = "unknown"
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=base_path, text=True
        ).strip()
    except Exception:
        commit = "unknown"
    return branch, commit


def create_database(spark):
    """Create the microbialdiscoveryforge database if it doesn't exist."""
    spark.sql(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")
    print(f"Database '{DATABASE}' ready.")


def create_registry_tables(spark):
    """Create the project_registry and project_files tables if they don't exist."""
    create_database(spark)

    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {DATABASE}.project_registry (
            project_id STRING,
            title STRING,
            status STRING,
            authors STRING,
            git_repo STRING,
            git_branch STRING,
            git_commit STRING,
            upload_date TIMESTAMP,
            file_manifest STRING
        )
        USING DELTA
    """)
    print(f"Table '{DATABASE}.project_registry' ready.")

    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {DATABASE}.project_files (
            project_id STRING,
            file_path STRING,
            file_type STRING,
            content STRING,
            size_bytes LONG,
            modified_date TIMESTAMP,
            upload_date TIMESTAMP
        )
        USING DELTA
    """)
    print(f"Table '{DATABASE}.project_files' ready.")


def _upload_tabular_file(spark, project_id, file_info, data_dir, overwrite=True):
    """Upload a CSV/TSV file as a Delta table."""
    file_path = file_info["file_path"]
    ext = file_info["extension"]
    table_name = _make_table_name(project_id, file_path, data_dir)
    full_table = f"{DATABASE}.{table_name}"

    sep = "\t" if ext == ".tsv" else ","

    try:
        df = spark.read.csv(file_path, header=True, inferSchema=True, sep=sep)
        row_count = df.count()

        mode = "overwrite" if overwrite else "append"
        df.write.format("delta").mode(mode).saveAsTable(full_table)
        print(f"  [TABLE] {full_table} ({row_count:,} rows)")
        return {"table": full_table, "rows": row_count, "status": "ok"}
    except Exception as e:
        print(f"  [ERROR] {full_table}: {e}")
        return {"table": full_table, "rows": 0, "status": f"error: {e}"}


def _upload_file_content(spark, project_id, file_info, upload_date):
    """Upload a non-tabular file to the project_files table."""
    from pyspark.sql import Row

    file_path = file_info["file_path"]
    classification = file_info["classification"]

    try:
        if classification == "binary":
            with open(file_path, "rb") as f:
                content = base64.b64encode(f.read()).decode("ascii")
        else:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

        row = Row(
            project_id=project_id,
            file_path=file_info["relative_path"],
            file_type=file_info["extension"].lstrip("."),
            content=content,
            size_bytes=file_info["size_bytes"],
            modified_date=file_info["modified_date"],
            upload_date=upload_date,
        )
        df = spark.createDataFrame([row])
        df.write.format("delta").mode("append").insertInto(f"{DATABASE}.project_files")
        print(f"  [FILE]  {file_info['relative_path']}")
        return True
    except Exception as e:
        print(f"  [ERROR] {file_info['relative_path']}: {e}")
        return False


def upload_project(spark, project_id, base_path, overwrite=True):
    """Upload a single project to the lakehouse.

    Args:
        spark: SparkSession from get_spark_session()
        project_id: project directory name (e.g., "metal_fitness_atlas")
        base_path: path to the BERIL-research-observatory root
        overwrite: if True, overwrite existing tables (default True)
    """
    base_path = Path(base_path)
    project_path = base_path / "projects" / project_id

    if not project_path.exists():
        print(f"ERROR: Project directory not found: {project_path}")
        return None

    print(f"\n{'='*60}")
    print(f"Uploading project: {project_id}")
    print(f"{'='*60}")

    # Ensure database and registry tables exist
    create_registry_tables(spark)

    # Get manifest
    manifest = get_upload_manifest(project_path)
    data_dir = project_path / "data"
    upload_date = datetime.now()

    tabular_files = [f for f in manifest if f["classification"] == "tabular" and f["in_data_dir"]]
    other_files = [f for f in manifest if f["classification"] != "tabular" or not f["in_data_dir"]]

    total_size = sum(f["size_bytes"] for f in manifest)
    print(f"  Total files: {len(manifest)}")
    print(f"  Tabular data files: {len(tabular_files)} (-> individual Delta tables)")
    print(f"  Other files: {len(other_files)} (-> project_files table)")
    print(f"  Total size: {total_size / 1024 / 1024:.1f} MB")
    print()

    # Clear existing project_files entries for this project if overwriting
    if overwrite:
        try:
            spark.sql(f"""
                DELETE FROM {DATABASE}.project_files
                WHERE project_id = '{project_id}'
            """)
        except Exception:
            pass  # Table might not have data yet

    # Upload tabular data files as individual Delta tables
    table_results = []
    if tabular_files:
        print("Uploading tabular data files:")
        for f in tabular_files:
            result = _upload_tabular_file(spark, project_id, f, data_dir, overwrite)
            table_results.append(result)
        print()

    # Upload non-tabular files to project_files
    file_count = 0
    if other_files:
        print("Uploading project files:")
        for f in other_files:
            success = _upload_file_content(spark, project_id, f, upload_date)
            if success:
                file_count += 1
        print()

    # Update project registry
    readme_meta = _extract_readme_metadata(project_path)
    git_branch, git_commit = _get_git_info(base_path)

    manifest_summary = json.dumps([{
        "path": f["relative_path"],
        "type": f["classification"],
        "size": f["size_bytes"],
    } for f in manifest])

    # Delete existing registry entry if overwriting
    if overwrite:
        try:
            spark.sql(f"""
                DELETE FROM {DATABASE}.project_registry
                WHERE project_id = '{project_id}'
            """)
        except Exception:
            pass

    from pyspark.sql import Row
    registry_row = Row(
        project_id=project_id,
        title=readme_meta["title"],
        status=readme_meta["status"],
        authors=readme_meta["authors"],
        git_repo="https://github.com/kbaseincubator/BERIL-research-observatory",
        git_branch=git_branch,
        git_commit=git_commit,
        upload_date=upload_date,
        file_manifest=manifest_summary,
    )
    df = spark.createDataFrame([registry_row])
    df.write.format("delta").mode("append").insertInto(f"{DATABASE}.project_registry")

    print(f"Summary for {project_id}:")
    print(f"  Delta tables created: {len(table_results)}")
    print(f"  Files uploaded: {file_count}")
    print(f"  Registry entry: updated")
    print(f"  Total size: {total_size / 1024 / 1024:.1f} MB")

    return {
        "project_id": project_id,
        "tables": table_results,
        "files_uploaded": file_count,
        "total_size_bytes": total_size,
    }


def upload_all_projects(spark, base_path, overwrite=True):
    """Upload all projects that have data directories.

    Args:
        spark: SparkSession from get_spark_session()
        base_path: path to the BERIL-research-observatory root
        overwrite: if True, overwrite existing tables (default True)
    """
    base_path = Path(base_path)
    projects_dir = base_path / "projects"

    project_ids = sorted([
        d.name for d in projects_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ])

    print(f"Found {len(project_ids)} projects to upload.\n")

    results = []
    for pid in project_ids:
        result = upload_project(spark, pid, base_path, overwrite)
        if result:
            results.append(result)

    print(f"\n{'='*60}")
    print(f"UPLOAD COMPLETE")
    print(f"{'='*60}")
    print(f"  Projects uploaded: {len(results)}")
    total_tables = sum(len(r["tables"]) for r in results)
    total_files = sum(r["files_uploaded"] for r in results)
    total_size = sum(r["total_size_bytes"] for r in results)
    print(f"  Delta tables created: {total_tables}")
    print(f"  Files uploaded: {total_files}")
    print(f"  Total size: {total_size / 1024 / 1024:.1f} MB")

    return results


def list_uploaded_projects(spark):
    """List all projects in the lakehouse registry."""
    try:
        df = spark.sql(f"""
            SELECT project_id, title, status, upload_date
            FROM {DATABASE}.project_registry
            ORDER BY project_id
        """)
        df.show(truncate=False)
        return df
    except Exception as e:
        print(f"Error listing projects: {e}")
        return None


def list_project_tables(spark, project_id):
    """List all Delta tables for a specific project."""
    prefix = _sanitize_table_name(project_id) + "__"
    try:
        tables = spark.sql(f"SHOW TABLES IN {DATABASE}").collect()
        project_tables = [
            t["tableName"] for t in tables
            if t["tableName"].startswith(prefix)
        ]
        print(f"Tables for project '{project_id}':")
        for t in sorted(project_tables):
            count = spark.sql(f"SELECT COUNT(*) as n FROM {DATABASE}.{t}").collect()[0]["n"]
            print(f"  {DATABASE}.{t} ({count:,} rows)")
        return project_tables
    except Exception as e:
        print(f"Error listing tables: {e}")
        return []
