"""Tests for the OpenViking ingest script."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from observatory_context.ingest.manifest import ResourceManifestItem


def _manifest_item(tmp_path: Path, name: str) -> ResourceManifestItem:
    source_path = tmp_path / name
    source_path.write_text(f"# {name}\n", encoding="utf-8")
    return ResourceManifestItem(
        uri=f"viking://resources/observatory/projects/{name}/authored/README.md",
        kind="project",
        source_path=str(source_path),
        project_ids=[name],
        metadata={"id": name, "kind": "project"},
    )


def test_ingest_skips_existing_resources_by_default(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    from scripts import viking_ingest

    existing = _manifest_item(tmp_path, "existing")
    missing = _manifest_item(tmp_path, "missing")
    calls: list[tuple[str, bool]] = []

    class FakeClient:
        def resource_exists(self, uri: str) -> bool:
            return uri == existing.uri

        def add_manifest_resource(self, item: ResourceManifestItem, wait: bool = True) -> None:
            calls.append((item.uri, wait))

        def wait_until_processed(self, timeout: float | None = None) -> None:
            raise AssertionError("wait_until_processed should not be called")

    monkeypatch.setattr(
        viking_ingest,
        "build_resource_manifest",
        lambda repo_root, project_ids=None: [existing, missing],
    )
    monkeypatch.setattr(viking_ingest, "OpenVikingObservatoryClient", lambda settings: FakeClient())
    monkeypatch.setattr(viking_ingest, "ObservatoryContextSettings", lambda: SimpleNamespace())

    assert viking_ingest.main([]) == 0

    assert calls == [(missing.uri, False)]
    output = capsys.readouterr().out
    assert f"Skipping existing {existing.uri}" in output
    assert f"Queued {missing.uri}" in output


def test_ingest_handles_wait_timeout_gracefully(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    from scripts import viking_ingest

    item = _manifest_item(tmp_path, "alpha")

    class FakeClient:
        def resource_exists(self, uri: str) -> bool:
            return False

        def add_manifest_resource(self, item: ResourceManifestItem, wait: bool = True) -> None:
            pass

        def wait_until_processed(self, timeout: float | None = None) -> None:
            raise TimeoutError("Timed out waiting for OpenViking to confirm processing. Resources were queued — processing may still be in progress.")

    monkeypatch.setattr(
        viking_ingest,
        "build_resource_manifest",
        lambda repo_root, project_ids=None: [item],
    )
    monkeypatch.setattr(viking_ingest, "OpenVikingObservatoryClient", lambda settings: FakeClient())
    monkeypatch.setattr(viking_ingest, "ObservatoryContextSettings", lambda: SimpleNamespace())

    assert viking_ingest.main(["--wait"]) == 0

    output = capsys.readouterr().out
    assert "Warning:" in output
    assert "healthcheck" in output


def test_ingest_waits_once_after_queueing_when_requested(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    from scripts import viking_ingest

    item = _manifest_item(tmp_path, "alpha")
    add_calls: list[tuple[str, bool]] = []
    wait_calls: list[float | None] = []

    class FakeClient:
        def resource_exists(self, uri: str) -> bool:
            return False

        def add_manifest_resource(self, item: ResourceManifestItem, wait: bool = True) -> None:
            add_calls.append((item.uri, wait))

        def wait_until_processed(self, timeout: float | None = None) -> None:
            wait_calls.append(timeout)

    monkeypatch.setattr(
        viking_ingest,
        "build_resource_manifest",
        lambda repo_root, project_ids=None: [item],
    )
    monkeypatch.setattr(viking_ingest, "OpenVikingObservatoryClient", lambda settings: FakeClient())
    monkeypatch.setattr(viking_ingest, "ObservatoryContextSettings", lambda: SimpleNamespace())

    assert viking_ingest.main(["--wait", "--wait-timeout", "900"]) == 0

    assert add_calls == [(item.uri, False)]
    assert wait_calls == [900.0]
    output = capsys.readouterr().out
    assert f"Queued {item.uri}" in output
    assert "Waiting for OpenViking processing to finish..." in output


def test_ingest_can_limit_to_specific_project_ids(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    from scripts import viking_ingest

    alpha = _manifest_item(tmp_path, "alpha_proj")
    beta = _manifest_item(tmp_path, "beta_proj")
    calls: list[str] = []

    class FakeClient:
        def resource_exists(self, uri: str) -> bool:
            return False

        def add_manifest_resource(self, item: ResourceManifestItem, wait: bool = True) -> None:
            calls.append(item.uri)

        def wait_until_processed(self, timeout: float | None = None) -> None:
            return None

    def fake_manifest(repo_root, project_ids=None):
        items = [alpha, beta]
        if project_ids:
            items = [item for item in items if project_ids.intersection(set(item.project_ids))]
        return items

    monkeypatch.setattr(viking_ingest, "build_resource_manifest", fake_manifest)
    monkeypatch.setattr(viking_ingest, "OpenVikingObservatoryClient", lambda settings: FakeClient())
    monkeypatch.setattr(viking_ingest, "ObservatoryContextSettings", lambda: SimpleNamespace())

    assert viking_ingest.main(["--project", "alpha_proj"]) == 0

    assert calls == [alpha.uri]
    output = capsys.readouterr().out
    assert f"Queued {alpha.uri}" in output
    assert beta.uri not in output
