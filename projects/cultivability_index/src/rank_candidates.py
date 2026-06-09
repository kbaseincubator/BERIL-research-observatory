"""
NB04 candidate ranking.

Apply the trained cultivability classifier to all HQ uncultured genomes and
produce a prioritized list of MAGs that:
1) Are scored as isolate-like (high P_isolate)
2) Belong to families where at least one isolate exists (the model has seen
   what that family's isolates look like).
3) Are NOT from known auxotroph-rich CPR/DPANN/Patescibacteria lineages,
   unless an isolate from that lineage already exists.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

PROJ = Path(__file__).resolve().parent.parent
DATA = PROJ / "data"
FIGS = PROJ / "figures"

scored = pd.read_parquet(DATA / "scored_genomes.parquet")
print(f"Scored cohort: {len(scored):,}")
print(f"  isolates: {int(scored.is_isolate.sum()):,}")
print(f"  uncultured: {int((1-scored.is_isolate).sum()):,}")

# Family isolate presence
fam_iso = scored.groupby("family")["is_isolate"].sum().to_dict()
scored["family_has_isolate"] = scored["family"].map(fam_iso) > 0

# Known auxotroph-rich lineages (per literature: Patescibacteria, DPANN-style)
AUX_PHYLA = {
    "p__Patescibacteria",
    "p__Nanoarchaeota",
    "p__Iainarchaeota",
    "p__Aenigmatarchaeota",
    "p__Micrarchaeota",
    "p__Huberarchaeota",
    "p__Nanohaloarchaeota",
    "p__Undinarchaeota",
    "p__Altiarchaeota",
}
scored["aux_phylum"] = scored["phylum"].isin(AUX_PHYLA)

# Candidate set
cands = scored[
    (scored.is_isolate == 0)
    & (scored.p_isolate >= 0.5)
    & (scored.family_has_isolate)
    & (~scored.aux_phylum)
].copy()
print(f"\nCandidate pool (uncultured, p_isolate>=0.5, family has isolate, non-aux phylum): {len(cands):,}")
print(f"Across {cands['phylum'].nunique()} phyla, {cands['family'].nunique()} families, {cands['species'].nunique()} species")

# Tiered ranking
cands["tier"] = pd.cut(cands["p_isolate"], bins=[0.5, 0.7, 0.9, 1.01], labels=["B", "A", "S"])
print("\nTier distribution:")
print(cands["tier"].value_counts().to_string())

# H3: are top candidates over-represented in environmentally-interesting taxa?
# (Soil/subsurface/plant-associated phyla we'd want to culture)
ENV_OF_INTEREST = {
    "p__Acidobacteriota", "p__Actinomycetota", "p__Pseudomonadota",
    "p__Bacillota", "p__Bacteroidota", "p__Chloroflexota",
    "p__Verrucomicrobiota", "p__Planctomycetota", "p__Gemmatimonadota",
    "p__Cyanobacteriota", "p__Spirochaetota", "p__Myxococcota",
}
cands["env_interest"] = cands["phylum"].isin(ENV_OF_INTEREST)

# Sort and save
cands = cands.sort_values("p_isolate", ascending=False)
cols_out = ["genome_id", "p_isolate", "tier", "phylum", "class", "order", "family", "genus", "species",
            "checkm_comp", "genome_size", "gc_pct", "aa_frac", "carbon_frac", "env_interest"]
cands[cols_out].to_csv(DATA / "cultivability_candidates.tsv", sep="\t", index=False, float_format="%.4g")
print(f"\nWrote data/cultivability_candidates.tsv ({len(cands):,} rows)")
print("\nTop 15 candidates:")
print(cands.head(15)[["genome_id", "p_isolate", "tier", "phylum", "family", "species"]].to_string(index=False))

# Top-tier (S) by phylum
print("\nS-tier (p_isolate >= 0.9) candidates by phylum:")
s_tier = cands[cands.tier == "S"]
print(s_tier["phylum"].value_counts().head(20).to_string())

# ----- visualization: candidate phyla breakdown -----
top_phyla = cands["phylum"].value_counts().head(15).index.tolist()
counts = pd.DataFrame({
    "S": cands[cands.tier == "S"]["phylum"].value_counts(),
    "A": cands[cands.tier == "A"]["phylum"].value_counts(),
    "B": cands[cands.tier == "B"]["phylum"].value_counts(),
}).fillna(0).astype(int).loc[top_phyla]

fig, ax = plt.subplots(figsize=(9, 6))
counts.plot(kind="barh", stacked=True, ax=ax, color=["#0571b0", "#92c5de", "#f4a582"])
ax.invert_yaxis()
ax.set_xlabel("Candidate MAG count")
ax.set_ylabel("")
ax.set_title(f"Top 15 phyla in the {len(cands):,}-genome cultivability candidate pool")
ax.legend(title="tier", loc="lower right")
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig(FIGS / "candidate_phyla.png", dpi=150, bbox_inches="tight")
plt.close()
print("\nWrote figures/candidate_phyla.png")

# ----- enrichment test: are S-tier candidates enriched in environmentally-interesting taxa? -----
from scipy import stats
all_uncultured = scored[scored.is_isolate == 0]
n_env_uncult = int(all_uncultured["phylum"].isin(ENV_OF_INTEREST).sum())
n_nonenv_uncult = len(all_uncultured) - n_env_uncult
n_env_s = int(s_tier["env_interest"].sum())
n_nonenv_s = len(s_tier) - n_env_s
table = [[n_env_s, n_nonenv_s], [n_env_uncult - n_env_s, n_nonenv_uncult - n_nonenv_s]]
or_, p = stats.fisher_exact(table)
print(f"\nH3: S-tier enriched in env-of-interest phyla?")
print(f"   Fisher exact OR={or_:.3f}, p={p:.3g}")
print(f"   S-tier env/non-env: {n_env_s} / {n_nonenv_s}")
print(f"   All-uncult env/non-env: {n_env_uncult} / {n_nonenv_uncult}")

# ============================================================================
# Stricter "genuinely uncultured" filter: genus has zero isolates,
# but family has at least one. These are the cultivability candidates that
# actually represent uncultured biology.
# ============================================================================
print("\n" + "=" * 70)
print("Stricter filter: genus has zero isolates, family has at least one isolate")
print("=" * 70)

genus_iso = scored.groupby("genus")["is_isolate"].sum().to_dict()
fam_iso_count = scored.groupby("family")["is_isolate"].sum().to_dict()
scored["genus_has_isolate"] = scored["genus"].map(genus_iso) > 0
scored["fam_iso_count"] = scored["family"].map(fam_iso_count)

strict = scored[
    (scored.is_isolate == 0)
    & (scored.p_isolate >= 0.5)
    & (~scored.aux_phylum)
    & (~scored.genus_has_isolate)
    & (scored.fam_iso_count > 0)
].copy()
print(f"Strict candidate pool: {len(strict):,} MAGs from genuinely uncultured genera in cultivated families")
print(f"  across {strict['phylum'].nunique()} phyla, {strict['family'].nunique()} families, {strict['genus'].nunique()} genera")

strict["tier"] = pd.cut(strict["p_isolate"], bins=[0.5, 0.7, 0.9, 1.01], labels=["B", "A", "S"])
print("\nStrict tier distribution:")
print(strict["tier"].value_counts().to_string())

strict = strict.sort_values("p_isolate", ascending=False)
strict["env_interest"] = strict["phylum"].isin(ENV_OF_INTEREST)
strict[cols_out].to_csv(DATA / "cultivability_candidates_strict.tsv", sep="\t", index=False, float_format="%.4g")
print(f"\nWrote data/cultivability_candidates_strict.tsv ({len(strict):,} rows)")

print("\nTop 15 strict candidates (uncultured genera in cultivated families):")
print(strict.head(15)[["genome_id", "p_isolate", "tier", "phylum", "family", "genus", "species"]].to_string(index=False))

print("\nStrict S-tier (p>=0.9) by family:")
print(strict[strict.tier == "S"]["family"].value_counts().head(15).to_string())

# Strict candidates phyla breakdown figure
top_phyla_strict = strict["phylum"].value_counts().head(12).index.tolist()
counts_s = pd.DataFrame({
    "S": strict[strict.tier == "S"]["phylum"].value_counts(),
    "A": strict[strict.tier == "A"]["phylum"].value_counts(),
    "B": strict[strict.tier == "B"]["phylum"].value_counts(),
}).fillna(0).astype(int).loc[top_phyla_strict]
fig, ax = plt.subplots(figsize=(9, 5))
counts_s.plot(kind="barh", stacked=True, ax=ax, color=["#0571b0", "#92c5de", "#f4a582"])
ax.invert_yaxis()
ax.set_xlabel("Candidate MAG count")
ax.set_ylabel("")
ax.set_title(f"Strict candidates: {len(strict):,} MAGs from uncultured genera in cultivated families")
ax.legend(title="tier", loc="lower right")
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig(FIGS / "candidate_phyla_strict.png", dpi=150, bbox_inches="tight")
plt.close()
print("Wrote figures/candidate_phyla_strict.png")
