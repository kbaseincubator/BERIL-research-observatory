"""Tests for the OpenViking runtime/bootstrap helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    _write(tmp_path / "docs" / "project_registry.yaml", "projects: []\n")
    _write(tmp_path / "docs" / "figure_catalog.yaml", "figures: []\n")
    _write(tmp_path / "config" / "openviking" / "ov.conf.example", '{\n  "server": {\n    "host": "127.0.0.1",\n    "port": 1933\n  }\n}\n')
    _write(tmp_path / "projects" / "alpha_proj" / "README.md", "# Alpha\n")
    _write(tmp_path / "projects" / "alpha_proj" / "REPORT.md", "# Report\n")
    _write(tmp_path / "projects" / "alpha_proj" / "provenance.yaml", "project_id: alpha_proj\n")
    _write(tmp_path / "knowledge" / "timeline.yaml", "events: []\n")
    return tmp_path


class FakeClient:
    def __init__(self, healthy: bool = True) -> None:
        self.healthy = healthy

    def health(self) -> bool:
        return self.healthy

    def get_status(self) -> dict[str, object]:
        return {"healthy": self.healthy}

    def list_resources(self, uri: str, recursive: bool = False) -> list[dict[str, object]]:
        return []


def test_build_service_supports_explicit_offline_mode(sample_repo: Path) -> None:
    from observatory_context.runtime import build_service

    service = build_service(sample_repo, offline=True)

    assert service.client is None
    assert service.repo_root == sample_repo


def test_build_service_fails_when_live_server_is_unhealthy(sample_repo: Path) -> None:
    from observatory_context.runtime import build_service

    with pytest.raises(RuntimeError, match="OpenViking server is not reachable"):
        build_service(sample_repo, offline=False, require_live=True, client=FakeClient(healthy=False))


def test_materialize_exports_uses_runtime_service_by_default(
    sample_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import viking_materialize_exports

    calls: list[tuple[Path, bool, bool]] = []

    class FakeService:
        pass

    def fake_build_service(repo_root: Path, offline: bool = False, require_live: bool = False):
        calls.append((repo_root, offline, require_live))
        return FakeService()

    monkeypatch.setattr(viking_materialize_exports.runtime, "build_service", fake_build_service)
    monkeypatch.setattr(viking_materialize_exports, "collect_project_ids", lambda repo_root: ["alpha_proj"])
    monkeypatch.setattr(
        viking_materialize_exports,
        "build_project_registry_export",
        lambda service, project_ids, generated_at: {"projects": []},
    )
    monkeypatch.setattr(
        viking_materialize_exports,
        "build_figure_catalog_export",
        lambda service, project_ids, generated_at: {"figures": []},
    )
    monkeypatch.setattr(
        viking_materialize_exports,
        "write_yaml_export",
        lambda path, payload: Path(path).write_text("ok\n", encoding="utf-8"),
    )

    assert (
        viking_materialize_exports.main(
            [
                "--repo-root",
                str(sample_repo),
                "--output-dir",
                str(tmp_path),
                "--generated-at",
                "2026-03-19T16:43:57",
            ]
        )
        == 0
    )
    assert calls == [(sample_repo, False, True)]


def test_materialize_overlays_supports_offline_flag(
    sample_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import viking_materialize_overlays

    calls: list[tuple[Path, bool, bool]] = []

    class FakeService:
        pass

    def fake_build_service(repo_root: Path, offline: bool = False, require_live: bool = False):
        calls.append((repo_root, offline, require_live))
        return FakeService()

    monkeypatch.setattr(viking_materialize_overlays.runtime, "build_service", fake_build_service)
    monkeypatch.setattr(viking_materialize_overlays, "build_raw_knowledge_overlays", lambda service: [])
    monkeypatch.setattr(viking_materialize_overlays, "write_overlay_documents", lambda output_dir, overlays: None)

    assert (
        viking_materialize_overlays.main(
            [
                "--repo-root",
                str(sample_repo),
                "--output-dir",
                str(tmp_path),
                "--offline",
            ]
        )
        == 0
    )
    assert calls == [(sample_repo, True, False)]


def test_setup_script_can_write_repo_config(
    sample_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import viking_setup

    monkeypatch.setattr(viking_setup.shutil, "which", lambda name: f"/usr/bin/{name}")

    config_path = sample_repo / "config" / "openviking" / "ov.conf"
    assert viking_setup.main(["--repo-root", str(sample_repo), "--write-config"]) == 0
    assert config_path.exists()


def test_setup_script_generates_valid_openai_config_from_shell_env(
    sample_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import viking_setup

    monkeypatch.setattr(viking_setup.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setenv("OPENAI_API_KEY", "shell-openai-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.delenv("OPENVIKING_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("OPENVIKING_VLM_MODEL", raising=False)

    config_path = sample_repo / "config" / "openviking" / "ov.conf"
    assert viking_setup.main(["--repo-root", str(sample_repo), "--write-config"]) == 0

    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert config["embedding"]["dense"]["provider"] == "openai"
    assert config["embedding"]["dense"]["api_key"] == "shell-openai-key"
    assert config["embedding"]["dense"]["api_base"] == "https://api.openai.com/v1"
    assert config["embedding"]["dense"]["model"] == "text-embedding-3-large"
    assert config["vlm"]["api_key"] == "shell-openai-key"
    assert config["vlm"]["model"] == "gpt-4o-mini"


def test_setup_script_uses_dotenv_when_shell_env_is_missing(
    sample_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import viking_setup

    monkeypatch.setattr(viking_setup.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENVIKING_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("OPENVIKING_VLM_MODEL", raising=False)

    _write(
        sample_repo / ".env",
        "OPENAI_API_KEY=dotenv-openai-key\n"
        "OPENAI_BASE_URL=https://example.test/v1\n"
        "OPENVIKING_EMBEDDING_MODEL=text-embedding-3-small\n"
        "OPENVIKING_VLM_MODEL=gpt-4.1-mini\n",
    )

    config_path = sample_repo / "config" / "openviking" / "ov.conf"
    assert viking_setup.main(["--repo-root", str(sample_repo), "--write-config"]) == 0

    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert config["embedding"]["dense"]["api_key"] == "dotenv-openai-key"
    assert config["embedding"]["dense"]["api_base"] == "https://example.test/v1"
    assert config["embedding"]["dense"]["model"] == "text-embedding-3-small"
    assert config["vlm"]["model"] == "gpt-4.1-mini"


def test_healthcheck_script_reports_server_state(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from scripts import viking_server_healthcheck

    monkeypatch.setattr(viking_server_healthcheck.runtime, "build_client", lambda: FakeClient(healthy=False))

    assert viking_server_healthcheck.main([]) == 1
    assert "FAIL: OpenViking server is not reachable." in capsys.readouterr().out
