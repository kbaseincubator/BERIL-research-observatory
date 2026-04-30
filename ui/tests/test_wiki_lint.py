"""Tests for Atlas lint checks."""

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
    _write_section_index_pages(tmp_path)
    return tmp_path


def _write_section_index_pages(tmp_path: Path) -> None:
    for section in ("topics", "data", "claims", "conflicts", "directions", "hypotheses"):
        _write_page(
            tmp_path,
            f"{section}/index.md",
            id=f"{section}.index",
            title=f"{section.title()} Index",
            type="meta",
            source_projects=[],
            source_docs=["docs/discoveries.md"],
            related_collections=[],
            related_pages=[],
        )


def _write_snapshot(tmp_path: Path, collection_ids: list[str]) -> None:
    snapshot_path = tmp_path / "ui" / "config" / "berdl_collections_snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "tenants": [
                    {
                        "id": "kbase",
                        "name": "KBase",
                        "collections": [
                            {"id": collection_id, "tables": []}
                            for collection_id in collection_ids
                        ],
                    }
                ]
            }
        )
    )


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
        "related_pages": ["claims.index"],
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
    page.write_text(page.read_text() + "\n[Broken](/atlas/missing/page)\n")

    messages = "\n".join(issue.message for issue in lint_wiki(repo))
    assert "duplicate Atlas id" in messages
    assert "broken Atlas link" in messages


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


def test_snapshot_requires_data_collection_pages(tmp_path):
    repo = _setup_repo(tmp_path)
    _write_snapshot(repo, ["kbase_ke_pangenome", "kbase_genomes"])
    _write_page(repo, "data/collections/pangenome.md", type="data_collection")

    messages = "\n".join(issue.message for issue in lint_wiki(repo))
    assert "missing data_collection page for discovered collection: kbase_genomes" in messages


def test_data_type_needs_two_known_collections(tmp_path):
    repo = _setup_repo(tmp_path)
    _write_snapshot(repo, ["kbase_ke_pangenome", "kbase_genomes"])
    _write_page(repo, "data/collections/pangenome.md", type="data_collection")
    _write_page(
        repo,
        "data/collections/genomes.md",
        id="data.genomes",
        title="Genomes",
        type="data_collection",
        related_collections=["kbase_genomes"],
    )
    _write_page(
        repo,
        "data/types/one.md",
        id="data.one",
        title="One Data Type",
        type="data_type",
        related_collections=["kbase_ke_pangenome"],
    )

    messages = "\n".join(issue.message for issue in lint_wiki(repo))
    assert "data_type pages must reference at least 2 known collections" in messages


def test_external_source_doc_is_allowed(tmp_path):
    repo = _setup_repo(tmp_path)
    _write_snapshot(repo, ["kbase_ke_pangenome"])
    _write_page(
        repo,
        "data/collections/pangenome.md",
        type="data_collection",
        source_docs=["https://example.org/source"],
    )

    messages = "\n".join(issue.message for issue in lint_wiki(repo))
    assert "missing source doc" not in messages


def test_evidence_metadata_required_for_reusable_pages(tmp_path):
    repo = _setup_repo(tmp_path)
    _write_page(
        repo,
        "claims/example.md",
        id="claim.example",
        title="Example Claim",
        type="claim",
    )

    messages = "\n".join(issue.message for issue in lint_wiki(repo))
    assert "claim pages require evidence metadata" in messages

    _write_page(
        repo,
        "claims/example.md",
        id="claim.example",
        title="Example Claim",
        type="claim",
        evidence=[{"source": "alpha_project", "support": "Test support."}],
    )
    messages = "\n".join(issue.message for issue in lint_wiki(repo))
    assert "claim pages require evidence metadata" not in messages


def test_derived_product_reuse_metadata_is_validated(tmp_path):
    repo = _setup_repo(tmp_path)
    _write_page(
        repo,
        "data/derived-products/example.md",
        id="data.example-product",
        title="Example Product",
        type="derived_product",
        evidence=[{"source": "alpha_project", "support": "Test support."}],
    )

    messages = "\n".join(issue.message for issue in lint_wiki(repo))
    assert "derived_product missing field: product_kind" in messages

    artifact = repo / "projects" / "alpha_project" / "product.tsv"
    artifact.write_text("id\tvalue\n")
    _write_page(
        repo,
        "data/derived-products/example.md",
        id="data.example-product",
        title="Example Product",
        type="derived_product",
        product_kind="score",
        reuse_status="promoted",
        produced_by_projects=["alpha_project"],
        used_by_projects=["beta_project"],
        output_artifacts=[{"path": "projects/alpha_project/product.tsv"}],
        review_routes=["alpha_project"],
        evidence=[{"source": "alpha_project", "support": "Test support."}],
    )

    messages = "\n".join(issue.message for issue in lint_wiki(repo))
    assert "derived_product missing field" not in messages
    assert "missing output artifact" not in messages


def test_conflict_pages_require_multiple_sides_and_resolution(tmp_path):
    repo = _setup_repo(tmp_path)
    _write_page(repo, "topics/example.md", id="topic.example")
    _write_page(
        repo,
        "conflicts/example.md",
        id="conflict.example",
        title="Example Conflict",
        type="conflict",
        source_projects=["alpha_project", "beta_project"],
        related_pages=["topic.example"],
        affected_pages=["topic.example"],
        conflict_status="unresolved",
        evidence_sides=[{"side": "a", "support": "Only one side."}],
        resolving_work=[],
    )

    messages = "\n".join(issue.message for issue in lint_wiki(repo))
    assert "conflict pages require at least two evidence_sides" in messages
    assert "conflict pages require resolving_work entries" in messages

    _write_page(
        repo,
        "conflicts/example.md",
        id="conflict.example",
        title="Example Conflict",
        type="conflict",
        source_projects=["alpha_project", "beta_project"],
        related_pages=["topic.example"],
        affected_pages=["topic.example"],
        conflict_status="unresolved",
        evidence_sides=[
            {"side": "a", "support": "A"},
            {"side": "b", "support": "B"},
        ],
        resolving_work=["Run a resolving analysis."],
    )

    messages = "\n".join(issue.message for issue in lint_wiki(repo))
    assert "conflict pages require at least two evidence_sides" not in messages
    assert "conflict pages require resolving_work entries" not in messages


def test_missing_section_index_is_reported(tmp_path):
    repo = _setup_repo(tmp_path)
    (repo / "wiki" / "topics" / "index.md").unlink()
    _write_page(repo, "topics/example.md")

    messages = "\n".join(issue.message for issue in lint_wiki(repo))
    assert "missing Atlas section index page: topics/index" in messages
