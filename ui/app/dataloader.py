"""Repository parser - reads markdown files and extracts structured data."""

import gzip
import pickle
import re
from datetime import datetime
from pathlib import Path

import yaml

import httpx

from .config import settings
from .models import (
    Collection,
    CollectionCategory,
    CollectionTable,
    Column,
    Contributor,
    DataFile,
    Discovery,
    IdeaStatus,
    Notebook,
    PerformanceTip,
    Pitfall,
    Priority,
    Project,
    ProjectStatus,
    RepositoryData,
    ResearchIdea,
    Review,
    SampleQuery,
    Table,
    Visualization,
)

REPOSITORY_DATA_FILE = "data.pkl.gz"
TIMESTAMP_FILE = "timestamp.json"


def load_repository_data(source_path: Path | str | None = None) -> RepositoryData:
    """
    Load repository data from a file path, URL, or local parsing.

    Args:
        source_path: Optional file path or URL to load data from.
                    If Path: loads from local pickle file
                    If str (URL): loads from HTTP
                    If None: parses from local repository files

    Returns:
        RepositoryData object with all parsed repository information.
    """
    if source_path:
        try:
            if isinstance(source_path, Path):
                # Load from local file
                return load_local_pickle(source_path)
            else:
                # Load from URL
                return load_external_data(source_path)
        except Exception as e:
            # Fall through to local parsing
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to load from {source_path}: {e}")
            logger.warning("Falling back to local file parsing")

    # Parse from local files
    parser = get_parser()
    return parser.parse_all()


def load_local_pickle(file_path: Path) -> RepositoryData:
    """
    Load repository data from a local gzipped pickle file.

    Args:
        file_path: Path to the .pkl.gz file

    Returns:
        RepositoryData object

    Raises:
        FileNotFoundError: If file doesn't exist
        pickle.UnpicklingError: If file is not a valid pickle
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Loading data from local file: {file_path}")

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    with gzip.open(file_path, "rb") as f:
        repository_data = pickle.load(f)

    # Validate that we got a RepositoryData object
    if not isinstance(repository_data, RepositoryData):
        raise ValueError(f"Expected RepositoryData object, got {type(repository_data)}")

    logger.info(f"Loaded data with last_updated: {repository_data.last_updated}")
    return repository_data


def check_for_updates(data_source_url: str, current_last_updated: datetime) -> bool:
    """
    Check if remote data has been updated since the current data.

    Args:
        data_source_url: Base URL where timestamp.json is located
        current_last_updated: The last_updated timestamp of currently loaded data

    Returns:
        True if remote data is newer, False otherwise
    """
    import json

    # Ensure URL ends with a slash
    if not data_source_url.endswith("/"):
        data_source_url = data_source_url + "/"

    # Construct URL to timestamp file
    timestamp_url = data_source_url + TIMESTAMP_FILE

    try:
        # Fetch timestamp metadata
        response = httpx.get(timestamp_url, follow_redirects=True, timeout=5.0)
        response.raise_for_status()

        timestamp_data = response.json()
        remote_timestamp_str = timestamp_data.get("timestamp")

        if not remote_timestamp_str:
            return False

        # Parse the remote timestamp
        from datetime import datetime as dt
        remote_timestamp = dt.fromisoformat(remote_timestamp_str)

        # Compare timestamps
        return remote_timestamp > current_last_updated

    except Exception:
        # If we can't check for updates, assume no update needed
        return False


def load_external_data(url: str) -> RepositoryData:
    """
    This loads an external pickle file from url/REPOSITORY_DATA_FILE.
    This gets returned as RepositoryData.
    Possible failures:
    HTTPError - if the url doesn't exist, or is inaccessible
    ValueError - if the url is invalid
    UnpicklingError - if the file is not a pickle file
    """
    # Ensure URL ends with a slash
    if not url.endswith("/"):
        url = url + "/"

    # Construct full URL to the data file
    full_url = url + REPOSITORY_DATA_FILE

    # Fetch the file from the URL
    response = httpx.get(full_url, follow_redirects=True)
    response.raise_for_status()  # Raises HTTPError for bad status codes

    # Decompress the gzipped content
    decompressed_data = gzip.decompress(response.content)

    # Unpickle the data
    repository_data = pickle.loads(decompressed_data)

    # Validate that we got a RepositoryData object
    if not isinstance(repository_data, RepositoryData):
        raise ValueError(f"Expected RepositoryData object, got {type(repository_data)}")

    return repository_data


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text


class RepositoryParser:
    """Parse git repository file system into structured data."""

    # Collection IDs to scan for in README text
    _COLLECTION_IDS = [
        "kbase_ke_pangenome",
        "kescience_fitnessbrowser",
        "kbase_msd_biochemistry",
        "kbase_genomes",
        "enigma_coral",
        "kbase_phenotype",
        "nmdc_arkin",
        "phagefoundry",
        "planetmicrobe",
        "protect_genomedepot",
        "kbase_uniprot",
        "kbase_uniref",
    ]

    def __init__(self, repo_path: Path | None = None):
        """Initialize parser with repository path."""
        self.repo_path = repo_path or settings.repo_dir

    def parse_all(self) -> RepositoryData:
        """Parse entire repository into structured data."""
        projects = self.parse_projects()
        discoveries = self.parse_discoveries()
        tables = self.parse_schema()
        pitfalls = self.parse_pitfalls()
        performance_tips = self.parse_performance()
        research_ideas = self.parse_research_ideas()
        collections = self.parse_collections()

        # Aggregate unique contributors across all projects
        contributors = self._aggregate_contributors(projects)

        # Compute stats
        total_notebooks = sum(len(p.notebooks) for p in projects)
        total_visualizations = sum(len(p.visualizations) for p in projects)
        total_data_files = sum(len(p.data_files) for p in projects)

        return RepositoryData(
            projects=projects,
            discoveries=discoveries,
            tables=tables,
            pitfalls=pitfalls,
            performance_tips=performance_tips,
            research_ideas=research_ideas,
            collections=collections,
            contributors=contributors,
            total_notebooks=total_notebooks,
            total_visualizations=total_visualizations,
            total_data_files=total_data_files,
            last_updated=datetime.now(),
        )

    def _aggregate_contributors(self, projects: list[Project]) -> list[Contributor]:
        """Merge contributors across projects by lowercased name."""
        merged: dict[str, Contributor] = {}

        for project in projects:
            for contrib in project.contributors:
                key = contrib.name.lower()
                if key in merged:
                    existing = merged[key]
                    # Union project_ids
                    for pid in contrib.project_ids:
                        if pid not in existing.project_ids:
                            existing.project_ids.append(pid)
                    # Union roles
                    for role in contrib.roles:
                        if role not in existing.roles:
                            existing.roles.append(role)
                    # Take first non-null affiliation/orcid
                    if not existing.affiliation and contrib.affiliation:
                        existing.affiliation = contrib.affiliation
                    if not existing.orcid and contrib.orcid:
                        existing.orcid = contrib.orcid
                else:
                    merged[key] = Contributor(
                        name=contrib.name,
                        affiliation=contrib.affiliation,
                        orcid=contrib.orcid,
                        roles=list(contrib.roles),
                        project_ids=list(contrib.project_ids),
                    )

        return sorted(merged.values(), key=lambda c: c.name.lower())

    def parse_projects(self) -> list[Project]:
        """Parse all projects from projects/ directory."""
        projects = []
        projects_dir = self.repo_path / "projects"

        if not projects_dir.exists():
            return projects

        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir() or project_dir.name.startswith("."):
                continue

            project = self._parse_project_dir(project_dir)
            if project:
                projects.append(project)

        return sorted(
            projects, key=lambda p: p.updated_date or datetime.min, reverse=True
        )

    def _parse_project_dir(self, project_dir: Path) -> Project | None:
        """Parse single project directory.

        Supports the three-file structure:
        - README.md: project overview (title, research question, status, authors)
        - RESEARCH_PLAN.md: hypothesis, approach, data sources, revision history
        - REPORT.md: key findings, results, interpretation, future directions

        Falls back to extracting all sections from README.md for legacy projects.
        """
        readme_path = project_dir / "README.md"
        if not readme_path.exists():
            return None

        readme_content = readme_path.read_text()

        # Extract title from first H1
        title_match = re.search(r"^#\s+(.+)$", readme_content, re.MULTILINE)
        title = title_match.group(1) if title_match else project_dir.name

        # Always extract research question and overview from README
        research_question = self._extract_section(readme_content, "Research Question")
        overview = self._extract_section(readme_content, "Overview")

        # Read RESEARCH_PLAN.md if it exists (preferred source for hypothesis/approach)
        plan_path = project_dir / "RESEARCH_PLAN.md"
        has_research_plan = plan_path.exists()
        research_plan_raw = None
        revision_history = None

        if has_research_plan:
            research_plan_raw = plan_path.read_text()
            hypothesis = self._extract_section(research_plan_raw, "Hypothesis")
            approach = self._extract_section(research_plan_raw, "Approach")
            revision_history = self._extract_section(research_plan_raw, "Revision History")
        else:
            # Fallback: extract from README (legacy projects)
            hypothesis = self._extract_section(readme_content, "Hypothesis")
            approach = self._extract_section(readme_content, "Approach")

        # Read REPORT.md if it exists (preferred source for findings)
        report_path = project_dir / "REPORT.md"
        has_report = report_path.exists()
        report_raw = None
        results = None
        interpretation = None
        limitations = None
        future_directions = None

        if has_report:
            report_raw = report_path.read_text()
            findings = self._extract_section(report_raw, "Key Findings")
            results = self._extract_section(report_raw, "Results")
            interpretation = self._extract_section(report_raw, "Interpretation")
            limitations = self._extract_section(report_raw, "Limitations")
            future_directions = self._extract_section(report_raw, "Future Directions")
        else:
            # Fallback: extract from README (legacy projects)
            findings = self._extract_section(readme_content, "Key Findings")

        # Determine status
        if findings and "to be filled" not in findings.lower() and "tbd" not in findings.lower():
            status = ProjectStatus.COMPLETED
        elif has_research_plan:
            status = ProjectStatus.IN_PROGRESS
        else:
            # Check if README has substantial content beyond a skeleton
            if research_question and approach:
                status = ProjectStatus.IN_PROGRESS
            else:
                status = ProjectStatus.PROPOSED

        # Parse notebooks
        notebooks = self._parse_notebooks(project_dir)

        # Parse visualizations and data files
        visualizations, data_files = self._parse_data_dir(project_dir)

        # Parse contributors
        contributors = self._parse_contributors(readme_content, project_dir.name)

        # Get file modification times as proxy for dates
        created_date = datetime.fromtimestamp(readme_path.stat().st_ctime)
        # Use latest mtime across all project docs
        mtimes = [readme_path.stat().st_mtime]
        if has_research_plan:
            mtimes.append(plan_path.stat().st_mtime)
        if has_report:
            mtimes.append(report_path.stat().st_mtime)
        updated_date = datetime.fromtimestamp(max(mtimes))

        # Parse review
        review = self._parse_review(project_dir)

        # Extract collection references from all available text
        all_text = readme_content
        if research_plan_raw:
            all_text += "\n" + research_plan_raw
        if report_raw:
            all_text += "\n" + report_raw
        related_collections = self._extract_collection_refs(all_text)

        return Project(
            id=project_dir.name,
            title=title,
            research_question=research_question or "",
            status=status,
            hypothesis=hypothesis,
            approach=approach,
            findings=findings,
            notebooks=notebooks,
            visualizations=visualizations,
            data_files=data_files,
            created_date=created_date,
            updated_date=updated_date,
            contributors=contributors,
            related_collections=related_collections,
            raw_readme=readme_content,
            review=review,
            has_research_plan=has_research_plan,
            has_report=has_report,
            research_plan_raw=research_plan_raw,
            report_raw=report_raw,
            overview=overview,
            results=results,
            interpretation=interpretation,
            limitations=limitations,
            future_directions=future_directions,
            revision_history=revision_history,
        )

    def _extract_collection_refs(self, readme_content: str) -> list[str]:
        """Extract BERDL collection IDs mentioned in README text."""
        return [cid for cid in self._COLLECTION_IDS if cid in readme_content]

    def _parse_contributors(
        self, readme_content: str, project_id: str
    ) -> list[Contributor]:
        """Parse contributors from ## Authors or ## Contributors section."""
        section = self._extract_section(readme_content, "Authors")
        if section is None:
            section = self._extract_section(readme_content, "Contributors")
        if not section:
            return []

        contributors = []
        for line in section.split("\n"):
            line = line.strip()
            # Match lines like: - **Name** (Affiliation) | ORCID: 0000-... | role text
            match = re.match(r"^-\s+\*\*(.+?)\*\*(?:\s*\(([^)]+)\))?(.*)", line)
            if not match:
                continue

            name = match.group(1).strip()
            affiliation = match.group(2).strip() if match.group(2) else None
            rest = match.group(3).strip()

            orcid = None
            roles = []

            if rest:
                # Split by pipe and parse segments
                segments = [s.strip() for s in rest.split("|") if s.strip()]
                for segment in segments:
                    orcid_match = re.match(r"ORCID:\s*([\d-]+)", segment)
                    if orcid_match:
                        orcid = orcid_match.group(1)
                    else:
                        roles.append(segment)

            contributors.append(
                Contributor(
                    name=name,
                    affiliation=affiliation,
                    orcid=orcid,
                    roles=roles,
                    project_ids=[project_id],
                )
            )

        return contributors

    def _parse_review(self, project_dir: Path) -> Review | None:
        """Parse REVIEW.md from a project directory."""
        review_path = project_dir / "REVIEW.md"
        if not review_path.exists():
            return None

        raw_content = review_path.read_text()

        # Parse YAML frontmatter
        reviewer = "BERIL Automated Review"
        date = None
        project_id = project_dir.name

        frontmatter_match = re.match(
            r"^---\s*\n(.*?)\n---\s*\n", raw_content, re.DOTALL
        )
        body = raw_content
        if frontmatter_match:
            frontmatter_text = frontmatter_match.group(1)
            body = raw_content[frontmatter_match.end() :]

            try:
                frontmatter = yaml.safe_load(frontmatter_text)
                if isinstance(frontmatter, dict):
                    reviewer = frontmatter.get("reviewer", reviewer)
                    project_id = frontmatter.get("project", project_id)
                    date_val = frontmatter.get("date")
                    if isinstance(date_val, datetime):
                        date = date_val
                    elif date_val:
                        try:
                            date = datetime.strptime(str(date_val), "%Y-%m-%d")
                        except ValueError:
                            pass
            except yaml.YAMLError:
                pass

        # Fall back to file mtime if no date in frontmatter
        if date is None:
            date = datetime.fromtimestamp(review_path.stat().st_mtime)

        # Extract sections from body
        summary = self._extract_section(body, "Summary")
        methodology = self._extract_section(body, "Methodology")
        code_quality = self._extract_section(body, "Code Quality")
        findings_assessment = self._extract_section(body, "Findings Assessment")
        suggestions = self._extract_section(body, "Suggestions")

        return Review(
            reviewer=reviewer,
            date=date,
            project_id=project_id,
            summary=summary,
            methodology=methodology,
            code_quality=code_quality,
            findings_assessment=findings_assessment,
            suggestions=suggestions,
            raw_content=raw_content,
        )

    def _extract_section(self, content: str, section_name: str) -> str | None:
        """Extract content between a section header and the next header."""
        # Match ## Section Name or ### Section Name
        pattern = rf"^##?\s*{re.escape(section_name)}\s*$\n(.*?)(?=^##|\Z)"
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def _parse_notebooks(self, project_dir: Path) -> list[Notebook]:
        """Parse notebooks from project/notebooks/ directory."""
        notebooks = []
        notebooks_dir = project_dir / "notebooks"

        if not notebooks_dir.exists():
            return notebooks

        for notebook_path in notebooks_dir.glob("*.ipynb"):
            notebooks.append(
                Notebook(
                    filename=notebook_path.name,
                    path=str(notebook_path.relative_to(self.repo_path)),
                    title=notebook_path.stem.replace("_", " ").title(),
                )
            )

        return sorted(notebooks, key=lambda n: n.filename)

    def _parse_data_dir(
        self, project_dir: Path
    ) -> tuple[list[Visualization], list[DataFile]]:
        """Parse visualizations and data files from project data/ and figures/ directories."""
        visualizations = []
        data_files = []

        # Scan both data/ and figures/ directories
        dirs_to_scan = [project_dir / "data", project_dir / "figures"]

        for scan_dir in dirs_to_scan:
            if not scan_dir.exists():
                continue

            for file_path in scan_dir.iterdir():
                if file_path.name.startswith("."):
                    continue

                size_bytes = file_path.stat().st_size

                if file_path.suffix.lower() in (
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".svg",
                    ".gif",
                ):
                    visualizations.append(
                        Visualization(
                            filename=file_path.name,
                            path=str(file_path.relative_to(self.repo_path)),
                            title=file_path.stem.replace("_", " ").title(),
                            size_bytes=size_bytes,
                        )
                    )
                elif file_path.suffix.lower() in (".csv", ".tsv", ".json", ".parquet"):
                    data_files.append(
                        DataFile(
                            filename=file_path.name,
                            path=str(file_path.relative_to(self.repo_path)),
                            size_bytes=size_bytes,
                        )
                    )

        return (
            sorted(visualizations, key=lambda v: v.filename),
            sorted(data_files, key=lambda d: d.filename),
        )

    def parse_discoveries(self) -> list[Discovery]:
        """Parse discoveries from docs/discoveries.md."""
        discoveries = []
        discoveries_path = self.repo_path / "docs" / "discoveries.md"

        if not discoveries_path.exists():
            return discoveries

        content = discoveries_path.read_text()

        # Split by ### headers (discovery entries)
        sections = re.split(r"\n###\s+", content)

        current_date = None

        for section in sections[1:]:  # Skip intro
            if not section.strip():
                continue

            # Check if this is a date header (## 2026-01)
            date_match = re.match(r"^##\s+(\d{4}-\d{2})", section)
            if date_match:
                current_date = datetime.strptime(date_match.group(1), "%Y-%m")
                continue

            lines = section.split("\n")
            title_line = lines[0].strip()

            # Parse [project_tag] from title
            match = re.match(r"\[(\w+)\]\s+(.+)", title_line)
            if match:
                project_tag = match.group(1)
                title = match.group(2)
                content_text = "\n".join(lines[1:]).strip()

                # Skip template section
                if (
                    "Brief title" in title
                    or "Description of what was discovered" in content_text
                ):
                    continue

                discovery = Discovery(
                    id=slugify(title),
                    title=title,
                    project_tag=project_tag,
                    content=content_text,
                    date=current_date,
                    related_projects=[project_tag],
                )
                discoveries.append(discovery)

        return discoveries

    def parse_schema(self) -> dict[str, list[Table]]:
        """Parse tables from all docs/schemas/*.md files.

        Returns a dict keyed by database/collection ID mapping to parsed tables.
        Each schema doc is keyed by its database ID (from the **Database** line)
        and also by the filename stem. Multi-database docs store under each
        listed database ID plus the filename stem.
        """
        all_tables: dict[str, list[Table]] = {}
        schemas_dir = self.repo_path / "docs" / "schemas"

        if not schemas_dir.exists():
            return all_tables

        for schema_file in sorted(schemas_dir.glob("*.md")):
            content = schema_file.read_text()
            filename_key = schema_file.stem

            # Extract database ID(s)
            db_ids: list[str] = []
            singular = re.search(r"\*\*Database\*\*:\s*`([^`]+)`", content)
            if singular:
                db_ids = [singular.group(1)]
            else:
                # Multi-database: extract all backtick IDs from the Databases section
                plural_match = re.search(
                    r"\*\*Databases?\*\*:?\s*(.*?)(?:\n\*\*|\n---)",
                    content,
                    re.DOTALL,
                )
                if plural_match:
                    db_ids = re.findall(r"`([^`]+)`", plural_match.group(1))

            # Parse row counts from Table Summary
            row_counts = self._parse_row_counts(content)

            # Parse individual table schemas
            tables = self._parse_table_sections(content, row_counts)

            if not tables:
                continue

            # Store under filename stem (always)
            all_tables[filename_key] = tables

            # Also store under each extracted database ID
            for db_id in db_ids:
                if db_id != filename_key:
                    all_tables[db_id] = tables

        return all_tables

    def _parse_row_counts(self, content: str) -> dict[str, int]:
        """Extract row counts from the Table Summary section."""
        row_counts: dict[str, int] = {}
        summary_match = re.search(
            r"## Table Summary\s*\n(.*?)(?:\n---|\n## )",
            content,
            re.DOTALL,
        )
        if not summary_match:
            return row_counts

        for line in summary_match.group(1).split("\n"):
            if not line.strip() or not line.startswith("|"):
                continue
            # Skip header and separator rows
            if "Table" in line and ("Row Count" in line or "Description" in line):
                continue
            if re.match(r"^\|[-\s|]+\|$", line):
                continue
            cols = [c.strip() for c in line.split("|") if c.strip()]
            if len(cols) >= 2:
                table_name = cols[0].strip("`")
                try:
                    row_count = int(cols[1].replace(",", ""))
                    row_counts[table_name] = row_count
                except ValueError:
                    pass

        return row_counts

    def _parse_table_sections(
        self, content: str, row_counts: dict[str, int]
    ) -> list[Table]:
        """Parse individual table schemas from ### headings."""
        tables: list[Table] = []

        # Match both numbered (### 1. `genome`) and unnumbered (### `organism`)
        table_sections = re.split(r"\n###\s+(?:\d+\.\s+)?", content)

        for section in table_sections[1:]:  # Skip intro
            lines = section.split("\n")
            if not lines:
                continue

            # First line contains table name in backticks
            name_match = re.match(r"`(\w+)`", lines[0])
            if not name_match:
                continue

            table_name = name_match.group(1)

            # Get description (first paragraph after name)
            description = ""
            for line in lines[1:]:
                if (
                    line.strip()
                    and not line.startswith("|")
                    and not line.startswith("-")
                ):
                    description = line.strip()
                    break

            # Parse columns from markdown table
            columns = []
            in_table = False
            for line in lines:
                if line.startswith("| Column"):
                    in_table = True
                    continue
                if in_table and line.startswith("|"):
                    if line.startswith("|--") or line.startswith("| --"):
                        continue
                    cols = [c.strip() for c in line.split("|") if c.strip()]
                    if len(cols) >= 3:
                        col_name = cols[0].strip("`")
                        col_type = cols[1]
                        col_desc = cols[2] if len(cols) > 2 else ""

                        is_pk = "Primary Key" in col_desc
                        is_fk = "FK" in col_desc or "→" in col_desc

                        columns.append(
                            Column(
                                name=col_name,
                                data_type=col_type,
                                description=col_desc,
                                is_primary_key=is_pk,
                                is_foreign_key=is_fk,
                            )
                        )
                elif in_table and not line.startswith("|"):
                    in_table = False

            tables.append(
                Table(
                    name=table_name,
                    description=description,
                    row_count=row_counts.get(table_name, 0),
                    columns=columns,
                )
            )

        return tables

    def parse_pitfalls(self) -> list[Pitfall]:
        """Parse pitfalls from docs/pitfalls.md."""
        pitfalls = []
        pitfalls_path = self.repo_path / "docs" / "pitfalls.md"

        if not pitfalls_path.exists():
            return pitfalls

        content = pitfalls_path.read_text()

        # Split by ## headers (categories)
        category_sections = re.split(r"\n##\s+", content)

        for cat_section in category_sections[1:]:  # Skip intro
            lines = cat_section.split("\n")
            category = lines[0].strip()

            # Skip non-category sections
            if category.lower() in ("overview", "purpose"):
                continue

            # Split by ### headers (individual pitfalls)
            pitfall_sections = re.split(r"\n###\s+", cat_section)

            for pitfall_section in pitfall_sections[1:]:
                pitfall_lines = pitfall_section.split("\n")
                title = pitfall_lines[0].strip()

                # Get content as problem description
                problem = "\n".join(pitfall_lines[1:]).strip()

                # Try to extract code example
                code_match = re.search(r"```sql\n(.*?)```", problem, re.DOTALL)
                code_example = code_match.group(1).strip() if code_match else None

                pitfalls.append(
                    Pitfall(
                        id=slugify(title),
                        title=title,
                        category=category,
                        problem=problem,
                        solution="",  # Could parse if there's a structured format
                        code_example=code_example,
                    )
                )

        return pitfalls

    def parse_performance(self) -> list[PerformanceTip]:
        """Parse performance tips from docs/performance.md."""
        tips = []
        perf_path = self.repo_path / "docs" / "performance.md"

        if not perf_path.exists():
            return tips

        content = perf_path.read_text()

        # Split by ### headers
        sections = re.split(r"\n###\s+", content)

        for section in sections[1:]:
            lines = section.split("\n")
            if not lines:
                continue

            title = lines[0].strip()
            description = "\n".join(lines[1:]).strip()

            # Try to extract code example
            code_match = re.search(
                r"```(?:sql|python)\n(.*?)```", description, re.DOTALL
            )
            code_example = code_match.group(1).strip() if code_match else None

            tips.append(
                PerformanceTip(
                    id=slugify(title),
                    title=title,
                    description=description,
                    code_example=code_example,
                )
            )

        return tips

    def parse_research_ideas(self) -> list[ResearchIdea]:
        """Parse research ideas from docs/research_ideas.md."""
        ideas = []
        ideas_path = self.repo_path / "docs" / "research_ideas.md"

        if not ideas_path.exists():
            return ideas

        content = ideas_path.read_text()

        # Determine priority from section headers
        current_priority = Priority.MEDIUM

        # Split by ### headers (individual ideas)
        sections = re.split(r"\n###\s+", content)

        for section in sections[1:]:
            # Check if this looks like a priority section header (## High Priority Ideas)
            if section.startswith("## "):
                if "High Priority" in section:
                    current_priority = Priority.HIGH
                elif "Medium Priority" in section:
                    current_priority = Priority.MEDIUM
                elif "Low Priority" in section:
                    current_priority = Priority.LOW
                continue

            lines = section.split("\n")
            if not lines:
                continue

            title_line = lines[0].strip()

            # Parse [source_tag] Title
            match = re.match(r"\[([^\]]+)\]\s+(.+)", title_line)
            if not match:
                continue

            source_tag = match.group(1)
            title = match.group(2)
            section_content = "\n".join(lines[1:])

            # Extract structured fields
            status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", section_content)
            priority_match = re.search(r"\*\*Priority\*\*:\s*(\w+)", section_content)
            effort_match = re.search(
                r"\*\*Effort\*\*:\s*(.+?)(?:\n|$)", section_content
            )
            research_q_match = re.search(
                r"\*\*Research Question\*\*:\s*(.+?)(?=\n\n|\*\*|\Z)",
                section_content,
                re.DOTALL,
            )
            hypothesis_match = re.search(
                r"\*\*Hypothesis\*\*:\s*(.+?)(?=\n\n|\*\*|\Z)",
                section_content,
                re.DOTALL,
            )
            approach_match = re.search(
                r"\*\*Approach\*\*:\s*(.+?)(?=\n\n|\*\*|\Z)",
                section_content,
                re.DOTALL,
            )
            impact_match = re.search(
                r"\*\*Impact\*\*:\s*(.+?)(?:\n|$)", section_content
            )

            # Parse status
            status = IdeaStatus.PROPOSED
            if status_match:
                status_str = status_match.group(1).upper()
                if status_str == "IN_PROGRESS":
                    status = IdeaStatus.IN_PROGRESS
                elif status_str == "COMPLETED":
                    status = IdeaStatus.COMPLETED

            # Parse priority
            priority = current_priority
            if priority_match:
                priority_str = priority_match.group(1).upper()
                if priority_str == "HIGH":
                    priority = Priority.HIGH
                elif priority_str == "MEDIUM":
                    priority = Priority.MEDIUM
                elif priority_str == "LOW":
                    priority = Priority.LOW

            ideas.append(
                ResearchIdea(
                    id=slugify(title),
                    title=title,
                    research_question=research_q_match.group(1).strip()
                    if research_q_match
                    else "",
                    status=status,
                    priority=priority,
                    hypothesis=hypothesis_match.group(1).strip()
                    if hypothesis_match
                    else None,
                    approach=approach_match.group(1).strip()
                    if approach_match
                    else None,
                    effort=effort_match.group(1).strip() if effort_match else None,
                    impact=impact_match.group(1).strip() if impact_match else None,
                    cross_project_tags=[source_tag],
                )
            )

        return ideas

    def parse_collections(self) -> list[Collection]:
        """Parse collections from config/collections.yaml."""
        collections = []
        config_path = settings.ui_dir / "config" / "collections.yaml"

        if not config_path.exists():
            return collections

        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        if not data or "collections" not in data:
            return collections

        for coll_data in data["collections"]:
            # Parse category
            category_str = coll_data.get("category", "primary")
            try:
                category = CollectionCategory(category_str)
            except ValueError:
                category = CollectionCategory.PRIMARY

            # Parse key tables
            key_tables = []
            for table_data in coll_data.get("key_tables", []):
                key_tables.append(
                    CollectionTable(
                        name=table_data.get("name", ""),
                        description=table_data.get("description", ""),
                        row_count=table_data.get("row_count"),
                    )
                )

            # Parse sample queries
            sample_queries = []
            for query_data in coll_data.get("sample_queries", []):
                sample_queries.append(
                    SampleQuery(
                        title=query_data.get("title", ""),
                        query=query_data.get("query", ""),
                    )
                )

            collection = Collection(
                id=coll_data.get("id", ""),
                name=coll_data.get("name", ""),
                category=category,
                icon=coll_data.get("icon", "&#128194;"),
                description=coll_data.get("description", "").strip(),
                philosophy=coll_data.get("philosophy", "").strip(),
                data_sources=coll_data.get("data_sources", []),
                scale_stats=coll_data.get("scale_stats", {}),
                key_tables=key_tables,
                sample_queries=sample_queries,
                related_collections=coll_data.get("related_collections", []),
                sub_collections=coll_data.get("sub_collections", []),
            )
            collections.append(collection)

        return collections


# Singleton instance
_parser: RepositoryParser | None = None


def get_parser() -> RepositoryParser:
    """Get or create parser singleton."""
    global _parser
    if _parser is None:
        _parser = RepositoryParser()
    return _parser
