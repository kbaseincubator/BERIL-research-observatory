from __future__ import annotations

from pathlib import Path

from observatory_context import fallback
from observatory_context.config import ContextConfig


def _repo(tmp_path: Path) -> ContextConfig:
    (tmp_path / "projects" / "alpha").mkdir(parents=True)
    (tmp_path / "projects" / "alpha" / "README.md").write_text(
        "# Alpha\nStudies phage timing in soil.\n"
    )
    (tmp_path / "projects" / "alpha" / "memories").mkdir()
    (tmp_path / "projects" / "alpha" / "memories" / "pitfalls.md").write_text(
        "[alpha] Spark OOM on the big table.\n"
    )
    # Non-corpus content must never be searched.
    (tmp_path / "projects" / "alpha" / "data").mkdir()
    (tmp_path / "projects" / "alpha" / "data" / "notes.md").write_text("phage phage phage\n")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "pitfalls.md").write_text("## kbase\nSpark timeout gotcha.\n")
    return ContextConfig(repo_root=tmp_path)


def test_file_uri_and_uri_to_path_round_trip(tmp_path: Path) -> None:
    config = _repo(tmp_path)
    readme = tmp_path / "projects" / "alpha" / "README.md"
    pitfalls_doc = tmp_path / "docs" / "pitfalls.md"
    memory = tmp_path / "projects" / "alpha" / "memories" / "pitfalls.md"

    assert fallback.file_uri(config, readme) == "viking://resources/projects/alpha/README.md"
    assert fallback.file_uri(config, memory) == (
        "viking://resources/projects/alpha/memories/pitfalls.md"
    )
    assert fallback.file_uri(config, pitfalls_doc) == "viking://resources/docs/pitfalls/pitfalls.md"

    assert fallback.uri_to_path(config, fallback.file_uri(config, readme)) == readme
    assert fallback.uri_to_path(config, fallback.file_uri(config, memory)) == memory
    assert fallback.uri_to_path(config, fallback.file_uri(config, pitfalls_doc)) == pitfalls_doc
    # Directory form of a doc URI resolves to docs/<slug>.md too.
    assert fallback.uri_to_path(config, "viking://resources/docs/pitfalls/") == pitfalls_doc


def test_local_find_is_degraded_scoped_and_skips_non_corpus(tmp_path: Path) -> None:
    config = _repo(tmp_path)

    result = fallback.local_find(config, "phage timing", "viking://resources/projects/", 10)

    assert result["degraded"] is True
    assert result["source"] == "local"
    uris = [r["uri"] for r in result["resources"]]
    assert "viking://resources/projects/alpha/README.md" in uris
    # data/notes.md is not in the selection corpus, so it is never returned.
    assert all("/data/" not in uri for uri in uris)
    top = result["resources"][0]
    assert top["score"] == 1.0  # both query terms present
    assert "phage" in top["abstract"].lower()


def test_local_find_scope_filters_to_docs(tmp_path: Path) -> None:
    config = _repo(tmp_path)

    result = fallback.local_find(config, "Spark", "viking://resources/docs/", 10)

    uris = [r["uri"] for r in result["resources"]]
    assert uris == ["viking://resources/docs/pitfalls/pitfalls.md"]


def test_local_grep_matches_and_excludes(tmp_path: Path) -> None:
    config = _repo(tmp_path)

    result = fallback.local_grep(config, "Spark", "viking://resources/")
    assert result["degraded"] is True
    hit_uris = {m["uri"] for m in result["matches"]}
    assert "viking://resources/projects/alpha/memories/pitfalls.md" in hit_uris
    assert "viking://resources/docs/pitfalls/pitfalls.md" in hit_uris

    excluded = fallback.local_grep(
        config, "Spark", "viking://resources/", exclude_uri="viking://resources/docs/"
    )
    assert all(not m["uri"].startswith("viking://resources/docs/") for m in excluded["matches"])


def test_local_read_resolves_uri_to_file(tmp_path: Path) -> None:
    config = _repo(tmp_path)
    content = fallback.local_read(config, "viking://resources/projects/alpha/README.md")
    assert "phage timing in soil" in content
