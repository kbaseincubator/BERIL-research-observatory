"""Parsing functions for project metadata extraction.

Extracted from scripts/build_registry.py for use by ingest/manifest.py
and other observatory_context consumers.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Paths (for parse_readme_deps project validation)
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = REPO_ROOT / "projects"

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

# ---------------------------------------------------------------------------
# Figure parsing
# ---------------------------------------------------------------------------

FIGURE_MD_RE = re.compile(r"!\[([^\]]*)\]\((?:[^)]*?/)?figures/([^)]+)\)")
NOTEBOOK_RE = re.compile(r"\*\(Notebook:\s*([^)]+\.ipynb)\)\*")

# ---------------------------------------------------------------------------
# Cross-project dependency detection
# ---------------------------------------------------------------------------

NOTEBOOK_DEP_PATTERNS = [
    re.compile(r"\.\./\.\./([a-z0-9_]+)/(?:data|user_data)(?:/([^\s'\"\\,)]+))?"),
    re.compile(
        r"\.parent\s*/\s*['\"]([a-z0-9_]+)['\"]\s*/\s*['\"](?:data|user_data)['\"]"
        r"(?:\s*/\s*['\"]([^'\"]+)['\"])?"
    ),
    re.compile(r"projects/([a-z0-9_]+)/(?:data|user_data)(?:/([^\s'\"\\,)]+))?"),
]

# ---------------------------------------------------------------------------
# Organism extraction
# ---------------------------------------------------------------------------

ORGANISM_PATTERNS = [
    re.compile(r"(\d+)\s+(?:Fitness Browser\s+)?(?:bacteria|organisms?)", re.IGNORECASE),
    re.compile(r"(\d+[\s,]*\d*)\s+(?:pangenome\s+)?species", re.IGNORECASE),
    re.compile(r"(\d+)\s+genomes?", re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


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

    if provenance:
        for ds in provenance.get("data_sources", []):
            if isinstance(ds, dict) and ds.get("collection"):
                found.add(ds["collection"])

    for coll_id in KNOWN_COLLECTIONS:
        if coll_id in text:
            found.add(coll_id)

    return sorted(found)


def extract_title(readme_content: str) -> str:
    """Extract project title from the first # heading."""
    for line in readme_content.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return "Untitled"


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


def detect_date_completed(
    project_dir: Path, status: str, report_content: str | None
) -> str | None:
    """Detect completion date from git history (fallback to file mtime)."""
    if status != "complete":
        return None

    report_path = project_dir / "REPORT.md"
    if report_path.exists():
        try:
            result = subprocess.run(
                [
                    "git",
                    "--no-pager",
                    "log",
                    "-1",
                    "--format=%aI",
                    "--",
                    str(report_path),
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                check=False,
            )
            iso = result.stdout.strip()
            if iso:
                dt = datetime.fromisoformat(iso)
                return dt.strftime("%Y-%m")
        except Exception:
            pass

        mtime = report_path.stat().st_mtime
        dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
        return dt.strftime("%Y-%m")

    return None


def extract_organisms(text: str) -> list[str]:
    """Extract organism descriptions from text."""
    organisms = []
    for pat in ORGANISM_PATTERNS:
        for m in pat.finditer(text):
            organisms.append(m.group(0).strip())
    return organisms[:5]


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
                    title = re.sub(r"^\d+[.)]\s*", "", title)
                    findings.append(title)
        if findings:
            return findings[:8]

    if status_text and any(
        status_text.lower().startswith(prefix)
        for prefix in ("complete", "completed")
    ):
        if "—" in status_text or "--" in status_text:
            sep = "—" if "—" in status_text else "--"
            after = status_text.split(sep, 1)[1].strip()
            if after:
                parts = re.split(r";", after)
                return [p.strip().rstrip(".") for p in parts if p.strip()][:5]

    return []


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
            for m in re.finditer(r"`([a-z0-9_]+)`", line):
                candidate = m.group(1)
                if (PROJECTS_DIR / candidate).is_dir():
                    dep_ids.append(candidate)
            for m in re.finditer(r"\.\./([a-z0-9_]+)", line):
                candidate = m.group(1)
                if (PROJECTS_DIR / candidate).is_dir():
                    dep_ids.append(candidate)
    return sorted(set(dep_ids))


def parse_data_artifacts(
    project_dir: Path, provenance: dict | None = None
) -> list[dict]:
    """Extract reusable data artifacts."""
    artifacts = []
    seen = set()

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


def parse_figures_from_report(
    project_id: str,
    report_content: str | None,
    figures_dir: Path,
    provenance: dict | None = None,
) -> list[dict]:
    """Parse figures from REPORT.md references and figures/ directory."""
    figures = []
    seen_files = set()

    if report_content:
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


def parse_project(project_dir: Path) -> dict | None:
    """Parse a project directory into a registry entry.

    Two-tier strategy:
    1. Primary: read provenance.yaml for structured data
    2. Fallback: parse README.md + REPORT.md with regex
    """
    project_id = project_dir.name

    readme_path = project_dir / "README.md"
    report_path = project_dir / "REPORT.md"
    provenance_path = project_dir / "provenance.yaml"

    if not readme_path.exists():
        return None

    readme_content = readme_path.read_text(encoding="utf-8")
    report_content = (
        report_path.read_text(encoding="utf-8") if report_path.exists() else None
    )

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

    combined_text = readme_content
    if report_content:
        combined_text += "\n" + report_content

    title = extract_title(readme_content)
    status_text = extract_status_text(readme_content)
    status = detect_status(status_text)
    research_question = extract_research_question(readme_content)

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

    key_findings = extract_key_findings_summary(report_content, provenance, status_text)
    tags = detect_tags(combined_text)
    databases_used = detect_databases(combined_text, provenance)
    organisms = extract_organisms(combined_text)

    depends_on = []
    if provenance:
        for dep in provenance.get("cross_project_deps", []):
            if isinstance(dep, dict) and dep.get("project"):
                depends_on.append(dep["project"])
    if not depends_on:
        nb_deps = scan_notebook_deps(project_dir)
        depends_on = [d["project"] for d in nb_deps]
        readme_deps = parse_readme_deps(readme_content)
        depends_on = sorted(set(depends_on + readme_deps))

    data_artifacts = parse_data_artifacts(project_dir, provenance)
    references = parse_references(provenance)
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
        "enables": [],
        "has_provenance": provenance is not None,
        "date_completed": date_completed,
    }

    return entry
