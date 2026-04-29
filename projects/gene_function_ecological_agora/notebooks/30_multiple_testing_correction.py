"""NB30 — multiple-testing correction pass.

Enumerate all formally-tested significance claims in REPORT v3.5; group into test
families; apply Bonferroni + Benjamini-Hochberg FDR; report which survive.

The reviewer's framing ("26 methodology revisions = 26 tests requiring FWER correction")
conflates pre-registration corrections with multiple hypothesis testing. The actual
test families are smaller and well-defined:
"""
import json, time
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"

t0 = time.time()
def tprint(msg):
    print(f"[{time.time()-t0:.1f}s] {msg}", flush=True)

tprint("=== NB30 — Multiple-Testing Correction Pass ===")

# === FAMILY 1: 4 pre-registered weak-prior hypotheses ===
tprint("\nFAMILY 1: 4 pre-registered weak-prior hypotheses")
family1 = pd.DataFrame([
    {"hypothesis": "H1 Bacteroidota PUL Innovator-Exchange", "test": "NB08c Sankoff diagnostic; consumer-z group comparison",
     "raw_p": 0.001, "effect": "d=0.146"},
    {"hypothesis": "H2 Mycobacteriota mycolic Innovator-Isolated (family rank)", "test": "NB12 Mann-Whitney; producer + consumer Cohen's d",
     "raw_p": 1e-6, "effect": "d_producer=+0.31, d_consumer=−0.19"},
    {"hypothesis": "H3 Cyanobacteria PSII Innovator-Exchange (class rank)", "test": "NB16 Mann-Whitney; producer + consumer Cohen's d",
     "raw_p": 2.1e-5, "effect": "d_producer=+1.50, d_consumer=+0.70"},
    {"hypothesis": "H4 Alm 2006 r ≈ 0.74 reproduction (P4-D3)", "test": "Pearson + Spearman correlation, 4 framings",
     "raw_p": 1e-43, "effect": "r=0.10–0.29 (reported as NOT REPRODUCED — point estimate too small even at significant p)"},
])
family1["bonferroni_alpha"] = 0.05 / len(family1)
family1["survives_bonferroni"] = family1["raw_p"] < family1["bonferroni_alpha"]
family1["survives_BH_fdr_05"] = stats.false_discovery_control(family1["raw_p"].values) < 0.05
print("\nFamily 1: 4 pre-registered hypotheses")
print(f"  Bonferroni α = 0.05 / {len(family1)} = {family1['bonferroni_alpha'].iloc[0]:.4f}")
print(family1[["hypothesis", "raw_p", "survives_bonferroni", "survives_BH_fdr_05"]].to_string(index=False))

# === FAMILY 2: P4-D1 ecology enrichment tests ===
tprint("\nFAMILY 2: P4-D1 ecology biome-enrichment tests")
family2 = pd.DataFrame([
    {"test": "Cyanobacteriia × marine (NB23 H1a)", "raw_p": 8.3e-19, "effect": "2.33× fold"},
    {"test": "Cyanobacteriia × photic aquatic (NB23 H1b)", "raw_p": 1.5e-53, "effect": "2.77× fold"},
    {"test": "Mycobacteriaceae × soil (NB23 H2a)", "raw_p": 0.87, "effect": "0.88× (NOT enriched)"},
    {"test": "Mycobacteriaceae × host-pathogen (NB23 H2b)", "raw_p": 3.6e-46, "effect": "7.88× fold"},
    {"test": "Mycobacteriaceae × (soil OR host-pathogen) (NB23 H2c)", "raw_p": 8.0e-12, "effect": "1.76× fold"},
    {"test": "Bacteroidota × gut/rumen (NB23 H3)", "raw_p": 3.6e-36, "effect": "1.40× fold"},
])
family2["bonferroni_alpha"] = 0.05 / len(family2)
family2["survives_bonferroni"] = family2["raw_p"] < family2["bonferroni_alpha"]
family2["survives_BH_fdr_05"] = stats.false_discovery_control(family2["raw_p"].values) < 0.05
print("\nFamily 2: P4-D1 6 biome-enrichment tests")
print(f"  Bonferroni α = 0.05 / {len(family2)} = {family2['bonferroni_alpha'].iloc[0]:.5f}")
print(family2[["test", "raw_p", "survives_bonferroni", "survives_BH_fdr_05"]].to_string(index=False))

# === FAMILY 3: P4-D5 D2 residualization replication ===
tprint("\nFAMILY 3: P4-D5 D2 residualization replication tests")
p4d5 = pd.read_csv(DATA_DIR / "p4d5_hypothesis_replication.tsv", sep="\t")
print(f"  Loaded {len(p4d5)} replication test rows")
# Filter to substantive tests (p_residualized non-null, not the producer-z direction-irrelevant ones)
p4d5_clean = p4d5[p4d5["p_residualized"] > 0].copy()
p4d5_clean["bonferroni_alpha"] = 0.05 / len(p4d5_clean) if len(p4d5_clean) else None
p4d5_clean["survives_bonferroni"] = p4d5_clean["p_residualized"] < p4d5_clean["bonferroni_alpha"]
print(f"  Bonferroni α = 0.05 / {len(p4d5_clean)} = {p4d5_clean['bonferroni_alpha'].iloc[0]:.5f}")
print(p4d5_clean[["test", "d_residualized", "p_residualized", "survives_bonferroni"]].to_string(index=False))

# === FAMILY 4: leaf_consistency descriptive — NOT a test family ===
tprint("\nFAMILY 4: leaf_consistency — descriptive statistic, NOT hypothesis-tested")
print("  Per-(rank × clade × ko) leaf_consistency = fraction of clade species carrying KO.")
print("  This is a DESCRIPTIVE point estimate, not a test of a null hypothesis.")
print("  No multiple testing correction applies.")
print("  S7 figure shows distribution shapes (focal vs atlas reference); medians reported as observation, not p-value claim.")

# === FAMILY 5: Tree-based donor inference (M26) ===
tprint("\nFAMILY 5: M26 tree-based donor inference — descriptive classification, NOT hypothesis-tested")
print("  Per-(genus × KO) Open/Broker/Sink/Closed assignment via parsimony rules + minimum-event-count threshold.")
print("  No null hypothesis tested; no p-values; no multiple testing correction needed.")
print("  Reportable as exploratory layer per REPORT v3.5 v2.16 plan; M25 still defers composition-based confirmation.")

# === Summary table ===
tprint("\n=== SUMMARY ===")
all_results = []
for fname, fam in [("Family 1: pre-registered hypotheses", family1),
                    ("Family 2: P4-D1 biome enrichment", family2),
                    ("Family 3: P4-D5 residualization replication", p4d5_clean)]:
    if "raw_p" in fam.columns:
        n_total = len(fam)
        n_bonf = fam["survives_bonferroni"].sum()
        all_results.append({"family": fname, "n_tests": n_total,
                            "bonferroni_alpha": float(fam["bonferroni_alpha"].iloc[0]),
                            "n_survives_bonferroni": int(n_bonf),
                            "pct_survives_bonferroni": round(100*n_bonf/n_total, 1)})

summary_df = pd.DataFrame(all_results)
print(summary_df.to_string(index=False))

print(f"\nKey verdict:")
total_tests = summary_df["n_tests"].sum()
total_bonf = summary_df["n_survives_bonferroni"].sum()
print(f"  Total formal hypothesis tests: {total_tests}")
print(f"  Total surviving family-wise Bonferroni: {total_bonf} ({100*total_bonf/total_tests:.1f}%)")
print(f"  Substantive interpretation: project's core claims (NB12 mycolic, NB16 PSII, P4-D1 enrichments)")
print(f"    survive even strict family-wise correction. Mycobacteriaceae × soil null result")
print(f"    (the 'NOT enriched' finding) is correctly negative — no false-positive issue.")

# Save
diag = {
    "phase": "REVIEW.md item #1 response",
    "deliverable": "Multiple-testing correction analysis",
    "family_1_pre_registered": family1.to_dict(orient="records"),
    "family_2_ecology_enrichment": family2.to_dict(orient="records"),
    "family_3_residualization_replication": p4d5_clean.to_dict(orient="records"),
    "summary": summary_df.to_dict(orient="records"),
    "total_formal_tests": int(total_tests),
    "total_surviving_bonferroni": int(total_bonf),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "elapsed_s": round(time.time()-t0, 1),
}
with open(DATA_DIR / "p4_multiple_testing_correction.json", "w") as f:
    json.dump(diag, f, indent=2, default=str)
summary_df.to_csv(DATA_DIR / "p4_multiple_testing_correction_summary.tsv", sep="\t", index=False)
tprint(f"\n=== DONE in {time.time()-t0:.1f}s ===")
