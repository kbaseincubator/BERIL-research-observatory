from pathlib import Path

import pytest

from compendium.data_index import build_collection_index, load_canonical_ids


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


def test_load_canonical_ids_from_corpus_collections_yaml():
    collections_yaml = Path(__file__).resolve().parents[2] / "ui/config/collections.yaml"
    if not collections_yaml.is_file():
        pytest.skip("corpus collections.yaml not present")
    canonical = load_canonical_ids(collections_yaml)
    assert len(canonical) >= 10
