# Research Plan: Subsurface Bacillota_B Specialization — What Distinguishes Deep-Clay Lineages from Soil Congeners?

## Research Question

Within the GTDB phylum **Bacillota_B** (which contains *Desulfosporosinus*, the BRH-c8a Peptococcaceae lineage, BRH-c4a Desulfotomaculales, and other obligate-anaerobe deep-subsurface taxa) — what accessory gene content distinguishes the deep-clay-isolated members (Bagnoud 2016 Mont Terri indigenous lineages, BacDive deep-clay strains) from the soil-baseline Bacillota_B in BERDL pangenome? In plain terms: beyond the curated marker dictionary used in `clay_confined_subsurface` (which mostly tested Wood–Ljungdahl, [NiFe]-hydrogenase, dsr-apr-sat — and whose IR-side markers turned out to be wrong genes), what does the pangenome gene-cluster–level signal actually say about subsurface adaptation in this phylum?

## Hypotheses

### H1 — Recurrent deep-subsurface accessory operons
- **H0**: Within Bacillota_B, deep-clay-isolated genomes carry the same accessory gene-cluster repertoire as phylum-matched soil-baseline genomes.
- **H1**: ≥10 specific gene clusters (orthologous within Bacillota_B at 90% AAI per the BERDL pangenome's `gene_cluster` definition) are enriched in deep-clay Bacillota_B at ≥3× the rate of soil-baseline Bacillota_B (Fisher BH-FDR q<0.05). Pre-registered functional categories these enriched clusters are expected to fall into:
  - **Sporulation-revival operons** (subsurface organisms persist as spores between activity windows; revival under low-water-activity is non-trivial — `cwlJ`, `gerAB`, `safA` analogs)
  - **Anaerobic accessory respiratory chains** beyond canonical SR (e.g., DMSO/TMAO reductase complexes, formate dehydrogenase variants, additional Group 3/4 hydrogenases)
  - **Mineral-attachment / EPS biosynthesis** (subsurface organisms attach to clay/mineral surfaces — exopolysaccharide biosynthesis operons, type IV pili / pilA expansions distinct from canonical Geobacter pilA)
  - **Osmoadaptation** (low water activity in clay porewater — glycine betaine biosynthesis, ectoine, K⁺ uptake regulators)
  - **Anaerobic-niche regulators** (sigma-F/sigma-B sporulation control, anti-anti-sigma factor cascades, redox-sensing two-component systems)

### H2 — Genome-compactness signal
- **H0**: Deep-clay Bacillota_B have the same mean genome size and gene count as soil-baseline Bacillota_B.
- **H1**: Deep-clay Bacillota_B have *smaller* mean genome size and gene count after CheckM-completeness control. Tests the "small is mighty" pattern Tian 2020 documented for Patescibacteria, applied to a cultivable phylum.

### H3 — Iron-reduction capacity (clay-project H3 IR-side correction)
- **H0**: Deep-clay Bacillota_B do not carry multi-heme cytochrome iron-reduction potential at higher rates than soil baseline.
- **H1**: Multi-heme cytochrome content (PFAM PF14537 Cytochrom_NNT + per-protein heme-binding motif `CXXCH` count ≥4) is enriched in deep-clay Bacillota_B vs soil-baseline Bacillota_B. **This corrects the clay_confined_subsurface H3 IR-side, which used K07811/K17324/K17323 — KOs that turn out to be TMAO reductase, glycerol ABC, and glycerol permease respectively, not iron-reduction markers.**

## Literature Context

The Bacillota_B phylum (formerly Firmicutes Class II per Schoch 2020, includes Desulfotomaculales, Desulfitobacteriales, Peptococcaceae, Heliobacteriaceae) is the cultivable counterpart to the uncultivable Patescibacteria/CPR superphylum at deep-subsurface sites (Beaver & Neufeld 2024). At Mont Terri, Bagnoud et al. (2016, [PMC5067608](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5067608/)) reported three MAGs (Desulfobulbaceae c16a, Rhodospirillaceae c57, **Peptococcaceae c8a — i.e., BRH-c8a in our cohort**) recurring across seven independent boreholes — the indigenous Opalinus core community. Vandieken et al. (2017, [PMID 28646634](https://pubmed.ncbi.nlm.nih.gov/28646634/)) described three new Desulfosporosinus species from Baltic Sea subsurface sediments with H₂-driven sulfate/thiosulfate/sulfite/DMSO/S⁰ reduction. Hilpmann et al. (2023, [PMID 36889400](https://pubmed.ncbi.nlm.nih.gov/36889400/)) demonstrated U(VI) reduction in *Desulfosporosinus hippei*, relevant for nuclear-waste-repository microbiology. Beller et al. (2012, [PMC3536105](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3536105/)) showed the Hanford 100H *Pelosinus* HCF1 carries 2 [NiFe] + 4 [FeFe] hydrogenases plus N-oxide reductase complement — a useful comparative-genomics template for what subsurface-adapted Firmicutes look like at the gene-content level.

The companion `clay_confined_subsurface` project's strongest within-phylum result was 5/5 deep-clay Bacillota_B carrying SR vs 4/19 soil-baseline Bacillota_B, OR=∞, p_BH=0.04 — the only marker that survived phylum control. That project's IR-side analysis used incorrect KOs and needs correction, recommended by the `oak_ridge_cultivation_gap` (`projects/oak_ridge_cultivation_gap/REPORT.md`) future-directions section. We address that here as Phase 1.

See [references.md](references.md) for the full bibliography (inherited + extended from `clay_confined_subsurface/references.md`).

## Cohort Definition

### Anchor cohort: deep-clay-isolated Bacillota_B (target n ≈ 15–25)

Sources:

| Sub-cohort | Source filter | Expected n |
|---|---|---|
| Mont Terri Opalinus Bacillota_B | `clay_confined_subsurface/data/cohort_assignments.tsv` filtered to Bacillota_B + sub_cohort='opalinus' | 5 (BRH-c4a, BRH-c8a×2, Desulfosporosinus×2 confirmed in clay project) |
| Coalvale silty clay Bacillota_B | clay project anchor_shallow filtered to Bacillota_B | check |
| BacDive expansion: clay-isolated Desulfosporosinus / Desulfotomaculales / Peptococcaceae genera | `kescience_bacdive.isolation` × `taxonomy` filtered to clay sample_type + Bacillota_B genera, GCA→GTDB linkage | ~10–20 |

### Soil-baseline cohort: phylum-matched Bacillota_B (target n ≈ 100–200)

Random sample from `kbase_ke_pangenome.gtdb_taxonomy_r214v1` filtered to `phylum = 'p__Bacillota_B'` joined to soil/sediment biosamples in `ncbi_env`. Excludes any clay-keyword-mentioning biosamples to avoid overlap with anchor.

### Pangenome scale check

Quick `COUNT(*)` during plan-writing: BERDL pangenome contains roughly **6,700 Bacillota_B genomes** across all habitats. Filtering to soil/sediment-isolated gives the parent population for the baseline draw. NB01 will confirm exact counts.

## Query Strategy

### Tables Required

| Table | Purpose | Rows | Filter |
|---|---|---|---|
| `kbase_ke_pangenome.gtdb_taxonomy_r214v1` | Bacillota_B genome universe | 293K | `phylum = 'p__Bacillota_B'` |
| `kbase_ke_pangenome.ncbi_env` | Soil/sediment vs clay biosample assignment | 4.1M | by `accession`+`content` keyword |
| `kbase_ke_pangenome.genome` | biosample → genome_id | 293K | join on `ncbi_biosample_id` |
| `kbase_ke_pangenome.gtdb_metadata` | Genome size, GC, CheckM | 293K | join on `accession` |
| `kbase_ke_pangenome.gene` + `gene_genecluster_junction` | Per-genome cluster membership | 1B / 1B | filter by `genome_id IN (cohort)` |
| `kbase_ke_pangenome.gene_cluster` | Cluster-level metadata | 132M | filter by `gene_cluster_id IN (cohort_clusters)` |
| `kbase_ke_pangenome.eggnog_mapper_annotations` | KEGG/COG/PFAM per cluster representative | 94M | filter by `query_name IN (cohort_clusters)` |
| `kbase_ke_pangenome.bakta_pfam_domains` | Per-genome PFAM detection (for Phase 1 IR correction) | 18M | filter by `gene_cluster_id IN (cohort)` |
| `kbase_ke_pangenome.bakta_annotations` | Per-cluster bakta annotations including amino acid sequences for heme-motif scan | 132M | filter by `gene_cluster_id IN (cohort)` |
| `kescience_bacdive.isolation` + `taxonomy` | BacDive clay-Bacillota_B expansion | 58K + 97K | LIKE filter on sample_type + Bacillota_B genera |

### Anti-pitfall checklist (from `docs/pitfalls.md`)

- `bakta_pfam_domains` may silently lack 12/22 marker PFAMs (documented in `plant_microbiome_ecotypes` pitfall) → for Phase 1, validate PF14537 is present before relying on it
- Bacillota_B is GTDB nomenclature (split from Bacillota a.k.a. Firmicutes); Bacillota_A and Bacillota_C are also Firmicutes-derived but distinct phyla — use exact phylum match, not LIKE
- BacDive accessions need GCA prefix harmonization for pangenome linkage

### Performance Plan

- **Tier**: BERDL JupyterHub on-cluster.
- **Largest job**: cluster-presence pull for ~250 cohort genomes against `gene_genecluster_junction` (1B rows) — same per-genome filter pattern used in `clay_confined_subsurface` and `oak_ridge_cultivation_gap`. ~10–15 min.
- **Alternate**: per-cluster Fisher across ~50K species-level gene clusters (the typical Bacillota_B accessory-genome size after deduplication) — local pandas/scipy after the cluster-presence matrix is in memory.

## Analysis Plan

### NB01 — Bacillota_B universe + cohort assembly (Spark)
- **Goal**: Pull all Bacillota_B genomes from BERDL pangenome with QC + isolation_source. Identify deep-clay anchor (incl. BacDive expansion) and phylum-matched soil-baseline.
- **Outputs**: `data/bacillota_b_universe.tsv` (~6.7K genomes with metadata), `data/cohort_assignments.tsv` (anchor + baseline tagged).

### NB02 — Cluster-presence matrix (Spark + local)
- **Goal**: For each cohort genome (anchor + baseline), pull its full set of `gene_cluster_id`s via `gene_genecluster_junction`. Build a sparse genome × cluster boolean matrix.
- **Outputs**: `data/cohort_cluster_presence.parquet` (long-format genome_id, gene_cluster_id pairs).

### NB03 — Per-cluster enrichment test (local)
- **Goal**: For each gene cluster present in any cohort genome, Fisher's exact test (anchor vs baseline). BH-FDR correct across clusters. Keep clusters with q<0.05 AND fold-difference ≥3 AND minimum support (≥3 anchor genomes).
- **Outputs**: `data/cluster_enrichment.tsv` (one row per significant cluster, columns: gene_cluster_id, anchor_n, anchor_pos, baseline_n, baseline_pos, OR, p, p_BH, fold_diff).

### NB04 — Functional annotation of enriched clusters (Spark + local)
- **Goal**: For the significant clusters from NB03, pull eggNOG annotations (KEGG_ko, COG_category, PFAM, Description) and bakta annotations. Group by functional category.
- **Outputs**: `data/enriched_clusters_annotated.tsv`, `figures/h1_functional_categories.png`.

### NB05 — H2 genome-compactness test (local)
- **Goal**: Compare genome size and gene count distributions (anchor vs baseline) after CheckM-completeness rescaling. Wilcoxon + Cohen's d.
- **Outputs**: `data/h2_compactness.tsv`, `figures/h2_genome_size.png`.

### NB06 — Phase 1 correction: clay_confined_subsurface H3 IR-side (Spark + local)
- **Goal**: Re-do the clay project's iron-reduction analysis using PFAM PF14537 (Cytochrom_NNT) + heme-binding motif counting, and write a corrected H3 result.
- **Method**:
  1. Pull `bakta_pfam_domains` filtered to clay project's anchor + shallow + baseline genome IDs (re-loaded from `clay_confined_subsurface/data/cohort_assignments.tsv` and `baseline_features.parquet`).
  2. Count PF14537 hits per genome.
  3. (Optional, if time) For each cluster in the clay cohort, pull `bakta_annotations.amino_acid_sequence`, count `CXXCH` heme-binding motif occurrences per protein. Multi-heme cytochrome candidate = ≥4 CXXCH motifs.
  4. Re-test the clay H3 hypothesis (deep clay vs shallow vs soil) with the corrected IR markers.
  5. Write `clay_confined_subsurface/REPORT_CORRECTION.md` (or amend their REPORT.md inline) summarizing the correction and revised H3 verdict.
- **Outputs**: `data/clay_h3_ir_corrected.tsv`, `figures/clay_h3_ir_corrected.png`, plus a commit on the `clay_confined_subsurface` project's branch (not on this branch — separate cherry-pick or PR).

### NB07 — Synthesis (local)
- **Goal**: Integrate H1 (enriched clusters), H2 (compactness), and Phase 1 (clay IR correction) into a single narrative figure + a draft REPORT.md.
- **Outputs**: `figures/summary_figure.png`, draft `REPORT.md`.

## Expected Outcomes

- **If H1 supported**: We identify a small set (≤50) of recurrent gene clusters that distinguish deep-clay Bacillota_B from soil Bacillota_B beyond the SR toolkit. Functional categories tell us *what* subsurface specialization looks like at the accessory-genome level — concrete, testable, and useful as a target list for future biochemistry / fitness-screen work.
- **If H1 not supported**: Within Bacillota_B, deep-clay vs soil isolates are gene-content-equivalent at the cluster level. Implication: Bacillota_B may be ecologically generalist within its niche; deep-clay specialization in this phylum is a regulatory or expression-level phenomenon, not an accessory-gene-presence one. Still informative.
- **If H2 supported**: Subsurface compactness ("small is mighty") extends from Patescibacteria to cultivable Firmicutes — strengthens Tian 2020's general claim.
- **If H2 not supported**: Compactness is a Patescibacteria-specific signature, not a general subsurface adaptation.
- **If Phase 1 (corrected IR) shows different pattern from clay project's original**: clay's "porewater-vs-rock-attached" headline needs revision. The SR side stands; the IR side may not. We'll patch clay's REPORT.md with a correction addendum.

### Potential confounders
- **Phylum-internal phylogenetic structure**: Bacillota_B has multiple orders (Desulfotomaculales, Desulfitobacteriales, Peptococcaceae, etc.); deep-clay anchor may be order-skewed. Sensitivity test: per-order within-phylum stratification.
- **Cluster-definition cohort dependence**: The BERDL pangenome's `gene_cluster` is species-specific (cluster IDs don't generalize across species). For cross-species accessory-genome analysis, must either (a) use eggNOG OG IDs as the orthology surrogate, or (b) build BBH ortholog groups across the cohort. **NB02 will use eggNOG OG (`eggNOG_OGs` field at the appropriate taxonomic level — per `docs/pitfalls.md` Bakta-vs-IPS Pfam audit, eggNOG OG-level is the correct cross-species cluster ID for Bacillota_B-internal comparison).**
- **BacDive expansion completeness**: Some clay-isolated Bacillota_B may not have GCA accessions in NCBI; cohort size is bounded by the BacDive→GTDB linkable subset (~27K out of 97K BacDive strains).

## Revision History

- **v1** (2026-04-30): Initial plan. Builds on `clay_confined_subsurface` (H1/H2/H3) and `oak_ridge_cultivation_gap` (NB02/NB03 pyhmmer + KOfam annotation pipeline). Phase 1 corrects the clay project's IR marker bug surfaced during oak_ridge synthesis.

## Authors

David Lyon (ORCID: [0000-0002-1927-3565](https://orcid.org/0000-0002-1927-3565)) — KBase
