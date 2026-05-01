from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from observatory_context.config import (
    DOCS_TARGET_URI,
    PROJECT_INDEX_TARGET_URI,
    PROJECTS_TARGET_URI,
)
from observatory_context.query import (
    format_find_text,
    result_to_json,
    target_uri_for_find,
)
from knowledge.scripts.knowledge_query import build_parser


def test_target_uri_for_find_prefers_raw_project_docs_then_projects_root() -> None:
    assert (
        target_uri_for_find(
            project="alpha",
            docs=True,
            metadata=True,
            target_uri="viking://custom/",
        )
        == "viking://custom/"
    )
    assert target_uri_for_find("alpha", True, True, None) == f"{PROJECTS_TARGET_URI}alpha/"
    assert target_uri_for_find(None, True, True, None) == DOCS_TARGET_URI
    assert target_uri_for_find(None, False, True, None) == PROJECT_INDEX_TARGET_URI
    assert target_uri_for_find(None, False, False, None) == PROJECTS_TARGET_URI


def test_find_scope_options_are_mutually_exclusive() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["find", "query", "--project", "demo", "--docs"])


def test_format_find_text_and_result_to_json() -> None:
    result = SimpleNamespace(
        total=2,
        resources=[
            SimpleNamespace(
                uri="viking://resources/projects/alpha/",
                score=0.98765,
                abstract="Alpha summary",
                match_reason="title match",
            ),
            SimpleNamespace(
                uri="viking://resources/docs/pitfalls/",
                score=0.5,
                abstract="Pitfalls summary",
            ),
        ],
    )

    text = format_find_text(result)
    payload = json.loads(result_to_json(result))

    assert "2 result(s)" in text
    assert "viking://resources/projects/alpha/" in text
    assert "score: 0.988" in text
    assert "Alpha summary" in text
    assert "match_reason: title match" in text
    assert "score: 0.500" in text
    assert payload == {
        "resources": [
            {
                "uri": "viking://resources/projects/alpha/",
                "score": 0.98765,
                "abstract": "Alpha summary",
                "match_reason": "title match",
            },
            {
                "uri": "viking://resources/docs/pitfalls/",
                "score": 0.5,
                "abstract": "Pitfalls summary",
            },
        ],
        "total": 2,
    }
