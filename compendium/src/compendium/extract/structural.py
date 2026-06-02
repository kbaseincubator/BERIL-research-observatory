"""Stage-1 deterministic structural extractor.

Parses a project's ``REPORT.md`` (and optional ``beril.yaml``) into a
:class:`~compendium.models.ProjectKG` using only regex/structure — no LLM, no network.
Identity is content-addressed via :mod:`compendium.ids`, so re-extraction is idempotent and
organism canonicalization yields the same node id across projects.
"""

from __future__ import annotations

import pathlib
import re
from typing import Optional

import yaml

from compendium import ids
from compendium.models import (
    Assertion,
    Entity,
    Evidence,
    Mention,
    ProjectKG,
    ProjectMeta,
    Span,
    TIER_ASSERTED,
)

_DICT_PATH = pathlib.Path(__file__).resolve().parent.parent / "ground" / "dictionary.yaml"

# Section headings (## ...).
_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
# Numbered findings: '### N. <statement>'.
_FINDING_RE = re.compile(r"^###\s+\d+\.\s+(.+?)\s*$", re.MULTILINE)
# Bullets.
_BULLET_RE = re.compile(r"^\s*[-*]\s+(.+?)\s*$", re.MULTILINE)
# Backticked tokens.
_BACKTICK_RE = re.compile(r"`([^`]+)`")
# 'BERDL collection <name>' (name may be backticked).
_BERDL_RE = re.compile(r"BERDL\s+collection\s+`?([\w./:-]+)`?")
# PMIDs.
_PMID_RE = re.compile(r"PMID:\d+")
# Gene / ortholog ids.
_KO_RE = re.compile(r"\bK\d{5}\b")
_COG_RE = re.compile(r"\bCOG\d{3,4}\b")
_PF_RE = re.compile(r"\bPF\d{5}\b")
# Generated-output artifacts to exclude from datasets (file paths / extensions).
_ARTIFACT_RE = re.compile(r"(/|\.[A-Za-z0-9]{1,5}$)")


def _read_report(project_dir: pathlib.Path) -> str:
    path = project_dir / "REPORT.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _parse_title(report_text: str, fallback: str) -> str:
    for line in report_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            if title.lower().startswith("report:"):
                title = title[len("report:"):].strip()
            return title
    return fallback


def _load_beril(project_dir: pathlib.Path) -> dict:
    path = project_dir / "beril.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _sections(report_text: str) -> list[tuple[str, int, int]]:
    """Return (heading, body_start, body_end) for each ``## heading`` section."""
    matches = list(_SECTION_RE.finditer(report_text))
    out: list[tuple[str, int, int]] = []
    for i, m in enumerate(matches):
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(report_text)
        out.append((m.group(1).strip(), body_start, body_end))
    return out


def _section_body(sections: list[tuple[str, int, int]], heading: str) -> Optional[tuple[int, int]]:
    for h, start, end in sections:
        if h.lower() == heading.lower():
            return (start, end)
    return None


def _load_organism_dict() -> dict[str, dict]:
    if not _DICT_PATH.exists():
        return {}
    data = yaml.safe_load(_DICT_PATH.read_text(encoding="utf-8")) or {}
    return data.get("organisms", {}) if isinstance(data, dict) else {}


def extract_project(project_dir: pathlib.Path, audit: dict | None = None) -> ProjectKG:
    """Deterministically extract a :class:`ProjectKG` from ``project_dir/REPORT.md``."""
    project_dir = pathlib.Path(project_dir)
    report_text = _read_report(project_dir)
    pid = project_dir.name
    title = _parse_title(report_text, fallback=pid)

    beril = _load_beril(project_dir)
    audit = audit or {}
    coverage = float(audit.get("stage1_coverage", audit.get("coverage", 0.0)))
    meta = ProjectMeta(
        id=pid,
        title=title,
        authors=list(beril.get("authors", [])),
        status=beril.get("status"),
        report_hash=ids.content_hash(report_text),
        stage1_coverage=coverage,
    )

    project_node = ids.node_id(title, "Project")

    entities: dict[str, Entity] = {}
    mentions: list[Mention] = []
    assertions: list[Assertion] = []
    seen_assertion_ids: set[str] = set()

    def add_entity(label: str, type_: str) -> str:
        node = ids.node_id(label, type_)
        if node not in entities:
            entities[node] = Entity(node=node, type=type_, label=label, tier=TIER_ASSERTED)
        return node

    def add_mention(label: str, type_: str, span: Span) -> None:
        mentions.append(
            Mention(id=f"{pid}/m/{len(mentions)}", label=label, type=type_, span=span)
        )

    def add_assertion(a: Assertion) -> None:
        if a.id in seen_assertion_ids:
            return
        seen_assertion_ids.add(a.id)
        assertions.append(a)

    # Project entity (label only — node id is canonical).
    add_entity(title, "Project")
    entities[project_node].curie = f"BERILProject:{pid}"

    sections = _sections(report_text)

    # --- Findings: '### N. <statement>' under '## Key Findings' --------------------
    kf = _section_body(sections, "Key Findings")
    if kf is not None:
        start, end = kf
        for m in _FINDING_RE.finditer(report_text, start, end):
            statement = m.group(1).strip()
            quote = report_text[m.start():m.end()]
            span = Span(file="REPORT.md", heading="Key Findings", char=(m.start(), m.end()), quote=quote)
            add_assertion(
                Assertion(
                    id=ids.assertion_id(statement=statement, project=pid),
                    kind="finding",
                    statement=statement,
                    entities=[project_node],   # links the finding to its producing project (graph connectivity)
                    evidence=Evidence(span=span),
                    tier=TIER_ASSERTED,
                )
            )

    # --- Opportunities: bullets under '## Future Directions' -----------------------
    fd = _section_body(sections, "Future Directions")
    if fd is not None:
        start, end = fd
        for m in _BULLET_RE.finditer(report_text, start, end):
            statement = m.group(1).strip()
            quote = report_text[m.start():m.end()]
            span = Span(file="REPORT.md", heading="Future Directions", char=(m.start(), m.end()), quote=quote)
            add_assertion(
                Assertion(
                    id=ids.assertion_id(statement=statement, project=pid),
                    kind="opportunity",
                    statement=statement,
                    entities=[project_node],
                    evidence=Evidence(span=span),
                    tier=TIER_ASSERTED,
                )
            )

    # --- Datasets: backticked tokens + 'BERDL collection X' under '## Data' --------
    data_sec = _section_body(sections, "Data")
    if data_sec is not None:
        start, end = data_sec
        dataset_names: list[tuple[str, int, int]] = []
        for m in _BACKTICK_RE.finditer(report_text, start, end):
            name = m.group(1).strip()
            dataset_names.append((name, m.start(1), m.end(1)))
        for m in _BERDL_RE.finditer(report_text, start, end):
            name = m.group(1).strip()
            dataset_names.append((name, m.start(1), m.end(1)))

        # Heuristic: keep dataset-like tokens (no path separators / file extensions that
        # are generated outputs are still captured as datasets — spec says backticked names).
        for name, s_off, e_off in dataset_names:
            # Skip generated-output artifacts (file paths / extensions); keep source dataset/table names.
            if _ARTIFACT_RE.search(name):
                continue
            dnode = add_entity(name, "Dataset")
            span = Span(file="REPORT.md", heading="Data", char=(s_off, e_off), quote=name)
            add_mention(name, "Dataset", span)
            add_assertion(
                Assertion(
                    id=ids.assertion_id(s=project_node, p="uses", o=dnode),
                    kind="relation",
                    s=project_node,
                    p="uses",
                    o=dnode,
                    evidence=Evidence(span=span),
                    tier=TIER_ASSERTED,
                )
            )

    # --- Publications: PMIDs under '## References' --------------------------------
    refs = _section_body(sections, "References")
    if refs is not None:
        start, end = refs
        for m in _PMID_RE.finditer(report_text, start, end):
            pmid = m.group(0)
            add_entity(pmid, "Publication")
            add_mention(pmid, "Publication", Span(file="REPORT.md", heading="References", char=(m.start(), m.end()), quote=pmid))

    # --- Organisms: dictionary-resolved only --------------------------------------
    # An Organism is admitted to the KG only if it resolves to a known taxon (dictionary).
    # An earlier unconditional binomial-regex pass produced ~140 prose false-positives
    # ("The near", "Pangenome cluster", ...). Real organism NER + grounding (Gilda/OGER) is
    # the documented future swap-in; until then we favor precision over recall.
    org_dict = _load_organism_dict()
    normalized_report = ids.normalize(report_text)
    organism_nodes: list[str] = []
    for alias, info in org_dict.items():
        if alias and alias in normalized_report:
            canonical = info.get("label", alias)
            onode = add_entity(canonical, "Organism")
            organism_nodes.append(onode)
            mloc = re.search(re.escape(alias), report_text, re.IGNORECASE)
            span = Span(file="REPORT.md")
            if mloc:
                span = Span(file="REPORT.md", char=(mloc.start(), mloc.end()), quote=mloc.group(0))
                add_mention(canonical, "Organism", span)
            # Link the project to the organism it studies -> the organism becomes the
            # cross-project hub (a single canonical node reached from every project that studies it).
            add_assertion(
                Assertion(
                    id=ids.assertion_id(s=project_node, p="studies", o=onode),
                    kind="relation",
                    s=project_node,
                    p="studies",
                    o=onode,
                    evidence=Evidence(span=span),
                    tier=TIER_ASSERTED,
                )
            )

    if organism_nodes:
        for assertion in assertions:
            if assertion.kind in {"finding", "opportunity"}:
                for onode in organism_nodes:
                    if onode not in assertion.entities:
                        assertion.entities.append(onode)

    # --- Gene / ortholog ids via regex --------------------------------------------
    for regex, type_ in ((_KO_RE, "KO"), (_COG_RE, "OrthologGroup"), (_PF_RE, "Gene")):
        for m in regex.finditer(report_text):
            label = m.group(0)
            add_entity(label, type_)
            add_mention(label, type_, Span(file="REPORT.md", char=(m.start(), m.end()), quote=label))

    return ProjectKG(
        project=meta,
        mentions=mentions,
        entities=list(entities.values()),
        assertions=assertions,
    )
