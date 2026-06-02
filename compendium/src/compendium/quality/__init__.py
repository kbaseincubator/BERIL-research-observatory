"""Deterministic quality assessment for the canonical KG and rendered wiki."""

from __future__ import annotations

from .kg_quality import assess_kg
from .wiki_quality import assess_wiki

__all__ = ["assess_kg", "assess_wiki"]
