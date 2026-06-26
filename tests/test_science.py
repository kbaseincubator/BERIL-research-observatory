"""Tests for beril_cli.science — pure, model-free calibrated-trust computation.

Ported from the beril-pi-agent reference (lib/science.ts, lib/claim-state.ts).
Confidence and groundedness are computed from artifact strength and rendered as
WORDS only — there is no numeric confidence anywhere.
"""

from __future__ import annotations

from beril_cli.science import (
    claim_id,
    groundedness_for_evidence,
    is_result,
    tier_for_evidence,
    tier_mismatch,
)


def _p(kind: str, locator: str = "") -> dict:
    return {"kind": kind, "locator": locator}


# --- is_result: only query/notebook are re-runnable results ---


def test_is_result_true_for_query_and_notebook():
    assert is_result(_p("query"))
    assert is_result(_p("notebook"))


def test_is_result_false_for_literature_and_figures():
    assert not is_result(_p("paper"))
    assert not is_result(_p("figure"))
    assert not is_result(_p("web"))
    assert not is_result(_p("docs"))


# --- tier_for_evidence: counts re-runnable result POINTERS ---


def test_tier_high_with_two_results():
    assert tier_for_evidence([_p("query", "a"), _p("notebook", "b")]) == "high"


def test_tier_medium_with_one_result_and_a_paper():
    assert tier_for_evidence([_p("query", "a"), _p("paper", "PMID:1")]) == "medium"


def test_tier_low_with_literature_only():
    assert tier_for_evidence([_p("paper", "x"), _p("web", "y")]) == "low"


def test_tier_low_with_no_evidence():
    assert tier_for_evidence([]) == "low"


def test_tier_counts_pointers_not_distinct_sources():
    # Two pointers into the SAME notebook still count as two results for confidence.
    assert tier_for_evidence([_p("notebook", "nb#cell-1"), _p("notebook", "nb#cell-1")]) == "high"


# --- groundedness_for_evidence: counts DISTINCT re-runnable sources ---


def test_groundedness_well_grounded_two_distinct_sources():
    assert groundedness_for_evidence([_p("query", "a"), _p("notebook", "b")]) == "well-grounded"


def test_groundedness_single_source_when_same_locator():
    # Two pointers into the same notebook dedupe to ONE source.
    assert (
        groundedness_for_evidence([_p("notebook", "nb#cell-1"), _p("notebook", "nb#cell-1")])
        == "single-source"
    )


def test_groundedness_dedupes_ignoring_whitespace_and_case():
    assert groundedness_for_evidence([_p("query", "Foo Bar"), _p("query", "foobar")]) == "single-source"


def test_groundedness_ungrounded_with_literature_only():
    assert groundedness_for_evidence([_p("paper", "x")]) == "ungrounded"


def test_groundedness_ignores_result_with_empty_locator():
    assert groundedness_for_evidence([_p("query", "")]) == "ungrounded"


def test_groundedness_tolerates_empty():
    assert groundedness_for_evidence([]) == "ungrounded"


# --- groundedness dedupes at the NOTEBOOK level (the #cell anchor is ignored) ---


def test_groundedness_same_notebook_different_cells_is_single_source():
    # Two cells of the SAME notebook are not independent corroboration -> one source.
    supports = [
        _p("notebook", "notebooks/NB.ipynb#cell-3"),
        _p("notebook", "notebooks/NB.ipynb#cell-7"),
    ]
    assert groundedness_for_evidence(supports) == "single-source"


def test_groundedness_distinct_notebooks_well_grounded():
    supports = [
        _p("notebook", "notebooks/NB03.ipynb#cell-1"),
        _p("notebook", "notebooks/NB04.ipynb#cell-1"),
    ]
    assert groundedness_for_evidence(supports) == "well-grounded"


# --- the calibration signal: high confidence can still be single-source ---


def test_confidence_and_groundedness_diverge_on_same_notebook():
    # Two cells of one notebook: high confidence (2 pointers) but single-source
    # (1 independent notebook) -> tier_mismatch should fire.
    supports = [_p("notebook", "nb.ipynb#cell-1"), _p("notebook", "nb.ipynb#cell-9")]
    assert tier_for_evidence(supports) == "high"
    assert groundedness_for_evidence(supports) == "single-source"
    assert tier_mismatch("high", groundedness_for_evidence(supports)) is True


# --- tier_mismatch: written confidence outruns the evidence ---


def test_tier_mismatch_high_confidence_single_source():
    assert tier_mismatch("high", "single-source") is True


def test_tier_mismatch_medium_confidence_ungrounded():
    assert tier_mismatch("medium", "ungrounded") is True


def test_no_tier_mismatch_when_well_grounded():
    assert tier_mismatch("high", "well-grounded") is False


def test_no_tier_mismatch_for_low_confidence():
    assert tier_mismatch("low", "ungrounded") is False


# --- claim_id: stable slug, trimmed THEN truncated to 56 (matches reference) ---


def test_claim_id_slugifies():
    assert claim_id("Lignin enrichment is higher in soil!") == "lignin-enrichment-is-higher-in-soil"


def test_claim_id_truncates_to_56():
    assert claim_id("a" * 100) == "a" * 56


def test_claim_id_empty_falls_back_to_claim():
    assert claim_id("!!!") == "claim"


# --- status_from: leftmost (text-order) match, like confidence_from ---


def test_status_from_reads_written_value_not_enum_order():
    from beril_cli.science import status_from

    # A status line that lists the other options in a trailing comment must parse
    # to the WRITTEN value (leftmost), not the first enum member that appears.
    assert status_from("supported   # supported | open | refuted | blocked") == "supported"


def test_status_from_returns_leftmost():
    from beril_cli.science import status_from

    assert status_from("refuted then open") == "refuted"


# --- never-throws contract holds for malformed (non-dict) evidence ---


def test_is_result_tolerates_non_dict():
    assert is_result("notadict") is False


def test_tier_tolerates_non_dict_elements():
    assert tier_for_evidence(["notadict", _p("query", "a")]) == "medium"


def test_groundedness_tolerates_non_dict_elements():
    assert groundedness_for_evidence(["notadict", _p("query", "a")]) == "single-source"
