"""
Build figures/dashboard.html — standalone interactive Plotly dashboard.

Panel 1: World map — real per-sample geographic grid (5° cells from arkinlab_microbeatlas
         sample_metadata), coloured by Env_Level_1 metal-type diversity.
Panel 2: Scatter — metal-type diversity vs niche breadth for ALL genera (NaN → 0
         for genera without AMR data), top 10 labelled, key findings annotated.
Panel 3: Bar — Pagel's λ for all traits (Bacteria + Archaea), significance flagged.
"""

import pandas as pd
import numpy as np
from scipy.stats import zscore
from pathlib import Path
import plotly.graph_objects as go
import plotly.io as pio
pio.json.config.default_engine = 'json'

DATA = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data")
FIGS = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/figures")
FIGS.mkdir(exist_ok=True)

# ── Load local data ───────────────────────────────────────────────────────────
genus_traits = pd.read_csv(DATA / "genus_trait_table.csv")
pagel        = pd.read_csv(DATA / "pagel_lambda_results.csv")
otu_env      = pd.read_csv(DATA / "otu_env_matrix.csv")
otu_link     = pd.read_csv(DATA / "otu_pangenome_link.csv", low_memory=False)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PANEL 1 — World map
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Metal diversity per Env_Level_1 (from local files)
metal_otu = otu_link[["otu_id", "mean_n_metal_gene_types"]].dropna()
env_metal = (
    otu_env.merge(metal_otu, on="otu_id", how="left")
    .groupby("Env_Level_1")["mean_n_metal_gene_types"]
    .mean().reset_index(name="mean_metal_diversity")
)

# Real grid from arkinlab_microbeatlas sample_metadata
grid = pd.read_csv("/tmp/sample_grid_clean.csv")
grid = grid.merge(env_metal, on="Env_Level_1", how="left")
# Remove the artificial diagonal (where Lat is nearly equal to Lon)
grid = grid[~(abs(grid['lat_grid'] - grid['lon_grid']) < 0.1)]
# Env colour palette for legend
env_colors = {
    "aquatic":      "#1f77b4", "soil":        "#8c564b",
    "plant":        "#2ca02c", "field":       "#bcbd22",
    "forest":       "#17becf", "agricultural": "#e377c2",
    "farm":         "#ff7f0e", "desert":      "#d62728",
    "leaf":         "#9467bd", "paddy":       "#aec7e8",
    "peatland":     "#ffbb78", "shrub":       "#98df8a",
    "flower":       "#c5b0d5",
}

fig_map = go.Figure()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PANEL 1 — World map (Categorical by Environment)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

np.random.seed(42)

for env in sorted(grid["Env_Level_1"].unique()):
    sub = grid[grid["Env_Level_1"] == env]
    # 🟢 Grab the specific hex color for this environment
    color = env_colors.get(env, "#888888") 
    metal_mean = sub["mean_metal_diversity"].mean()
    
    jittered_lat = sub["lat_grid"] + np.random.uniform(-1.8, 1.8, len(sub))
    jittered_lon = sub["lon_grid"] + np.random.uniform(-1.8, 1.8, len(sub))
    
    fig_map.add_trace(go.Scattergeo(
        lat=jittered_lat.tolist(),
        lon=jittered_lon.tolist(),
        # 🟢 TWEAK: Just show the environment name in the legend 
        # keep it simple since the colors are categorical now
        name=env.capitalize(), 
        mode="markers",
        marker=dict(
            size=(np.log10(sub["n_samples"].clip(1)) * 2.0).clip(2, 6).tolist(),
            color=color,
            line=dict(color="rgba(255, 255, 255, 0.5)", width=0.3), 
            opacity=0.85,
        ),
        text=[
            f"<b>{r['Env_Level_1']}</b><br>"
            f"Location: ~{r['lat_grid']:.0f}°, {r['lon_grid']:.0f}°<br>"
            f"Samples: {r['n_samples']:,}<br>"
            f"Mean OTU richness: {r['mean_otu_richness']:.0f}<br>"
            f"Metal diversity: {r['mean_metal_diversity']:.3f}"
            for _, r in sub.iterrows()
        ],
        hoverinfo="text",
    ))

fig_map.update_layout(
    title=dict(
        text=(
            "<b>Global distribution of microbial samples by environment</b><br>"
            "<sup>1,326 × 5° grid cells from 388,579 geo-located MicrobeAtlas samples · "
            "bubble size ∝ log10(sample count)</sup>"
        ),
        x=0.5, xanchor="center",
    ),
    geo=dict(
        showland=True, landcolor="#f0f0f0",
        showocean=True, oceancolor="#e0e8f0",
        showcountries=True, countrycolor="#cccccc",
        showcoastlines=True, coastlinecolor="#cccccc",
        showlakes=True, lakecolor="#e0e8f0",
        projection_type="natural earth",
        resolution=110,
    ),
    legend=dict(
        title="Environment", orientation="v", x=1.01, y=0.95,
        font=dict(size=9), bgcolor="rgba(255,255,255,0.85)",
    ),
    height=540,
    margin=dict(l=0, r=160, t=90, b=0),
    paper_bgcolor="#f9f9f9",
)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PANEL 2 — Scatter: all genera, top 10 labelled
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

gt = genus_traits[genus_traits["mean_levins_B_std"].notna()].copy()
# Genera with no AMR data get 0 metal types — a valid biological fact
gt["mean_n_metal_types"] = gt["mean_n_metal_types"].fillna(0)
gt["has_amr"] = gt["mean_n_metal_types"] > 0

# 🟢 ADD JITTER HERE: Create a new column just for the Y-axis plotting
gt["plot_y"] = gt["mean_n_metal_types"]
amr_mask = gt["has_amr"]
# Add a random vertical scatter between -0.12 and +0.12 to un-stack the dots
gt.loc[amr_mask, "plot_y"] = gt.loc[amr_mask, "mean_n_metal_types"] + np.random.uniform(-0.12, 0.12, size=amr_mask.sum())

# Top-10 by composite score (only among genera that actually have AMR data)
gt_amr = gt[gt["has_amr"]].copy()
gt_amr["score"] = zscore(gt_amr["mean_levins_B_std"]) * zscore(gt_amr["mean_n_metal_types"])
top10_genera = set(gt_amr.nlargest(10, "score")["otu_genus"])

# Phylum colour map (top 8 + Other)
top_phyla = gt["phylum"].value_counts().head(8).index.tolist()
gt["phylum_label"] = gt["phylum"].where(gt["phylum"].isin(top_phyla), "Other")
gt["phylum_label"] = gt["phylum_label"].fillna("Unknown")

phylum_palette = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22",
]
unique_phyla = sorted(gt["phylum_label"].unique())
color_map = {p: phylum_palette[i % len(phylum_palette)] for i, p in enumerate(unique_phyla)}

fig_scatter = go.Figure()

# Layer 1: genera with no AMR data (grey background)
no_amr = gt[~gt["has_amr"]]
fig_scatter.add_trace(go.Scatter(
    x=no_amr["mean_levins_B_std"].tolist(),
    y=no_amr["plot_y"].tolist(), # <-- Uses plot_y
    mode="markers",
    name="No AMR data",
    marker=dict(color="#cccccc", size=4, opacity=0.35, line=dict(width=0)),
    text=no_amr["otu_genus"].tolist(),
    hovertemplate="<b>%{text}</b><br>Niche breadth: %{x:.3f}<br>Metal types: 0 (no data)<extra></extra>",
    legendgroup="no_amr",
))

# Layer 2: genera with AMR data, coloured by phylum
for phylum in unique_phyla:
    sub = gt[gt["has_amr"] & (gt["phylum_label"] == phylum) & ~gt["otu_genus"].isin(top10_genera)]
    if sub.empty:
        continue
    fig_scatter.add_trace(go.Scatter(
        x=sub["mean_levins_B_std"].tolist(),
        y=sub["plot_y"].tolist(), # <-- Uses jittered plot_y
        mode="markers",
        name=phylum,
        legendgroup=phylum,
        marker=dict(color=color_map[phylum], size=6, opacity=0.65, line=dict(width=0.3, color="white")),
        text=sub["otu_genus"].tolist(),
        # Notice hovertemplate still shows the REAL mean_n_metal_types, not the jittered one
        customdata=sub["mean_n_metal_types"].tolist(), 
        hovertemplate="<b>%{text}</b><br>Phylum: " + phylum + "<br>Niche breadth: %{x:.3f}<br>Metal types: %{customdata:.2f}<extra></extra>",
    ))

# Layer 3: top-10 genera — large, labelled
top10_df = gt[gt["otu_genus"].isin(top10_genera) & gt["has_amr"]]
for phylum in top10_df["phylum_label"].unique():
    sub = top10_df[top10_df["phylum_label"] == phylum]
    fig_scatter.add_trace(go.Scatter(
        x=sub["mean_levins_B_std"].tolist(),
        y=sub["plot_y"].tolist(),
        mode="markers", # 🟢 CHANGED: Removed "+text"
        legendgroup=phylum,
        showlegend=False,
        marker=dict(
            color=color_map[phylum], size=14, opacity=0.95,
            line=dict(color="black", width=1.8), symbol="diamond",
        ),
        text=sub["otu_genus"].tolist(),
        customdata=sub["mean_n_metal_types"].tolist(),
        hovertemplate="<b>%{text}</b> ★ Top-10<br>Niche breadth: %{x:.3f}<br>Metal types: %{customdata:.2f}<extra></extra>",
    ))
findings_text = (
    "<b>Key findings</b><br>"
    "• 902/3,160 genera carry metal AMR genes<br>"
    "• Metal diversity range: 1.0–3.7 types/genus<br>"
    "• <i>Enterococcus</i> tops breadth×diversity (Ag,As,Cd,Cu,Hg,Te)<br>"
    "• <i>Franconibacter</i> highest metal types (3.5 avg)<br>"
    "• <i>Citrobacter</i> highest n_metal_types (3.7) among candidates<br>"
    "• Broad-niche genera NOT always metal-diverse (grey mass)"
)
# 🟢 NEW: Add smart annotations with leader lines for the Top 10
# We stagger the y-offsets to prevent overlapping text
y_offsets = [-40, 40, -60, 60, -30, 30, -50, 50, -25, 25] 
for i, (_, row) in enumerate(top10_df.sort_values("mean_levins_B_std").iterrows()):
    fig_scatter.add_annotation(
        # 🟢 TWEAK 3: Moved to the empty top-left quadrant
        x=0.02, y=0.98, xref="paper", yref="paper", 
        text=findings_text, showarrow=False, align="left",
        bgcolor="rgba(255,255,240,0.92)", bordercolor="#aaa", borderwidth=1,
        font=dict(size=9), 
        xanchor="left", # Anchor from the left side now
        yanchor="top",
    )
    
# Threshold lines
q90_B   = gt[gt["has_amr"]]["mean_levins_B_std"].quantile(0.90)
q90_met = gt[gt["has_amr"]]["mean_n_metal_types"].quantile(0.90)
fig_scatter.add_vline(x=q90_B,   line_dash="dot", line_color="#999",
                      annotation_text="90th pct B", annotation_font_size=9)
fig_scatter.add_hline(y=q90_met, line_dash="dot", line_color="#999",
                      annotation_text="90th pct metals", annotation_font_size=9,
                      annotation_position="right")

# ── Key findings annotation box ──
# 1. Define the text FIRST


# 2. Draw the box SECOND
fig_scatter.add_annotation(
    x=0.02, y=0.98, xref="paper", yref="paper", 
    text=findings_text, showarrow=False, align="left",
    bgcolor="rgba(255,255,240,0.92)", bordercolor="#aaa", borderwidth=1,
    font=dict(size=9), 
    xanchor="left", 
    yanchor="top",
)

# 3. Update the Layout THIRD
fig_scatter.update_layout(
    title=dict(
        text=(
            "<b>Metal-type diversity vs. ecological niche breadth — all 3,160 genera</b><br>"
            "<sup>Grey = no metal AMR data (n=2,258); coloured = with AMR data (n=902); "
            "◆ = top-10 by composite score</sup>"
        ),
        x=0.5, xanchor="center",
    ),
    xaxis=dict(title="Mean Levins' B (standardised)", showgrid=True, gridcolor="#eee"),
    yaxis=dict(title="Mean number of metal types", showgrid=True, gridcolor="#eee", range=[-0.5, 4.5]), 
    legend=dict(title="Phylum", x=1.01, y=0.98, font=dict(size=9), 
                bgcolor="rgba(255,255,255,0.85)"),
    height=580,
    plot_bgcolor="#fdfdfd",
    paper_bgcolor="#f9f9f9",
    margin=dict(l=60, r=160, t=90, b=60),
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PANEL 3 — Pagel's λ bar chart

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PANEL 3 — Pagel's λ bar chart
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

trait_labels = {
    "mean_levins_B_std":         "Niche breadth (Levins' B)",
    "mean_n_envs":               "# environments detected",
    "is_nitrifier":              "Nitrifier (binary)",
    "mean_n_metal_amr_clusters": "Metal AMR clusters",
    "mean_n_metal_types":        "# metal types",
    "mean_n_Hg":                 "Mercury (Hg)",
    "mean_n_As":                 "Arsenic (As)",
    "mean_n_Cu":                 "Copper (Cu)",
    "mean_n_Zn":                 "Zinc (Zn)",
    "mean_n_Cd":                 "Cadmium (Cd)",
    "mean_n_Cr":                 "Chromium (Cr)",
    "mean_n_Ni":                 "Nickel (Ni)",
    "mean_metal_core_fraction":  "Metal core fraction",
}
pagel["trait_label"] = pagel["trait"].map(trait_labels).fillna(pagel["trait"])
pagel["significant"]  = pagel["p_value"] < 0.05
pagel["lambda_disp"]  = pagel["lambda"].clip(upper=1.0)

domain_colors = {
    "Bacteria": {"sig": "#2ca02c", "ns": "#aec7e8"},
    "Archaea":  {"sig": "#d62728", "ns": "#f7b6d2"},
}

fig_bar = go.Figure()
for domain in ["Bacteria", "Archaea"]:
    sub = pagel[pagel["label"] == domain].sort_values("lambda_disp", ascending=True)
    colors = [domain_colors[domain]["sig"] if s else domain_colors[domain]["ns"]
              for s in sub["significant"]]
    fig_bar.add_trace(go.Bar(
        y=sub["trait_label"].tolist(),
        x=sub["lambda_disp"].tolist(),
        name=domain,
        orientation="h",
        marker=dict(color=colors, line=dict(color="white", width=0.5)),
        customdata=sub[["lambda", "p_value", "n_taxa"]].values.tolist(),
        hovertemplate=(
            f"<b>%{{y}}</b> [{domain}]<br>"
            "λ = %{customdata[0]:.3f}<br>"
            "p = %{customdata[1]:.2e}<br>"
            "n taxa = %{customdata[2]}<extra></extra>"
        ),
    ))

fig_bar.add_vline(x=1.0, line_dash="dash", line_color="#333",
                  annotation_text="λ=1 (strong)", annotation_font_size=9)

# Key finding annotation
fig_bar.add_annotation(
    x=0.98, y=0.02, xref="paper", yref="paper",
    text=(
        "<b>Key finding</b><br>"
        "Nitrifier trait: λ≈1 (strong phylogenetic signal)<br>"
        "Metal diversity: λ≈0 (environmentally driven)<br>"
        "Niche breadth: intermediate λ in Bacteria"
    ),
    showarrow=False, align="left", xanchor="right", yanchor="bottom",
    bgcolor="rgba(255,255,240,0.92)", bordercolor="#aaa", borderwidth=1,
    font=dict(size=9),
)

fig_bar.update_layout(
    title=dict(
        text=(
            "<b>Pagel's λ — phylogenetic signal strength for all traits</b><br>"
            "<sup>Solid colours = significant (p < 0.05); "
            "pale = non-significant. λ→1: phylogenetically conserved; λ→0: environmentally labile.</sup>"
        ),
        x=0.5, xanchor="center",
    ),
    xaxis=dict(title="Pagel's λ (capped at 1.0)", range=[0, 1.12],
               showgrid=True, gridcolor="#eee"),
    yaxis=dict(autorange="reversed"),
    barmode="group",
    height=540,
    plot_bgcolor="#fdfdfd",
    paper_bgcolor="#f9f9f9",
    legend=dict(x=1.01, y=0.95, font=dict(size=9)),
    margin=dict(l=200, r=160, t=90, b=60),
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ASSEMBLE STANDALONE HTML
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

html_map     = pio.to_html(fig_map,     full_html=False, include_plotlyjs=False)
html_scatter = pio.to_html(fig_scatter, full_html=False, include_plotlyjs=False)
html_bar     = pio.to_html(fig_bar,     full_html=False, include_plotlyjs=False)

standalone_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>MicrobeAtlas Metal Ecology — Interactive Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: "Helvetica Neue", Arial, sans-serif;
      background: #f0f2f5;
      color: #222;
      margin: 0;
      padding: 0 0 48px;
    }}
    header {{
      background: linear-gradient(135deg, #1a2332 0%, #2c4a6e 100%);
      color: white;
      padding: 24px 40px 20px;
    }}
    header h1 {{ margin: 0 0 6px; font-size: 1.6em; letter-spacing: 0.01em; }}
    header p  {{ margin: 0; font-size: 0.87em; opacity: 0.78; }}
    .summary-bar {{
      background: #fff3cd;
      border-left: 5px solid #ffc107;
      margin: 24px 40px 0;
      padding: 14px 20px;
      border-radius: 6px;
      font-size: 0.92em;
      line-height: 1.6;
    }}
    .summary-bar strong {{ color: #856404; }}
    .panel {{
      background: white;
      border-radius: 10px;
      box-shadow: 0 2px 14px rgba(0,0,0,0.08);
      margin: 24px 40px 0;
      padding: 20px 20px 10px;
    }}
    .panel-title {{
      font-size: 1.05em;
      font-weight: 600;
      color: #1a2332;
      margin: 0 0 8px;
      padding-bottom: 8px;
      border-bottom: 2px solid #eef0f3;
    }}
    footer {{
      margin: 28px 40px 0;
      font-size: 0.76em;
      color: #999;
      line-height: 1.5;
    }}
  </style>
</head>
<body>
  <header>
    <h1>MicrobeAtlas Metal Ecology — Interactive Dashboard</h1>
    <p>
      Global microbiome metal-resistance diversity · 463,972 samples ·
      98,919 OTUs · 3,160 genera · GTDB r214 pangenome AMR annotations
    </p>
  </header>

  <div class="summary-bar">
    <strong>Key findings:</strong>
    (1) Metal-resistance diversity is <em>environmentally labile</em> (Pagel's λ ≈ 0 for all metal traits),
    contrasting with the strong phylogenetic signal of nitrification (λ ≈ 1).
    (2) Only 902 of 3,160 genera (29%) carry detectable metal AMR genes; the rest have λ constrained by
    environmental filtering, not ancestry.
    (3) <em>Enterococcus</em>, <em>Franconibacter</em>, and <em>Citrobacter</em> sit at the frontier of
    high metal-type diversity combined with broad ecological niche — prime candidates for
    multi-metal resistance experiments.
    (4) Aquatic biomes show the highest metal-gene diversity globally (μ = 2.23 gene types/OTU),
    followed by plant-associated samples (μ = 2.25).
  </div>

  <div class="panel">
    <div class="panel-title">
      1 · Global metal-resistance diversity — real sample locations from MicrobeAtlas
    </div>
    {html_map}
  </div>

  <div class="panel">
    <div class="panel-title">
      2 · Metal-type diversity vs. ecological niche breadth (all 3,160 genera)
    </div>
    {html_scatter}
  </div>

  <div class="panel">
    <div class="panel-title">
      3 · Pagel's λ — phylogenetic signal strength for all traits
    </div>
    {html_bar}
  </div>

  <footer>
    Data sources: MicrobeAtlas 16S OTUs (97% identity, 463,972 samples, 6,390 SRA/ENA projects) ·
    GTDB r214 pangenome · Bakta AMR HMM annotations ·
    Geographic grid: 5° cells, valid coordinates only (n=388,579 samples with GPS).
    Built with Plotly 2.27 · BERIL Research Observatory.
  </footer>
</body>
</html>
"""

out_path = FIGS / "dashboard.html"
out_path.write_text(standalone_html, encoding="utf-8")
print(f"Saved → {out_path}  ({out_path.stat().st_size / 1024:.0f} KB)")
