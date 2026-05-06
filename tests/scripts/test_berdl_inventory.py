"""Tests for scripts/berdl_inventory.py."""
from __future__ import annotations

from unittest.mock import patch

import pytest


def test_split_tenant_with_underscore():
    from scripts.berdl_inventory import _split_tenant
    assert _split_tenant("kbase_ke_pangenome") == "kbase"
    assert _split_tenant("kescience_fitnessbrowser") == "kescience"


def test_split_tenant_no_underscore():
    from scripts.berdl_inventory import _split_tenant
    assert _split_tenant("noprefix") == "(other)"


def test_format_inventory_empty():
    from scripts.berdl_inventory import format_inventory
    out = format_inventory({})
    assert "No accessible databases" in out


def test_format_inventory_groups_by_tenant():
    from scripts.berdl_inventory import format_inventory
    structure = {
        "kbase_genomes": ["feature", "contig", "protein", "extra1", "extra2"],
        "kbase_ke_pangenome": ["gene", "gene_cluster"],
        "kescience_fitnessbrowser": ["experiments", "scores"],
    }
    out = format_inventory(structure, sample=3, emoji=False)
    # Header line counts
    assert "3 tenants" not in out  # only 2 tenants present
    assert "2 tenants" in out
    assert "3 databases" in out
    assert "9 tables" in out
    # Per-tenant H3 sections
    assert "### kbase" in out
    assert "### kescience" in out
    # Database rows with backticks
    assert "`kbase_genomes`" in out
    assert "`kescience_fitnessbrowser`" in out
    # Sample names truncated with "+N more"
    assert "+2 more" in out  # kbase_genomes had 5 tables, sample=3 → 2 hidden


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
    """A database with zero tables shows an explicit marker."""
    from scripts.berdl_inventory import format_inventory
    out = format_inventory({"kbase_x": []}, emoji=False)
    assert "_(empty or inaccessible)_" in out


def test_main_off_cluster_exits_zero(capsys):
    """When --off-cluster forces the off-cluster path and it succeeds, exit 0."""
    fake = {"kbase_x": ["t1", "t2"]}
    with patch("scripts.berdl_inventory.fetch_off_cluster", return_value=fake):
        from scripts.berdl_inventory import main
        rc = main(["--off-cluster", "--no-emoji"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "kbase_x" in out
        assert "1 tenants · 1 databases · 2 tables" in out


def test_main_falls_back_to_off_cluster_on_import_error(capsys):
    """If on-cluster import fails, main() falls back to off-cluster."""
    fake = {"kbase_x": ["t1"]}
    with patch(
        "scripts.berdl_inventory.fetch_on_cluster", side_effect=ImportError("no helper")
    ), patch("scripts.berdl_inventory.fetch_off_cluster", return_value=fake):
        from scripts.berdl_inventory import main
        rc = main(["--no-emoji"])
        assert rc == 0
        assert "kbase_x" in capsys.readouterr().out


def test_main_returns_nonzero_when_both_paths_fail(capsys):
    with patch(
        "scripts.berdl_inventory.fetch_on_cluster", side_effect=ImportError("no helper")
    ), patch(
        "scripts.berdl_inventory.fetch_off_cluster", side_effect=RuntimeError("auth")
    ):
        from scripts.berdl_inventory import main
        rc = main([])
        assert rc == 1
        assert "Failed to fetch inventory" in capsys.readouterr().err
