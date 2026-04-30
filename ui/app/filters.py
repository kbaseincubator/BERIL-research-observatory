import re

import markdown
from markupsafe import Markup


def markdown_filter(text: str) -> Markup:
    """Convert markdown text to HTML."""
    if not text:
        return Markup("")
    # Convert markdown to HTML
    html = markdown.markdown(
        text,
        extensions=["fenced_code", "tables", "toc", "nl2br"],
    )
    return Markup(html)


def markdown_inline_filter(text: str) -> Markup:
    """Convert markdown text to inline HTML (strips outer <p> tags)."""
    if not text:
        return Markup("")
    html = markdown.markdown(text, extensions=["fenced_code"])
    # Strip outer <p> tags for inline use
    if html.startswith("<p>") and html.endswith("</p>"):
        html = html[3:-4]
    return Markup(html)


def strip_images_filter(text: str) -> str:
    """Strip markdown image syntax from text for preview use."""
    if not text:
        return ""
    return re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)


def slugify_filter(text: str) -> str:
    """Convert text to a URL-friendly slug for anchor IDs."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text
