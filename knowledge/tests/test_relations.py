from __future__ import annotations

from pathlib import Path

from observatory_context.relations import apply_project_relations, read_related_projects


class _LinkClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str], str]] = []

    def link(self, from_uri: str, to_uris, reason: str = "") -> None:
        self.calls.append((from_uri, list(to_uris), reason))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_read_related_projects_returns_list_or_empty(tmp_path: Path) -> None:
    project = tmp_path / "alpha"
    project.mkdir()
    assert read_related_projects(project) == []

    _write(project / "beril.yaml", "project_id: alpha\nrelated_projects:\n  - beta\n  - gamma\n")
    assert read_related_projects(project) == ["beta", "gamma"]


def test_read_related_projects_ignores_non_list(tmp_path: Path) -> None:
    project = tmp_path / "alpha"
    project.mkdir()
    _write(project / "beril.yaml", "project_id: alpha\nrelated_projects: beta\n")
    assert read_related_projects(project) == []


def test_apply_project_relations_links_existing_targets_only(tmp_path: Path) -> None:
    projects_dir = tmp_path / "projects"
    alpha = projects_dir / "alpha"
    beta = projects_dir / "beta"
    alpha.mkdir(parents=True)
    beta.mkdir()
    _write(
        alpha / "beril.yaml",
        "project_id: alpha\nrelated_projects:\n  - beta\n  - missing\n  - alpha\n",
    )
    client = _LinkClient()

    linked = apply_project_relations(client, alpha, projects_dir)

    assert linked == ["viking://resources/projects/beta/"]
    assert client.calls == [
        (
            "viking://resources/projects/alpha/",
            ["viking://resources/projects/beta/"],
            "beril.yaml related_projects",
        )
    ]


def test_apply_project_relations_skips_when_no_related(tmp_path: Path) -> None:
    projects_dir = tmp_path / "projects"
    alpha = projects_dir / "alpha"
    alpha.mkdir(parents=True)
    _write(alpha / "beril.yaml", "project_id: alpha\n")
    client = _LinkClient()

    assert apply_project_relations(client, alpha, projects_dir) == []
    assert client.calls == []
