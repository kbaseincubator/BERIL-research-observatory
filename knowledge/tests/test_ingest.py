from pathlib import Path

from observatory_context.config import ContextConfig
import pytest

from observatory_context.ingest import ingest_all, ingest_changed, resolve_project_dir


class FakeClient:
    def __init__(self) -> None:
        self.added: list[tuple[str, str]] = []
        self.removed: list[tuple[str, bool]] = []
        self.wait_count = 0

    def add_resource(self, path: str, to: str, reason: str, wait: bool = False):
        self.added.append((path, to))
        return {"root_uri": to}

    def wait_processed(self):
        self.wait_count += 1

    def rm(self, uri: str, recursive: bool = False):
        self.removed.append((uri, recursive))


def write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_config(repo_root: Path) -> ContextConfig:
    return ContextConfig(repo_root=repo_root)


def test_ingest_all_adds_index_project_and_docs(tmp_path: Path) -> None:
    write(tmp_path / "projects" / "demo" / "README.md", "# Demo\n")
    write(tmp_path / "docs" / "pitfalls.md", "# Pitfalls\n")
    client = FakeClient()

    ingest_all(make_config(tmp_path), client)

    targets = [target for _, target in client.added]
    assert "viking://resources/projects/" in targets
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
        "viking://resources/projects/",
    ]


def test_ingest_changed_removes_deleted_project_and_refreshes_index(tmp_path: Path) -> None:
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
    assert [target for _, target in client.added] == ["viking://resources/projects/"]


def test_resolve_project_dir_rejects_missing_and_path_like_ids(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    write(tmp_path / "projects" / "demo" / "README.md", "# Demo\n")

    assert resolve_project_dir(config, "demo") == tmp_path / "projects" / "demo"
    with pytest.raises(ValueError):
        resolve_project_dir(config, "../docs")
    with pytest.raises(FileNotFoundError):
        resolve_project_dir(config, "missing")
