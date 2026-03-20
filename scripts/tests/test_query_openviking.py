"""Tests for the OpenViking query helper script."""

from __future__ import annotations

from types import SimpleNamespace

from observatory_context.render import RenderLevel
from observatory_context.service.models import ContextResource, ProjectWorkspace, ResourceResponse


def _resource(resource_id: str, uri: str, title: str, kind: str = "project") -> ContextResource:
    return ContextResource(
        id=resource_id,
        uri=uri,
        kind=kind,
        title=title,
        project_ids=["alpha_proj"] if resource_id == "alpha_proj" else [],
        tags=["metal-stress"],
        summary=f"Summary for {title}",
        metadata={},
    )


def test_query_openviking_search_prints_ranked_results(monkeypatch, capsys) -> None:
    from scripts import query_openviking

    service = SimpleNamespace(
        search_context=lambda query, kind=None, project=None, tags=None, detail_level=RenderLevel.L1: [
            ResourceResponse(
                resource=_resource(
                    "alpha_proj",
                    "viking://resources/observatory/projects/alpha_proj/authored/README.md",
                    "Alpha Project",
                ),
                detail_level=RenderLevel.L1,
                rendered="# Alpha Project\n\nSummary for Alpha Project",
            )
        ]
    )
    monkeypatch.setattr(query_openviking.runtime, "build_service", lambda *args, **kwargs: service)

    assert query_openviking.main(["search", "alpha response"]) == 0

    output = capsys.readouterr().out
    assert 'Results for "alpha response"' in output
    assert "Alpha Project" in output
    assert "viking://resources/observatory/projects/alpha_proj/authored/README.md" in output


def test_query_openviking_project_prints_workspace_summary(monkeypatch, capsys) -> None:
    from scripts import query_openviking

    project_resource = _resource(
        "alpha_proj",
        "viking://resources/observatory/projects/alpha_proj/authored/README.md",
        "Alpha Project",
    )
    workspace = ProjectWorkspace(
        project_id="alpha_proj",
        workspace_uri="viking://resources/observatory/projects/alpha_proj",
        detail_level=RenderLevel.L1,
        project_resource=project_resource,
        resources=[
            project_resource,
            _resource(
                "alpha_report",
                "viking://resources/observatory/projects/alpha_proj/authored/REPORT.md",
                "Alpha Report",
                kind="project_document",
            ),
        ],
    )
    service = SimpleNamespace(get_project_workspace=lambda project_id, detail_level=RenderLevel.L1: workspace)
    monkeypatch.setattr(query_openviking.runtime, "build_service", lambda *args, **kwargs: service)

    assert query_openviking.main(["project", "alpha_proj"]) == 0

    output = capsys.readouterr().out
    assert "Project workspace: alpha_proj" in output
    assert "viking://resources/observatory/projects/alpha_proj" in output
    assert "Alpha Report" in output
