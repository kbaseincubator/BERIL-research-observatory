"""Typed models for the Observatory Context Service."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from observatory_context.render import RenderLevel


class ContextResource(BaseModel):
    """Normalized resource representation used by the service layer."""

    id: str
    uri: str
    kind: str
    title: str
    project_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    summary: str | None = None
    research_question: str | None = None
    body: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def render_payload(self) -> dict[str, Any]:
        payload = {
            "id": self.id,
            "uri": self.uri,
            "kind": self.kind,
            "title": self.title,
            "project_ids": self.project_ids,
            "tags": self.tags,
            "source_refs": self.source_refs,
            "links": self.links,
            "metadata": self.metadata,
        }
        if self.summary:
            payload["summary"] = self.summary
        if self.research_question:
            payload["research_question"] = self.research_question
        if self.body:
            payload["body"] = self.body
        return payload


class ResourceResponse(BaseModel):
    """A resource plus the requested deterministic render."""

    resource: ContextResource
    detail_level: RenderLevel
    rendered: str


class ProjectWorkspace(BaseModel):
    """The default retrieval unit for a project."""

    project_id: str
    workspace_uri: str
    detail_level: RenderLevel
    project_resource: ContextResource
    resources: list[ContextResource]
