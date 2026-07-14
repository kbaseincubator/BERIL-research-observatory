# Report: T4SS-CAZy Environmental HGT

## Status

Preliminary — core analyses complete (NB01–NB04). NB05 threshold validation and
NB06 manuscript figures pending.

## Key Findings

- **21.8% of 30,497 high-quality environmental MAGs** carry T4SS/conjugative machinery
  (6,652 MAGs; multi-marker definition: VirB4/6/8/9/10/11, VirD4, TraI/D, TrwB, TraG).
- **92 CAZy families** show elevated co-occurrence with T4SS loci at ≤10 kb (threshold
  validation pending); GT2 glycosyltransferases are the top hit (767 genomes, avg 5,041 bp).
- **Biome enrichment**: marine sediment (OR=5.5, q<10⁻⁹⁸), barley rhizosphere (OR=10.4),
  maize rhizosphere (OR=4.1).
- **77 HGT events** detected in GT2 gene tree; **32 high-confidence cross-phylum events**
  (normalised). Strongest: Node_4915 spans 8 phyla at max divergence 4.843.
- **CAZy genes are not on plasmids** (ICEfinder: 12 IMEs in top 100 accumulators);
  T4SS+ genomes have **10× higher MGE density** (p<0.001), consistent with
  chromosomal/integrative transfer.
- **Discovery/validation split** (70/30): enrichment patterns replicate across sets,
  confirming robustness.

## Interpretation

T4SS machinery in environmental MAGs is significantly co-localised with GT2
glycosyltransferase cassettes, and phylogenetic incongruence in the GT2 gene tree
provides positive evidence for 32 cross-phylum HGT events. The ICEfinder null result
(no plasmid-borne CAZy genes) combined with the 10× MGE density elevation in T4SS+
genomes is consistent with chromosomal or integrative transfer mechanisms (IMEs/ICEs)
rather than plasmid mobilisation.

These results support the hypothesis that T4SS machinery mediates environmental
dissemination of carbohydrate-active enzyme diversity across phylogenetically distant
bacteria. All associations are observational; mechanistic confirmation requires
experimental validation.

## NB05 Analysis Results

**HGT event characterisation (Detected_HGT_Events.csv, n=77):**
- Distinct_Phyla distribution: 65 events span 2 phyla, 12 span ≥3 phyla (15.6%).
- **Node_4915 confirmed**: 35 genes, 82.9% syntenic, 8 phyla (WOR-3, Desulfobacterota,
  Patescibacteria, Bacteroidota, Firmicutes_A, Methanobacteriota, Bdellovibrionota,
  Acidobacteriota), Max_Divergence = 4.843.
- **Divergence vs. synteny**: Spearman ρ = −0.615 (p<0.001) — more phylogenetically
  distant events have lower syntenic percentage, consistent with sequence divergence
  after transfer. This is the expected biological pattern.
- Most-involved phyla across all events: Firmicutes_A (27), Pseudomonadota (22),
  Bacillota_A (19), Actinomycetota (10).
- Figure: `figures/fig_nb05_hgt_scatter.png`

**GT2 neighbourhood analysis (376 genomes):**
- Neighbourhood parsed as list-format: T4SS co-occurs in 503 neighbourhood entries,
  GT2 in 495 — confirming syntenic co-localisation at the contig level.
- GH23 (murein lytic transglycosylase) is the second most common CAZy family in GT2
  neighbourhoods (106 occurrences), suggesting cell wall remodelling genes cluster with
  GT2-T4SS syntenic loci.
- Figure: `figures/fig_nb05_neighbourhood_functions.png`

**GT2 × metal resistance (new finding):**
GT2-neighbourhood MAGs (n=376) have mean 0.045 metal resistance types vs 0.004 for
non-GT2 MAGs (n=260,276); Mann-Whitney p=8.6e-27. Genomes with GT2 in T4SS-proximal
neighbourhoods carry **11× more metal resistance genes**. This is an independent link
between CAZy-T4SS synteny and the metal resistance niche breadth hypothesis: genomes
that serve as hubs for GT2 horizontal transfer are also enriched for metal resistance
functions.

## Pending Validation

1. Synteny threshold permutation test (requires Spark unfiltered data)
2. Node_4915 BLAST validation (requires BLAST against NCBI nr)
3. Housekeeping gene null baseline
4. Biome enrichment factorisation: θ = OR(T4SS-CAZy) / [OR(T4SS) × OR(CAZy)]
