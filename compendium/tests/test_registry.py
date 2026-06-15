from compendium.registry import Registry

RAW = {
    "topics": {"metal-resistance": {"label": "Metal Resistance & Critical Minerals",
                                     "definition": "x", "projects": []}},
    "entities": {"adp1": {"label": "Acinetobacter baylyi ADP1", "kind": "organism",
                          "aliases": ["a_baylyi_adp1", "acinetobacter_baylyi", "adp1"]}},
}


def test_resolves_entity_alias_to_canonical_key():
    reg = Registry(RAW)
    assert reg.entity_key("a_baylyi_adp1") == "adp1"
    assert reg.entity_key("ADP1") == "adp1"            # case-insensitive
    assert reg.entity_key("unknown_x") == "unknown_x"  # unknown passes through unchanged


def test_resolves_topic_key():
    reg = Registry(RAW)
    assert reg.topic_key("metal-resistance") == "metal-resistance"
    assert reg.topic_key("Metal-Resistance") == "metal-resistance"  # case-insensitive
    assert reg.topic_key("unknown-topic") == "unknown-topic"        # passthrough
