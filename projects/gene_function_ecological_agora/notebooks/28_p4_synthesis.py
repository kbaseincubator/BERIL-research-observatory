"""NB28 / P4-Synthesis — final atlas synthesis pass.

Stages (each writes intermediate artifacts so partial results recoverable):
  1. pre-registered verdicts TSV + 4-category P×P atlas parquet
  2. tree-based donor inference at genus rank → quadrants TSV
  3. concordance-weighted atlas + conflict analysis + per-event uncertainty
  4. 8 synthesis figures
  5. final REPORT/README/DESIGN updates (separate)

This file: Stage 1 only.
"""
import json, time
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"

t0 = time.time()
def tprint(msg):
    print(f"[{time.time()-t0:.1f}s] {msg}", flush=True)

tprint("=== NB28 Stage 1 — pre-registered verdicts + 4-category P×P atlas ===")

# === Stage 1a: 4-category P×P atlas parquet ===
tprint("Stage 1a: 4-category P×P atlas (deep ranks)")
atlas = pd.read_parquet(DATA_DIR / "p2_ko_atlas.parquet")
tprint(f"  full atlas: {len(atlas):,} rows")
tprint(f"  pp_category distribution: {atlas['pp_category'].value_counts().to_dict()}")

# Normalize the category name for downstream use
atlas["pp_category_clean"] = atlas["pp_category"].replace({
    "Innovator-Isolated": "Innovator-Isolated",
    "Innovator-Exchange": "Innovator-Exchange",
    "Sink/Broker-Exchange": "Sink-Broker-Exchange",
    "Stable": "Stable",
    "insufficient_data": "Insufficient-Data",
})
tprint(f"  cleaned category counts: {atlas['pp_category_clean'].value_counts().to_dict()}")

# Persist as the 4-category P×P atlas (rename pp_category_clean → pp_category for output)
out = atlas[["rank", "clade_id", "ko", "producer_z", "consumer_z", "n_clades_with",
              "control_class", "pp_category_clean"]].rename(columns={"pp_category_clean": "pp_category"})
out_path = DATA_DIR / "p4_deep_rank_pp_atlas.parquet"
out.to_parquet(out_path, index=False)
tprint(f"  wrote {out_path} ({len(out):,} rows × 8 cols)")

# Per-rank pp_category distributions (sanity)
for rank in ["genus", "family", "order", "class", "phylum"]:
    sub = atlas[atlas["rank"] == rank]
    cat_counts = sub["pp_category_clean"].value_counts().to_dict()
    tprint(f"  {rank}: {cat_counts}")

# === Stage 1b: pre-registered verdicts TSV ===
tprint("\nStage 1b: pre-registered verdicts TSV")

# Pull effect sizes from existing diagnostic JSONs
def safe_load(path):
    try:
        with open(path) as f: return json.load(f)
    except Exception as e:
        return None

p3_gate = safe_load(DATA_DIR / "p3_phase_gate_decision.json")
p4d1 = safe_load(DATA_DIR / "p4d1_diagnostics.json")
p4d2 = safe_load(DATA_DIR / "p4d2_diagnostics.json")
p4d3 = safe_load(DATA_DIR / "p4d3_diagnostics.json")
p4d5 = safe_load(DATA_DIR / "p4d5_diagnostics.json")

verdicts = []

# H1: Bacteroidota PUL (Phase 1B)
verdicts.append({
    "hypothesis_id": "H1",
    "hypothesis": "Bacteroidota → Innovator-Exchange on PUL CAZymes",
    "phase": "1B (UniRef50)",
    "atlas_test": "Per-rank Sankoff-parsimony diagnostic NB08c (deep-rank absolute-zero criterion failed; small consumer-z signal recovered)",
    "atlas_effect_size": "d=0.146 (UniRef50, NB08c Sankoff diagnostic)",
    "atlas_p_value": "p<0.001",
    "ecology_grounding": "1.40× gut/rumen biome enrichment (NB23 Fisher's exact)",
    "ecology_p_value": "p < 1e-35",
    "phenotype_anchor": "Bacteroidota saccharolytic + glycoside-hydrolase-rich (BacDive n=577, NB24)",
    "mge_verdict": "0% MGE-machinery (NB26c); ICE-mediated transfer per Sonnenburg 2010",
    "d2_residualization": "consumer d=−0.21 → −0.21 (unchanged, NB11 atlas-wide; not directly Bacteroidota-specific)",
    "final_disposition": "qualified pass — falsified at deep-rank absolute-zero criterion; small effect recovered via Sankoff diagnostic; ecology + phenotype + non-phage mechanism converge on PUL biology",
})

# H2: Mycobacteriota mycolic-acid (Phase 2 NB12)
verdicts.append({
    "hypothesis_id": "H2",
    "hypothesis": "Mycobacteriota → Innovator-Isolated on mycolic-acid pathway",
    "phase": "2 (KO)",
    "atlas_test": "NB12 Mycobacteriaceae × mycolic-acid Innovator-Isolated test at family + order ranks",
    "atlas_effect_size": "producer d=+0.31, consumer d=−0.19",
    "atlas_p_value": "p<10⁻⁶ (Bonferroni-corrected, both ranks)",
    "ecology_grounding": "7.88× host-pathogen biome enrichment (NB23 Fisher's exact)",
    "ecology_p_value": "p < 1e-45",
    "phenotype_anchor": "89.4% aerobic-leaning + Gram-positive 171/172 + non-motile 195/196 + catalase EC 1.11.1.6 at 317/318 (BacDive n=318, NB24)",
    "mge_verdict": "0.57% MGE-machinery (NB26c); chromosomal operons per Marrakchi 2014",
    "d2_residualization": "producer d=0.31 → 0.31; consumer d=−0.19 → −0.16 (preserved, P4-D5)",
    "final_disposition": "SUPPORTED — atlas effect + ecology + phenotype + mechanism all converge",
})

# H3: Cyanobacteria PSII (Phase 3 NB16)
verdicts.append({
    "hypothesis_id": "H3",
    "hypothesis": "Cyanobacteria → Innovator-Exchange on PSII (originally Broker; M25 reframed to Innovator-Exchange donor-undistinguished)",
    "phase": "3 (Pfam architecture)",
    "atlas_test": "NB16 Cyanobacteriia × PSII test at class rank (n_psii_kos_present=21 vs n_ref=554,280)",
    "atlas_effect_size": "producer d=+1.50, consumer d=+0.70",
    "atlas_p_value": "p_producer=2.1e-5, p_consumer=1.83e-4",
    "ecology_grounding": "2.77× photic aquatic biome enrichment (NB23 Fisher's exact)",
    "ecology_p_value": "p < 1e-52",
    "phenotype_anchor": "BacDive coverage too thin (n=4); env-cluster 0 marine+sponge 35.6% concentration (NB25 AlphaEarth)",
    "mge_verdict": "0% MGE-machinery (NB26c); 10.91% gene-neighborhood ≈ Poisson baseline 10.6% (NB26g); not phage-cargo per Cardona 2018",
    "d2_residualization": "producer d=1.50 → 1.50; consumer d=0.70 → 0.63 (preserved, P4-D5)",
    "final_disposition": "SUPPORTED at class rank; rank-dependence noted (genus/family/order STABLE; phylum INNOVATOR-ISOLATED reversal — biological framing: PSII is class-level innovation per Cardona 2018)",
})

# H4: Alm 2006 r ≈ 0.74 reproduction (Phase 2/3/4)
verdicts.append({
    "hypothesis_id": "H4",
    "hypothesis": "Alm 2006 r ≈ 0.74 correlation (HPK count vs LSE fraction) reproduces at GTDB scale",
    "phase": "4 (P4-D3)",
    "atlas_test": "P4-D3 explicit r computation at full GTDB scale (n=18,989 species reps); 4 framings tested",
    "atlas_effect_size": "r = 0.10–0.29 (Pearson) / 0.11–0.33 (Spearman); strongest framing (HPK count vs recent TCS gains at genus rank): r=0.29",
    "atlas_p_value": "p<10⁻⁴³ (statistically significant due to large n; biologically modest)",
    "ecology_grounding": "n/a (this is a correlation reproduction, not a clade enrichment test)",
    "ecology_p_value": "n/a",
    "phenotype_anchor": "n/a; NB17 architectural concordance r=0.67 consumer-side (qualitative result holds at architectural resolution)",
    "mge_verdict": "n/a",
    "d2_residualization": "n/a (correlation, not z-scored test)",
    "final_disposition": "NOT REPRODUCED at GTDB scale; methodology generalization holds (NB17 r=0.67 architectural concordance); point-estimate reproduction does not. Three identified mechanisms: substrate scale dilution (207→18,989 genomes), tree-aware vs paralog-count operationalization, tree-rank granularity",
})

# Bonus: NB11 reframe
verdicts.append({
    "hypothesis_id": "Bonus",
    "hypothesis": "Regulatory vs metabolic Cohen's d ≥ 0.3 asymmetry (originally pre-registered; reframed)",
    "phase": "2 (NB11)",
    "atlas_test": "NB11 Tier-1 regulatory vs metabolic 2-sample tests across atlas",
    "atlas_effect_size": "consumer d=−0.21 (regulatory KOs LOWER consumer scores than metabolic — direction supports complexity hypothesis)",
    "atlas_p_value": "p<10⁻¹⁰",
    "ecology_grounding": "n/a (atlas-wide test, not clade-specific)",
    "ecology_p_value": "n/a",
    "phenotype_anchor": "Independently empirically validated by Burch et al. 2023 (PMID:37232518) at Lactobacillaceae scale, same direction",
    "mge_verdict": "Regulatory KOs show 4.13% MGE-machinery vs metabolic 0.37% (consistent with regulatory products including transposon-bound regulators)",
    "d2_residualization": "consumer d=−0.21 → −0.21 (unchanged, P4-D5)",
    "final_disposition": "REFRAMED — original d ≥ 0.3 falsified; direction-consistent with Jain 1999 complexity hypothesis at small effect size; Burch 2023 independent validation",
})

verdicts_df = pd.DataFrame(verdicts)
verdicts_path = DATA_DIR / "p4_pre_registered_verdicts.tsv"
verdicts_df.to_csv(verdicts_path, sep="\t", index=False)
tprint(f"\n  wrote {verdicts_path} ({len(verdicts_df)} hypotheses × {verdicts_df.shape[1]} cols)")
tprint(f"  hypotheses landed: {verdicts_df['hypothesis_id'].tolist()}")
print()
print(verdicts_df[["hypothesis_id", "atlas_effect_size", "final_disposition"]].to_string(index=False), flush=True)

tprint(f"\n=== Stage 1 DONE in {time.time()-t0:.1f}s ===")
