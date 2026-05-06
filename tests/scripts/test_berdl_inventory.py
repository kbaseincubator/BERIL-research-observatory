"""Tests for scripts/berdl_inventory.py."""
from __future__ import annotations

from unittest.mock import patch


def _tenant(name, prefix="", **kwargs):
    from scripts.berdl_inventory import TenantInfo
    return TenantInfo(name=name, namespace_prefix=prefix, **kwargs)


def test_split_tenant_prefix_with_underscore():
    from scripts.berdl_inventory import _split_tenant_prefix
    assert _split_tenant_prefix("kbase_ke_pangenome") == "kbase"
    assert _split_tenant_prefix("kescience_fitnessbrowser") == "kescience"


def test_split_tenant_prefix_no_underscore():
    from scripts.berdl_inventory import _split_tenant_prefix
    assert _split_tenant_prefix("noprefix") == "(other)"


def test_format_inventory_empty():
    from scripts.berdl_inventory import format_inventory
    assert "No accessible databases" in format_inventory({})


def test_format_inventory_groups_by_tenant_no_metadata():
    from scripts.berdl_inventory import format_inventory
    structure = {
        "kbase_genomes": ["feature", "contig", "protein", "extra1", "extra2"],
        "kbase_ke_pangenome": ["gene", "gene_cluster"],
        "kescience_fitnessbrowser": ["experiments", "scores"],
    }
    out = format_inventory(structure, sample=3, emoji=False)
    assert "2 tenants" in out
    assert "3 databases" in out
    assert "9 tables" in out
    assert "### kbase" in out
    assert "### kescience" in out
    assert "`kbase_genomes`" in out
    assert "+2 more" in out  # 5 tables, sample=3 → 2 hidden


def test_format_inventory_uses_namespace_prefix():
    """When tenant metadata supplies namespace_prefix, use it instead of underscore split."""
    from scripts.berdl_inventory import format_inventory
    structure = {
        "kbase_dev_thing": ["t1"],
        "kbase_genomes": ["t1", "t2"],
    }
    # Two tenants share the 'kbase' underscore prefix; the dev one has a longer
    # namespace prefix that should win for kbase_dev_thing.
    tenants = [
        _tenant("kbase", prefix="kbase_", display_name="KBase"),
        _tenant("kbase_dev", prefix="kbase_dev_", display_name="KBase Dev"),
    ]
    out = format_inventory(structure, tenants=tenants, sample=3, emoji=False)
    # Section headers use the full tenant name, with display name when distinct.
    assert "### kbase — KBase" in out
    assert "### kbase_dev — KBase Dev" in out
    # kbase_dev_thing should be under the kbase_dev section, not kbase.
    kbase_section = out.split("### kbase — KBase")[1].split("###")[0]
    kbase_dev_section = out.split("### kbase_dev — KBase Dev")[1].split("> Run")[0]
    assert "kbase_genomes" in kbase_section
    assert "kbase_dev_thing" in kbase_dev_section
    assert "kbase_dev_thing" not in kbase_section


def test_format_inventory_renders_tenant_metadata():
    from scripts.berdl_inventory import format_inventory
    structure = {"kbase_genomes": ["t1"]}
    tenants = [
        _tenant(
            "kbase",
            prefix="kbase_",
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
    structure = {"kbase_genomes": ["t1"]}
    tenants = [
        _tenant(
            "kbase",
            prefix="kbase_",
            members_rw=["alice", "bob"],
            members_ro=["carol"],
        )
    ]
    out = format_inventory(structure, tenants=tenants, with_members=True, emoji=False)
    assert "Read-write members (2):** alice, bob" in out
    assert "Read-only members (1):** carol" in out


def test_format_inventory_sample_size():
    from scripts.berdl_inventory import format_inventory
    structure = {"kbase_x": ["t1", "t2", "t3", "t4", "t5"]}
    out = format_inventory(structure, sample=2, emoji=False)
    assert "+3 more" in out


def test_format_inventory_emoji_toggle():
    from scripts.berdl_inventory import format_inventory
    out_with = format_inventory({"kbase_x": ["t"]}, emoji=True)
    out_without = format_inventory({"kbase_x": ["t"]}, emoji=False)
    assert "📦" in out_with
    assert "📦" not in out_without


def test_format_inventory_empty_db_section():
    from scripts.berdl_inventory import format_inventory
    out = format_inventory({"kbase_x": []}, emoji=False)
    assert "_(empty or inaccessible)_" in out


def test_format_inventory_omits_tenant_with_no_accessible_dbs():
    """Tenants the user is a member of but has no databases for don't appear in the report.

    The inventory is access-aware: structure (returned by get_db_structure with
    filter_by_namespace=True) only contains accessible databases, so showing a
    tenant section with zero rows would just be visual noise.
    """
    from scripts.berdl_inventory import format_inventory
    tenants = [_tenant("orphan", prefix="orphan_", description="No data here")]
    out = format_inventory({}, tenants=tenants, emoji=False)
    assert "### orphan" not in out
    assert "No data here" not in out
    assert "No accessible databases" in out  # falls through to the empty message


def test_format_inventory_hides_globalusers_databases():
    """globalusers_* databases never appear in the rendered output, even if accessible."""
    from scripts.berdl_inventory import format_inventory
    structure = {
        "kbase_genomes": ["t1"],
        "globalusers_sandbox": ["t1", "t2"],
        "globalusers_test_thing": ["t1"],
    }
    tenants = [
        _tenant("kbase", prefix="kbase_"),
        _tenant("globalusers", prefix="globalusers_"),
    ]
    out = format_inventory(structure, tenants=tenants, emoji=False)
    assert "kbase_genomes" in out
    assert "globalusers" not in out
    assert "sandbox" not in out
    # Header counts reflect only the visible databases.
    assert "1 databases" in out


def test_format_inventory_lists_other_tenants_without_access():
    """Tenants the user has no accessible databases in show up in a brief footer."""
    from scripts.berdl_inventory import format_inventory
    structure = {"kbase_genomes": ["t1"]}
    tenants = [
        _tenant("kbase", prefix="kbase_"),
        _tenant("nmdc", prefix="nmdc_"),
        _tenant("planetmicrobe", prefix="planetmicrobe_"),
    ]
    out = format_inventory(structure, tenants=tenants, emoji=False)
    assert "Other tenants in BERDL (no access): nmdc, planetmicrobe" in out


def test_format_inventory_other_tenants_excludes_hidden():
    """Hidden tenants (globalusers) don't appear in the 'other tenants' footer."""
    from scripts.berdl_inventory import format_inventory
    structure = {"kbase_genomes": ["t1"]}
    tenants = [
        _tenant("kbase", prefix="kbase_"),
        _tenant("globalusers", prefix="globalusers_"),
        _tenant("nmdc", prefix="nmdc_"),
    ]
    out = format_inventory(structure, tenants=tenants, emoji=False)
    # nmdc is in the footer; globalusers is suppressed entirely.
    assert "Other tenants in BERDL (no access): nmdc" in out
    assert "globalusers" not in out


def test_format_inventory_no_other_tenants_footer_when_only_user_tenants():
    """When the user has access to every (non-hidden) tenant, no footer line appears."""
    from scripts.berdl_inventory import format_inventory
    structure = {"kbase_genomes": ["t1"]}
    tenants = [_tenant("kbase", prefix="kbase_")]
    out = format_inventory(structure, tenants=tenants, emoji=False)
    assert "Other tenants in BERDL" not in out


def test_format_inventory_includes_agent_relay_banner():
    """The output ends with an HTML-comment instruction telling the agent to relay verbatim.

    This is a backstop against the Claude Code UI collapsing long bash output —
    the agent reading the bash result sees the comment and is reminded to surface
    the full report in its chat reply.
    """
    from scripts.berdl_inventory import format_inventory
    out = format_inventory({"kbase_x": ["t1"]}, emoji=False)
    assert "<!-- AGENT:" in out
    assert "Relay this entire markdown report verbatim" in out
    assert "Do NOT summarize" in out


def test_main_off_cluster_exits_zero(capsys):
    fake = {"kbase_x": ["t1", "t2"]}
    with patch("scripts.berdl_inventory.fetch_off_cluster", return_value=fake):
        from scripts.berdl_inventory import main
        rc = main(["--off-cluster", "--no-emoji"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "kbase_x" in out


def test_main_falls_back_to_off_cluster_on_import_error(capsys):
    fake = {"kbase_x": ["t1"]}
    with patch(
        "scripts.berdl_inventory.fetch_structure_on_cluster",
        side_effect=ImportError("no helper"),
    ), patch("scripts.berdl_inventory._is_on_cluster", return_value=False), patch(
        "scripts.berdl_inventory.fetch_off_cluster", return_value=fake,
    ):
        from scripts.berdl_inventory import main
        rc = main(["--no-emoji"])
        assert rc == 0
        assert "kbase_x" in capsys.readouterr().out


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
    fake = {"kbase_x": ["t1"]}
    with patch(
        "scripts.berdl_inventory.fetch_structure_on_cluster",
        side_effect=ImportError("No module named 'berdl_notebook_utils'"),
    ), patch("scripts.berdl_inventory._is_on_cluster", return_value=False), patch(
        "scripts.berdl_inventory.fetch_off_cluster", return_value=fake,
    ):
        from scripts.berdl_inventory import main
        rc = main(["--no-emoji"])
        assert rc == 0
        assert "kbase_x" in capsys.readouterr().out


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
    """When on-cluster, tenants metadata is fetched and passed to format_inventory."""
    fake_structure = {"kbase_genomes": ["t1"]}
    fake_tenants = [
        _tenant("kbase", prefix="kbase_", display_name="KBase", description="Test desc")
    ]
    with patch(
        "scripts.berdl_inventory.fetch_structure_on_cluster", return_value=fake_structure
    ), patch(
        "scripts.berdl_inventory.fetch_tenants_on_cluster", return_value=fake_tenants
    ):
        from scripts.berdl_inventory import main
        rc = main(["--no-emoji"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "### kbase — KBase" in out
        assert "Test desc" in out
