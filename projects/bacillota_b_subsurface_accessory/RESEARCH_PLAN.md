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
- **H1**: Multi-heme cytochrome content is enriched in deep-clay Bacillota_B vs soil-baseline Bacillota_B. Detection method (v1.2 update — PF14537 confirmed silently absent from `bakta_pfam_domains`, the documented `plant_microbiome_ecotypes` pitfall): use **PF02085 Cytochrom_CIII** (3,203 hits in `bakta_pfam_domains`, multi-heme c-type) + **PF22678 Cytochrom_c_NrfB-like** (388 hits, multi-heme nitrite reductase) + **CXXCH heme-binding motif count ≥4 in `gene_cluster.faa_sequence`** (the canonical method since Methé et al. 2003 *Geobacter*). A genome scores positive for "multi-heme cytochrome IR potential" if it carries ≥1 cluster matching any of these three signals. **This corrects the clay_confined_subsurface H3 IR-side, which used K07811/K17324/K17323 — KOs that turn out to be TMAO reductase, glycerol ABC, and glycerol permease respectively, not iron-reduction markers.**

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

### Pangenome scale check (v1.2 update)

`COUNT(*)` confirmed at plan-revision time: BERDL pangenome contains exactly **334 Bacillota_B genomes** across all habitats — much smaller than the 6,700 estimate in v1.1 (which conflated multiple Firmicutes-derived phyla). With 5 known Mont Terri Opalinus Bacillota_B + BacDive expansion (~10–20 expected from clay sample_type × Bacillota_B genera) + a phylum-internal soil baseline (whatever fraction of the remaining ~310 are soil/sediment-isolated), the cohort sizes are tighter than originally planned. The cohort-size fallback in NB01 is now load-bearing rather than a sanity check.

## Query Strategy

### Execution environment

All Spark queries (NB01 universe assembly, NB02 cluster-presence, NB04 cluster annotation, NB06 PFAM pull) run on **BERDL JupyterHub on-cluster** with the kernel-injected `spark = get_spark_session()`. NB03 (Fisher per OG) and NB05 (compactness test) run locally in pandas/scipy on the parquet outputs.

### Unit of analysis: eggNOG OG, NOT `gene_cluster_id`

`kbase_ke_pangenome.gene_cluster.gene_cluster_id` is **species-specific** per the schema (`docs/schemas/pangenome.md`). Cluster IDs do not generalize across species, so a Fisher test on `gene_cluster_id` for a multi-species cohort would compare apples-to-oranges. Instead, **NB02 maps each genome's gene clusters to their `eggNOG_OGs` annotation** (from `eggnog_mapper_annotations.eggNOG_OGs`, which carries cross-species OG IDs at the appropriate taxonomic depth), and **NB03 runs Fisher's exact at OG level** (anchor presence vs baseline presence per OG, BH-FDR-corrected). The eggNOG OG namespace is the cross-species orthology surrogate.

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

### NB01 — Bacillota_B universe + cohort assembly + IR-PFAM availability check (Spark)
- **Goal**: Pull all 334 Bacillota_B genomes from BERDL pangenome with QC + isolation_source. Identify deep-clay anchor (incl. BacDive expansion) and phylum-matched soil-baseline. **Confirm that the IR-detection PFAMs we plan to use in NB06 (PF02085 Cytochrom_CIII, PF22678 Cytochrom_c_NrfB-like) are present in `bakta_pfam_domains` for Bacillota_B genomes specifically** (we verified the table-level row counts during plan-writing; NB01 confirms within-phylum availability so we don't run NB06 on a phylum where these PFAMs happen to also be silently absent).
- **Inputs**: `gtdb_taxonomy_r214v1`, `genome`, `gtdb_metadata`, `ncbi_env`, `bacdive.isolation` + `taxonomy`, `bakta_pfam_domains` (PF02085 + PF22678 within-Bacillota_B count).
- **Outputs**: `data/bacillota_b_universe.tsv` (334 genomes with metadata), `data/cohort_assignments.tsv` (anchor + baseline tagged), `data/ir_pfam_availability.tsv` (Bacillota_B-specific PF02085 and PF22678 row counts — gate output for NB06).
- **Cohort size fallback**: With only 334 Bacillota_B genomes total, the soil-baseline draw is bounded above by however many soil/sediment-isolated genomes exist in this universe. If BacDive linkage yields <10 deep-clay Bacillota_B beyond the 5 from the clay project, expand the anchor by including all clay-mentioning Bacillota_B in `ncbi_env` (relaxing the deep/shallow distinction). Minimum viable n=10 anchor for H1 OG-level Fisher tests; if even that isn't reached, document and proceed with descriptive analysis only.

### NB02 — Genome × eggNOG-OG presence matrix (Spark + local)
- **Goal**: For each cohort genome (anchor + baseline), pull its full set of `gene_cluster_id`s via `gene_genecluster_junction`, then map each cluster to its `eggNOG_OGs` value in `eggnog_mapper_annotations`. Aggregate to a sparse genome × OG boolean matrix (one row per (genome_id, og_id) presence).
- **Performance**: For ~250 cohort genomes against the 1B-row `gene_genecluster_junction`, use the BROADCAST-temp-view pattern (per `cofitness_coinheritance` pitfall in `docs/pitfalls.md`): create a small temp view of cohort `genome_id`s and broadcast it into the join. Then join eggnog annotations on the resulting cluster IDs (smaller intermediate). If `kbase_uniprot.uniprot_identifier` ends up in the join path (it shouldn't here), set `spark.sql.autoBroadcastJoinThreshold = -1` per the `bakta_reannotation` pitfall.
- **Outputs**: `data/cohort_og_presence.parquet` (long-format genome_id, og_id pairs).

### NB03 — Per-OG enrichment test (local)
- **Goal**: For each eggNOG OG present in any cohort genome, Fisher's exact test (anchor vs baseline). BH-FDR correct across all OGs tested. Keep OGs with q<0.05 AND fold-difference ≥3 AND minimum support (≥3 anchor genomes).
- **Outputs**: `data/og_enrichment.tsv` (one row per significant OG, columns: og_id, anchor_n, anchor_pos, baseline_n, baseline_pos, OR, p, p_BH, fold_diff).

### NB04 — Functional annotation of enriched OGs (Spark + local)
- **Goal**: For the significant OGs from NB03, pull representative eggNOG annotations (KEGG_ko, COG_category, PFAM, Description) for clusters tagged with each OG. Group by functional category and per-OG-best annotation.
- **Outputs**: `data/enriched_ogs_annotated.tsv`, `figures/h1_functional_categories.png`.

### NB05 — H2 genome-compactness test (local)
- **Goal**: Compare genome size and gene count distributions (anchor vs baseline) after CheckM-completeness rescaling. Wilcoxon + Cohen's d.
- **Outputs**: `data/h2_compactness.tsv`, `figures/h2_genome_size.png`.

### NB06 — Phase 1 correction: clay_confined_subsurface H3 IR-side (Spark + local)
- **Goal**: Re-do the clay project's iron-reduction analysis using a triple-signal multi-heme cytochrome detector (PF14537 was silently absent so it can't be used; alternatives confirmed available during plan-writing). Write a corrected H3 result.
- **Method** (v1.2 revised — PF14537 silent absence forced this change):
  1. Pull `bakta_pfam_domains` rows for PF02085 (Cytochrom_CIII) and PF22678 (Cytochrom_c_NrfB-like), restricted to clay project's anchor + shallow + baseline genome IDs (re-loaded from `clay_confined_subsurface/data/cohort_assignments.tsv` and `baseline_features.parquet`).
  2. Pull `gene_cluster.faa_sequence` for all clusters belonging to the clay cohort genomes; count `CXXCH` heme-binding motif occurrences per protein in pandas (regex on the protein sequence). Multi-heme cytochrome candidate = ≥4 CXXCH motifs.
  3. Per-genome IR-corrected score: `has_multiheme_cytochrome` = (genome carries ≥1 cluster with PF02085) OR (≥1 cluster with PF22678) OR (≥1 cluster with ≥4 CXXCH motifs in faa_sequence).
  4. Re-test the clay H3 hypothesis (deep clay vs shallow vs soil) with the corrected IR marker.
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
- **v1.1** (2026-04-30): Addressed `PLAN_REVIEW_1.md` feedback. (a) Clarified unit of analysis is **eggNOG OG**, not species-specific `gene_cluster_id`, with explicit explanation of why and the new `eggNOG_OGs` field used for cross-species orthology. (b) Moved PF14537 availability validation from NB06 to NB01 as a precondition gate. (c) Added explicit execution-environment section. (d) Added BROADCAST-temp-view performance pattern for the 1B-row gene/junction join in NB02. (e) Added cohort-size fallback strategy if BacDive linkage yields <10 deep-clay Bacillota_B.
- **v1.2** (2026-04-30): Pre-NB01 schema probe revealed two important data realities. (a) **PF14537 (Cytochrom_NNT) confirmed silently absent from `bakta_pfam_domains`** (0 hits in entire 132M-row table) — the documented `plant_microbiome_ecotypes` pitfall confirmed for our specific marker. NB06 IR-correction method revised: now uses PF02085 (Cytochrom_CIII, 3,203 hits, multi-heme c-type), PF22678 (Cytochrom_c_NrfB-like, 388 hits, multi-heme nitrite reductase), and CXXCH heme-binding motif counting on `gene_cluster.faa_sequence` (canonical Methé 2003 *Geobacter* method) as a triple-signal detector. (b) **Bacillota_B universe is 334 genomes, not the 6,700 estimated in v1.1** — the larger number conflated multiple Firmicutes-derived phyla. Cohort-size fallback is now load-bearing rather than a sanity check.

## Authors

David Lyon (ORCID: [0000-0002-1927-3565](https://orcid.org/0000-0002-1927-3565)) — KBase
