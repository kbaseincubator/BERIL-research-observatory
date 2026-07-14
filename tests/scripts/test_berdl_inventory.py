"""Tests for scripts/berdl_inventory.py."""
from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _isolate_default_cache(tmp_path_factory, monkeypatch):
    """Point the default inventory cache at a temp file so main() never reads or
    writes the repo's real data/berdl_inventory_cache.json during tests."""
    import scripts.berdl_inventory as mod
    monkeypatch.setattr(
        mod,
        "_DEFAULT_CACHE",
        tmp_path_factory.mktemp("inv_cache") / "berdl_inventory_cache.json",
    )


def _tenant(name, prefix="", **kwargs):
    from scripts.berdl_inventory import TenantInfo
    return TenantInfo(name=name, namespace_prefix=prefix, **kwargs)


def test_split_tenant_prefix_with_dot():
    from scripts.berdl_inventory import _split_tenant_prefix
    assert _split_tenant_prefix("kbase.ke_pangenome") == "kbase"
    assert _split_tenant_prefix("kescience.fitnessbrowser") == "kescience"


def test_split_tenant_prefix_no_dot():
    from scripts.berdl_inventory import _split_tenant_prefix
    assert _split_tenant_prefix("noprefix") == "(other)"


def test_format_inventory_empty():
    from scripts.berdl_inventory import format_inventory
    assert "No accessible databases" in format_inventory({})


def test_format_inventory_groups_by_tenant_no_metadata():
    from scripts.berdl_inventory import format_inventory
    structure = {
        "kbase.genomes": ["feature", "contig", "protein", "extra1", "extra2"],
        "kbase.ke_pangenome": ["gene", "gene_cluster"],
        "kescience.fitnessbrowser": ["experiments", "scores"],
    }
    out = format_inventory(structure, sample=3, emoji=False)
    assert "2 tenants" in out
    assert "3 databases" in out
    assert "9 tables" in out
    assert "### kbase" in out
    assert "### kescience" in out
    assert "`kbase.genomes`" in out
    assert "+2 more" in out  # 5 tables, sample=3 → 2 hidden


def test_format_inventory_uses_namespace_prefix():
    """When tenant metadata supplies namespace_prefix, use it instead of underscore split."""
    from scripts.berdl_inventory import format_inventory
    structure = {
        "kbase_dev.thing": ["t1"],
        "kbase.genomes": ["t1", "t2"],
    }
    # Two tenants share the 'kbase' underscore prefix; the dev one has a longer
    # namespace prefix that should win for kbase_dev_thing.
    tenants = [
        _tenant("kbase", prefix="kbase.", display_name="KBase"),
        _tenant("kbase_dev", prefix="kbase_dev.", display_name="KBase Dev"),
    ]
    out = format_inventory(structure, tenants=tenants, sample=3, emoji=False)
    # Section headers use the full tenant name, with display name when distinct.
    assert "### kbase — KBase" in out
    assert "### kbase_dev — KBase Dev" in out
    # kbase_dev_thing should be under the kbase_dev section, not kbase.
    kbase_section = out.split("### kbase — KBase")[1].split("###")[0]
    kbase_dev_section = out.split("### kbase_dev — KBase Dev")[1].split("> Run")[0]
    assert "kbase.genomes" in kbase_section
    assert "kbase_dev.thing" in kbase_dev_section
    assert "kbase_dev.thing" not in kbase_section


def test_format_inventory_renders_tenant_metadata():
    from scripts.berdl_inventory import format_inventory
    structure = {"kbase.genomes": ["t1"]}
    tenants = [
        _tenant(
            "kbase",
            prefix="kbase.",
            display_name="KBase",
            description="Knowledge base for systems biology",
            website="https://kbase.us",
            organization="DOE Systems Biology Knowledgebase",
            stewards=["alice", "bob"],
            members_rw=["alice", "bob", "carol"],
            members_ro=["dan"],
        )
    ]
    out = format_inventory(structure, tenants=tenants, emoji=False)
    assert "**Description:** Knowledge base for systems biology" in out
    assert "**Website:** https://kbase.us" in out
    assert "**Organization:** DOE Systems Biology Knowledgebase" in out
    assert "**Stewards:** alice, bob" in out
    # Without --with-members, only counts are shown.
    assert "3 read-write, 1 read-only" in out
    assert "alice, bob, carol" not in out  # members not listed by default


def test_format_inventory_with_members_lists_users():
    from scripts.berdl_inventory import format_inventory
    structure = {"kbase.genomes": ["t1"]}
    tenants = [
        _tenant(
            "kbase",
            prefix="kbase.",
            members_rw=["alice", "bob"],
            members_ro=["carol"],
        )
    ]
    out = format_inventory(structure, tenants=tenants, with_members=True, emoji=False)
    assert "Read-write members (2):** alice, bob" in out
    assert "Read-only members (1):** carol" in out


def test_format_inventory_sample_size():
    from scripts.berdl_inventory import format_inventory
    structure = {"kbase.x": ["t1", "t2", "t3", "t4", "t5"]}
    out = format_inventory(structure, sample=2, emoji=False)
    assert "+3 more" in out


def test_format_inventory_emoji_toggle():
    from scripts.berdl_inventory import format_inventory
    out_with = format_inventory({"kbase.x": ["t"]}, emoji=True)
    out_without = format_inventory({"kbase.x": ["t"]}, emoji=False)
    assert "📦" in out_with
    assert "📦" not in out_without


def test_format_inventory_empty_db_section():
    from scripts.berdl_inventory import format_inventory
    out = format_inventory({"kbase.x": []}, emoji=False)
    assert "_(empty or inaccessible)_" in out


def test_format_inventory_omits_tenant_with_no_accessible_dbs():
    """Tenants the user is a member of but has no databases for don't appear in the report.

    The inventory is access-aware: structure (returned by get_db_structure with
    filter_by_namespace=True) only contains accessible databases, so showing a
    tenant section with zero rows would just be visual noise.
    """
    from scripts.berdl_inventory import format_inventory
    tenants = [_tenant("orphan", prefix="orphan.", description="No data here")]
    out = format_inventory({}, tenants=tenants, emoji=False)
    assert "### orphan" not in out
    assert "No data here" not in out
    assert "No accessible databases" in out  # falls through to the empty message


def test_format_inventory_hides_globalusers_databases():
    """globalusers_* databases never appear in the rendered output, even if accessible."""
    from scripts.berdl_inventory import format_inventory
    structure = {
        "kbase.genomes": ["t1"],
        "globalusers.sandbox": ["t1", "t2"],
        "globalusers.test_thing": ["t1"],
    }
    tenants = [
        _tenant("kbase", prefix="kbase."),
        _tenant("globalusers", prefix="globalusers."),
    ]
    out = format_inventory(structure, tenants=tenants, emoji=False)
    assert "kbase.genomes" in out
    assert "globalusers" not in out
    assert "sandbox" not in out
    # Header counts reflect only the visible databases.
    assert "1 databases" in out


def test_format_inventory_lists_other_tenants_without_access():
    """Non-member tenants the user has no access to show up in a brief footer."""
    from scripts.berdl_inventory import format_inventory
    structure = {"kbase.genomes": ["t1"]}
    tenants = [
        _tenant("kbase", prefix="kbase."),
        _tenant("nmdc", prefix="nmdc."),
        _tenant("planetmicrobe", prefix="planetmicrobe."),
    ]
    out = format_inventory(structure, tenants=tenants, emoji=False)
    assert "Other tenants in BERDL (no membership): nmdc, planetmicrobe" in out


def test_format_inventory_other_tenants_excludes_hidden():
    """Hidden tenants (globalusers) don't appear in the 'other tenants' footer."""
    from scripts.berdl_inventory import format_inventory
    structure = {"kbase.genomes": ["t1"]}
    tenants = [
        _tenant("kbase", prefix="kbase."),
        _tenant("globalusers", prefix="globalusers."),
        _tenant("nmdc", prefix="nmdc."),
    ]
    out = format_inventory(structure, tenants=tenants, emoji=False)
    # nmdc is in the footer; globalusers is suppressed entirely.
    assert "Other tenants in BERDL (no membership): nmdc" in out
    assert "globalusers" not in out


def test_format_inventory_separates_member_no_dbs_from_non_member():
    """Member-with-no-databases tenants get their own footer line, separate from non-members."""
    from scripts.berdl_inventory import format_inventory
    structure = {"kbase.genomes": ["t1"]}
    tenants = [
        _tenant("kbase", prefix="kbase."),
        _tenant("microbialdiscoveryforge", prefix="microbialdiscoveryforge.", is_member=True),
        _tenant("nmdc", prefix="nmdc."),
    ]
    out = format_inventory(structure, tenants=tenants, emoji=False)
    assert "Tenants you can access (no databases yet): microbialdiscoveryforge" in out
    assert "Other tenants in BERDL (no membership): nmdc" in out
    # The member-but-no-DBs tenant must NOT be lumped into the non-membership line.
    assert "no membership): microbialdiscoveryforge" not in out
    assert "no membership): nmdc, microbialdiscoveryforge" not in out


def test_format_inventory_no_other_tenants_footer_when_only_user_tenants():
    """When the user has access to every (non-hidden) tenant, no footer line appears."""
    from scripts.berdl_inventory import format_inventory
    structure = {"kbase.genomes": ["t1"]}
    tenants = [_tenant("kbase", prefix="kbase.")]
    out = format_inventory(structure, tenants=tenants, emoji=False)
    assert "Other tenants in BERDL" not in out


def test_format_inventory_no_longer_carries_agent_banner():
    """The full report is written to a file now, so no in-band agent-relay banner.

    The banner moved to format_summary (the stdout output), where it's still
    needed because the agent has to relay the summary verbatim.
    """
    from scripts.berdl_inventory import format_inventory
    out = format_inventory({"kbase.x": ["t1"]}, emoji=False)
    assert "<!-- AGENT:" not in out


def test_format_summary_compact_and_carries_agent_banner():
    """format_summary is short, lists tenants but not per-database tables."""
    from scripts.berdl_inventory import format_summary
    structure = {
        "kbase.genomes": ["feature", "contig"],
        "kbase.ke_pangenome": ["gene"],
        "kescience.fitnessbrowser": ["experiments", "scores", "fit"],
    }
    out = format_summary(structure, emoji=False)
    assert "BERDL Inventory" in out
    assert "2 tenants" in out
    assert "3 databases" in out
    assert "6 tables" in out
    # Tenant rows present
    assert "`kbase`" in out
    assert "`kescience`" in out
    # Per-database rows must NOT appear in the summary
    assert "kbase.genomes" not in out
    assert "kbase.ke_pangenome" not in out
    # Agent banner reminds the LLM to paste the (short) summary verbatim
    assert "<!-- AGENT:" in out


def test_format_summary_includes_full_report_path_when_provided():
    from scripts.berdl_inventory import format_summary
    out = format_summary(
        {"kbase.x": ["t"]},
        emoji=False,
        full_report_path="data/berdl_inventory.md",
    )
    assert "`data/berdl_inventory.md`" in out
    assert "Full report" in out


def test_format_summary_omits_path_line_when_no_path():
    from scripts.berdl_inventory import format_summary
    out = format_summary({"kbase.x": ["t"]}, emoji=False)
    assert "Full report" not in out


def test_format_summary_empty_message():
    from scripts.berdl_inventory import format_summary
    assert "No accessible databases" in format_summary({})


def test_format_summary_uses_display_name_when_available():
    from scripts.berdl_inventory import format_summary
    structure = {"kbase.genomes": ["t1"]}
    tenants = [_tenant("kbase", prefix="kbase.", display_name="KBase")]
    out = format_summary(structure, tenants=tenants, emoji=False)
    assert "| `kbase` | KBase |" in out


def test_format_summary_stays_compact():
    """Sanity: the summary for a typical 5-tenant inventory stays under ~30 lines.

    The whole point of the summary is that it survives the Claude Code UI's
    long-bash-output collapse. If this grows materially, revisit the design.
    """
    from scripts.berdl_inventory import format_summary
    structure = {
        f"tenant{i}.db{j}": [f"t{k}" for k in range(50)]
        for i in range(5)
        for j in range(4)
    }
    out = format_summary(
        structure, full_report_path="data/berdl_inventory.md", emoji=False
    )
    assert out.count("\n") < 30


def test_main_off_cluster_writes_file_and_prints_summary(tmp_path, capsys):
    fake = {"kbase.x": ["t1", "t2"]}
    out_path = tmp_path / "inventory.md"
    with patch("scripts.berdl_inventory.fetch_off_cluster", return_value=fake):
        from scripts.berdl_inventory import main
        rc = main(["--off-cluster", "--no-emoji", "--output", str(out_path)])
        out = capsys.readouterr().out
        assert rc == 0
        # Stdout: compact summary with tenant key, NOT per-database row
        assert "`kbase`" in out
        assert "kbase.x" not in out
        # File: the full report, including per-database row
        assert out_path.exists()
        file_content = out_path.read_text()
        assert "kbase.x" in file_content


def test_main_full_flag_prints_full_report(tmp_path, capsys):
    fake = {"kbase.x": ["t1", "t2"]}
    out_path = tmp_path / "inventory.md"
    with patch("scripts.berdl_inventory.fetch_off_cluster", return_value=fake):
        from scripts.berdl_inventory import main
        rc = main(
            ["--off-cluster", "--no-emoji", "--full", "--output", str(out_path)]
        )
        out = capsys.readouterr().out
        assert rc == 0
        # --full puts the per-database row on stdout
        assert "kbase.x" in out
        # File is still written
        assert out_path.exists()


def test_main_no_file_skips_write(tmp_path, capsys):
    fake = {"kbase.x": ["t1"]}
    out_path = tmp_path / "inventory.md"
    with patch("scripts.berdl_inventory.fetch_off_cluster", return_value=fake):
        from scripts.berdl_inventory import main
        rc = main(
            ["--off-cluster", "--no-emoji", "--no-file", "--output", str(out_path)]
        )
        out = capsys.readouterr().out
        assert rc == 0
        assert not out_path.exists()
        # Without --full, summary still goes to stdout (no per-database row)
        assert "`kbase`" in out
        assert "kbase.x" not in out


def test_main_falls_back_to_off_cluster_on_import_error(tmp_path, capsys):
    fake = {"kbase.x": ["t1"]}
    out_path = tmp_path / "inventory.md"
    with patch(
        "scripts.berdl_inventory.fetch_structure_on_cluster",
        side_effect=ImportError("no helper"),
    ), patch("scripts.berdl_inventory._is_on_cluster", return_value=False), patch(
        "scripts.berdl_inventory.fetch_off_cluster", return_value=fake,
    ):
        from scripts.berdl_inventory import main
        rc = main(["--no-emoji", "--output", str(out_path)])
        assert rc == 0
        out = capsys.readouterr().out
        # Summary mentions the tenant grouping; full per-db detail goes to the file.
        assert "`kbase`" in out
        assert out_path.exists()


def test_main_detects_uv_run_on_cluster_and_errors_clearly(capsys):
    """If on-cluster but berdl_notebook_utils isn't importable (uv run case), error clearly."""
    with patch(
        "scripts.berdl_inventory.fetch_structure_on_cluster",
        side_effect=ImportError("No module named 'berdl_notebook_utils'"),
    ), patch("scripts.berdl_inventory._is_on_cluster", return_value=True), patch(
        "scripts.berdl_inventory.fetch_off_cluster",
    ) as off_cluster:
        from scripts.berdl_inventory import main
        rc = main([])
        err = capsys.readouterr().err
        assert rc == 2
        assert "uv run" in err
        assert "python scripts/berdl_inventory.py" in err
        # Critical: must NOT have fallen through to the off-cluster path.
        off_cluster.assert_not_called()


def test_main_falls_back_off_cluster_when_truly_off_cluster(capsys):
    """ImportError off-cluster (no berdl_notebook_utils locally) is the normal fallback path."""
    fake = {"kbase.x": ["t1"]}
    with patch(
        "scripts.berdl_inventory.fetch_structure_on_cluster",
        side_effect=ImportError("No module named 'berdl_notebook_utils'"),
    ), patch("scripts.berdl_inventory._is_on_cluster", return_value=False), patch(
        "scripts.berdl_inventory.fetch_off_cluster", return_value=fake,
    ):
        from scripts.berdl_inventory import main
        # --full + --no-file so we get the per-database row on stdout without
        # writing to the real repo.
        rc = main(["--no-emoji", "--full", "--no-file"])
        assert rc == 0
        assert "kbase.x" in capsys.readouterr().out


def test_main_returns_nonzero_when_both_paths_fail(capsys):
    with patch(
        "scripts.berdl_inventory.fetch_structure_on_cluster",
        side_effect=ImportError("no helper"),
    ), patch("scripts.berdl_inventory._is_on_cluster", return_value=False), patch(
        "scripts.berdl_inventory.fetch_off_cluster", side_effect=RuntimeError("auth"),
    ):
        from scripts.berdl_inventory import main
        rc = main([])
        assert rc == 1
        assert "Failed to fetch inventory" in capsys.readouterr().err


def test_main_passes_tenants_through_to_formatter(capsys):
    """When on-cluster, tenants metadata is fetched and passed through to both renderers."""
    fake_structure = {"kbase.genomes": ["t1"]}
    fake_tenants = [
        _tenant("kbase", prefix="kbase.", display_name="KBase", description="Test desc")
    ]
    with patch(
        "scripts.berdl_inventory.fetch_structure_on_cluster", return_value=fake_structure
    ), patch(
        "scripts.berdl_inventory.fetch_tenants_on_cluster", return_value=fake_tenants
    ), patch("scripts.berdl_inventory._is_on_cluster", return_value=False):
        from scripts.berdl_inventory import main
        # --full + --no-file: full report on stdout, no file write.
        rc = main(["--no-emoji", "--full", "--no-file"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "### kbase — KBase" in out
        assert "Test desc" in out


def test_main_default_output_path_resolves_under_repo_root():
    """Sanity check that the default output path lives at <repo>/data/berdl_inventory.md."""
    from scripts.berdl_inventory import _DEFAULT_OUTPUT, _REPO_ROOT
    assert _DEFAULT_OUTPUT == _REPO_ROOT / "data" / "berdl_inventory.md"


# --- Inventory caching (Tasks 1-6) -----------------------------------------


def test_token_fingerprint_hashes_env_token(monkeypatch):
    from scripts.berdl_inventory import _token_fingerprint
    monkeypatch.setenv("KBASE_AUTH_TOKEN", "secret-abc")
    fp = _token_fingerprint()
    assert fp.startswith("sha256:")
    assert "secret-abc" not in fp
    assert len(fp) == len("sha256:") + 12
    assert _token_fingerprint() == fp


def test_token_fingerprint_sentinel_when_unset(monkeypatch):
    from scripts.berdl_inventory import _token_fingerprint
    monkeypatch.delenv("KBASE_AUTH_TOKEN", raising=False)
    assert _token_fingerprint() == "sha256:none"


def test_now_is_timezone_aware():
    from scripts.berdl_inventory import _now
    assert _now().tzinfo is not None


def test_cache_round_trip_preserves_structure_and_tenants(tmp_path):
    from datetime import datetime, timezone
    from scripts.berdl_inventory import CacheEntry, write_cache, load_cache, TenantInfo
    path = tmp_path / "cache.json"
    entry = CacheEntry(
        environment="off-cluster",
        token_fp="sha256:abc123abc123",
        fetched_at=datetime(2026, 7, 5, 14, 22, 7, tzinfo=timezone.utc),
        structure={"kbase.genomes": ["t1", "t2"]},
        tenants=[TenantInfo(name="kbase", display_name="KBase", stewards=["u1"])],
    )
    write_cache(path, entry)
    loaded = load_cache(path)
    assert loaded.environment == "off-cluster"
    assert loaded.token_fp == "sha256:abc123abc123"
    assert loaded.fetched_at == entry.fetched_at
    assert loaded.structure == {"kbase.genomes": ["t1", "t2"]}
    assert loaded.tenants[0].name == "kbase"
    assert loaded.tenants[0].display_name == "KBase"
    assert loaded.tenants[0].stewards == ["u1"]


def test_cache_write_does_not_store_raw_token(tmp_path):
    from datetime import datetime, timezone
    from scripts.berdl_inventory import CacheEntry, write_cache
    path = tmp_path / "cache.json"
    write_cache(path, CacheEntry("off-cluster", "sha256:deadbeefdead",
                                 datetime(2026, 1, 1, tzinfo=timezone.utc), {}, []))
    assert "deadbeef" in path.read_text()
    assert "KBASE_AUTH_TOKEN" not in path.read_text()


def test_load_cache_returns_none_on_missing_file(tmp_path):
    from scripts.berdl_inventory import load_cache
    assert load_cache(tmp_path / "nope.json") is None


def test_load_cache_returns_none_on_corrupt_json(tmp_path):
    from scripts.berdl_inventory import load_cache
    path = tmp_path / "cache.json"
    path.write_text("{ this is not json")
    assert load_cache(path) is None


def test_load_cache_returns_none_on_missing_keys(tmp_path):
    from scripts.berdl_inventory import load_cache
    path = tmp_path / "cache.json"
    path.write_text('{"meta": {}, "structure": {}}')
    assert load_cache(path) is None


def _entry(environment="off-cluster", token_fp="sha256:aaa", fetched_at=None):
    from datetime import datetime, timezone
    from scripts.berdl_inventory import CacheEntry
    return CacheEntry(environment, token_fp,
                      fetched_at or datetime(2026, 7, 1, tzinfo=timezone.utc), {}, [])


def test_cache_fresh_when_recent_and_matching():
    from datetime import datetime, timezone
    from scripts.berdl_inventory import _cache_is_fresh
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    assert _cache_is_fresh(_entry(), "off-cluster", "sha256:aaa", 7, now) is True


def test_cache_stale_when_older_than_ttl():
    from datetime import datetime, timezone
    from scripts.berdl_inventory import _cache_is_fresh
    now = datetime(2026, 7, 10, tzinfo=timezone.utc)
    assert _cache_is_fresh(_entry(), "off-cluster", "sha256:aaa", 7, now) is False


def test_cache_miss_on_environment_mismatch():
    from datetime import datetime, timezone
    from scripts.berdl_inventory import _cache_is_fresh
    now = datetime(2026, 7, 2, tzinfo=timezone.utc)
    assert _cache_is_fresh(_entry(environment="on-cluster"),
                           "off-cluster", "sha256:aaa", 7, now) is False


def test_cache_miss_on_token_mismatch():
    from datetime import datetime, timezone
    from scripts.berdl_inventory import _cache_is_fresh
    now = datetime(2026, 7, 2, tzinfo=timezone.utc)
    assert _cache_is_fresh(_entry(token_fp="sha256:bbb"),
                           "off-cluster", "sha256:aaa", 7, now) is False


def test_format_age_units():
    from datetime import timedelta
    from scripts.berdl_inventory import _format_age
    assert _format_age(timedelta(minutes=5)) == "5 minutes ago"
    assert _format_age(timedelta(minutes=1)) == "1 minute ago"
    assert _format_age(timedelta(hours=3)) == "3 hours ago"
    assert _format_age(timedelta(days=1)) == "1 day ago"
    assert _format_age(timedelta(days=3, hours=4)) == "3 days ago"
    assert _format_age(timedelta(seconds=10)) == "1 minute ago"


def test_banner_cache_hit_mentions_age_env_and_refresh():
    from datetime import datetime, timezone
    from scripts.berdl_inventory import _banner
    fetched = datetime(2026, 7, 2, 14, 22, tzinfo=timezone.utc)
    now = datetime(2026, 7, 5, 14, 22, tzinfo=timezone.utc)
    b = _banner("cache", "off-cluster", fetched, now, emoji=True)
    assert "Cached 3 days ago" in b
    assert "off-cluster" in b
    assert "--refresh" in b
    assert "2026-07-02 14:22 UTC" in b
    assert b.startswith("_\U0001F4E6")


def test_banner_expired_and_first_run():
    from datetime import datetime, timezone
    from scripts.berdl_inventory import _banner
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    expired = _banner("expired", "on-cluster", None, now, emoji=True)
    first = _banner("first", "on-cluster", None, now, emoji=True)
    assert "cache expired" in expired and "on-cluster" in expired
    assert "first run" in first and "on-cluster" in first


def test_banner_no_emoji_drops_glyph():
    from datetime import datetime, timezone
    from scripts.berdl_inventory import _banner
    fetched = datetime(2026, 7, 2, tzinfo=timezone.utc)
    now = datetime(2026, 7, 3, tzinfo=timezone.utc)
    b = _banner("cache", "off-cluster", fetched, now, emoji=False)
    assert "\U0001F4E6" not in b
    assert b.startswith("_Cached")


def test_parse_args_cache_flag_defaults():
    from scripts.berdl_inventory import parse_args, _DEFAULT_CACHE
    ns = parse_args([])
    assert ns.refresh is False
    assert ns.no_cache is False
    assert ns.ttl_days is None
    assert ns.cache_path == _DEFAULT_CACHE


def test_parse_args_cache_flags_set():
    from pathlib import Path
    from scripts.berdl_inventory import parse_args
    ns = parse_args(["--refresh", "--no-cache", "--ttl-days", "3",
                     "--cache-path", "/tmp/c.json"])
    assert ns.refresh is True
    assert ns.no_cache is True
    assert ns.ttl_days == 3
    assert ns.cache_path == Path("/tmp/c.json")


def test_main_cache_hit_skips_fetch(tmp_path, capsys, monkeypatch):
    from datetime import datetime, timezone
    from scripts.berdl_inventory import main, CacheEntry, write_cache, TenantInfo
    import scripts.berdl_inventory as mod

    cache = tmp_path / "cache.json"
    out = tmp_path / "inv.md"
    monkeypatch.setenv("KBASE_AUTH_TOKEN", "tok")
    monkeypatch.setattr(mod, "_now",
                        lambda: datetime(2026, 7, 3, tzinfo=timezone.utc))
    write_cache(cache, CacheEntry(
        environment="off-cluster", token_fp=mod._token_fingerprint(),
        fetched_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        structure={"kbase.genomes": ["g1"]}, tenants=[TenantInfo(name="kbase")]))

    def boom():
        raise AssertionError("fetch should not be called on a cache hit")
    monkeypatch.setattr(mod, "fetch_off_cluster", boom)

    rc = main(["--off-cluster", "--no-emoji", "--cache-path", str(cache),
               "--output", str(out)])
    assert rc == 0
    printed = capsys.readouterr().out
    assert "Cached 2 days ago" in printed
    assert "Cached 2 days ago" in out.read_text()


def test_main_cache_miss_expired_refetches_and_rewrites(tmp_path, capsys, monkeypatch):
    from datetime import datetime, timezone
    from scripts.berdl_inventory import main, CacheEntry, write_cache, load_cache
    import scripts.berdl_inventory as mod

    cache = tmp_path / "cache.json"
    out = tmp_path / "inv.md"
    monkeypatch.setenv("KBASE_AUTH_TOKEN", "tok")
    monkeypatch.setattr(mod, "_now",
                        lambda: datetime(2026, 7, 20, tzinfo=timezone.utc))
    write_cache(cache, CacheEntry(
        environment="off-cluster", token_fp=mod._token_fingerprint(),
        fetched_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        structure={"old.db": ["x"]}, tenants=[]))

    monkeypatch.setattr(mod, "fetch_off_cluster",
                        lambda: {"kbase.new": ["fresh1"]})
    rc = main(["--off-cluster", "--no-emoji", "--cache-path", str(cache),
               "--output", str(out)])
    assert rc == 0
    assert "cache expired, refetched just now" in capsys.readouterr().out
    reloaded = load_cache(cache)
    assert reloaded.structure == {"kbase.new": ["fresh1"]}
    assert reloaded.fetched_at == datetime(2026, 7, 20, tzinfo=timezone.utc)


def test_main_first_run_writes_cache(tmp_path, capsys, monkeypatch):
    from datetime import datetime, timezone
    from scripts.berdl_inventory import main, load_cache
    import scripts.berdl_inventory as mod
    cache = tmp_path / "cache.json"
    out = tmp_path / "inv.md"
    monkeypatch.setenv("KBASE_AUTH_TOKEN", "tok")
    monkeypatch.setattr(mod, "_now", lambda: datetime(2026, 7, 5, tzinfo=timezone.utc))
    monkeypatch.setattr(mod, "fetch_off_cluster", lambda: {"kbase.x": ["t1"]})
    rc = main(["--off-cluster", "--no-emoji", "--cache-path", str(cache),
               "--output", str(out)])
    assert rc == 0
    assert "first run" in capsys.readouterr().out
    assert load_cache(cache).structure == {"kbase.x": ["t1"]}


def test_main_refresh_forces_fetch_over_fresh_cache(tmp_path, capsys, monkeypatch):
    from datetime import datetime, timezone
    from scripts.berdl_inventory import main, CacheEntry, write_cache, TenantInfo
    import scripts.berdl_inventory as mod
    cache = tmp_path / "cache.json"
    out = tmp_path / "inv.md"
    monkeypatch.setenv("KBASE_AUTH_TOKEN", "tok")
    monkeypatch.setattr(mod, "_now", lambda: datetime(2026, 7, 2, tzinfo=timezone.utc))
    write_cache(cache, CacheEntry(
        environment="off-cluster", token_fp=mod._token_fingerprint(),
        fetched_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        structure={"stale.db": ["x"]}, tenants=[TenantInfo(name="kbase")]))
    called = {"n": 0}
    def fetch():
        called["n"] += 1
        return {"kbase.fresh": ["y"]}
    monkeypatch.setattr(mod, "fetch_off_cluster", fetch)
    rc = main(["--off-cluster", "--no-emoji", "--refresh",
               "--cache-path", str(cache), "--output", str(out)])
    assert rc == 0
    assert called["n"] == 1
    assert "kbase.fresh" in out.read_text()


def test_main_no_cache_neither_reads_nor_writes(tmp_path, capsys, monkeypatch):
    from datetime import datetime, timezone
    from scripts.berdl_inventory import main
    import scripts.berdl_inventory as mod
    cache = tmp_path / "cache.json"
    out = tmp_path / "inv.md"
    monkeypatch.setenv("KBASE_AUTH_TOKEN", "tok")
    monkeypatch.setattr(mod, "_now", lambda: datetime(2026, 7, 5, tzinfo=timezone.utc))
    monkeypatch.setattr(mod, "fetch_off_cluster", lambda: {"kbase.x": ["t1"]})
    rc = main(["--off-cluster", "--no-emoji", "--no-cache",
               "--cache-path", str(cache), "--output", str(out)])
    assert rc == 0
    assert not cache.exists()


def test_main_ttl_days_flag_controls_freshness(tmp_path, capsys, monkeypatch):
    from datetime import datetime, timezone
    from scripts.berdl_inventory import main, CacheEntry, write_cache
    import scripts.berdl_inventory as mod
    cache = tmp_path / "cache.json"
    out = tmp_path / "inv.md"
    monkeypatch.setenv("KBASE_AUTH_TOKEN", "tok")
    monkeypatch.setattr(mod, "_now", lambda: datetime(2026, 7, 6, tzinfo=timezone.utc))
    write_cache(cache, CacheEntry(
        environment="off-cluster", token_fp=mod._token_fingerprint(),
        fetched_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        structure={"stale.db": ["x"]}, tenants=[]))
    monkeypatch.setattr(mod, "fetch_off_cluster", lambda: {"kbase.fresh": ["y"]})
    rc = main(["--off-cluster", "--no-emoji", "--ttl-days", "3",
               "--cache-path", str(cache), "--output", str(out)])
    assert rc == 0
    assert "kbase.fresh" in out.read_text()


# --- degraded (partial) fetches must never be cached -------------------------


def _write_fresh_cache(mod, cache, structure, when):
    from scripts.berdl_inventory import CacheEntry, write_cache
    write_cache(cache, CacheEntry(
        environment="off-cluster", token_fp=mod._token_fingerprint(),
        fetched_at=when, structure=structure, tenants=[]))


def test_watch_fetch_failures_flags_upstream_listing_warning(capsys):
    import logging
    from scripts.berdl_inventory import _watch_fetch_failures

    with _watch_fetch_failures() as watcher:
        assert watcher.degraded is False
        logging.getLogger("berdl_notebook_utils.spark.data_store").warning(
            "Failed to list tables in 'planetmicrobe.x': UNAUTHENTICATED"
        )
    assert watcher.degraded is True
    assert "UNAUTHENTICATED" in capsys.readouterr().err


def test_watch_fetch_failures_detaches_handler_after_exit():
    import logging
    from scripts.berdl_inventory import _watch_fetch_failures
    lg = logging.getLogger("berdl_notebook_utils")
    before = list(lg.handlers)
    with _watch_fetch_failures():
        assert len(lg.handlers) == len(before) + 1
    assert list(lg.handlers) == before


def test_main_partial_fetch_is_not_cached(tmp_path, capsys, monkeypatch):
    from datetime import datetime, timezone
    from scripts.berdl_inventory import main
    import scripts.berdl_inventory as mod

    cache = tmp_path / "cache.json"
    monkeypatch.setenv("KBASE_AUTH_TOKEN", "tok")
    monkeypatch.setattr(mod, "_now", lambda: datetime(2026, 7, 5, tzinfo=timezone.utc))

    def lossy_fetch():
        # Mirrors berdl_notebook_utils.get_tables(): log and return [].
        mod.structure_logger.warning("could not list tables for kbase.lost: UNAUTHENTICATED")
        return {"kbase.kept": ["t1"], "kbase.lost": []}

    monkeypatch.setattr(mod, "fetch_off_cluster", lossy_fetch)
    rc = main(["--off-cluster", "--no-emoji", "--no-file", "--cache-path", str(cache)])
    assert rc == 0
    assert not cache.exists(), "a partial inventory must never be cached"
    captured = capsys.readouterr()
    assert "not caching this partial inventory" in captured.err
    assert "partial" in captured.out


def test_main_partial_fetch_preserves_existing_good_cache(tmp_path, capsys, monkeypatch):
    from datetime import datetime, timezone
    from scripts.berdl_inventory import main, load_cache
    import scripts.berdl_inventory as mod

    cache = tmp_path / "cache.json"
    monkeypatch.setenv("KBASE_AUTH_TOKEN", "tok")
    monkeypatch.setattr(mod, "_now", lambda: datetime(2026, 7, 20, tzinfo=timezone.utc))
    # Expired, but complete.
    _write_fresh_cache(mod, cache, {"kbase.good": ["a", "b"]},
                       datetime(2026, 7, 1, tzinfo=timezone.utc))

    def lossy_fetch():
        mod.structure_logger.warning("could not list tables for kbase.good: UNAUTHENTICATED")
        return {"kbase.good": []}

    monkeypatch.setattr(mod, "fetch_off_cluster", lossy_fetch)
    rc = main(["--off-cluster", "--no-emoji", "--no-file", "--cache-path", str(cache)])
    assert rc == 0
    # The good snapshot survives; the lossy one did not overwrite it.
    assert load_cache(cache).structure == {"kbase.good": ["a", "b"]}


def test_main_clean_fetch_still_caches(tmp_path, capsys, monkeypatch):
    from datetime import datetime, timezone
    from scripts.berdl_inventory import main, load_cache
    import scripts.berdl_inventory as mod
    cache = tmp_path / "cache.json"
    monkeypatch.setenv("KBASE_AUTH_TOKEN", "tok")
    monkeypatch.setattr(mod, "_now", lambda: datetime(2026, 7, 5, tzinfo=timezone.utc))
    monkeypatch.setattr(mod, "fetch_off_cluster", lambda: {"kbase.x": ["t1"]})
    rc = main(["--off-cluster", "--no-emoji", "--no-file", "--cache-path", str(cache)])
    assert rc == 0
    assert load_cache(cache).structure == {"kbase.x": ["t1"]}


def test_banner_partial_mentions_not_cached():
    from datetime import datetime, timezone
    from scripts.berdl_inventory import _banner
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    b = _banner("partial", "on-cluster", None, now, emoji=False)
    assert "partial" in b and "not cached" in b and "on-cluster" in b


# --- banners no longer mislabel forced fetches as expiry ----------------------


def test_banner_refresh_and_nocache_are_not_labelled_expired():
    from datetime import datetime, timezone
    from scripts.berdl_inventory import _banner
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    refresh = _banner("refresh", "on-cluster", None, now, emoji=False)
    nocache = _banner("nocache", "on-cluster", None, now, emoji=False)
    assert "refreshed just now" in refresh and "expired" not in refresh
    assert "--no-cache" in nocache and "expired" not in nocache


def test_main_refresh_banner_says_refreshed_not_expired(tmp_path, capsys, monkeypatch):
    from datetime import datetime, timezone
    from scripts.berdl_inventory import main
    import scripts.berdl_inventory as mod
    cache = tmp_path / "cache.json"
    monkeypatch.setenv("KBASE_AUTH_TOKEN", "tok")
    monkeypatch.setattr(mod, "_now", lambda: datetime(2026, 7, 2, tzinfo=timezone.utc))
    _write_fresh_cache(mod, cache, {"stale.db": ["x"]},
                       datetime(2026, 7, 1, tzinfo=timezone.utc))
    monkeypatch.setattr(mod, "fetch_off_cluster", lambda: {"kbase.fresh": ["y"]})
    rc = main(["--off-cluster", "--no-emoji", "--refresh", "--no-file",
               "--cache-path", str(cache)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "refreshed just now" in out
    assert "expired" not in out


def test_main_no_cache_banner_says_bypassed(tmp_path, capsys, monkeypatch):
    from datetime import datetime, timezone
    from scripts.berdl_inventory import main
    import scripts.berdl_inventory as mod
    cache = tmp_path / "cache.json"
    monkeypatch.setenv("KBASE_AUTH_TOKEN", "tok")
    monkeypatch.setattr(mod, "_now", lambda: datetime(2026, 7, 2, tzinfo=timezone.utc))
    _write_fresh_cache(mod, cache, {"cached.db": ["x"]},
                       datetime(2026, 7, 1, tzinfo=timezone.utc))
    monkeypatch.setattr(mod, "fetch_off_cluster", lambda: {"kbase.fresh": ["y"]})
    rc = main(["--off-cluster", "--no-emoji", "--no-cache", "--no-file",
               "--cache-path", str(cache)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "cache bypassed" in out
    assert "expired" not in out


# --- malformed TTL env var must not crash the inventory -----------------------


@pytest.mark.parametrize("raw", ["", "   ", "seven", "7d", "3.5"])
def test_resolve_ttl_days_falls_back_on_malformed_env(raw, monkeypatch, capsys):
    from scripts.berdl_inventory import _resolve_ttl_days, _DEFAULT_TTL_DAYS
    monkeypatch.setenv("BERDL_INVENTORY_TTL_DAYS", raw)
    assert _resolve_ttl_days(None) == _DEFAULT_TTL_DAYS


def test_resolve_ttl_days_warns_only_on_unparseable(monkeypatch, capsys):
    from scripts.berdl_inventory import _resolve_ttl_days
    monkeypatch.setenv("BERDL_INVENTORY_TTL_DAYS", "seven")
    _resolve_ttl_days(None)
    assert "ignoring BERDL_INVENTORY_TTL_DAYS" in capsys.readouterr().err
    monkeypatch.setenv("BERDL_INVENTORY_TTL_DAYS", "")
    _resolve_ttl_days(None)
    assert capsys.readouterr().err == ""


def test_resolve_ttl_days_precedence(monkeypatch):
    from scripts.berdl_inventory import _resolve_ttl_days, _DEFAULT_TTL_DAYS
    monkeypatch.setenv("BERDL_INVENTORY_TTL_DAYS", "2")
    assert _resolve_ttl_days(5) == 5      # CLI wins
    assert _resolve_ttl_days(None) == 2   # env next
    monkeypatch.delenv("BERDL_INVENTORY_TTL_DAYS")
    assert _resolve_ttl_days(None) == _DEFAULT_TTL_DAYS


def test_main_survives_malformed_ttl_env(tmp_path, capsys, monkeypatch):
    from datetime import datetime, timezone
    from scripts.berdl_inventory import main
    import scripts.berdl_inventory as mod
    monkeypatch.setenv("KBASE_AUTH_TOKEN", "tok")
    monkeypatch.setenv("BERDL_INVENTORY_TTL_DAYS", "")
    monkeypatch.setattr(mod, "_now", lambda: datetime(2026, 7, 5, tzinfo=timezone.utc))
    monkeypatch.setattr(mod, "fetch_off_cluster", lambda: {"kbase.x": ["t1"]})
    rc = main(["--off-cluster", "--no-emoji", "--no-file",
               "--cache-path", str(tmp_path / "c.json")])
    assert rc == 0


# --- a tz-naive cached timestamp is a miss, not a crash -----------------------


def test_load_cache_returns_none_on_naive_timestamp(tmp_path):
    import json
    from scripts.berdl_inventory import load_cache
    cache = tmp_path / "cache.json"
    cache.write_text(json.dumps({
        "meta": {"environment": "off-cluster", "token_fp": "sha256:abc",
                 "fetched_at": "2026-07-01T00:00:00"},  # no tzinfo
        "structure": {}, "tenants": [],
    }))
    assert load_cache(cache) is None


def test_main_naive_cached_timestamp_refetches_instead_of_crashing(tmp_path, capsys, monkeypatch):
    import json
    from datetime import datetime, timezone
    from scripts.berdl_inventory import main
    import scripts.berdl_inventory as mod
    cache = tmp_path / "cache.json"
    cache.write_text(json.dumps({
        "meta": {"environment": "off-cluster", "token_fp": "sha256:abc",
                 "fetched_at": "2026-07-01T00:00:00"},
        "structure": {"old.db": ["x"]}, "tenants": [],
    }))
    monkeypatch.setenv("KBASE_AUTH_TOKEN", "tok")
    monkeypatch.setattr(mod, "_now", lambda: datetime(2026, 7, 2, tzinfo=timezone.utc))
    monkeypatch.setattr(mod, "fetch_off_cluster", lambda: {"kbase.fresh": ["y"]})
    rc = main(["--off-cluster", "--no-emoji", "--no-file", "--full",
               "--cache-path", str(cache)])
    assert rc == 0
    assert "kbase.fresh" in capsys.readouterr().out


def test_tenant_metadata_warning_does_not_block_caching(tmp_path, capsys, monkeypatch):
    """A failed get_tenant_detail costs a display name, not a database.

    Blocking the cache on it would let one permanently-403ing tenant disable
    caching forever for that user — reinstating the slow startup this fixes.
    """
    from datetime import datetime, timezone
    from scripts.berdl_inventory import main, load_cache
    import scripts.berdl_inventory as mod

    cache = tmp_path / "cache.json"
    monkeypatch.setenv("KBASE_AUTH_TOKEN", "tok")
    monkeypatch.setattr(mod, "_now", lambda: datetime(2026, 7, 5, tzinfo=timezone.utc))

    def fetch_with_tenant_warning():
        mod.logger.warning("get_tenant_detail(enigma) failed: 403 Forbidden")
        return {"kbase.x": ["t1"]}

    monkeypatch.setattr(mod, "fetch_off_cluster", fetch_with_tenant_warning)
    rc = main(["--off-cluster", "--no-emoji", "--no-file", "--cache-path", str(cache)])
    assert rc == 0
    assert load_cache(cache) is not None, "tenant-metadata warnings must not block the cache"
    assert "partial" not in capsys.readouterr().out


def test_structure_logger_is_watched_but_parent_logger_is_not():
    import logging
    from scripts.berdl_inventory import _watch_fetch_failures

    with _watch_fetch_failures() as watcher:
        logging.getLogger("berdl_inventory").warning("tenant metadata hiccup")
        assert watcher.degraded is False, "parent logger must not degrade the fetch"
        logging.getLogger("berdl_inventory.structure").warning("could not list tables")
        assert watcher.degraded is True
