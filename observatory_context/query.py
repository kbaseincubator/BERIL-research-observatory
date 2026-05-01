from __future__ import annotations

import json
from typing import Any

from openviking.utils.search_filters import merge_time_filter

from .config import DOCS_TARGET_URI, PROJECTS_TARGET_URI
from .selection import project_target_uri


def target_uri_for_find(
    project: str | None,
    docs: bool,
    target_uri: str | None,
) -> str:
    if target_uri:
        return target_uri
    if project:
        return project_target_uri(project)
    if docs:
        return DOCS_TARGET_URI
    return PROJECTS_TARGET_URI


def run_find(
    client: Any,
    query: str,
    target_uri: str,
    limit: int,
    *,
    filter: dict[str, Any] | None = None,
    score_threshold: float | None = None,
    since: str | None = None,
    until: str | None = None,
    time_field: str | None = None,
) -> Any:
    resolved_filter = merge_time_filter(filter, since=since, until=until, time_field=time_field)
    kwargs: dict[str, Any] = {}
    if resolved_filter is not None:
        kwargs["filter"] = resolved_filter
    if score_threshold is not None:
        kwargs["score_threshold"] = score_threshold
    return client.find(query=query, target_uri=target_uri, limit=limit, **kwargs)


def parse_filter_arg(value: str | None) -> dict[str, Any] | None:
    if not value:
        return None
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("--filter must be a JSON object")
    return parsed


def format_find_text(result: Any) -> str:
    resources = _resources(result)
    lines = [f"{_total(result, resources)} result(s)"]
    for resource in resources:
        lines.extend(
            [
                "",
                str(_field(resource, "uri", "")),
                f"score: {float(_field(resource, 'score', 0.0)):.3f}",
                str(_field(resource, "abstract", "")),
            ]
        )
        match_reason = _field(resource, "match_reason", None)
        if match_reason:
            lines.append(f"match_reason: {match_reason}")
    return "\n".join(lines)


def result_to_json(result: Any) -> str:
    resources = [_resource_to_dict(resource) for resource in _resources(result)]
    return json.dumps({"resources": resources, "total": _total(result, resources)})


def _resources(result: Any) -> list[Any]:
    resources = _field(result, "resources", [])
    return list(resources or [])


def _total(result: Any, resources: list[Any]) -> int:
    total = _field(result, "total", None)
    return int(total if total is not None else len(resources))


def _resource_to_dict(resource: Any) -> dict[str, Any]:
    data = {
        "uri": _field(resource, "uri", ""),
        "score": _field(resource, "score", 0.0),
        "abstract": _field(resource, "abstract", ""),
    }
    match_reason = _field(resource, "match_reason", None)
    if match_reason is not None:
        data["match_reason"] = match_reason
    return data


def _field(value: Any, name: str, default: Any) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)
