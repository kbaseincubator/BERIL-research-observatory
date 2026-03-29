"""ContextDelivery — service layer between Claude Code skills and OpenViking."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import yaml

from observatory_context._text import slugify, split_frontmatter
from observatory_context.client import OpenVikingObservatoryClient
from observatory_context.extraction import CBORGExtractor
from observatory_context.models import (
    ContextItem,
    GraphResult,
    RelationEdge,
    Scope,
    SearchResults,
    Tier,
)
from observatory_context.uris import (
    _ENTITY_TYPE_PLURALS,
    _ROOT,
    build_entity_uri,
    build_knowledge_graph_uri,
    build_memory_uri,
    build_timeline_uri,
)

logger = logging.getLogger(__name__)


def _is_not_found(exc: Exception) -> bool:
    """Check if an exception is an OpenViking NotFoundError (by class name)."""
    return any(cls.__name__ == "NotFoundError" for cls in type(exc).__mro__)


_MEMORY_FILE_NAMES = {
    "journal": "entry.md",
    "patterns": "pattern.yaml",
    "conversations": "insight.yaml",
}


class ContextDelivery:
    """Tier-aware retrieval, graph traversal, memory ops, and ingest.

    Parameters
    ----------
    client:
        An initialised OpenVikingObservatoryClient.
    extractor:
        Optional CBORG extractor for entity extraction and tier generation.
    """

    def __init__(
        self,
        client: OpenVikingObservatoryClient,
        extractor: CBORGExtractor | None = None,
    ) -> None:
        self.client = client
        self.extractor = extractor

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _scope_uri(self, scope: Scope) -> str:
        """Map a Scope enum to a URI prefix."""
        if scope == Scope.memory:
            return f"{_ROOT}/memories"
        if scope == Scope.graph:
            return build_knowledge_graph_uri()
        # ALL and RESOURCES both start from root
        return _ROOT

    def _load_item(self, uri: str, tier: Tier) -> ContextItem:
        """Load a single resource at the requested tier."""
        if tier == Tier.L0:
            return self._load_tier_file(uri, ".abstract.md", Tier.L0)
        if tier == Tier.L1:
            return self._load_tier_file(uri, ".overview.md", Tier.L1)
        # L2 — full content
        return self._load_full(uri)

    def _load_tier_file(self, uri: str, suffix: str, tier: Tier) -> ContextItem:
        """Try to load a tier file, falling back to full content."""
        # Try in-directory first (for entities that ARE directories)
        try:
            content = self.client.read_resource(f"{uri}/{suffix}")
            return self._build_item(uri, content, tier)
        except Exception as exc:
            if not _is_not_found(exc):
                raise

        # Try at parent level (for files)
        parent, _name = uri.rsplit("/", 1)
        try:
            content = self.client.read_resource(f"{parent}/{suffix}")
            return self._build_item(uri, content, tier)
        except Exception as exc:
            if not _is_not_found(exc):
                raise

        # Fall back to full L2 content
        return self._load_full(uri, override_tier=tier)

    def _load_full(self, uri: str, override_tier: Tier | None = None) -> ContextItem:
        """Load the full L2 content of a resource."""
        raw = self.client.read_resource(uri)
        return self._build_item(uri, raw, override_tier or Tier.L2)

    def _build_item(self, uri: str, raw_content: str, tier: Tier) -> ContextItem:
        """Parse raw content (possibly with frontmatter) into a ContextItem."""
        metadata, body = split_frontmatter(raw_content, {})
        source_type = "memory" if "/memories/" in uri else "resource"
        return ContextItem(
            uri=uri,
            title=metadata.get("title", uri.rsplit("/", 1)[-1]),
            kind=metadata.get("kind", "unknown"),
            tier=tier,
            content=body,
            project_ids=_ensure_list(metadata.get("project_ids")),
            tags=_ensure_list(metadata.get("tags")),
            source_type=source_type,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Search & Retrieval
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        *,
        scope: Scope = Scope.all,
        tier: Tier = Tier.L2,
        kind: str | None = None,
        project: str | None = None,
        with_memory: bool = False,
        limit: int = 10,
    ) -> SearchResults:
        """Semantic search across observatory resources.

        Parameters
        ----------
        query:
            Natural language search query.
        scope:
            Scope to restrict the search.
        tier:
            Detail tier for returned items.
        kind:
            Optional kind filter (e.g. ``"report"``, ``"figure"``).
        project:
            Optional project ID filter.
        with_memory:
            If True, search ALL and include memory results.
        limit:
            Maximum number of results.
        """
        target_uri = self._scope_uri(Scope.all if with_memory else scope)
        search_filter: dict[str, Any] | None = None
        if kind or project:
            search_filter = {}
            if kind:
                search_filter["kind"] = kind
            if project:
                search_filter["project"] = project

        hits = self.client.search(
            query=query,
            target_uri=target_uri,
            limit=limit,
            filter=search_filter,
        )

        items = []
        for hit in hits:
            try:
                uri = hit.uri if hasattr(hit, "uri") else hit["uri"]
                item = self._load_item(uri, tier)
                items.append(item)
            except Exception:
                logger.warning("Failed to load search hit %s", hit, exc_info=True)

        return SearchResults(query=query, items=items, total_count=len(items))

    def get(self, uri: str, *, tier: Tier = Tier.L2) -> ContextItem:
        """Retrieve a single resource by URI at the requested tier."""
        return self._load_item(uri, tier)

    def browse(self, uri: str, *, tier: Tier = Tier.L1, depth: int = 1) -> list[ContextItem]:
        """List children of a directory URI.

        Parameters
        ----------
        uri:
            Directory URI to browse.
        tier:
            Detail tier for each child item.
        depth:
            Listing depth (1 = immediate children).
        """
        entries = self.client.list_resources(uri, recursive=(depth > 1))
        items = []
        for entry in entries:
            try:
                item = self._load_item(entry["uri"], tier)
                items.append(item)
            except Exception:
                logger.warning("Failed to load browse entry %s", entry.get("uri"), exc_info=True)
        return items

    def traverse(
        self,
        entity_uri: str,
        *,
        relation_filter: str | None = None,
        hops: int = 1,
        tier: Tier = Tier.L2,
        ) -> GraphResult:
        """Traverse the knowledge graph from an entity.

        Parameters
        ----------
        entity_uri:
            Starting entity URI.
        relation_filter:
            Optional predicate name to filter relations.
        hops:
            Number of traversal hops.
        tier:
            Detail tier for items.
        """
        root = self._load_item(entity_uri, tier)
        edges: list[RelationEdge] = []
        connected: list[ContextItem] = []
        seen_entities: set[str] = {entity_uri}
        seen_edges: set[tuple[str, str, str]] = set()

        def walk(current_uri: str, remaining_hops: int) -> None:
            try:
                rel_entries = self.client.list_resources(f"{current_uri}/relations")
            except Exception:
                return

            for entry in rel_entries:
                entry_uri = entry["uri"]
                if entry_uri.endswith((".abstract.md", ".overview.md")):
                    continue

                try:
                    relation_data = self._parse_relation(self.client.read_resource(entry_uri))
                except Exception:
                    logger.debug("Failed to parse relation %s", entry_uri)
                    continue

                predicate = str(relation_data.get("predicate", ""))
                if relation_filter and predicate != relation_filter:
                    continue

                target_uri = self._resolve_entity_ref(str(relation_data.get("object", "")))
                edge_key = (current_uri, predicate, target_uri)
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    edges.append(
                        RelationEdge(
                            subject_uri=current_uri,
                            predicate=predicate,
                            object_uri=target_uri,
                            evidence=str(relation_data.get("evidence", "")),
                            confidence=str(relation_data.get("confidence", "moderate")),
                        )
                    )

                if target_uri in seen_entities:
                    continue

                seen_entities.add(target_uri)
                try:
                    connected_item = self._load_item(target_uri, tier)
                except Exception:
                    logger.debug("Could not load connected entity %s", target_uri)
                    continue

                connected.append(connected_item)
                if remaining_hops > 1:
                    walk(target_uri, remaining_hops - 1)

        walk(entity_uri, hops)

        return GraphResult(root=root, connected=connected, relations=edges)

    # ------------------------------------------------------------------
    # Knowledge Graph shortcuts
    # ------------------------------------------------------------------

    def entities(
        self, entity_type: str | None = None, *, tier: Tier = Tier.L2
    ) -> list[ContextItem]:
        """List entities, optionally filtered by type."""
        if entity_type:
            plural = _ENTITY_TYPE_PLURALS[entity_type]
            uri = f"{build_knowledge_graph_uri()}/entities/{plural}"
        else:
            uri = f"{build_knowledge_graph_uri()}/entities"
        return self.browse(uri, tier=tier)

    def hypotheses(
        self, status: str | None = None, *, tier: Tier = Tier.L2
    ) -> list[ContextItem]:
        """List hypotheses, optionally filtered by status."""
        uri = f"{build_knowledge_graph_uri()}/hypotheses"
        items = self.browse(uri, tier=tier)
        if status:
            items = [i for i in items if i.metadata.get("status") == status]
        return items

    def timeline(
        self,
        project: str | None = None,
        since: str | None = None,
        *,
        tier: Tier = Tier.L2,
    ) -> list[ContextItem]:
        """List timeline events."""
        uri = build_timeline_uri()
        items = self.browse(uri, tier=tier)
        if project:
            items = [i for i in items if project in i.project_ids]
        if since:
            items = [i for i in items if i.metadata.get("date", "") >= since]
        return items

    # ------------------------------------------------------------------
    # Memory operations
    # ------------------------------------------------------------------

    def remember(
        self,
        store: str,
        title: str,
        body: str,
        *,
        entities: list[str] | None = None,
        projects: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """Create a memory resource.

        Parameters
        ----------
        store:
            Memory store name (journal, patterns, conversations).
        title:
            Title for the memory entry.
        body:
            Content body.
        entities:
            Optional entity references.
        projects:
            Optional project IDs.
        tags:
            Optional tags.

        Returns
        -------
        str
            URI of the created memory resource.
        """
        today = date.today().isoformat()
        slug = f"{today}_{slugify(title)}"
        file_name = _MEMORY_FILE_NAMES.get(store, "entry.md")
        uri = f"{build_memory_uri(store, slug)}/{file_name}"

        metadata: dict[str, Any] = {
            "title": title,
            "kind": "memory",
            "store": store,
            "date": today,
        }
        if entities:
            metadata["entities"] = entities
        if projects:
            metadata["project_ids"] = projects
        if tags:
            metadata["tags"] = tags

        # Generate L0/L1 via CBORG if extractor is available
        if self.extractor:
            try:
                abstract = self.extractor.generate_abstract(body)
                overview = self.extractor.generate_overview(body)
                metadata["abstract"] = abstract
                metadata["overview"] = overview
            except Exception:
                logger.debug("CBORG tier generation failed for memory %s", title)

        self.client.add_text_resource(
            uri=uri,
            content=body,
            metadata=metadata,
            reason=f"Remember: {title}",
        )
        return uri

    def recall(
        self, query: str, *, store: str | None = None, limit: int = 5
    ) -> list[ContextItem]:
        """Search memories by semantic query.

        Parameters
        ----------
        query:
            Natural language search query.
        store:
            Optional store to restrict search to.
        limit:
            Maximum results.
        """
        if store:
            target_uri = build_memory_uri(store)
        else:
            target_uri = f"{_ROOT}/memories"

        hits = self.client.search(query=query, target_uri=target_uri, limit=limit)
        items = []
        for hit in hits:
            try:
                item = self._load_item(hit["uri"], Tier.L2)
                items.append(item)
            except Exception:
                logger.warning("Failed to load memory hit %s", hit.get("uri"), exc_info=True)
        return items

    # ------------------------------------------------------------------
    # Ingest operations
    # ------------------------------------------------------------------

    def ingest_resource(
        self,
        uri: str,
        content: str,
        *,
        metadata: dict[str, Any] | None = None,
        generate_tiers: bool = True,
    ) -> None:
        """Ingest a resource into the observatory.

        Parameters
        ----------
        uri:
            Target URI.
        content:
            Resource text content.
        metadata:
            Optional metadata dict.
        generate_tiers:
            Whether to generate L0/L1 tiers via CBORG.
        """
        meta = metadata or {}

        if generate_tiers and self.extractor:
            try:
                abstract = self.extractor.generate_abstract(content)
                overview = self.extractor.generate_overview(content)
                meta["abstract"] = abstract
                meta["overview"] = overview
            except Exception:
                logger.debug("CBORG tier generation failed for %s", uri)

        self.client.add_text_resource(
            uri=uri,
            content=content,
            metadata=meta,
            reason=f"Ingest resource: {uri}",
        )

    def ingest_entity(
        self,
        entity_type: str,
        entity_id: str,
        profile: dict[str, Any],
        *,
        relations: list[dict[str, Any]] | None = None,
    ) -> str:
        """Create an entity with profile and relation files.

        Parameters
        ----------
        entity_type:
            Entity type (organism, gene, pathway, method, concept).
        entity_id:
            Entity identifier slug.
        profile:
            Profile data dict.
        relations:
            Optional list of relation dicts with subject, predicate,
            object, evidence, confidence.

        Returns
        -------
        str
            Entity URI.
        """
        entity_uri = build_entity_uri(entity_type, entity_id)
        profile_uri = f"{entity_uri}/profile.yaml"

        profile_content = yaml.safe_dump(profile, sort_keys=True)
        profile_meta = {
            "title": profile.get("name", entity_id),
            "kind": "entity",
            "entity_type": entity_type,
            "entity_id": entity_id,
        }

        self.client.add_text_resource(
            uri=profile_uri,
            content=profile_content,
            metadata=profile_meta,
            reason=f"Ingest entity profile: {entity_type}/{entity_id}",
        )

        for rel in relations or []:
            self._write_relation(entity_uri, rel)
            self._write_inverse_relation(entity_uri, rel)

        return entity_uri

    def _write_relation(self, entity_uri: str, rel: dict[str, Any]) -> None:
        """Write a forward relation file."""
        predicate = rel["predicate"]
        obj_ref = rel["object"]  # e.g. "genes/trpA"
        safe_name = f"{predicate}__{obj_ref.replace('/', '__')}"
        rel_uri = f"{entity_uri}/relations/{safe_name}.yaml"

        content = yaml.safe_dump(rel, sort_keys=True)
        self.client.add_text_resource(
            uri=rel_uri,
            content=content,
            metadata={"kind": "relation"},
            reason=f"Relation: {rel.get('subject')} {predicate} {obj_ref}",
        )

    def _write_inverse_relation(self, entity_uri: str, rel: dict[str, Any]) -> None:
        """Write an inverse relation at the object entity's location."""
        obj_ref = rel["object"]  # e.g. "genes/trpA"
        parts = obj_ref.split("/", 1)
        if len(parts) != 2:
            logger.debug("Cannot parse object ref for inverse: %s", obj_ref)
            return
        obj_plural, obj_id = parts

        obj_entity_uri = f"{_ROOT}/knowledge-graph/entities/{obj_plural}/{obj_id}"

        subj_ref = rel["subject"]  # e.g. "organisms/ecoli"
        predicate = rel["predicate"]
        safe_name = f"inv_{predicate}__{subj_ref.replace('/', '__')}"
        inv_uri = f"{obj_entity_uri}/relations/{safe_name}.yaml"

        inverse_rel = {
            "subject": obj_ref,
            "predicate": f"inverse_{predicate}",
            "object": subj_ref,
            "evidence": rel.get("evidence", ""),
            "confidence": rel.get("confidence", "moderate"),
        }
        content = yaml.safe_dump(inverse_rel, sort_keys=True)
        self.client.add_text_resource(
            uri=inv_uri,
            content=content,
            metadata={"kind": "relation"},
            reason=f"Inverse relation: {obj_ref} inverse_{predicate} {subj_ref}",
        )

    def _resolve_entity_ref(self, ref: str) -> str:
        """Resolve a short entity ref like ``genes/trpA`` to a full URI."""
        if ref.startswith("viking://"):
            return ref
        return f"{_ROOT}/knowledge-graph/entities/{ref}"

    def _parse_relation(self, raw: str) -> dict[str, Any]:
        """Parse relation content from frontmatter, YAML body, or both."""
        metadata, body = split_frontmatter(raw, {})
        if not body.strip():
            return metadata

        parsed_body = yaml.safe_load(body)
        if isinstance(parsed_body, dict):
            return {**parsed_body, **metadata}
        return metadata


def _ensure_list(val: Any) -> list[str]:
    """Coerce a value to a list of strings."""
    if val is None:
        return []
    if isinstance(val, list):
        return val
    return [str(val)]
