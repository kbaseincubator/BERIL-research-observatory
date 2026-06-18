"""Deterministic assembly of a per-project wiki page (stub + LLM lead).

Project pages are mostly assembled by Python from data already in the KG: the project's
key findings (its statement texts, verbatim) and links to its topics, shared data, authors,
and source report. ``kg-write`` contributes only a short plain-language lead, which is
injected at the top. Keeping the structured parts deterministic guarantees the findings list
is complete and faithful, and keeps the page cheap to regenerate.
"""

from __future__ import annotations

from collections.abc import Sequence


def build_project_page(
    *,
    title: str,
    lead: str,
    findings: Sequence[tuple[str, str]],
    topics: Sequence[tuple[str, str]],
    data: Sequence[tuple[str, str]],
    authors: Sequence[tuple[str, str]],
    report_link: str | None = None,
) -> str:
    """Compose the Markdown for one project page.

    ``findings`` are ``(statement_text, confidence)`` pairs; ``topics``/``data``/``authors`` are
    ``(label, relative_link)`` pairs; ``report_link`` is the relative path to the source report.
    """
    parts: list[str] = [f"# {title}", "", lead.strip()]

    if findings:
        parts += ["", "## Key findings", ""]
        parts += [f"- {text} *(confidence: {confidence})*" for text, confidence in findings]

    for heading, items in (("Topics", topics), ("Data", data), ("Authors", authors)):
        if items:
            parts += ["", f"## {heading}", ""]
            parts += [f"- [{label}]({link})" for label, link in items]

    if report_link:
        parts += ["", f"[Open the full report →]({report_link})"]

    return "\n".join(parts).rstrip() + "\n"
