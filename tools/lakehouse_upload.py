"""
Lakehouse Upload Utility for BERIL Research Observatory

Upload project data and files to the microbialdiscoveryforge tenant on BERDL
MinIO object storage via the `mc` (MinIO Client) CLI.

Usage (CLI):
    python tools/lakehouse_upload.py metal_fitness_atlas
    python tools/lakehouse_upload.py --all
    python tools/lakehouse_upload.py --list

Usage (Python):
    from lakehouse_upload import upload_project, upload_all_projects
    upload_project("metal_fitness_atlas", "/path/to/BERIL-research-observatory")
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MC_ALIAS = "berdl-minio"
BUCKET = "cdm-lake"
TENANT_PATH = "tenant-general-warehouse/microbialdiscoveryforge"
LAKEHOUSE_BASE = f"{MC_ALIAS}/{BUCKET}/{TENANT_PATH}/projects"

# S3a path for documentation and Spark references
S3A_BASE = f"s3a://{BUCKET}/{TENANT_PATH}/projects"

# Files/directories to skip during upload
SKIP_PATTERNS = {
    "__pycache__", ".ipynb_checkpoints", ".DS_Store", "Thumbs.db",
}


def _mc(*args, capture=True):
    """Run an mc command and return (returncode, stdout, stderr)."""
    cmd = ["mc"] + list(args)
    result = subprocess.run(cmd, capture_output=capture, text=True)
    return result.returncode, result.stdout, result.stderr


def _check_mc_alias():
    """Verify the berdl-minio mc alias is configured."""
    rc, out, err = _mc("alias", "list", MC_ALIAS)
    if rc != 0:
        print(f"ERROR: mc alias '{MC_ALIAS}' not configured.", file=sys.stderr)
        print("Run: mc alias set berdl-minio $MINIO_ENDPOINT_URL $AWS_ACCESS_KEY_ID $AWS_SECRET_ACCESS_KEY", file=sys.stderr)
        return False
    return True


def _get_git_info(base_path):
    """Get current git branch and commit hash."""
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=base_path, text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        branch = "unknown"
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=base_path, text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        commit = "unknown"
    return branch, commit


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


def get_upload_manifest(project_path):
    """Scan a project directory and list all files for upload.

    Returns a list of dicts with keys:
        file_path: absolute path
        relative_path: path relative to project directory
        extension: file extension
        size_bytes: file size
        modified_date: last modified datetime
    """
    project_path = Path(project_path)
    manifest = []

    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in SKIP_PATTERNS]

        for fname in files:
            if fname in SKIP_PATTERNS:
                continue

            full_path = Path(root) / fname
            rel_path = full_path.relative_to(project_path)

            manifest.append({
                "file_path": str(full_path),
                "relative_path": str(rel_path),
                "extension": full_path.suffix.lower(),
                "size_bytes": full_path.stat().st_size,
                "modified_date": datetime.fromtimestamp(
                    full_path.stat().st_mtime, tz=timezone.utc
                ),
            })

    return manifest


def generate_metadata(project_id, base_path):
    """Generate a project_metadata.json for a project.

    Follows the BERDL lakehouse publishing guidelines.
    Returns the metadata dict.
    """
    base_path = Path(base_path)
    project_path = base_path / "projects" / project_id

    manifest = get_upload_manifest(project_path)
    readme_meta = _extract_readme_metadata(project_path)
    git_branch, git_commit = _get_git_info(base_path)

    total_bytes = sum(f["size_bytes"] for f in manifest)
    data_files = [f for f in manifest if f["relative_path"].startswith("data/")]

    metadata = {
        "project_id": project_id,
        "title": readme_meta["title"],
        "status": readme_meta["status"],
        "authors": readme_meta["authors"],
        "description": f"BERIL Observatory project: {readme_meta['title']}",
        "git_repo": "https://github.com/kbaseincubator/BERIL-research-observatory",
        "git_branch": git_branch,
        "git_commit": git_commit,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": os.environ.get("USER", "unknown"),
        "lakehouse_path": f"{S3A_BASE}/{project_id}/",
        "local_path": f"projects/{project_id}/",
        "total_files": len(manifest),
        "total_size_bytes": total_bytes,
        "data_files": [
            {
                "name": Path(f["relative_path"]).name,
                "path": f["relative_path"],
                "size_bytes": f["size_bytes"],
                "extension": f["extension"],
            }
            for f in data_files
        ],
        "files": [
            {
                "path": f["relative_path"],
                "size_bytes": f["size_bytes"],
            }
            for f in manifest
        ],
    }

    return metadata


def upload_project(project_id, base_path):
    """Upload a single project to the lakehouse via mc cp.

    Args:
        project_id: project directory name (e.g., "metal_fitness_atlas")
        base_path: path to the BERIL-research-observatory root

    Returns dict with upload results, or None on failure.
    """
    base_path = Path(base_path)
    project_path = base_path / "projects" / project_id

    if not project_path.exists():
        print(f"ERROR: Project directory not found: {project_path}")
        return None

    if not _check_mc_alias():
        return None

    remote_path = f"{LAKEHOUSE_BASE}/{project_id}/"
    manifest = get_upload_manifest(project_path)
    total_size = sum(f["size_bytes"] for f in manifest)

    print(f"\n{'='*60}")
    print(f"Uploading: {project_id}")
    print(f"  Local:  {project_path}")
    print(f"  Remote: {remote_path}")
    print(f"  Files:  {len(manifest)}")
    print(f"  Size:   {total_size / 1024 / 1024:.1f} MB")
    print(f"{'='*60}")

    # Generate and write metadata locally first
    metadata = generate_metadata(project_id, base_path)
    metadata_path = project_path / "project_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, default=str))

    # Upload entire project directory
    rc, out, err = _mc("cp", "--recursive", f"{project_path}/", remote_path, capture=False)
    if rc != 0:
        print(f"ERROR: mc cp failed for {project_id}")
        metadata_path.unlink(missing_ok=True)
        return None

    # Validate upload
    rc, out, _ = _mc("ls", "--recursive", remote_path)
    remote_count = len([line for line in out.strip().split("\n") if line.strip()])

    # Clean up local metadata file (it's now in the lakehouse)
    metadata_path.unlink(missing_ok=True)

    result = {
        "project_id": project_id,
        "local_files": len(manifest),
        "remote_files": remote_count,
        "total_size_bytes": total_size,
        "remote_path": remote_path,
        "s3a_path": f"{S3A_BASE}/{project_id}/",
        "status": "ok" if remote_count >= len(manifest) else "warning",
    }

    print(f"  Result: {remote_count} files uploaded")
    if remote_count < len(manifest):
        print(f"  WARNING: expected {len(manifest)}, got {remote_count}")

    return result


def upload_all_projects(base_path):
    """Upload all projects to the lakehouse.

    Args:
        base_path: path to the BERIL-research-observatory root

    Returns list of upload result dicts.
    """
    base_path = Path(base_path)
    projects_dir = base_path / "projects"

    if not _check_mc_alias():
        return []

    project_ids = sorted([
        d.name for d in projects_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ])

    print(f"Found {len(project_ids)} projects.\n")

    results = []
    for pid in project_ids:
        result = upload_project(pid, base_path)
        if result:
            results.append(result)

    print(f"\n{'='*60}")
    print(f"UPLOAD COMPLETE")
    print(f"{'='*60}")
    print(f"  Projects: {len(results)}")
    total_files = sum(r["remote_files"] for r in results)
    total_size = sum(r["total_size_bytes"] for r in results)
    print(f"  Files:    {total_files}")
    print(f"  Size:     {total_size / 1024 / 1024:.1f} MB")

    failed = [r for r in results if r["status"] != "ok"]
    if failed:
        print(f"\n  WARNINGS ({len(failed)}):")
        for r in failed:
            print(f"    {r['project_id']}: {r['local_files']} local, {r['remote_files']} remote")

    return results


def list_projects():
    """List all projects currently in the lakehouse."""
    if not _check_mc_alias():
        return

    rc, out, _ = _mc("ls", f"{LAKEHOUSE_BASE}/")
    if rc != 0:
        print("ERROR: Could not list lakehouse projects.")
        return

    print(f"Projects in {S3A_BASE}/\n")
    for line in out.strip().split("\n"):
        if line.strip():
            print(f"  {line.strip()}")


def validate_uploads(base_path):
    """Compare local projects against lakehouse and report discrepancies."""
    base_path = Path(base_path)
    projects_dir = base_path / "projects"

    if not _check_mc_alias():
        return

    project_ids = sorted([
        d.name for d in projects_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ])

    print(f"{'Project':<45} {'Local':<9} {'Remote':<9} {'Status'}")
    print("-" * 75)

    for pid in project_ids:
        project_path = projects_dir / pid
        manifest = get_upload_manifest(project_path)
        local_count = len(manifest)

        rc, out, _ = _mc("ls", "--recursive", f"{LAKEHOUSE_BASE}/{pid}/")
        if rc != 0:
            remote_count = 0
        else:
            remote_count = len([l for l in out.strip().split("\n") if l.strip()])

        if remote_count == 0:
            status = "NOT UPLOADED"
        elif remote_count >= local_count:
            status = "OK"
        else:
            status = "MISMATCH"

        print(f"{pid:<45} {local_count:<9} {remote_count:<9} {status}")


def main():
    parser = argparse.ArgumentParser(
        description="Upload BERIL Observatory projects to the BERDL lakehouse (MinIO)."
    )
    parser.add_argument(
        "project_id",
        nargs="?",
        help="Project to upload (directory name under projects/)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Upload all projects",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List projects in the lakehouse",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Compare local projects against lakehouse uploads",
    )
    parser.add_argument(
        "--base-path",
        default=".",
        help="Path to BERIL-research-observatory root (default: current dir)",
    )

    args = parser.parse_args()

    if args.list:
        list_projects()
    elif args.validate:
        validate_uploads(args.base_path)
    elif args.all:
        upload_all_projects(args.base_path)
    elif args.project_id:
        upload_project(args.project_id, args.base_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
