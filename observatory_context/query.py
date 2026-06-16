from __future__ import annotations

import json
import sys
from typing import Any

from openviking.utils.search_filters import merge_time_filter
from openviking_cli.exceptions import OpenVikingError

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


def _print_json(value: Any, out: Any) -> None:
    print(json.dumps(value, indent=2, default=str), file=out)


def dispatch_command(args: Any, client: Any, out: Any) -> None:
    """Run one parsed query subcommand against the OpenViking client.

    Raises OpenVikingError / ValueError for the caller to map to a clean
    message; this function does no error handling of its own.
    """
    if args.command == "find":
        target_uri = target_uri_for_find(
            project=args.project, docs=args.docs, target_uri=args.target_uri
        )
        result = run_find(
            client,
            args.query,
            target_uri,
            args.limit,
            filter=parse_filter_arg(args.filter),
            score_threshold=args.score_threshold,
            since=args.since,
            until=args.until,
            time_field=args.time_field,
        )
        print(
            result_to_json(result) if args.json else format_find_text(result),
            file=out,
        )
    elif args.command == "grep":
        kwargs: dict[str, Any] = {"case_insensitive": args.case_insensitive}
        if args.node_limit is not None:
            kwargs["node_limit"] = args.node_limit
        if args.exclude_uri:
            kwargs["exclude_uri"] = args.exclude_uri
        _print_json(client.grep(args.uri, args.pattern, **kwargs), out)
    elif args.command == "glob":
        _print_json(client.glob(args.pattern, uri=args.uri), out)
    elif args.command == "ls":
        _print_json(
            client.ls(args.uri, simple=args.simple, recursive=args.recursive), out
        )
    elif args.command == "tree":
        _print_json(client.tree(args.uri, node_limit=args.node_limit), out)
    elif args.command == "stat":
        _print_json(client.stat(args.uri), out)
    elif args.command == "relations":
        _print_json(client.relations(args.uri), out)
    elif args.command == "link":
        client.link(args.from_uri, args.to_uris, reason=args.reason)
    elif args.command == "unlink":
        client.unlink(args.from_uri, args.to_uri)
    elif args.command == "overview":
        print(client.overview(args.uri), file=out)
    elif args.command == "read":
        print(client.read(args.uri), file=out)


def run_command(args: Any, client: Any, *, out: Any = None, err: Any = None) -> int:
    """Dispatch a query subcommand, mapping expected errors to a clean message.

    Returns 0 on success, 1 if an OpenViking or argument/parse error was caught.
    """
    out = out if out is not None else sys.stdout
    err = err if err is not None else sys.stderr
    try:
        dispatch_command(args, client, out)
        return 0
    except (OpenVikingError, ValueError) as exc:
        print(f"error: {exc}", file=err)
        return 1
