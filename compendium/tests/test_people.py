from pathlib import Path

import pytest

from compendium.people import parse_authors, build_author_index

README = """# Title
## Authors
- Beril Admin (https://orcid.org/0009-0007-0287-2979), Lawrence Berkeley National Laboratory
- Paramvir S. Dehal (https://orcid.org/0000-0001-5810-2497), Lawrence Berkeley National Laboratory
## Overview
"""

# Real corpus format: bold name, indented ORCID/Affiliation child bullets (gene_function_ecological_agora).
NESTED = """# Title
## Authors
- **Adam Arkin**
  - ORCID: 0000-0002-4999-2931
  - Affiliation: U.C. Berkeley / Lawrence Berkeley National Laboratory
## Overview
"""

# Real corpus format: bold name, em-dash affiliation, no ORCID (snipe_defense_system).
EMDASH = """# Title
## Authors
- **Chris Mungall** — Lawrence Berkeley National Laboratory
## Overview
"""

# Real corpus format: pipe-delimited (cog_analysis etc.).
PIPE = """# Title
## Authors
- **Christopher Neely** | ORCID: 0000-0002-2620-8948 | Author
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


def test_nested_subbullet_author_yields_one_clean_author():
    authors = parse_authors(NESTED)
    assert len(authors) == 1
    a = authors[0]
    assert a.name == "Adam Arkin"
    assert a.orcid == "0000-0002-4999-2931"
    assert "Berkeley" in (a.affiliation or "")


def test_no_phantom_label_authors():
    for a in parse_authors(NESTED):
        assert not a.name.lower().startswith(("orcid", "affiliation"))


def test_emdash_affiliation_not_glued_into_name():
    a = parse_authors(EMDASH)[0]
    assert a.name == "Chris Mungall"
    assert a.orcid is None
    assert "Lawrence Berkeley" in (a.affiliation or "")


def test_pipe_delimited_author():
    a = parse_authors(PIPE)[0]
    assert a.name == "Christopher Neely"
    assert a.orcid == "0000-0002-2620-8948"


def test_orcid_recovered_globally_so_person_does_not_fragment():
    with_orcid = "## Authors\n- Chris Mungall, LBNL, ORCID 0000-0002-6601-2165\n"
    name_only = "## Authors\n- **Chris Mungall** — Lawrence Berkeley National Laboratory\n"
    idx = build_author_index({"p1": with_orcid, "p2": name_only})
    assert sorted(idx["0000-0002-6601-2165"].projects) == ["p1", "p2"]
    assert "Chris Mungall" not in idx  # not fragmented into a name-keyed record


def test_corpus_authors_parse_clean():
    corpus = Path(__file__).resolve().parents[2] / "projects"
    if not corpus.exists():
        pytest.skip("corpus not present")
    readmes = {
        p.name: (p / "README.md").read_text()
        for p in sorted(corpus.iterdir())
        if (p / "README.md").is_file()
    }
    assert readmes, "no project READMEs found"

    rows = 0
    with_orcid = 0
    for project, text in readmes.items():
        authors = parse_authors(text)
        assert authors, f"{project} yielded no authors"
        for a in authors:
            rows += 1
            # no junk names leaked from labels or glued affiliations
            assert not a.name.lower().startswith(("orcid", "affiliation")), (project, a.name)
            assert "—" not in a.name and "–" not in a.name, (project, a.name)
            if a.orcid:
                with_orcid += 1

    assert with_orcid / rows >= 0.80

    idx = build_author_index(readmes)
    top = max(idx.values(), key=lambda r: len(r.projects))
    assert top.orcid == "0000-0001-5810-2497"  # Paramvir S. Dehal
    assert "Dehal" in top.name  # a real name, not "ORCID: ..."
