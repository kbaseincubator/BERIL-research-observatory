# ---------------------------------------------------------------------------
# Filter: markdown_filter
# ---------------------------------------------------------------------------


from markupsafe import Markup

from app.filters import (
    markdown_filter,
    markdown_inline_filter,
    slugify_filter,
    strip_images_filter,
)


class TestMarkdownFilter:
    def test_converts_bold(self):
        result = markdown_filter("**bold**")
        assert "<strong>bold</strong>" in result

    def test_converts_heading(self):
        result = markdown_filter("# Heading")
        assert "<h1>" in result

    def test_empty_string(self):
        result = markdown_filter("")
        assert result == Markup("")

    def test_none_value(self):
        result = markdown_filter(None)
        assert result == Markup("")

    def test_returns_markup(self):
        result = markdown_filter("hello")
        assert isinstance(result, Markup)

    def test_fenced_code(self):
        result = markdown_filter("```python\nprint('hi')\n```")
        assert "<code" in result

    def test_table_extension(self):
        result = markdown_filter("| a | b |\n|---|---|\n| 1 | 2 |")
        assert "<table>" in result


# ---------------------------------------------------------------------------
# Filter: markdown_inline_filter
# ---------------------------------------------------------------------------


class TestMarkdownInlineFilter:
    def test_strips_outer_p_tags(self):
        result = markdown_inline_filter("hello world")
        assert not str(result).startswith("<p>")
        assert not str(result).endswith("</p>")

    def test_empty_string(self):
        assert markdown_inline_filter("") == Markup("")

    def test_none_value(self):
        assert markdown_inline_filter(None) == Markup("")

    def test_returns_markup(self):
        result = markdown_inline_filter("test")
        assert isinstance(result, Markup)

    def test_preserves_inline_code(self):
        result = markdown_inline_filter("`code`")
        assert "<code>" in str(result)

    def test_multiline_keeps_inner_structure(self):
        # Multi-paragraph won't be stripped since it's more than one <p>
        result = markdown_inline_filter("line one\n\nline two")
        assert "line" in str(result)


# ---------------------------------------------------------------------------
# Filter: strip_images_filter
# ---------------------------------------------------------------------------


class TestStripImagesFilter:
    def test_strips_image(self):
        result = strip_images_filter("Text ![alt](path/to/img.png) more text")
        assert "![" not in result
        assert "more text" in result

    def test_empty_string(self):
        assert strip_images_filter("") == ""

    def test_none_value(self):
        assert strip_images_filter(None) == ""

    def test_no_image(self):
        text = "Just some text without images."
        assert strip_images_filter(text) == text

    def test_multiple_images(self):
        text = "![a](a.png) text ![b](b.png)"
        result = strip_images_filter(text)
        assert "![" not in result
        assert "text" in result


# ---------------------------------------------------------------------------
# Filter: slugify_filter
# ---------------------------------------------------------------------------


class TestSlugifyFilter:
    def test_basic(self):
        assert slugify_filter("Hello World") == "hello-world"

    def test_empty_string(self):
        assert slugify_filter("") == ""

    def test_none_value(self):
        assert slugify_filter(None) == ""

    def test_special_chars_removed(self):
        result = slugify_filter("Research & Development!")
        assert "&" not in result
        assert "!" not in result

    def test_spaces_become_hyphens(self):
        assert slugify_filter("My Section Title") == "my-section-title"

    def test_underscores_become_hyphens(self):
        assert slugify_filter("my_section") == "my-section"
