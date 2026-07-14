# T4SS-CAZy Environmental HGT: Cross-Phylum Transfer of Carbohydrate-Active Enzyme Cassettes

## Research Question

Do Type IV secretion systems (T4SS) in environmental bacteria physically co-localise with
carbohydrate-active enzyme (CAZy) genes in a manner consistent with horizontal gene transfer,
and does phylogenetic analysis of syntenic GT2 glycosyltransferases reveal cross-phylum
transfer events that cannot be explained by vertical inheritance?

## Status

**Active** — Core analysis complete (NB01–NB04 executed). NB05 validation analyses in
progress. See [Analysis Plan](#analysis-plan) for outstanding items.

Initiated: 2026-05-02. Source notebooks: `projects/misc_exploratory/exploratory/`.

## Key Findings (Preliminary)

- **21.8% of 30,497 high-quality environmental MAGs are T4SS-positive** (6,652 MAGs;
  multi-marker definition: VirB4/6/8/9/10/11, VirD4, TraI/D, TrwB, TraG).
- **92 CAZy families** show elevated co-occurrence with T4SS loci at ≤10 kb (threshold
  validation pending in NB05); GT2 glycosyltransferases are the top hit (767 genomes,
  avg 5,041 bp).
- **Biome enrichment**: marine sediment (OR=5.5, q<10⁻⁹⁸), barley rhizosphere (OR=10.4),
  maize rhizosphere (OR=4.1).
- **77 HGT events detected** in GT2 gene tree; 32 high-confidence cross-phylum events
  (normalised file). Strongest: Node_4915 spans 8 phyla at max divergence 4.843.
- **CAZy genes are not on plasmids** (ICEfinder: 12 IMEs in top 100 accumulators);
  T4SS+ genomes have **10× higher MGE density** (p<0.001), consistent with
  chromosomal/integrative transfer rather than plasmid mobilisation.
- **Negative binomial GLM**: each additional CAZy family increases expected enriched KEGG
  pathway count by ~35% (coefficient 0.299, 95% CI 0.253–0.345), offset by genome length,
  cluster-robust standard errors by taxonomic class.

## Claim Framing

The central claim is associative, not causal:

> Cross-phylum clustering of syntenic T4SS-GT2 loci in 32 independently verified cases,
> spanning up to 8 bacterial phyla at phylogenetic divergences up to 4.843, is inconsistent
> with vertical inheritance and consistent with conjugative horizontal gene transfer of
> carbohydrate-active enzyme cassettes in environmental bacteria.

This is explicitly distinguished from the Polysaccharide Utilization Locus (PUL) paradigm,
which involves TonB-dependent transporters (TBDTs) in Bacteroidetes. The T4SS-CAZy signal
here occurs across non-Bacteroidetes lineages via a conjugation-based mechanism.

## Analysis Plan

| NB | Notebook | Status | Description |
|---|---|---|---|
| NB01 | `T4SS_CAZy_Refined.ipynb` | ✅ Done | T4SS identification, discovery/validation split, pathway enrichment, negative binomial GLM |
| NB02 | `T4SS_CAZy_Refined.ipynb` | ✅ Done | Synteny scan (92 families, ≤10 kb), biome enrichment (Fisher's exact, FDR), BacDive/FitnessBrowser ecological mapping |
| NB03 | `T4SS_CAzy_Tree_v3.ipynb` | ✅ Done | GT2 gene tree (8,245 sequences, 1,096 genomes), HGT event detection, iTOL annotation, Figure 4 PDFs |
| NB04 | `Alternative_HGT_Mechanisms_Plasticity_vs_Plasmids.ipynb` | ✅ Done | ICEfinder mobilome scan, MGE density comparison, plasmid vs. chromosomal CAZy location |
| NB05 | `notebooks/05_validation_analyses.ipynb` | 🔲 Todo | Four gap analyses (see below) |
| NB06 | `notebooks/06_synthesis_figures.ipynb` | 🔲 Todo | Consolidated manuscript figures |

### NB05 — Characterisation and Validation Analyses

**Completed (script `scripts/nb05_hgt_analysis.py`):**
- HGT event characterisation: Node_4915 confirmation (8 phyla, divergence 4.843, 82.9%
  syntenic), Spearman ρ(divergence, synteny) = −0.615 (p<0.001), phyla involvement frequency.
- GT2 neighbourhood analysis: 376 unique genomes, T4SS co-occurs 503×, GT2 495×; top
  co-occurring function is GH23 murein lytic transglycosylase.
- GT2 × metal resistance link: 11× enrichment (Mann-Whitney p=8.6e-27, n=376 vs 260,276).

**Outstanding validation analyses (require Spark or network access):**
These four analyses were identified through structured adversarial review as necessary before
manuscript submission:

1. **Permutation test for 10 kb synteny threshold** *(requires Spark)*
   — Randomly shuffle T4SS gene positions within genomes (1,000 permutations); compute CAZy
   co-occurrence at 5, 10, 15, 20 kb. Show observed 10 kb signal exceeds 95th percentile of
   null distribution. Resolves: arbitrary threshold concern.

2. **Housekeeping gene null baseline for phylogenetic incongruence** *(requires Spark)*
   — Build gene trees for 5 conserved single-copy genes (rRNA, gyrase B, RNA polymerase β,
   recA, rpS3) from the same 1,096 genomes. Quantify incongruence rate per gene. Show GT2
   syntenic incongruence (77 events / 32 cross-phylum) significantly exceeds this null.
   Resolves: "0.9% detection rate may be noise" concern.

3. **Biome enrichment factorisation** *(local-computable from staged data)*
   — For each biome, compute θ = OR(T4SS-GT2 synteny) / [OR(T4SS alone) × OR(GT2 alone)].
   θ > 1 indicates genuine co-enrichment beyond independent prevalence effects.
   Resolves: biome confounding concern.

4. **Node_4915 sequence validation** *(requires NCBI BLAST)*
   — BLAST all 35 sequences in Node_4915 against NCBI RefSeq (non-redundant protein
   database). Flag any hits with >95% identity to organisms outside the 8 reported phyla as
   potential misclassification. Resolves: "divergence 4.843 may be chimeric" concern.

## Data Sources

| Database | Tables Used | Access |
|---|---|---|
| `kescience_mgnify` | `genome`, `gene`, `gene_eggnog`, `gene_cazy`, `gene_amr`, `gene_mobilome`, `biome` | JupyterHub Spark |
| `kescience_fitnessbrowser` | `kgroupdesc` | JupyterHub Spark |
| `kescience_bacdive` | `taxonomy`, `metabolite_utilization` | JupyterHub Spark |
| NCBI RefSeq | Protein BLAST | Remote API |

## Source Data

Key intermediate files staged in `data/` (local, no Spark required):

```
data/
  Detected_HGT_Events.csv            # 77 raw HGT events
  Normalized_Detected_HGT_Events.csv # 32 cross-phylum events (≥2 distinct phyla)
  GT2_neighborhood_signatures.csv    # 386 contig neighbourhoods, 376 unique genomes
  tree_metadata.csv                  # Phylum/biome annotations (393K)
  Cytoscape_Edge_List.csv            # Network visualisation edges
  Cytoscape_Node_Table.csv           # Network node metadata
```

Large files remaining in `misc_exploratory/exploratory/data/phylogeny/` (not staged; too
large for git):

```
  GT2_gene_tree.nwk              # FastTree GT2 gene tree (502K)
  GT2_combined_sequences.fasta   # 8,245 tagged sequences
  GT2_aligned.fasta              # MAFFT alignment (191M)
  Figure4_GT2_HGT_Tree.pdf       # Circular tree, syntenic vs. chromosomal
  Figure4_Circular_Tree_Clean.pdf
  itol_phylum_ring.txt           # iTOL colour annotation
```

The full 260K-MAG metal traits file (`mgnify_mag_metal_traits.csv`, 58MB) is also in
`misc_exploratory/exploratory/data/` — too large to stage here; NB05 script retains that
path directly.

## Reproduction

| Step | Notebook / Script | Spark required? | Notes |
|---|---|---|---|
| NB01–NB02: T4SS identification, synteny, biome enrichment | `notebooks/01_t4ss_identification_and_enrichment.ipynb` | **Yes** | Reads `kescience_mgnify` via JupyterHub |
| NB03: GT2 gene tree, HGT detection | `notebooks/03_gt2_gene_tree_hgt_detection.ipynb` | **Yes** (data extraction) | Tree construction uses local FastTree after Spark extraction |
| NB04: Mobilome scan, ICEfinder | `notebooks/04_mobilome_scan.ipynb` | **Yes** | Reads `gene_mobilome` table |
| NB05 characterisation: HGT events, GT2 neighbourhoods, metal link | `scripts/nb05_hgt_analysis.py` | No | Runs from staged `data/` CSVs |
| NB05 validation: biome factorisation | `notebooks/05_validation_analyses.ipynb` | No | Uses staged CSVs; pending implementation |
| NB05 validation: permutation test, housekeeping null | `notebooks/05_validation_analyses.ipynb` | **Yes** | Requires unfiltered gene table |
| NB05 validation: Node_4915 BLAST | — | No (network) | Requires NCBI BLAST API access |

## Distinguishing from PUL/TBDT Literature

The existing PUL paradigm (Bjursell 2006, Martens 2009, PULDB, PULpy) characterises
**TonB-dependent transporter (TBDT) + SusC/D + CAZyme clusters** in Bacteroidetes. That
system involves cis-regulatory carbohydrate uptake, not inter-genome transfer.

This project studies **T4SS (VirB/VirD conjugation machinery) + CAZy synteny** in
non-Bacteroidetes environmental MAGs. The 32 cross-phylum HGT events are the key distinction:
PULs do not predict cross-phylum phylogenetic incongruence in GT2 gene trees.

The introduction should cite PULDB/PULpy and explicitly frame the T4SS system as mechanistically
and taxonomically distinct.

## Figures

| Figure | File | Status |
|---|---|---|
| Fig. 1 — Enriched KEGG pathways bubble chart | TBD | 🔲 |
| Fig. 2 — Metabolic niche heatmap (BacDive) | `data/Figure2_Metabolic_Niche_Final.pdf` | ✅ |
| Fig. 3 — Forest plot of GLM predictors | TBD | 🔲 |
| Fig. 4 — GT2 circular phylogenetic tree + HGT snapshots | `data/phylogeny/Figure4_Circular_Tree_Clean.pdf` | ✅ |

## Authors

Heather MacGregor
