# OpenViking Context Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first BERIL knowledge context layer by staging curated project Markdown/YAML into stable OpenViking resource targets, supporting initial/incremental ingestion and agent queries.

**Architecture:** Keep repository-specific logic in `knowledge/observatory_context/`, thin command-line entry points in `knowledge/scripts/`, generated files under `knowledge/staging/`, and local change state under `knowledge/state/`. OpenViking owns parsing, L0/L1/L2 generation, vector indexing, and resource-tree incremental sync; this code only selects files, stages a filtered tree, calls the Python SDK, and formats query output.

**Tech Stack:** Python 3.11+, `uv`, OpenViking Python SDK, PyYAML, pytest, OpenRouter-compatible `ov.conf` template.

---

## File Structure

- Create `knowledge/observatory_context/__init__.py`
  - Package marker and exported version.
- Create `knowledge/observatory_context/config.py`
  - Repository path discovery, OpenViking env config, target URI constants.
- Create `knowledge/observatory_context/selection.py`
  - Curated project/docs file selection and URI mapping.
- Create `knowledge/observatory_context/metadata.py`
  - `beril.yaml` parsing plus generated `PROJECT_METADATA.md` and `PROJECT_INDEX.md` content.
- Create `knowledge/observatory_context/manifest.py`
  - Hash selected source files and detect changed project/docs targets.
- Create `knowledge/observatory_context/staging.py`
  - Rebuild filtered staging trees from selected files plus generated metadata.
- Create `knowledge/observatory_context/openviking_client.py`
  - Create/close `openviking.SyncHTTPClient`.
- Create `knowledge/observatory_context/ingest.py`
  - Ingestion orchestration for all, changed, one project, and docs.
- Create `knowledge/observatory_context/query.py`
  - Query/overview/read wrappers and text/JSON formatting.
- Create `knowledge/scripts/ingest_context.py`
  - Thin ingestion CLI.
- Create `knowledge/scripts/knowledge_query.py`
  - Thin query CLI.
- Create `knowledge/openviking/ov.conf.example`
  - OpenRouter-focused OpenViking server config template.
- Create `knowledge/state/.gitkeep`
  - Keep state directory tracked; generated manifests are ignored.
- Create `knowledge/state/.gitignore`
  - Ignore generated manifest state.
- Create `knowledge/staging/.gitignore`
  - Ignore generated staging content.
- Create `knowledge/tests/`
  - Focused tests for selection, metadata, manifest, staging, query formatting, and CLI argument behavior.
- Modify `pyproject.toml`
  - Add a separate `knowledge` dependency group containing `openviking`, `pyyaml`, and `pytest`.
- Create `.claude/skills/knowledge-context/SKILL.md`
  - Agent instructions for querying and ingesting context.
- Modify `.claude/skills/pitfall-capture/SKILL.md`
  - Note project-local durable pitfall preference.
- Modify `.claude/skills/suggest-research/SKILL.md`
  - Note OpenViking context as the first project landscape query path.
- Modify `.claude/skills/synthesize/SKILL.md`
  - Note incremental context ingestion after report updates.

## Task 1: Dependencies And OpenRouter Config Template

**Files:**
- Modify: `pyproject.toml`
- Create: `knowledge/openviking/ov.conf.example`
- Create: `knowledge/state/.gitkeep`
- Create: `knowledge/state/.gitignore`
- Create: `knowledge/staging/.gitignore`

- [ ] **Step 1: Add knowledge dependency group**

Modify `pyproject.toml` to append:

```toml
[dependency-groups]
knowledge = [
  "openviking",
  "pyyaml",
  "pytest",
]
```

If `[dependency-groups]` already exists by the time this task is executed, add only the `knowledge` group.

- [ ] **Step 2: Add the OpenRouter OpenViking template**

Create `knowledge/openviking/ov.conf.example`:

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 1933
  },
  "storage": {
    "workspace": "knowledge/openviking/workspace"
  },
  "embedding": {
    "dense": {
      "provider": "openai",
      "api_key": "replace-with-openrouter-api-key",
      "api_base": "https://openrouter.ai/api/v1",
      "model": "openai/text-embedding-3-large",
      "dimension": 3072
    }
  },
  "vlm": {
    "provider": "openai",
    "api_key": "replace-with-openrouter-api-key",
    "api_base": "https://openrouter.ai/api/v1",
    "model": "google/gemini-3-flash-preview",
    "temperature": 0.0,
    "max_retries": 2,
    "extra_headers": {
      "HTTP-Referer": "https://github.com/kbaseincubator/BERIL-research-observatory",
      "X-Title": "BERIL Research Observatory"
    }
  },
  "log": {
    "level": "INFO"
  }
}
```

- [ ] **Step 3: Add generated-file placeholders**

Create `knowledge/state/.gitkeep` as an empty file.

Create `knowledge/state/.gitignore`:

```gitignore
*
!.gitignore
!.gitkeep
```

Create `knowledge/staging/.gitignore`:

```gitignore
*
!.gitignore
```

- [ ] **Step 4: Verify dependency parsing**

Run:

```bash
uv run --group knowledge python -c "import yaml; print('knowledge deps ok')"
```

Expected output:

```text
knowledge deps ok
```

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml knowledge/openviking/ov.conf.example knowledge/state/.gitkeep knowledge/state/.gitignore knowledge/staging/.gitignore
git commit -m "chore: add knowledge dependencies"
```

## Task 2: File Selection And URI Mapping

**Files:**
- Create: `knowledge/observatory_context/__init__.py`
- Create: `knowledge/observatory_context/config.py`
- Create: `knowledge/observatory_context/selection.py`
- Test: `knowledge/tests/test_selection.py`

- [ ] **Step 1: Write selection tests**

Create `knowledge/tests/test_selection.py`:

```python
from pathlib import Path

from observatory_context.config import ContextConfig
from observatory_context.selection import (
    DOC_SOURCE_PATHS,
    project_target_uri,
    select_central_docs,
    select_project_files,
)


def write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_select_project_files_uses_curated_top_level_files(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    write(project / "README.md")
    write(project / "REPORT.md")
    write(project / "REVIEW.md")
    write(project / "REVIEW_1.md")
    write(project / "ADVERSARIAL_REVIEW.md")
    write(project / "beril.yaml")
    write(project / "data" / "README.md")
    write(project / "figures" / "caption.md")
    write(project / "notebooks" / "notes.md")
    write(project / ".adversarial-debug" / "audit.md")

    selected = [path.relative_to(project).as_posix() for path in select_project_files(project)]

    assert selected == ["README.md", "REPORT.md", "REVIEW.md", "beril.yaml"]


def test_select_project_files_includes_approved_extras(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    for name in [
        "FINDINGS.md",
        "EXECUTIVE_SUMMARY.md",
        "FAILURE_ANALYSIS.md",
        "DESIGN_NOTES.md",
        "CORRECTIONS.md",
        "QUICK_START.md",
    ]:
        write(project / name)

    selected = [path.name for path in select_project_files(project)]

    assert selected == [
        "FINDINGS.md",
        "EXECUTIVE_SUMMARY.md",
        "FAILURE_ANALYSIS.md",
        "DESIGN_NOTES.md",
        "CORRECTIONS.md",
    ]


def test_select_central_docs_uses_only_requested_docs(tmp_path: Path) -> None:
    for rel in DOC_SOURCE_PATHS:
        write(tmp_path / rel)
    write(tmp_path / "docs" / "workflow.md")

    selected = [path.relative_to(tmp_path).as_posix() for path in select_central_docs(tmp_path)]

    assert selected == DOC_SOURCE_PATHS


def test_project_target_uri_is_stable() -> None:
    assert project_target_uri("metal_cross_resistance") == (
        "viking://resources/projects/metal_cross_resistance/"
    )


def test_context_config_defaults_to_local_openviking(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENVIKING_URL", raising=False)
    monkeypatch.delenv("OPENVIKING_API_KEY", raising=False)

    config = ContextConfig.from_env(repo_root=tmp_path)

    assert config.openviking_url == "http://localhost:1933"
    assert config.openviking_api_key is None
    assert config.projects_dir == tmp_path / "projects"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run --group knowledge pytest knowledge/tests/test_selection.py -q
```

Expected: import failure for missing `observatory_context`.

- [ ] **Step 3: Implement config and selection**

Create `knowledge/observatory_context/__init__.py`:

```python
"""BERIL OpenViking context utilities."""

__all__ = ["__version__"]

__version__ = "0.1.0"
```

Create `knowledge/observatory_context/config.py`:

```python
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_OPENVIKING_URL = "http://localhost:1933"
PROJECTS_TARGET_URI = "viking://resources/projects/"
DOCS_TARGET_URI = "viking://resources/docs/"


@dataclass(frozen=True)
class ContextConfig:
    repo_root: Path
    openviking_url: str
    openviking_api_key: str | None

    @classmethod
    def from_env(cls, repo_root: Path | None = None) -> "ContextConfig":
        root = repo_root or Path(__file__).resolve().parents[2]
        return cls(
            repo_root=root,
            openviking_url=os.environ.get("OPENVIKING_URL", DEFAULT_OPENVIKING_URL),
            openviking_api_key=os.environ.get("OPENVIKING_API_KEY"),
        )

    @property
    def projects_dir(self) -> Path:
        return self.repo_root / "projects"

    @property
    def docs_dir(self) -> Path:
        return self.repo_root / "docs"

    @property
    def staging_dir(self) -> Path:
        return self.repo_root / "knowledge" / "staging"

    @property
    def state_dir(self) -> Path:
        return self.repo_root / "knowledge" / "state"
```

Create `knowledge/observatory_context/selection.py`:

```python
from __future__ import annotations

from pathlib import Path

from .config import DOCS_TARGET_URI, PROJECTS_TARGET_URI


PROJECT_INCLUDE_NAMES = (
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

DOC_SOURCE_PATHS = [
    "docs/pitfalls.md",
    "docs/discoveries.md",
    "docs/performance.md",
    "docs/research_ideas.md",
]


def iter_project_dirs(projects_dir: Path) -> list[Path]:
    if not projects_dir.exists():
        return []
    return sorted(path for path in projects_dir.iterdir() if path.is_dir())


def select_project_files(project_dir: Path) -> list[Path]:
    selected: list[Path] = []
    for name in PROJECT_INCLUDE_NAMES:
        path = project_dir / name
        if path.is_file():
            selected.append(path)
    return selected


def select_central_docs(repo_root: Path) -> list[Path]:
    selected: list[Path] = []
    for rel in DOC_SOURCE_PATHS:
        path = repo_root / rel
        if path.is_file():
            selected.append(path)
    return selected


def project_target_uri(project_id: str) -> str:
    return f"{PROJECTS_TARGET_URI}{project_id}/"


def docs_target_uri(doc_path: Path) -> str:
    return f"{DOCS_TARGET_URI}{doc_path.stem}/"
```

- [ ] **Step 4: Run selection tests**

Run:

```bash
PYTHONPATH=knowledge uv run --group knowledge pytest knowledge/tests/test_selection.py -q
```

Expected: `5 passed`.

- [ ] **Step 5: Commit**

```bash
git add knowledge/observatory_context knowledge/tests/test_selection.py
git commit -m "feat: select context source files"
```

## Task 3: Metadata Generation

**Files:**
- Create: `knowledge/observatory_context/metadata.py`
- Test: `knowledge/tests/test_metadata.py`

- [ ] **Step 1: Write metadata tests**

Create `knowledge/tests/test_metadata.py`:

```python
from pathlib import Path

from observatory_context.metadata import build_project_index, build_project_metadata


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_build_project_metadata_from_beril_yaml(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "metal_cross_resistance"
    write(
        project / "beril.yaml",
        """
project_id: metal_cross_resistance
status: complete
created_at: "2026-04-27T00:00:00Z"
last_session_at: "2026-04-28T00:00:00Z"
branch: projects/metal_cross_resistance
engine:
  name: claude
authors:
  - name: "Paramvir S. Dehal"
    affiliation: "Lawrence Berkeley National Laboratory"
    orcid: "0000-0001-5810-2497"
artifacts:
  readme: true
  report: true
""",
    )
    write(project / "README.md", "# Gene-Resolution Metal Cross-Resistance\n\n## Status\nComplete\n")

    metadata = build_project_metadata(project)

    assert metadata.project_id == "metal_cross_resistance"
    assert metadata.title == "Gene-Resolution Metal Cross-Resistance"
    assert metadata.status == "complete"
    assert metadata.author_names == ["Paramvir S. Dehal"]
    assert "ORCID: 0000-0001-5810-2497" in metadata.markdown
    assert "Source metadata files: beril.yaml, README.md" in metadata.markdown


def test_build_project_metadata_falls_back_to_readme_status(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    write(project / "README.md", "# Demo Project\n\n## Status\nComplete - see report.\n")

    metadata = build_project_metadata(project)

    assert metadata.project_id == "demo"
    assert metadata.title == "Demo Project"
    assert metadata.status == "Complete - see report."
    assert metadata.author_names == []


def test_build_project_index_sorts_projects(tmp_path: Path) -> None:
    alpha = tmp_path / "projects" / "alpha"
    beta = tmp_path / "projects" / "beta"
    write(beta / "README.md", "# Beta\n\n## Status\nIn progress\n")
    write(alpha / "README.md", "# Alpha\n\n## Status\nComplete\n")

    index = build_project_index([beta, alpha])

    assert "| alpha | Alpha |  | Complete |" in index
    assert "| beta | Beta |  | In progress |" in index
    assert index.index("| alpha |") < index.index("| beta |")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONPATH=knowledge uv run --group knowledge pytest knowledge/tests/test_metadata.py -q
```

Expected: import failure for missing `metadata.py`.

- [ ] **Step 3: Implement metadata generation**

Create `knowledge/observatory_context/metadata.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
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


def build_project_metadata(project_dir: Path) -> ProjectMetadata:
    project_id = project_dir.name
    readme = _read_text(project_dir / "README.md")
    beril_path = project_dir / "beril.yaml"
    data = _load_yaml(beril_path) if beril_path.is_file() else {}

    title = _first_markdown_heading(readme) or project_id
    status = str(data.get("status") or _read_status_from_readme(readme) or "")
    authors = data.get("authors") if isinstance(data.get("authors"), list) else []
    author_lines = [_format_author(author) for author in authors if isinstance(author, dict)]
    author_names = [str(author.get("name")) for author in authors if isinstance(author, dict) and author.get("name")]
    engine = data.get("engine") if isinstance(data.get("engine"), dict) else {}
    source_files = []
    if beril_path.is_file():
        source_files.append("beril.yaml")
    if readme:
        source_files.append("README.md")

    lines = [
        f"# Project Metadata: {project_id}",
        "",
        f"- Project ID: {data.get('project_id') or project_id}",
        f"- Title: {title}",
        f"- Status: {status}",
        f"- Created at: {data.get('created_at', '')}",
        f"- Last session at: {data.get('last_session_at', '')}",
        f"- Branch: {data.get('branch', '')}",
        f"- Engine: {engine.get('name', '')}",
        f"- Source metadata files: {', '.join(source_files)}",
        "",
        "## Authors",
    ]
    lines.extend(author_lines or ["- "])
    lines.append("")

    return ProjectMetadata(
        project_id=project_id,
        title=title,
        status=status,
        author_names=author_names,
        markdown="\n".join(lines),
    )


def build_project_index(project_dirs: list[Path]) -> str:
    rows = []
    for project_dir in sorted(project_dirs, key=lambda path: path.name):
        metadata = build_project_metadata(project_dir)
        authors = ", ".join(metadata.author_names)
        rows.append(f"| {metadata.project_id} | {metadata.title} | {authors} | {metadata.status} |")

    return "\n".join(
        [
            "# BERIL Project Index",
            "",
            "| Project | Title | Authors | Status |",
            "|---|---|---|---|",
            *rows,
            "",
        ]
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _first_markdown_heading(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _read_status_from_readme(markdown: str) -> str:
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        if line.strip().lower() == "## status":
            for candidate in lines[index + 1 :]:
                stripped = candidate.strip()
                if stripped and not stripped.startswith("#"):
                    return stripped
    return ""


def _format_author(author: dict[str, Any]) -> str:
    name = author.get("name", "")
    affiliation = author.get("affiliation", "")
    orcid = author.get("orcid", "")
    parts = [str(name)] if name else []
    if affiliation:
        parts.append(str(affiliation))
    if orcid:
        parts.append(f"ORCID: {orcid}")
    return f"- {'; '.join(parts)}"
```

- [ ] **Step 4: Run metadata tests**

Run:

```bash
PYTHONPATH=knowledge uv run --group knowledge pytest knowledge/tests/test_metadata.py -q
```

Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add knowledge/observatory_context/metadata.py knowledge/tests/test_metadata.py
git commit -m "feat: generate project metadata context"
```

## Task 4: Manifest And Staging

**Files:**
- Create: `knowledge/observatory_context/manifest.py`
- Create: `knowledge/observatory_context/staging.py`
- Test: `knowledge/tests/test_manifest.py`
- Test: `knowledge/tests/test_staging.py`

- [ ] **Step 1: Write manifest tests**

Create `knowledge/tests/test_manifest.py`:

```python
from pathlib import Path

from observatory_context.manifest import build_manifest, changed_targets


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_changed_targets_detects_new_and_modified_files(tmp_path: Path) -> None:
    source = tmp_path / "README.md"
    write(source, "first")

    old = {}
    new = build_manifest({"viking://resources/projects/demo/": [source]}, tmp_path)

    assert changed_targets(old, new) == ["viking://resources/projects/demo/"]

    old = new
    write(source, "second")
    new = build_manifest({"viking://resources/projects/demo/": [source]}, tmp_path)

    assert changed_targets(old, new) == ["viking://resources/projects/demo/"]


def test_changed_targets_ignores_unchanged_files(tmp_path: Path) -> None:
    source = tmp_path / "README.md"
    write(source, "same")

    old = build_manifest({"target": [source]}, tmp_path)
    new = build_manifest({"target": [source]}, tmp_path)

    assert changed_targets(old, new) == []
```

- [ ] **Step 2: Write staging tests**

Create `knowledge/tests/test_staging.py`:

```python
from pathlib import Path

from observatory_context.staging import stage_docs, stage_project, stage_project_index


def write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_stage_project_copies_selected_files_and_metadata(tmp_path: Path) -> None:
    repo = tmp_path
    project = repo / "projects" / "demo"
    staging = repo / "knowledge" / "staging"
    write(project / "README.md", "# Demo\n\n## Status\nComplete\n")
    write(project / "REPORT.md", "# Report\n")
    write(project / "data" / "README.md", "# Data\n")

    staged = stage_project(project, staging)

    assert staged == staging / "projects" / "demo"
    assert (staged / "README.md").read_text(encoding="utf-8") == "# Demo\n\n## Status\nComplete\n"
    assert (staged / "REPORT.md").is_file()
    assert not (staged / "data" / "README.md").exists()
    assert (staged / "PROJECT_METADATA.md").is_file()


def test_stage_project_removes_stale_files(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    staging = tmp_path / "knowledge" / "staging"
    write(project / "README.md", "# Demo\n")
    stale = staging / "projects" / "demo" / "OLD.md"
    write(stale, "old")

    staged = stage_project(project, staging)

    assert not (staged / "OLD.md").exists()


def test_stage_docs_copies_selected_docs(tmp_path: Path) -> None:
    staging = tmp_path / "knowledge" / "staging"
    pitfalls = tmp_path / "docs" / "pitfalls.md"
    write(pitfalls, "# Pitfalls\n")

    staged = stage_docs([pitfalls], staging, tmp_path)

    assert staged == staging / "docs"
    assert (staged / "pitfalls.md").read_text(encoding="utf-8") == "# Pitfalls\n"


def test_stage_project_index_writes_index(tmp_path: Path) -> None:
    staging = tmp_path / "knowledge" / "staging"
    project = tmp_path / "projects" / "demo"
    write(project / "README.md", "# Demo\n\n## Status\nComplete\n")

    path = stage_project_index([project], staging)

    assert path == staging / "projects" / "PROJECT_INDEX.md"
    assert "| demo | Demo |  | Complete |" in path.read_text(encoding="utf-8")
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
PYTHONPATH=knowledge uv run --group knowledge pytest knowledge/tests/test_manifest.py knowledge/tests/test_staging.py -q
```

Expected: import failures for missing modules.

- [ ] **Step 4: Implement manifest**

Create `knowledge/observatory_context/manifest.py`:

```python
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


Manifest = dict[str, dict[str, str]]


def build_manifest(target_sources: dict[str, list[Path]], repo_root: Path) -> Manifest:
    manifest: Manifest = {}
    for target_uri, paths in sorted(target_sources.items()):
        entries: dict[str, str] = {}
        for path in sorted(paths):
            rel = path.relative_to(repo_root).as_posix()
            entries[rel] = _sha256(path)
        manifest[target_uri] = entries
    return manifest


def changed_targets(old: Manifest, new: Manifest) -> list[str]:
    return [target for target in sorted(new) if old.get(target) != new[target]]


def load_manifest(path: Path) -> Manifest:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def save_manifest(path: Path, manifest: Manifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
```

- [ ] **Step 5: Implement staging**

Create `knowledge/observatory_context/staging.py`:

```python
from __future__ import annotations

import shutil
from pathlib import Path

from .metadata import build_project_index, build_project_metadata
from .selection import select_project_files


def stage_project(project_dir: Path, staging_dir: Path) -> Path:
    target = staging_dir / "projects" / project_dir.name
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    for source in select_project_files(project_dir):
        shutil.copy2(source, target / source.name)

    metadata = build_project_metadata(project_dir)
    (target / "PROJECT_METADATA.md").write_text(metadata.markdown, encoding="utf-8")
    return target


def stage_project_index(project_dirs: list[Path], staging_dir: Path) -> Path:
    target = staging_dir / "projects"
    target.mkdir(parents=True, exist_ok=True)
    path = target / "PROJECT_INDEX.md"
    path.write_text(build_project_index(project_dirs), encoding="utf-8")
    return path


def stage_docs(doc_paths: list[Path], staging_dir: Path, repo_root: Path) -> Path:
    target = staging_dir / "docs"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    for source in doc_paths:
        shutil.copy2(source, target / source.name)
    return target
```

- [ ] **Step 6: Run manifest and staging tests**

Run:

```bash
PYTHONPATH=knowledge uv run --group knowledge pytest knowledge/tests/test_manifest.py knowledge/tests/test_staging.py -q
```

Expected: `6 passed`.

- [ ] **Step 7: Commit**

```bash
git add knowledge/observatory_context/manifest.py knowledge/observatory_context/staging.py knowledge/tests/test_manifest.py knowledge/tests/test_staging.py
git commit -m "feat: stage curated context files"
```

## Task 5: OpenViking Client And Ingestion Orchestration

**Files:**
- Create: `knowledge/observatory_context/openviking_client.py`
- Create: `knowledge/observatory_context/ingest.py`
- Test: `knowledge/tests/test_ingest.py`

- [ ] **Step 1: Write ingestion tests with a fake client**

Create `knowledge/tests/test_ingest.py`:

```python
from pathlib import Path

from observatory_context.config import ContextConfig
from observatory_context.ingest import ingest_all, ingest_changed


class FakeClient:
    def __init__(self) -> None:
        self.added: list[tuple[str, str, str, bool]] = []
        self.waited = False

    def add_resource(self, path: str, to: str, reason: str, wait: bool = False):
        self.added.append((path, to, reason, wait))
        return {"root_uri": to}

    def wait_processed(self):
        self.waited = True
        return {"status": "ok"}


def write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def config(tmp_path: Path) -> ContextConfig:
    return ContextConfig(repo_root=tmp_path, openviking_url="http://localhost:1933", openviking_api_key=None)


def test_ingest_all_adds_project_index_projects_and_docs(tmp_path: Path) -> None:
    write(tmp_path / "projects" / "demo" / "README.md", "# Demo\n")
    write(tmp_path / "docs" / "pitfalls.md", "# Pitfalls\n")
    client = FakeClient()

    ingest_all(config(tmp_path), client)

    targets = [entry[1] for entry in client.added]
    assert "viking://resources/projects/" in targets
    assert "viking://resources/projects/demo/" in targets
    assert "viking://resources/docs/pitfalls/" in targets
    assert client.waited is True


def test_ingest_changed_only_adds_modified_project(tmp_path: Path) -> None:
    write(tmp_path / "projects" / "demo" / "README.md", "# Demo\n")
    client = FakeClient()
    cfg = config(tmp_path)

    ingest_changed(cfg, client)
    client.added.clear()
    ingest_changed(cfg, client)

    assert client.added == []

    write(tmp_path / "projects" / "demo" / "README.md", "# Demo changed\n")
    ingest_changed(cfg, client)

    assert [entry[1] for entry in client.added] == ["viking://resources/projects/demo/"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONPATH=knowledge uv run --group knowledge pytest knowledge/tests/test_ingest.py -q
```

Expected: import failure for missing `ingest.py`.

- [ ] **Step 3: Implement OpenViking client factory**

Create `knowledge/observatory_context/openviking_client.py`:

```python
from __future__ import annotations

from typing import Any

import openviking as ov

from .config import ContextConfig


def create_client(config: ContextConfig) -> Any:
    client = ov.SyncHTTPClient(url=config.openviking_url, api_key=config.openviking_api_key)
    client.initialize()
    return client
```

- [ ] **Step 4: Implement ingestion orchestration**

Create `knowledge/observatory_context/ingest.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import DOCS_TARGET_URI, PROJECTS_TARGET_URI, ContextConfig
from .manifest import build_manifest, changed_targets, load_manifest, save_manifest
from .selection import (
    docs_target_uri,
    iter_project_dirs,
    project_target_uri,
    select_central_docs,
    select_project_files,
)
from .staging import stage_docs, stage_project, stage_project_index


MANIFEST_PATH = "context_manifest.json"


def ingest_all(config: ContextConfig, client: Any) -> None:
    project_dirs = iter_project_dirs(config.projects_dir)
    project_index = stage_project_index(project_dirs, config.staging_dir)
    _add_resource(client, project_index, PROJECTS_TARGET_URI, "BERIL project metadata index")

    for project_dir in project_dirs:
        staged = stage_project(project_dir, config.staging_dir)
        _add_resource(client, staged, project_target_uri(project_dir.name), f"BERIL project {project_dir.name}")

    for doc_path in select_central_docs(config.repo_root):
        staged_docs = stage_docs([doc_path], config.staging_dir, config.repo_root)
        _add_resource(client, staged_docs, docs_target_uri(doc_path), f"BERIL central doc {doc_path.name}")

    client.wait_processed()
    save_manifest(_manifest_file(config), _current_manifest(config))


def ingest_changed(config: ContextConfig, client: Any) -> None:
    old = load_manifest(_manifest_file(config))
    new = _current_manifest(config)
    targets = changed_targets(old, new)

    project_dirs = {project_dir.name: project_dir for project_dir in iter_project_dirs(config.projects_dir)}
    docs = {docs_target_uri(path): path for path in select_central_docs(config.repo_root)}

    for target_uri in targets:
        if target_uri.startswith(PROJECTS_TARGET_URI) and target_uri != PROJECTS_TARGET_URI:
            project_id = target_uri.removeprefix(PROJECTS_TARGET_URI).strip("/")
            staged = stage_project(project_dirs[project_id], config.staging_dir)
            _add_resource(client, staged, target_uri, f"BERIL project {project_id}")
        elif target_uri in docs:
            doc_path = docs[target_uri]
            staged_docs = stage_docs([doc_path], config.staging_dir, config.repo_root)
            _add_resource(client, staged_docs, target_uri, f"BERIL central doc {doc_path.name}")

    if targets:
        client.wait_processed()
    save_manifest(_manifest_file(config), new)


def ingest_project(config: ContextConfig, client: Any, project_id: str) -> None:
    project_dir = config.projects_dir / project_id
    staged = stage_project(project_dir, config.staging_dir)
    _add_resource(client, staged, project_target_uri(project_id), f"BERIL project {project_id}")
    client.wait_processed()
    save_manifest(_manifest_file(config), _current_manifest(config))


def ingest_docs(config: ContextConfig, client: Any) -> None:
    for doc_path in select_central_docs(config.repo_root):
        staged_docs = stage_docs([doc_path], config.staging_dir, config.repo_root)
        _add_resource(client, staged_docs, docs_target_uri(doc_path), f"BERIL central doc {doc_path.name}")
    client.wait_processed()
    save_manifest(_manifest_file(config), _current_manifest(config))


def _current_manifest(config: ContextConfig):
    target_sources = {}
    for project_dir in iter_project_dirs(config.projects_dir):
        target_sources[project_target_uri(project_dir.name)] = select_project_files(project_dir)
    for doc_path in select_central_docs(config.repo_root):
        target_sources[docs_target_uri(doc_path)] = [doc_path]
    return build_manifest(target_sources, config.repo_root)


def _add_resource(client: Any, path: Path, target_uri: str, reason: str) -> None:
    client.add_resource(path=str(path), to=target_uri, reason=reason, wait=False)


def _manifest_file(config: ContextConfig) -> Path:
    return config.state_dir / MANIFEST_PATH
```

- [ ] **Step 5: Run ingestion tests**

Run:

```bash
PYTHONPATH=knowledge uv run --group knowledge pytest knowledge/tests/test_ingest.py -q
```

Expected: `2 passed`.

- [ ] **Step 6: Run all current knowledge tests**

Run:

```bash
PYTHONPATH=knowledge uv run --group knowledge pytest knowledge/tests -q
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add knowledge/observatory_context/openviking_client.py knowledge/observatory_context/ingest.py knowledge/tests/test_ingest.py
git commit -m "feat: ingest staged context into OpenViking"
```

## Task 6: Query Formatting And Query CLI Core

**Files:**
- Create: `knowledge/observatory_context/query.py`
- Test: `knowledge/tests/test_query.py`

- [ ] **Step 1: Write query formatting tests**

Create `knowledge/tests/test_query.py`:

```python
from dataclasses import dataclass

from observatory_context.query import format_find_text, target_uri_for_find


@dataclass
class Match:
    uri: str
    score: float
    abstract: str
    match_reason: str = ""


@dataclass
class Result:
    resources: list[Match]
    total: int


def test_format_find_text_shows_uri_score_and_abstract() -> None:
    text = format_find_text(
        Result(
            resources=[
                Match(
                    uri="viking://resources/projects/demo/REPORT.md",
                    score=0.91,
                    abstract="Demo finding",
                    match_reason="semantic match",
                )
            ],
            total=1,
        )
    )

    assert "1 result" in text
    assert "viking://resources/projects/demo/REPORT.md" in text
    assert "Score: 0.910" in text
    assert "Demo finding" in text
    assert "semantic match" in text


def test_target_uri_for_find_prefers_project_scope() -> None:
    assert target_uri_for_find(project="demo", docs=False, metadata=False, target_uri=None) == (
        "viking://resources/projects/demo/"
    )


def test_target_uri_for_find_supports_docs_and_raw_uri() -> None:
    assert target_uri_for_find(project=None, docs=True, metadata=False, target_uri=None) == (
        "viking://resources/docs/"
    )
    assert target_uri_for_find(project=None, docs=False, metadata=False, target_uri="viking://x/") == (
        "viking://x/"
    )
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONPATH=knowledge uv run --group knowledge pytest knowledge/tests/test_query.py -q
```

Expected: import failure for missing `query.py`.

- [ ] **Step 3: Implement query helpers**

Create `knowledge/observatory_context/query.py`:

```python
from __future__ import annotations

import json
from typing import Any

from .config import DOCS_TARGET_URI, PROJECTS_TARGET_URI
from .selection import project_target_uri


def target_uri_for_find(
    project: str | None,
    docs: bool,
    metadata: bool,
    target_uri: str | None,
) -> str:
    if target_uri:
        return target_uri
    if project:
        return project_target_uri(project)
    if docs:
        return DOCS_TARGET_URI
    if metadata:
        return PROJECTS_TARGET_URI
    return PROJECTS_TARGET_URI


def run_find(client: Any, query: str, target_uri: str, limit: int):
    return client.find(query=query, target_uri=target_uri, limit=limit)


def format_find_text(result: Any) -> str:
    resources = list(getattr(result, "resources", []) or [])
    lines = [f"{len(resources)} result{'s' if len(resources) != 1 else ''}"]
    for index, resource in enumerate(resources, start=1):
        lines.extend(
            [
                "",
                f"{index}. {getattr(resource, 'uri', '')}",
                f"Score: {float(getattr(resource, 'score', 0.0)):.3f}",
                f"Abstract: {getattr(resource, 'abstract', '')}",
            ]
        )
        reason = getattr(resource, "match_reason", "")
        if reason:
            lines.append(f"Reason: {reason}")
    return "\n".join(lines)


def result_to_json(result: Any) -> str:
    resources = []
    for resource in list(getattr(result, "resources", []) or []):
        resources.append(
            {
                "uri": getattr(resource, "uri", ""),
                "score": getattr(resource, "score", None),
                "abstract": getattr(resource, "abstract", ""),
                "match_reason": getattr(resource, "match_reason", ""),
            }
        )
    return json.dumps({"resources": resources, "total": len(resources)}, indent=2)
```

- [ ] **Step 4: Run query tests**

Run:

```bash
PYTHONPATH=knowledge uv run --group knowledge pytest knowledge/tests/test_query.py -q
```

Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add knowledge/observatory_context/query.py knowledge/tests/test_query.py
git commit -m "feat: format OpenViking query results"
```

## Task 7: Thin CLI Scripts

**Files:**
- Create: `knowledge/scripts/ingest_context.py`
- Create: `knowledge/scripts/knowledge_query.py`
- Test: `knowledge/tests/test_cli.py`

- [ ] **Step 1: Write CLI parser tests**

Create `knowledge/tests/test_cli.py`:

```python
from knowledge.scripts.ingest_context import build_parser as build_ingest_parser
from knowledge.scripts.knowledge_query import build_parser as build_query_parser


def test_ingest_parser_accepts_project() -> None:
    args = build_ingest_parser().parse_args(["--project", "demo"])
    assert args.project == "demo"
    assert args.all is False


def test_query_parser_accepts_find_project_json() -> None:
    args = build_query_parser().parse_args(["find", "metal resistance", "--project", "demo", "--json"])
    assert args.command == "find"
    assert args.query == "metal resistance"
    assert args.project == "demo"
    assert args.json is True


def test_query_parser_accepts_overview_uri() -> None:
    args = build_query_parser().parse_args(["overview", "viking://resources/projects/demo/"])
    assert args.command == "overview"
    assert args.uri == "viking://resources/projects/demo/"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONPATH=knowledge:. uv run --group knowledge pytest knowledge/tests/test_cli.py -q
```

Expected: import failure for missing scripts.

- [ ] **Step 3: Implement ingestion CLI**

Create `knowledge/scripts/ingest_context.py`:

```python
from __future__ import annotations

import argparse

from observatory_context.config import ContextConfig
from observatory_context.ingest import ingest_all, ingest_changed, ingest_docs, ingest_project
from observatory_context.openviking_client import create_client


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest BERIL context into OpenViking")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--all", action="store_true", help="Ingest all selected projects and docs")
    mode.add_argument("--changed", action="store_true", help="Ingest selected sources changed since last manifest")
    mode.add_argument("--project", help="Ingest one project ID")
    mode.add_argument("--docs", action="store_true", help="Ingest selected central docs")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = ContextConfig.from_env()
    client = create_client(config)
    try:
        if args.all:
            ingest_all(config, client)
        elif args.changed:
            ingest_changed(config, client)
        elif args.project:
            ingest_project(config, client, args.project)
        elif args.docs:
            ingest_docs(config, client)
    finally:
        close = getattr(client, "close", None)
        if close:
            close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Implement query CLI**

Create `knowledge/scripts/knowledge_query.py`:

```python
from __future__ import annotations

import argparse

from observatory_context.config import ContextConfig
from observatory_context.openviking_client import create_client
from observatory_context.query import format_find_text, result_to_json, run_find, target_uri_for_find


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query BERIL OpenViking context")
    subparsers = parser.add_subparsers(dest="command", required=True)

    find = subparsers.add_parser("find")
    find.add_argument("query")
    find.add_argument("--project")
    find.add_argument("--docs", action="store_true")
    find.add_argument("--metadata", action="store_true")
    find.add_argument("--target-uri")
    find.add_argument("--limit", type=int, default=10)
    find.add_argument("--json", action="store_true")

    overview = subparsers.add_parser("overview")
    overview.add_argument("uri")

    read = subparsers.add_parser("read")
    read.add_argument("uri")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = ContextConfig.from_env()
    client = create_client(config)
    try:
        if args.command == "find":
            target_uri = target_uri_for_find(args.project, args.docs, args.metadata, args.target_uri)
            result = run_find(client, args.query, target_uri, args.limit)
            print(result_to_json(result) if args.json else format_find_text(result))
        elif args.command == "overview":
            print(client.overview(args.uri))
        elif args.command == "read":
            print(client.read(args.uri))
    finally:
        close = getattr(client, "close", None)
        if close:
            close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run CLI tests**

Run:

```bash
PYTHONPATH=knowledge:. uv run --group knowledge pytest knowledge/tests/test_cli.py -q
```

Expected: `3 passed`.

- [ ] **Step 6: Run all knowledge tests**

Run:

```bash
PYTHONPATH=knowledge:. uv run --group knowledge pytest knowledge/tests -q
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add knowledge/scripts/ingest_context.py knowledge/scripts/knowledge_query.py knowledge/tests/test_cli.py
git commit -m "feat: add knowledge context CLIs"
```

## Task 8: Claude Skills

**Files:**
- Create: `.claude/skills/knowledge-context/SKILL.md`
- Modify: `.claude/skills/pitfall-capture/SKILL.md`
- Modify: `.claude/skills/suggest-research/SKILL.md`
- Modify: `.claude/skills/synthesize/SKILL.md`

- [ ] **Step 1: Create knowledge-context skill**

Create `.claude/skills/knowledge-context/SKILL.md`:

```markdown
---
name: knowledge-context
description: Query or update the BERIL OpenViking knowledge context layer for project scientific context.
allowed-tools: Bash, Read
user-invocable: true
---

# Knowledge Context Skill

Use this skill when answering scientific or project-status questions that may depend on prior BERIL project reports, reviews, research plans, references, or central docs.

## Query

Use the thin wrapper:

```bash
PYTHONPATH=knowledge uv run --group knowledge python knowledge/scripts/knowledge_query.py find "<query>"
```

Scope to a project:

```bash
PYTHONPATH=knowledge uv run --group knowledge python knowledge/scripts/knowledge_query.py find "<query>" --project <project_id>
```

Query metadata such as author or status:

```bash
PYTHONPATH=knowledge uv run --group knowledge python knowledge/scripts/knowledge_query.py find "projects by <author>" --metadata
```

Load deeper context progressively:

```bash
PYTHONPATH=knowledge uv run --group knowledge python knowledge/scripts/knowledge_query.py overview viking://resources/projects/<project_id>/
PYTHONPATH=knowledge uv run --group knowledge python knowledge/scripts/knowledge_query.py read viking://resources/projects/<project_id>/REPORT.md
```

## Ingest

After changing project Markdown or `beril.yaml`, update that project:

```bash
PYTHONPATH=knowledge uv run --group knowledge python knowledge/scripts/ingest_context.py --project <project_id>
```

Scheduled update:

```bash
PYTHONPATH=knowledge uv run --group knowledge python knowledge/scripts/ingest_context.py --changed
```

Initial build:

```bash
PYTHONPATH=knowledge uv run --group knowledge python knowledge/scripts/ingest_context.py --all
```

## Configuration

The scripts connect to OpenViking through:

```bash
export OPENVIKING_URL=http://localhost:1933
```

For local OpenViking, copy `knowledge/openviking/ov.conf.example` to `knowledge/openviking/ov.conf`, add the OpenRouter API key, then run:

```bash
openviking-server doctor --config knowledge/openviking/ov.conf
openviking-server --config knowledge/openviking/ov.conf
uv run --group knowledge python knowledge/scripts/smoke_ingest_openviking.py
```
```

- [ ] **Step 2: Patch pitfall-capture integration note**

Append this paragraph near the "Integration" or "Important Notes" area in `.claude/skills/pitfall-capture/SKILL.md`:

```markdown
## Knowledge Context Integration

When a pitfall belongs to a specific project and that project has a durable documentation location, prefer adding or recommending the pitfall under `projects/{project_id}/` so the OpenViking context ingestion can keep project-local knowledge current. If there is no clear project context, continue using `docs/pitfalls.md`.
```

- [ ] **Step 3: Patch suggest-research integration note**

Add this bullet under `.claude/skills/suggest-research/SKILL.md` "Integration":

```markdown
- **May query**: `.claude/skills/knowledge-context/SKILL.md` / `knowledge/scripts/knowledge_query.py` for a quick OpenViking-backed scan of completed projects, authors, statuses, and central docs before falling back to manual file reads.
```

- [ ] **Step 4: Patch synthesize integration note**

Add this bullet under `.claude/skills/synthesize/SKILL.md` "Integration":

```markdown
- **After report updates**: run or suggest `PYTHONPATH=knowledge uv run --group knowledge python knowledge/scripts/ingest_context.py --project {project_id}` so OpenViking reflects the latest project findings.
```

- [ ] **Step 5: Verify skill files mention knowledge context**

Run:

```bash
rg -n "knowledge-context|OpenViking|ingest_context.py|knowledge_query.py" .claude/skills
```

Expected: matches in the new skill and the three updated skills.

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/knowledge-context/SKILL.md .claude/skills/pitfall-capture/SKILL.md .claude/skills/suggest-research/SKILL.md .claude/skills/synthesize/SKILL.md
git commit -m "docs: add knowledge context skill"
```

## Task 9: Final Verification And Smoke Documentation

**Files:**
- Modify: `docs/superpowers/specs/2026-05-01-openviking-context-layer-design.md` only if implementation revealed a mismatch.

- [ ] **Step 1: Run all knowledge tests**

Run:

```bash
PYTHONPATH=knowledge:. uv run --group knowledge pytest knowledge/tests -q
```

Expected: all tests pass.

- [ ] **Step 2: Run import checks**

Run:

```bash
PYTHONPATH=knowledge uv run --group knowledge python -c "from observatory_context.config import ContextConfig; print(ContextConfig.from_env().openviking_url)"
```

Expected:

```text
http://localhost:1933
```

- [ ] **Step 3: Run CLI help without OpenViking**

Run:

```bash
PYTHONPATH=knowledge uv run --group knowledge python knowledge/scripts/ingest_context.py --help
PYTHONPATH=knowledge uv run --group knowledge python knowledge/scripts/knowledge_query.py --help
```

Expected: both commands print help and exit successfully.

- [ ] **Step 4: Optional local OpenViking smoke test**

Only run this if a local OpenViking server is configured and running. The smoke
test ingests and queries the five most recently modified projects:

```bash
openviking-server doctor --config knowledge/openviking/ov.conf
openviking-server --config knowledge/openviking/ov.conf
export OPENVIKING_URL=http://localhost:1933
uv run --group knowledge python knowledge/scripts/smoke_ingest_openviking.py
PYTHONPATH=knowledge uv run --group knowledge python knowledge/scripts/ingest_context.py --project metal_cross_resistance
PYTHONPATH=knowledge uv run --group knowledge python knowledge/scripts/knowledge_query.py find "metal cross resistance" --project metal_cross_resistance
```

Expected:

```text
openviking-server doctor reports valid config
knowledge_query.py prints at least one result after processing completes
```

- [ ] **Step 5: Check generated files are ignored**

Run:

```bash
git status --short --ignored knowledge/staging knowledge/state
```

Expected: generated staging files and `knowledge/state/context_manifest.json` are ignored; `knowledge/state/.gitkeep` and `knowledge/state/.gitignore` remain tracked.

- [ ] **Step 6: Confirm no verification-only changes remain**

Run:

```bash
git status --short
```

Expected: no uncommitted changes unless the optional local OpenViking smoke test produced intentional local artifacts, which should be ignored.

## Self-Review

- Spec coverage: This plan covers OpenRouter `ov.conf`, curated file selection, central docs ingestion, generated metadata/index context, stable per-project target URIs, initial and incremental ingestion, query wrapper, Claude skills, dependency grouping, and tests that do not require a running OpenViking server.
- Placeholder scan: Passed; tasks contain concrete file paths, commands, and content.
- Type consistency: `ContextConfig`, URI helpers, metadata dataclass, manifest functions, staging functions, ingestion functions, and query helpers are introduced before they are used by later CLI tasks.
