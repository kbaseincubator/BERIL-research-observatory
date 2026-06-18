"""Reflow hard-wrapped prose into one line per paragraph.

Authors (especially smaller models) often hard-wrap prose at ~72-80 columns. In Markdown a single
newline inside a paragraph is only a soft wrap, but some renderers (notably Cosma's) turn each one
into a ``<br>``, producing ragged mid-sentence line breaks. Joining soft-wrapped lines into one
physical line per paragraph renders identically everywhere. Structural lines — headings, list items
(including the generated ``## References`` entries), blockquotes, tables, and fenced code — are
preserved, and code blocks are never reflowed.
"""

from __future__ import annotations

import re

_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s")
_LIST_RE = re.compile(r"^\s*([-*+]\s|\d+[.)]\s)")
_HR_RE = re.compile(r"^\s{0,3}([-*_])(\s*\1){2,}\s*$")


def reflow_paragraphs(markdown: str) -> str:
    """Join soft-wrapped lines within each paragraph / list item into a single line."""
    out: list[str] = []
    buffer: list[str] = []
    in_code = False

    def flush() -> None:
        if buffer:
            out.append(" ".join(part.strip() for part in buffer))
            buffer.clear()

    for line in markdown.splitlines():
        if _FENCE_RE.match(line):
            flush()
            in_code = not in_code
            out.append(line)
            continue
        if in_code:
            out.append(line)
            continue
        if not line.strip():
            flush()
            out.append("")
            continue
        if _HEADING_RE.match(line) or _HR_RE.match(line) or line.lstrip()[:1] in (">", "|"):
            flush()
            out.append(line.rstrip())
            continue
        if _LIST_RE.match(line):
            flush()
            buffer.append(line.rstrip())
            continue
        buffer.append(line)

    flush()
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(out))
    return text.rstrip() + "\n"
