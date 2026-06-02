"""Compendium: a deterministic, knowledge-graph-centered scientific aggregation wiki.

Pipeline: audit -> extract (Stage-1, deterministic) -> ground -> verify -> canonicalize
-> assemble (KGX) -> render (static site). LLM steps live in ``compendium/skills`` and never
sit on the render path. See docs/kg-wiki/2026-06-01-kg-wiki-design.md.
"""

__version__ = "0.1.0"
