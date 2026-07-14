from __future__ import annotations

import io
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
    run_command,
    run_find,
    target_uri_for_find,
)
from openviking_cli.exceptions import InvalidArgumentError, NotFoundError


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


def test_run_find_forwards_plain_filter_and_score_threshold() -> None:
    client = _RecordingClient()
    run_find(
        client,
        "q",
        "viking://resources/",
        5,
        filter={"op": "must", "field": "uri", "conds": ["x"]},
        score_threshold=0.4,
    )
    assert client.last_kwargs == {
        "query": "q",
        "target_uri": "viking://resources/",
        "limit": 5,
        "filter": {"op": "must", "field": "uri", "conds": ["x"]},
        "score_threshold": 0.4,
    }


def test_run_find_resolves_time_bounds_into_filter() -> None:
    client = _RecordingClient()
    run_find(
        client,
        "q",
        "viking://resources/",
        5,
        since="2026-04-01",
        until="2026-05-01",
        time_field="updated_at",
    )
    sent = client.last_kwargs
    assert "since" not in sent and "until" not in sent and "time_field" not in sent
    assert sent["filter"]["op"] == "time_range"
    assert sent["filter"]["field"] == "updated_at"
    assert sent["filter"]["gte"].startswith("2026-04-01")
    assert sent["filter"]["lte"].startswith("2026-05-01")


def test_run_find_ands_time_bounds_with_existing_filter() -> None:
    client = _RecordingClient()
    base = {"op": "must", "field": "uri", "conds": ["viking://resources/projects/alpha/"]}
    run_find(
        client,
        "q",
        "viking://resources/",
        5,
        filter=base,
        since="2026-04-01",
    )
    sent = client.last_kwargs["filter"]
    assert sent["op"] == "and"
    assert base in sent["conds"]
    assert any(cond.get("op") == "time_range" for cond in sent["conds"])


def _find_args(**overrides):
    base = dict(
        command="find",
        query="microbial",
        project=None,
        docs=False,
        target_uri=None,
        limit=5,
        filter=None,
        score_threshold=None,
        since=None,
        until=None,
        time_field=None,
        json=False,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class _DispatchClient:
    def __init__(self, *, find_exc=None, read_exc=None):
        self._find_exc = find_exc
        self._read_exc = read_exc
        self.calls: list = []

    def find(self, **kwargs):
        self.calls.append(("find", kwargs))
        if self._find_exc is not None:
            raise self._find_exc
        return SimpleNamespace(
            total=1,
            resources=[SimpleNamespace(uri="viking://x/", score=0.5, abstract="A")],
        )

    def read(self, uri):
        self.calls.append(("read", uri))
        if self._read_exc is not None:
            raise self._read_exc
        return "file body"


def test_run_command_find_success_returns_zero_and_prints():
    out, err = io.StringIO(), io.StringIO()
    client = _DispatchClient()
    code = run_command(_find_args(), client, out=out, err=err)
    assert code == 0
    assert "1 result(s)" in out.getvalue()
    assert err.getvalue() == ""


def test_run_command_maps_invalid_argument_to_clean_error():
    out, err = io.StringIO(), io.StringIO()
    client = _DispatchClient(
        find_exc=InvalidArgumentError("Search query must not be empty.")
    )
    code = run_command(_find_args(query=""), client, out=out, err=err)
    assert code == 1
    assert out.getvalue() == ""
    assert err.getvalue().startswith("error: ")
    assert "must not be empty" in err.getvalue()
    assert "Traceback" not in err.getvalue()


def test_run_command_maps_not_found_to_clean_error():
    out, err = io.StringIO(), io.StringIO()
    client = _DispatchClient(read_exc=NotFoundError("File not found: viking://x/"))
    args = SimpleNamespace(command="read", uri="viking://x/")
    code = run_command(args, client, out=out, err=err)
    assert code == 1
    assert "error: " in err.getvalue()
    assert "not found" in err.getvalue().lower()
    assert "Traceback" not in err.getvalue()


def test_run_command_maps_malformed_filter_to_clean_error_without_calling_client():
    out, err = io.StringIO(), io.StringIO()
    client = _DispatchClient()
    code = run_command(
        _find_args(filter="{not valid json"), client, out=out, err=err
    )
    assert code == 1
    assert err.getvalue().startswith("error: ")
    assert client.calls == []  # parse fails before the client is touched


def test_run_command_maps_bad_since_to_clean_error():
    out, err = io.StringIO(), io.StringIO()
    client = _DispatchClient()
    code = run_command(
        _find_args(since="not-a-duration", time_field="updated_at"),
        client,
        out=out,
        err=err,
    )
    assert code == 1
    assert err.getvalue().startswith("error: ")


def test_run_command_read_success_prints_body():
    out, err = io.StringIO(), io.StringIO()
    client = _DispatchClient()
    args = SimpleNamespace(command="read", uri="viking://x/")
    code = run_command(args, client, out=out, err=err)
    assert code == 0
    assert "file body" in out.getvalue()
