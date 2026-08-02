#!/usr/bin/env python3
"""
PLSDB / NCBI plasmid cross-reference for double-signal resistance KOs.

Tests whether KOs with strong horizontal-transfer signatures (Fritz & Purvis D > 0.2
AND Pagel's λ < 0.3) are enriched in plasmid-borne sequences relative to the
background set of resistance/detoxification KOs.

Three complementary approaches are run, each with known limitations:

  1. PLSDB API (filter_nuccore, AMR gene name filter)
     Limitation: only covers genes in CARD/AMRFinder — biased against unusual
     metal resistance genes (gesA, gesB, nrsD, aoxB) which are not in those DBs.
     Result: confounded by AMR database coverage; enrichment test not valid.

  2. MGnify / geNomad plasmid contigs (via Spark, kescience_mgnify + arkinlab_mobilome)
     Limitation: only 1,053 geNomad-classified plasmid contigs from environmental MAGs;
     mercury/gold/arsenite resistance plasmids are predominantly clinical/industrial.
     Result: null (OR<1) due to environmental bias; enrichment test not valid.

  3. NCBI Entrez plasmid fraction [PREFERRED]
     For each gene: plasmid_frac = n_NCBI_plasmid / n_NCBI_total
     Uses 'plasmid[Filter]' in nuccore — sequence-based, not AMR-database-based.
     Limitation: genes with <50 total NCBI hits are excluded (gesA, gesB, nrsD).
     Result: Mann-Whitney p=0.045 (marginal), driven by merD/merE/iucD.

Outputs
-------
  data/plsdb_resistance_crossref.csv    — per-KO table (all three approaches)
  data/plsdb_enrichment_test.json       — enrichment test results with caveats
"""
import os, sys, json, time
os.environ['OMP_NUM_THREADS'] = '1'

from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, mannwhitneyu

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

D_THRESH   = 0.2
LAM_THRESH = 0.3
MIN_NCBI_N = 50   # minimum NCBI total hits to include in statistical test


# ── 1. Load per-KO phylogenetic signal metrics ────────────────────────────────

def load_kos() -> pd.DataFrame:
    d_df  = pd.read_csv(DATA / 'fritz_purvis_D_genome.csv',
                        usecols=['ko_id', 'gene_name', 'subcategory', 'D'])
    lam_df = pd.read_csv(DATA / 'phylo_d_all_ko.csv',
                         usecols=['ko_id', 'lambda'])
    mrg = d_df.merge(lam_df, on='ko_id')
    mrg['is_resistance'] = mrg['subcategory'].str.contains(
        'Resistance|Detox', case=False, na=False)
    mrg['is_double_signal'] = (mrg['D'] > D_THRESH) & (mrg['lambda'] < LAM_THRESH)
    print(f"Total KOs: {len(mrg)}  Resistance: {mrg['is_resistance'].sum()}"
          f"  Double-signal: {mrg['is_double_signal'].sum()}")
    return mrg


# ── 2. PLSDB API (approach 1) ─────────────────────────────────────────────────

PLSDB_API = 'https://ccb-microbe.cs.uni-saarland.de/plsdb2025/api/'

def query_plsdb_api(kos_df: pd.DataFrame) -> pd.DataFrame:
    """
    Query PLSDB filter_nuccore by AMR gene name.

    Coverage caveat: PLSDB uses CARD/AMRFinder annotations. Unusual metal resistance
    genes (gesA, gesB, nrsD, aoxB, iucD siderophore) are not in those databases and
    return 0, making the enrichment test confounded by database coverage rather than
    true plasmid biology. Results should NOT be used for a statistical enrichment test.
    """
    try:
        import requests
    except ImportError:
        print("  requests not available — skipping PLSDB API")
        kos_df['n_plsdb'] = np.nan
        return kos_df

    print("  Querying PLSDB API (filter_nuccore by gene name) …")
    counts = {}
    for _, row in kos_df.iterrows():
        gene = row['gene_name']
        try:
            r = requests.get(PLSDB_API + 'filter_nuccore',
                             params={'AMR_genes': gene}, timeout=20)
            data = r.json()
            counts[row['ko_id']] = len(data.get('NUCCORE_ACC', []))
        except Exception:
            counts[row['ko_id']] = np.nan
        time.sleep(0.2)

    kos_df = kos_df.copy()
    kos_df['n_plsdb'] = kos_df['ko_id'].map(counts)
    return kos_df


# ── 3. MGnify / geNomad plasmid contigs via Spark (approach 2) ───────────────

def query_mgnify_spark(kos_df: pd.DataFrame) -> pd.DataFrame:
    """
    Count genes on geNomad-classified plasmid contigs in kescience_mgnify.

    Coverage caveat: only 1,053 geNomad plasmid contigs from environmental MGnify MAGs.
    Mercury/gold/arsenite resistance plasmids are predominantly clinical/industrial
    and are absent from this environmental collection. Enrichment test not valid.
    """
    try:
        spark
    except NameError:
        try:
            from berdl_notebook_utils.setup_spark_session import get_spark_session
            spark = get_spark_session()
        except Exception as e:
            print(f"  Spark unavailable: {e}")
            kos_df['n_mgnify_plasmid_genes'] = np.nan
            return kos_df

    ko_list_sql = ', '.join(f"'{k}'" for k in kos_df['ko_id'].tolist())
    try:
        result = spark.sql(f'''
            WITH plasmid_contigs AS (
                SELECT DISTINCT seq_name AS contig_id
                FROM arkinlab_mobilome.genomad_summary
                WHERE element_type = "plasmid"
            ),
            plasmid_genes AS (
                SELECT g.gene_id
                FROM kescience_mgnify.gene g
                INNER JOIN plasmid_contigs pc ON g.contig_id = pc.contig_id
            ),
            exploded AS (
                SELECT pg.gene_id,
                       REPLACE(TRIM(ko_raw), "ko:", "") AS ko_id
                FROM plasmid_genes pg
                INNER JOIN kescience_mgnify.gene_eggnog e ON pg.gene_id = e.gene_id
                LATERAL VIEW OUTER explode(split(e.kegg_ko, ",")) t AS ko_raw
                WHERE e.kegg_ko IS NOT NULL AND e.kegg_ko != "-"
                  AND TRIM(ko_raw) != "" AND TRIM(ko_raw) != "-"
            )
            SELECT ko_id, COUNT(DISTINCT gene_id) AS n_mgnify_plasmid_genes
            FROM exploded
            WHERE ko_id IN ({ko_list_sql})
            GROUP BY ko_id
        ''').toPandas()
        kos_df = kos_df.merge(result, on='ko_id', how='left')
        kos_df['n_mgnify_plasmid_genes'] = kos_df['n_mgnify_plasmid_genes'].fillna(0).astype(int)
        print(f"  MGnify/Spark: {(kos_df['n_mgnify_plasmid_genes'] > 0).sum()} KOs with plasmid hits")
    except Exception as e:
        print(f"  MGnify Spark query failed: {e}")
        kos_df['n_mgnify_plasmid_genes'] = np.nan

    return kos_df


# ── 4. NCBI Entrez plasmid fraction (approach 3 — preferred) ─────────────────

def query_ncbi_plasmid_fraction(kos_df: pd.DataFrame) -> pd.DataFrame:
    """
    For each gene: plasmid_frac = n_sequences_with_gene_on_plasmid / n_total_sequences_with_gene.

    Uses NCBI Entrez esearch with:
      '{gene_name}'[Gene Name] AND plasmid[Filter]   (plasmid hits)
      '{gene_name}'[Gene Name]                        (total hits)

    This approach is NOT biased by AMR database coverage — it searches by gene name
    across all of NCBI nuccore. However, genes with fewer than MIN_NCBI_N total hits
    are excluded from the statistical test as their fractions are unreliable.

    Statistical test: Mann-Whitney U (double-signal vs background resistance KOs,
    filtered to n_total >= MIN_NCBI_N).
    """
    try:
        from Bio import Entrez
        Entrez.email = 'hmacgregor@lbl.gov'
    except ImportError:
        print("  Biopython not available — skipping NCBI query")
        kos_df['n_ncbi_total'] = np.nan
        kos_df['n_ncbi_plasmid'] = np.nan
        kos_df['plasmid_frac'] = np.nan
        return kos_df

    print(f"  Querying NCBI Entrez for {len(kos_df)} KOs …")
    n_total_list, n_plasmid_list = [], []

    for _, row in kos_df.iterrows():
        gene = row['gene_name']
        try:
            h = Entrez.esearch(db='nuccore',
                               term=f'"{gene}"[Gene Name] AND plasmid[Filter]', retmax=0)
            n_p = int(Entrez.read(h)['Count']); h.close()
            time.sleep(0.35)
            h = Entrez.esearch(db='nuccore', term=f'"{gene}"[Gene Name]', retmax=0)
            n_t = int(Entrez.read(h)['Count']); h.close()
            time.sleep(0.35)
        except Exception as e:
            print(f"    {gene}: NCBI error {e}")
            n_p, n_t = np.nan, np.nan
        n_total_list.append(n_t)
        n_plasmid_list.append(n_p)

    kos_df = kos_df.copy()
    kos_df['n_ncbi_total']   = n_total_list
    kos_df['n_ncbi_plasmid'] = n_plasmid_list
    kos_df['plasmid_frac'] = np.where(
        kos_df['n_ncbi_total'] > 0,
        kos_df['n_ncbi_plasmid'] / kos_df['n_ncbi_total'],
        np.nan
    )
    return kos_df


# ── 5. Enrichment test (NCBI fraction, Mann-Whitney) ─────────────────────────

def enrichment_test_ncbi(kos_df: pd.DataFrame) -> dict:
    filt = kos_df[kos_df['n_ncbi_total'] >= MIN_NCBI_N].dropna(subset=['plasmid_frac'])
    resist = filt[filt['is_resistance']]
    ds = resist[resist['is_double_signal']]
    bg = resist[~resist['is_double_signal']]

    print(f"\n  NCBI plasmid fraction — resistance KOs with n_total >= {MIN_NCBI_N}:")
    print(f"    Double-signal: n={len(ds)}  "
          f"median={ds['plasmid_frac'].median():.4f}  "
          f"KOs={list(zip(ds['gene_name'], ds['plasmid_frac'].round(4)))}")
    print(f"    Background:    n={len(bg)}  median={bg['plasmid_frac'].median():.4f}")

    result = {
        'method': 'ncbi_plasmid_fraction',
        'description': (
            'Mann-Whitney U test comparing NCBI plasmid fraction (n_plasmid/n_total) '
            'between double-signal and background resistance KOs. '
            f'Filtered to genes with >= {MIN_NCBI_N} total NCBI nuccore hits. '
            'Genes absent from NCBI (gesA n=1, gesB n=1, nrsD n=16) are excluded.'
        ),
        'n_double_signal_included': int(len(ds)),
        'n_background_included': int(len(bg)),
        'median_frac_double_signal': float(ds['plasmid_frac'].median()),
        'median_frac_background': float(bg['plasmid_frac'].median()),
        'min_ncbi_n_threshold': int(MIN_NCBI_N),
    }

    if len(ds) > 0 and len(bg) > 0:
        stat, p = mannwhitneyu(ds['plasmid_frac'], bg['plasmid_frac'], alternative='greater')
        result['U_statistic'] = float(stat)
        result['p_value'] = float(p)
        print(f"    Mann-Whitney U={stat:.0f}  p={p:.4f}")
    else:
        result['U_statistic'] = None
        result['p_value'] = None

    # PLSDB API counts for narrative (not statistical test)
    result['plsdb_api_counts'] = {
        row['gene_name']: int(row['n_plsdb'])
        for _, row in kos_df[kos_df['is_double_signal']].iterrows()
        if not pd.isna(row.get('n_plsdb', np.nan))
    }

    result['caveats'] = [
        'PLSDB AMR filter confounded: CARD/AMRFinder does not cover gesA, gesB, nrsD, '
        'aoxB — zeros reflect database gaps, not true plasmid absence.',
        'MGnify/geNomad plasmid set (1,053 contigs) is environmentally biased: '
        'mercury/gold/arsenite resistance plasmids are predominantly clinical/industrial.',
        'NCBI test underpowered: only 3 double-signal resistance KOs have n_total >= 50 '
        '(merD, norB, aoxB). gesA/gesB absent from NCBI. Result driven by merD/merE.',
        'golS (K19592) has high D=0.26 and low lambda=0.13 but plasmid_frac=0.000017 — '
        'a gold-sensing regulator, not a resistance effector; HGT may have occurred '
        'chromosomally rather than via plasmids.',
    ]

    return result


# ── 6. Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    print("Loading KOs …")
    kos = load_kos()
    resist = kos[kos['is_resistance'] | kos['is_double_signal']].drop_duplicates('ko_id').copy()

    print("\n[Approach 1] PLSDB API (AMR gene name filter) …")
    resist = query_plsdb_api(resist)

    print("\n[Approach 2] MGnify/geNomad plasmid contigs via Spark …")
    resist = query_mgnify_spark(resist)

    print("\n[Approach 3] NCBI Entrez plasmid fraction (preferred) …")
    resist = query_ncbi_plasmid_fraction(resist)

    print("\nRunning enrichment test …")
    result = enrichment_test_ncbi(resist)

    # Merge back into full KO frame for CSV output
    full = kos.merge(
        resist[['ko_id', 'n_plsdb', 'n_mgnify_plasmid_genes',
                'n_ncbi_total', 'n_ncbi_plasmid', 'plasmid_frac']],
        on='ko_id', how='left'
    )

    out_csv = DATA / 'plsdb_resistance_crossref.csv'
    full.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv}")

    out_json = DATA / 'plsdb_enrichment_test.json'
    with open(out_json, 'w') as f:
        json.dump(result, f, indent=2, default=int)
    print(f"Saved: {out_json}")

    print("\n=== Double-signal KOs summary ===")
    ds_all = resist[resist['is_double_signal']].sort_values('plasmid_frac', ascending=False)
    cols = ['ko_id', 'gene_name', 'subcategory', 'D', 'lambda',
            'n_plsdb', 'n_mgnify_plasmid_genes', 'n_ncbi_total', 'n_ncbi_plasmid', 'plasmid_frac']
    cols = [c for c in cols if c in ds_all.columns]
    print(ds_all[cols].to_string(index=False))


if __name__ == '__main__':
    main()
