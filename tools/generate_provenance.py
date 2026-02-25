# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "anthropic>=0.40",
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
import sys
import time
from pathlib import Path

import anthropic
import yaml

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


def validate_provenance(yaml_text: str) -> tuple[dict | None, list[str]]:
    """Parse YAML and validate required fields. Returns (data, errors)."""
    errors = []

    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        return None, [f"YAML parse error: {e}"]

    if not isinstance(data, dict):
        return None, ["Top-level YAML is not a mapping"]

    if "schema_version" not in data:
        errors.append("Missing schema_version")

    # Validate references
    for i, ref in enumerate(data.get("references", [])):
        if not isinstance(ref, dict):
            errors.append(f"references[{i}]: not a mapping")
            continue
        for field in ("id", "type", "title"):
            if not ref.get(field):
                errors.append(f"references[{i}]: missing required field '{field}'")

    # Validate data_sources
    for i, ds in enumerate(data.get("data_sources", [])):
        if not isinstance(ds, dict):
            errors.append(f"data_sources[{i}]: not a mapping")
            continue
        if not ds.get("collection"):
            errors.append(f"data_sources[{i}]: missing 'collection'")

    # Validate findings
    for i, f in enumerate(data.get("findings", [])):
        if not isinstance(f, dict):
            errors.append(f"findings[{i}]: not a mapping")
            continue
        for field in ("id", "title"):
            if not f.get(field):
                errors.append(f"findings[{i}]: missing required field '{field}'")

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

    data, errors = validate_provenance(yaml_text)

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
        data, errors = validate_provenance(yaml_text)

    if errors:
        print(f" FAIL: {'; '.join(errors[:3])}", file=sys.stderr)
        return False

    # Write the file
    output_path = project_dir / "provenance.yaml"
    output_path.write_text(yaml_text + "\n", encoding="utf-8")
    print(f" OK", file=sys.stderr)
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
            client, project_dir, args.model, system_prompt, args.dry_run
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
