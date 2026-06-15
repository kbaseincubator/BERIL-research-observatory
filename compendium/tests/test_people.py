from pathlib import Path

import pytest

from compendium.people import parse_authors, build_author_index

README = """# Title
## Authors
- Beril Admin (https://orcid.org/0009-0007-0287-2979), Lawrence Berkeley National Laboratory
- Paramvir S. Dehal (https://orcid.org/0000-0001-5810-2497), Lawrence Berkeley National Laboratory
## Overview
"""


def test_parse_authors_extracts_name_orcid_affiliation():
    authors = parse_authors(README)
    dehal = next(a for a in authors if a.orcid == "0000-0001-5810-2497")
    assert dehal.name == "Paramvir S. Dehal"
    assert "Lawrence Berkeley" in dehal.affiliation


def test_build_author_index_groups_projects_by_orcid():
    idx = build_author_index({"proj_a": README, "proj_b": README})
    assert sorted(idx["0000-0001-5810-2497"].projects) == ["proj_a", "proj_b"]


def test_corpus_authors_parse():
    corpus = Path(__file__).resolve().parents[2] / "projects"
    if not corpus.exists():
        pytest.skip("corpus not present")
    readmes = {
        p.name: (p / "README.md").read_text()
        for p in sorted(corpus.iterdir())
        if (p / "README.md").is_file()
    }
    assert readmes, "no project READMEs found"

    with_orcid = 0
    for project, text in readmes.items():
        authors = parse_authors(text)
        assert authors, f"{project} yielded no authors"
        if any(a.orcid for a in authors):
            with_orcid += 1

    assert with_orcid / len(readmes) >= 0.85
