from pathlib import Path

from observatory_context.config import (
    DEFAULT_OPENVIKING_URL,
    DOCS_TARGET_URI,
    PROJECTS_TARGET_URI,
    ContextConfig,
)
from observatory_context.selection import (
    DOC_SOURCE_PATHS,
    docs_target_uri,
    iter_project_dirs,
    project_target_uri,
    select_central_docs,
    select_project_files,
)


def test_select_project_files_includes_curated_top_level_only(tmp_path: Path) -> None:
    project_dir = tmp_path / "demo"
    project_dir.mkdir()

    for name in (
        "REPORT.md",
        "README.md",
        "references.md",
        "beril.yaml",
        "README.review.md",
    ):
        (project_dir / name).write_text(name)

    for dirname in ("data", "figures", "notebooks", ".adversarial-debug"):
        nested_dir = project_dir / dirname
        nested_dir.mkdir()
        (nested_dir / "README.md").write_text("nested")

    assert select_project_files(project_dir) == [
        project_dir / "README.md",
        project_dir / "REPORT.md",
        project_dir / "references.md",
        project_dir / "beril.yaml",
    ]


def test_central_docs_uris_config_defaults_and_project_dirs(
    tmp_path: Path, monkeypatch
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    for name in ("research_ideas.md", "pitfalls.md", "unlisted.md"):
        (docs_dir / name).write_text(name)

    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    alpha = projects_dir / "alpha"
    beta = projects_dir / "beta"
    alpha.mkdir()
    beta.mkdir()
    (projects_dir / "README.md").write_text("not a project dir")

    monkeypatch.delenv("OPENVIKING_API_KEY", raising=False)

    config = ContextConfig.from_env(repo_root=tmp_path)

    assert config.openviking_url == DEFAULT_OPENVIKING_URL
    assert config.openviking_api_key is None
    assert config.projects_dir == tmp_path / "projects"
    assert config.docs_dir == tmp_path / "docs"
    assert config.staging_dir == tmp_path / "knowledge" / "staging"
    assert config.state_dir == tmp_path / "knowledge" / "state"
    assert select_central_docs(tmp_path) == [
        docs_dir / "pitfalls.md",
        docs_dir / "research_ideas.md",
    ]
    assert [path.relative_to(tmp_path).as_posix() for path in select_central_docs(tmp_path)] == [
        rel for rel in DOC_SOURCE_PATHS if rel in {"docs/pitfalls.md", "docs/research_ideas.md"}
    ]
    assert project_target_uri("alpha") == f"{PROJECTS_TARGET_URI}alpha/"
    assert docs_target_uri(Path("docs/pitfalls.md")) == f"{DOCS_TARGET_URI}pitfalls/"
    assert list(iter_project_dirs(projects_dir)) == [alpha, beta]

    monkeypatch.setenv("OPENVIKING_API_KEY", "secret")

    assert ContextConfig.from_env(repo_root=tmp_path).openviking_api_key == "secret"


