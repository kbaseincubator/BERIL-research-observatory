# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "anthropic>=0.40",
#   "jsonschema>=4.23",
#   "pyyaml>=6.0",
# ]
# ///
"""
Generate provenance.yaml for existing BERIL Research Observatory projects.

Reads each project's markdown files (REPORT.md, references.md, README.md,
RESEARCH_PLAN.md) and uses the Claude API to extract structured provenance
metadata into provenance.yaml.

Usage:
    uv run tools/generate_provenance.py                       # all projects missing provenance.yaml
    uv run tools/generate_provenance.py paperblast_explorer    # single project
    uv run tools/generate_provenance.py --force                # overwrite existing
    uv run tools/generate_provenance.py --dry-run              # show what would be generated
    uv run tools/generate_provenance.py --model claude-haiku-4-5-20251001  # use a different model

Requires ANTHROPIC_API_KEY environment variable.
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path

import anthropic
import yaml
from jsonschema import Draft202012Validator

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = REPO_ROOT / "projects"

# ---------------------------------------------------------------------------
# Known BERDL collection IDs (for the prompt context)
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

PROVENANCE_SCHEMA_PATH = REPO_ROOT / "docs" / "schemas" / "provenance.schema.json"

REFERENCE_TYPES = {
    "primary_data_source",
    "supporting",
    "contradicting",
    "methodology",
    "review",
}

DEPENDENCY_RELATIONSHIPS = {
    "data_input",
    "extends",
    "contradicts",
    "replicates",
    "synthesizes",
}

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a metadata extraction assistant for the BERIL Research Observatory.
Your job is to read a project's markdown documentation and produce a single
provenance.yaml file in the exact schema described below.

Output ONLY the YAML content — no markdown fences, no commentary, no
explanation. The output must be valid YAML that can be parsed by PyYAML.

## Schema

```yaml
schema_version: 1  # always 1

references:          # list of literature/data references cited in the project
  - id: <str>        # short key: first author surname + year, e.g. "price2018"
    type: <str>      # one of: primary_data_source | supporting | contradicting | methodology | review
    title: <str>     # full paper title
    authors: [<str>] # list of "Surname Initials" strings, e.g. ["Price MN", "Arkin AP"]
    year: <int|null>
    journal: <str|null>
    volume: <str|null>
    pages: <str|null>
    doi: <str|null>   # bare DOI without https://doi.org/ prefix
    pmid: <str|null>  # bare PubMed ID (digits only)
    url: <str|null>   # only if no DOI/PMID available

data_sources:         # BERDL collections used
  - collection: <str> # must be a known BERDL collection ID (see list below)
    tables: [<str>]   # table names within the collection
    purpose: <str|null>
    reference: <str|null>  # links to a references[].id if applicable

cross_project_deps:   # dependencies on other BERIL projects
  - project: <str>    # source project directory name (snake_case)
    relationship: <str>  # one of: data_input | extends | contradicts | replicates | synthesizes
    files: [<str>]    # specific files referenced (relative paths)
    description: <str|null>

findings:             # key findings with evidence links
  - id: <str>         # short snake_case slug derived from the finding title
    title: <str>      # the finding title (from ### heading)
    notebook: <str|null>  # notebook filename from *(Notebook: ...)* annotation
    figures: [<str>]  # figure filenames (just the filename, not full path)
    data_files: [<str>]  # data file paths relative to project dir
    references: [<str>]  # reference IDs cited in this finding
    statistics:       # key statistical results mentioned
      <key>: <str>    # e.g. test: "Mann-Whitney U", p_value: "1.6e-87"

generated_data:       # data files produced by the project
  - file: <str>       # path relative to project dir, e.g. "data/output.csv"
    rows: <int|null>
    description: <str|null>
    source_notebook: <str|null>
```

## Rules

1. **Reference IDs**: Use first author surname (lowercase) + year. If duplicates,
   append a/b/c (e.g. "price2018a", "price2018b").

2. **Reference type classification**:
   - `primary_data_source`: The paper that produced the primary dataset being analyzed
   - `supporting`: Papers whose findings agree with or support this project's conclusions
   - `contradicting`: Papers whose findings contradict this project's conclusions
   - `methodology`: Papers describing methods/tools used (e.g. clustering algorithms, statistical tests)
   - `review`: Review papers cited for background context
   - When uncertain, default to `supporting`

3. **DOI format**: Strip any "https://doi.org/" prefix. Output bare DOI like "10.1038/s41586-018-0124-0".

4. **PMID format**: Digits only, as a string. No "PMID:" prefix.

5. **Collection IDs**: Only use these known BERDL collection IDs:
   KNOWN_COLLECTION_IDS

6. **Cross-project deps**: Look for references to other project directories via
   relative paths (../../other_project/data/...), explicit "Dependencies" sections,
   or mentions of upstream project names.

7. **Findings**: Parse each `### ...` heading under `## Key Findings`. Extract:
   - Notebook from `*(Notebook: name.ipynb)*` pattern
   - Figures from `![...](figures/name.png)` pattern
   - Statistics from bold numbers and statistical test mentions
   - Reference links by matching author/year citations to reference IDs

8. **Generated data**: Parse `## Data > ### Generated Data` tables. Also check
   the data/ directory listing provided for CSV/TSV/JSON files.

9. **Omit empty sections**: If a project has no cross-project deps, output
   `cross_project_deps: []`. Same for other list fields.

10. If a section has no extractable data, use an empty list `[]`.
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def gather_project_context(project_dir: Path) -> dict[str, str]:
    """Read all relevant markdown files and directory listings for a project."""
    context = {}

    for filename in ["REPORT.md", "references.md", "README.md", "RESEARCH_PLAN.md"]:
        filepath = project_dir / filename
        if filepath.exists():
            context[filename] = filepath.read_text(encoding="utf-8")

    # Include directory listings for data/ and figures/ so the LLM knows what files exist
    for dirname in ["data", "figures", "notebooks"]:
        dirpath = project_dir / dirname
        if dirpath.exists():
            files = sorted(
                f.name for f in dirpath.iterdir()
                if f.is_file() and not f.name.startswith(".")
            )
            if files:
                context[f"{dirname}/ (directory listing)"] = "\n".join(files)

    return context


def build_user_prompt(project_id: str, context: dict[str, str]) -> str:
    """Build the user prompt from gathered project context."""
    parts = [f"Project ID: {project_id}\n"]

    for filename, content in context.items():
        parts.append(f"=== {filename} ===")
        parts.append(content)
        parts.append("")

    parts.append(
        "Generate the provenance.yaml for this project. "
        "Output ONLY valid YAML, no markdown fences or commentary."
    )
    return "\n".join(parts)


def call_claude(
    client: anthropic.Anthropic,
    system: str,
    user_prompt: str,
    model: str,
    max_retries: int = 5,
) -> str:
    """Call Claude API and return the text response. Retries on transient errors."""
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model=model,
                max_tokens=8192,
                system=system,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return message.content[0].text
        except (anthropic.APIStatusError,) as e:
            # Retry on overloaded (529), rate limit (429), or server errors (5xx)
            status = getattr(e, "status_code", 0)
            if status in (429, 529) or 500 <= status < 600:
                delay = 2 ** attempt  # 1, 2, 4, 8, 16 seconds
                print(f" [{status}, retry in {delay}s]", end="", flush=True, file=sys.stderr)
                time.sleep(delay)
                continue
            raise
    raise RuntimeError(f"API call failed after {max_retries} retries")


def _load_provenance_validator() -> Draft202012Validator:
    """Load JSON Schema validator for provenance.yaml."""
    if not PROVENANCE_SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema not found: {PROVENANCE_SCHEMA_PATH}")
    schema = yaml.safe_load(PROVENANCE_SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    value = str(doi).strip()
    value = re.sub(r"^https?://doi\.org/", "", value, flags=re.IGNORECASE)
    return value or None


def _normalize_pmid(pmid: str | int | None) -> str | None:
    if pmid is None:
        return None
    value = re.sub(r"\D+", "", str(pmid))
    return value or None


def _to_str_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if value is None:
        return []
    casted = str(value).strip()
    return [casted] if casted else []


def _to_int_or_none(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None

def _normalize_stat_value(value: object) -> str | int | float | bool | None:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _discover_generated_data_files(project_dir: Path) -> list[str]:
    data_dir = project_dir / "data"
    if not data_dir.exists():
        return []
    files = []
    for item in sorted(data_dir.iterdir()):
        if not item.is_file() or item.name.startswith("."):
            continue
        if item.suffix.lower() not in {".csv", ".tsv", ".json", ".parquet"}:
            continue
        files.append(f"data/{item.name}")
    return files


def _normalize_provenance_data(data: dict, project_dir: Path) -> dict:
    """Normalize provenance content and deterministically enrich missing artifacts."""
    normalized: dict = {
        "schema_version": 1,
        "references": [],
        "data_sources": [],
        "cross_project_deps": [],
        "findings": [],
        "generated_data": [],
    }

    # References
    seen_ref_ids: set[str] = set()
    for ref in data.get("references", []) or []:
        if not isinstance(ref, dict):
            continue
        ref_id = str(ref.get("id", "")).strip()
        if not ref_id or ref_id in seen_ref_ids:
            continue
        ref_type = str(ref.get("type", "supporting")).strip() or "supporting"
        if ref_type not in REFERENCE_TYPES:
            ref_type = "supporting"
        entry = {
            "id": ref_id,
            "type": ref_type,
            "title": str(ref.get("title", "")).strip(),
            "authors": _to_str_list(ref.get("authors", [])),
            "year": _to_int_or_none(ref.get("year")),
            "journal": ref.get("journal"),
            "volume": str(ref["volume"]) if ref.get("volume") is not None else None,
            "pages": str(ref["pages"]) if ref.get("pages") is not None else None,
            "doi": _normalize_doi(ref.get("doi")),
            "pmid": _normalize_pmid(ref.get("pmid")),
            "url": ref.get("url"),
        }
        normalized["references"].append(entry)
        seen_ref_ids.add(ref_id)
    ref_ids = {r["id"] for r in normalized["references"]}

    # Data sources
    for ds in data.get("data_sources", []) or []:
        if not isinstance(ds, dict):
            continue
        collection = str(ds.get("collection", "")).strip()
        if not collection:
            continue
        entry = {
            "collection": collection,
            "tables": _to_str_list(ds.get("tables", [])),
            "purpose": ds.get("purpose"),
            "reference": ds.get("reference") if ds.get("reference") in ref_ids else None,
        }
        normalized["data_sources"].append(entry)

    # Cross-project dependencies
    for dep in data.get("cross_project_deps", []) or []:
        if not isinstance(dep, dict):
            continue
        project = str(dep.get("project", "")).strip()
        if not project:
            continue
        relationship = str(dep.get("relationship", "data_input")).strip() or "data_input"
        if relationship not in DEPENDENCY_RELATIONSHIPS:
            relationship = "data_input"
        entry = {
            "project": project,
            "relationship": relationship,
            "files": _to_str_list(dep.get("files", [])),
            "description": dep.get("description"),
        }
        normalized["cross_project_deps"].append(entry)

    # Findings
    seen_finding_ids: set[str] = set()
    for finding in data.get("findings", []) or []:
        if not isinstance(finding, dict):
            continue
        fid = str(finding.get("id", "")).strip()
        title = str(finding.get("title", "")).strip()
        if not fid or not title or fid in seen_finding_ids:
            continue

        notebook = finding.get("notebook")
        if notebook and not (project_dir / "notebooks" / str(notebook)).exists():
            notebook = None

        figures = [f for f in _to_str_list(finding.get("figures", [])) if (project_dir / "figures" / f).exists()]
        data_files = [f for f in _to_str_list(finding.get("data_files", [])) if (project_dir / f).exists()]
        refs = [r for r in _to_str_list(finding.get("references", [])) if r in ref_ids]
        stats = finding.get("statistics", {})
        if not isinstance(stats, dict):
            stats = {}
        entry = {
            "id": fid,
            "title": title,
            "notebook": notebook,
            "figures": figures,
            "data_files": data_files,
            "references": refs,
            "statistics": {str(k): _normalize_stat_value(v) for k, v in stats.items()},
        }
        normalized["findings"].append(entry)
        seen_finding_ids.add(fid)

    # Generated data (deterministic supplementation from data/ directory)
    seen_generated_files: set[str] = set()
    for gd in data.get("generated_data", []) or []:
        if not isinstance(gd, dict):
            continue
        file = str(gd.get("file", "")).strip()
        if not file or file in seen_generated_files:
            continue
        if not (project_dir / file).exists():
            continue
        source_nb = gd.get("source_notebook")
        if source_nb and not (project_dir / "notebooks" / str(source_nb)).exists():
            source_nb = None
        entry = {
            "file": file,
            "rows": _to_int_or_none(gd.get("rows")),
            "description": gd.get("description"),
            "source_notebook": source_nb,
        }
        normalized["generated_data"].append(entry)
        seen_generated_files.add(file)

    for file in _discover_generated_data_files(project_dir):
        if file not in seen_generated_files:
            normalized["generated_data"].append(
                {
                    "file": file,
                    "rows": None,
                    "description": None,
                    "source_notebook": None,
                }
            )
            seen_generated_files.add(file)

    return normalized


def validate_provenance(
    yaml_text: str, project_dir: Path, validator: Draft202012Validator
) -> tuple[dict | None, list[str]]:
    """Parse, normalize, and strictly validate provenance YAML."""
    errors: list[str] = []
    try:
        raw = yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        return None, [f"YAML parse error: {e}"]
    if not isinstance(raw, dict):
        return None, ["Top-level YAML is not a mapping"]

    data = _normalize_provenance_data(raw, project_dir)

    for err in validator.iter_errors(data):
        path = ".".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"schema error at {path}: {err.message}")

    # Additional strict integrity checks.
    ref_ids = {r["id"] for r in data.get("references", [])}
    for ref in data.get("references", []):
        rid = ref.get("id", "<missing-id>")
        if not (ref.get("doi") or ref.get("pmid") or ref.get("url")):
            errors.append(f"references[{rid}] must include at least one of DOI, PMID, or URL")
    for i, ds in enumerate(data.get("data_sources", [])):
        coll = ds.get("collection")
        if coll not in KNOWN_COLLECTIONS:
            errors.append(f"data_sources[{i}] unknown collection '{coll}'")
        if ds.get("reference") and ds["reference"] not in ref_ids:
            errors.append(f"data_sources[{i}] unknown reference ID '{ds['reference']}'")

    for i, dep in enumerate(data.get("cross_project_deps", [])):
        dep_project = dep.get("project")
        if dep_project and not (PROJECTS_DIR / dep_project).is_dir():
            errors.append(f"cross_project_deps[{i}] unknown project '{dep_project}'")

    for i, finding in enumerate(data.get("findings", [])):
        nb = finding.get("notebook")
        if nb and not (project_dir / "notebooks" / nb).exists():
            errors.append(f"findings[{i}] notebook not found: notebooks/{nb}")
        for fig in finding.get("figures", []):
            if not (project_dir / "figures" / fig).exists():
                errors.append(f"findings[{i}] figure not found: figures/{fig}")
        for file in finding.get("data_files", []):
            if not (project_dir / file).exists():
                errors.append(f"findings[{i}] data_file not found: {file}")
        for ref in finding.get("references", []):
            if ref not in ref_ids:
                errors.append(f"findings[{i}] unknown reference ID '{ref}'")

    for i, gd in enumerate(data.get("generated_data", [])):
        file = gd.get("file")
        if file and not (project_dir / file).exists():
            errors.append(f"generated_data[{i}] file not found: {file}")
        source_nb = gd.get("source_notebook")
        if source_nb and not (project_dir / "notebooks" / source_nb).exists():
            errors.append(f"generated_data[{i}] source_notebook not found: notebooks/{source_nb}")

    return data, errors


def strip_yaml_fences(text: str) -> str:
    """Strip markdown code fences if the LLM wrapped the output."""
    text = text.strip()
    if text.startswith("```yaml"):
        text = text[len("```yaml"):]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def generate_for_project(
    client: anthropic.Anthropic,
    project_dir: Path,
    model: str,
    system_prompt: str,
    validator: Draft202012Validator,
    dry_run: bool = False,
) -> bool:
    """Generate provenance.yaml for a single project. Returns True on success."""
    project_id = project_dir.name
    context = gather_project_context(project_dir)

    if not context:
        print(f"  SKIP  {project_id}: no markdown files found", file=sys.stderr)
        return False

    # Need at least REPORT.md or README.md
    if "REPORT.md" not in context and "README.md" not in context:
        print(f"  SKIP  {project_id}: no REPORT.md or README.md", file=sys.stderr)
        return False

    user_prompt = build_user_prompt(project_id, context)

    if dry_run:
        print(f"  DRY   {project_id}: would generate ({len(context)} files, ~{len(user_prompt)} chars)", file=sys.stderr)
        return True

    # First attempt
    print(f"  GEN   {project_id}...", end="", flush=True, file=sys.stderr)
    try:
        raw_response = call_claude(client, system_prompt, user_prompt, model)
    except (RuntimeError, anthropic.APIError) as e:
        print(f" FAIL: {e}", file=sys.stderr)
        return False
    yaml_text = strip_yaml_fences(raw_response)

    data, errors = validate_provenance(yaml_text, project_dir, validator)

    # Retry once if validation failed
    if errors:
        print(" (retrying)", end="", flush=True, file=sys.stderr)
        retry_prompt = (
            user_prompt
            + "\n\nYour previous output had these validation errors:\n"
            + "\n".join(f"- {e}" for e in errors)
            + "\n\nPlease fix them and output the corrected YAML."
        )
        try:
            raw_response = call_claude(client, system_prompt, retry_prompt, model)
        except (RuntimeError, anthropic.APIError) as e:
            print(f" FAIL: {e}", file=sys.stderr)
            return False
        yaml_text = strip_yaml_fences(raw_response)
        data, errors = validate_provenance(yaml_text, project_dir, validator)

    if errors:
        print(f" FAIL: {'; '.join(errors[:3])}", file=sys.stderr)
        return False
    assert data is not None
    normalized_yaml = yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=120,
    ).strip()

    # Write the file
    output_path = project_dir / "provenance.yaml"
    output_path.write_text(normalized_yaml + "\n", encoding="utf-8")
    print(" OK", file=sys.stderr)
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Generate provenance.yaml for BERIL projects using Claude API.",
    )
    parser.add_argument(
        "project_id",
        nargs="?",
        help="Project ID to generate for. If omitted, processes all projects.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing provenance.yaml files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without making API calls.",
    )
    parser.add_argument(
        "--model",
        default="claude-haiku-4-5-20251001",
        help="Claude model to use (default: claude-haiku-4-5-20251001).",
    )
    args = parser.parse_args()

    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key and not args.dry_run:
        print(
            "Error: ANTHROPIC_API_KEY environment variable is required.\n"
            "Set it with: export ANTHROPIC_API_KEY=sk-ant-...",
            file=sys.stderr,
        )
        sys.exit(1)

    client = anthropic.Anthropic() if not args.dry_run else None
    validator = _load_provenance_validator()

    # Prepare system prompt with actual collection IDs
    system_prompt = SYSTEM_PROMPT.replace(
        "KNOWN_COLLECTION_IDS",
        ", ".join(KNOWN_COLLECTIONS),
    )

    # Determine which projects to process
    if args.project_id:
        project_dir = PROJECTS_DIR / args.project_id
        if not project_dir.is_dir():
            print(f"Error: Project '{args.project_id}' not found at {project_dir}", file=sys.stderr)
            sys.exit(1)
        project_dirs = [project_dir]
    else:
        project_dirs = sorted(
            d for d in PROJECTS_DIR.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )

    # Filter out projects that already have provenance.yaml (unless --force)
    if not args.force:
        before = len(project_dirs)
        project_dirs = [d for d in project_dirs if not (d / "provenance.yaml").exists()]
        skipped = before - len(project_dirs)
        if skipped:
            print(f"Skipping {skipped} project(s) with existing provenance.yaml (use --force to overwrite)", file=sys.stderr)

    if not project_dirs:
        print("No projects to process.", file=sys.stderr)
        sys.exit(0)

    print(f"Processing {len(project_dirs)} project(s)...\n", file=sys.stderr)

    success = 0
    failed = 0
    for i, project_dir in enumerate(project_dirs):
        ok = generate_for_project(
            client, project_dir, args.model, system_prompt, validator, args.dry_run
        )
        if ok:
            success += 1
        else:
            failed += 1

        # Rate limit between API calls
        if not args.dry_run and i < len(project_dirs) - 1:
            time.sleep(1)

    print(f"\nDone: {success} succeeded, {failed} failed.", file=sys.stderr)
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
