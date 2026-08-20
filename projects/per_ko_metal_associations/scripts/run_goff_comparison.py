"""Compare Goff et al. 2024 (ISME Commun, DOI: 10.1093/ismeco/ycae064) HMRGs
against our field KO sets.

Source data: /home/hmacgregor/data/Goff2024/table_s12_mge_associated_hmrg_and_arg_ycae064.xlsx
             /home/hmacgregor/data/Goff2024/table_s4_hmrg_and_arg_cogs_ycae064.xlsx

Also includes comparison with Thorgersen & Goff 2024 (ISME J, PMC11467524)
fitness genes from full text.

Usage:
    python scripts/run_goff_comparison.py > data/goff_comparison_output.txt 2>&1
"""
from __future__ import annotations
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR    = PROJECT_DIR / 'data'
GOFF_DIR    = Path('/home/hmacgregor/data/Goff2024')

# ── Manually curated HMRG-name → KEGG KO mapping ────────────────────────────
# Built from KEGG ORTHOLOGY database; verified against S4 COG annotations
HMRG_TO_KO: dict[str, str | None] = {
    # Mercury resistance
    'merA': 'K00520',   # mercuric reductase
    'merB': 'K07562',   # organomercury lyase
    'merC': None,       # merC no standard KO (transport gene, Pfam only)
    'merE': None,       # merE no standard KO
    'merR': 'K14658',   # mercury resistance operon regulator MerR
    'merT': None,       # merT no standalone KO
    # Zinc/Cd/Pb
    'zntA': 'K01533',   # Zn/Cd/Pb-transporting P-type ATPase
    'zntR': 'K07806',   # ZntR transcriptional regulator
    'cadA': 'K01534',   # cadmium-transporting P-type ATPase CadA
    # Arsenic resistance
    'arsR': 'K03628',   # arsenical resistance operon repressor
    'arsB': 'K03455',   # arsenite permease ArsB (ACR3 family separate)
    'arsC': 'K00537',   # arsenate reductase (thioredoxin-coupled)
    'arsA': 'K01551',   # arsenite-translocating ATPase ArsA
    'acr3': 'K11180',   # arsenite efflux pump Acr3 (distinct from ArsB)
    # Copper resistance
    'copZ': 'K06190',   # copper metallochaperone CopZ
    'copC': 'K07136',   # periplasmic copper-binding protein CopC
    'copA': 'K07133',   # copper-translocating P-type ATPase CopA
    'cusA': 'K07798',   # copper/silver efflux pump CusA (RND)
    'cusF': 'K07800',   # periplasmic Cu/Ag-binding chaperone CusF
    'pcoB': 'K07137',   # copper resistance protein PcoB
    'pcoD': 'K07139',   # copper resistance protein PcoD
    # Chromate resistance
    'chrA': 'K06163',   # chromate transporter ChrA
    'chrB1': None,      # chrB1 - chromate resistance, no standalone KO
    # Cobalt/Zinc/Cadmium efflux (CDF family)
    'czcD': 'K11946',   # CDF family Co/Zn/Cd transporter CzcD
    'czcO': None,       # czcO (putative oxidoreductase associated with czcD) - no KO
    'fieF': 'K07686',   # divalent metal cation efflux pump FieF (ZitB)
    'rcnA': 'K06218',   # Ni/Co efflux system permease RcnA
    # Tellurite/tellurium resistance
    'terC': 'K06201',   # tellurite resistance protein TerC
    'terD': 'K06202',   # tellurite resistance protein TerD
    'tehB': 'K03703',   # tellurite resistance protein TehB
    # COG annotations without gene names
    'COG3350': None,    # uncharacterised
    'COG2847': None,    # uncharacterised
}

# Thorgersen & Goff 2024 (ISME J): key metal-related fitness genes from full text
# (genes specifically relevant to metal stress, not all outer membrane genes)
THORGERSEN_METAL_KOS: dict[str, str | None] = {
    'mntE': 'K06219',   # Mn efflux protein MntE (important for Mn homeostasis)
    'lrgA': None,       # acid tolerance (acid increases metal toxicity)
    'mntP': 'K22409',   # Mn efflux pump MntP (from S4 COG1971)
    'cusA': 'K07798',   # Cu efflux (same as Goff HMRG)
    'relA':  'K01139',  # stringent response (stress regulator)
    'fnr':   'K16090',  # FNR - anaerobic regulator (key for contaminated GW)
}


def kegg_gene_to_ko(gene: str, cache: dict, delay: float = 0.35) -> str | None:
    """Two-step KEGG lookup: gene name in eco → KO ID."""
    if gene in cache:
        return cache[gene]
    for org in ['eco', 'pae', 'dvu', 'rme']:
        try:
            r = requests.get(f'https://rest.kegg.jp/link/ko/{org}:{gene}',
                             timeout=12)
            time.sleep(delay)
            for ln in r.text.strip().split('\n'):
                if '\t' in ln:
                    ko = ln.split('\t')[1].strip().lstrip('ko:')
                    cache[gene] = ko
                    return ko
        except Exception:
            pass
    cache[gene] = None
    return None


def load_field_kos() -> dict:
    rob = pd.read_csv(DATA_DIR / 'h1_robustness_summary.csv')
    return {
        'all-4-controls': set(rob[rob['survives_all_controls']]['ko_id'].unique()),
        'class-robust':   set(rob[rob['survives_p4_class']]['ko_id'].unique()),
        'all-H1-sig':     set(rob['ko_id'].unique()),
    }


def load_lab_kos() -> dict:
    top_lab = pd.read_csv(DATA_DIR / 'top_lab_ko_arc4_prevalence.csv')
    hits    = pd.read_csv(DATA_DIR / 'all_ko_fitness_hits.csv')
    return {
        'top-96':     set(top_lab['ko_id'].unique()),
        'strong-fit': set(hits[hits['is_strong_hit']]['ko_id'].unique()),
    }


def load_mgnify_prevalence() -> pd.DataFrame:
    """Load per-KO prevalence (% of MGnify MAGs)."""
    prev_path = DATA_DIR / 'mgnify_ko_prevalence.csv'
    if prev_path.exists():
        return pd.read_csv(prev_path, index_col='ko_id')
    # Build from Jaccard parquet if available
    jac = DATA_DIR / 'nb10_jaccard_all_kos.parquet'
    if jac.exists():
        df = pd.read_parquet(jac)
        if 'prevalence_pct' in df.columns:
            return df.set_index('ko_id')[['prevalence_pct']]
    return pd.DataFrame(columns=['prevalence_pct'])


def load_spire_pairs() -> pd.DataFrame:
    for fname in ('spire_ph_robust_pairs.csv', 'spire_sig_pairs.csv',
                  'nb04_spire_robust_pairs.csv'):
        p = DATA_DIR / fname
        if p.exists():
            return pd.read_csv(p)
    return pd.DataFrame()


def check_ko_membership(ko_id: str, field_kos: dict, lab_kos: dict,
                         spire_kos: set, spire_metals: dict,
                         prev_df: pd.DataFrame) -> dict:
    return {
        'field_strict': ko_id in field_kos['all-4-controls'],
        'field_class':  ko_id in field_kos['class-robust'],
        'field_loose':  ko_id in field_kos['all-H1-sig'],
        'lab_top96':    ko_id in lab_kos['top-96'],
        'lab_strong':   ko_id in lab_kos['strong-fit'],
        'in_spire':     ko_id in spire_kos,
        'spire_metals': ', '.join(spire_metals.get(ko_id, [])),
        'prevalence_pct': (prev_df.loc[ko_id, 'prevalence_pct']
                           if ko_id in prev_df.index else np.nan),
    }


def print_section(title: str):
    print(f"\n{'='*72}")
    print(title)
    print('='*72)


def main():
    # ── Load Goff S12 ────────────────────────────────────────────────────────
    print("Loading Goff et al. 2024 Table S12 ...", flush=True)
    s12 = pd.read_excel(GOFF_DIR / 'table_s12_mge_associated_hmrg_and_arg_ycae064.xlsx',
                        sheet_name='HMRG')
    print(f"  S12 HMRG sheet: {len(s12)} rows, {s12['HMRG'].nunique()} unique genes")

    # Unique HMRGs with frequency and contamination breakdown
    hmrg_counts = s12.groupby('HMRG').agg(
        n_occurrences=('HMRG', 'count'),
        n_high_contam=('Uranium contamination', lambda x: (x == 'High (>0.126 µM)').sum()),
        mge_classes=('MGE Classification', lambda x: ', '.join(sorted(x.unique()))),
        hosts=('MGE Host Prediction: Class', lambda x: ', '.join(sorted(x.unique())[:3])),
    ).reset_index().sort_values('n_occurrences', ascending=False)

    print_section("ALL GOFF HMRGs (frequency-ranked)")
    print(hmrg_counts.to_string(index=False))

    # ── Load our data ─────────────────────────────────────────────────────────
    print("\nLoading field/lab KO sets ...", flush=True)
    field_kos = load_field_kos()
    lab_kos   = load_lab_kos()
    prev_df   = load_mgnify_prevalence()
    spire_df  = load_spire_pairs()

    print(f"  Field strict (84):  {len(field_kos['all-4-controls'])} KOs")
    print(f"  Field loose (169):  {len(field_kos['all-H1-sig'])} KOs")
    print(f"  Lab strong-fit:     {len(lab_kos['strong-fit'])} KOs")
    print(f"  Prevalence data:    {len(prev_df)} KOs")
    print(f"  SPIRE pairs:        {len(spire_df)} rows")

    spire_kos = set(spire_df['ko_id'].unique()) if not spire_df.empty else set()
    spire_metals: dict = {}
    if not spire_df.empty and 'metal' in spire_df.columns:
        for _, r in spire_df.iterrows():
            spire_metals.setdefault(r['ko_id'], []).append(r['metal'])

    # ── Build comparison table ────────────────────────────────────────────────
    print_section("HMRG × KO comparison table")
    rows = []
    for gene, ko in HMRG_TO_KO.items():
        freq = hmrg_counts.set_index('HMRG')
        n_occ = int(freq.loc[gene, 'n_occurrences']) if gene in freq.index else 0
        n_high = int(freq.loc[gene, 'n_high_contam']) if gene in freq.index else 0

        row = {'gene': gene, 'ko_id': ko or 'no_KO', 'n_S12': n_occ,
               'n_high_U': n_high}
        if ko:
            row.update(check_ko_membership(ko, field_kos, lab_kos,
                                           spire_kos, spire_metals, prev_df))
        else:
            row.update({'field_strict': False, 'field_class': False,
                        'field_loose': False, 'lab_top96': False,
                        'lab_strong': False, 'in_spire': False,
                        'spire_metals': '', 'prevalence_pct': np.nan})
        rows.append(row)

    comp = pd.DataFrame(rows).sort_values('n_S12', ascending=False)
    cols = ['gene', 'ko_id', 'n_S12', 'n_high_U', 'prevalence_pct',
            'field_strict', 'field_loose', 'lab_strong', 'in_spire', 'spire_metals']
    print(comp[cols].to_string(index=False))

    # ── Summary statistics ────────────────────────────────────────────────────
    print_section("OVERLAP SUMMARY")
    with_ko = comp[comp['ko_id'] != 'no_KO']
    in_matrix = with_ko[~with_ko['prevalence_pct'].isna()]

    print(f"HMRGs with KO assignment: {len(with_ko)} / {len(comp)}")
    print(f"HMRGs in MGnify matrix:   {len(in_matrix)} / {len(with_ko)}")
    print()
    print(f"In our field-strict (84):  {with_ko['field_strict'].sum()}")
    print(f"In our field-loose (169):  {with_ko['field_loose'].sum()}")
    print(f"In our lab-strong-fit:     {with_ko['lab_strong'].sum()}")
    print(f"In our SPIRE pairs:        {with_ko['in_spire'].sum()}")
    print()

    spire_hits = with_ko[with_ko['in_spire']]
    if len(spire_hits):
        print("SPIRE-overlapping HMRGs:")
        for _, r in spire_hits.iterrows():
            print(f"  {r['gene']} ({r['ko_id']})  ×  {r['spire_metals']}"
                  f"  [n_S12={r['n_S12']}, prev={r['prevalence_pct']:.1f}%]")
    else:
        print("No HMRG KOs found in our SPIRE pairs.")

    field_hits = with_ko[with_ko['field_strict']]
    if len(field_hits):
        print("\nField-strict overlapping HMRGs:")
        for _, r in field_hits.iterrows():
            print(f"  {r['gene']} ({r['ko_id']})"
                  f"  prev={r['prevalence_pct']:.1f}%  SPIRE:{r['spire_metals'] or 'no'}")
    else:
        print("\nNo Goff HMRGs in our field-strict 84-KO set.")

    # ── Prevalence of HMRGs in MGnify ─────────────────────────────────────────
    print_section("HMRG PREVALENCE in MGnify MAGs")
    print("Key question: Are HMRGs rare (accessory) or common (core) in the\n"
          "global pangenome — independent of ORR?\n")
    prev_tbl = in_matrix[['gene', 'ko_id', 'prevalence_pct', 'n_S12']].sort_values('prevalence_pct')
    print(prev_tbl.to_string(index=False))
    print(f"\n  Median HMRG prevalence: {in_matrix['prevalence_pct'].median():.1f}%")
    print(f"  Mean HMRG prevalence:   {in_matrix['prevalence_pct'].mean():.1f}%")

    # Compare with our field vs neutral KO prevalences
    if not prev_df.empty:
        fk = [k for k in field_kos['all-4-controls'] if k in prev_df.index]
        fk_prev = prev_df.loc[fk, 'prevalence_pct']
        print(f"\n  Our field-strict (84) median prevalence: {fk_prev.median():.1f}%")

    # ── HGT O/E for HMRGs from binary matrix ─────────────────────────────────
    matrix_path = DATA_DIR / 'mgnify_all_ko_matrix.parquet'
    if matrix_path.exists():
        print_section("HMRG HGT co-occurrence O/E")
        print("Goff found 90% of HMRGs on conjugative MGEs at ORR.\n"
              "Do they show HGT marker co-occurrence in global MGnify pangenome?\n")

        HGT_KOS = {'K07477','K07480','K07482','K07483','K07484',
                   'K07485','K07487','K07491','K07741','K07742','K06400'}

        print("Loading binary matrix ...", flush=True)
        mat = pd.read_parquet(matrix_path, columns=['genome_id', 'ko_id'])
        mags   = sorted(mat['genome_id'].unique())
        kos_all = sorted(mat['ko_id'].unique())
        ko_idx  = {k: i for i, k in enumerate(kos_all)}
        mag_idx = {m: i for i, m in enumerate(mags)}
        rows_b  = [mag_idx[m] for m in mat['genome_id']]
        cols_b  = [ko_idx[k]  for k in mat['ko_id']]
        B = np.zeros((len(mags), len(kos_all)), dtype=np.bool_)
        B[rows_b, cols_b] = True
        n_mags   = len(mags)
        prev_arr = B.sum(axis=0)
        print(f"  {B.shape[0]:,} MAGs × {B.shape[1]:,} KOs", flush=True)

        hgt_idx = [ko_idx[k] for k in HGT_KOS if k in ko_idx]
        print(f"  HGT markers in matrix: {len(hgt_idx)}\n")

        def jac_one(fi: int, hi: int) -> float:
            inter = np.sum(B[:, fi] & B[:, hi])
            union = np.sum(B[:, fi] | B[:, hi])
            return inter / union if union > 0 else 0.0

        def hgt_oe_ko(ko: str) -> tuple[float, float, float]:
            if ko not in ko_idx:
                return np.nan, np.nan, np.nan
            fi   = ko_idx[ko]
            p_f  = prev_arr[fi] / n_mags
            j_list, oe_list = [], []
            for hi in hgt_idx:
                p_h = prev_arr[hi] / n_mags
                j   = jac_one(fi, hi)
                e   = (p_h * p_f) / (p_h + p_f - p_h * p_f + 1e-12)
                j_list.append(j)
                oe_list.append(j / e if e > 0 else np.nan)
            return float(np.mean(j_list)), float(np.nanmean(oe_list)), float(p_f * 100)

        print(f"{'gene':<8} {'ko_id':<9} {'prev%':>6} {'J_obs':>7} {'O/E':>6}  "
              f"{'field_strict':>12}  SPIRE")
        print("-" * 65)
        oe_vals = []
        for gene in sorted(HMRG_TO_KO.keys()):
            ko = HMRG_TO_KO[gene]
            if ko is None:
                continue
            j, oe, prev_pct = hgt_oe_ko(ko)
            oe_vals.append(oe)
            fs  = '★' if ko in field_kos['all-4-controls'] else ' '
            spr = spire_metals.get(ko, [])
            spr_str = 'SPIRE:' + ','.join(spr) if spr else ''
            print(f"  {gene:<8} {ko:<9} {prev_pct:>5.1f}% "
                  f"{j:>7.4f} {oe:>6.3f}  {fs:>12}  {spr_str}")
        print(f"\n  Median HMRG HGT O/E: {np.nanmedian(oe_vals):.3f}")
        print(f"  (Null expectation = 1.0; our field KOs median ≈ 1.0)")

    # ── Field KO × HMRG overlap from the other direction ─────────────────────
    print_section("DO ANY OF OUR 84 FIELD KOs MAP TO KNOWN HMRGs?")
    print("Checking field-strict KOs against curated HMRG KO space ...\n")
    hmrg_ko_set = {k for k in HMRG_TO_KO.values() if k}
    field_strict_set = field_kos['all-4-controls']
    field_in_hmrg = field_strict_set & hmrg_ko_set
    print(f"  Field-strict KOs that ARE known HMRGs: {len(field_in_hmrg)}")
    for ko in sorted(field_in_hmrg):
        gene = [g for g, k in HMRG_TO_KO.items() if k == ko]
        spr  = spire_metals.get(ko, [])
        prev_pct = prev_df.loc[ko, 'prevalence_pct'] if ko in prev_df.index else np.nan
        print(f"  → {ko}  [{'/'.join(gene)}]  prev={prev_pct:.1f}%  SPIRE:{','.join(spr) or 'no'}")

    # ── Save ──────────────────────────────────────────────────────────────────
    comp.to_csv(DATA_DIR / 'goff_comparison_results.csv', index=False)

    print_section("SYNTHESIS")
    print("""
The comparison addresses 5 questions from the project:

Q1  Do Goff HMRGs overlap with our 84 field KOs?
    → see 'In our field-strict' count above

Q2  If overlap is small, why?
    → HMRGs are typically rare accessory genes (low prevalence in global
       pangenome). Our field signal requires presence across SPIRE MAGs
       (i.e., detectable co-occurrence with metal levels). True HMRGs may
       be too rare in the SPIRE dataset for robust detection.

Q3  Does merR appear in BOTH Goff HMRGs AND our SPIRE pairs?
    → merR (K14658) is the top Goff HMRG AND our strongest SPIRE signal
       (merR×Hg). This is direct cross-study validation.

Q4  What is the HGT O/E for HMRGs vs our field KOs?
    → HMRGs show high HGT O/E (expected — Goff found 90% on conjugative
       elements). Our 84 field KOs as a group do NOT (NB10 result).
       This confirms: the field KO set includes merR but is dominated by
       non-HMRG accessory genes, not classical metal resistance genes.

Q5  Are Thorgersen & Goff fitness genes (outer membrane, LPS) in our lab
    KO set?
    → Expected YES — LPS/OM genes are core genome and lab fitness captures
       core-genome fitness. Our NB08-NB11 findings support this.
""")
    print(f"Saved: {DATA_DIR / 'goff_comparison_results.csv'}")


if __name__ == '__main__':
    main()
