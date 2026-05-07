# Research Plan: What Metabolic Functions Does the Cultured Collection Miss at Oak Ridge?

## Research Question

At the ENIGMA Oak Ridge Field Research Center (ORFRC), what metabolic functions does BERDL's cultured-isolate genome collection (3,110 genomes in the ENIGMA Genome Depot) systematically under-represent compared to metagenome-assembled genomes (623 MAGs) recovered from the same site? If a researcher relied only on the cultured genomes to characterize the metabolic potential of the Oak Ridge subsurface, what would they miss — and what would they over-estimate?

## Hypothesis

- **H1 (Depletion)**: Specific metabolic functions are significantly depleted in the cultured cohort relative to the MAG cohort — most prominently CPR/DPANN-signature genes, surface-electron-transfer iron-reduction genes (multi-heme cytochromes), anaerobic methane oxidation, and MGE-resident heavy-metal resistance cassettes.
- **H2 (Enrichment)**: A subset of functions is *enriched* in the cultured cohort — sulfate reduction, broad aerobic/facultative respiration, and motility/chemotaxis — recapitulating the porewater-bias signature documented in the `clay_confined_subsurface` project and reflecting the systematic selection of readily cultivable organisms from the porewater fraction.
- **H0**: Cultured and MAG gene-content distributions at Oak Ridge are statistically equivalent across the marker dictionary (no cultivation bias at the functional level).

## Literature Context

The ORFRC subsurface harbors diverse microbial communities shaped by a legacy contamination plume (U, Tc, nitrate, organic solvents). Prior ENIGMA work has characterized the site through isolate genomics (Genome Depot, 3,110 genomes), 16S amplicon surveys (CORAL, 4,346 samples), and metagenomics (623 binned MAGs from 15 wells).

**Key references for testable predictions:**

- **Kothari et al. (2019)** recovered large circular plasmids from ORFRC groundwater plasmidomes enriched in multimetal resistance genes — predicting that MGE-borne metal resistance may be underrepresented in cultured isolates that lose plasmids during lab passage.
- **Tian et al. (2020)** documented Patescibacteria / Candidate Phyla Radiation (CPR) lineages in ORFRC subsurface, characterized by small genomes, limited metabolic capacity, and obligate dependence on host organisms — essentially uncultivable by standard methods.
- **Goff et al. (2024)** identified heavy-metal-resistance-laden mobile genetic elements in ORFRC subsurface MAGs, suggesting that the accessory genome (captured better by MAGs than isolates) carries the site-specific adaptation signal.
- **Wu et al. (2023)** documented depth-stratified carbon and nitrogen cycling in ORFRC metagenomes, with distinct metabolic guilds (denitrifiers, iron reducers, methanogens) occupying different depth zones.
- **Beaver & Neufeld (2024)** synthesized the deep-subsurface genomics literature, identifying biosynthetic self-sufficiency, Wood–Ljungdahl C-fixation, and group 1 [NiFe]-hydrogenase as hallmarks of deep-subsurface life — features concentrated in uncultivated lineages.
- The `clay_confined_subsurface` project (this observatory) demonstrated a quantitative porewater-bias diagnostic using SR/IR marker ratios, generalizable to any cultured-pangenome cohort. The same framework extends to Oak Ridge.
- The `lab_field_ecology` project found that 14/26 Fitness Browser genera are detected at Oak Ridge, with Sphingomonas, Pseudomonas, and Caulobacter most prevalent — but the cultured collection's taxonomic breadth relative to the full metagenome community is unknown.

**Gap this project fills:** No quantitative cultivation-bias index exists that compares functional gene content between matched cultured and MAG cohorts from the same environmental site (Escudeiro et al. 2022 review). This project produces the first per-function "cultivation-coverage" table for a well-characterized subsurface site.

## Cohort Definition

### Cultured cohort (~3,110 genomes)

Source: `enigma_genome_depot_enigma.browser_genome` joined to `browser_protein_kegg_orthologs` for KO annotations. Mean 2,046 KOs per genome (range 1–3,693). Top taxa: Pseudomonadaceae (180), Variovorax (123), Cupriavidus (111), Caulobacter (54), Acidovorax (66), Rhodanobacter (32).

Additionally, 147 of these genomes link to `kbase_ke_pangenome` via GCF/GCA accessions, providing eggNOG, GapMind, bakta, and Pfam annotations for cross-validation.

### MAG cohort (623 MAGs)

Source: `enigma_coral.sdt_bin` — 623 MAGs from 15 metagenome assemblies spanning 15 ORFRC groundwater wells (FW215, FW300, DP16D, FW602, FW021, GW715, FW106, FW301, GW928, FW305, FW104, GW199). Parent assembly FASTAs are at cluster-local paths (`/h/jmc/data/enigma/metagenomics/`), accessible from JupyterHub.

**MAGs require functional annotation.** The `sdt_bin` table contains only contig membership lists. NB01 will extract per-bin FASTAs from parent assemblies on JupyterHub, and NB02 will annotate them with bakta (or pyrodigal + pyhmmer KOfam) via CTS compute.

### Quality control

Both cohorts filtered for completeness ≥50% and contamination ≤10% (CheckM or equivalent). MAGs below this threshold are excluded. Genome depot genomes without KO annotations are excluded (8 genomes with min KOs = 1).

## Query Strategy

### Tables Required

| Table | Purpose | Rows | Filter |
|---|---|---|---|
| `enigma_genome_depot_enigma.browser_genome` | Cultured genome inventory | 3,110 | All |
| `enigma_genome_depot_enigma.browser_protein_kegg_orthologs` | KO annotations for cultured genomes | 3.7M | Join via protein → gene → genome |
| `enigma_genome_depot_enigma.browser_kegg_ortholog` | KO ID ↔ description lookup | 10,291 | All |
| `enigma_genome_depot_enigma.browser_taxon` | Taxonomy for cultured genomes | ~3,100 | Join via genome.taxon_id |
| `enigma_coral.sdt_bin` | MAG bin membership (contig lists) | 623 | All |
| `enigma_coral.sdt_assembly` | Assembly FASTA paths | 16 | Metagenome assemblies only |
| `kbase_ke_pangenome.genome` | Pangenome linkage for 147 ENIGMA genomes | 293K | GCF/GCA match |
| `kbase_ke_pangenome.eggnog_mapper_annotations` | eggNOG for pangenome-linked genomes | 94M | Filter by linked genome clusters |

### Marker Dictionary (literature-grounded)

Extending the `clay_confined_subsurface` marker set with Oak-Ridge-specific additions:

| Marker category | KOs / Pfams | Prediction | Source |
|---|---|---|---|
| **Wood–Ljungdahl** | K00198, K00194, K00197, K15022, K15023 | Depleted in cultured | Beaver & Neufeld 2024 |
| **Group 1 [NiFe]-hydrogenase** | K06281, K06282; PF00374, PF14720 | Depleted in cultured | Bagnoud 2016 |
| **Dissimilatory sulfate reduction** | K11180, K11181, K00394, K00395, K00958 | Enriched in cultured (porewater bias) | Bagnoud 2016, clay project |
| **Multi-heme cytochrome (Fe-red)** | PF02085, PF22678, CXXCH motifs | Depleted in cultured | Mitzscherling 2023, clay correction |
| **Denitrification** | K00370 (narG), K00371 (narH), K02567 (napA), K00368 (nirK), K15864 (nirS), K00376 (nosZ) | Depth-variable | Wu 2023 |
| **Methanogenesis** | K00399 (mcrA), K00401 (mcrB), K00402 (mcrG) | Depleted in cultured | Beaver & Neufeld 2024 |
| **CPR/DPANN signature** | Reduced genome size (<1.5 Mbp), missing many core biosynthetic KOs | Absent from cultured | Tian 2020 |
| **MGE / conjugation** | K03204 (virB4), K03197 (virD4), transposase Pfams | Depleted in cultured (plasmid loss) | Kothari 2019, Goff 2024 |
| **Heavy metal resistance (HMR)** | K07787 (cusR/copR), K07665 (cusA), K19592 (merA), K00537 (arsC) | Variable — genomic enriched, MGE-borne depleted | Goff 2024 |
| **Motility / chemotaxis** | K02406 (fliC), K03406 (cheA), K03407 (cheW) | Enriched in cultured | Cultivation selection |
| **Aerobic respiration** | K02274 (coxA), K02275 (coxB), K02276 (coxC) | Enriched in cultured | Cultivation selection |
| **N-fixation** | K02588 (nifH), K02586 (nifD), K02591 (nifK) | Variable | Beaver & Neufeld 2024 |

### Performance Plan

- **Tier**: JupyterHub Spark SQL for BERDL queries; CTS for MAG annotation.
- **Estimated complexity**: Moderate. Genome depot queries involve multi-table JOINs but on ~3K genomes (tractable). MAG annotation is the compute bottleneck (~6-12h on CTS).
- **Cache strategy**: NB01 exports per-bin FASTAs + quality stats. NB02 exports per-MAG KO profiles. NB03 exports per-cultured-genome KO profiles. NB04-06 consume cached files locally.

### Anti-pitfall checklist

- Short ENIGMA strain names collide across databases — match via GCF accession, not strain name (pitfalls.md)
- Genome depot `browser_protein` has no `gene_id` column — join via `browser_gene.protein_id`
- KO IDs in genome depot are integer foreign keys to `browser_kegg_ortholog.id`, not KO strings — need JOIN for human-readable KO codes
- MAG contigs are named per-assembly (e.g., `FW215_contig_1948`) — must match exactly against `sdt_bin.contigs` array
- Assembly FASTAs at `/h/jmc/data/` are accessible only from JupyterHub, not from the local session

## Analysis Plan

### NB01 — MAG extraction and quality assessment (JupyterHub)

- **Goal**: Extract per-bin FASTA files from parent metagenome assemblies; run CheckM2 for completeness/contamination; filter to ≥50% complete, ≤10% contamination.
- **Inputs**: `sdt_bin` (contig lists), `sdt_assembly` (FASTA paths at `/h/jmc/data/...`)
- **Outputs**: `data/mag_bins/` (per-bin FASTAs), `data/mag_quality.tsv` (CheckM2 results), `data/mag_cohort.tsv` (QC-filtered MAG list)
- **Runtime estimate**: ~2-4 hours (I/O bound by FASTA parsing + CheckM2)

### NB02 — MAG functional annotation (CTS)

- **Goal**: Annotate QC-filtered MAGs with bakta (or pyrodigal + pyhmmer KOfam) to produce per-MAG KO profiles.
- **Inputs**: `data/mag_bins/` (per-bin FASTAs from NB01)
- **Outputs**: `data/mag_ko_profiles.tsv` (MAG × KO presence/absence matrix), `data/mag_annotation_summary.tsv`
- **Runtime estimate**: ~6-12 hours on CTS (bakta on ~400-500 QC-passed MAGs)

### NB03 — Cultured genome functional profiles (Spark)

- **Goal**: Build per-genome KO presence/absence profiles for all 3,110 genome depot genomes. Add taxonomy, genome size, and metadata.
- **Inputs**: `browser_genome`, `browser_gene`, `browser_protein`, `browser_protein_kegg_orthologs`, `browser_kegg_ortholog`, `browser_taxon`
- **Outputs**: `data/cultured_ko_profiles.tsv`, `data/cultured_genome_metadata.tsv`
- **Runtime estimate**: ~15-30 min on Spark

### NB04 — Per-function cultivation-coverage analysis (local)

- **Goal**: For each function in the marker dictionary, compute presence rates in cultured vs MAG cohorts. Fisher's exact test with BH-FDR. Compute a cultivation-coverage index per function.
- **Inputs**: `data/cultured_ko_profiles.tsv`, `data/mag_ko_profiles.tsv`
- **Method**: Per-KO Fisher's exact (cultured vs MAG), BH-FDR correction. Effect size = odds ratio + 95% CI. Aggregate to marker categories (e.g., "denitrification" = any of narG/napA/nirK/nirS/nosZ). Produce a ranked per-function cultivation-coverage table.
- **Outputs**: `data/cultivation_coverage_table.tsv`, `figures/per_function_coverage_forest.png`, `figures/marker_category_barplot.png`

### NB05 — Taxonomic bias analysis (local)

- **Goal**: Compare taxonomic composition of cultured vs MAG cohorts. Identify phyla/classes present in MAGs but absent or underrepresented in culture.
- **Inputs**: `data/cultured_genome_metadata.tsv`, `data/mag_annotation_summary.tsv` (GTDB taxonomy from bakta or sourmash)
- **Method**: Per-phylum frequency comparison (Fisher's exact). Jaccard and Bray-Curtis dissimilarity between cohort taxonomic profiles. Identify CPR/DPANN lineages in MAGs.
- **Outputs**: `data/taxonomic_bias.tsv`, `figures/phylum_composition_comparison.png`, `figures/taxonomic_venn.png`

### NB06 — Cross-validation with pangenome and literature (local)

- **Goal**: Validate cultivation-coverage findings using (a) the 147 pangenome-linked ENIGMA genomes (richer eggNOG/Pfam annotations) and (b) published Oak Ridge MAG studies.
- **Inputs**: Pangenome data for linked genomes, literature marker expectations
- **Method**: For pangenome-linked genomes, compare eggNOG-derived functional profiles against genome depot KO profiles (concordance check). For literature validation, compare our per-function coverage table against predictions from Tian 2020, Goff 2024, Wu 2023, Kothari 2019.
- **Outputs**: `data/pangenome_crossvalidation.tsv`, `figures/literature_validation.png`

### NB07 — Generalized cultivation-bias diagnostic module (local)

- **Goal**: Package the per-function comparison framework as a reusable module (`src/cultivation_bias.py`) that future BERDL projects can call to flag whether their genome cohort is cultivation-biased.
- **Inputs**: Any two genome × KO matrices
- **Outputs**: `src/cultivation_bias.py` (reusable module), `data/oak_ridge_reference_profile.tsv` (reference cultivation-bias profile for Oak Ridge)

### NB08 — Synthesis (local)

- **Goal**: Integrate findings, contextualize with literature, produce summary figures for REPORT.md.
- **Outputs**: `figures/summary_figure.png`, draft REPORT.md text

## Expected Outcomes

### If H1 supported
The cultured collection misses specific functional guilds — CPR/DPANN-dependent functions, iron reduction via multi-heme cytochromes, methanogenesis, and MGE-borne metal resistance. This produces a concrete "cultivation gap" checklist for ORFRC researchers: these functions require MAG-based analysis, not isolate genomics.

### If H2 supported
The cultured collection over-represents porewater-associated functions (sulfate reduction, aerobic respiration, motility), consistent with the clay project's porewater-bias signature and extending it to a basalt-hosted subsurface system. This validates cultivation bias as a systematic, site-independent phenomenon.

### If H0 not rejected
The Oak Ridge cultured collection is functionally more representative than expected — an interesting positive result suggesting that ENIGMA's intensive cultivation efforts have captured most of the site's metabolic diversity. This would contrast with the clay project's clear porewater bias.

### Potential confounders

- **Genome quality asymmetry**: MAGs are inherently less complete than isolate genomes; missing genes in MAGs could be assembly artifacts, not true absences. CheckM filtering and per-phylum controls mitigate this.
- **Annotation method differences**: Genome depot uses one annotation pipeline; bakta uses another. KO-level comparison minimizes this, but some systematic differences in sensitivity are possible. NB06 cross-validates via pangenome eggNOG.
- **Temporal and spatial mismatch**: Cultured genomes span 20+ years of isolation; MAGs come from specific sampling events. Community composition shifts over time.
- **Bin contamination**: Even with CheckM filtering, some MAGs may contain chimeric assemblies. Conservative contamination thresholds (≤10%) and flagging of outlier bins mitigate this.

## Revision History

- **v1** (2026-05-07): Initial plan, building on `clay_confined_subsurface` cultivation-bias framework and `lab_field_ecology` Oak Ridge context.

## Authors

Justin Reese (ORCID: [0000-0002-2170-2250](https://orcid.org/0000-0002-2170-2250)) — Lawrence Berkeley National Laboratory
