"""Tests for deterministic synthesis quality dashboard artifacts."""

from __future__ import annotations

import json

from compendium.quality.synthesis_dashboard import (
    build_synthesis_quality_dashboard,
    render_synthesis_quality_dashboard_html,
)


def _metrics() -> dict[str, object]:
    return {
        "statement_counts": {
            "total": 6,
            "by_kind": {"opportunity": 2, "finding": 4},
            "by_tier": {"grounded": 5, "asserted": 1},
            "by_source_project": {"proj_b": 1, "proj_a": 5},
        },
        "evidence_resolution": {
            "checked": True,
            "total": 6,
            "resolved": 5,
            "unresolved": 1,
            "rate": 5 / 6,
            "unresolved_statement_ids": ["stmt:z"],
        },
        "topic_coverage": {
            "topic_count": 2,
            "topic_page_count": 1,
            "covered_topic_count": 1,
            "coverage_rate": 0.5,
            "topics_without_pages": ["topic:missing"],
            "topic_pages_without_statements": [],
            "statements_with_topics": 5,
            "statements_without_topics": ["stmt:z"],
            "topic_statement_counts": {"topic:b": 1, "topic:a": 4},
        },
        "claim_balance": {
            "total_claims": 2,
            "supported_claims": 1,
            "refuted_claims": 1,
            "unsupported_claim_statement_ids": ["stmt:unsupported"],
            "support_link_count": 2,
            "refutation_link_count": 1,
            "net_support_balance": 1,
            "claims": [
                {
                    "statement_id": "stmt:claim",
                    "support_count": 2,
                    "refutation_count": 1,
                    "supporting_statement_ids": ["stmt:a", "stmt:b"],
                    "refuting_statement_ids": ["stmt:z"],
                },
                {
                    "statement_id": "stmt:unsupported",
                    "support_count": 0,
                    "refutation_count": 0,
                    "supporting_statement_ids": [],
                    "refuting_statement_ids": [],
                },
            ],
        },
        "graph_integrity": {
            "node_count": 6,
            "edge_count": 7,
            "dangling_edges": 1,
            "dangling_edge_details": [
                {
                    "edge_id": "edge:z",
                    "source": "stmt:z",
                    "predicate": "supports",
                    "target": "stmt:missing",
                    "missing_endpoints": ["stmt:missing"],
                }
            ],
        },
        "page_integrity": {
            "page_count": 3,
            "pages_by_type": {"topic": 1, "home": 1, "claim": 1},
            "orphan_pages": ["topic:empty"],
            "weakly_connected_pages": [
                {"page_id": "claim:a", "link_degree": 1, "member_count": 1}
            ],
            "unknown_page_members": [
                {"page_id": "claim:a", "member_statement_id": "stmt:unknown"}
            ],
            "unknown_section_members": [
                {
                    "page_id": "claim:a",
                    "section_id": "main",
                    "member_statement_id": "stmt:unknown",
                }
            ],
            "statements_without_page_membership": ["stmt:z"],
        },
        "link_integrity": {
            "broken_outgoing_links": [
                {"page_id": "home", "target_page_id": "missing:page"}
            ],
            "broken_backlinks": [
                {"page_id": "claim:a", "source_page_id": "missing:source"}
            ],
            "missing_backlinks": [{"page_id": "home", "target_page_id": "claim:a"}],
            "stale_backlinks": [{"page_id": "claim:a", "source_page_id": "old"}],
            "broken_outgoing_link_count": 1,
            "broken_backlink_count": 1,
            "backlink_mismatch_count": 2,
        },
        "statement_link_integrity": {
            "unresolved_statement_link_count": 1,
            "unresolved_statement_links": [
                {
                    "source_statement_id": "stmt:z",
                    "link_kind": "supports",
                    "target_statement_id": "stmt:missing",
                }
            ],
        },
        "opportunity_targets": {
            "total": 2,
            "with_target_outputs": 1,
            "rate": 0.5,
            "opportunities": [
                {"statement_id": "stmt:opportunity", "target_outputs": ["dataset:a"]}
            ],
            "missing_target_output_statement_ids": ["stmt:missing_target"],
        },
        "active_conflicts": {
            "count": 2,
            "conflict_statement_ids": ["stmt:conflict"],
            "contradiction_links": [
                {"source_statement_id": "stmt:z", "target_statement_id": "stmt:conflict"}
            ],
        },
        "high_centrality_asserted_statements": [
            {"statement_id": "stmt:asserted_b", "degree": 2},
            {"statement_id": "stmt:asserted_a", "degree": 4},
        ],
        "synthesis_page_changes": {
            "available": True,
            "tracked_page_count": 2,
            "regenerated": 1,
            "changed": 1,
            "regenerated_page_ids": ["topic:a"],
            "changed_page_ids": ["claim:a"],
        },
    }


def test_synthesis_quality_dashboard_summarizes_metrics_and_review_records() -> None:
    records = [
        {
            "statement_id": "stmt:low",
            "score": 25,
            "reasons": ["low_confidence"],
            "kind": "finding",
            "tier": "grounded",
            "confidence": "low",
            "centrality_degree": 1,
            "statement": "needs review",
            "affected_pages": [{"page_id": "home"}],
            "contradictions": [],
            "unresolved_statement_links": [],
        },
        {
            "statement_id": "stmt:conflict",
            "score": 90,
            "reasons": ["conflict_status", "contradictions:1"],
            "kind": "conflict",
            "tier": "conflict",
            "confidence": "high",
            "centrality_degree": 3,
            "statement": "conflict statement",
            "affected_pages": [{"page_id": "home"}, {"page_id": "conflict:a"}],
            "contradictions": [{"source_statement_id": "stmt:z"}],
            "unresolved_statement_links": [{"source_statement_id": "stmt:z"}],
        },
    ]

    dashboard = build_synthesis_quality_dashboard(_metrics(), records, review_limit=1)

    assert dashboard["summary"] == {
        "statement_total": 6,
        "evidence_resolution_rate": 5 / 6,
        "topic_coverage_rate": 0.5,
        "unsupported_claim_count": 1,
        "opportunity_target_rate": 0.5,
        "active_conflict_count": 2,
        "high_centrality_asserted_statement_count": 2,
        "synthesis_pages_regenerated": 1,
        "synthesis_pages_changed": 1,
        "failure_counts": {
            "graph_dangling_edges": 1,
            "orphan_pages": 1,
            "weakly_connected_pages": 1,
            "unknown_page_members": 1,
            "unknown_section_members": 1,
            "statements_without_page_membership": 1,
            "broken_outgoing_links": 1,
            "broken_backlinks": 1,
            "backlink_mismatches": 2,
            "unresolved_statement_links": 1,
        },
    }
    assert dashboard["topic_coverage"]["topics_without_pages"] == ["topic:missing"]
    assert dashboard["claim_balance"]["unsupported_claim_statement_ids"] == [
        "stmt:unsupported"
    ]
    assert dashboard["failures"]["links"]["backlink_mismatch_count"] == 2
    assert dashboard["synthesis_page_changes"]["changed_page_ids"] == ["claim:a"]
    assert dashboard["opportunity_targets"]["with_target_outputs"] == 1
    assert dashboard["active_conflicts"]["conflict_statement_ids"] == ["stmt:conflict"]
    assert dashboard["high_centrality_asserted_statements"] == [
        {"degree": 4, "statement_id": "stmt:asserted_a"},
        {"degree": 2, "statement_id": "stmt:asserted_b"},
    ]
    assert dashboard["review_queue"] == {
        "total": 2,
        "highlight_count": 1,
        "highlights": [
            {
                "statement_id": "stmt:conflict",
                "score": 90,
                "reasons": ["conflict_status", "contradictions:1"],
                "kind": "conflict",
                "tier": "conflict",
                "confidence": "high",
                "centrality_degree": 3,
                "statement": "conflict statement",
                "affected_page_count": 2,
                "contradiction_count": 1,
                "unresolved_statement_link_count": 1,
            }
        ],
    }
    assert json.loads(json.dumps(dashboard, sort_keys=True)) == dashboard


def test_synthesis_quality_dashboard_html_is_static_and_escaped() -> None:
    records = [
        {
            "statement_id": "stmt:<unsafe>",
            "score": 10,
            "reasons": ["low_confidence"],
            "kind": "finding",
            "tier": "grounded",
            "confidence": "low",
            "centrality_degree": 0,
            "statement": "<script>alert(1)</script>",
            "affected_pages": [],
            "contradictions": [],
            "unresolved_statement_links": [],
        }
    ]

    html = render_synthesis_quality_dashboard_html(
        _metrics(),
        records,
        title="Synthesis <Quality>",
    )

    assert "<!doctype html>" in html
    assert "<style>" in html
    assert "http://" not in html
    assert "https://" not in html
    assert "Synthesis &lt;Quality&gt;" in html
    assert "stmt:&lt;unsafe&gt;" in html
    assert "<script>alert(1)</script>" not in html
