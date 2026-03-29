"""Tests for query_knowledge_unified.py CLI parser."""

from __future__ import annotations

import scripts.query_knowledge_unified as query_knowledge


def test_backfill_parser_is_deprecated_and_takes_no_project_id() -> None:
    parser = query_knowledge.build_parser()

    args = parser.parse_args(["backfill"])

    assert args.command == "backfill"


def test_timeline_parser_accepts_since() -> None:
    parser = query_knowledge.build_parser()

    args = parser.parse_args(["timeline", "--project", "essential_genome", "--since", "2026-03-01"])

    assert args.command == "timeline"
    assert args.project == "essential_genome"
    assert args.since == "2026-03-01"


def test_all_subcommands_present() -> None:
    parser = query_knowledge.build_parser()
    subparsers = parser._subparsers._group_actions[0].choices
    expected = {
        "search", "figures", "data", "project", "landscape",
        "entities", "connections", "hypotheses", "gaps",
        "timeline", "backfill", "related", "grep", "glob",
        "browse", "traverse", "recall", "remember", "ingest-entity",
    }
    assert set(subparsers.keys()) == expected
