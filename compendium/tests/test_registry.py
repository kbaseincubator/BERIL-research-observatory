from compendium.registry import Registry

RAW = {
    "topics": {"metal-resistance": {"label": "Metal Resistance & Critical Minerals",
                                     "definition": "x",
                                     "aliases": ["metal_fitness", "critical-minerals"],
                                     "projects": []}},
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


def test_resolves_topic_alias_to_canonical_key():
    # The reconcile pass maps many raw per-project topic slugs onto one canonical theme.
    reg = Registry(RAW)
    assert reg.topic_key("metal_fitness") == "metal-resistance"
    assert reg.topic_key("Critical-Minerals") == "metal-resistance"  # alias, case-insensitive


def test_registry_keeps_entity_definitions_and_urls(tmp_path):
    path = tmp_path / "registry.yaml"
    path.write_text(
        """
topics: {}
entities:
  adp1:
    label: Acinetobacter baylyi ADP1
    kind: organism
    definition: A naturally competent soil bacterium.
    aliases: [entity:adp1]
    url: https://example.org/adp1
""",
        encoding="utf-8",
    )

    registry = Registry.from_yaml(path)

    assert registry.entities["adp1"]["definition"] == "A naturally competent soil bacterium."
    assert registry.entities["adp1"]["url"] == "https://example.org/adp1"
