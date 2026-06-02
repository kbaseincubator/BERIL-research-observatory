"""Transitional graph assembly for synthesis-wiki statement cards."""

from __future__ import annotations

import csv
import io
import json
import pathlib
import re
from collections.abc import Iterable
from typing import Any

from .. import ids
from ..models import EvidenceAnchor, StatementCard

GraphDict = dict[str, list[dict[str, Any]]]

_CURIE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*:[^\s:][^\s]*$")
_NON_ENTITY_CURIE_PREFIXES = {
    "conflict",
    "derived_product",
    "edge",
    "evidence",
    "figure",
    "notebook",
    "product",
    "project",
    "source_doc",
    "source_section",
    "statement",
    "stmt",
    "topic",
}
_ENTITY_QUALIFIER_KEYS = {
    "condition",
    "compound",
    "dataset",
    "enzyme",
    "environment",
    "function",
    "gene",
    "genes",
    "ko",
    "locus",
    "locus_tag",
    "metabolite",
    "organism",
    "ortholog",
    "ortholog_group",
    "pathway",
    "phenotype",
    "protein",
    "publication",
    "species",
    "strain",
    "substrate",
}


def build_statement_graph(cards: Iterable[StatementCard]) -> GraphDict:
    """Convert statement cards into a stable graph-like ``{"nodes", "edges"}`` dict.

    Statement cards are first-class nodes. Related entities, topics, evidence anchors, and
    unresolved statement-link targets are materialized as endpoint nodes so emitted edges do
    not dangle.
    """
    sorted_cards = sorted(cards, key=lambda c: c.id)
    entity_index = _build_entity_index(sorted_cards)
    conflicts = _explicit_conflicts(sorted_cards)

    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}

    def add_node(
        node_id: str,
        node_type: str,
        label: str | None = None,
        attrs: dict[str, Any] | None = None,
    ) -> None:
        existing = nodes.get(node_id)
        node = {
            "id": node_id,
            "type": node_type,
            "label": label or node_id,
            "attrs": _stable_attrs(attrs or {}),
        }
        if existing is None:
            nodes[node_id] = node
            return

        if existing["type"] == "statement_reference" and node_type == "statement_card":
            existing["type"] = node_type
            existing["label"] = node["label"]
        elif existing["label"] == existing["id"] and node["label"] != node["id"]:
            existing["label"] = node["label"]
        existing["attrs"] = _stable_attrs({**existing["attrs"], **node["attrs"]})

    def add_edge(
        source: str,
        predicate: str,
        target: str,
        edge_class: str,
        statement_id: str,
        provenance: str,
        attrs: dict[str, Any] | None = None,
    ) -> None:
        stable_attrs = _stable_attrs(attrs or {})
        edge_id = "edge:" + ids.content_hash(
            edge_class,
            source,
            predicate,
            target,
            _attrs_key(stable_attrs),
            n=16,
        )
        key = (source, predicate, target, edge_class, edge_id)
        existing = edges.get(key)
        if existing is None:
            edges[key] = {
                "id": edge_id,
                "s": source,
                "p": predicate,
                "o": target,
                "edge_class": edge_class,
                "statement_ids": [statement_id],
                "provenance": [provenance],
                "attrs": stable_attrs,
            }
            return

        if statement_id not in existing["statement_ids"]:
            existing["statement_ids"].append(statement_id)
            existing["statement_ids"].sort()
        if provenance and provenance not in existing["provenance"]:
            existing["provenance"].append(provenance)
            existing["provenance"].sort()

    for card in sorted_cards:
        source_project = card.evidence.source_project
        about_entities = sorted({_canonical_entity_id(entity_id) for entity_id in card.about.entities})
        qualifier_entities = sorted(_qualifier_entity_ids(card.qualifiers))
        original_about_entities = sorted(set(card.about.entities))
        qualifiers = _canonical_qualifiers(card.qualifiers)
        add_node(
            card.id,
            "statement_card",
            card.statement,
            {
                "kind": card.kind,
                "scope": card.scope,
                "tier": card.tier,
                "confidence": card.confidence,
                "statement": card.statement,
                "about": {
                    "entities": about_entities,
                    "topics": sorted(set(card.about.topics)),
                },
                "original_about": {
                    "entities": original_about_entities,
                },
                "qualifier_entities": qualifier_entities,
                "qualifiers": _stable_attrs(qualifiers),
                "original_qualifiers": _stable_attrs(card.qualifiers),
            },
        )

        for entity_id in sorted(set(about_entities + qualifier_entities)):
            entity_meta = entity_index.get(entity_id, _entity_metadata(entity_id, {entity_id}))
            add_node(entity_id, "entity", entity_meta["label"], entity_meta["attrs"])
            add_edge(
                card.id,
                "about_entity",
                entity_id,
                "navigation_edge",
                card.id,
                source_project,
            )

        for topic_id in sorted(set(card.about.topics)):
            add_node(topic_id, "topic")
            add_edge(
                card.id,
                "member_of_topic",
                topic_id,
                "navigation_edge",
                card.id,
                source_project,
            )

        for link_kind in ("supports", "contradicts", "motivates", "refines"):
            for target_id in sorted(set(getattr(card.links, link_kind))):
                add_node(target_id, "statement_reference")
                edge_attrs = None
                if link_kind == "contradicts":
                    edge_attrs = {"conflict_id": _conflict_node_id(card.id, target_id)}
                add_edge(
                    card.id,
                    link_kind,
                    target_id,
                    "scientific_edge",
                    card.id,
                    source_project,
                    edge_attrs,
                )

        for target_id in sorted(set(card.links.requires_validation)):
            add_node(target_id, "statement_reference")
            add_edge(
                card.id,
                "needs_review",
                target_id,
                "review_edge",
                card.id,
                source_project,
                {"link_kind": "requires_validation"},
            )

        _add_evidence_subgraph(card, add_node, add_edge)

    for conflict_id in sorted(conflicts):
        conflict = conflicts[conflict_id]
        statement_ids = conflict["statement_ids"]
        links = conflict["contradiction_links"]
        add_node(
            conflict_id,
            "conflict",
            f"Explicit contradiction: {' <-> '.join(statement_ids)}",
            {
                "kind": "explicit_contradiction",
                "statement_ids": statement_ids,
                "contradiction_links": links,
                "requires_review": True,
            },
        )
        for statement_id in statement_ids:
            add_node(statement_id, "statement_reference")
        for link in links:
            source_id = link["source_statement_id"]
            target_id = link["target_statement_id"]
            source_project = link["source_project"]
            for statement_id in sorted({source_id, target_id}):
                add_edge(
                    statement_id,
                    "needs_review",
                    conflict_id,
                    "review_edge",
                    source_id,
                    source_project,
                    {
                        "conflict_id": conflict_id,
                        "review_reason": "explicit_contradiction",
                    },
                )

    return {
        "nodes": [nodes[node_id] for node_id in sorted(nodes)],
        "edges": [
            edges[key]
            for key in sorted(
                edges,
                key=lambda x: (x[0], x[1], x[2], x[3], x[4]),
            )
        ],
    }


def canonical_statement_graph(graph: GraphDict) -> GraphDict:
    """Return a deterministically sorted v4 statement graph dict."""
    nodes = [_canonical_value(node) for node in graph.get("nodes", [])]
    edges = [_canonical_value(edge) for edge in graph.get("edges", [])]
    return {
        "nodes": sorted(nodes, key=_node_sort_key),
        "edges": sorted(edges, key=_edge_sort_key),
    }


def export_statement_graph_artifacts(graph: GraphDict, out_dir: pathlib.Path | str) -> None:
    """Write deterministic ``graph.json``, ``nodes.tsv``, and ``edges.tsv`` artifacts."""
    out_path = pathlib.Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    sorted_graph = canonical_statement_graph(graph)
    (out_path / "graph.json").write_text(
        json.dumps(sorted_graph, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_path / "nodes.tsv").write_text(_nodes_tsv(sorted_graph["nodes"]), encoding="utf-8")
    (out_path / "edges.tsv").write_text(_edges_tsv(sorted_graph["edges"]), encoding="utf-8")


def _add_evidence_subgraph(
    card: StatementCard,
    add_node: Any,
    add_edge: Any,
) -> None:
    evidence = card.evidence
    source_project_id = _source_project_node_id(evidence.source_project)
    source_doc_id = _source_doc_node_id(evidence)
    evidence_id = _evidence_node_id(evidence)

    add_node(
        evidence_id,
        "evidence_anchor",
        evidence.exact,
        {
            "source_project": evidence.source_project,
            "source_doc": evidence.source_doc,
            "source_section": evidence.source_section,
            "exact": evidence.exact,
            "prefix": evidence.prefix,
            "suffix": evidence.suffix,
            "notebook": evidence.notebook,
            "figure": evidence.figure,
            "p_value": evidence.p_value,
        },
    )
    add_node(source_project_id, "project", evidence.source_project)
    add_node(source_doc_id, "source_doc", evidence.source_doc)

    add_edge(
        card.id,
        "has_evidence",
        evidence_id,
        "provenance_edge",
        card.id,
        evidence.source_project,
    )
    add_edge(
        evidence_id,
        "extracted_from",
        source_project_id,
        "provenance_edge",
        card.id,
        evidence.source_project,
    )
    add_edge(
        evidence_id,
        "extracted_from",
        source_doc_id,
        "provenance_edge",
        card.id,
        evidence.source_project,
    )

    if evidence.source_section:
        source_section_id = _source_section_node_id(evidence)
        add_node(source_section_id, "source_section", evidence.source_section)
        add_edge(
            evidence_id,
            "extracted_from",
            source_section_id,
            "provenance_edge",
            card.id,
            evidence.source_project,
        )

    if evidence.notebook:
        notebook_id = f"notebook:{evidence.source_project}:{evidence.notebook}"
        add_node(notebook_id, "notebook", evidence.notebook)
        add_edge(
            evidence_id,
            "uses_notebook",
            notebook_id,
            "provenance_edge",
            card.id,
            evidence.source_project,
        )

    if evidence.figure:
        figure_id = f"figure:{evidence.source_project}:{evidence.figure}"
        add_node(figure_id, "figure", evidence.figure)
        add_edge(
            evidence_id,
            "cites",
            figure_id,
            "provenance_edge",
            card.id,
            evidence.source_project,
        )


def _evidence_node_id(evidence: EvidenceAnchor) -> str:
    return "evidence:" + ids.content_hash(
        evidence.source_project,
        evidence.source_doc,
        evidence.source_section or "",
        evidence.exact,
        evidence.prefix,
        evidence.suffix,
        n=16,
    )


def _source_project_node_id(source_project: str) -> str:
    return f"project:{source_project}"


def _source_doc_node_id(evidence: EvidenceAnchor) -> str:
    return f"source_doc:{evidence.source_project}:{evidence.source_doc}"


def _source_section_node_id(evidence: EvidenceAnchor) -> str:
    return f"source_section:{evidence.source_project}:{evidence.source_doc}:{evidence.source_section}"


def _build_entity_index(cards: list[StatementCard]) -> dict[str, dict[str, Any]]:
    aliases_by_id: dict[str, set[str]] = {}
    original_ids_by_id: dict[str, set[str]] = {}
    labels_by_id: dict[str, set[str]] = {}
    curies_by_id: dict[str, set[str]] = {}

    for card in cards:
        for entity_id in card.about.entities:
            canonical_id = _canonical_entity_id(entity_id)
            aliases_by_id.setdefault(canonical_id, set()).add(entity_id)
            original_ids_by_id.setdefault(canonical_id, set()).add(entity_id)
            label = _entity_label(entity_id)
            if label:
                labels_by_id.setdefault(canonical_id, set()).add(label)
            curie = _entity_curie(entity_id)
            if curie:
                curies_by_id.setdefault(canonical_id, set()).add(curie)

        for value in _entity_qualifier_values(card.qualifiers):
            canonical_id = _canonical_entity_id(value)
            aliases_by_id.setdefault(canonical_id, set()).add(value)
            label = _entity_label(value)
            if label:
                labels_by_id.setdefault(canonical_id, set()).add(label)
            curie = _entity_curie(value)
            if curie:
                curies_by_id.setdefault(canonical_id, set()).add(curie)

    return {
        canonical_id: _entity_metadata(
            canonical_id,
            aliases,
            original_ids_by_id.get(canonical_id, set()),
            labels_by_id.get(canonical_id, set()),
            curies_by_id.get(canonical_id, set()),
        )
        for canonical_id, aliases in aliases_by_id.items()
    }


def _entity_metadata(
    canonical_id: str,
    aliases: set[str],
    original_ids: set[str] | None = None,
    labels: set[str] | None = None,
    curies: set[str] | None = None,
) -> dict[str, Any]:
    label = _canonical_entity_label(canonical_id, labels or set())
    attrs: dict[str, Any] = {
        "aliases": sorted(aliases),
        "canonical_id": canonical_id,
        "original_ids": sorted(original_ids or aliases),
    }
    if curies:
        attrs["curies"] = sorted(curies)
    return {"label": label, "attrs": attrs}


def _canonical_entity_id(entity_ref: str) -> str:
    value = entity_ref.strip()
    if value.startswith("entity:"):
        value = value.removeprefix("entity:").strip()
    if _is_curie_like(value):
        prefix, identifier = value.split(":", 1)
        return f"entity:{prefix.strip().lower()}:{_entity_slug(identifier)}"
    return f"entity:{_entity_slug(value)}"


def _canonical_qualifiers(qualifiers: dict[str, str]) -> dict[str, str]:
    return {
        key: _canonical_entity_id(value) if _qualifier_value_is_entity(key, value) else value
        for key, value in qualifiers.items()
    }


def _qualifier_entity_ids(qualifiers: dict[str, str]) -> set[str]:
    return {_canonical_entity_id(value) for value in _entity_qualifier_values(qualifiers)}


def _entity_qualifier_values(qualifiers: dict[str, str]) -> list[str]:
    return [
        value
        for key, value in qualifiers.items()
        if _qualifier_value_is_entity(key, value)
    ]


def _qualifier_value_is_entity(key: str, value: str) -> bool:
    if not value:
        return False
    if value.strip().startswith("entity:"):
        return True
    if _is_curie_like(value):
        return value.split(":", 1)[0].lower() not in _NON_ENTITY_CURIE_PREFIXES
    normalized_key = key.lower().replace("-", "_")
    return normalized_key in _ENTITY_QUALIFIER_KEYS


def _is_curie_like(value: str) -> bool:
    return bool(_CURIE_RE.match(value.strip()))


def _entity_slug(value: str) -> str:
    normalized = ids.normalize(value)
    return normalized.replace(" ", "-")


def _entity_label(entity_ref: str) -> str | None:
    value = entity_ref.strip()
    if not value:
        return None
    if value.startswith("entity:"):
        return None
    if _is_curie_like(value):
        return value
    return value


def _entity_curie(entity_ref: str) -> str | None:
    value = entity_ref.strip()
    if value.startswith("entity:"):
        value = value.removeprefix("entity:").strip()
    if not _is_curie_like(value):
        return None
    prefix, identifier = value.split(":", 1)
    return f"{prefix.strip()}:{identifier.strip()}"


def _canonical_entity_label(canonical_id: str, labels: set[str]) -> str:
    if labels:
        return sorted(labels, key=lambda value: (ids.normalize(value), value))[0]
    return canonical_id


def _explicit_conflicts(cards: list[StatementCard]) -> dict[str, dict[str, Any]]:
    conflicts: dict[str, dict[str, Any]] = {}
    for card in cards:
        for target_id in sorted(set(card.links.contradicts)):
            conflict_id = _conflict_node_id(card.id, target_id)
            pair = sorted({card.id, target_id})
            conflict = conflicts.setdefault(
                conflict_id,
                {
                    "statement_ids": pair,
                    "contradiction_links": [],
                },
            )
            conflict["contradiction_links"].append(
                {
                    "source_project": card.evidence.source_project,
                    "source_statement_id": card.id,
                    "target_statement_id": target_id,
                }
            )

    for conflict in conflicts.values():
        conflict["contradiction_links"].sort(
            key=lambda link: (
                link["source_statement_id"],
                link["target_statement_id"],
                link["source_project"],
            )
        )
    return conflicts


def _conflict_node_id(source_id: str, target_id: str) -> str:
    pair = sorted({source_id, target_id})
    return "conflict:" + ids.content_hash("explicit_contradiction", *pair, n=16)


def _stable_attrs(attrs: dict[str, Any]) -> dict[str, Any]:
    return {key: attrs[key] for key in sorted(attrs)}


def _attrs_key(attrs: dict[str, Any]) -> str:
    parts = []
    for key in sorted(attrs):
        parts.append(f"{key}={attrs[key]}")
    return "|".join(parts)


def _canonical_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _canonical_value(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_canonical_value(item) for item in value]
    return value


def _node_sort_key(node: dict[str, Any]) -> tuple[str, str, str]:
    return (str(node.get("id", "")), str(node.get("type", "")), str(node.get("label", "")))


def _edge_sort_key(edge: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(edge.get("s", "")),
        str(edge.get("p", "")),
        str(edge.get("o", "")),
        str(edge.get("edge_class", "")),
        str(edge.get("id", "")),
    )


def _nodes_tsv(nodes: list[dict[str, Any]]) -> str:
    return _tsv_text(
        ["id", "type", "label", "attrs"],
        [
            [
                _tsv_value(node.get("id", "")),
                _tsv_value(node.get("type", "")),
                _tsv_value(node.get("label", "")),
                _tsv_value(node.get("attrs", {})),
            ]
            for node in nodes
        ],
    )


def _edges_tsv(edges: list[dict[str, Any]]) -> str:
    return _tsv_text(
        ["id", "s", "p", "o", "edge_class", "statement_ids", "provenance", "attrs"],
        [
            [
                _tsv_value(edge.get("id", "")),
                _tsv_value(edge.get("s", "")),
                _tsv_value(edge.get("p", "")),
                _tsv_value(edge.get("o", "")),
                _tsv_value(edge.get("edge_class", "")),
                _tsv_value(edge.get("statement_ids", [])),
                _tsv_value(edge.get("provenance", [])),
                _tsv_value(edge.get("attrs", {})),
            ]
            for edge in edges
        ],
    )


def _tsv_text(headers: list[str], rows: list[list[str]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, delimiter="\t", lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(rows)
    return output.getvalue()


def _tsv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "|".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(_canonical_value(value), sort_keys=True, separators=(",", ":"))
    return str(value)
