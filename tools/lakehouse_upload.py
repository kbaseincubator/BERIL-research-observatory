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
import time
from datetime import datetime, timezone
from pathlib import Path

MC_ALIAS = "berdl-minio"
BUCKET = "cdm-lake"
TENANT_PATH = "tenant-general-warehouse/microbialdiscoveryforge"
LAKEHOUSE_BASE = f"{MC_ALIAS}/{BUCKET}/{TENANT_PATH}/projects"

# S3a path for documentation and Spark references
S3A_BASE = f"s3a://{BUCKET}/{TENANT_PATH}/projects"

# Files/directories to skip during the manifest walk. The manifest is the
# source of truth for what gets uploaded — upload_project iterates the
# manifest directly rather than `mc cp --recursive`, so any name in this
# set is guaranteed to stay out of the lakehouse archive regardless of
# mc's exclude semantics.
#
# `.submit.lock` is held by /submit through Phase 3, so the upload runs
# while the lock file is still present in the project directory. Without
# this entry it would be archived in every successful submission.
#
# `project_metadata.json` is generated fresh on every upload and added
# explicitly to the upload list (see `upload_project`). Skipping it from
# the walk avoids two failure modes: (1) `generate_metadata`'s self-listing
# would otherwise include the previous run's stale metadata in the new
# `files[]` array, and (2) if a previous run died between writing the
# metadata file and the cleanup `unlink`, the stale file would appear in
# the new manifest, the upload list would then have the same relative
# path twice, and `expected_remote_count = len(manifest) + 1` would
# expect two when only one lands — turning a successful retry into a
# false partial-upload failure.
SKIP_PATTERNS = {
    "__pycache__", ".ipynb_checkpoints", ".DS_Store", "Thumbs.db",
    ".submit.lock", "project_metadata.json",
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
        print(f"ERROR: Project directory not found: {project_path}", file=sys.stderr)
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

    # Time the upload step itself for the duration metric
    upload_start = time.monotonic()

    # Upload entire project directory. Always clean up the generated metadata
    # file afterwards, regardless of upload outcome — leaving it behind on
    # failure pollutes git status and confuses later retry manifests.
    try:
        # Re-submission contamination guard: if the remote prefix already has
        # contents from a previous submission, clear them before uploading.
        # `mc cp --recursive` overlays files but does not delete remote files
        # absent from the new manifest, so a re-submit that drops files would
        # leave stale objects in the archive. The pre-clear ensures the
        # archive at archive_key contains *only* the current approved manifest.
        # First-time submissions skip this (rc != 0 from `mc ls` on missing
        # prefix is normal).
        rc, ls_out, _ = _mc("ls", "--recursive", remote_path)
        if rc == 0 and any(line.strip() for line in ls_out.split("\n")):
            rc_rm, _, rm_err = _mc("rm", "--recursive", "--force", remote_path)
            if rc_rm != 0:
                print(
                    f"ERROR: pre-upload clear of {remote_path} failed (rc={rc_rm}); "
                    f"refusing to upload to avoid mixing with stale archive contents.",
                    file=sys.stderr,
                )
                if rm_err:
                    print(rm_err, file=sys.stderr)
                return None

        # Upload only the files we explicitly want in the archive: the
        # SKIP_PATTERNS-filtered manifest, plus the just-written
        # `project_metadata.json`. Per-file uploads (rather than
        # `mc cp --recursive`) ensure transient files like `.submit.lock`
        # — which `/submit` holds in the project directory through
        # Phase 3 — never enter the canonical lakehouse copy. SKIP_PATTERNS
        # is honored by the manifest walker; relying on `mc cp`'s
        # `--exclude` would couple correctness to mc's glob semantics
        # across versions, which we'd rather not bet the integrity
        # boundary on.
        upload_list = [
            (Path(f["file_path"]), f["relative_path"]) for f in manifest
        ]
        upload_list.append((metadata_path, "project_metadata.json"))

        upload_failures = []
        for local, rel in upload_list:
            target = f"{remote_path}{rel}"
            rc, _, _ = _mc("cp", str(local), target, capture=False)
            if rc != 0:
                upload_failures.append(rel)
        if upload_failures:
            print(
                f"ERROR: mc cp failed for {project_id} on "
                f"{len(upload_failures)} file(s): {upload_failures[:5]}"
                f"{'...' if len(upload_failures) > 5 else ''}",
                file=sys.stderr,
            )
            return None

        # Validate upload
        rc, out, _ = _mc("ls", "--recursive", remote_path)
        remote_count = len([line for line in out.strip().split("\n") if line.strip()])

        duration_seconds = round(time.monotonic() - upload_start, 2)
    finally:
        metadata_path.unlink(missing_ok=True)

    # We uploaded the manifest plus the generated `project_metadata.json`,
    # so the expected remote count is len(manifest) + 1. Without the +1,
    # a real project file failing to upload while metadata succeeds would
    # still satisfy `remote_count >= len(manifest)` and we'd mark an
    # incomplete archive as `status: ok`.
    expected_remote_count = len(manifest) + 1  # +1 for project_metadata.json

    result = {
        "project_id": project_id,
        "local_files": len(manifest),
        "remote_files": remote_count,
        "total_size_bytes": total_size,
        "remote_path": remote_path,
        "s3a_path": f"{S3A_BASE}/{project_id}/",
        "duration_seconds": duration_seconds,
        "status": "ok" if remote_count >= expected_remote_count else "warning",
    }

    print(f"  Result: {remote_count} files uploaded")
    if remote_count < expected_remote_count:
        print(f"  WARNING: expected {expected_remote_count} (manifest + project_metadata.json), got {remote_count}")

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
        result = upload_project(args.project_id, args.base_path)
        if result is None:
            sys.exit(1)
        # Emit a single-line JSON summary as the final line of stdout so
        # /submit (and other automated callers) can parse the upload result
        # without scraping freeform text.
        #
        # Exit code contract for callers:
        #   0  = full success; JSON has the success schema
        #        (archive_key, file_count, byte_total, duration_seconds)
        #   1  = hard failure; no JSON emitted (error already on stderr)
        #   2  = partial success; JSON has the success schema PLUS an
        #        "error" field describing the count mismatch. The archive
        #        exists at archive_key but is incomplete; the caller should
        #        treat this as a submission failure (write SUBMISSION_FAILED.md).
        payload = {
            "archive_key": result["s3a_path"],
            "file_count": result["remote_files"],
            "byte_total": result["total_size_bytes"],
            "duration_seconds": result["duration_seconds"],
        }
        if result["status"] != "ok":
            # `remote_files` counts everything at archive_key including the
            # generated `project_metadata.json`; subtract 1 so the message
            # reflects how many of the local manifest files actually landed.
            present_manifest = max(0, result["remote_files"] - 1)
            payload["error"] = (
                f"partial upload: {present_manifest} of "
                f"{result['local_files']} local files present at archive_key"
            )
        print(json.dumps(payload))
        sys.exit(0 if result["status"] == "ok" else 2)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
