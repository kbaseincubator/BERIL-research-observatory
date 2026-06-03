"""Shared data contracts for the Compendium pipeline.

Every module codes against these dataclasses. They are plain stdlib dataclasses (no third-party
runtime dep) with ``to_dict``/``from_dict`` for YAML/JSON round-tripping. The LinkML schema in
``compendium/schema/compendium.yaml`` is the canonical type spec; these mirror it at runtime.

Tier vocabulary (deterministic, entities-only — no tier claims the *relation* is true):
  - ``grounded``: all referenced entities are grounded (CURIE) and the evidence span is located.
  - ``asserted``: ungrounded entity / weak-or-missing span / low confidence -> flagged in the wiki.
  - ``conflict``: a grounded assertion that contradicts another grounded assertion.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional

# --- vocabularies -----------------------------------------------------------------
TIER_GROUNDED = "grounded"
TIER_ASSERTED = "asserted"
TIER_CONFLICT = "conflict"
TIER_REVIEWED = "reviewed"
TIER_RETRACTED = "retracted"
TIERS = (TIER_GROUNDED, TIER_ASSERTED, TIER_CONFLICT)
STATEMENT_TIERS = (TIER_ASSERTED, TIER_GROUNDED, TIER_REVIEWED, TIER_CONFLICT, TIER_RETRACTED)

# Synthesis-unit (Layer A) and biology (Layer B) entity types.
SYNTHESIS_TYPES = (
    "Topic", "Claim", "Conflict", "Opportunity", "Direction", "Hypothesis",
    "Finding", "DerivedProduct", "Method",
)
BIOLOGY_TYPES = (
    "Organism", "Gene", "GeneCluster", "KO", "OrthologGroup", "Pathway", "Function",
    "Metabolite", "Phenotype", "Condition", "Environment", "Dataset", "Notebook",
    "Project", "Publication",
)
ASSERTION_KINDS = ("relation", "finding", "claim", "opportunity", "hypothesis", "direction")
STATEMENT_KINDS = (
    "finding", "claim", "caveat", "conflict", "hypothesis", "opportunity",
    "direction", "method_note", "derived_product",
)
STATEMENT_SCOPES = ("project_local", "cross_project", "corpus_level", "hypothesis")
CONFIDENCE_LEVELS = ("low", "medium", "high")
PAGE_TYPES = (
    "home", "topic", "claim", "conflict", "opportunity", "direction", "hypothesis",
    "derived_product", "method", "project", "finding", "source_section", "dataset",
    "notebook", "publication", "entity", "organism", "gene", "KO", "ortholog_group",
    "pathway", "phenotype", "condition", "environment", "data_collection",
)

SCIENTIFIC_EDGE_KINDS = (
    "supports", "contradicts", "refines", "generalizes", "narrows", "motivates", "tests",
)
PROVENANCE_EDGE_KINDS = (
    "has_evidence", "extracted_from", "cites", "uses_dataset", "uses_notebook",
)
NAVIGATION_EDGE_KINDS = (
    "about_entity",
    "related_page",
    "member_of_topic",
    "backlink",
    "next_read",
)
DERIVATION_EDGE_KINDS = ("produced_by", "reused_by", "depends_on", "derived_from")
REVIEW_EDGE_KINDS = (
    "needs_review", "caveat_for", "resolves_conflict", "supersedes", "retracted_by",
)
EDGE_CLASS_PREDICATES = {
    "scientific_edge": SCIENTIFIC_EDGE_KINDS,
    "provenance_edge": PROVENANCE_EDGE_KINDS,
    "navigation_edge": NAVIGATION_EDGE_KINDS,
    "derivation_edge": DERIVATION_EDGE_KINDS,
    "review_edge": REVIEW_EDGE_KINDS,
}
EDGE_CLASSES = tuple(EDGE_CLASS_PREDICATES)
EDGE_KINDS = tuple(p for predicates in EDGE_CLASS_PREDICATES.values() for p in predicates)


def _require_nonempty(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")


def _validate_in(value: str, allowed: tuple[str, ...], field_name: str) -> None:
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}; got {value!r}")


# --- statement-card KG -------------------------------------------------------------
@dataclass
class AboutRefs:
    entities: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "AboutRefs":
        return cls(entities=list(d.get("entities", [])), topics=list(d.get("topics", [])))


@dataclass
class StatementLinks:
    supports: list[str] = field(default_factory=list)
    contradicts: list[str] = field(default_factory=list)
    motivates: list[str] = field(default_factory=list)
    refines: list[str] = field(default_factory=list)
    requires_validation: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "StatementLinks":
        return cls(
            supports=list(d.get("supports", [])),
            contradicts=list(d.get("contradicts", [])),
            motivates=list(d.get("motivates", [])),
            refines=list(d.get("refines", [])),
            requires_validation=list(d.get("requires_validation", [])),
        )


@dataclass
class EvidenceAnchor:
    source_project: str
    source_doc: str
    exact: str
    source_section: Optional[str] = None
    prefix: str = ""
    suffix: str = ""
    notebook: Optional[str] = None
    figure: Optional[str] = None
    p_value: Optional[float] = None

    def __post_init__(self) -> None:
        _require_nonempty(self.source_project, "source_project")
        _require_nonempty(self.source_doc, "source_doc")
        _require_nonempty(self.exact, "exact")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "EvidenceAnchor":
        return cls(
            source_project=d["source_project"],
            source_doc=d["source_doc"],
            source_section=d.get("source_section"),
            exact=d["exact"],
            prefix=d.get("prefix", ""),
            suffix=d.get("suffix", ""),
            notebook=d.get("notebook"),
            figure=d.get("figure"),
            p_value=d.get("p_value"),
        )


@dataclass
class ExtractionManifest:
    agent_type: str
    skill: str
    model: str
    prompt_hash: str
    context_pack_hash: str
    repo_commit: str
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ExtractionManifest":
        return cls(
            agent_type=d["agent_type"],
            skill=d["skill"],
            model=d["model"],
            prompt_hash=d["prompt_hash"],
            context_pack_hash=d["context_pack_hash"],
            repo_commit=d["repo_commit"],
            timestamp=d["timestamp"],
        )


@dataclass
class StatementCard:
    id: str
    kind: str
    statement: str
    scope: str
    tier: str
    confidence: str
    about: AboutRefs
    links: StatementLinks
    qualifiers: dict[str, str]
    evidence: EvidenceAnchor
    extraction: ExtractionManifest

    def __post_init__(self) -> None:
        _require_nonempty(self.id, "id")
        _require_nonempty(self.statement, "statement")
        _validate_in(self.kind, STATEMENT_KINDS, "kind")
        _validate_in(self.scope, STATEMENT_SCOPES, "scope")
        _validate_in(self.tier, STATEMENT_TIERS, "tier")
        _validate_in(self.confidence, CONFIDENCE_LEVELS, "confidence")
        if self.evidence is None:
            raise ValueError("evidence is required")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "statement": self.statement,
            "scope": self.scope,
            "tier": self.tier,
            "confidence": self.confidence,
            "about": self.about.to_dict(),
            "links": self.links.to_dict(),
            "qualifiers": dict(self.qualifiers),
            "evidence": self.evidence.to_dict(),
            "extraction": self.extraction.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StatementCard":
        return cls(
            id=d["id"],
            kind=d["kind"],
            statement=d["statement"],
            scope=d["scope"],
            tier=d["tier"],
            confidence=d["confidence"],
            about=AboutRefs.from_dict(d["about"]),
            links=StatementLinks.from_dict(d["links"]),
            qualifiers=dict(d.get("qualifiers", {})),
            evidence=EvidenceAnchor.from_dict(d["evidence"]),
            extraction=ExtractionManifest.from_dict(d["extraction"]),
        )


@dataclass
class StatementEdge:
    s: str
    p: str
    o: str
    edge_class: str
    statement_ids: list[str] = field(default_factory=list)
    provenance: list[str] = field(default_factory=list)
    attrs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_in(self.edge_class, EDGE_CLASSES, "edge_class")
        _validate_in(self.p, EDGE_CLASS_PREDICATES[self.edge_class], "p")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "StatementEdge":
        return cls(
            s=d["s"],
            p=d["p"],
            o=d["o"],
            edge_class=d["edge_class"],
            statement_ids=list(d.get("statement_ids", [])),
            provenance=list(d.get("provenance", [])),
            attrs=dict(d.get("attrs", {})),
        )


@dataclass
class PageSectionPlan:
    id: str
    heading: str
    member_statement_ids: list[str] = field(default_factory=list)
    member_hash: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "PageSectionPlan":
        return cls(
            id=d["id"],
            heading=d["heading"],
            member_statement_ids=list(d.get("member_statement_ids", [])),
            member_hash=d.get("member_hash", ""),
        )


@dataclass
class PagePlan:
    id: str
    type: str
    title: str
    member_statement_ids: list[str]
    sections: list[PageSectionPlan]
    outgoing_links: list[str]
    backlinks: list[str]
    member_hash: str

    def __post_init__(self) -> None:
        _require_nonempty(self.id, "id")
        _require_nonempty(self.title, "title")
        _validate_in(self.type, PAGE_TYPES, "type")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "member_statement_ids": list(self.member_statement_ids),
            "sections": [s.to_dict() for s in self.sections],
            "outgoing_links": list(self.outgoing_links),
            "backlinks": list(self.backlinks),
            "member_hash": self.member_hash,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PagePlan":
        return cls(
            id=d["id"],
            type=d["type"],
            title=d["title"],
            member_statement_ids=list(d.get("member_statement_ids", [])),
            sections=[PageSectionPlan.from_dict(x) for x in d.get("sections", [])],
            outgoing_links=list(d.get("outgoing_links", [])),
            backlinks=list(d.get("backlinks", [])),
            member_hash=d["member_hash"],
        )


# --- lower-level transition KG (kg.yaml) -------------------------------------------
@dataclass
class Span:
    file: str
    char: tuple[int, int] = (0, 0)
    heading: Optional[str] = None
    quote: str = ""

    def to_dict(self) -> dict:
        return {"file": self.file, "char": list(self.char), "heading": self.heading, "quote": self.quote}

    @classmethod
    def from_dict(cls, d: dict) -> "Span":
        c = d.get("char") or [0, 0]
        return cls(file=d["file"], char=(int(c[0]), int(c[1])), heading=d.get("heading"), quote=d.get("quote", ""))


@dataclass
class Mention:
    id: str
    label: str
    type: str
    span: Optional[Span] = None

    def to_dict(self) -> dict:
        return {"id": self.id, "label": self.label, "type": self.type,
                "span": self.span.to_dict() if self.span else None}

    @classmethod
    def from_dict(cls, d: dict) -> "Mention":
        return cls(id=d["id"], label=d["label"], type=d["type"],
                   span=Span.from_dict(d["span"]) if d.get("span") else None)


@dataclass
class Entity:
    node: str            # content-addressed canonical node id (see ids.node_id)
    type: str
    label: str
    curie: Optional[str] = None
    mentions: list[str] = field(default_factory=list)
    confidence: float = 1.0
    tier: str = TIER_ASSERTED

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Entity":
        return cls(node=d["node"], type=d["type"], label=d["label"], curie=d.get("curie"),
                   mentions=list(d.get("mentions", [])), confidence=float(d.get("confidence", 1.0)),
                   tier=d.get("tier", TIER_ASSERTED))


@dataclass
class Evidence:
    span: Optional[Span] = None
    notebook: Optional[str] = None
    figure: Optional[str] = None
    dataset: Optional[str] = None
    p_value: Optional[float] = None

    def to_dict(self) -> dict:
        return {"span": self.span.to_dict() if self.span else None, "notebook": self.notebook,
                "figure": self.figure, "dataset": self.dataset, "p_value": self.p_value}

    @classmethod
    def from_dict(cls, d: dict) -> "Evidence":
        return cls(span=Span.from_dict(d["span"]) if d.get("span") else None, notebook=d.get("notebook"),
                   figure=d.get("figure"), dataset=d.get("dataset"), p_value=d.get("p_value"))


@dataclass
class Assertion:
    id: str                          # content-addressed (see ids.assertion_id)
    kind: str                        # one of ASSERTION_KINDS
    s: Optional[str] = None          # subject node id (relation)
    p: Optional[str] = None          # predicate
    o: Optional[str] = None          # object node id (relation)
    polarity: Optional[str] = None   # "positive" | "negative"
    statement: Optional[str] = None  # for finding/claim/opportunity/etc.
    supported_by: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    evidence: Optional[Evidence] = None
    extractor: dict = field(default_factory=lambda: {"agent_type": "automated_agent", "confidence": 1.0})
    tier: str = TIER_ASSERTED

    def to_dict(self) -> dict:
        d = asdict(self)
        d["evidence"] = self.evidence.to_dict() if self.evidence else None
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Assertion":
        return cls(id=d["id"], kind=d["kind"], s=d.get("s"), p=d.get("p"), o=d.get("o"),
                   polarity=d.get("polarity"), statement=d.get("statement"),
                   supported_by=list(d.get("supported_by", [])), entities=list(d.get("entities", [])),
                   evidence=Evidence.from_dict(d["evidence"]) if d.get("evidence") else None,
                   extractor=dict(d.get("extractor", {})), tier=d.get("tier", TIER_ASSERTED))


@dataclass
class ProjectMeta:
    id: str
    title: str
    authors: list[dict] = field(default_factory=list)
    status: Optional[str] = None
    report_hash: Optional[str] = None
    stage1_coverage: float = 0.0
    extraction: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ProjectMeta":
        return cls(id=d["id"], title=d.get("title", d["id"]), authors=list(d.get("authors", [])),
                   status=d.get("status"), report_hash=d.get("report_hash"),
                   stage1_coverage=float(d.get("stage1_coverage", 0.0)), extraction=dict(d.get("extraction", {})))


@dataclass
class ProjectKG:
    """One project's contribution to the KG — serialized as ``kg/<project>.kg.yaml``."""
    project: ProjectMeta
    mentions: list[Mention] = field(default_factory=list)
    entities: list[Entity] = field(default_factory=list)
    assertions: list[Assertion] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"project": self.project.to_dict(),
                "mentions": [m.to_dict() for m in self.mentions],
                "entities": [e.to_dict() for e in self.entities],
                "assertions": [a.to_dict() for a in self.assertions]}

    @classmethod
    def from_dict(cls, d: dict) -> "ProjectKG":
        return cls(project=ProjectMeta.from_dict(d["project"]),
                   mentions=[Mention.from_dict(x) for x in d.get("mentions", [])],
                   entities=[Entity.from_dict(x) for x in d.get("entities", [])],
                   assertions=[Assertion.from_dict(x) for x in d.get("assertions", [])])
