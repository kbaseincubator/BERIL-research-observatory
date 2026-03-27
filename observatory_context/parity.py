"""Parity validation helpers for the OpenViking migration."""

from __future__ import annotations


def collect_parity_issues(
    expected_counts: dict[str, int],
    actual_counts: dict[str, int],
    duplicate_uris: list[str] | None = None,
    missing_project_ids: list[str] | None = None,
) -> list[str]:
    """Return human-readable parity issues."""
    issues: list[str] = []

    for name, expected in expected_counts.items():
        actual = actual_counts.get(name)
        if actual != expected:
            issues.append(f"{name[:-1] if name.endswith('s') else name} count mismatch: expected {expected}, got {actual}")

    duplicate_uris = duplicate_uris or []
    if duplicate_uris:
        issues.append(f"duplicate logical resources detected: {len(duplicate_uris)}")

    missing_project_ids = missing_project_ids or []
    if missing_project_ids:
        issues.append(f"missing project workspaces: {', '.join(sorted(missing_project_ids))}")

    return issues

