"""
gene_list_utils.py
==================
Load and filter the comprehensive evidence-tiered metal-gene list
(curated_mrg_ko_ids_v2.csv, 730 KOs, 24 metals, 5 evidence tiers).

Subset naming conventions
--------------------------
Named subsets (primary, tier*_only, fitness_only, all_non_ambiguous) are defined
on the *evidence_tier* column (source-confidence).  The research plan uses these
for sensitivity comparisons.

Functional-category subsets (resistance, transport, sensing, cofactor, metabolism)
are defined on the *primary_category* column.  These test whether the ecological
signal is driven by a particular biological function.

Metal-specific subsets filter the *metals* column (comma-separated element symbols).
Only metals present in ≥20 KOs are exposed as named subsets; others can be built
with ``get_metal_subset()``.

Usage
-----
>>> from scripts.gene_list_utils import load_gene_list, get_subset, SUBSET_REGISTRY
>>> df = load_gene_list()
>>> primary = get_subset("primary", df)         # 140 KOs (Tier1+Tier2 evidence)
>>> resistance = get_subset("resistance", df)   # primary_category == Resistance
>>> cu_kos = get_metal_subset("Cu", df)         # metals contains Cu
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Set

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = Path(__file__).parent
_DATA = _HERE.parent / "data"
GENE_LIST_CSV = _DATA / "curated_mrg_ko_ids_v2.csv"


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load_gene_list(path: Path | str | None = None) -> pd.DataFrame:
    """Load the gene list CSV and return a clean DataFrame.

    Parameters
    ----------
    path:
        Override the default path (``data/curated_mrg_ko_ids_v2.csv``).

    Returns
    -------
    pd.DataFrame
        All 730 KOs with boolean columns cast correctly.
    """
    csv = Path(path) if path else GENE_LIST_CSV
    df = pd.read_csv(csv)
    bool_cols = ["is_resistance", "is_transport", "is_sensor",
                 "is_cofactor", "is_metabolism", "overlap_flag", "pfam_metal"]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].map({"True": True, "False": False, True: True, False: False})
    return df


# ---------------------------------------------------------------------------
# Named subsets — evidence_tier column
# ---------------------------------------------------------------------------

#: Registry of subset filters keyed by name.
#: Each entry is (description, filter_fn).  Access via ``get_subset()``.
SUBSET_REGISTRY: Dict[str, tuple[str, callable]] = {}

def _register(name: str, description: str):
    """Decorator that registers a subset builder."""
    def _wrap(fn):
        SUBSET_REGISTRY[name] = (description, fn)
        return fn
    return _wrap


@_register("primary", "evidence_tier ∈ {Tier 1, Tier 2}  — 140 KOs; highest-confidence KEGG-supported set")
def _subset_primary(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["evidence_tier"].isin(["Tier 1", "Tier 2"])]


@_register("all_non_ambiguous", "evidence_tier ≠ Tier 3  — excludes KEGG-ambiguous KOs (~444 KOs)")
def _subset_all_non_ambiguous(df: pd.DataFrame) -> pd.DataFrame:
    return df[~df["evidence_tier"].isin(["Tier 3"])]


@_register("tier1_only", "evidence_tier == Tier 1  — 32 KOs; multi-source validated (BacMet2 + FitnessBrowser + clear KEGG def)")
def _subset_tier1_only(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["evidence_tier"] == "Tier 1"]


@_register("tier2_only", "evidence_tier == Tier 2  — 108 KOs; clear KEGG definition, single source")
def _subset_tier2_only(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["evidence_tier"] == "Tier 2"]


@_register("fitness_only", "evidence_tier == Tier 2-Fitness  — 116 KOs; empirically validated cross-species fitness defects, invisible to KEGG modules")
def _subset_fitness_only(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["evidence_tier"] == "Tier 2-Fitness"]


@_register("bacmet_only", "evidence_tier == Tier 3-BacMet  — 188 KOs; BacMet2-only, curated literature but no cross-validation")
def _subset_bacmet_only(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["evidence_tier"] == "Tier 3-BacMet"]


@_register("overlap_excluded", "primary subset minus dual-function KOs (overlap_flag == True)")
def _subset_overlap_excluded(df: pd.DataFrame) -> pd.DataFrame:
    primary = _subset_primary(df)
    return primary[~primary["overlap_flag"]]


# ---------------------------------------------------------------------------
# Functional category subsets — primary_category column
# ---------------------------------------------------------------------------

@_register("resistance", "primary_category == Resistance/Detoxification  — direct efflux, reductases, sequestration")
def _subset_resistance(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["primary_category"] == "Resistance/Detoxification"]


@_register("transport", "primary_category == Transport/Homeostasis  — importers, metallochaperones, ferritins")
def _subset_transport(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["primary_category"] == "Transport/Homeostasis"]


@_register("sensing", "primary_category == Sensing/Regulation  — MerR/Fur/Zur family sensors and two-component systems")
def _subset_sensing(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["primary_category"] == "Sensing/Regulation"]


@_register("cofactor", "primary_category == Cofactor Biosynthesis  — Fe-S cluster, molybdopterin, cobalamin assembly")
def _subset_cofactor(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["primary_category"] == "Cofactor Biosynthesis"]


@_register("metabolism", "primary_category == Metal-dependent Metabolism  — enzymes using metal cofactors for catalysis")
def _subset_metabolism(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["primary_category"] == "Metal-dependent Metabolism"]


# ---------------------------------------------------------------------------
# Functional-tier subsets (tier_1_vs_2 column) — use for functional analyses
# ---------------------------------------------------------------------------

@_register("functional_tier1", "tier_1_vs_2 == Tier 1  (= Resistance/Detoxification; 106 KOs)")
def _subset_functional_tier1(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["tier_1_vs_2"] == "Tier 1"]


@_register("functional_tier2", "tier_1_vs_2 == Tier 2  (= all other functional categories; 322 KOs)")
def _subset_functional_tier2(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["tier_1_vs_2"] == "Tier 2"]


@_register("primary_functional", "tier_1_vs_2 ∈ {Tier 1, Tier 2}  — all functionally assigned KOs (428 KOs)")
def _subset_primary_functional(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["tier_1_vs_2"].isin(["Tier 1", "Tier 2"])]


# ---------------------------------------------------------------------------
# Metal-specific subsets
# ---------------------------------------------------------------------------

def get_metal_subset(symbol: str, df: pd.DataFrame) -> pd.DataFrame:
    """Return KOs where *symbol* appears in the comma-separated ``metals`` column.

    Parameters
    ----------
    symbol:
        Element symbol exactly as stored (e.g., ``"Cu"``, ``"Zn"``).
    df:
        Full gene list DataFrame (from :func:`load_gene_list`).

    Returns
    -------
    pd.DataFrame filtered to KOs associated with that metal.
    """
    mask = df["metals"].fillna("").apply(
        lambda s: symbol in [m.strip() for m in s.split(",") if m.strip()]
    )
    return df[mask]


def list_metals_with_min_kos(df: pd.DataFrame, min_kos: int = 20) -> Dict[str, int]:
    """Return {symbol: count} for metals with ≥ *min_kos* KOs.

    Parameters
    ----------
    df:
        Full gene list DataFrame.
    min_kos:
        Minimum KO count to include (default 20).
    """
    from collections import Counter
    counts: Counter = Counter()
    for row in df["metals"].fillna(""):
        for sym in row.split(","):
            sym = sym.strip()
            if sym:
                counts[sym] += 1
    return {s: n for s, n in sorted(counts.items(), key=lambda x: -x[1]) if n >= min_kos}


# Register metal subsets for metals with ≥20 KOs at import time
def _register_metal_subsets(df: pd.DataFrame) -> None:
    """Dynamically register metal-specific subsets after loading the gene list."""
    for sym, n in list_metals_with_min_kos(df).items():
        key = f"{sym.lower()}_specific"
        if key not in SUBSET_REGISTRY:
            SUBSET_REGISTRY[key] = (
                f"metals contains {sym}  ({n} KOs)",
                lambda d, s=sym: get_metal_subset(s, d),
            )


# ---------------------------------------------------------------------------
# Primary accessor
# ---------------------------------------------------------------------------

def get_subset(name: str, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return a named subset of the gene list.

    Parameters
    ----------
    name:
        Subset key (see ``SUBSET_REGISTRY`` for all names).
    df:
        Gene list DataFrame; if *None*, loaded from the default path.

    Returns
    -------
    pd.DataFrame subset.

    Raises
    ------
    KeyError if *name* is not a known subset.
    """
    if df is None:
        df = load_gene_list()
        _register_metal_subsets(df)
    if name not in SUBSET_REGISTRY:
        raise KeyError(
            f"Unknown subset '{name}'.  Available: {sorted(SUBSET_REGISTRY)}"
        )
    _, fn = SUBSET_REGISTRY[name]
    return fn(df).copy()


def get_ko_set(name: str, df: pd.DataFrame | None = None) -> Set[str]:
    """Return the KO identifiers for a named subset as a frozenset."""
    return set(get_subset(name, df)["KO"].tolist())


def subset_summary(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Print a table of all named subsets with n and description."""
    if df is None:
        df = load_gene_list()
        _register_metal_subsets(df)
    rows = []
    for name, (desc, fn) in sorted(SUBSET_REGISTRY.items()):
        n = len(fn(df))
        rows.append({"subset": name, "n_kos": n, "description": desc})
    return pd.DataFrame(rows).sort_values("n_kos", ascending=False)
