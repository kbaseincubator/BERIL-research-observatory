from __future__ import annotations

from pathlib import Path

from .config import DOCS_TARGET_URI, PROJECTS_TARGET_URI


PROJECT_CURATED_NAMES = (
    "README.md",
    "RESEARCH_PLAN.md",
    "REPORT.md",
    "REVIEW.md",
    "references.md",
    "FINDINGS.md",
    "EXECUTIVE_SUMMARY.md",
    "FAILURE_ANALYSIS.md",
    "DESIGN_NOTES.md",
    "CORRECTIONS.md",
    "beril.yaml",
)

CENTRAL_DOC_NAMES = (
    "pitfalls.md",
    "discoveries.md",
    "performance.md",
    "research_ideas.md",
)

DOC_SOURCE_PATHS = [f"docs/{name}" for name in CENTRAL_DOC_NAMES]


def select_project_files(project_dir: Path) -> list[Path]:
    project_path = Path(project_dir)
    return [
        project_path / name
        for name in PROJECT_CURATED_NAMES
        if (project_path / name).is_file()
    ]


def select_central_docs(repo_root: Path) -> list[Path]:
    root = Path(repo_root)
    return [root / rel for rel in DOC_SOURCE_PATHS if (root / rel).is_file()]


def project_target_uri(project_id: str) -> str:
    return f"{PROJECTS_TARGET_URI}{project_id}/"


def docs_target_uri(doc_path: Path) -> str:
    return f"{DOCS_TARGET_URI}{Path(doc_path).stem}/"


def iter_project_dirs(projects_dir: Path) -> list[Path]:
    path = Path(projects_dir)
    if not path.exists():
        return []
    return sorted(child for child in path.iterdir() if child.is_dir())
