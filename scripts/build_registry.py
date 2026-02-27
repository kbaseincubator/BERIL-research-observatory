#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///
"""
Build the BERIL Research Observatory knowledge registry.

Reads all project directories and generates three searchable index files:
  - docs/project_registry.yaml  — aggregated index of all projects
  - docs/figure_catalog.yaml    — searchable catalog of all figures
  - docs/findings_digest.md     — concise summary of key findings with links

Two-tier data strategy:
  1. Primary: reads provenance.yaml (from PR #123) for structured metadata
  2. Fallback: parses README.md / REPORT.md with regex when provenance.yaml absent

Usage:
    python scripts/build_registry.py                  # full rebuild
    python scripts/build_registry.py --project cog_analysis  # single project update
    python scripts/build_registry.py --dry-run         # preview without writing
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = REPO_ROOT / "projects"
DOCS_DIR = REPO_ROOT / "docs"

OUTPUT_REGISTRY = DOCS_DIR / "project_registry.yaml"
OUTPUT_FIGURES = DOCS_DIR / "figure_catalog.yaml"
OUTPUT_FINDINGS = DOCS_DIR / "findings_digest.md"

# Directories to skip
SKIP_PROJECTS = {"hackathon_demo"}

# ---------------------------------------------------------------------------
# Known BERDL collection IDs (for auto-detection)
# ---------------------------------------------------------------------------

KNOWN_COLLECTIONS = [
    "kbase_ke_pangenome",
    "kescience_fitnessbrowser",
    "kbase_genomes",
    "kbase_msd_biochemistry",
    "kbase_phenotype",
    "phagefoundry",
    "enigma_coral",
    "nmdc_arkin",
    "nmdc_ncbi_biosamples",
    "planetmicrobe",
    "protect_genomedepot",
    "kbase_uniref",
    "kbase_uniprot",
    "kbase_ontology_source",
    "kescience_paperblast",
    "kescience_webofmicrobes",
    "kescience_bacdive",
]

# ---------------------------------------------------------------------------
# Tag vocabulary
# ---------------------------------------------------------------------------

# Biological tags — keyword patterns mapped to tag names
BIO_TAG_PATTERNS: dict[str, list[str]] = {
    "pangenome": ["pangenome", "pan-genome", "gene_cluster", "core.*accessory"],
    "fitness": ["fitness", "RB-TnSeq", "TnSeq", "fitnessbrowser", "mutant phenotype"],
    "conservation": ["conservation", "conserved", "core.*fraction", "purifying selection"],
    "dark-genes": ["dark gene", "unknown function", "hypothetical protein", "functionally dark"],
    "essential-genes": ["essential", "essentiality", "minimal genome"],
    "defense": ["defense", "defence", "CRISPR", "restriction-modification", "COG.*V"],
    "mobile-elements": ["mobile element", "transpos", "phage", "IS element", "COG.*L", "HGT"],
    "metabolism": ["metabol", "biosynthesis", "pathway", "enzyme", "cofactor"],
    "cofitness": ["co-fitness", "cofitness", "cofit"],
    "modules": ["module", "ICA", "iModulon"],
    "ecotype": ["ecotype", "ecology", "environmental", "habitat", "niche"],
    "biogeography": ["biogeograph", "geographic", "spatial distribution"],
    "metal-stress": ["metal", "zinc", "copper", "nickel", "cobalt", "arsenic", "uranium"],
    "gene-annotation": ["COG", "eggNOG", "annotation", "functional category"],
    "HGT": ["horizontal.*transfer", "HGT", "lateral.*transfer"],
    "enrichment": ["enrichment", "overrepresent", "enriched"],
    "correlation": ["correlation", "correlat", "regression"],
    "pathway-analysis": ["pathway", "GapMind", "KEGG", "metabolic capability"],
    "co-occurrence": ["co-occur", "cooccur", "presence.*absence", "phi coefficient"],
}

# ---------------------------------------------------------------------------
# Status detection
# ---------------------------------------------------------------------------

STATUS_PATTERNS = [
    (re.compile(r"^Completed?\s*[—–-]", re.IGNORECASE), "complete"),
    (re.compile(r"^In\s+Progress\s*[—–-]", re.IGNORECASE), "in-progress"),
    (re.compile(r"^Proposed\s*[—–-]", re.IGNORECASE), "proposed"),
]


def detect_status(text: str) -> str:
    """Detect project status from the line after '## Status'."""
    text = text.strip()
    for pattern, status in STATUS_PATTERNS:
        if pattern.match(text):
            return status
    if text.lower().startswith("complete"):
        return "complete"
    if text.lower().startswith("in progress"):
        return "in-progress"
    if text.lower().startswith("proposed"):
        return "proposed"
    return "unknown"


# ---------------------------------------------------------------------------
# Cross-project dependency detection (from dataloader.py patterns)
# ---------------------------------------------------------------------------

NOTEBOOK_DEP_PATTERNS = [
    # ../../project/data/file or ../../project/data (dir-only)
    re.compile(r"\.\./\.\./([a-z_]+)/(?:data|user_data)(?:/([^\s'\"\\,)]+))?"),
    # .parent / 'project' / 'data' / 'file' (Path objects)
    re.compile(
        r"\.parent\s*/\s*['\"]([a-z_]+)['\"]\s*/\s*['\"](?:data|user_data)['\"]"
        r"(?:\s*/\s*['\"]([^'\"]+)['\"])?"
    ),
    # projects/project/data/file (absolute-ish paths)
    re.compile(r"projects/([a-z_]+)/(?:data|user_data)(?:/([^\s'\"\\,)]+))?"),
]


def scan_notebook_deps(project_dir: Path) -> list[dict]:
    """Scan notebook code cells for cross-project data references."""
    notebooks_dir = project_dir / "notebooks"
    if not notebooks_dir.exists():
        return []

    project_id = project_dir.name
    deps: dict[str, set[str]] = {}

    for nb_path in notebooks_dir.glob("*.ipynb"):
        try:
            nb_data = json.loads(nb_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        for cell in nb_data.get("cells", []):
            if cell.get("cell_type") != "code":
                continue
            source = "".join(cell.get("source", []))
            for pattern in NOTEBOOK_DEP_PATTERNS:
                for match in pattern.finditer(source):
                    src_project = match.group(1)
                    if src_project == project_id:
                        continue
                    filename = (
                        match.group(2) if match.lastindex >= 2 and match.group(2) else None
                    )
                    deps.setdefault(src_project, set())
                    if filename:
                        deps[src_project].add(filename)

    return [
        {"project": sp, "files": sorted(files)}
        for sp, files in sorted(deps.items())
    ]


# ---------------------------------------------------------------------------
# Markdown dependency detection (README ## Dependencies section)
# ---------------------------------------------------------------------------


def parse_readme_deps(readme_content: str) -> list[str]:
    """Parse ## Dependencies section from README for project references."""
    dep_ids = []
    in_deps = False
    for line in readme_content.split("\n"):
        if re.match(r"^##\s+Dependencies", line, re.IGNORECASE):
            in_deps = True
            continue
        if in_deps and line.startswith("## "):
            break
        if in_deps:
            # Look for project directory references like `project_name`
            for m in re.finditer(r"`([a-z_]+)`", line):
                candidate = m.group(1)
                if (PROJECTS_DIR / candidate).is_dir():
                    dep_ids.append(candidate)
            # Also look for links like [name](../project_name/)
            for m in re.finditer(r"\.\./([a-z_]+)", line):
                candidate = m.group(1)
                if (PROJECTS_DIR / candidate).is_dir():
                    dep_ids.append(candidate)
    return sorted(set(dep_ids))


# ---------------------------------------------------------------------------
# Tag detection
# ---------------------------------------------------------------------------


def detect_tags(text: str) -> list[str]:
    """Detect tags from combined project text using keyword patterns."""
    tags = []
    for tag, patterns in BIO_TAG_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                tags.append(tag)
                break
    return sorted(tags)


def detect_databases(text: str, provenance: dict | None = None) -> list[str]:
    """Detect BERDL collection IDs from text or provenance data."""
    found = set()

    # From provenance.yaml data_sources
    if provenance:
        for ds in provenance.get("data_sources", []):
            if isinstance(ds, dict) and ds.get("collection"):
                found.add(ds["collection"])

    # From text content (collection IDs are distinctive enough)
    for coll_id in KNOWN_COLLECTIONS:
        if coll_id in text:
            found.add(coll_id)

    return sorted(found)


# ---------------------------------------------------------------------------
# Figure parsing
# ---------------------------------------------------------------------------

# Match ![caption](figures/filename) or ![caption](path/to/figures/filename)
FIGURE_MD_RE = re.compile(r"!\[([^\]]*)\]\((?:[^)]*?/)?figures/([^)]+)\)")

# Match *(Notebook: name.ipynb)* anywhere in text
NOTEBOOK_RE = re.compile(r"\*\(Notebook:\s*([^)]+\.ipynb)\)\*")


def parse_figures_from_report(
    project_id: str,
    report_content: str | None,
    figures_dir: Path,
    provenance: dict | None = None,
) -> list[dict]:
    """Parse figures from REPORT.md references and figures/ directory."""
    figures = []
    seen_files = set()

    # Figures referenced in REPORT.md with captions
    if report_content:
        # Track the most recent notebook annotation for context
        current_notebook = None
        for line in report_content.split("\n"):
            nb_match = NOTEBOOK_RE.search(line)
            if nb_match:
                current_notebook = nb_match.group(1).strip()

            for match in FIGURE_MD_RE.finditer(line):
                caption = match.group(1).strip()
                filename = match.group(2).strip()
                if filename not in seen_files:
                    seen_files.add(filename)
                    figures.append({
                        "project": project_id,
                        "file": filename,
                        "path": f"projects/{project_id}/figures/{filename}",
                        "caption": caption or None,
                        "notebook": current_notebook,
                        "tags": detect_tags(caption) if caption else [],
                    })

    # Also include figures from provenance findings
    if provenance:
        for finding in provenance.get("findings", []):
            if not isinstance(finding, dict):
                continue
            for fig_file in finding.get("figures", []):
                if fig_file not in seen_files:
                    seen_files.add(fig_file)
                    figures.append({
                        "project": project_id,
                        "file": fig_file,
                        "path": f"projects/{project_id}/figures/{fig_file}",
                        "caption": finding.get("title"),
                        "notebook": finding.get("notebook"),
                        "tags": [],
                    })

    # Include unreferenced figures from directory
    if figures_dir.exists():
        for f in sorted(figures_dir.iterdir()):
            if f.is_file() and not f.name.startswith(".") and f.name not in seen_files:
                seen_files.add(f.name)
                figures.append({
                    "project": project_id,
                    "file": f.name,
                    "path": f"projects/{project_id}/figures/{f.name}",
                    "caption": None,
                    "notebook": None,
                    "tags": [],
                })

    return figures


# ---------------------------------------------------------------------------
# Findings parsing
# ---------------------------------------------------------------------------


def parse_findings_from_provenance(project_id: str, provenance: dict) -> list[dict]:
    """Extract findings from provenance.yaml."""
    findings = []
    for f in provenance.get("findings", []):
        if not isinstance(f, dict):
            continue
        findings.append({
            "project": project_id,
            "id": f.get("id", ""),
            "title": f.get("title", ""),
            "notebook": f.get("notebook"),
            "figures": f.get("figures", []),
            "references": f.get("references", []),
            "statistics": f.get("statistics", {}),
        })
    return findings


def parse_findings_from_report(project_id: str, report_content: str) -> list[dict]:
    """Extract findings from REPORT.md '## Key Findings' section."""
    findings = []
    in_findings = False
    current_finding: dict | None = None
    current_notebook: str | None = None

    for line in report_content.split("\n"):
        # Enter Key Findings section
        if re.match(r"^##\s+Key\s+Findings", line, re.IGNORECASE):
            in_findings = True
            continue

        # Exit on next ## section
        if in_findings and re.match(r"^##\s+[^#]", line):
            if current_finding:
                findings.append(current_finding)
            break

        if not in_findings:
            continue

        # New finding (### heading)
        heading_match = re.match(r"^###\s+(.+)", line)
        if heading_match:
            if current_finding:
                findings.append(current_finding)

            title = heading_match.group(1).strip()
            # Strip leading numbers like "1. " or "1) "
            title = re.sub(r"^\d+[.)]\s*", "", title)
            finding_id = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:60]
            current_finding = {
                "project": project_id,
                "id": finding_id,
                "title": title,
                "notebook": None,
                "figures": [],
                "references": [],
                "statistics": {},
            }
            current_notebook = None
            continue

        if current_finding is None:
            # Findings text before any ### heading — create a single finding
            stripped = line.strip()
            if stripped and not stripped.startswith("*"):
                # Grab first substantial line as a finding
                finding_id = re.sub(r"[^a-z0-9]+", "_", stripped[:60].lower()).strip("_")
                current_finding = {
                    "project": project_id,
                    "id": finding_id,
                    "title": stripped.rstrip("."),
                    "notebook": None,
                    "figures": [],
                    "references": [],
                    "statistics": {},
                }

        # Track notebook annotations
        nb_match = NOTEBOOK_RE.search(line)
        if nb_match:
            current_notebook = nb_match.group(1).strip()
            if current_finding and current_finding["notebook"] is None:
                current_finding["notebook"] = current_notebook

        # Track figure references within findings
        if current_finding:
            for fig_match in FIGURE_MD_RE.finditer(line):
                fig_file = fig_match.group(2).strip()
                if fig_file not in current_finding["figures"]:
                    current_finding["figures"].append(fig_file)

    # Flush last finding
    if current_finding and current_finding not in findings:
        findings.append(current_finding)

    return findings


# ---------------------------------------------------------------------------
# Key data artifacts (from provenance generated_data or data/ directory)
# ---------------------------------------------------------------------------


def parse_data_artifacts(
    project_dir: Path, provenance: dict | None = None
) -> list[dict]:
    """Extract reusable data artifacts."""
    artifacts = []
    seen = set()

    # From provenance.yaml generated_data
    if provenance:
        for gd in provenance.get("generated_data", []):
            if not isinstance(gd, dict):
                continue
            filepath = gd.get("file", "")
            if filepath and filepath not in seen:
                seen.add(filepath)
                artifacts.append({
                    "file": filepath,
                    "description": gd.get("description"),
                    "reusable": True,
                })

    # Supplement from data/ directory (only TSV/CSV files, skip very small)
    data_dir = project_dir / "data"
    if data_dir.exists():
        for f in sorted(data_dir.iterdir()):
            if not f.is_file():
                continue
            if f.suffix.lower() not in (".csv", ".tsv", ".json", ".parquet"):
                continue
            if f.name.startswith("."):
                continue
            rel_path = f"data/{f.name}"
            if rel_path not in seen:
                seen.add(rel_path)
                artifacts.append({
                    "file": rel_path,
                    "description": None,
                    "reusable": True,
                })

    return artifacts


# ---------------------------------------------------------------------------
# References from provenance
# ---------------------------------------------------------------------------


def parse_references(provenance: dict | None) -> list[dict]:
    """Extract references from provenance.yaml."""
    if not provenance:
        return []
    refs = []
    for r in provenance.get("references", []):
        if not isinstance(r, dict):
            continue
        refs.append({
            "id": r.get("id", ""),
            "title": r.get("title", ""),
            "doi": r.get("doi"),
            "pmid": str(r["pmid"]) if r.get("pmid") else None,
            "type": r.get("type", "supporting"),
        })
    return refs


# ---------------------------------------------------------------------------
# Research question extraction
# ---------------------------------------------------------------------------


def extract_research_question(readme_content: str) -> str | None:
    """Extract research question from README.md."""
    in_rq = False
    lines = []
    for line in readme_content.split("\n"):
        if re.match(r"^##\s+Research\s+Question", line, re.IGNORECASE):
            in_rq = True
            continue
        if in_rq and line.startswith("## "):
            break
        if in_rq:
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
    return " ".join(lines) if lines else None


# ---------------------------------------------------------------------------
# Title extraction
# ---------------------------------------------------------------------------


def extract_title(readme_content: str) -> str:
    """Extract project title from the first # heading."""
    for line in readme_content.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return "Untitled"


# ---------------------------------------------------------------------------
# Status text extraction
# ---------------------------------------------------------------------------


def extract_status_text(readme_content: str) -> str:
    """Extract the raw status text line."""
    in_status = False
    for line in readme_content.split("\n"):
        if re.match(r"^##\s+Status", line, re.IGNORECASE):
            in_status = True
            continue
        if in_status:
            stripped = line.strip()
            if stripped:
                return stripped
    return ""


# ---------------------------------------------------------------------------
# Date detection
# ---------------------------------------------------------------------------


def detect_date_completed(
    project_dir: Path, status: str, report_content: str | None
) -> str | None:
    """Try to detect completion date from git or file modification time."""
    if status != "complete":
        return None

    # Use REPORT.md modification time as a rough proxy
    report_path = project_dir / "REPORT.md"
    if report_path.exists():
        mtime = report_path.stat().st_mtime
        dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
        return dt.strftime("%Y-%m")

    return None


# ---------------------------------------------------------------------------
# Organism extraction
# ---------------------------------------------------------------------------

ORGANISM_PATTERNS = [
    re.compile(r"(\d+)\s+(?:Fitness Browser\s+)?(?:bacteria|organisms?)", re.IGNORECASE),
    re.compile(r"(\d+[\s,]*\d*)\s+(?:pangenome\s+)?species", re.IGNORECASE),
    re.compile(r"(\d+)\s+genomes?", re.IGNORECASE),
]


def extract_organisms(text: str) -> list[str]:
    """Extract organism descriptions from text."""
    organisms = []
    for pat in ORGANISM_PATTERNS:
        for m in pat.finditer(text):
            organisms.append(m.group(0).strip())
    return organisms[:5]  # Cap at 5


# ---------------------------------------------------------------------------
# Key findings extraction (concise, for registry summary)
# ---------------------------------------------------------------------------


def extract_key_findings_summary(
    report_content: str | None, provenance: dict | None, status_text: str
) -> list[str]:
    """Extract concise key findings (just titles/summaries)."""
    findings = []

    if provenance:
        for f in provenance.get("findings", []):
            if isinstance(f, dict) and f.get("title"):
                findings.append(f["title"])
        if findings:
            return findings[:8]

    if report_content:
        # Extract ### headings under ## Key Findings
        in_findings = False
        for line in report_content.split("\n"):
            if re.match(r"^##\s+Key\s+Findings", line, re.IGNORECASE):
                in_findings = True
                continue
            if in_findings and re.match(r"^##\s+[^#]", line):
                break
            if in_findings:
                heading = re.match(r"^###\s+(.+)", line)
                if heading:
                    title = heading.group(1).strip()
                    # Strip leading numbers like "1. " or "1) "
                    title = re.sub(r"^\d+[.)]\s*", "", title)
                    findings.append(title)
        if findings:
            return findings[:8]

    # Fall back to status text if it contains a summary (only for complete projects)
    if status_text and any(
        status_text.lower().startswith(prefix)
        for prefix in ("complete", "completed")
    ):
        if "—" in status_text or "--" in status_text:
            sep = "—" if "—" in status_text else "--"
            after = status_text.split(sep, 1)[1].strip()
            if after:
                # Split on semicolons for multiple findings
                parts = re.split(r";", after)
                return [p.strip().rstrip(".") for p in parts if p.strip()][:5]

    return []


# ---------------------------------------------------------------------------
# Main project parser
# ---------------------------------------------------------------------------


def parse_project(project_dir: Path) -> dict | None:
    """Parse a project directory into a registry entry.

    Two-tier strategy:
    1. Primary: read provenance.yaml for structured data
    2. Fallback: parse README.md + REPORT.md with regex
    """
    project_id = project_dir.name

    # Read markdown files
    readme_path = project_dir / "README.md"
    report_path = project_dir / "REPORT.md"
    provenance_path = project_dir / "provenance.yaml"

    if not readme_path.exists():
        return None

    readme_content = readme_path.read_text(encoding="utf-8")
    report_content = (
        report_path.read_text(encoding="utf-8") if report_path.exists() else None
    )

    # Try provenance.yaml
    provenance: dict | None = None
    if provenance_path.exists():
        try:
            provenance = yaml.safe_load(
                provenance_path.read_text(encoding="utf-8")
            )
            if not isinstance(provenance, dict):
                provenance = None
        except (yaml.YAMLError, OSError):
            provenance = None

    # Combined text for tag/database detection
    combined_text = readme_content
    if report_content:
        combined_text += "\n" + report_content

    # Extract fields
    title = extract_title(readme_content)
    status_text = extract_status_text(readme_content)
    status = detect_status(status_text)
    research_question = extract_research_question(readme_content)

    # Count resources
    notebooks_dir = project_dir / "notebooks"
    figures_dir = project_dir / "figures"
    notebook_count = (
        len(list(notebooks_dir.glob("*.ipynb"))) if notebooks_dir.exists() else 0
    )
    figure_count = (
        len([f for f in figures_dir.iterdir() if f.is_file() and not f.name.startswith(".")])
        if figures_dir.exists()
        else 0
    )

    # Key findings
    key_findings = extract_key_findings_summary(report_content, provenance, status_text)

    # Tags
    tags = detect_tags(combined_text)

    # Databases
    databases_used = detect_databases(combined_text, provenance)

    # Organisms
    organisms = extract_organisms(combined_text)

    # Dependencies
    depends_on = []
    if provenance:
        for dep in provenance.get("cross_project_deps", []):
            if isinstance(dep, dict) and dep.get("project"):
                depends_on.append(dep["project"])
    if not depends_on:
        # Fallback: notebook scanning + README parsing
        nb_deps = scan_notebook_deps(project_dir)
        depends_on = [d["project"] for d in nb_deps]
        readme_deps = parse_readme_deps(readme_content)
        depends_on = sorted(set(depends_on + readme_deps))

    # Data artifacts
    data_artifacts = parse_data_artifacts(project_dir, provenance)

    # References
    references = parse_references(provenance)

    # Date completed
    date_completed = detect_date_completed(project_dir, status, report_content)

    entry = {
        "id": project_id,
        "title": title,
        "status": status,
        "research_question": research_question,
        "key_findings": key_findings,
        "tags": tags,
        "organisms": organisms,
        "databases_used": databases_used,
        "notebook_count": notebook_count,
        "figure_count": figure_count,
        "key_data_artifacts": data_artifacts if data_artifacts else [],
        "references": references if references else [],
        "depends_on": depends_on,
        "enables": [],  # Populated in post-processing
        "has_provenance": provenance is not None,
        "date_completed": date_completed,
    }

    return entry


# ---------------------------------------------------------------------------
# Post-processing: compute enables (reverse of depends_on)
# ---------------------------------------------------------------------------


def compute_enables(projects: list[dict]) -> None:
    """Populate 'enables' field as the reverse of 'depends_on'."""
    id_to_idx = {p["id"]: i for i, p in enumerate(projects)}
    for p in projects:
        for dep_id in p["depends_on"]:
            if dep_id in id_to_idx:
                dep_project = projects[id_to_idx[dep_id]]
                if p["id"] not in dep_project["enables"]:
                    dep_project["enables"].append(p["id"])
    # Sort enables lists
    for p in projects:
        p["enables"] = sorted(p["enables"])


# ---------------------------------------------------------------------------
# Output generators
# ---------------------------------------------------------------------------


def generate_registry(projects: list[dict]) -> dict:
    """Generate the project_registry.yaml content."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return {
        "version": 1,
        "generated_at": now,
        "project_count": len(projects),
        "projects": projects,
    }


def generate_figure_catalog(
    project_dirs: list[Path],
    provenance_cache: dict[str, dict | None],
    report_cache: dict[str, str | None],
) -> dict:
    """Generate the figure_catalog.yaml content."""
    all_figures = []
    for project_dir in project_dirs:
        pid = project_dir.name
        figures = parse_figures_from_report(
            pid,
            report_cache.get(pid),
            project_dir / "figures",
            provenance_cache.get(pid),
        )
        all_figures.extend(figures)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return {
        "version": 1,
        "generated_at": now,
        "figure_count": len(all_figures),
        "figures": all_figures,
    }


def generate_findings_digest(
    project_dirs: list[Path],
    projects: list[dict],
    provenance_cache: dict[str, dict | None],
    report_cache: dict[str, str | None],
) -> str:
    """Generate the findings_digest.md content."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Collect all findings
    all_findings: dict[str, list[dict]] = {}
    for project_dir in project_dirs:
        pid = project_dir.name
        prov = provenance_cache.get(pid)
        report = report_cache.get(pid)
        if prov:
            findings = parse_findings_from_provenance(pid, prov)
        elif report:
            findings = parse_findings_from_report(pid, report)
        else:
            findings = []
        if findings:
            all_findings[pid] = findings

    total_findings = sum(len(v) for v in all_findings.values())
    project_count = len(projects)

    lines = [
        "# Findings Digest",
        f"**Last updated**: {now} | **Projects**: {project_count} | **Findings**: ~{total_findings}",
        "",
    ]

    # Build lookup for project metadata
    proj_map = {p["id"]: p for p in projects}

    for pid in sorted(all_findings.keys()):
        proj = proj_map.get(pid, {})
        status = proj.get("status", "unknown")
        date = proj.get("date_completed", "")
        date_str = f"{date}, " if date else ""
        rq = proj.get("research_question", "")

        lines.append(f"## {pid} ({date_str}{status})")
        if rq:
            lines.append(f"**Q**: {rq}")
        for i, finding in enumerate(all_findings[pid], 1):
            title = finding.get("title", "Untitled")
            lines.append(
                f"{i}. **{title}** — "
                f"[REPORT](../projects/{pid}/REPORT.md)"
            )
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# YAML output helper
# ---------------------------------------------------------------------------


def yaml_dump(data: dict) -> str:
    """Dump YAML with readable formatting."""
    return yaml.dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Build the BERIL Research Observatory knowledge registry.",
    )
    parser.add_argument(
        "--project",
        help="Single project ID for incremental update.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without writing files.",
    )
    args = parser.parse_args()

    # Discover project directories
    if args.project:
        project_dir = PROJECTS_DIR / args.project
        if not project_dir.is_dir():
            print(f"Error: Project '{args.project}' not found at {project_dir}", file=sys.stderr)
            sys.exit(1)

        # For incremental update, load existing registry and update one entry
        if OUTPUT_REGISTRY.exists() and not args.dry_run:
            existing = yaml.safe_load(OUTPUT_REGISTRY.read_text(encoding="utf-8"))
            existing_projects = existing.get("projects", [])
        else:
            existing = None
            existing_projects = []

        entry = parse_project(project_dir)
        if entry is None:
            print(f"Warning: Could not parse project '{args.project}'", file=sys.stderr)
            sys.exit(1)

        # Replace or append
        replaced = False
        for i, p in enumerate(existing_projects):
            if p["id"] == args.project:
                existing_projects[i] = entry
                replaced = True
                break
        if not replaced:
            existing_projects.append(entry)

        compute_enables(existing_projects)
        all_projects = existing_projects

        # For figures and findings, we need all project dirs
        all_project_dirs = sorted(
            d for d in PROJECTS_DIR.iterdir()
            if d.is_dir() and d.name not in SKIP_PROJECTS and (d / "README.md").exists()
        )
    else:
        all_project_dirs = sorted(
            d for d in PROJECTS_DIR.iterdir()
            if d.is_dir() and d.name not in SKIP_PROJECTS and (d / "README.md").exists()
        )

        print(f"Scanning {len(all_project_dirs)} projects...", file=sys.stderr)

        all_projects = []
        for project_dir in all_project_dirs:
            entry = parse_project(project_dir)
            if entry:
                all_projects.append(entry)
            else:
                print(f"  SKIP  {project_dir.name}: no README.md", file=sys.stderr)

        compute_enables(all_projects)

    # Build caches for figure catalog and findings digest
    provenance_cache: dict[str, dict | None] = {}
    report_cache: dict[str, str | None] = {}
    for project_dir in all_project_dirs:
        pid = project_dir.name
        prov_path = project_dir / "provenance.yaml"
        report_path = project_dir / "REPORT.md"
        try:
            provenance_cache[pid] = (
                yaml.safe_load(prov_path.read_text(encoding="utf-8"))
                if prov_path.exists()
                else None
            )
        except (yaml.YAMLError, OSError):
            provenance_cache[pid] = None
        report_cache[pid] = (
            report_path.read_text(encoding="utf-8") if report_path.exists() else None
        )

    # Generate outputs
    registry = generate_registry(all_projects)
    figure_catalog = generate_figure_catalog(all_project_dirs, provenance_cache, report_cache)
    findings_digest = generate_findings_digest(
        all_project_dirs, all_projects, provenance_cache, report_cache
    )

    # Summary
    status_counts: dict[str, int] = {}
    for p in all_projects:
        status_counts[p["status"]] = status_counts.get(p["status"], 0) + 1
    prov_count = sum(1 for p in all_projects if p["has_provenance"])

    print(f"\nRegistry summary:", file=sys.stderr)
    print(f"  Projects: {len(all_projects)}", file=sys.stderr)
    for st, count in sorted(status_counts.items()):
        print(f"    {st}: {count}", file=sys.stderr)
    print(f"  With provenance.yaml: {prov_count}", file=sys.stderr)
    print(f"  Figures: {figure_catalog['figure_count']}", file=sys.stderr)
    total_findings = sum(
        len(all_findings)
        for all_findings in [
            parse_findings_from_provenance(pid, provenance_cache[pid])
            if provenance_cache.get(pid)
            else parse_findings_from_report(pid, report_cache[pid])
            if report_cache.get(pid)
            else []
            for pid in [d.name for d in all_project_dirs]
        ]
        if all_findings
    )
    print(f"  Findings: ~{total_findings}", file=sys.stderr)

    if args.dry_run:
        print("\n[DRY RUN] Would write:", file=sys.stderr)
        print(f"  {OUTPUT_REGISTRY}", file=sys.stderr)
        print(f"  {OUTPUT_FIGURES}", file=sys.stderr)
        print(f"  {OUTPUT_FINDINGS}", file=sys.stderr)
        return

    # Write outputs
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    OUTPUT_REGISTRY.write_text(yaml_dump(registry), encoding="utf-8")
    print(f"  Wrote {OUTPUT_REGISTRY}", file=sys.stderr)

    OUTPUT_FIGURES.write_text(yaml_dump(figure_catalog), encoding="utf-8")
    print(f"  Wrote {OUTPUT_FIGURES}", file=sys.stderr)

    OUTPUT_FINDINGS.write_text(findings_digest, encoding="utf-8")
    print(f"  Wrote {OUTPUT_FINDINGS}", file=sys.stderr)


if __name__ == "__main__":
    main()
