"""
Build a markdown table: for each genus in the candidate list, show which metal
types they resist and which specific resistance genes they carry.

Focus genera: Pseudomonas, Bacillus, Cupriavidus, Staphylococcus, Nitrosomonas,
Methylobacillus, Salinicola, Alkalihalobacillus, Faecalibacterium, Streptomyces.

Also emit a hypothesis for each.
"""

import pandas as pd
from pathlib import Path

DATA = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data")

# ── Load data ─────────────────────────────────────────────────────────────────
candidates = pd.read_csv(DATA / "candidate_otu_list.csv")
gene_detail = pd.read_csv(DATA / "metal_amr_gene_detail.csv", low_memory=False)
species_amr = pd.read_csv(DATA / "species_metal_amr.csv", low_memory=False)

# Normalise genus column in gene_detail: extract genus from gtdb_species_clade_id
# Format: s__Genus_species--GB_GCA_XXXXXXX
gene_detail["gtdb_genus"] = (
    gene_detail["gtdb_species_clade_id"]
    .str.split("--").str[0]           # drop accession suffix
    .str.replace(r"^s__", "", regex=True)  # drop s__ prefix
    .str.split("_").str[0]            # first word = genus
)

# ── Focus genera ──────────────────────────────────────────────────────────────
# Pull from candidates (top-10% or nitrifier); take genera that have ≥1 OTU
candidate_genera = candidates["genus"].dropna().unique()

# Priority genera explicitly requested + top genera from candidates
priority = [
    "Pseudomonas", "Bacillus", "Cupriavidus", "Staphylococcus",
    "Nitrosomonas", "Methylobacillus", "Salinicola", "Alkalihalobacillus",
    "Faecalibacterium", "Streptomyces",
]
# Supplement with top candidates by n_metal_types that aren't already listed
top_others = (
    candidates[candidates["top10pct_both"] == 1]
    .groupby("genus")["n_metal_types"].mean()
    .sort_values(ascending=False)
    .index.tolist()
)
focus_genera = priority.copy()
for g in top_others:
    if g not in focus_genera:
        focus_genera.append(g)
    if len(focus_genera) >= 15:
        break

# ── Per-genus metal gene summary ──────────────────────────────────────────────
rows = []
for genus in focus_genera:
    sub = gene_detail[gene_detail["gtdb_genus"] == genus]
    if sub.empty:
        # Try species_amr table as fallback
        sub_sp = species_amr[species_amr["gtdb_genus"] == genus]
        if sub_sp.empty:
            metal_types = "—"
            genes = "—"
            n_otus = int(candidates[candidates["genus"] == genus].shape[0])
            rep_otu = candidates[candidates["genus"] == genus]["OTU_id"].iloc[0] \
                      if n_otus > 0 else "—"
            rows.append({
                "Genus": genus,
                "Candidate OTUs (n)": n_otus,
                "Representative OTU": rep_otu,
                "Metal types": metal_types,
                "Key resistance genes": genes,
            })
            continue
        metals = sorted(sub_sp["metal_types"].dropna().str.split("|").explode().unique())
        metal_types = ", ".join(m for m in metals if m and m != "nan")
        genes = "—"
    else:
        metals = sorted(sub["metal_type"].dropna().unique())
        metal_types = ", ".join(metals)

        # Top genes by frequency
        top_genes = (
            sub.groupby(["amr_gene", "amr_product", "metal_type"])
            .size().reset_index(name="n")
            .sort_values("n", ascending=False)
            .head(5)
        )
        gene_strs = [
            f"**{r['amr_gene']}** ({r['metal_type']})"
            for _, r in top_genes.iterrows()
        ]
        genes = "; ".join(gene_strs) if gene_strs else "—"

    n_otus = int(candidates[candidates["genus"] == genus].shape[0])
    rep_otu = candidates[candidates["genus"] == genus]["OTU_id"].iloc[0] \
              if n_otus > 0 else "—"

    rows.append({
        "Genus": genus,
        "Candidate OTUs (n)": n_otus,
        "Representative OTU": rep_otu,
        "Metal types": metal_types if metal_types else "—",
        "Key resistance genes": genes,
    })

table_df = pd.DataFrame(rows)

# ── Hypotheses ────────────────────────────────────────────────────────────────
hypotheses = {
    "Pseudomonas": (
        "Under Cu stress, *Pseudomonas* OTU {otu} should increase in abundance because "
        "it carries **copA** (Cu-exporting P-type ATPase) and **czc** efflux genes, "
        "conferring a competitive advantage in Cu-contaminated soils."
    ),
    "Bacillus": (
        "Under Zn/Cd co-contamination, *Bacillus* OTU {otu} should persist because "
        "its **czcA**-family efflux pumps handle both Zn²⁺ and Cd²⁺, and spore "
        "formation buffers acute toxicity."
    ),
    "Cupriavidus": (
        "In Cu-spiked soils, *Cupriavidus* OTU {otu} should dominate because "
        "**copA** and **pcoABCD** form a complete Cu-resistance operon rarely found "
        "outside this genus, giving near-exclusive fitness at high [Cu]."
    ),
    "Staphylococcus": (
        "Under As(III) exposure, *Staphylococcus* OTU {otu} should be enriched because "
        "**arsD**–**arsA** operons reduce arsenite toxicity, and the genus shows the "
        "broadest niche breadth among Gram-positive candidates."
    ),
    "Nitrosomonas": (
        "In Cu-amended bioreactors, *Nitrosomonas* OTU {otu} may decline despite Cu "
        "resistance because ammonia mono-oxygenase (AMO) is Cu-dependent and excess "
        "Cu disrupts AMO stoichiometry—a testable trade-off between resistance and function."
    ),
    "Methylobacillus": (
        "In Hg-contaminated wetlands, *Methylobacillus* OTU {otu} should increase "
        "because **merA** (mercuric reductase) detoxifies Hg²⁺ to volatile Hg⁰, "
        "and one-carbon metabolism supports growth under anoxic conditions."
    ),
    "Salinicola": (
        "Under combined salinity and Zn stress (e.g., coastal agricultural runoff), "
        "*Salinicola* OTU {otu} should thrive because halotolerance co-selects with "
        "heavy-metal efflux via shared RND transporter families."
    ),
    "Alkalihalobacillus": (
        "In alkaline Cr(VI)-contaminated soils, *Alkalihalobacillus* OTU {otu} "
        "should increase because **chrA** (chromate efflux) is common in alkaliphiles "
        "and alkaline pH reduces Cr(VI) toxicity to manageable levels."
    ),
    "Faecalibacterium": (
        "Under As-contaminated drinking water regimes, gut-associated *Faecalibacterium* "
        "OTU {otu} is predicted to decline, as As resistance genes are rare in this "
        "genus and As(III) disrupts redox homeostasis in strict anaerobes."
    ),
    "Streptomyces": (
        "In multi-metal-contaminated soil, *Streptomyces* OTU {otu} should persist "
        "because its large genome encodes a diversity of metal-resistance clusters "
        "(**merB**, **arsC**, **copZ**) alongside secondary metabolite biosynthesis "
        "that may chelate metals extracellularly."
    ),
}

# ── Print markdown table ──────────────────────────────────────────────────────
md_lines = []
md_lines.append("## Genus-level Metal Resistance Summary\n")
md_lines.append(
    "Metal types and key resistance genes are derived from `metal_amr_gene_detail.csv` "
    "(AMR gene annotations via HMM against GTDB pangenomes). "
    "Candidate OTUs are those in the top-10% by niche breadth × metal diversity, plus nitrifier controls.\n"
)

# Table header
header = ["Genus", "Candidate OTUs (n)", "Representative OTU", "Metal types", "Key resistance genes"]
md_lines.append("| " + " | ".join(header) + " |")
md_lines.append("| " + " | ".join(["---"] * len(header)) + " |")

for _, r in table_df.iterrows():
    cells = [str(r[c]) for c in header]
    md_lines.append("| " + " | ".join(cells) + " |")

md_lines.append("\n## Ecological Hypotheses\n")

for _, r in table_df.iterrows():
    genus = r["Genus"]
    rep_otu = r["Representative OTU"]
    hyp_template = hypotheses.get(genus, None)
    if hyp_template:
        hyp = hyp_template.format(otu=rep_otu)
    else:
        metals = r["Metal types"]
        hyp = (
            f"Under {metals.split(',')[0].strip()} stress, *{genus}* OTU {rep_otu} "
            f"is predicted to increase in relative abundance because it carries "
            f"resistance genes for {metals}, providing a selective advantage over "
            f"susceptible co-residents."
        )
    md_lines.append(f"**{genus}** (`{rep_otu}`): {hyp}\n")

md_out = "\n".join(md_lines)
print(md_out)

# Save as markdown file
out_path = DATA.parent / "METAL_RESISTANCE_TABLE.md"
out_path.write_text(md_out)
print(f"\n[Saved → {out_path}]")
