from pathlib import Path

import pytest

from compendium.data_index import (
    build_collection_index,
    cited_collections,
    load_canonical_ids,
)


def test_groups_projects_by_canonical_collection():
    cited = {
        "metal_fitness_atlas": {"kbase_ke_pangenome", "kescience_fitnessbrowser"},
        "amr_pangenome_atlas": {"kbase_ke_pangenome"},
    }
    canonical = {"kbase_ke_pangenome", "kescience_fitnessbrowser", "enigma_coral"}
    idx = build_collection_index(cited, canonical)
    assert sorted(idx["kbase_ke_pangenome"].projects) == ["amr_pangenome_atlas", "metal_fitness_atlas"]
    assert idx["kescience_fitnessbrowser"].projects == ["metal_fitness_atlas"]
    assert "enigma_coral" not in idx  # no project cites it -> omitted


def test_cited_collections_substring_scans_report_and_readme(tmp_path):
    project = tmp_path / "metal_fitness_atlas"
    project.mkdir()
    (project / "REPORT.md").write_text(
        "## Data\nWe joined `kbase_ke_pangenome` clusters to fitness data.\n",
        encoding="utf-8",
    )
    (project / "README.md").write_text(
        "Reuses `kescience_fitnessbrowser` cofitness scores.\n",
        encoding="utf-8",
    )
    canonical = {"kbase_ke_pangenome", "kescience_fitnessbrowser", "enigma_coral"}
    assert cited_collections(project, canonical) == {
        "kbase_ke_pangenome",
        "kescience_fitnessbrowser",
    }


def test_cited_collections_handles_missing_files(tmp_path):
    project = tmp_path / "empty_project"
    project.mkdir()
    assert cited_collections(project, {"kbase_ke_pangenome"}) == set()


def test_load_canonical_ids_from_corpus_collections_yaml():
    collections_yaml = Path(__file__).resolve().parents[2] / "ui/config/collections.yaml"
    if not collections_yaml.is_file():
        pytest.skip("corpus collections.yaml not present")
    canonical = load_canonical_ids(collections_yaml)
    assert len(canonical) >= 10
