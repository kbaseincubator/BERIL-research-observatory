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
TIERS = (TIER_GROUNDED, TIER_ASSERTED, TIER_CONFLICT)

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


# --- per-project KG (kg.yaml) -----------------------------------------------------
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


# --- canonical graph --------------------------------------------------------------
@dataclass
class Node:
    id: str
    type: str
    label: str
    curie: Optional[str] = None
    tier: str = TIER_ASSERTED
    x: float = 0.0
    y: float = 0.0
    provenance: list[str] = field(default_factory=list)   # project ids contributing this node
    attrs: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Node":
        return cls(id=d["id"], type=d["type"], label=d["label"], curie=d.get("curie"),
                   tier=d.get("tier", TIER_ASSERTED), x=float(d.get("x", 0.0)), y=float(d.get("y", 0.0)),
                   provenance=list(d.get("provenance", [])), attrs=dict(d.get("attrs", {})))


@dataclass
class Edge:
    s: str
    p: str
    o: str
    tier: str = TIER_ASSERTED
    polarity: Optional[str] = None
    evidence: list[str] = field(default_factory=list)     # assertion ids backing this edge
    provenance: list[str] = field(default_factory=list)   # project ids

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Edge":
        return cls(s=d["s"], p=d["p"], o=d["o"], tier=d.get("tier", TIER_ASSERTED),
                   polarity=d.get("polarity"), evidence=list(d.get("evidence", [])),
                   provenance=list(d.get("provenance", [])))


@dataclass
class Graph:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)

    def node_by_id(self, nid: str) -> Optional[Node]:
        for n in self.nodes:
            if n.id == nid:
                return n
        return None

    def to_dict(self) -> dict:
        return {"nodes": [n.to_dict() for n in self.nodes], "edges": [e.to_dict() for e in self.edges]}

    @classmethod
    def from_dict(cls, d: dict) -> "Graph":
        return cls(nodes=[Node.from_dict(x) for x in d.get("nodes", [])],
                   edges=[Edge.from_dict(x) for x in d.get("edges", [])])


# --- corrections ------------------------------------------------------------------
@dataclass
class Correction:
    id: str
    targets: list[str]
    kind: str                       # retract|fix-value|reground|force-merge|force-split|promote|demote
    value: dict = field(default_factory=dict)
    scope: str = "instance"
    proposed_rule: Optional[dict] = None
    rationale: str = ""
    author: str = ""
    timestamp: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Correction":
        return cls(id=d["id"], targets=list(d.get("targets", [])), kind=d["kind"], value=dict(d.get("value", {})),
                   scope=d.get("scope", "instance"), proposed_rule=d.get("proposed_rule"),
                   rationale=d.get("rationale", ""), author=d.get("author", ""), timestamp=d.get("timestamp", ""))


# --- rendered page ----------------------------------------------------------------
@dataclass
class Page:
    slug: str
    title: str
    type: str
    sections: list[dict] = field(default_factory=list)   # [{"id","heading","fact_hash","html"|"facts"}]
    links: list[str] = field(default_factory=list)
    fact_hash: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
