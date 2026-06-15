"""Small runtime contracts for the Compendium topic wiki.

These dataclasses mirror the hand-written YAML contract in ``compendium/SCHEMA.md``.
They intentionally avoid LinkML/Biolink-style graph machinery: the graph exists only to
build bounded page contexts for human-readable wiki synthesis.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

STATEMENT_KINDS = ("finding", "claim", "caveat", "opportunity")
CONFIDENCE_LEVELS = ("low", "medium", "high")
LINK_KINDS = ("supports", "contradicts", "refines")
PAGE_TYPES = ("home", "topic", "data", "author", "organism")


def _require_nonempty(value: str | None, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")


def _validate_in(value: str, allowed: tuple[str, ...], field_name: str) -> None:
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}; got {value!r}")


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("expected a list")
    return [str(item) for item in value]


@dataclass
class EvidenceAnchor:
    source_project: str
    source_doc: str
    quote: str
    source_section: str | None = None
    notebook: str | None = None
    figure: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty(self.source_project, "source_project")
        _require_nonempty(self.source_doc, "source_doc")
        _require_nonempty(self.quote, "quote")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_project": self.source_project,
            "source_doc": self.source_doc,
            "source_section": self.source_section,
            "quote": self.quote,
            "notebook": self.notebook,
            "figure": self.figure,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EvidenceAnchor":
        quote = d.get("quote", d.get("exact"))
        return cls(
            source_project=d["source_project"],
            source_doc=d["source_doc"],
            source_section=d.get("source_section"),
            quote=quote,
            notebook=d.get("notebook"),
            figure=d.get("figure"),
        )


@dataclass
class StatementLinks:
    supports: list[str] = field(default_factory=list)
    contradicts: list[str] = field(default_factory=list)
    refines: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[str]]:
        return {
            "supports": list(self.supports),
            "contradicts": list(self.contradicts),
            "refines": list(self.refines),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> "StatementLinks":
        d = d or {}
        unsupported = sorted(set(d) - set(LINK_KINDS) - {"motivates", "requires_validation"})
        if unsupported:
            raise ValueError(f"unsupported statement link field(s): {unsupported}")
        return cls(
            supports=_as_string_list(d.get("supports", [])),
            contradicts=_as_string_list(d.get("contradicts", [])),
            refines=_as_string_list(d.get("refines", [])),
        )


@dataclass
class StatementCard:
    id: str
    kind: str
    text: str
    confidence: str
    topics: list[str]
    entities: list[str]
    evidence: list[EvidenceAnchor]
    links: StatementLinks = field(default_factory=StatementLinks)

    def __post_init__(self) -> None:
        _require_nonempty(self.id, "id")
        _require_nonempty(self.text, "text")
        _validate_in(self.kind, STATEMENT_KINDS, "kind")
        _validate_in(self.confidence, CONFIDENCE_LEVELS, "confidence")
        if not self.evidence:
            raise ValueError("evidence is required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "text": self.text,
            "confidence": self.confidence,
            "topics": list(self.topics),
            "entities": list(self.entities),
            "links": self.links.to_dict(),
            "evidence": [anchor.to_dict() for anchor in self.evidence],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "StatementCard":
        about = d.get("about", {})
        raw_evidence = d["evidence"]
        if isinstance(raw_evidence, dict):
            raw_evidence = [raw_evidence]
        if not isinstance(raw_evidence, list):
            raise ValueError("evidence must be a list")
        return cls(
            id=d["id"],
            kind=d["kind"],
            text=d.get("text", d.get("statement")),
            confidence=d["confidence"],
            topics=_as_string_list(d.get("topics", about.get("topics", []))),
            entities=_as_string_list(d.get("entities", about.get("entities", []))),
            links=StatementLinks.from_dict(d.get("links")),
            evidence=[EvidenceAnchor.from_dict(item) for item in raw_evidence],
        )


@dataclass
class PageSectionPlan:
    id: str
    heading: str
    member_statement_ids: list[str] = field(default_factory=list)
    member_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PageSectionPlan":
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "member_statement_ids": list(self.member_statement_ids),
            "sections": [section.to_dict() for section in self.sections],
            "outgoing_links": list(self.outgoing_links),
            "backlinks": list(self.backlinks),
            "member_hash": self.member_hash,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PagePlan":
        return cls(
            id=d["id"],
            type=d["type"],
            title=d["title"],
            member_statement_ids=list(d.get("member_statement_ids", [])),
            sections=[PageSectionPlan.from_dict(item) for item in d.get("sections", [])],
            outgoing_links=list(d.get("outgoing_links", [])),
            backlinks=list(d.get("backlinks", [])),
            member_hash=d["member_hash"],
        )
