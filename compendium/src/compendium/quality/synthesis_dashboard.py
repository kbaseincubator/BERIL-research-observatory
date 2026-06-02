"""Dashboard artifacts for deterministic synthesis quality metrics."""

from __future__ import annotations

import html
import json
from collections.abc import Iterable, Mapping
from typing import Any

__all__ = [
    "build_synthesis_quality_dashboard",
    "render_synthesis_quality_dashboard_html",
]


def build_synthesis_quality_dashboard(
    metrics: Mapping[str, Any],
    review_queue_records: Iterable[Mapping[str, Any]] | None = None,
    *,
    review_limit: int = 5,
) -> dict[str, Any]:
    """Build a stable JSON-friendly dashboard summary from synthesis metrics.

    Parameters
    ----------
    metrics
        Metrics returned by ``assess_synthesis_quality``.
    review_queue_records
        Optional records returned by ``build_review_queue``.
    review_limit
        Maximum number of review queue highlights to include.

    Returns
    -------
    dict[str, Any]
        Deterministic dashboard data suitable for JSON serialization.
    """
    statement_counts = _mapping(metrics.get("statement_counts"))
    evidence = _mapping(metrics.get("evidence_resolution"))
    graph = _mapping(metrics.get("graph_integrity"))
    pages = _mapping(metrics.get("page_integrity"))
    links = _mapping(metrics.get("link_integrity"))
    statement_links = _mapping(metrics.get("statement_link_integrity"))
    opportunities = _mapping(metrics.get("opportunity_targets"))
    conflicts = _mapping(metrics.get("active_conflicts"))
    high_centrality = _records(metrics.get("high_centrality_asserted_statements"))

    failure_counts = {
        "graph_dangling_edges": _int(graph.get("dangling_edges")),
        "orphan_pages": len(_items(pages.get("orphan_pages"))),
        "unknown_page_members": len(_items(pages.get("unknown_page_members"))),
        "unknown_section_members": len(_items(pages.get("unknown_section_members"))),
        "statements_without_page_membership": len(
            _items(pages.get("statements_without_page_membership"))
        ),
        "broken_outgoing_links": _int(links.get("broken_outgoing_link_count")),
        "broken_backlinks": _int(links.get("broken_backlink_count")),
        "backlink_mismatches": _int(links.get("backlink_mismatch_count")),
        "unresolved_statement_links": _int(
            statement_links.get("unresolved_statement_link_count")
        ),
    }

    return {
        "artifact": "synthesis_quality_dashboard",
        "version": 1,
        "summary": {
            "statement_total": _int(statement_counts.get("total")),
            "evidence_resolution_rate": evidence.get("rate"),
            "opportunity_target_rate": opportunities.get("rate"),
            "active_conflict_count": _int(conflicts.get("count")),
            "high_centrality_asserted_statement_count": len(high_centrality),
            "failure_counts": failure_counts,
        },
        "statement_counts": _normalize(statement_counts),
        "evidence_resolution": {
            "checked": bool(evidence.get("checked", False)),
            "total": _int(evidence.get("total")),
            "resolved": _int(evidence.get("resolved")),
            "unresolved": _int(evidence.get("unresolved")),
            "rate": evidence.get("rate"),
            "unresolved_statement_ids": _strings(
                evidence.get("unresolved_statement_ids")
            ),
        },
        "failures": {
            "graph": {
                "node_count": _int(graph.get("node_count")),
                "edge_count": _int(graph.get("edge_count")),
                "dangling_edges": failure_counts["graph_dangling_edges"],
                "dangling_edge_details": _records(graph.get("dangling_edge_details")),
            },
            "pages": {
                "page_count": _int(pages.get("page_count")),
                "pages_by_type": _normalize(_mapping(pages.get("pages_by_type"))),
                "orphan_pages": _strings(pages.get("orphan_pages")),
                "unknown_page_members": _records(pages.get("unknown_page_members")),
                "unknown_section_members": _records(
                    pages.get("unknown_section_members")
                ),
                "statements_without_page_membership": _strings(
                    pages.get("statements_without_page_membership")
                ),
            },
            "links": {
                "broken_outgoing_link_count": failure_counts["broken_outgoing_links"],
                "broken_backlink_count": failure_counts["broken_backlinks"],
                "backlink_mismatch_count": failure_counts["backlink_mismatches"],
                "broken_outgoing_links": _records(links.get("broken_outgoing_links")),
                "broken_backlinks": _records(links.get("broken_backlinks")),
                "missing_backlinks": _records(links.get("missing_backlinks")),
                "stale_backlinks": _records(links.get("stale_backlinks")),
            },
            "statement_links": {
                "unresolved_statement_link_count": failure_counts[
                    "unresolved_statement_links"
                ],
                "unresolved_statement_links": _records(
                    statement_links.get("unresolved_statement_links")
                ),
            },
        },
        "opportunity_targets": {
            "total": _int(opportunities.get("total")),
            "with_target_outputs": _int(opportunities.get("with_target_outputs")),
            "rate": opportunities.get("rate"),
            "opportunities": _records(opportunities.get("opportunities")),
            "missing_target_output_statement_ids": _strings(
                opportunities.get("missing_target_output_statement_ids")
            ),
        },
        "active_conflicts": {
            "count": _int(conflicts.get("count")),
            "conflict_statement_ids": _strings(conflicts.get("conflict_statement_ids")),
            "contradiction_links": _records(conflicts.get("contradiction_links")),
        },
        "high_centrality_asserted_statements": sorted(
            high_centrality,
            key=lambda record: (
                -_int(record.get("degree")),
                str(record.get("statement_id", "")),
            ),
        ),
        "review_queue": _review_queue(review_queue_records, review_limit),
    }


def render_synthesis_quality_dashboard_html(
    metrics: Mapping[str, Any],
    review_queue_records: Iterable[Mapping[str, Any]] | None = None,
    *,
    review_limit: int = 5,
    title: str = "Synthesis Quality Dashboard",
) -> str:
    """Render a self-contained static HTML dashboard."""
    dashboard = build_synthesis_quality_dashboard(
        metrics,
        review_queue_records,
        review_limit=review_limit,
    )
    summary = dashboard["summary"]
    failures = summary["failure_counts"]
    cards = [
        ("Statements", summary["statement_total"]),
        ("Evidence rate", _rate(summary["evidence_resolution_rate"])),
        ("Opportunity rate", _rate(summary["opportunity_target_rate"])),
        ("Active conflicts", summary["active_conflict_count"]),
        (
            "High-centrality asserted",
            summary["high_centrality_asserted_statement_count"],
        ),
        ("Review highlights", dashboard["review_queue"]["highlight_count"]),
    ]
    failure_rows = [
        (name.replace("_", " "), value)
        for name, value in sorted(failures.items())
        if value
    ] or [("none", 0)]
    review_rows = [
        (
            record["statement_id"],
            record["score"],
            record["kind"],
            record["tier"],
            ", ".join(record["reasons"]),
        )
        for record in dashboard["review_queue"]["highlights"]
    ] or [("none", 0, "", "", "")]

    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{_escape(title)}</title>",
            f"<style>{_CSS}</style>",
            "</head>",
            "<body><main>",
            f"<h1>{_escape(title)}</h1>",
            '<section class="cards">',
            *[
                (
                    '<article class="card">'
                    f"<h2>{_escape(label)}</h2>"
                    f"<p>{_escape(value)}</p>"
                    "</article>"
                )
                for label, value in cards
            ],
            "</section>",
            "<section><h2>Failure Counts</h2>",
            _table(("Failure", "Count"), failure_rows),
            "</section>",
            "<section><h2>Review Highlights</h2>",
            _table(("Statement", "Score", "Kind", "Tier", "Reasons"), review_rows),
            "</section>",
            "<section><h2>Dashboard JSON</h2>",
            "<pre>"
            f"{_escape(json.dumps(dashboard, indent=2, sort_keys=True))}"
            "</pre>",
            "</section>",
            "</main></body>",
            "</html>",
        ]
    )


def _review_queue(
    records: Iterable[Mapping[str, Any]] | None,
    limit: int,
) -> dict[str, Any]:
    highlights = [_review_highlight(record) for record in records or []]
    highlights.sort(
        key=lambda record: (
            -_int(record["score"]),
            -_int(record["centrality_degree"]),
            record["statement_id"],
        )
    )
    total = len(highlights)
    highlights = highlights[: max(limit, 0)]
    return {
        "total": total,
        "highlight_count": len(highlights),
        "highlights": highlights,
    }


def _review_highlight(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "statement_id": str(record.get("statement_id", "")),
        "score": _int(record.get("score")),
        "reasons": [str(reason) for reason in _items(record.get("reasons"))],
        "kind": str(record.get("kind", "")),
        "tier": str(record.get("tier", "")),
        "confidence": str(record.get("confidence", "")),
        "centrality_degree": _int(record.get("centrality_degree")),
        "statement": str(record.get("statement", "")),
        "affected_page_count": len(_items(record.get("affected_pages"))),
        "contradiction_count": len(_items(record.get("contradictions"))),
        "unresolved_statement_link_count": len(
            _items(record.get("unresolved_statement_links"))
        ),
    }


def _table(headers: tuple[str, ...], rows: Iterable[tuple[Any, ...]]) -> str:
    head = "".join(f"<th>{_escape(value)}</th>" for value in headers)
    body = "".join(
        "<tr>"
        + "".join(f"<td>{_escape(value)}</td>" for value in row)
        + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _records(value: Any) -> list[dict[str, Any]]:
    return sorted(
        [_record(item) for item in _items(value)],
        key=lambda item: json.dumps(item, sort_keys=True, default=str),
    )


def _record(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {
            str(key): _normalize(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    return {"value": _normalize(value)}


def _normalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _normalize(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, list | tuple | set):
        return [_normalize(item) for item in value]
    return value


def _strings(value: Any) -> list[str]:
    return sorted(str(item) for item in _items(value))


def _items(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple | set):
        return list(value)
    return []


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _int(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _rate(value: Any) -> str:
    return f"{value:.0%}" if isinstance(value, int | float) else "not checked"


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


_CSS = """
:root {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f6f7f9;
  color: #20242a;
}
body{margin:0}
main{max-width:1120px;margin:0 auto;padding:32px 20px 48px}
h1{margin:0 0 24px;font-size:28px}
h2{margin:0 0 12px;font-size:16px}
section{margin-top:24px}
.cards{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
  gap:12px;
}
.card{border:1px solid #d7dce2;border-radius:8px;background:#fff;padding:14px}
.card p{margin:0;font-size:24px;font-weight:700}
table{width:100%;border-collapse:collapse;background:#fff}
th,td{
  border:1px solid #d7dce2;
  padding:8px 10px;
  text-align:left;
  vertical-align:top;
}
th{background:#eef1f4}
pre{
  overflow:auto;
  border:1px solid #d7dce2;
  border-radius:8px;
  background:#fff;
  padding:16px;
}
""".strip()
