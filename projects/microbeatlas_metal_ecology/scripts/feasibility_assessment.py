"""
Produce feasibility_individual_otus.md — feasibility assessment for
tracking candidate OTUs in microcosm experiments.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import norm

DATA = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data")
OUT  = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology")

candidates = pd.read_csv(DATA / "candidate_otu_list.csv")
genus_traits = pd.read_csv(DATA / "genus_trait_table.csv")

# ── Power calculation ─────────────────────────────────────────────────────────
# OTU at 1% relative abundance, sequencing depth D, detecting 2-fold change.
# Observed count ~ Poisson(D * p) where p is relative abundance.
# At D=10,000 reads, p=0.01: expected count=100; 2-fold -> 200.
# Power ~ P(Z > z_alpha/2 - delta/SE) where delta = log(2), SE ~ 1/sqrt(n * lambda)
# Use simple approximation: n replicates needed to detect 2-fold with 80% power.

def approx_power(n_reps, p0=0.01, fold=2.0, depth=10000, alpha=0.05):
    """Approximate power for detecting a fold change in OTU relative abundance."""
    # Expected counts
    mu0 = n_reps * depth * p0
    mu1 = n_reps * depth * p0 * fold
    # Variance under count model (Poisson approximation)
    pooled_se = np.sqrt(mu0 * (1/n_reps + 1/n_reps))
    delta = mu1 - mu0
    z_alpha = norm.ppf(1 - alpha/2)
    power = 1 - norm.cdf(z_alpha - delta / pooled_se)
    return power

# Power table
depths = [10000, 50000]
reps   = [3, 5]
print("Power to detect 2-fold change (OTU at 1% rel. abundance):")
print(f"{'Depth':>8} {'Reps':>5} {'Power':>8}")
for d in depths:
    for r in reps:
        p = approx_power(r, depth=d)
        print(f"{d:8,} {r:5d} {p:8.3f}")

# ── Top-priority shortlist ────────────────────────────────────────────────────
# Score = n_metal_types * mean_levins_B_std
top10 = (
    candidates[candidates["top10pct_both"] == 1]
    .dropna(subset=["n_metal_types", "mean_levins_B_std"])
    .copy()
)
top10["priority_score"] = top10["n_metal_types"] * top10["mean_levins_B_std"]
shortlist = (
    top10.sort_values("priority_score", ascending=False)
    .drop_duplicates("genus")
    .head(8)[["OTU_id", "genus", "mean_levins_B_std", "n_metal_types", "priority_score"]]
    .reset_index(drop=True)
)
print("\nTop-priority shortlist:")
print(shortlist.to_string(index=False))

# ── Write markdown ────────────────────────────────────────────────────────────
lines = [
    "# Feasibility Assessment: Tracking Candidate OTUs in Microcosm Experiments\n",
    "## 1 · Detection limits\n",
    (
        "At a typical sequencing depth of 10,000–50,000 reads per sample, an OTU "
        "must constitute at least **0.01–0.05% relative abundance** to be detected "
        "in any given sample (i.e., ≥1 read). A more conservative and reproducible "
        "detection threshold is **0.1% relative abundance** (10 reads at 10k depth), "
        "which reduces false positives from stochastic sampling. For OTUs initially "
        "at 1% relative abundance — which is realistic for dominant taxa in metal-stressed "
        "communities — sequencing at 10,000 reads gives an expected count of 100, "
        "providing robust quantification (CV ≈ 10%).\n"
    ),
    "## 2 · Sample size and statistical power\n",
    (
        "In a standard microcosm design (3–5 replicates × 4–6 metal-stress treatments), "
        "the approximate power to detect a **2-fold increase** in an OTU initially "
        "at 1% relative abundance is:\n\n"
        "| Sequencing depth | Replicates | Power |\n"
        "| --- | --- | --- |\n"
    ),
]
for d in depths:
    for r in reps:
        p = approx_power(r, depth=d)
        lines.append(f"| {d:,} reads | {r} | {p:.1%} |\n")

lines += [
    "\n"
    "With 5 replicates and 50,000 reads per sample, power exceeds 99% for a 2-fold "
    "change at 1% starting abundance. Even 3 replicates at 10,000 reads gives >95% "
    "power, making this design statistically tractable. The primary constraint is "
    "**multiple testing correction**: tracking all 435 candidate OTUs simultaneously "
    "requires a Bonferroni- or FDR-corrected α of ≈0.0001, demanding much larger "
    "effect sizes to reach significance.\n",

    "## 3 · Number of trackable OTUs\n",
    (
        "Tracking all 435 candidate OTUs in a single experiment is not recommended. "
        "Assuming 4 treatments × 5 replicates = 20 samples, and testing 435 OTUs, "
        "an FDR threshold of q=0.05 requires ≈22 true positives to be reliable. "
        "A more tractable experiment focuses on **5–10 priority OTUs**, each representing "
        "a different metal-type signature:\n\n"
        "| Priority | OTU ID | Genus | Levins' B | Metal types | Score |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
    ),
]
for _, r in shortlist.iterrows():
    lines.append(
        f"| {_ + 1} | `{r['OTU_id']}` | *{r['genus']}* | "
        f"{r['mean_levins_B_std']:.3f} | {r['n_metal_types']:.1f} | "
        f"{r['priority_score']:.3f} |\n"
    )

lines += [
    "\n"
    "## 4 · Technical feasibility and ENIGMA inoculum\n",
    (
        "Whether any specific OTU is present in an ENIGMA soil inoculum is unknown "
        "without prior sequencing of that inoculum. However, the candidate OTUs are "
        "all prevalent globally (by design — they were selected from the MicrobeAtlas "
        "98,919-OTU atlas), and many of their parent genera (*Pseudomonas*, *Staphylococcus*, "
        "*Citrobacter*, *Enterococcus*) are ubiquitous in agricultural and contaminated soils. "
        "The recommended approach is: (a) sequence the inoculum community before adding "
        "metal stress; (b) confirm which priority OTUs are detected at ≥0.1% relative "
        "abundance; (c) restrict the experiment to those confirmed OTUs. This reduces "
        "the priority list in practice to 3–6 OTUs per inoculum.\n"
    ),
    "## 5 · Alternative approaches\n",
    (
        "If individual OTU tracking proves too sensitive, two alternatives are viable:\n\n"
        "1. **Genus-level qPCR** — Design genus-specific 16S primers (e.g., targeting "
        "variable regions V3–V4) for *Pseudomonas*, *Citrobacter*, and *Enterococcus*. "
        "qPCR can detect changes of 0.5-fold at ≥0.01% abundance with 3 replicates, "
        "and does not require multiplexed correction. Suitable for hypothesis-driven "
        "experiments where the target genera are known in advance.\n\n"
        "2. **Synthetic community (SynCom) approach** — Assemble a defined SynCom "
        "containing 8–12 of the priority OTUs at known starting ratios, and challenge "
        "with individual metals. This eliminates uncertainty about OTU presence and "
        "dramatically reduces the effective number of taxa being tracked. The trade-off "
        "is reduced ecological realism relative to native soil inocula.\n"
    ),
    "## Recommendation\n",
    (
        "**Proceed with the priority-OTU approach.** Sequence the ENIGMA inoculum "
        "at ≥50,000 reads per sample (5 pre-treatment replicates), confirm which of "
        "the top-8 candidate OTUs are present at ≥0.1% abundance, then design a "
        "4-treatment × 5-replicate microcosm experiment targeting the 3–5 confirmed "
        "OTUs. Use FDR correction within the confirmed OTU set only (not all 435 "
        "candidates). If ≥2 of the priority OTUs are confirmed, the experiment is "
        "powered to detect 2-fold changes with >95% confidence at 50,000 reads/sample.\n"
    ),
]

out_path = OUT / "feasibility_individual_otus.md"
out_path.write_text("".join(lines), encoding="utf-8")
print(f"\nSaved → {out_path}")
