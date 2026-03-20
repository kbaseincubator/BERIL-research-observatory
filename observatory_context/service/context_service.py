"""Phase 2 Observatory Context Service."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import yaml

from observatory_context.notes import build_live_resource, parse_live_resource
from observatory_context.render import RenderLevel, render_resource
from observatory_context.retrieval import build_authored_resource_index, lexical_search, rank_related_resources
from observatory_context.service.models import ContextResource, ProjectWorkspace, ResourceResponse
from observatory_context.uris import (
    build_observatory_root_uri,
    build_project_notes_root_uri,
    build_project_workspace_uri,
)


class ObservatoryContextService:
    """Root-level service for deterministic reads and live-context writes."""

    def __init__(
        self,
        repo_root: Path,
        client: Any | None = None,
        now_factory: Callable[[], str] | None = None,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.client = client
        self.now_factory = now_factory or (lambda: "1970-01-01T00:00:00Z")
        self._authored_resources = build_authored_resource_index(self.repo_root)
        self._project_ids = sorted(
            {
                project_id
                for resource in self._authored_resources.values()
                for project_id in resource.project_ids
            }
        )

    def search_context(
        self,
        query: str,
        kind: str | None = None,
        project: str | None = None,
        tags: list[str] | None = None,
        detail_level: RenderLevel = RenderLevel.L1,
    ) -> list[ResourceResponse]:
        resources = self._filtered_resources(kind=kind, project=project, tags=tags)
        semantic_results: list[ContextResource] = []
        if self.client is not None:
            target_uri = build_project_workspace_uri(project) if project else None
            try:
                semantic_hits = self.client.search(query, target_uri=target_uri)
            except Exception:
                semantic_hits = []
            all_resources = self._all_resources()
            semantic_results = []
            for hit in self._semantic_hit_items(semantic_hits):
                resolved_uri = self._resolve_semantic_hit_uri(hit, all_resources)
                if resolved_uri is None:
                    continue
                semantic_results.append(all_resources[resolved_uri])
        ranked = semantic_results or lexical_search(resources, query)
        seen: set[str] = set()
        results: list[ResourceResponse] = []
        for resource in ranked:
            if resource.uri in seen:
                continue
            seen.add(resource.uri)
            results.append(self._render_response(resource, detail_level))
        return results

    def _semantic_hit_items(self, semantic_hits: Any) -> list[Any]:
        if isinstance(semantic_hits, list):
            return semantic_hits
        if hasattr(semantic_hits, "resources") and isinstance(semantic_hits.resources, list):
            return semantic_hits.resources
        return []

    def _resolve_semantic_hit_uri(
        self,
        hit: Any,
        resources: dict[str, ContextResource],
    ) -> str | None:
        if isinstance(hit, dict):
            uri = hit.get("uri")
        else:
            uri = getattr(hit, "uri", None)
        if not isinstance(uri, str):
            return None
        if uri in resources:
            return uri
        for suffix in ("/.abstract.md", "/.overview.md"):
            if uri.endswith(suffix):
                uri = uri[: -len(suffix)]
                break
        while uri:
            if uri in resources:
                return uri
            if "/" not in uri.replace("://", "__", 1):
                break
            uri = uri.rsplit("/", 1)[0]
        return None

    def get_resource(
        self,
        id_or_uri: str,
        detail_level: RenderLevel = RenderLevel.L2,
    ) -> ResourceResponse:
        resource = self._resolve_resource(id_or_uri)
        return self._render_response(resource, detail_level)

    def get_project_workspace(
        self,
        project_id: str,
        detail_level: RenderLevel = RenderLevel.L1,
    ) -> ProjectWorkspace:
        project_resource = self._resolve_project_resource(project_id)
        resources = self.list_project_resources(project_id)
        return ProjectWorkspace(
            project_id=project_id,
            workspace_uri=build_project_workspace_uri(project_id),
            detail_level=self._coerce_level(detail_level),
            project_resource=project_resource,
            resources=resources,
        )

    def list_project_resources(
        self,
        project_id: str,
        kind: str | None = None,
        path: str | None = None,
    ) -> list[ContextResource]:
        resources = self._filtered_resources(project=project_id, kind=kind)
        if path:
            path_lower = path.lower()
            resources = [
                resource
                for resource in resources
                if path_lower in resource.uri.lower()
                or any(path_lower in ref.lower() for ref in resource.source_refs)
            ]
        return sorted(resources, key=lambda resource: (resource.kind != "project", resource.uri))

    def related_resources(
        self,
        id_or_uri: str,
        mode: str = "default",
        limit: int = 10,
    ) -> list[ContextResource]:
        source = self._resolve_resource(id_or_uri)
        candidates = self._filtered_resources()
        return rank_related_resources(source, candidates, mode=mode, limit=limit)

    def add_note(
        self,
        project_id: str | None,
        title: str,
        body: str,
        tags: list[str] | None = None,
        links: list[str] | None = None,
    ) -> ResourceResponse:
        payload = build_live_resource(
            kind="note",
            now=self.now_factory(),
            title=title,
            body=body,
            project_id=project_id,
            tags=tags,
            links=links,
        )
        resource = self._write_live_resource(payload)
        return self._render_response(resource, RenderLevel.L2)

    def add_observation(
        self,
        project_id: str | None,
        source_ref: str | None,
        body: str,
        tags: list[str] | None = None,
        links: list[str] | None = None,
    ) -> ResourceResponse:
        title = body.split(".", 1)[0].strip()[:72] or "Observation"
        payload = build_live_resource(
            kind="observation",
            now=self.now_factory(),
            title=title,
            body=body,
            project_id=project_id,
            source_ref=source_ref,
            tags=tags,
            links=links,
        )
        resource = self._write_live_resource(payload)
        return self._render_response(resource, RenderLevel.L2)

    def _render_response(self, resource: ContextResource, detail_level: RenderLevel) -> ResourceResponse:
        level = self._coerce_level(detail_level)
        return ResourceResponse(
            resource=resource,
            detail_level=level,
            rendered=render_resource(resource.render_payload(), level),
        )

    def _resolve_resource(self, id_or_uri: str) -> ContextResource:
        resources = self._all_resources()
        if id_or_uri in resources:
            return resources[id_or_uri]
        matches = [resource for resource in resources.values() if resource.id == id_or_uri]
        if not matches:
            raise KeyError(f"Unknown resource: {id_or_uri}")
        matches.sort(key=self._resource_priority)
        return matches[0]

    def _resolve_project_resource(self, project_id: str) -> ContextResource:
        matches = [
            resource
            for resource in self._all_resources().values()
            if resource.kind == "project" and project_id in resource.project_ids
        ]
        if not matches:
            raise KeyError(f"Unknown project workspace: {project_id}")
        return sorted(matches, key=lambda resource: resource.uri)[0]

    def _filtered_resources(
        self,
        kind: str | None = None,
        project: str | None = None,
        tags: list[str] | None = None,
    ) -> list[ContextResource]:
        required_tags = set(tags or [])
        resources = []
        for resource in self._all_resources().values():
            if kind and resource.kind != kind:
                continue
            if project and project not in resource.project_ids:
                continue
            if required_tags and not required_tags.issubset(set(resource.tags)):
                continue
            resources.append(resource)
        return resources

    def _all_resources(self) -> dict[str, ContextResource]:
        resources = dict(self._authored_resources)
        resources.update(self._load_client_resources())
        return resources

    def _load_client_resources(self) -> dict[str, ContextResource]:
        if self.client is None:
            return {}
        resources: dict[str, ContextResource] = {}
        try:
            entries = self.client.list_resources(build_observatory_root_uri(), recursive=True)
        except Exception:
            return {}
        for entry in entries:
            uri = entry.get("uri")
            if not uri or uri in resources:
                continue
            try:
                content = self.client.read_resource(uri)
            except Exception:
                continue
            fallback_metadata: dict[str, Any] = {}
            try:
                stat = self.client.stat_resource(uri)
            except Exception:
                stat = {}
            if isinstance(stat.get("metadata"), dict):
                fallback_metadata = dict(stat["metadata"])
            resource = self._parse_client_resource(uri, content, fallback_metadata)
            if resource is not None:
                resources[uri] = resource
        return resources

    def _parse_client_resource(
        self,
        uri: str,
        content: str,
        fallback_metadata: dict[str, Any],
    ) -> ContextResource | None:
        metadata, body = _split_frontmatter(content, fallback_metadata)
        kind = str(metadata.get("kind") or "")
        if not kind:
            return None
        if kind in {"note", "observation"}:
            return ContextResource(**parse_live_resource(uri, content, fallback_metadata=metadata))

        if kind == "project":
            summary = metadata.get("research_question")
        elif kind == "figure":
            summary = metadata.get("caption")
        else:
            summary = metadata.get("summary") or _compact_text(body)
        return ContextResource(
            id=str(metadata.get("id") or uri.rsplit("/", 1)[-1]),
            uri=uri,
            kind=kind,
            title=str(metadata.get("title") or metadata.get("id") or uri.rsplit("/", 1)[-1]),
            project_ids=list(metadata.get("project_ids") or []),
            tags=list(metadata.get("tags") or []),
            source_refs=list(metadata.get("source_refs") or []),
            links=list(metadata.get("links") or []),
            summary=summary,
            research_question=metadata.get("research_question"),
            body=body,
            metadata=metadata,
        )

    def _write_live_resource(self, payload: dict[str, Any]) -> ContextResource:
        uri = payload["uri"]
        metadata = payload["metadata"]
        content = payload["content"]
        if self.client is not None:
            project_ids = metadata.get("project_ids") or []
            for project_id in project_ids:
                self.client.make_directory(build_project_notes_root_uri(project_id))
            if hasattr(self.client, "add_note_resource"):
                self.client.add_note_resource(uri=uri, content=content, metadata=metadata)
            else:
                self.client.add_text_resource(
                    uri=uri,
                    content=content,
                    metadata=metadata,
                    reason=f"Add live {metadata['kind']} for BERIL observatory context",
                )
            if metadata.get("links"):
                self.client.link_resources(uri, metadata["links"], reason=f"{metadata['kind']} links")
        parsed = parse_live_resource(uri, content, fallback_metadata=metadata)
        return ContextResource(**parsed)

    @staticmethod
    def _resource_priority(resource: ContextResource) -> tuple[int, str]:
        priority = {
            "project": 0,
            "note": 1,
            "observation": 2,
            "figure": 3,
            "project_document": 4,
            "knowledge_document": 5,
        }
        return (priority.get(resource.kind, 99), resource.uri)

    @staticmethod
    def _coerce_level(detail_level: RenderLevel | str) -> RenderLevel:
        if isinstance(detail_level, RenderLevel):
            return detail_level
        return RenderLevel(detail_level)


def _split_frontmatter(content: str, fallback_metadata: dict[str, Any]) -> tuple[dict[str, Any], str]:
    metadata = dict(fallback_metadata)
    body = content
    if content.startswith("---\n") and "\n---\n" in content:
        _, remainder = content.split("---\n", 1)
        front_matter, body = remainder.split("\n---\n", 1)
        metadata.update(yaml.safe_load(front_matter) or {})
    return metadata, body.strip()


def _compact_text(text: str | None, limit: int = 240) -> str | None:
    if not text:
        return None
    compact = " ".join(text.split())
    return compact[:limit]
