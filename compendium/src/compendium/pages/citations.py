"""Publish-time provenance transforms for authored wiki pages.

``kg-write`` now places its ``[stmt:id; project]`` tokens *inline* at the claim each
statement backs (instead of a trailing ``## Sources`` slug dump). These deterministic
transforms turn that raw provenance into reader-facing citations:

- :func:`render_inline_citations` rewrites each inline token into a numbered marker and
  appends a readable ``## References`` list whose entries link to the per-project page.
- :func:`link_project_mentions` turns ```project_id``` code spans in prose into links to
  the matching project page.

Both emit real ``[label](../projects/<slug>.md)`` Markdown links, which the Cosma exporter
converts into graph edges -- so citations and project mentions become connected nodes
rather than dead bracket-text.
"""

from __future__ import annotations

import posixpath
import re

from compendium.models import StatementCard

_INLINE_CITATION_RE = re.compile(r"\[(stmt:[^;\]\s]+);\s*([^\]]+?)\]")
_BACKTICK_PROJECT_RE = re.compile(r"`([a-z0-9][a-z0-9_]+)`")
_PAGE_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+?\.md(?:#[^)]*)?)\)")
# A trailing provenance section whose heading is *exactly* "Sources" or "References" (the slug dump
# we replace, or a References list the author wrote despite instructions). Anchored to the heading
# line so legitimate sections like "## Sources of variation" are left untouched.
_PROVENANCE_SECTION_RE = re.compile(
    r"\n#{1,6}[ \t]+(?:Sources|References)[ \t]*(?:\n.*)?\Z",
    re.DOTALL | re.IGNORECASE,
)
_REFERENCE_ANCHOR = "#references"


def render_inline_citations(
    markdown: str,
    card_by_id: dict[str, StatementCard],
    *,
    page_path: str,
    member_ids: set[str],
) -> tuple[str, list[str]]:
    """Rewrite inline ``[stmt:id; project]`` tokens into numbered, linked references.

    Returns ``(transformed_markdown, cited_ids)`` where ``cited_ids`` is the citation order.
    Raises ``ValueError`` if a cited id is not a page member, or if a page that has members
    cites none.
    """
    body = _strip_sources_section(markdown)
    order: list[str] = []
    seen: set[str] = set()
    for match in _INLINE_CITATION_RE.finditer(body):
        statement_id = match.group(1)
        if statement_id not in seen:
            seen.add(statement_id)
            order.append(statement_id)

    nonmember = [sid for sid in order if sid not in member_ids]
    if nonmember:
        raise ValueError(
            "authored page cites statements outside page membership: " + ", ".join(sorted(nonmember))
        )
    if member_ids and not order:
        raise ValueError("authored page must cite at least one member statement inline")

    numbers = {statement_id: index + 1 for index, statement_id in enumerate(order)}

    def _marker(match: re.Match) -> str:
        return f"[\\[{numbers[match.group(1)]}\\]]({_REFERENCE_ANCHOR})"

    new_body = _INLINE_CITATION_RE.sub(_marker, body).rstrip()
    if not order:
        return new_body + "\n", order
    references = _references_section(order, numbers, card_by_id, page_path)
    return new_body + "\n\n" + references, order


def normalize_page_links(markdown: str, *, page_path: str, known_paths: set[str]) -> str:
    """Rewrite cross-page links that use a wiki-root-relative path to the correct page-relative one.

    The page context hands the author wiki-root-relative paths (e.g. ``topics/x.md``); an author may
    paste one verbatim instead of making it relative to the current page, producing a link that
    resolves to ``topics/topics/x.md``. When a link target — read as a wiki-root-relative path — is a
    real page, rewrite it relative to this page. Targets that are already relative (start with ``.``)
    or are not known pages are left untouched.
    """
    page_dir = posixpath.dirname(page_path)

    def _fix(match: re.Match) -> str:
        label, target = match.group(1), match.group(2)
        base, sep, frag = target.partition("#")
        if base.startswith((".", "/")) or base not in known_paths:
            return match.group(0)
        rel = posixpath.relpath(base, page_dir or ".")
        return f"[{label}]({rel}{sep}{frag})"

    return _PAGE_LINK_RE.sub(_fix, markdown)


def link_project_mentions(markdown: str, known_projects: set[str], *, page_path: str) -> str:
    """Rewrite ```project_id``` code spans into links to the project's wiki page."""

    def _link(match: re.Match) -> str:
        project_id = match.group(1)
        if project_id not in known_projects:
            return match.group(0)
        return f"[`{project_id}`]({project_relpath(project_id, page_path)})"

    return _BACKTICK_PROJECT_RE.sub(_link, markdown)


def clean_project_lead(lead: str) -> str:
    """Sanitize an LLM-authored project lead before it is injected into the stub.

    Project leads are meant to be 2-3 sentences of prose with no headings or citations, but the
    instruction is advisory. Strip any stray inline ``[stmt:id; project]`` tokens (project pages
    carry no citations) and any leading Markdown heading lines (the title is added by the template,
    so a heading here would duplicate it).
    """
    text = _INLINE_CITATION_RE.sub("", lead)
    text = re.sub(r"[ \t]+([.,;:])", r"\1", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    lines = text.strip().splitlines()
    while lines and lines[0].lstrip().startswith("#"):
        lines.pop(0)
    return "\n".join(lines).strip()


def project_relpath(project_id: str, page_path: str) -> str:
    """Return the relative link from ``page_path`` to the project's wiki page."""
    start = posixpath.dirname(page_path) or "."
    return posixpath.relpath(f"projects/{_slug(project_id)}.md", start)


def _references_section(
    order: list[str],
    numbers: dict[str, int],
    card_by_id: dict[str, StatementCard],
    page_path: str,
) -> str:
    lines = ["## References", ""]
    for statement_id in order:
        card = card_by_id[statement_id]
        evidence = card.evidence[0]
        project = evidence.source_project
        link = f"[{_titleize(project)}]({project_relpath(project, page_path)})"
        source = evidence.source_doc
        if evidence.source_section:
            source += f' › "{evidence.source_section}"'
        lines.append(f"{numbers[statement_id]}. {link} — {source}.")
    return "\n".join(lines) + "\n"


def _strip_sources_section(markdown: str) -> str:
    return _PROVENANCE_SECTION_RE.sub("\n", markdown).rstrip() + "\n"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "page"


def _titleize(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()
