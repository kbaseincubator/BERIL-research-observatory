"""NB28 Stage 2 — Tree-based parsimony donor inference at genus rank.

Algorithm (sister-clade-presence-as-donor-proxy, NOT requiring re-running Sankoff):
  For each recent-rank gain event at recipient_genus G for KO K:
    - parent = recipient_family of G
    - candidate_donor_genera = {genera in parent that have K at non-zero prevalence} - {G}
    - n_alt_candidates = |candidate_donor_genera|

  For each (genus G × KO K), aggregate:
    - n_recipient_gains  = recent-gain events landing in G for K
    - n_donor_events     = recent-gain events landing in sister-genera of G for K, where G has K present
    - donor_recipient_ratio = n_donor_events / max(n_recipient_gains, 1)

  Classify {Open Innovator, Broker, Sink, Closed/Stable, Ambiguous, Insufficient-Data}:
    - Insufficient if (n_recipient + n_donor) < 5
    - Closed/Stable if both close to zero AND G has K present (ancestral, no transitions)
    - Open Innovator if donor_recipient_ratio >= 2.0
    - Broker if 0.5 ≤ donor_recipient_ratio < 2.0
    - Sink if donor_recipient_ratio < 0.5

Restricted to Phase 3 candidate set (~10K KOs) for tractability and biological relevance.
"""
import json, time
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"
MIN_EVENTS_FOR_VERDICT = 5

t0 = time.time()
def tprint(msg):
    print(f"[{time.time()-t0:.1f}s] {msg}", flush=True)

tprint("=== NB28 Stage 2 — tree-based donor inference at genus rank ===")

# Load substrate
species = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
genus_to_family = species[["genus", "family"]].drop_duplicates().dropna()
genus_to_family_map = dict(zip(genus_to_family["genus"], genus_to_family["family"]))
tprint(f"  genera with family mapping: {len(genus_to_family_map):,}")

# Load atlas at genus rank only (to identify which genera carry which KOs)
atlas = pd.read_parquet(DATA_DIR / "p4_deep_rank_pp_atlas.parquet")
atlas_genus = atlas[atlas["rank"] == "genus"].copy()
tprint(f"  atlas genus rank: {len(atlas_genus):,} (genus × KO) entries")

# Build (KO, genus) → present-flag from atlas (presence = pp_category != Insufficient-Data AND clade has the KO)
# Use n_clades_with > 0 within atlas as presence proxy — actually atlas only contains tuples where ko is observed
# So all rows in atlas_genus indicate genus carries KO at some prevalence.
genus_has_ko = atlas_genus[["clade_id", "ko"]].rename(columns={"clade_id": "genus"})
genus_has_ko["has_ko"] = 1
tprint(f"  genus-has-ko table: {len(genus_has_ko):,}")

# Restrict to Phase 3 candidate KOs
candidate_set = pd.read_csv(DATA_DIR / "p3_candidate_set.tsv", sep="\t")
candidate_kos = set(candidate_set["ko"].unique())
tprint(f"  Phase 3 candidate KOs: {len(candidate_kos):,}")

genus_has_ko_candidate = genus_has_ko[genus_has_ko["ko"].isin(candidate_kos)].copy()
tprint(f"  genus-has-ko on candidate set: {len(genus_has_ko_candidate):,}")

# Add family
genus_has_ko_candidate["family"] = genus_has_ko_candidate["genus"].map(genus_to_family_map)
genus_has_ko_candidate = genus_has_ko_candidate.dropna(subset=["family"])
tprint(f"  with family: {len(genus_has_ko_candidate):,}")

# Build (family, ko) → list of genera with this ko (for donor candidate identification)
fam_ko_genera = (genus_has_ko_candidate
    .groupby(["family", "ko"])["genus"].agg(list).reset_index()
    .rename(columns={"genus": "genera_with_ko"}))
tprint(f"  (family × ko) → genera lookup: {len(fam_ko_genera):,}")

# Also compute n_alt_candidates per (family, ko)
fam_ko_genera["n_genera_with_ko"] = fam_ko_genera["genera_with_ko"].apply(len)

# Load M22 recent gains
gains = pd.read_parquet(DATA_DIR / "p2_m22_gains_attributed.parquet")
recent = gains[(gains["depth_bin"] == "recent") &
                gains["recipient_genus"].notna() &
                gains["ko"].isin(candidate_kos)].copy()
tprint(f"  recent gains on candidate KOs: {len(recent):,}")

# Add family
recent["recipient_family"] = recent["recipient_genus"].map(genus_to_family_map)
recent = recent.dropna(subset=["recipient_family"])
tprint(f"  with family: {len(recent):,}")

# Stage 2a: per-event donor candidate identification
tprint("\nStage 2a: identify donor candidates per event")

# Merge events with (family × ko) → candidate donor genera
recent_with_donors = recent.merge(
    fam_ko_genera, left_on=["recipient_family", "ko"], right_on=["family", "ko"], how="left")

# n_alt_candidates = n_genera_with_ko - 1 (subtract the recipient genus itself)
# But the recipient genus may not be in genera_with_ko if the ko was just gained and prevalence is low at the genus level
def compute_n_alt(row):
    if not isinstance(row["genera_with_ko"], list): return 0
    rec = row["recipient_genus"]
    return len([g for g in row["genera_with_ko"] if g != rec])

recent_with_donors["n_alt_donor_candidates"] = recent_with_donors.apply(compute_n_alt, axis=1)
tprint(f"  events with at least 1 donor candidate: {(recent_with_donors['n_alt_donor_candidates'] >= 1).sum():,}")
tprint(f"  events with 0 donor candidates (cross-family / orphan): {(recent_with_donors['n_alt_donor_candidates'] == 0).sum():,}")

# Stage 2b: per (genus × KO) aggregation — count recipient + donor events
tprint("\nStage 2b: aggregate per (genus × KO)")

# Recipient counts: trivial
recipient_counts = (recent.groupby(["recipient_genus", "ko"])
    .size().reset_index(name="n_recipient_gains")
    .rename(columns={"recipient_genus": "genus"}))

# Donor events — computed algebraically (no explode, no OOM):
#   For each (family × ko), let R_FK = total recipient events with recipient_family=F, ko=K.
#   For each genus G in F that has K present:
#       n_donor_events(G, K) = R_FK − recipient_events(G, K)
# This counts how many gain events into G's family the genus G could have donated.

# Total recipient events per (family × ko)
fam_ko_recipient = (recent.groupby(["recipient_family", "ko"])
    .size().reset_index(name="R_FK")
    .rename(columns={"recipient_family": "family"}))
tprint(f"  family × ko recipient totals: {len(fam_ko_recipient):,}")

# Per (family × ko × genus_with_ko_in_family) → R_FK − recipient_events_for_that_genus_ko
# Build via merging: family-ko genera (presence-side) × family-ko recipient totals × genus-ko recipient counts
gh = genus_has_ko_candidate[["genus", "ko", "family"]].copy()
gh_with_total = gh.merge(fam_ko_recipient, on=["family", "ko"], how="left")
gh_with_total["R_FK"] = gh_with_total["R_FK"].fillna(0).astype(int)
gh_with_total = gh_with_total.merge(
    recipient_counts.rename(columns={"genus": "genus", "n_recipient_gains": "self_recipient"}),
    on=["genus", "ko"], how="left")
gh_with_total["self_recipient"] = gh_with_total["self_recipient"].fillna(0).astype(int)
gh_with_total["n_donor_candidate_events"] = gh_with_total["R_FK"] - gh_with_total["self_recipient"]
gh_with_total["n_donor_candidate_events"] = gh_with_total["n_donor_candidate_events"].clip(lower=0)
donor_counts = gh_with_total[gh_with_total["n_donor_candidate_events"] > 0][["genus", "ko", "n_donor_candidate_events"]].copy()
tprint(f"  distinct (donor genus × ko) tuples (algebraic, no explode): {len(donor_counts):,}")

# Merge: full per-(genus × ko) view
merged = recipient_counts.merge(donor_counts, on=["genus", "ko"], how="outer").fillna(0)
merged["n_recipient_gains"] = merged["n_recipient_gains"].astype(int)
merged["n_donor_candidate_events"] = merged["n_donor_candidate_events"].astype(int)
merged["total_events"] = merged["n_recipient_gains"] + merged["n_donor_candidate_events"]
merged["donor_recipient_ratio"] = merged["n_donor_candidate_events"] / np.maximum(merged["n_recipient_gains"], 1)
tprint(f"  merged (genus × KO) donor inference table: {len(merged):,}")

# Stage 2c: classify
def classify(row):
    if row["total_events"] < MIN_EVENTS_FOR_VERDICT:
        return "Insufficient-Data"
    ratio = row["donor_recipient_ratio"]
    if ratio >= 2.0: return "Open-Innovator"
    if ratio >= 0.5: return "Broker"
    if row["n_recipient_gains"] > 0: return "Sink"
    return "Closed-Stable"

merged["quadrant_proxy"] = merged.apply(classify, axis=1)

# Confidence: high if total_events >= 20 AND mean_n_alt <= 5; medium if events >= 10; low otherwise
def confidence(row):
    if row["total_events"] < MIN_EVENTS_FOR_VERDICT: return "insufficient"
    if row["total_events"] >= 20: return "high"
    if row["total_events"] >= 10: return "medium"
    return "low"
merged["confidence"] = merged.apply(confidence, axis=1)

tprint(f"\n  Quadrant distribution:")
for q, n in merged["quadrant_proxy"].value_counts().items():
    tprint(f"    {q}: {n:,}")
tprint(f"  Confidence distribution:")
for c, n in merged["confidence"].value_counts().items():
    tprint(f"    {c}: {n:,}")

# Save
out_path = DATA_DIR / "p4_genus_rank_quadrants_tree_proxy.tsv"
merged.to_csv(out_path, sep="\t", index=False)
tprint(f"\n  wrote {out_path} ({len(merged):,} (genus × KO) tuples)")

# Notable highlights for confirmed hypothesis clades
tprint("\nHighlights — confirmed hypothesis clades:")
# Mycobacteriaceae genera
myco_genera = species[species["family"] == "f__Mycobacteriaceae"]["genus"].dropna().unique()
myco_quadrants = merged[merged["genus"].isin(myco_genera)]
tprint(f"  Mycobacteriaceae genera × candidate KOs: {len(myco_quadrants):,}")
tprint(f"    quadrant breakdown: {myco_quadrants['quadrant_proxy'].value_counts().to_dict()}")

# Cyanobacteriia genera
cyano_genera = species[species["class"] == "c__Cyanobacteriia"]["genus"].dropna().unique()
cyano_quadrants = merged[merged["genus"].isin(cyano_genera)]
tprint(f"  Cyanobacteriia genera × candidate KOs: {len(cyano_quadrants):,}")
tprint(f"    quadrant breakdown: {cyano_quadrants['quadrant_proxy'].value_counts().to_dict()}")

# Bacteroidota genera
bact_genera = species[species["phylum"] == "p__Bacteroidota"]["genus"].dropna().unique()
bact_quadrants = merged[merged["genus"].isin(bact_genera)]
tprint(f"  Bacteroidota genera × candidate KOs: {len(bact_quadrants):,}")
tprint(f"    quadrant breakdown: {bact_quadrants['quadrant_proxy'].value_counts().to_dict()}")

# Save diagnostics
diag = {
    "phase": "4", "deliverable": "NB28 Stage 2 — tree-based donor inference",
    "n_genera_total": int(len(merged["genus"].unique())),
    "n_kos_total": int(len(merged["ko"].unique())),
    "n_genus_ko_tuples": int(len(merged)),
    "min_events_for_verdict": MIN_EVENTS_FOR_VERDICT,
    "quadrant_distribution": merged["quadrant_proxy"].value_counts().to_dict(),
    "confidence_distribution": merged["confidence"].value_counts().to_dict(),
    "mycobacteriaceae_quadrants": myco_quadrants["quadrant_proxy"].value_counts().to_dict(),
    "cyanobacteriia_quadrants": cyano_quadrants["quadrant_proxy"].value_counts().to_dict(),
    "bacteroidota_quadrants": bact_quadrants["quadrant_proxy"].value_counts().to_dict(),
    "elapsed_s": round(time.time()-t0, 1),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p4_genus_rank_quadrants_diagnostics.json", "w") as f:
    json.dump(diag, f, indent=2, default=str)
tprint(f"\n=== Stage 2 DONE in {time.time()-t0:.1f}s ===")
