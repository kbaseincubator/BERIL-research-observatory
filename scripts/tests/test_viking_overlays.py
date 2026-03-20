"""Tests for deterministic overlay materialization."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
import yaml

from observatory_context.ingest.manifest import build_resource_manifest
from observatory_context.service import ObservatoryContextService


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class FakeLiveClient:
    def __init__(self) -> None:
        self.resources: dict[str, dict[str, object]] = {}

    def seed_manifest_resource(
        self,
        source_path: Path,
        uri: str,
        metadata: dict[str, object],
        kind: str,
        body: str | None = None,
    ) -> None:
        if body is None:
            body = source_path.read_text(encoding="utf-8") if kind != "figure" else "Figure resource\n"
        front_matter = yaml.safe_dump(metadata, sort_keys=True).strip()
        content = f"---\n{front_matter}\n---\n\n{body.strip()}\n"
        self.resources[uri] = {"content": content, "metadata": dict(metadata)}

    def list_resources(self, uri: str, recursive: bool = False) -> list[dict[str, object]]:
        prefix = uri.rstrip("/")
        return [{"uri": resource_uri} for resource_uri in sorted(self.resources) if recursive and resource_uri.startswith(prefix)]

    def read_resource(self, uri: str) -> str:
        return str(self.resources[uri]["content"])

    def stat_resource(self, uri: str) -> dict[str, object]:
        return {"uri": uri, "metadata": self.resources[uri]["metadata"]}


def _seed_live_resources(
    sample_repo: Path,
    mutate: Callable[[object, dict[str, object]], tuple[dict[str, object], str | None]] | None = None,
) -> FakeLiveClient:
    client = FakeLiveClient()
    for item in build_resource_manifest(sample_repo):
        metadata = dict(item.metadata)
        body = None
        if mutate is not None:
            metadata, body = mutate(item, metadata)
        client.seed_manifest_resource(Path(item.source_path), item.uri, metadata, item.kind, body=body)
    return client


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    _write(tmp_path / "docs" / "project_registry.yaml", "projects: []\n")
    _write(tmp_path / "docs" / "figure_catalog.yaml", "figures: []\n")

    _write(
        tmp_path / "projects" / "alpha_proj" / "README.md",
        "# Alpha Project\n\nQuestion: How does alpha respond?\n",
    )
    _write(tmp_path / "projects" / "alpha_proj" / "REPORT.md", "# Alpha Report\n")
    _write(
        tmp_path / "projects" / "alpha_proj" / "provenance.yaml",
        "project_id: alpha_proj\n",
    )

    _write(
        tmp_path / "knowledge" / "entities" / "genes.yaml",
        """
genes:
  - id: gene_beta
    name: Beta gene
  - id: gene_alpha
    name: Alpha gene
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "knowledge" / "relations.yaml",
        """
relations:
  - subject: gene_alpha
    predicate: interacts_with
    object: gene_beta
    evidence_project: alpha_proj
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "knowledge" / "timeline.yaml",
        """
events:
  - date: "2026-03-19"
    type: discovery
    project: alpha_proj
    summary: Alpha discovery
""".strip()
        + "\n",
    )
    return tmp_path


@pytest.fixture
def service(sample_repo: Path) -> ObservatoryContextService:
    return ObservatoryContextService(repo_root=sample_repo, client=None)


def test_build_raw_knowledge_overlays_from_service(
    service: ObservatoryContextService,
) -> None:
    from observatory_context.overlays import build_raw_knowledge_overlays

    overlays = build_raw_knowledge_overlays(service)

    assert [overlay.relative_path for overlay in overlays] == [
        "entities/genes.yaml",
        "relations.yaml",
        "timeline.yaml",
    ]
    assert overlays[0].uri.endswith("/overlays/raw-knowledge/entities/genes.yaml")
    assert overlays[0].payload == {
        "genes": [
            {"id": "gene_beta", "name": "Beta gene"},
            {"id": "gene_alpha", "name": "Alpha gene"},
        ]
    }


def test_overlay_serialization_is_deterministic(service: ObservatoryContextService) -> None:
    from observatory_context.overlays import build_raw_knowledge_overlays, dump_overlay_yaml

    overlays = build_raw_knowledge_overlays(service)

    first_pass = [(overlay.relative_path, dump_overlay_yaml(overlay.payload)) for overlay in overlays]
    second_pass = [
        (overlay.relative_path, dump_overlay_yaml(overlay.payload))
        for overlay in reversed(build_raw_knowledge_overlays(service))
    ]

    assert first_pass == second_pass[::-1]


def test_build_raw_knowledge_overlays_prefers_live_server_resources(sample_repo: Path) -> None:
    from observatory_context.overlays import build_raw_knowledge_overlays

    def mutate(item, metadata):
        if item.uri.endswith("/overlays/raw-knowledge/entities/genes.yaml"):
            body = """
genes:
  - id: gene_live
    name: Live gene
""".strip()
            return metadata, body
        return metadata, None

    service = ObservatoryContextService(repo_root=sample_repo, client=_seed_live_resources(sample_repo, mutate=mutate))
    overlays = build_raw_knowledge_overlays(service)

    assert overlays[0].payload == {"genes": [{"id": "gene_live", "name": "Live gene"}]}


def test_missing_required_overlay_metadata_fails(service: ObservatoryContextService) -> None:
    from observatory_context.overlays import OverlayMaterializationError, build_raw_knowledge_overlays

    resource = next(
        resource
        for resource in service._all_resources().values()
        if resource.uri.endswith("/overlays/raw-knowledge/entities/genes.yaml")
    )
    resource.metadata.pop("overlay_relative_path", None)

    with pytest.raises(
        OverlayMaterializationError,
        match="missing overlay_relative_path metadata",
    ):
        build_raw_knowledge_overlays(service)


def test_materialize_and_validate_overlay_outputs(
    sample_repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from scripts.viking_materialize_overlays import main as materialize_main
    from scripts.viking_validate_overlays import main as validate_main

    output_dir = tmp_path / "generated"

    assert materialize_main(
        [
            "--repo-root",
            str(sample_repo),
            "--output-dir",
            str(output_dir),
            "--offline",
        ]
    ) == 0
    assert (output_dir / "entities" / "genes.yaml").exists()
    assert yaml.safe_load((output_dir / "timeline.yaml").read_text(encoding="utf-8")) == {
        "events": [
            {
                "date": "2026-03-19",
                "project": "alpha_proj",
                "summary": "Alpha discovery",
                "type": "discovery",
            }
        ]
    }

    assert validate_main(
        [
            "--repo-root",
            str(sample_repo),
            "--generated-dir",
            str(output_dir),
            "--offline",
        ]
    ) == 0
    assert "PASS: generated overlays match tracked knowledge outputs." in capsys.readouterr().out

    (output_dir / "relations.yaml").write_text("relations: []\n", encoding="utf-8")

    assert validate_main(
        [
            "--repo-root",
            str(sample_repo),
            "--generated-dir",
            str(output_dir),
            "--offline",
        ]
    ) == 1
    assert "relations.yaml does not match tracked output" in capsys.readouterr().out
