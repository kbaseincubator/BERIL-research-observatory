from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ProjectMetadata:
    project_id: str
    title: str
    status: str
    author_names: list[str]
    markdown: str


def build_project_metadata(project_dir: str | Path) -> ProjectMetadata:
    project_path = Path(project_dir)
    beril = _read_beril_yaml(project_path / "beril.yaml")
    readme = _read_text(project_path / "README.md")

    project_id = _string_field(beril.get("project_id")) or project_path.name
    title = _readme_title(readme) or project_id
    status = _string_field(beril.get("status")) or _readme_status(readme)
    engine = beril.get("engine") if isinstance(beril.get("engine"), dict) else {}
    authors = _authors(beril.get("authors"))
    author_names = [author["name"] for author in authors if author["name"]]

    markdown = _metadata_markdown(
        project_id=project_id,
        title=title,
        status=status,
        created_at=_string_field(beril.get("created_at")),
        last_session_at=_string_field(beril.get("last_session_at")),
        branch=_string_field(beril.get("branch")),
        engine_name=_string_field(engine.get("name")),
        authors=authors,
        source_files=_source_metadata_files(project_path),
    )

    return ProjectMetadata(
        project_id=project_id,
        title=title,
        status=status,
        author_names=author_names,
        markdown=markdown,
    )


def build_project_index(project_dirs: list[str | Path]) -> str:
    rows = [
        "# BERIL Project Index",
        "",
        "| Project | Title | Authors | Status |",
        "|---|---|---|---|",
    ]
    for project_dir in sorted(
        (Path(path) for path in project_dirs), key=lambda path: path.name
    ):
        metadata = build_project_metadata(project_dir)
        rows.append(
            "| "
            + " | ".join(
                [
                    metadata.project_id,
                    metadata.title,
                    ", ".join(metadata.author_names),
                    metadata.status,
                ]
            )
            + " |"
        )
    return "\n".join(rows)


def _read_beril_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _readme_title(readme: str) -> str:
    for line in readme.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _readme_status(readme: str) -> str:
    lines = readme.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "## Status":
            for status_line in lines[index + 1 :]:
                stripped = status_line.strip()
                if not stripped:
                    continue
                if stripped.startswith("#"):
                    return ""
                return stripped
    return ""


def _authors(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    authors = []
    for author in value:
        author_fields = author if isinstance(author, dict) else {}
        authors.append(
            {
                "name": _string_field(author_fields.get("name")),
                "affiliation": _string_field(author_fields.get("affiliation")),
                "orcid": _string_field(author_fields.get("orcid")),
            }
        )
    return authors


def _metadata_markdown(
    *,
    project_id: str,
    title: str,
    status: str,
    created_at: str,
    last_session_at: str,
    branch: str,
    engine_name: str,
    authors: list[dict[str, str]],
    source_files: list[str],
) -> str:
    lines = [
        f"# Project Metadata: {project_id}",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Project ID | {project_id} |",
        f"| Title | {title} |",
        f"| Status | {status} |",
        f"| Created At | {created_at} |",
        f"| Last Session At | {last_session_at} |",
        f"| Branch | {branch} |",
        f"| Engine | {engine_name} |",
        f"| Source metadata files | {', '.join(source_files)} |",
        "",
        "## Authors",
        "",
        "| Name | Affiliation | ORCID |",
        "| --- | --- | --- |",
    ]
    lines.extend(
        f"| {author['name']} | {author['affiliation']} | {author['orcid']} |"
        for author in authors
    )
    return "\n".join(lines)


def _source_metadata_files(project_path: Path) -> list[str]:
    names = []
    if (project_path / "beril.yaml").is_file():
        names.append("beril.yaml")
    if (project_path / "README.md").is_file():
        names.append("README.md")
    return names


def _string_field(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime | date):
        return value.isoformat()
    return str(value)
