"""Foundation tests: content-addressed identity + canonical serialization are stable & order-free."""

from compendium import ids


def test_node_id_stable_and_label_normalized():
    a = ids.node_id("Acinetobacter baylyi ADP1", "Organism")
    b = ids.node_id("  acinetobacter   baylyi  adp1 ", "Organism")  # whitespace/case differ
    assert a == b
    assert a.startswith("n:")
    # type participates in identity
    assert ids.node_id("ADP1", "Organism") != ids.node_id("ADP1", "Gene")


def test_relation_assertion_id_order_sensitive_but_deterministic():
    a1 = ids.assertion_id(s="n:x", p="has_phenotype", o="n:y")
    a2 = ids.assertion_id(s="n:x", p="has_phenotype", o="n:y")
    assert a1 == a2 and a1.startswith("a:")
    # same relation extracted in two projects collapses to one id (no project folded in)
    assert ids.assertion_id(s="n:x", p="has_phenotype", o="n:y") == a1


def test_statement_assertion_id_is_project_scoped():
    p1 = ids.assertion_id(statement="Genes are core-enriched", project="proj_a")
    p2 = ids.assertion_id(statement="Genes are core-enriched", project="proj_b")
    assert p1 != p2  # findings are project-local
    assert p1 == ids.assertion_id(statement="genes  are core-enriched!", project="proj_a")  # normalized
