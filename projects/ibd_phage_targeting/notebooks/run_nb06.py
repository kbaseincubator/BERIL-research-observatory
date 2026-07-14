"""NB06 — Per-ecotype co-occurrence networks + module ↔ Tier-A intersection (H2d test).

Standalone runner (sidesteps the environment nbconvert numpy.bool bug seen in NB05).
Writes TSVs + figure + section logs; a companion build_nb06_with_outputs.py hydrates
a clean NB06_cooccurrence_networks.ipynb with pre-populated outputs.

Per H2d in RESEARCH_PLAN.md: "Pathobiont co-occurrence modules (SparCC / SpiecEasi
per ecotype) contain >= 2 Tier-A candidates each. Disproved if: modules contain <=1
Tier-A hub on average -- suggesting pathobionts are ecologically independent and
monovalent cocktails may suffice."

Method: CLR-transform per-subnet relative abundance, compute Spearman correlation
(rank-transform + Pearson = Spearman), FDR-correct per-edge p-values, threshold
|rho| > 0.3 and FDR < 0.05, build undirected graph, Louvain community detection
(networkx 3.5 built-in). Score each module by Tier-A candidate content from NB05.

Subnets:
  - E1 all samples (n=2,601; primary)
  - E3 all samples (n=1,364; primary)
  - E1 CD-only (n=581; disease-specific modules)
  - E3 CD-only (n=605; disease-specific modules)
"""
import warnings; warnings.filterwarnings('ignore')
from pathlib import Path
import json, io, sys, contextlib, time
import numpy as np
import pandas as pd
import networkx as nx
from scipy.stats import spearmanr
from statsmodels.stats.multitest import multipletests
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 100

NOTEBOOK_DIR = Path(__file__).parent
PROJECT = NOTEBOOK_DIR.parent
DATA_MART = Path.home() / 'data' / 'CrohnsPhage'
DATA_OUT = PROJECT / 'data'
FIG_OUT = PROJECT / 'figures'

section_logs = {}
def section(name):
    buf = io.StringIO()
    return buf, contextlib.redirect_stdout(buf)

# ============================================================
# §1. Load wide matrix + ecotype + diagnosis + NB05 Tier-A
# ============================================================
buf, redir = section('1')
with redir:
    syn = pd.read_csv(DATA_OUT / 'species_synonymy.tsv', sep='\t')
    lookup = dict(zip(syn.alias, syn.canonical))

    ta = pd.read_parquet(DATA_MART / 'fact_taxon_abundance.snappy.parquet')
    ta = ta[(ta.classification_method == 'metaphlan3') & (ta.study_id.isin(['CMD_HEALTHY','CMD_IBD']))].copy()
    def normalize_format(name):
        if not isinstance(name, str): return None
        if '|' in name:
            parts = [p for p in name.split('|') if p.startswith('s__')]
            return parts[0][3:].replace('_',' ').strip() if parts else None
        return name.replace('[','').replace(']','').strip()
    def resolve(name):
        if not isinstance(name, str): return None
        if name in lookup: return lookup[name]
        fn = normalize_format(name)
        return lookup.get(fn, fn) if fn else None
    ta['species'] = ta['taxon_name_original'].map(resolve)
    ta = ta.dropna(subset=['species']).copy()
    wide = ta.pivot_table(index='species', columns='sample_id', values='relative_abundance',
                         aggfunc='sum', fill_value=0.0)

    eco = pd.read_csv(DATA_OUT / 'ecotype_assignments.tsv', sep='\t')
    eco_map = dict(zip(eco.sample_id, eco.consensus_ecotype))
    diag_map = dict(zip(eco.sample_id, eco.diagnosis))
    cols_keep = [c for c in wide.columns if c in eco_map]
    wide = wide[cols_keep]
    keep = pd.concat([
        (wide[[c for c in wide.columns if diag_map.get(c) == d]] > 0).mean(axis=1)
        for d in ['HC','CD','UC'] if any(diag_map.get(c) == d for c in wide.columns)
    ], axis=1).max(axis=1) >= 0.05
    w = wide.loc[keep].copy()
    print(f'Wide matrix: {w.shape[0]:,} species × {w.shape[1]:,} samples')

    nb05 = pd.read_csv(DATA_OUT / 'nb05_tier_a_scored.tsv', sep='\t')
    actionable = set(nb05[nb05.actionable].species)
    tier_b = set(nb05[(~nb05.actionable) & (nb05.total_score >= 2.2)].species)
    all_scored = set(nb05.species)
    print(f'NB05 Tier-A: {len(nb05)} scored; {len(actionable)} actionable; {len(tier_b)} Tier-B (2.2-2.4)')
    print(f'Actionable: {sorted(actionable)}')
section_logs['1'] = buf.getvalue()

def clr(M):
    M = M.astype(float).copy()
    col_min_nz = np.where(M > 0, M, np.nan)
    col_min_nz = np.nanmin(col_min_nz, axis=0)
    col_min_nz = np.where(np.isnan(col_min_nz), 1e-6, col_min_nz / 2)
    M = np.where(M > 0, M, col_min_nz[None, :])
    logM = np.log(M)
    return logM - logM.mean(axis=0, keepdims=True)

def compute_network(w_sub, species_labels, rho_thresh=0.3, fdr_thresh=0.05):
    """Vectorized Spearman: rank-transform each species across samples, then Pearson."""
    M = w_sub.values  # species × samples
    X = clr(M)  # species × samples CLR
    # Rank-transform rows (species × sample ranks within each species row)
    R = np.apply_along_axis(lambda x: pd.Series(x).rank(method='average').values, 1, X)
    # Pearson on ranks = Spearman
    R_c = R - R.mean(axis=1, keepdims=True)
    R_norm = R_c / np.sqrt((R_c**2).sum(axis=1, keepdims=True))
    corr = R_norm @ R_norm.T
    n = M.shape[1]
    # t-statistic for per-edge p-value
    t = corr * np.sqrt((n - 2) / np.maximum(1 - corr**2, 1e-12))
    from scipy.stats import t as t_dist
    p = 2 * (1 - t_dist.cdf(np.abs(t), df=n - 2))
    # Collect upper triangle
    iu, ju = np.triu_indices(len(species_labels), k=1)
    rho = corr[iu, ju]; pv = p[iu, ju]
    # FDR
    fdr = multipletests(pv, method='fdr_bh')[1]
    mask = (np.abs(rho) > rho_thresh) & (fdr < fdr_thresh)
    edges = pd.DataFrame({
        'source': [species_labels[i] for i in iu[mask]],
        'target': [species_labels[j] for j in ju[mask]],
        'rho': rho[mask], 'fdr': fdr[mask],
    })
    return edges

# ============================================================
# §2. Per-ecotype subnets + correlation matrices
# ============================================================
buf, redir = section('2')
with redir:
    subnets = {}
    for k in [1, 3]:
        for diag_filter, label in [(None, 'all'), ({'CD'}, 'CD')]:
            cols = [c for c in w.columns if eco_map.get(c) == k and
                    (diag_filter is None or diag_map.get(c) in diag_filter)]
            if len(cols) < 50:
                continue
            subnets[f'E{k}_{label}'] = cols
    for name, cols in subnets.items():
        print(f'{name}: {len(cols):,} samples')
section_logs['2'] = buf.getvalue()

# ============================================================
# §3. Compute networks
# ============================================================
buf, redir = section('3')
edge_tables = {}
graphs = {}
with redir:
    species_all = list(w.index)
    for name, cols in subnets.items():
        w_sub = w[cols]
        # drop species with 0 variance in this subset
        keep = w_sub.std(axis=1) > 0
        w_sub = w_sub.loc[keep]
        edges = compute_network(w_sub, list(w_sub.index))
        print(f'{name}: {len(edges):,} edges passing FDR<0.05, |rho|>0.3 '
              f'(of {len(w_sub)*(len(w_sub)-1)//2:,} pairs)')
        edges.to_csv(DATA_OUT / f'nb06_edges_{name}.tsv', sep='\t', index=False)
        edge_tables[name] = edges
        # Build networkx graph
        G = nx.from_pandas_edgelist(edges, source='source', target='target',
                                    edge_attr=['rho','fdr'])
        graphs[name] = G
        print(f'  graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges')
section_logs['3'] = buf.getvalue()

# ============================================================
# §4. Louvain community detection
# ============================================================
buf, redir = section('4')
module_assignments = {}
with redir:
    for name, G in graphs.items():
        if G.number_of_nodes() < 5:
            continue
        # Weight by |rho| to separate strong pos/neg correlations
        for u, v, d in G.edges(data=True):
            d['weight'] = abs(d['rho'])
        communities = nx.community.louvain_communities(G, weight='weight', seed=42, resolution=1.0)
        # Sort by size descending; assign IDs
        communities = sorted(communities, key=len, reverse=True)
        node_to_module = {n: i for i, comm in enumerate(communities) for n in comm}
        module_assignments[name] = (communities, node_to_module)
        print(f'{name}: {len(communities)} modules, sizes: {[len(c) for c in communities][:10]}')
section_logs['4'] = buf.getvalue()

# ============================================================
# §5. Per-module Tier-A content
# ============================================================
buf, redir = section('5')
module_stats = []
with redir:
    for name, (communities, n2m) in module_assignments.items():
        for mod_id, comm in enumerate(communities):
            act_hits = sorted(set(comm) & actionable)
            tier_b_hits = sorted(set(comm) & tier_b)
            all_scored_hits = sorted(set(comm) & all_scored)
            module_stats.append({
                'subnet': name, 'module_id': mod_id, 'size': len(comm),
                'n_actionable': len(act_hits), 'n_tier_b': len(tier_b_hits),
                'n_all_scored': len(all_scored_hits),
                'actionable_species': '|'.join(act_hits),
                'tier_b_species': '|'.join(tier_b_hits),
            })
    mod_df = pd.DataFrame(module_stats)
    mod_df.to_csv(DATA_OUT / 'nb06_modules.tsv', sep='\t', index=False)
    print('Per-subnet module summary (top 5 modules per subnet by size):')
    for name in sorted(mod_df.subnet.unique()):
        sub = mod_df[mod_df.subnet == name].head(5)
        print(f'\\n-- {name} --')
        print(sub[['module_id','size','n_actionable','n_tier_b','actionable_species']].to_string(index=False))
section_logs['5'] = buf.getvalue()

# ============================================================
# §6. H2d test: modules with >= 2 Tier-A hubs?
# ============================================================
buf, redir = section('6')
with redir:
    for name in sorted(mod_df.subnet.unique()):
        sub = mod_df[mod_df.subnet == name]
        # Consider modules of size >= 5 to avoid singletons
        big = sub[sub['size'] >= 5]
        n_big = len(big)
        if n_big == 0:
            print(f'{name}: no modules >= 5 nodes')
            continue
        n_ge2_actionable = (big.n_actionable >= 2).sum()
        n_ge1_actionable = (big.n_actionable >= 1).sum()
        mean_act = big.n_actionable.mean()
        # Include Tier-B too — "n_ge2_any" = modules with >= 2 of (actionable + tier_b)
        big_any = big.copy()
        big_any['n_act_or_b'] = big.n_actionable + big.n_tier_b
        n_ge2_any = (big_any.n_act_or_b >= 2).sum()
        print(f'{name}: {n_big} modules >= 5 nodes')
        print(f'  mean actionable per module: {mean_act:.2f}')
        print(f'  modules with >= 2 actionable: {n_ge2_actionable}')
        print(f'  modules with >= 1 actionable: {n_ge1_actionable}')
        print(f'  modules with >= 2 (actionable + tier-B): {n_ge2_any}')

    # Verdict for H2d across E1_all + E3_all (primary subnets)
    primary = mod_df[mod_df.subnet.isin(['E1_all','E3_all']) & (mod_df['size'] >= 5)]
    mean_act_primary = primary.n_actionable.mean() if len(primary) else 0
    verdict_h2d = 'SUPPORTED (modules cluster Tier-A hubs)' if mean_act_primary >= 2 else (
                   'PARTIAL (some modules have multiple Tier-A; others are monovalent)' if mean_act_primary >= 1 else
                   'NOT SUPPORTED (Tier-A species are mostly ecologically independent)')
    print(f'\\nH2d primary verdict (E1_all + E3_all, modules size >= 5):')
    print(f'  Mean actionable per module: {mean_act_primary:.2f}')
    print(f'  Verdict: {verdict_h2d}')
section_logs['6'] = buf.getvalue()

# ============================================================
# §7. Hub identification per module (degree centrality)
# ============================================================
buf, redir = section('7')
hub_rows = []
with redir:
    for name, G in graphs.items():
        if G.number_of_nodes() < 5:
            continue
        communities, n2m = module_assignments[name]
        deg = dict(G.degree())
        for mod_id, comm in enumerate(communities):
            if len(comm) < 5:
                continue
            # Top-3 hubs by degree within module
            sub_deg = sorted(((n, deg[n]) for n in comm), key=lambda x: -x[1])[:3]
            hub_rows.append({
                'subnet': name, 'module_id': mod_id, 'size': len(comm),
                'hub1': sub_deg[0][0] if len(sub_deg) > 0 else '',
                'hub1_deg': sub_deg[0][1] if len(sub_deg) > 0 else 0,
                'hub2': sub_deg[1][0] if len(sub_deg) > 1 else '',
                'hub2_deg': sub_deg[1][1] if len(sub_deg) > 1 else 0,
                'hub3': sub_deg[2][0] if len(sub_deg) > 2 else '',
                'hub3_deg': sub_deg[2][1] if len(sub_deg) > 2 else 0,
                'actionable_in_module': '|'.join(sorted(set(comm) & actionable)),
            })
    hub_df = pd.DataFrame(hub_rows)
    hub_df.to_csv(DATA_OUT / 'nb06_module_hubs.tsv', sep='\t', index=False)
    # Show top modules in E1_all and E3_all
    for name in ['E1_all','E3_all']:
        sub = hub_df[hub_df.subnet == name].head(8)
        print(f'\\n-- {name} module hubs --')
        print(sub[['module_id','size','hub1','hub2','hub3','actionable_in_module']].to_string(index=False))
section_logs['7'] = buf.getvalue()

# ============================================================
# §8. Figure
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
subnet_names = ['E1_all','E1_CD','E3_all','E3_CD']
for ax, name in zip(axes.flat, subnet_names):
    if name not in graphs:
        ax.set_title(f'{name} (not built)'); ax.axis('off'); continue
    G = graphs[name]
    communities, n2m = module_assignments[name]
    # Color nodes by module
    pos = nx.spring_layout(G, k=0.3, iterations=50, seed=42)
    cmap = mpl.colormaps['tab20']
    colors = [cmap(n2m[n] % 20) for n in G.nodes()]
    # Highlight actionable Tier-A with red border, Tier-B with orange
    edgecolors = ['red' if n in actionable else ('orange' if n in tier_b else 'white') for n in G.nodes()]
    linewidths = [2 if n in actionable else (1.5 if n in tier_b else 0.3) for n in G.nodes()]
    sizes = [100 if n in actionable else (50 if n in tier_b else 20) for n in G.nodes()]
    nx.draw_networkx_edges(G, pos, alpha=0.15, width=0.5, ax=ax)
    nx.draw_networkx_nodes(G, pos, node_color=colors, edgecolors=edgecolors,
                           linewidths=linewidths, node_size=sizes, ax=ax)
    # Label actionable + top-3 tier-B per module
    labels = {n: n.split(' ')[-1][:10] for n in G.nodes() if n in actionable}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=6, ax=ax)
    n_mods = len(communities)
    n_act = sum(1 for n in G.nodes() if n in actionable)
    ax.set_title(f'{name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, '
                 f'{n_mods} modules, {n_act} actionable highlighted', fontsize=10)
    ax.axis('off')
plt.tight_layout()
plt.savefig(FIG_OUT / 'NB06_cooccurrence_networks.png', dpi=120, bbox_inches='tight')
plt.close()
print('wrote figures/NB06_cooccurrence_networks.png')

# ============================================================
# §9. Verdict JSON
# ============================================================
def _def(o):
    if isinstance(o, (np.bool_, bool)): return bool(o)
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, np.floating): return float(o)
    return str(o)

verdict = {
    'date': '2026-04-24',
    'test': 'H2d — modules contain >= 2 Tier-A hubs (SparCC/SpiecEasi style)',
    'method': 'CLR + Spearman correlation, FDR<0.05, |rho|>0.3, Louvain communities',
    'subnets': {name: {'n_samples': len(subnets[name]),
                       'n_nodes': graphs[name].number_of_nodes() if name in graphs else 0,
                       'n_edges': graphs[name].number_of_edges() if name in graphs else 0,
                       'n_modules': len(module_assignments[name][0]) if name in module_assignments else 0}
                for name in subnet_names if name in subnets},
    'primary_mean_actionable_per_module': float(mean_act_primary),
    'h2d_verdict': verdict_h2d,
}
with open(DATA_OUT / 'nb06_verdict.json', 'w') as f:
    json.dump(verdict, f, indent=2, default=_def)
print('wrote data/nb06_verdict.json')

# Section logs dump
with open('/tmp/nb06_section_logs.json','w') as f:
    json.dump(section_logs, f, indent=2)
print('All sections done.')
