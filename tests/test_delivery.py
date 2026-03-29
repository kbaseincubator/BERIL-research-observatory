"""Essential tests for the ContextDelivery service layer."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from observatory_context.delivery import ContextDelivery
from observatory_context.models import ContextItem, Scope, SearchResults, Tier


@pytest.fixture()
def mock_client():
    return MagicMock()


@pytest.fixture()
def delivery(mock_client):
    return ContextDelivery(client=mock_client)


def _make_search_hit(uri: str, title: str = "Hit") -> dict:
    return {
        "uri": uri,
        "title": title,
        "score": 0.9,
        "metadata": {"kind": "report"},
    }


# --- search ---


def test_search_returns_search_results(delivery, mock_client):
    mock_client.search.return_value = [
        _make_search_hit("viking://resources/observatory/projects/p1/report.md"),
    ]
    mock_client.read_resource.return_value = "---\ntitle: Hit\nkind: report\n---\n\nBody text"

    result = delivery.search("test query")

    assert isinstance(result, SearchResults)
    assert result.query == "test query"
    assert len(result.items) >= 1
    mock_client.search.assert_called_once()


def test_search_with_scope_memory(delivery, mock_client):
    mock_client.search.return_value = []
    delivery.search("test", scope=Scope.memory)
    _, kwargs = mock_client.search.call_args
    assert "memories" in kwargs.get("target_uri", "")


# --- get ---


def test_get_at_tier_l0(delivery, mock_client):
    mock_client.read_resource.side_effect = [
        "L0 abstract text",  # .abstract.md found at parent
    ]
    mock_client.resource_exists.side_effect = [False, True]

    item = delivery.get("viking://resources/observatory/projects/p1/doc.md", tier=Tier.L0)
    assert item.tier == Tier.L0


def test_browse_returns_list(delivery, mock_client):
    mock_client.list_resources.return_value = [
        {"uri": "viking://resources/observatory/kg/entities/organisms/ecoli", "name": "ecoli"},
        {"uri": "viking://resources/observatory/kg/entities/organisms/yeast", "name": "yeast"},
    ]
    mock_client.read_resource.return_value = "---\ntitle: Entity\nkind: entity\n---\n\nProfile"
    mock_client.resource_exists.return_value = False

    items = delivery.browse("viking://resources/observatory/kg/entities/organisms")
    assert isinstance(items, list)
    assert all(isinstance(i, ContextItem) for i in items)


# --- traverse ---


def test_traverse_reads_relation_fields_from_yaml_body(delivery, mock_client):
    entity_uri = "viking://resources/observatory/knowledge-graph/entities/organisms/ecoli"
    relation_uri = f"{entity_uri}/relations/regulates__genes__trpA.yaml"
    target_uri = "viking://resources/observatory/knowledge-graph/entities/genes/trpA"

    mock_client.resource_exists.return_value = False
    mock_client.list_resources.return_value = [{"uri": relation_uri, "name": "regulates__genes__trpA.yaml"}]
    mock_client.read_resource.side_effect = [
        "---\ntitle: E. coli\nkind: entity\n---\n\nProfile",
        "---\nkind: relation\n---\n\n"
        "subject: organisms/ecoli\n"
        "predicate: regulates\n"
        "object: genes/trpA\n"
        "evidence: paper\n"
        "confidence: high\n",
        "---\ntitle: trpA\nkind: entity\n---\n\nGene profile",
    ]

    result = delivery.traverse(entity_uri)

    assert [edge.object_uri for edge in result.relations] == [target_uri]
    assert [item.uri for item in result.connected] == [target_uri]


def test_traverse_supports_multiple_hops(delivery, mock_client):
    root_uri = "viking://resources/observatory/knowledge-graph/entities/organisms/ecoli"
    gene_uri = "viking://resources/observatory/knowledge-graph/entities/genes/trpA"
    pathway_uri = (
        "viking://resources/observatory/knowledge-graph/entities/pathways/tryptophan-biosynthesis"
    )
    relation_one_uri = f"{root_uri}/relations/regulates__genes__trpA.yaml"
    relation_two_uri = f"{gene_uri}/relations/participates_in__pathways__tryptophan-biosynthesis.yaml"

    mock_client.resource_exists.return_value = False

    def list_resources(uri, recursive=False):
        if uri == f"{root_uri}/relations":
            return [{"uri": relation_one_uri, "name": "regulates__genes__trpA.yaml"}]
        if uri == f"{gene_uri}/relations":
            return [
                {
                    "uri": relation_two_uri,
                    "name": "participates_in__pathways__tryptophan-biosynthesis.yaml",
                }
            ]
        return []

    def read_resource(uri):
        contents = {
            root_uri: "---\ntitle: E. coli\nkind: entity\n---\n\nProfile",
            relation_one_uri: (
                "---\npredicate: regulates\nobject: genes/trpA\nevidence: paper\nconfidence: high\n---\n"
            ),
            gene_uri: "---\ntitle: trpA\nkind: entity\n---\n\nGene profile",
            relation_two_uri: (
                "---\npredicate: participates_in\n"
                "object: pathways/tryptophan-biosynthesis\nevidence: pathway db\nconfidence: moderate\n---\n"
            ),
            pathway_uri: "---\ntitle: Tryptophan Biosynthesis\nkind: entity\n---\n\nPathway profile",
        }
        return contents[uri]

    mock_client.list_resources.side_effect = list_resources
    mock_client.read_resource.side_effect = read_resource

    result = delivery.traverse(root_uri, hops=2)

    assert [item.uri for item in result.connected] == [gene_uri, pathway_uri]
    assert [edge.object_uri for edge in result.relations] == [gene_uri, pathway_uri]


def test_remember_calls_add_text_resource(delivery, mock_client):
    mock_client.add_text_resource.return_value = {}

    uri = delivery.remember(
        store="journal",
        title="Test Memory",
        body="Some content",
        tags=["tag1"],
    )

    assert "memories" in uri
    assert "research-journal" in uri
    mock_client.add_text_resource.assert_called_once()
    # Verify reason parameter is passed
    args = mock_client.add_text_resource.call_args
    # reason is the 4th positional arg (uri, content, metadata, reason)
    assert args[1].get("reason") or (len(args[0]) >= 4 and args[0][3])


def test_recall_searches_with_memory_prefix(delivery, mock_client):
    mock_client.search.return_value = []
    delivery.recall("test query")
    _, kwargs = mock_client.search.call_args
    assert "memories" in kwargs.get("target_uri", "")


def test_entities_calls_browse_correct_uri(delivery, mock_client):
    mock_client.list_resources.return_value = []
    delivery.entities(entity_type="organism")
    mock_client.list_resources.assert_called_once()
    call_args = mock_client.list_resources.call_args
    assert "organisms" in call_args[0][0]


def test_ingest_entity_creates_profile_and_relations(delivery, mock_client):
    mock_client.add_text_resource.return_value = {}
    mock_client.make_directory.return_value = None

    relations = [
        {
            "subject": "organisms/ecoli",
            "predicate": "regulates",
            "object": "genes/trpA",
            "evidence": "paper",
            "confidence": "high",
        }
    ]

    uri = delivery.ingest_entity(
        entity_type="organism",
        entity_id="ecoli",
        profile={"name": "E. coli", "description": "Model organism"},
        relations=relations,
    )

    assert "organisms/ecoli" in uri
    # At least profile + 1 relation + 1 inverse relation
    assert mock_client.add_text_resource.call_count >= 2
