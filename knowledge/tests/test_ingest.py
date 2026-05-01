from pathlib import Path

from observatory_context.config import ContextConfig
from observatory_context.ingest import (
    ingest_all,
    ingest_changed,
    ingest_projects,
)


class FakeClient:
    def __init__(self) -> None:
        self.added: list[tuple[str, str]] = []
        self.removed: list[tuple[str, bool]] = []
        self.linked: list[tuple[str, list[str], str]] = []
        self.wait_count = 0

    def add_resource(self, path: str, to: str, reason: str, wait: bool = False):
        self.added.append((path, to))
        return {"root_uri": to}

    def wait_processed(self):
        self.wait_count += 1

    def rm(self, uri: str, recursive: bool = False):
        self.removed.append((uri, recursive))

    def link(self, from_uri: str, to_uris, reason: str = ""):
        self.linked.append((from_uri, list(to_uris), reason))


def write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_config(repo_root: Path) -> ContextConfig:
    return ContextConfig(repo_root=repo_root)


def test_ingest_all_adds_project_and_docs(tmp_path: Path) -> None:
    write(tmp_path / "projects" / "demo" / "README.md", "# Demo\n")
    write(tmp_path / "docs" / "pitfalls.md", "# Pitfalls\n")
    client = FakeClient()

    ingest_all(make_config(tmp_path), client)

    targets = [target for _, target in client.added]
    assert "viking://resources/projects/demo/" in targets
    assert "viking://resources/docs/pitfalls/" in targets
    assert client.wait_count == 1


def test_ingest_changed_skips_unchanged_then_ingests_modified(tmp_path: Path) -> None:
    readme = tmp_path / "projects" / "demo" / "README.md"
    write(readme, "# Demo\n")
    config = make_config(tmp_path)
    client = FakeClient()

    ingest_changed(config, client)
    client.added.clear()
    ingest_changed(config, client)
    assert client.added == []

    write(readme, "# Demo changed\n")
    ingest_changed(config, client)

    assert [target for _, target in client.added] == [
        "viking://resources/projects/demo/",
    ]


def test_ingest_changed_removes_deleted_project(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    write(project / "README.md", "# Demo\n")
    config = make_config(tmp_path)
    client = FakeClient()

    ingest_changed(config, client)
    client.added.clear()
    project.joinpath("README.md").unlink()
    project.rmdir()
    ingest_changed(config, client)

    assert client.removed == [("viking://resources/projects/demo/", True)]
    assert client.added == []


def test_ingest_projects_uploads_only_listed_projects(tmp_path: Path) -> None:
    write(tmp_path / "projects" / "alpha" / "README.md", "# A\n")
    write(tmp_path / "projects" / "beta" / "README.md", "# B\n")
    write(tmp_path / "projects" / "gamma" / "README.md", "# G\n")
    client = FakeClient()

    ingest_projects(make_config(tmp_path), client, ["alpha", "beta"])

    targets = [target for _, target in client.added]
    assert "viking://resources/projects/alpha/" in targets
    assert "viking://resources/projects/beta/" in targets
    assert "viking://resources/projects/gamma/" not in targets
    assert client.wait_count == 1


def test_ingest_all_with_limit_ingests_first_n_projects_and_skips_docs(tmp_path: Path) -> None:
    for name in ("alpha", "beta", "gamma"):
        write(tmp_path / "projects" / name / "README.md", f"# {name}\n")
    write(tmp_path / "docs" / "pitfalls.md", "# Pitfalls\n")
    client = FakeClient()

    ingest_all(make_config(tmp_path), client, limit=2)

    targets = [target for _, target in client.added]
    assert "viking://resources/projects/alpha/" in targets
    assert "viking://resources/projects/beta/" in targets
    assert "viking://resources/projects/gamma/" not in targets
    assert "viking://resources/docs/pitfalls/" not in targets


def test_ingest_all_with_limit_writes_partial_manifest_so_changed_picks_up_remainder(
    tmp_path: Path,
) -> None:
    for name in ("alpha", "beta", "gamma"):
        write(tmp_path / "projects" / name / "README.md", f"# {name}\n")
    config = make_config(tmp_path)

    ingest_all(config, FakeClient(), limit=2)
    followup = FakeClient()
    ingest_changed(config, followup)

    targets = [target for _, target in followup.added]
    assert "viking://resources/projects/gamma/" in targets
    assert "viking://resources/projects/alpha/" not in targets
    assert "viking://resources/projects/beta/" not in targets


def test_ingest_project_links_related_projects_from_beril_yaml(tmp_path: Path) -> None:
    write(tmp_path / "projects" / "alpha" / "README.md", "# A\n")
    write(
        tmp_path / "projects" / "alpha" / "beril.yaml",
        "project_id: alpha\nrelated_projects:\n  - beta\n",
    )
    write(tmp_path / "projects" / "beta" / "README.md", "# B\n")
    client = FakeClient()

    ingest_projects(make_config(tmp_path), client, ["alpha"])

    assert client.linked == [
        (
            "viking://resources/projects/alpha/",
            ["viking://resources/projects/beta/"],
            "beril.yaml related_projects",
        )
    ]


def test_ingest_changed_with_limit_caps_project_targets(tmp_path: Path) -> None:
    for name in ("alpha", "beta", "gamma"):
        write(tmp_path / "projects" / name / "README.md", f"# {name}\n")
    config = make_config(tmp_path)
    client = FakeClient()

    ingest_changed(config, client, limit=2)

    targets = [target for _, target in client.added]
    project_targets = [t for t in targets if t.startswith("viking://resources/projects/")]
    assert len(project_targets) == 2
    assert project_targets == [
        "viking://resources/projects/alpha/",
        "viking://resources/projects/beta/",
    ]


