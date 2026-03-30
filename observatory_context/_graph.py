"""Shared helpers for project dependency graph operations."""

from __future__ import annotations


def compute_enables(projects: list[dict]) -> None:
    """Populate reverse-dependency ``enables`` lists on project dicts.

    Each dict must have ``"id"`` and ``"depends_on"`` keys.  The function
    normalises ``depends_on`` to a sorted list, then builds the ``enables``
    list for every project whose id appears as a dependency.  Mutates
    *projects* in place.
    """
    id_to_project = {str(project["id"]): project for project in projects}
    for project in projects:
        project["depends_on"] = sorted(project.get("depends_on") or [])
        project["enables"] = []
    for project in projects:
        for dependency in project["depends_on"]:
            dep_id = str(dependency)
            if dep_id in id_to_project:
                id_to_project[dep_id]["enables"].append(project["id"])
    for project in projects:
        project["enables"] = sorted(project["enables"])
