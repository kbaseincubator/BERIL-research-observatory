"""Stage-1 deterministic extraction (no LLM): REPORT.md -> ProjectKG."""

from compendium.extract.structural import extract_project

__all__ = ["extract_project"]
