"""Tests for query_knowledge_unified.py CLI parser."""

from __future__ import annotations

import scripts.query_knowledge_unified as query_knowledge


def test_backfill_parser_accepts_optional_project_id() -> None:
    parser = query_knowledge.build_parser()

    args = parser.parse_args(["backfill", "essential_genome"])

    assert args.command == "backfill"
    assert args.project_id == "essential_genome"


def test_all_subcommands_present() -> None:
    parser = query_knowledge.build_parser()
    subparsers = parser._subparsers._group_actions[0].choices
    expected = {
        "search", "figures", "data", "project", "landscape",
        "entities", "connections", "hypotheses", "gaps",
        "timeline", "backfill", "related", "grep", "glob",
    }
    assert set(subparsers.keys()) == expected
