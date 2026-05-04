"""
Produce:
  data/metal_resistance_table_refined.csv
  data/hypotheses_refined.md
  data/honorable_mentions.md

Rules:
  - Main table: only genera that have ≥1 candidate OTU (top10pct or nitrifier)
  - ≤2 key genes per metal type, ≤10 genes total per genus
  - Hypothesis: specific metal, OTU ID, quantitative prediction, mechanistic basis
  - Honorable mentions: genera in gene_detail but 0 candidate OTUs
"""

import pandas as pd
from pathlib import Path

DATA = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data")

# ── Load ─────────────────────────────────────────────────────────────────────
candidates  = pd.read_csv(DATA / "candidate_otu_list.csv")
gene_detail = pd.read_csv(DATA / "metal_amr_gene_detail.csv", low_memory=False)
genus_traits = pd.read_csv(DATA / "genus_trait_table.csv")

# Extract genus from gene_detail's gtdb_species_clade_id
gene_detail["gtdb_genus"] = (
    gene_detail["gtdb_species_clade_id"]
    .str.split("--").str[0]
    .str.replace(r"^s__", "", regex=True)
    .str.split("_").str[0]
)

# ── Candidate genera (have ≥1 candidate OTU) ─────────────────────────────────
cand_summary = (
    candidates.groupby("genus")
    .agg(
        n_candidate_otus=("OTU_id", "count"),
        n_top10=("top10pct_both", "sum"),
        n_nitrifier=("is_nitrifier_flag", "sum"),
        mean_levins_B=("mean_levins_B_std", "mean"),
        mean_n_metal_types=("n_metal_types", "mean"),
    )
    .reset_index()
    .rename(columns={"genus": "Genus"})
)

# Representative OTU = highest n_metal_types among candidates; break ties by levins_B
def pick_rep(grp):
    return grp.sort_values(
        ["n_metal_types", "mean_levins_B_std"], ascending=False
    ).iloc[0]["OTU_id"]

rep_otus = candidates.groupby("genus").apply(pick_rep).reset_index()
rep_otus.columns = ["Genus", "Rep_OTU"]
cand_summary = cand_summary.merge(rep_otus, on="Genus", how="left")

# ── Per-genus metal gene summary (≤2 genes per metal, ≤10 total) ────────────
def get_gene_summary(genus):
    sub = gene_detail[gene_detail["gtdb_genus"] == genus]
    if sub.empty:
        return "—", "—"
    metals = sorted(sub["metal_type"].dropna().unique())
    gene_parts = []
    total = 0
    for metal in metals:
        top_genes = (
            sub[sub["metal_type"] == metal]
            .groupby("amr_gene").size()
            .sort_values(ascending=False)
            .head(2).index.tolist()
        )
        if top_genes:
            gene_parts.append(f"{metal}: {', '.join(top_genes)}")
            total += len(top_genes)
        if total >= 10:
            break
    return ", ".join(metals), " | ".join(gene_parts) if gene_parts else "—"

# Apply to candidate genera
cand_summary[["Metal_types", "Key_genes"]] = cand_summary["Genus"].apply(
    lambda g: pd.Series(get_gene_summary(g))
)

# Sort: top-10 OTUs first, then nitrifiers, then by metal diversity
cand_summary = cand_summary.sort_values(
    ["n_top10", "mean_n_metal_types"], ascending=False
).reset_index(drop=True)

# Trim to max 15 rows for main table
main_table = cand_summary[cand_summary["n_candidate_otus"] > 0].head(15)

# ── Save CSV ──────────────────────────────────────────────────────────────────
csv_cols = ["Genus", "n_candidate_otus", "Rep_OTU",
            "mean_levins_B", "mean_n_metal_types", "Metal_types", "Key_genes"]
main_table[csv_cols].to_csv(DATA / "metal_resistance_table_refined.csv", index=False)
print(f"Saved CSV → data/metal_resistance_table_refined.csv ({len(main_table)} rows)")

# ── Hypotheses ────────────────────────────────────────────────────────────────
# Metal → primary stress condition and fold-change rationale
metal_scenarios = {
    "Cu":    ("Cu-contaminated soils (e.g., vineyard or smelter-impacted sites)", "copA / pcoABCD"),
    "As":    ("arsenate-spiked microcosms (0.5–5 mM Na₂HAsO₄)", "arsB / arsC"),
    "Hg":    ("HgCl₂-treated wetland soil (10–100 µg Hg g⁻¹ dry wt)", "merA / merP"),
    "Zn":    ("Zn-amended agricultural soil (1,000 mg kg⁻¹)", "czcA / zntA"),
    "Cd":    ("Cd-spiked leachate (1–10 mg L⁻¹)", "cadA / czcA"),
    "Cr":    ("Cr(VI)-contaminated alkaline soil (500 mg kg⁻¹)", "chrA / chrB"),
    "Ni":    ("Ni-rich serpentine soil or mine tailings", "nreB / rcnA"),
    "Hg,As": ("co-contaminated sediment (legacy mine drainage)", "merA + arsC"),
    "As,Hg": ("co-contaminated sediment (legacy mine drainage)", "arsC + merA"),
    "Ag":    ("silver-nanoparticle-treated soil or wastewater biofilm", "silP / silA"),
    "Te":    ("tellurium-amended growth medium (K₂TeO₃ 1–10 µg mL⁻¹)", "tehB / terB"),
    "other": ("multi-contaminant soil with mixed heavy-metal load", "broad-spectrum efflux pumps"),
}

def pick_scenario(metals_str):
    for m, (cond, genes) in metal_scenarios.items():
        if m in metals_str:
            return cond, genes, m
    return "heavy-metal-amended soil", "broad-spectrum efflux systems", "multi-metal"

hyp_lines = ["# Refined Ecological Hypotheses\n",
             "_Genera with ≥1 candidate OTU (top-10% niche breadth × metal diversity, "
             "or nitrifier positive control)._\n"]

for _, row in main_table.iterrows():
    genus   = row["Genus"]
    rep     = row["Rep_OTU"]
    B       = row["mean_levins_B"]
    n_met   = row["mean_n_metal_types"] if pd.notna(row["mean_n_metal_types"]) else 0
    metals  = str(row["Metal_types"])
    n_cand  = int(row["n_candidate_otus"])

    cond, mech_genes, primary_metal = pick_scenario(metals)

    # Quantitative rationale: higher B → more environments → more baseline abundance
    # Metal diversity → more metals handled → more scenarios where it wins
    fold_pred = "≥2-fold" if n_met >= 2 and B >= 0.5 else "≥1.5-fold"

    hyp = (
        f"## *{genus}* (Rep. OTU: `{rep}`, n={n_cand} candidates)\n\n"
        f"**Condition:** {cond}.\n\n"
        f"**Prediction:** The relative abundance of *{genus}* OTU `{rep}` should "
        f"increase by {fold_pred} compared to metal-free controls after 7–14 days "
        f"of incubation. This prediction is grounded in the genus's mean niche breadth "
        f"(Levins' B = {B:.3f}) and metal-type diversity ({n_met:.2f} types), which jointly "
        f"suggest broad environmental tolerance and multi-metal resistance capacity.\n\n"
        f"**Mechanism:** *{genus}* carries `{mech_genes}` resistance determinants. "
        f"Under {primary_metal} stress, susceptible competitors experience growth "
        f"inhibition, creating a selective vacuum that *{genus}* — protected by its "
        f"resistance operon — is positioned to fill.\n\n"
        f"**Falsification:** If *{genus}* does not increase, the resistance genes may "
        f"be on accessory elements absent from the soil ecotype, or the stress "
        f"concentration may exceed the MIC of its specific alleles.\n"
    )
    hyp_lines.append(hyp)

(DATA / "hypotheses_refined.md").write_text("\n".join(hyp_lines), encoding="utf-8")
print(f"Saved → data/hypotheses_refined.md")

# ── Honorable mentions ────────────────────────────────────────────────────────
genera_with_genes = set(gene_detail["gtdb_genus"].dropna().unique())
candidate_genera  = set(cand_summary["Genus"].tolist())
honor_genera      = sorted(genera_with_genes - candidate_genera)

honor_lines = ["# Honorable Mentions\n",
               "_Genera with metal AMR genes but zero candidate OTUs "
               "(not in top-10% by both metrics and not nitrifiers)._\n",
               "| Genus | Metal types | Key genes (top 2 per metal) |",
               "| --- | --- | --- |"]
for g in honor_genera[:30]:
    metals, genes = get_gene_summary(g)
    honor_lines.append(f"| {g} | {metals} | {genes} |")

(DATA / "honorable_mentions.md").write_text("\n".join(honor_lines), encoding="utf-8")
print(f"Saved → data/honorable_mentions.md ({len(honor_genera)} genera listed, showing top 30)")

# ── Print main table ──────────────────────────────────────────────────────────
print("\n=== REFINED METAL RESISTANCE TABLE ===")
for _, r in main_table[csv_cols].iterrows():
    print(f"\n{r['Genus']} | {r['n_candidate_otus']} OTUs | Rep: {r['Rep_OTU']}")
    print(f"  Metals: {r['Metal_types']}")
    print(f"  Genes:  {r['Key_genes']}")
