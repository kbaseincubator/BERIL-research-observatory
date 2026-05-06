"""Repository parser - reads markdown files and extracts structured data."""

import gzip
import json
import pickle
import posixpath
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

import httpx

from .config import get_settings
from .models import (
    Collection,
    CollectionCategory,
    CollectionEdge,
    CollectionTable,
    Column,
    Contributor,
    DataFile,
    DerivedDataRef,
    Discovery,
    IdeaStatus,
    Notebook,
    PerformanceTip,
    Pitfall,
    Priority,
    Project,
    ProjectStatus,
    RepositoryData,
    ResearchArea,
    ResearchIdea,
    Review,
    SampleQuery,
    Skill,
    Table,
    Visualization,
    AtlasIndex,
    AtlasLink,
    AtlasHeading,
    AtlasPage,
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

    REQUIRED_ATLAS_FIELDS = {
        "id",
        "title",
        "type",
        "status",
        "summary",
        "source_projects",
        "source_docs",
        "related_collections",
        "confidence",
        "generated_by",
        "last_reviewed",
    }

    ATLAS_PAGE_TYPES = {
        "atlas",
        "topic",
        "data_tenant",
        "data_collection",
        "data_type",
        "derived_product",
        "join_recipe",
        "data_gap",
        "conflict",
        "opportunity",
        "claim",
        "direction",
        "hypothesis",
        "person",
        "method",
        "meta",
    }

    # Collection IDs to scan for in README text
    _COLLECTION_IDS = [
        "kbase_ke_pangenome",
        "kbase_genomes",
        "kbase_msd_biochemistry",
        "kbase_phenotype",
        "kbase_uniprot",
        "kbase_uniref50",
        "kbase_uniref90",
        "kbase_uniref100",
        "kbase_refseq_taxon_api",
        "kbase_ontology_source",
        "kescience_alphafold",
        "kescience_pdb",
        "kescience_structural_biology",
        "kescience_fitnessbrowser",
        "kescience_webofmicrobes",
        "kescience_bacdive",
        "kescience_paperblast",
        "enigma_coral",
        "nmdc_arkin",
        "nmdc_ncbi_biosamples",
        "phagefoundry_acinetobacter_genome_browser",
        "phagefoundry_klebsiella_genome_browser_genomedepot",
        "phagefoundry_paeruginosa_genome_browser",
        "phagefoundry_pviridiflava_genome_browser",
        "phagefoundry_strain_modelling",
        "planetmicrobe_planetmicrobe",
        "planetmicrobe_planetmicrobe_raw",
        "protect_genomedepot",
        "globalusers_demo_shared",
        "globalusers_demo_test",
        "globalusers_demo_test_1",
        "globalusers_demo_test_2",
        "globalusers_gapmind_pathways",
        "globalusers_kepangenome_parquet_1",
        "globalusers_nmdc_core_test",
        "globalusers_nmdc_core_test2",
        "globalusers_nmdc_core_test3",
        "globalusers_phenotype_ontology_1",
        "globalusers_phenotype_parquet_1",
    ]

    def __init__(self, repo_path: Path | None = None):
        """Initialize parser with repository path."""
        self.repo_path = repo_path or get_settings().repo_dir

    def parse_all(self) -> RepositoryData:
        """Parse entire repository into structured data."""
        projects = self.parse_projects()
        discoveries = self.parse_discoveries()
        tables: dict[str, list[Table]] = {}
        for collection_id, snapshot_tables in self.parse_berdl_snapshot_tables().items():
            tables[collection_id] = snapshot_tables
        pitfalls = self.parse_pitfalls()
        performance_tips = self.parse_performance()
        research_ideas = self.parse_research_ideas()
        collections = self.parse_collections()
        skills = self.parse_skills()
        atlas_index = self.parse_atlas()

        # Aggregate unique contributors across all projects
        contributors = self._aggregate_contributors(projects)

        # Auto-cluster projects into research areas
        research_areas = self._cluster_research_areas(projects)

        # Compute collection-to-collection edges
        collection_edges = self._compute_collection_edges(collections, projects)

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
            skills=skills,
            research_areas=research_areas,
            collection_edges=collection_edges,
            atlas_index=atlas_index,
            total_notebooks=total_notebooks,
            total_visualizations=total_visualizations,
            total_data_files=total_data_files,
            last_updated=datetime.now(),
        )

    @staticmethod
    def _contributor_key(name: str) -> str:
        """Normalize contributor name for deduplication.

        Strips middle initials (single chars followed by period) so
        'Paramvir S. Dehal' and 'Paramvir Dehal' merge correctly.
        """
        # Remove single-letter-dot patterns like "S." or "J."
        normalized = re.sub(r"\b[A-Za-z]\.\s*", "", name)
        return " ".join(normalized.lower().split())

    def _aggregate_contributors(self, projects: list[Project]) -> list[Contributor]:
        """Merge contributors across projects by normalized name."""
        merged: dict[str, Contributor] = {}

        for project in projects:
            for contrib in project.contributors:
                key = self._contributor_key(contrib.name)
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
                    # Prefer longer name (e.g., "Paramvir S. Dehal" over "Paramvir Dehal")
                    if len(contrib.name) > len(existing.name):
                        existing.name = contrib.name
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

    @staticmethod
    def _cluster_research_areas(projects: list[Project]) -> list[ResearchArea]:
        """Auto-cluster projects into thematic research areas.

        Uses text similarity (title + research question), data provenance,
        and shared collections as signals. Agglomerative clustering with
        average linkage.
        """
        from collections import Counter
        from math import sqrt

        _STOP = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "can",
            "this",
            "that",
            "these",
            "those",
            "it",
            "its",
            "we",
            "our",
            "how",
            "what",
            "which",
            "where",
            "when",
            "who",
            "than",
            "more",
            "most",
            "between",
            "across",
            "each",
            "per",
            "using",
            "used",
            "based",
            "whether",
            "not",
            "no",
            "into",
            "also",
            "both",
            "all",
            "show",
            "results",
            "data",
            "analysis",
            "gene",
            "genes",
            "genome",
            "genomes",
            "species",
            "bacterial",
            "bacteria",
            "pangenome",
            "pangenomes",
            "fitness",
        }

        def _terms(text: str | None) -> Counter:
            if not text:
                return Counter()
            words = re.findall(r"[a-z]{4,}", text.lower())
            return Counter(w for w in words if w not in _STOP)

        def _cosine(a: Counter, b: Counter) -> float:
            keys = set(a) | set(b)
            dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
            mag_a = sqrt(sum(v**2 for v in a.values()))
            mag_b = sqrt(sum(v**2 for v in b.values()))
            if mag_a == 0 or mag_b == 0:
                return 0.0
            return dot / (mag_a * mag_b)

        if not projects:
            return []

        pids = [p.id for p in projects]
        features = {}
        dep_sets = {}
        for p in projects:
            features[p.id] = _terms(p.title) + _terms(p.research_question)
            dep_sets[p.id] = {r.source_project for r in p.derived_from}

        # Pairwise similarity with data dep boost
        sims: dict[tuple[str, str], float] = {}
        for i in range(len(pids)):
            for j in range(i + 1, len(pids)):
                a, b = pids[i], pids[j]
                s = _cosine(features[a], features[b])
                if b in dep_sets[a] or a in dep_sets[b]:
                    s += 0.3
                if dep_sets[a] & dep_sets[b]:
                    s += 0.15
                sims[(a, b)] = s
                sims[(b, a)] = s

        # Agglomerative clustering (average linkage)
        clusters: dict[str, list[str]] = {pid: [pid] for pid in pids}
        THRESHOLD = 0.25

        while True:
            best_sim = 0.0
            best_pair = None
            ckeys = list(clusters.keys())
            for i in range(len(ckeys)):
                for j in range(i + 1, len(ckeys)):
                    total = sum(
                        sims.get((a, b), 0.0)
                        for a in clusters[ckeys[i]]
                        for b in clusters[ckeys[j]]
                    )
                    count = len(clusters[ckeys[i]]) * len(clusters[ckeys[j]])
                    avg = total / count if count else 0.0
                    if avg > best_sim:
                        best_sim = avg
                        best_pair = (ckeys[i], ckeys[j])
            if best_sim < THRESHOLD or best_pair is None:
                break
            a, b = best_pair
            clusters[a].extend(clusters[b])
            del clusters[b]

        # Build ResearchArea objects
        areas = []
        singletons = []
        for members in clusters.values():
            # Auto-name from top distinctive terms
            combined = Counter()
            for pid in members:
                combined += features[pid]
            top = [t for t, _ in combined.most_common(3)]
            name = " & ".join(w.title() for w in top[:2]) if top else "Misc"

            if len(members) == 1:
                singletons.extend(members)
            else:
                areas.append(
                    ResearchArea(
                        id=slugify(name),
                        name=name,
                        project_ids=sorted(members),
                        top_terms=[t for t, _ in combined.most_common(5)],
                    )
                )

        # Sort by cluster size descending
        areas.sort(key=lambda a: len(a.project_ids), reverse=True)

        # Group singletons under "Independent Studies"
        if singletons:
            areas.append(
                ResearchArea(
                    id="independent-studies",
                    name="Independent Studies",
                    project_ids=sorted(singletons),
                    top_terms=[],
                )
            )

        return areas

    @staticmethod
    def _compute_collection_edges(
        collections: list[Collection], projects: list[Project]
    ) -> list[CollectionEdge]:
        """Build collection-to-collection edges from explicit links and project co-usage.

        Two edge types:
        1. "explicit" — from Collection.related_collections in collections.yaml
        2. "project_cooccurrence" — projects that reference multiple collections
        """
        edges: dict[tuple[str, str], CollectionEdge] = {}
        collection_ids = {c.id for c in collections}

        def _edge_key(a: str, b: str) -> tuple[str, str]:
            return (min(a, b), max(a, b))

        # Explicit links from collections.yaml
        for coll in collections:
            for related_id in coll.related_collections:
                if related_id in collection_ids:
                    key = _edge_key(coll.id, related_id)
                    if key not in edges:
                        edges[key] = CollectionEdge(
                            source_id=key[0],
                            target_id=key[1],
                            edge_type="explicit",
                        )

        # Project co-occurrence: projects that reference 2+ collections
        for project in projects:
            colls = [c for c in project.related_collections if c in collection_ids]
            for i in range(len(colls)):
                for j in range(i + 1, len(colls)):
                    key = _edge_key(colls[i], colls[j])
                    if key not in edges:
                        edges[key] = CollectionEdge(
                            source_id=key[0],
                            target_id=key[1],
                            edge_type="project_cooccurrence",
                        )
                    if project.id not in edges[key].projects:
                        edges[key].projects.append(project.id)

        return sorted(edges.values(), key=lambda e: (e.source_id, e.target_id))

    def _get_git_dates(
        self, project_dir: Path
    ) -> tuple[datetime | None, datetime | None]:
        """Get first and last commit dates for a project directory using git log."""
        try:
            # Last commit date
            result = subprocess.run(
                ["git", "log", "-1", "--format=%aI", "--", str(project_dir)],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
            )
            updated = (
                datetime.fromisoformat(result.stdout.strip())
                if result.stdout.strip()
                else None
            )

            # First commit date
            result = subprocess.run(
                ["git", "log", "--reverse", "--format=%aI", "--", str(project_dir)],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
            )
            lines = result.stdout.strip().split("\n")
            created = datetime.fromisoformat(lines[0]) if lines and lines[0] else None

            return created, updated
        except Exception:
            return None, None

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

        # Compute reverse mapping: which projects use each project's data
        project_ids = {p.id for p in projects}
        for project in projects:
            for ref in project.derived_from:
                if ref.source_project in project_ids:
                    # Find the source project and add this project to its used_by
                    for src in projects:
                        if src.id == ref.source_project:
                            if project.id not in src.used_by:
                                src.used_by.append(project.id)
                            break

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
            revision_history = self._extract_section(
                research_plan_raw, "Revision History"
            )
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
        data_section = None
        references = None
        other_sections = []

        _KNOWN_REPORT_SECTIONS = {
            "Key Findings",
            "Results",
            "Interpretation",
            "Limitations",
            "Future Directions",
            "Data",
            "References",
            "Supporting Evidence",
            "Revision History",
        }

        if has_report:
            report_raw = report_path.read_text()
            findings = self._extract_section(report_raw, "Key Findings")
            results = self._extract_section(report_raw, "Results")
            interpretation = self._extract_section(report_raw, "Interpretation")
            limitations = self._extract_section(report_raw, "Limitations")
            future_directions = self._extract_section(report_raw, "Future Directions")
            data_section = self._extract_section(report_raw, "Data")
            references = self._extract_section(report_raw, "References")
            other_sections = self._extract_other_sections(
                report_raw, _KNOWN_REPORT_SECTIONS
            )
        else:
            # Fallback: extract from README (legacy projects)
            findings = self._extract_section(readme_content, "Key Findings")

        # Determine status
        if (
            findings
            and "to be filled" not in findings.lower()
            and "tbd" not in findings.lower()
        ):
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

        # Scan notebooks for cross-project data dependencies
        derived_from = self._scan_notebook_data_deps(project_dir)

        # Parse visualizations and data files
        visualizations, data_files = self._parse_data_dir(project_dir)

        # Parse contributors
        contributors = self._parse_contributors(readme_content, project_dir.name)

        # Get dates from git history (reliable in CI), fall back to filesystem
        git_created, git_updated = self._get_git_dates(project_dir)
        if git_created and git_updated:
            created_date = git_created
            updated_date = git_updated
        else:
            created_date = datetime.fromtimestamp(readme_path.stat().st_ctime)
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
            findings=self._rewrite_md_links(findings, project_dir.name),
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
            overview=self._rewrite_md_links(overview, project_dir.name),
            results=self._rewrite_md_links(results, project_dir.name),
            interpretation=self._rewrite_md_links(interpretation, project_dir.name),
            limitations=self._rewrite_md_links(limitations, project_dir.name),
            future_directions=self._rewrite_md_links(
                future_directions, project_dir.name
            ),
            data_section=self._rewrite_md_links(data_section, project_dir.name),
            references=self._rewrite_md_links(references, project_dir.name),
            other_sections=[
                (name, self._rewrite_md_links(body, project_dir.name) or body)
                for name, body in other_sections
            ],
            revision_history=revision_history,
            derived_from=derived_from,
        )

    @staticmethod
    def _rewrite_md_links(content: str | None, project_id: str) -> str | None:
        """Rewrite bare .md links and image paths to be project-relative.

        Converts e.g. [Report](REPORT.md) to [Report](/projects/{id}/REPORT.md)
        and ![caption](figures/foo.png) to ![caption](/project-assets/{id}/figures/foo.png)
        so the browser resolves them correctly.
        """
        if not content:
            return content
        # Rewrite .md links to project-relative paths
        content = re.sub(
            r"\[([^\]]+)\]\(([A-Za-z0-9_.-]+\.md)\)",
            rf"[\1](/projects/{project_id}/\2)",
            content,
        )
        # Rewrite relative image paths to /project-assets/ URLs
        content = re.sub(
            r"!\[([^\]]*)\]\((figures/[^)]+)\)",
            rf"![\1](/project-assets/{project_id}/\2)",
            content,
        )
        return content

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
            # Match lines starting with - **Name** (bold format)
            match = re.match(r"^-\s+\*\*(.+?)\*\*\s*(.*)", line)
            if not match:
                # Fallback: plain format - Name, Affiliation or - Name (url)
                plain = re.match(r"^-\s+(.+)", line)
                if not plain:
                    continue
                plain_text = plain.group(1).strip()
                # Extract ORCID if present
                orcid = None
                # Full pattern: (ORCID: [id](url)) or (ORCID: id)
                orcid_paren_match = re.search(
                    r"\(ORCID:\s*\[?([\d-]+)\]?(?:\([^)]*\))?\)",
                    plain_text,
                )
                if orcid_paren_match:
                    orcid = orcid_paren_match.group(1)
                    plain_text = (
                        (
                            plain_text[: orcid_paren_match.start()]
                            + plain_text[orcid_paren_match.end() :]
                        )
                        .strip()
                        .strip(",")
                        .strip()
                    )
                else:
                    # Bare URL fallback: (https://orcid.org/id)
                    orcid_url_match = re.search(
                        r"\(https://orcid\.org/([\d-]+)\)", plain_text
                    )
                    if orcid_url_match:
                        orcid = orcid_url_match.group(1)
                        plain_text = (
                            (
                                plain_text[: orcid_url_match.start()]
                                + plain_text[orcid_url_match.end() :]
                            )
                            .strip()
                            .strip(",")
                            .strip()
                        )
                # Split by comma: first part is name, rest is affiliation
                parts = [p.strip() for p in plain_text.split(",", 1)]
                name = parts[0]
                affiliation = parts[1] if len(parts) > 1 else None
                contributors.append(
                    Contributor(
                        name=name,
                        affiliation=affiliation,
                        orcid=orcid,
                        roles=[],
                        project_ids=[project_id],
                    )
                )
                continue

            name = match.group(1).strip()
            rest = match.group(2).strip()

            orcid = None
            affiliation = None
            roles = []

            # Format 1: (ORCID: [id](url)) -- Affiliation
            orcid_paren = re.match(
                r"\(ORCID:\s*\[?([\d-]+)\]?(?:\([^)]*\))?\)\s*[-—]+\s*(.*)",
                rest,
            )
            if orcid_paren:
                orcid = orcid_paren.group(1)
                affiliation = orcid_paren.group(2).strip() or None
            else:
                # Format 2: (Affiliation) | ORCID: 0000-... | role
                paren_match = re.match(r"\(([^)]+)\)\s*(.*)", rest)
                if paren_match:
                    affiliation = paren_match.group(1).strip()
                    rest = paren_match.group(2).strip()

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
        """Extract content between a ## section header and the next ## header."""
        pattern = rf"^## {re.escape(section_name)}\s*$\n(.*?)(?=^## (?!#)|\Z)"
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def _extract_other_sections(
        self, content: str, known_sections: set[str]
    ) -> list[tuple[str, str]]:
        """Extract ## sections from content that aren't in the known set.

        Returns a list of (section_name, section_content) tuples.
        """
        others = []
        for match in re.finditer(
            r"^## (.+?)\s*$\n(.*?)(?=^## (?!#)|\Z)",
            content,
            re.MULTILINE | re.DOTALL,
        ):
            name = match.group(1).strip()
            if name not in known_sections:
                body = match.group(2).strip()
                if body:
                    others.append((name, body))
        return others

    def _scan_notebook_data_deps(self, project_dir: Path) -> list[DerivedDataRef]:
        """Scan notebook code cells for cross-project data references.

        Detects patterns like:
        - ../../other_project/data/file.tsv
        - .parent / 'other_project' / 'data'
        - projects/other_project/data/file.tsv
        """
        notebooks_dir = project_dir / "notebooks"
        if not notebooks_dir.exists():
            return []

        project_id = project_dir.name
        # source_project -> set of filenames
        deps: dict[str, set[str]] = {}

        patterns = [
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

        import json

        for nb_path in notebooks_dir.glob("*.ipynb"):
            try:
                nb_data = json.loads(nb_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

            for cell in nb_data.get("cells", []):
                if cell.get("cell_type") != "code":
                    continue
                source = "".join(cell.get("source", []))
                for pattern in patterns:
                    for match in pattern.finditer(source):
                        src_project = match.group(1)
                        if src_project == project_id:
                            continue
                        filename = (
                            match.group(2)
                            if match.lastindex >= 2 and match.group(2)
                            else None
                        )
                        deps.setdefault(src_project, set())
                        if filename:
                            deps[src_project].add(filename)

        return [
            DerivedDataRef(source_project=sp, files=sorted(files))
            for sp, files in sorted(deps.items())
        ]

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

    def _extract_plotly_height(self, html_path: Path) -> int | None:
        """
        Extract figure height (px) from the plotly-graph-div in a Plotly HTML export.
        Adds an extra 20 px as a buffer to avoid having a scrollbar.
        """
        try:
            from bs4 import BeautifulSoup

            with open(html_path, encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
            div = soup.find("div", class_="plotly-graph-div")
            if div is None:
                return None
            style = div.get("style", "")
            for part in style.split(";"):
                part = part.strip()
                if part.startswith("height:"):
                    val = part.split(":")[1].strip()
                    if val.endswith("px"):
                        return int(val[:-2]) + 20
        except Exception:
            pass
        return None

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
                    ".html",
                ):
                    is_interactive = file_path.suffix.lower() == ".html"
                    iframe_height = None
                    if is_interactive:
                        iframe_height = self._extract_plotly_height(file_path)
                    visualizations.append(
                        Visualization(
                            filename=file_path.name,
                            path=str(file_path.relative_to(self.repo_path)),
                            title=file_path.stem.replace("_", " ").title(),
                            size_bytes=size_bytes,
                            is_interactive=is_interactive,
                            iframe_height=iframe_height,
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

        # Strip the template section at the end (## Template ...)
        template_match = re.search(r"^## Template\b", content, re.MULTILINE)
        if template_match:
            content = content[: template_match.start()]

        # Extract date headers and their positions first
        date_positions = []
        for m in re.finditer(r"^## (\d{4}-\d{2})\s*$", content, re.MULTILINE):
            date_positions.append((m.start(), datetime.strptime(m.group(1), "%Y-%m")))

        # Split by ### headers (discovery entries)
        sections = re.split(r"\n###\s+", content)

        # Track cumulative character position to map sections to dates
        current_date = None
        pos = 0

        for section in sections[1:]:  # Skip intro
            # Advance past the split delimiter to find our position
            pos = content.find(section, pos)

            # Update current_date from any date headers before this position
            while date_positions and date_positions[0][0] < pos:
                current_date = date_positions.pop(0)[1]

            if not section.strip():
                continue

            lines = section.split("\n")
            title_line = lines[0].strip()

            # Parse [project_tag] from title
            match = re.match(r"\[(\w+)\]\s+(.+)", title_line)
            if match:
                project_tag = match.group(1)
                title = match.group(2)
                # Strip any trailing ## date headers from the content
                content_text = "\n".join(lines[1:])
                content_text = re.sub(r"\n## \d{4}-\d{2}\s*$", "", content_text).strip()

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

    def parse_berdl_snapshot_tables(self) -> dict[str, list[Table]]:
        """Parse table schemas from the generated BERDL discovery snapshot."""
        snapshot = self._load_berdl_snapshot()
        tables_by_collection: dict[str, list[Table]] = {}
        if not snapshot:
            return tables_by_collection

        for tenant in snapshot.get("tenants", []):
            for coll_data in tenant.get("collections", []):
                collection_id = str(coll_data.get("id", ""))
                if not collection_id:
                    continue
                tables: list[Table] = []
                for table_data in coll_data.get("tables", []):
                    columns = [
                        Column(
                            name=str(col.get("name", "")),
                            data_type=str(col.get("data_type") or col.get("type") or ""),
                            description=col.get("description"),
                        )
                        for col in table_data.get("columns", [])
                        if col.get("name")
                    ]
                    row_count = table_data.get("row_count") or 0
                    try:
                        row_count = int(row_count)
                    except (TypeError, ValueError):
                        row_count = 0
                    tables.append(
                        Table(
                            name=str(table_data.get("name", "")),
                            description=str(table_data.get("description", "")).strip(),
                            row_count=row_count,
                            columns=columns,
                        )
                    )
                if tables:
                    tables_by_collection[collection_id] = tables
        return tables_by_collection

    def parse_collections(self) -> list[Collection]:
        """Parse BERDL collections from discovery snapshot plus curated overlays."""
        curated = self._load_curated_collection_data()
        snapshot = self._load_berdl_snapshot()

        if not snapshot:
            return [
                self._collection_from_curated(coll_data)
                for coll_data in curated.values()
            ]

        snapshot_source = str(snapshot.get("source_url") or snapshot.get("source") or "")
        discovered_at = str(snapshot.get("discovered_at") or "")
        snapshot_ids = {
            str(coll.get("id"))
            for tenant in snapshot.get("tenants", [])
            for coll in tenant.get("collections", [])
            if coll.get("id")
        }

        collections: list[Collection] = []
        for tenant in snapshot.get("tenants", []):
            tenant_id = str(tenant.get("id", "")).strip()
            tenant_name = str(tenant.get("name") or tenant_id).strip()
            for coll_data in tenant.get("collections", []):
                collection_id = str(coll_data.get("id", "")).strip()
                if not collection_id:
                    continue
                overlay = curated.get(collection_id, {})
                group_overlays = self._matching_group_overlays(collection_id, curated)
                collections.append(
                    self._collection_from_snapshot(
                        coll_data=coll_data,
                        tenant_id=tenant_id,
                        tenant_name=tenant_name,
                        snapshot_source=snapshot_source,
                        discovered_at=discovered_at,
                        overlay=overlay,
                        group_overlays=group_overlays,
                        snapshot_ids=snapshot_ids,
                    )
                )

        return collections

    def _load_berdl_snapshot(self) -> dict[str, Any]:
        snapshot_path = self.repo_path / "ui" / "config" / "berdl_collections_snapshot.json"
        if not snapshot_path.exists():
            return {}
        try:
            with open(snapshot_path) as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def _load_curated_collection_data(self) -> dict[str, dict[str, Any]]:
        config_path = self.repo_path / "ui" / "config" / "collections.yaml"
        if not config_path.exists():
            return {}
        with open(config_path) as f:
            data = yaml.safe_load(f)
        if not data or "collections" not in data:
            return {}
        return {
            str(coll_data.get("id", "")): coll_data
            for coll_data in data["collections"]
            if coll_data.get("id")
        }

    def _matching_group_overlays(
        self, collection_id: str, curated: dict[str, dict[str, Any]]
    ) -> list[dict[str, Any]]:
        groups: list[dict[str, Any]] = []
        for group_id, coll_data in curated.items():
            if group_id == collection_id:
                continue
            for child_id in coll_data.get("sub_collections", []):
                child_id = str(child_id)
                if collection_id == child_id or collection_id.startswith(child_id):
                    groups.append(coll_data)
                    break
        return groups

    def _collection_from_curated(self, coll_data: dict[str, Any]) -> Collection:
        return Collection(
            id=coll_data.get("id", ""),
            name=coll_data.get("name", ""),
            category=self._collection_category(coll_data.get("category", "primary")),
            icon=coll_data.get("icon", "&#128194;"),
            description=coll_data.get("description", "").strip(),
            philosophy=coll_data.get("philosophy", "").strip(),
            data_sources=coll_data.get("data_sources", []),
            scale_stats=coll_data.get("scale_stats", {}),
            key_tables=self._collection_tables(coll_data.get("key_tables", [])),
            sample_queries=self._sample_queries(coll_data.get("sample_queries", [])),
            related_collections=coll_data.get("related_collections", []),
            sub_collections=coll_data.get("sub_collections", []),
            citation=coll_data.get("citation"),
            doi=coll_data.get("doi"),
            website=coll_data.get("website"),
            provider=coll_data.get("provider"),
            schema_status="curated",
            curation_status="curated",
        )

    def _collection_from_snapshot(
        self,
        coll_data: dict[str, Any],
        tenant_id: str,
        tenant_name: str,
        snapshot_source: str,
        discovered_at: str,
        overlay: dict[str, Any],
        group_overlays: list[dict[str, Any]],
        snapshot_ids: set[str],
    ) -> Collection:
        group_ids = [str(group.get("id")) for group in group_overlays if group.get("id")]
        parent_collection_id = group_ids[0] if group_ids else None
        name = overlay.get("name") or coll_data.get("name") or self._title_from_id(coll_data.get("id", ""))
        description = (
            overlay.get("description")
            or coll_data.get("description")
            or "Discovered BERDL database. Add curated description as this collection is used."
        )
        group_description = next(
            (group.get("description", "").strip() for group in group_overlays if group.get("description")),
            "",
        )
        if not overlay and group_description:
            description = group_description

        category = self._collection_category(
            overlay.get("category")
            or next((group.get("category") for group in group_overlays if group.get("category")), None)
            or ("primary" if tenant_id == "kbase" else "domain")
        )
        key_tables = self._collection_tables(coll_data.get("tables", []))
        if overlay.get("key_tables"):
            key_tables = self._collection_tables(overlay.get("key_tables", []))

        related = self._canonical_related_collections(
            overlay.get("related_collections", []), snapshot_ids
        )
        if not related:
            for group in group_overlays:
                related.extend(
                    self._canonical_related_collections(
                        group.get("related_collections", []), snapshot_ids
                    )
                )
        related = sorted(set(related))

        errors = [
            str(err)
            for err in coll_data.get("discovery_errors", [])
            if str(err).strip()
        ]
        schema_status = "discovered"
        if errors:
            schema_status = "partial"
        if not coll_data.get("tables"):
            schema_status = "missing"

        return Collection(
            id=str(coll_data.get("id", "")),
            name=str(name),
            category=category,
            icon=overlay.get("icon")
            or next((group.get("icon") for group in group_overlays if group.get("icon")), "&#128194;"),
            description=str(description).strip(),
            philosophy=str(overlay.get("philosophy") or "").strip(),
            data_sources=overlay.get("data_sources", coll_data.get("data_sources", [])),
            scale_stats=overlay.get("scale_stats", coll_data.get("scale_stats", {})),
            key_tables=key_tables,
            sample_queries=self._sample_queries(overlay.get("sample_queries", [])),
            related_collections=related,
            sub_collections=[],
            citation=overlay.get("citation"),
            doi=overlay.get("doi"),
            website=overlay.get("website"),
            provider=overlay.get("provider") or coll_data.get("provider"),
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            snapshot_source=snapshot_source,
            discovered_at=discovered_at,
            schema_status=schema_status,
            curation_status="curated" if overlay else "discovered",
            parent_collection_id=parent_collection_id,
            group_ids=group_ids,
            discovery_errors=errors,
        )

    @staticmethod
    def _collection_category(value: str | None) -> CollectionCategory:
        try:
            return CollectionCategory(value or "primary")
        except ValueError:
            return CollectionCategory.PRIMARY

    @staticmethod
    def _collection_tables(table_data: list[dict[str, Any]]) -> list[CollectionTable]:
        tables: list[CollectionTable] = []
        for item in table_data:
            row_count = item.get("row_count")
            try:
                row_count = int(row_count) if row_count is not None else None
            except (TypeError, ValueError):
                row_count = None
            tables.append(
                CollectionTable(
                    name=str(item.get("name", "")),
                    description=str(item.get("description", "")),
                    row_count=row_count,
                )
            )
        return tables

    @staticmethod
    def _sample_queries(query_data: list[dict[str, Any]]) -> list[SampleQuery]:
        return [
            SampleQuery(title=str(item.get("title", "")), query=str(item.get("query", "")))
            for item in query_data
        ]

    @staticmethod
    def _canonical_related_collections(
        related_ids: list[str], snapshot_ids: set[str]
    ) -> list[str]:
        canonical: list[str] = []
        for related_id in related_ids:
            related_id = str(related_id)
            if related_id in snapshot_ids:
                canonical.append(related_id)
                continue
            matches = sorted(cid for cid in snapshot_ids if cid.startswith(related_id))
            canonical.extend(matches)
        return canonical

    @staticmethod
    def _title_from_id(collection_id: str) -> str:
        return collection_id.replace("_", " ").title()

    def parse_atlas(self) -> AtlasIndex:
        """Parse markdown Atlas pages from the Atlas corpus directory.

        The parser is intentionally permissive: malformed pages are skipped so the
        app can still boot, while app.atlas_lint reports actionable failures.
        """
        atlas_dir = self.repo_path / "atlas"
        if not atlas_dir.exists():
            return AtlasIndex()

        pages: list[AtlasPage] = []
        for atlas_file in sorted(atlas_dir.rglob("*.md")):
            if any(
                part.startswith(".") for part in atlas_file.relative_to(atlas_dir).parts
            ):
                continue
            page = self._parse_atlas_file(atlas_file, atlas_dir)
            if page:
                pages.append(page)

        pages.sort(key=lambda p: (p.section, p.order, p.title.lower()))
        links = [
            AtlasLink(source_id=page.id, target_id=target_id)
            for page in pages
            for target_id in page.related_pages
        ]
        return AtlasIndex(pages=pages, links=links)

    @classmethod
    def _parse_atlas_file(cls, atlas_file: Path, atlas_dir: Path) -> AtlasPage | None:
        """Parse one Atlas markdown file with YAML frontmatter."""
        try:
            raw_content = atlas_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return None

        frontmatter_match = re.match(
            r"^---\s*\n(.*?)\n---\s*\n?", raw_content, re.DOTALL
        )
        if not frontmatter_match:
            return None

        try:
            frontmatter = yaml.safe_load(frontmatter_match.group(1)) or {}
        except yaml.YAMLError:
            return None
        if not isinstance(frontmatter, dict):
            return None

        missing = cls.REQUIRED_ATLAS_FIELDS - set(frontmatter)
        if missing:
            return None
        if frontmatter.get("type") not in cls.ATLAS_PAGE_TYPES:
            return None

        route_path = atlas_file.relative_to(atlas_dir).with_suffix("").as_posix()
        body = raw_content[frontmatter_match.end() :].strip()
        section = route_path.split("/", 1)[0] if "/" in route_path else "root"

        known_keys = cls.REQUIRED_ATLAS_FIELDS | {
            "related_pages",
            "order",
            "section",
        }
        metadata = {k: v for k, v in frontmatter.items() if k not in known_keys}

        return AtlasPage(
            id=str(frontmatter["id"]),
            title=str(frontmatter["title"]),
            type=str(frontmatter["type"]),
            status=str(frontmatter["status"]),
            summary=str(frontmatter["summary"]),
            path=route_path,
            body=cls._rewrite_atlas_body_links(body, route_path),
            source_projects=cls._as_string_list(frontmatter.get("source_projects")),
            source_docs=cls._as_string_list(frontmatter.get("source_docs")),
            related_collections=cls._as_string_list(
                frontmatter.get("related_collections")
            ),
            related_pages=cls._as_string_list(frontmatter.get("related_pages")),
            confidence=str(frontmatter.get("confidence", "medium")),
            generated_by=str(frontmatter.get("generated_by", "")),
            last_reviewed=str(frontmatter.get("last_reviewed", "")),
            section=str(frontmatter.get("section") or section),
            order=int(frontmatter.get("order", 100)),
            metadata=metadata,
            headings=cls._extract_atlas_headings(body),
        )

    @staticmethod
    def _as_string_list(value) -> list[str]:
        """Normalize a frontmatter scalar/list/null into a string list."""
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v) for v in value if v is not None]
        return [str(value)]

    @staticmethod
    def _rewrite_atlas_body_links(content: str, route_path: str) -> str:
        """Rewrite common repo-relative Atlas links to route links."""
        source_dir = posixpath.dirname(route_path)

        def _md_link(match: re.Match) -> str:
            target = match.group(1)
            anchor = match.group(2) or ""
            target_route = posixpath.normpath(posixpath.join(source_dir, target))
            if target_route == ".":
                target_route = ""
            return f"](/atlas/{target_route}{anchor})"

        content = re.sub(
            r"\]\((?:\./)?([A-Za-z0-9_./-]+)\.md(#.*?)?\)",
            _md_link,
            content,
        )
        content = re.sub(r"\]\((?:\./)?index(#.*?)?\)", r"](/atlas\1)", content)
        return content

    @staticmethod
    def _extract_atlas_headings(content: str) -> list[AtlasHeading]:
        """Extract markdown headings for page-level Atlas navigation."""
        headings: list[AtlasHeading] = []
        seen: dict[str, int] = {}
        for line in content.splitlines():
            match = re.match(r"^(#{2,4})\s+(.+?)\s*$", line)
            if not match:
                continue
            title = re.sub(r"`([^`]+)`", r"\1", match.group(2)).strip()
            anchor = RepositoryParser._slugify_heading(title)
            duplicate_count = seen.get(anchor, 0)
            seen[anchor] = duplicate_count + 1
            if duplicate_count:
                anchor = f"{anchor}_{duplicate_count}"
            headings.append(
                AtlasHeading(level=len(match.group(1)), title=title, anchor=anchor)
            )
        return headings

    @staticmethod
    def _slugify_heading(title: str) -> str:
        """Mirror the markdown TOC extension's simple slug convention."""
        slug = title.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        return slug

    def parse_skills(self) -> list[Skill]:
        """Parse skills from .claude/skills/*/SKILL.md frontmatter."""
        skills = []
        skills_dir = self.repo_path / ".claude" / "skills"

        if not skills_dir.exists():
            return skills

        for skill_dir in sorted(skills_dir.iterdir()):
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            content = skill_file.read_text()

            # Parse YAML frontmatter
            frontmatter_match = re.match(
                r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL
            )
            if not frontmatter_match:
                continue

            try:
                frontmatter = yaml.safe_load(frontmatter_match.group(1))
                if not isinstance(frontmatter, dict):
                    continue
            except Exception:
                continue

            skills.append(
                Skill(
                    name=frontmatter.get("name", skill_dir.name),
                    description=frontmatter.get("description", ""),
                    user_invocable=frontmatter.get("user-invocable", False),
                )
            )

        return skills


# Singleton instance
_parser: RepositoryParser | None = None


def get_parser() -> RepositoryParser:
    """Get or create parser singleton."""
    global _parser
    if _parser is None:
        _parser = RepositoryParser()
    return _parser
