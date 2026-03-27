"""Tests for the OpenViking-backed context service."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from observatory_context.render import RenderLevel


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class FakeOpenVikingClient:
    """Small in-memory fake for Phase 2 service tests."""

    def __init__(self) -> None:
        self.resources: dict[str, dict[str, object]] = {}
        self.links: dict[str, list[dict[str, str]]] = {}
        self.search_calls = 0
        self.fail_semantic_search = False

    def add_text_resource(self, uri: str, content: str, metadata: dict[str, object]) -> None:
        self.resources[uri] = {"uri": uri, "content": content, "metadata": metadata}

    def list_resources(self, uri: str, recursive: bool = False) -> list[dict[str, object]]:
        results: list[dict[str, object]] = []
        prefix = uri.rstrip("/")
        for resource_uri in sorted(self.resources):
            if recursive:
                if resource_uri.startswith(prefix):
                    results.append({"uri": resource_uri})
            elif resource_uri.rsplit("/", 1)[0] == prefix:
                results.append({"uri": resource_uri})
        return results

    def read_resource(self, uri: str) -> str:
        return str(self.resources[uri]["content"])

    def stat_resource(self, uri: str) -> dict[str, object]:
        resource = self.resources[uri]
        return {"uri": uri, "metadata": resource["metadata"]}

    def search(self, query: str, target_uri: str | None = None) -> list[dict[str, object]]:
        self.search_calls += 1
        if self.fail_semantic_search:
            raise RuntimeError("semantic retrieval unavailable")
        query_lower = query.lower()
        results = []
        for uri, resource in self.resources.items():
            if target_uri and not uri.startswith(target_uri):
                continue
            if query_lower in str(resource["content"]).lower():
                results.append({"uri": uri, "score": 1.0})
        return results

    def make_directory(self, uri: str) -> None:
        return None

    def link_resources(self, from_uri: str, uris: list[str], reason: str = "") -> None:
        self.links.setdefault(from_uri, [])
        for uri in uris:
            self.links[from_uri].append({"uri": uri, "reason": reason})

    def relations(self, uri: str) -> list[dict[str, str]]:
        return self.links.get(uri, [])

    def add_note_resource(self, uri: str, content: str, metadata: dict[str, object]) -> None:
        self.resources[uri] = {"uri": uri, "content": content, "metadata": metadata}


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    _write(
        tmp_path / "docs" / "project_registry.yaml",
        """
projects:
  - id: alpha_proj
    title: Alpha Project
    status: complete
    tags: [metal-stress, fitness]
    research_question: How does alpha respond?
  - id: beta_proj
    title: Beta Project
    status: in-progress
    tags: [fitness, regulation]
    research_question: How does beta respond?
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "docs" / "figure_catalog.yaml",
        """
figure_count: 1
figures:
  - id: alpha_proj__main
    project_id: alpha_proj
    figure_file: figures/main.png
    caption: Main alpha figure
    tags: [metal-stress]
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "knowledge" / "entities" / "organisms.yaml",
        """\
organisms:
  - id: org_alpha
    name: Alpha organism
    strain: Alpha-1
    projects:
      - alpha_proj
  - id: org_beta
    name: Beta organism
    projects:
      - beta_proj
""",
    )
    _write(
        tmp_path / "knowledge" / "entities" / "concepts.yaml",
        """\
concepts:
  - id: conc_fitness
    name: Fitness
    projects:
      - alpha_proj
      - beta_proj
""",
    )
    _write(
        tmp_path / "knowledge" / "entities" / "genes.yaml",
        "genes: []\n",
    )
    _write(
        tmp_path / "knowledge" / "entities" / "pathways.yaml",
        "pathways: []\n",
    )
    _write(
        tmp_path / "knowledge" / "entities" / "methods.yaml",
        "methods: []\n",
    )
    _write(
        tmp_path / "knowledge" / "relations.yaml",
        """\
relations:
  - subject: org_alpha
    predicate: studied_in
    object: conc_fitness
    evidence_project: alpha_proj
    confidence: high
  - subject: org_beta
    predicate: studied_in
    object: conc_fitness
    evidence_project: beta_proj
    confidence: high
""",
    )
    _write(
        tmp_path / "knowledge" / "hypotheses.yaml",
        """\
hypotheses:
  - id: H001
    statement: Alpha and Beta share fitness patterns.
    status: testing
    origin_project: alpha_proj
""",
    )
    _write(
        tmp_path / "projects" / "alpha_proj" / "README.md",
        "# Alpha Project\n\nQuestion: How does alpha respond?\n",
    )
    _write(
        tmp_path / "projects" / "alpha_proj" / "REPORT.md",
        "# Report\n\nAlpha report body mentions org_adp1 and metal stress.\n",
    )
    _write(
        tmp_path / "projects" / "alpha_proj" / "provenance.yaml",
        """
project_id: alpha_proj
created_at: 2026-03-18
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "projects" / "alpha_proj" / "figures" / "main.png",
        "not a real png, just a fixture\n",
    )
    _write(
        tmp_path / "projects" / "beta_proj" / "README.md",
        "# Beta Project\n\nQuestion: How does beta respond?\n",
    )
    _write(
        tmp_path / "projects" / "beta_proj" / "REPORT.md",
        "# Beta Report\n\nBeta report body.\n",
    )
    _write(
        tmp_path / "projects" / "beta_proj" / "provenance.yaml",
        """
project_id: beta_proj
created_at: 2026-03-19
""".strip()
        + "\n",
    )
    return tmp_path


@pytest.fixture
def service(sample_repo: Path) -> object:
    from observatory_context.service import ObservatoryContextService

    client = FakeOpenVikingClient()
    return ObservatoryContextService(
        repo_root=sample_repo,
        client=client,
        now_factory=lambda: "2026-03-19T12:00:00Z",
    )


def test_get_resource_returns_deterministic_views(service: object) -> None:
    resource = service.get_resource("alpha_proj", detail_level=RenderLevel.L1)

    assert resource.resource.id == "alpha_proj"
    assert resource.resource.uri.endswith("/projects/alpha_proj/authored/README.md")
    assert "How does alpha respond?" in resource.rendered

    by_uri = service.get_resource(resource.resource.uri, detail_level=RenderLevel.L2)
    assert "```yaml" in by_uri.rendered
    assert by_uri.resource.kind == "project"


def test_get_project_workspace_lists_authored_resources(service: object) -> None:
    workspace = service.get_project_workspace("alpha_proj", detail_level=RenderLevel.L0)

    assert workspace.project_id == "alpha_proj"
    assert workspace.workspace_uri.endswith("/projects/alpha_proj")
    assert workspace.project_resource.id == "alpha_proj"
    assert {resource.kind for resource in workspace.resources} == {
        "project",
        "project_document",
        "figure",
    }


def test_list_project_resources_supports_kind_filter(service: object) -> None:
    figures = service.list_project_resources("alpha_proj", kind="figure")

    assert len(figures) == 1
    assert figures[0].uri.endswith("/authored/figures/alpha_proj__main")


def test_search_context_falls_back_to_lexical_metadata_search(service: object) -> None:
    service.client.fail_semantic_search = True

    results = service.search_context("org_adp1", detail_level=RenderLevel.L0)

    assert service.client.search_calls == 1
    assert [result.resource.id for result in results] == ["alpha_proj"]
    assert "Alpha Project" in results[0].rendered


def test_search_context_accepts_findresult_style_semantic_hits(service: object) -> None:
    report_uri = "viking://resources/observatory/projects/alpha_proj/authored/REPORT.md"
    service.client.search = lambda query, target_uri=None: SimpleNamespace(
        resources=[
            SimpleNamespace(
                uri=f"{report_uri}/Nested_Section/.abstract.md",
                score=0.8,
            )
        ]
    )

    results = service.search_context("metal stress", detail_level=RenderLevel.L1)

    assert [result.resource.uri for result in results] == [report_uri]
    assert "Alpha report body" in results[0].rendered


def test_related_resources_are_metadata_and_link_driven(service: object) -> None:
    note = service.add_note(
        project_id="alpha_proj",
        title="Alpha follow-up",
        body="Cross-reference the main figure and report.",
        tags=["metal-stress"],
        links=["viking://resources/observatory/projects/alpha_proj/authored/figures/alpha_proj__main"],
    )

    related = service.related_resources("alpha_proj", limit=5)
    related_uris = [resource.uri for resource in related]

    assert any(uri.endswith("/authored/REPORT.md") for uri in related_uris)
    assert any(uri.endswith("/authored/figures/alpha_proj__main") for uri in related_uris)
    assert note.resource.uri in related_uris


def test_add_note_and_observation_are_visible_to_subsequent_reads(service: object) -> None:
    note = service.add_note(
        project_id="alpha_proj",
        title="Shared note",
        body="A live note for other clients.",
        tags=["live-context"],
        links=["viking://resources/observatory/projects/alpha_proj/authored/REPORT.md"],
    )
    observation = service.add_observation(
        project_id="alpha_proj",
        source_ref="projects/alpha_proj/REPORT.md",
        body="Observed a strong lexical fallback hit for org_adp1.",
        tags=["observation"],
        links=[note.resource.uri],
    )

    resources = service.list_project_resources("alpha_proj")
    resource_ids = {resource.id for resource in resources}

    assert note.resource.id in resource_ids
    assert observation.resource.id in resource_ids

    note_read = service.get_resource(note.resource.uri, detail_level=RenderLevel.L2)
    assert "A live note for other clients." in note_read.rendered

    search_results = service.search_context("lexical fallback", project="alpha_proj")
    assert [result.resource.id for result in search_results] == [observation.resource.id]


# --- Knowledge graph integration tests ---


@pytest.fixture
def offline_service(sample_repo: Path) -> object:
    from observatory_context.service import ObservatoryContextService

    return ObservatoryContextService(
        repo_root=sample_repo,
        client=None,
        now_factory=lambda: "2026-03-19T12:00:00Z",
    )


def test_search_context_boosts_entity_linked_projects(offline_service: object) -> None:
    results = offline_service.search_context("alpha respond", detail_level=RenderLevel.L0)

    project_ids = [r.resource.id for r in results if r.resource.kind == "project"]
    assert "alpha_proj" in project_ids


def test_related_resources_use_graph_connections(offline_service: object) -> None:
    related = offline_service.related_resources("alpha_proj", limit=10)

    related_ids = {r.id for r in related}
    assert "beta_proj" in related_ids


def test_get_entity_returns_knowledge_entity(offline_service: object) -> None:
    entity = offline_service.get_entity("org_alpha")

    assert entity is not None
    assert entity["name"] == "Alpha organism"
    assert entity["kind"] == "organism"
    assert "alpha_proj" in entity["projects"]


def test_get_entity_returns_none_for_unknown(offline_service: object) -> None:
    assert offline_service.get_entity("nonexistent") is None


def test_list_entities_filters_by_kind(offline_service: object) -> None:
    organisms = offline_service.list_entities(kind="organism")
    assert len(organisms) == 2
    assert all(e["kind"] == "organism" for e in organisms)

    concepts = offline_service.list_entities(kind="concept")
    assert len(concepts) == 1
    assert concepts[0]["id"] == "conc_fitness"

    all_entities = offline_service.list_entities()
    assert len(all_entities) == 3  # 2 organisms + 1 concept


def test_entity_connections_returns_relations(offline_service: object) -> None:
    connections = offline_service.entity_connections("org_alpha")

    assert len(connections) == 1
    assert connections[0]["predicate"] == "studied_in"
    assert connections[0]["object"] == "conc_fitness"

    connections = offline_service.entity_connections("conc_fitness")
    assert len(connections) == 2


# --- Client wrapper tests ---


class FakeUnderlyingClient:
    """Minimal fake for the raw OpenViking SyncHTTPClient."""

    def __init__(self) -> None:
        self.find_calls: list[dict] = []
        self.grep_calls: list[dict] = []
        self.glob_calls: list[dict] = []
        self.abstract_calls: list[str] = []
        self.overview_calls: list[str] = []

    def find(self, query, target_uri="", limit=10, score_threshold=None, filter=None, **kw):
        self.find_calls.append({
            "query": query, "target_uri": target_uri,
            "limit": limit, "score_threshold": score_threshold, "filter": filter,
        })
        return []

    def grep(self, uri, pattern, case_insensitive=False, **kw):
        self.grep_calls.append({"uri": uri, "pattern": pattern, "case_insensitive": case_insensitive})
        return {"matches": []}

    def glob(self, pattern, uri="viking://", **kw):
        self.glob_calls.append({"pattern": pattern, "uri": uri})
        return {"matches": []}

    def abstract(self, uri):
        self.abstract_calls.append(uri)
        return "L0 abstract text"

    def overview(self, uri):
        self.overview_calls.append(uri)
        return "L1 overview text"

    def health(self):
        return True

    def initialize(self):
        pass


def _make_client_with_fake():
    from observatory_context.client import OpenVikingObservatoryClient
    from observatory_context.config import ObservatoryContextSettings

    settings = ObservatoryContextSettings(openviking_url="http://localhost:1933")
    client = OpenVikingObservatoryClient(settings)
    fake = FakeUnderlyingClient()
    client._client = fake
    return client, fake


def test_client_search_passes_filter_limit_threshold():
    client, fake = _make_client_with_fake()
    client.search("metal stress", limit=3, score_threshold=0.5, filter={"kind": "project"})
    assert len(fake.find_calls) == 1
    call = fake.find_calls[0]
    assert call["query"] == "metal stress"
    assert call["limit"] == 3
    assert call["score_threshold"] == 0.5
    assert call["filter"] == {"kind": "project"}


def test_client_grep_delegates():
    client, fake = _make_client_with_fake()
    result = client.grep("viking://resources/observatory", "cadA", case_insensitive=True)
    assert len(fake.grep_calls) == 1
    assert fake.grep_calls[0]["pattern"] == "cadA"
    assert fake.grep_calls[0]["case_insensitive"] is True
    assert result == {"matches": []}


def test_client_glob_delegates():
    client, fake = _make_client_with_fake()
    result = client.glob("*.yaml", uri="viking://resources/observatory")
    assert len(fake.glob_calls) == 1
    assert fake.glob_calls[0]["pattern"] == "*.yaml"
    assert result == {"matches": []}


def test_client_abstract_delegates():
    client, fake = _make_client_with_fake()
    result = client.abstract("viking://resources/observatory/projects/alpha/authored/README.md")
    assert result == "L0 abstract text"
    assert len(fake.abstract_calls) == 1


def test_client_overview_delegates():
    client, fake = _make_client_with_fake()
    result = client.overview("viking://resources/observatory/projects/alpha/authored/README.md")
    assert result == "L1 overview text"
    assert len(fake.overview_calls) == 1
