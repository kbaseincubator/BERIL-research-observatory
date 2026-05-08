"""
Produce ENIGMA_PREDICTIONS.md — final combined deliverable.
Assembles: global analysis summary, refined metal resistance table,
testable hypotheses (concise), and feasibility recommendation.
Target: <10 KB, no duplication.
"""

import pandas as pd
from pathlib import Path

DATA = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data")
OUT  = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology")

table = pd.read_csv(DATA / "metal_resistance_table_refined.csv")
candidates = pd.read_csv(DATA / "candidate_otu_list.csv")
pagel = pd.read_csv(DATA / "pagel_lambda_results.csv")

# Pagel lambda for key traits (Bacteria)
bac = pagel[pagel["label"] == "Bacteria"].set_index("trait")
lam_niche = bac.loc["mean_levins_B_std", "lambda"] if "mean_levins_B_std" in bac.index else "N/A"
lam_metal = bac.loc["mean_n_metal_types", "lambda"] if "mean_n_metal_types" in bac.index else "N/A"
lam_nitri = bac.loc["is_nitrifier", "lambda"] if "is_nitrifier" in bac.index else "N/A"

# Shortlist from feasibility (hardcoded to match output)
shortlist = [
    ("97_56843", "Klebsiella",        3.53, "Ag, As, Hg, Te",        "silA/B, arsC, merA/P, tcrB",    "Ag or Te stress"),
    ("97_51587", "Enterococcus",      3.33, "Ag, As, Cd, Cu, Hg, Te","arsD/B, cadC/A, copB/A, merA",  "Cu or Cd stress"),
    ("97_14443", "Citrobacter",       3.70, "Ag, As, Cr, Hg",        "silP/A, arsC/D, chrA, merA/P",  "As or Hg stress"),
    ("97_3668",  "Franconibacter",    3.50, "Ag, As, Hg",            "silP/A, arsC, pcoA/B",          "Ag or As stress"),
    ("97_12431", "Noviherbaspirillum",3.00, "As, Hg",                "arsD, merP, arsN2",             "As stress"),
    ("97_66129", "Serratia",          2.44, "Ag, As, Hg",            "silA/C, arsC/D, merA/P",        "Hg stress"),
    ("97_80244", "Aeromonas",         2.24, "Ag, As, Hg",            "silA/B, arsD/C, merP/A",        "As+Hg co-stress"),
    ("97_39338", "Pseudomonas",       2.13, "Ag, As, Cr, Cu, Hg",    "copA/C, arsD/B, chrA, merP/A",  "Cu stress"),
]

lines = []

# ── Header ────────────────────────────────────────────────────────────────────
lines += [
    "# ENIGMA Metal-Resistance OTU Predictions\n",
    "_MicrobeAtlas Metal Ecology Project · BERIL Research Observatory_\n\n",
    "---\n\n",
]

# ── 1. Global analysis summary ────────────────────────────────────────────────
lines += [
    "## 1. Global analysis summary\n\n",
    "A global meta-analysis of 463,972 16S amplicon samples (98,919 OTUs at 97% identity) "
    "linked to GTDB r214 pangenome metal-AMR annotations reveals that "
    f"**metal-resistance diversity is environmentally labile** (Pagel's λ = {lam_metal:.3f} for "
    "# metal types, Bacteria), while nitrification is strongly phylogenetically conserved "
    f"(λ = {lam_nitri:.3f}). "
    f"Ecological niche breadth shows intermediate signal (λ = {lam_niche:.3f}). "
    "Only 902 of 3,160 genera (29%) carry detectable metal AMR genes; among these, a composite "
    "score (niche breadth × metal diversity) identifies **435 candidate OTUs** spanning 215 in "
    "the top-10% by both metrics and 220 nitrifier positive controls.\n\n",
]

# ── 2. Refined metal resistance table ────────────────────────────────────────
lines += [
    "## 2. Candidate genera — metal resistance summary\n\n",
    "_(Only genera with ≥1 candidate OTU shown; max 15 rows. "
    "Full table: `data/metal_resistance_table_refined.csv`)_\n\n",
    "| Genus | OTUs | Rep. OTU | Metal types | Key genes (≤2 per metal) |\n",
    "| --- | --- | --- | --- | --- |\n",
]
for _, r in table.iterrows():
    genes_short = r["Key_genes"][:80] + "…" if len(str(r["Key_genes"])) > 80 else r["Key_genes"]
    lines.append(
        f"| *{r['Genus']}* | {r['n_candidate_otus']} | `{r['Rep_OTU']}` "
        f"| {r['Metal_types']} | {genes_short} |\n"
    )

# ── 3. Testable hypotheses ────────────────────────────────────────────────────
lines += [
    "\n## 3. Testable hypotheses\n\n",
    "For the 8 highest-priority OTUs (top-scoring by niche breadth × metal-type diversity), "
    "each hypothesis specifies: metal condition, expected direction, representative OTU, and mechanism.\n\n",
]
for otu, genus, n_met, metals, genes, stress in shortlist:
    lines.append(
        f"**{genus}** `{otu}` — Under **{stress}**, relative abundance should increase "
        f"≥2-fold vs. metal-free controls (n_metal_types = {n_met}; metals: {metals}). "
        f"Mechanism: resistance determinants `{genes}` neutralise metal toxicity, creating "
        f"competitive advantage over susceptible community members.\n\n"
    )

# ── 4. Feasibility and design recommendation ──────────────────────────────────
lines += [
    "## 4. Experimental feasibility\n\n",
    "**Detection limit:** ≥0.1% relative abundance (≥10 reads at 10,000 reads/sample). "
    "OTUs at 1% abundance are quantified with CV ≈ 10%; rarer OTUs risk stochastic "
    "dropout and should not be tracked without ≥50,000 reads/sample.\n\n",

    "**Statistical power:** For an OTU at 1% abundance, a 2-fold increase is detectable "
    "with >99% power using 3 replicates at 10,000 reads. The binding constraint is "
    "**multiple testing**: tracking all 435 candidates requires FDR correction that "
    "demands large effects. Restrict tracked OTUs to the pre-confirmed shortlist of 5–10.\n\n",

    "**ENIGMA inoculum:** Sequence inoculum pre-treatment (5 replicates, ≥50,000 reads). "
    "Confirm which of the 8 shortlisted OTUs are detectable at ≥0.1%; restrict experiment "
    "to confirmed OTUs (expected: 3–5). Apply FDR correction within that set only.\n\n",

    "**Recommended design:**\n",
    "- 4–6 metal-stress treatments (single metal + 1 co-contamination control)\n",
    "- 5 replicates per treatment × ≥50,000 reads/sample\n",
    "- 7- and 14-day time points\n",
    "- Primary endpoint: relative abundance fold-change vs. metal-free control\n",
    "- Backup: genus-level qPCR for *Pseudomonas*, *Citrobacter*, *Enterococcus* "
    "if OTU-level tracking fails\n\n",

    "Full feasibility document: `feasibility_individual_otus.md`  \n",
    "Full hypotheses with mechanistic detail: `data/hypotheses_refined.md`  \n",
    "Honorable mentions (no candidate OTUs): `data/honorable_mentions.md`\n",
]

out_path = OUT / "ENIGMA_PREDICTIONS.md"
out_path.write_text("".join(lines), encoding="utf-8")
size_kb = out_path.stat().st_size / 1024
print(f"Saved → {out_path}  ({size_kb:.1f} KB)")
assert size_kb < 10, f"File exceeds 10 KB ({size_kb:.1f} KB)"
print("Size check: OK")
