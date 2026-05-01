from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from observatory_context.config import (
    DOCS_TARGET_URI,
    PROJECTS_TARGET_URI,
)
from observatory_context.query import (
    format_find_text,
    parse_filter_arg,
    result_to_json,
    run_find,
    target_uri_for_find,
)


def test_target_uri_for_find_prefers_raw_project_docs_then_projects_root() -> None:
    assert (
        target_uri_for_find(
            project="alpha",
            docs=True,
            target_uri="viking://custom/",
        )
        == "viking://custom/"
    )
    assert target_uri_for_find("alpha", True, None) == f"{PROJECTS_TARGET_URI}alpha/"
    assert target_uri_for_find(None, True, None) == DOCS_TARGET_URI
    assert target_uri_for_find(None, False, None) == PROJECTS_TARGET_URI


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


def test_parse_filter_arg_returns_none_for_empty() -> None:
    assert parse_filter_arg(None) is None
    assert parse_filter_arg("") is None


def test_parse_filter_arg_parses_filter_tree() -> None:
    raw = '{"op": "must", "field": "uri", "conds": ["viking://resources/projects/alpha/"]}'
    assert parse_filter_arg(raw) == {
        "op": "must",
        "field": "uri",
        "conds": ["viking://resources/projects/alpha/"],
    }


def test_parse_filter_arg_rejects_non_object() -> None:
    with pytest.raises(ValueError):
        parse_filter_arg("[1, 2, 3]")


class _RecordingClient:
    def __init__(self) -> None:
        self.last_kwargs: dict | None = None

    def find(self, **kwargs):
        self.last_kwargs = kwargs
        return SimpleNamespace(total=0, resources=[])


def test_run_find_omits_unset_kwargs() -> None:
    client = _RecordingClient()
    run_find(client, "q", "viking://resources/", 5)
    assert client.last_kwargs == {
        "query": "q",
        "target_uri": "viking://resources/",
        "limit": 5,
    }


def test_run_find_forwards_filter_and_time_bounds() -> None:
    client = _RecordingClient()
    run_find(
        client,
        "q",
        "viking://resources/",
        5,
        filter={"op": "must", "field": "uri", "conds": ["x"]},
        score_threshold=0.4,
        since="7d",
        until="2026-05-01",
        time_field="updated_at",
    )
    assert client.last_kwargs == {
        "query": "q",
        "target_uri": "viking://resources/",
        "limit": 5,
        "filter": {"op": "must", "field": "uri", "conds": ["x"]},
        "score_threshold": 0.4,
        "since": "7d",
        "until": "2026-05-01",
        "time_field": "updated_at",
    }
