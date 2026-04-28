"""Tests for wiki lint checks."""

import json
from pathlib import Path

from app.wiki_lint import lint_wiki


def _setup_repo(tmp_path: Path) -> Path:
    (tmp_path / "projects").mkdir()
    for project_id in ("alpha_project", "beta_project", "gamma_project"):
        (tmp_path / "projects" / project_id).mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "discoveries.md").write_text("# Discoveries\n")
    (tmp_path / "ui" / "config").mkdir(parents=True)
    (tmp_path / "ui" / "config" / "collections.yaml").write_text(
        "collections:\n"
        "  - id: kbase_ke_pangenome\n"
        "    name: Pangenome\n"
        "    category: primary\n"
        "    icon: ''\n"
        "    description: test\n"
    )
    return tmp_path


def _write_page(tmp_path: Path, rel_path: str, **overrides) -> Path:
    page_path = tmp_path / "wiki" / rel_path
    page_path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = {
        "id": "topic.example",
        "title": "Example Topic",
        "type": "topic",
        "status": "draft",
        "summary": "Example summary.",
        "source_projects": ["alpha_project", "beta_project", "gamma_project"],
        "source_docs": ["docs/discoveries.md"],
        "related_collections": ["kbase_ke_pangenome"],
        "confidence": "medium",
        "generated_by": "pytest",
        "last_reviewed": "2026-04-28",
        "related_pages": [],
    }
    frontmatter.update(overrides)
    yaml_text = "\n".join(
        f"{key}: {json.dumps(value)}" for key, value in frontmatter.items()
    )
    page_path.write_text(f"---\n{yaml_text}\n---\n# {frontmatter.get('title', 'Untitled')}\n")
    return page_path


def test_valid_wiki_passes(tmp_path):
    repo = _setup_repo(tmp_path)
    _write_page(repo, "topics/example.md")
    assert lint_wiki(repo) == []


def test_missing_required_field_is_reported(tmp_path):
    repo = _setup_repo(tmp_path)
    _write_page(repo, "topics/example.md", summary=None)
    text = "\n".join(issue.message for issue in lint_wiki(repo))
    assert "empty required field: summary" in text

    page = repo / "wiki" / "topics" / "example.md"
    page.write_text(page.read_text().replace("summary: null\n", ""))
    text = "\n".join(issue.message for issue in lint_wiki(repo))
    assert "missing required field: summary" in text


def test_duplicate_id_and_broken_link_are_reported(tmp_path):
    repo = _setup_repo(tmp_path)
    _write_page(repo, "topics/example.md")
    _write_page(repo, "topics/duplicate.md", title="Different Title")
    page = repo / "wiki" / "topics" / "example.md"
    page.write_text(page.read_text() + "\n[Broken](/wiki/missing/page)\n")

    messages = "\n".join(issue.message for issue in lint_wiki(repo))
    assert "duplicate wiki id" in messages
    assert "broken wiki link" in messages


def test_unknown_project_and_collection_are_reported(tmp_path):
    repo = _setup_repo(tmp_path)
    _write_page(
        repo,
        "topics/example.md",
        source_projects=["missing_project"],
        related_collections=["missing_collection"],
    )
    messages = "\n".join(issue.message for issue in lint_wiki(repo))
    assert "unknown source project: missing_project" in messages
    assert "unknown related collection: missing_collection" in messages
