# BERIL Research Observatory - Reusable Data Inventory

**Generated:** April 24, 2026
**Last Updated:** April 25, 2026 (Phase 2b refresh)

## Summary

This document catalogues reusable data across BERIL projects, with focus on what can support the **plant_microbiome_ecotypes** project and other cross-project analyses.

---

## Plant Microbiome Ecotypes - Active Dataset (73 files, 873 MB, 7.8M rows)

Located: `/home/aparkin/BERIL-research-observatory/projects/plant_microbiome_ecotypes/data/`

**Project status:** Phase 2b complete (April 25, 2026). All 8 hypotheses (H0–H7) carry defensible verdicts; all five paired-adversarial-review issues closed. See `projects/plant_microbiome_ecotypes/REPORT.md` §11 for the synthesis and `docs/adversarial_review_2026-04-24.md` for the paired adversarial review that drove the corrections.

**Phase 1/2/2b structure**:
- *Phase 1* generated the foundational pangenome marker analysis (NB01–NB08), classification cohorts, and complementarity tests.
- *Phase 2* extended with InterProScan-based marker recovery, KEGG-module-gated refinement, MGnify cross-validation, and within-species subclade clustering (NB09–NB12).
- *Phase 2b* (NB13–NB15 + 4 follow-up scripts) closed adversarial-review issues: real per-species genome-size control, cluster-robust GLM as a PGLMM analogue, full 65→18 species subclade scan, db-RDA location-vs-dispersion decomposition, and a bakta-vs-IPS Pfam audit. Some Phase 1 files are now superseded but kept for chronology — flagged below.

### Core Reference Datasets

#### 1. **genome_environment.csv** (65.9 MB, 293,059 rows)
**Purpose:** Maps genomes to environmental/ecological context and taxonomy
```
Columns: genome_id, ncbi_isolation_source, phylum, class, order, family, genus, species, 
          gtdb_species_clade_id, compartment, is_plant_associated, host_is_plant, 
          env_broad_is_plant, host, env_broad_scale, bacdive_is_plant
```
**Key features:**
- Plant-associated classification (binary indicators)
- Host information (e.g., "Homo sapiens", plant species names)
- Environment classification (plant compartment: rhizosphere, phyllosphere, endosphere, other)
- NCBI isolation source text (raw, unstructured)

**Reusability:** Foundation for any plant-microbe linkage analysis across projects

> **Phase 2b note**: `genome_id` is GTDB-prefixed (`RS_GCF_*`, `GB_GCA_*`). Cross-references to `phylogenetic_tree_distance_pairs` use *bare* NCBI accessions and require prefix-prepending — see `docs/pitfalls.md`.

---

#### 2. **cohort_assignments.csv** (3.0 MB, 25,660 rows)  *— Phase 1*
**Purpose:** Species-level functional phenotype classification (composite scoring)
```
Columns: gtdb_species_clade_id, genus, dominant_compartment, pgp_score_raw, pathogen_score_raw,
          composite_pgp, composite_pathogen, core_fraction, avg_complementarity, cohort,
          n_pgp_functions, n_pathogen_functions
```
**Cohort values:** beneficial, neutral, pathogenic

**Reusability:** Phase 1 cohort labels — useful for legacy comparison with `species_cohort_refined.csv`.

---

#### 2b. **species_cohort_refined.csv** (2.5 MB, 25,660 rows)  *— Phase 2 (preferred)*
**Purpose:** Refined species-level cohort using 17 plant-specific markers + KEGG-module gating (NB10)
```
Columns: gtdb_species_clade_id, genus, phylum, is_plant_associated, cohort_refined,
          n_pgp_refined, n_pathogen_refined, n_host_genomes, dominant_host, n_hosts, all_hosts
```
**Cohort values:** beneficial, pathogenic, dual-nature, neutral

**Key changes from Phase 1**:
- Removed 6 ubiquitous markers (flagella, chemotaxis, T6SS, biofilm, quorum sensing, T2SS) that had only 1.2–2.4× plant enrichment.
- Applied KEGG-module completeness gating (M00175 N-fix ≥2 genes; M00332 T3SS ≥3 genes; M00333 T4SS ≥3 genes) — removed 8,855 false-positive T3SS calls.
- Adds `dual-nature` as an explicit fourth class (78.7% of plant-associated species).

> **Phase 2b validation caveat**: Per the species-level test in NB13 against 18 model organisms, the *categorical* cohort label is uninformative at species level (all 14 known beneficial + pathogenic species were assigned to dual-nature). The discriminative signal is the *continuous* `n_pathogen_refined / (n_pgp_refined + n_pathogen_refined)` ratio (Mann-Whitney p=0.027 on N=7+7). Use the continuous ratio for ranking; treat the cohort label as a coarse screen.

---

#### 3. **gapmind_plant_species.csv** (137.3 MB, 2,213,340 rows)
**Purpose:** Metabolic pathway completeness for species × metabolic function
```
Columns: gtdb_species_clade_id, pathway, metabolic_category, complete
```
**Metabolic categories:** carbon, aa (amino acid), nucleotide, cofactor
**Completeness:** Binary (0.0 = incomplete, 1.0 = complete)

**Scope:** ~2.2 million species-pathway relationships; covers essential biosynthesis

**Reusability:** 
- Phenotype prediction (which species can synthesize amino acids, vitamins, cofactors?)
- Niche complementarity (which species pairs could metabolically cooperate?)
- Cross-validation for PGP potential (e.g., IAA biosynthesis requires tryptophan pathway)

---

#### 4. **bacdive_isolation.csv** (1.7 MB, 23,988 rows)
**Purpose:** Manual curation of isolation context from BacDive
```
Columns: gca_accession, bacdive_id, cat1, cat2, cat3, sample_type
```

**Reusability:** High-confidence mapping to specific plant hosts and tissues (curated); bridges genome→plant isolation evidence

---

#### 5. **hypothesis_verdicts_final.csv** (5.3 KB, 8 rows)  *— Phase 2b canonical*
**Purpose:** Final post-Phase-2b verdicts for all 8 hypotheses (H0–H7)
```
Columns: id, hypothesis, phase1_verdict, phase2b_evidence, final_verdict, notebooks
```

**Use this as the authoritative source** for hypothesis status when integrating findings into other projects. Preferred over reading verdicts off chronological notebook outputs.

---

### Functional Annotation Datasets

#### 6. **bakta_marker_hits.csv** (49.0 MB, 387,822 rows)  *— Phase 1*
**Purpose:** Annotated gene clusters for PGP/pathogenic markers (gene-name search)
```
Columns: gene_cluster_id, gene, product, kegg_orthology_id, gtdb_species_clade_id, is_core, is_auxiliary, is_singleton
```
**Genes:** nifH, acdS, pqqA-E, ipdC, hcnA-C, + 50 pathogenic markers (cwde_cellulase, t2ss, t6ss, etc.)

**Reusability:** Trait-by-species matrix; core/accessory status indicates HGT vs. vertical inheritance

---

#### 6b. **interproscan_marker_hits.csv** (44.4 MB, 280,193 rows)  *— Phase 2 (preferred for secretion systems)*
**Purpose:** InterProScan domain hits for marker recovery (NB10)
```
Columns: gene_cluster_id, analysis, signature_acc, signature_desc, ipr_acc, ipr_desc, gtdb_species_clade_id, is_core
```

**Reusability:** Use for T3SS/T4SS/T6SS/CWDE marker queries. The bakta_pfam_domains BERDL table silently omits ~12 of these Pfam accessions — see Phase 2b audit (`pfam_bakta_ips_audit.csv`) and `docs/pitfalls.md`.

---

#### 6c. **pfam_recovery_hits.csv** (1.5 MB, 19,364 rows)  *— Phase 2b (NB13)*
**Purpose:** Recovered Pfam hits via LIKE query (versioned ID format fix)
```
Columns: gene_cluster_id, pfam_id, gtdb_species_clade_id, is_core, pfam_bare
```

**Reusability:** Genuine new marker coverage for nitrogen fixation (+2,872 species) and CWDEs (+811/+1,082); for T3SS/T4SS/T6SS, see `interproscan_marker_hits.csv` instead.

---

#### 6d. **pfam_bakta_ips_audit.csv** (0.7 KB, 22 rows)  *— Phase 2b cross-project gotcha*
**Purpose:** Documents which marker Pfams are silently missing from `bakta_pfam_domains` despite being abundant in `interproscan_domains`
```
Columns: pfam_id, ips_hits, ips_species, bakta_hits, bakta_species, silent_gap
```

**Cross-project relevance:** 12 of 22 marker Pfams (nearly all secretion-system components — T3SS, T4SS, T6SS) silently absent from the bakta source despite InterProScan having them in 18,000+ gene clusters. **Future BERDL projects: cross-check `bakta_pfam_domains` against `interproscan_domains.signature_acc` before drawing conclusions about absent functions.** See `projects/plant_microbiome_ecotypes/docs/pitfalls.md`.

---

#### 7. **kegg_marker_hits.csv** (6.1 MB, 39,640 rows)
**Purpose:** KEGG orthology mapping for functional markers
```
Columns: gene_cluster_id, KEGG_ko, Description, gtdb_species_clade_id, is_core, is_auxiliary
```

**Reusability:** Functional annotation cross-validation; pathway reconstruction

---

#### 7b. **kegg_module_completeness.csv** (1.0 MB, 19,665 rows)  *— Phase 2 (NB10)*
**Purpose:** KEGG module gene counts per species — used for multi-gene-system gating (T3SS M00332, T4SS M00333, N-fix M00175)
```
Columns: gtdb_species_clade_id, module, n_genes, ...
```

---

#### 8. **marker_gene_clusters.csv** (67.0 MB, 588,098 rows)
**Purpose:** Full pangenome-level gene cluster membership
```
Columns: gene_cluster_id, gtdb_species_clade_id, is_core, is_auxiliary, is_singleton, cluster_size, mean_cluster_identity, cluster_prevalence
```

**Reusability:** Genome-wide accessory gene burden; horizontal gene transfer inference

---

#### 9. **product_marker_hits.csv** (32.1 MB, 256,269 rows)
**Purpose:** Gene product annotations (text-based functional labels)

---

#### 10. **species_marker_matrix.csv** (5.2 MB, 25,660 rows)  *— Phase 1*
**Purpose:** Species × 25 functional markers binary matrix (Phase 1 panel)

#### 10b. **species_marker_matrix_v2.csv** (2.3 MB, 25,660 rows)  *— Phase 2 (preferred)*
**Purpose:** Species × 17 plant-specific markers with KEGG-module gating (NB10)

---

#### 11. **genome_host_species.csv** (1.5 MB, 11,852 rows)  *— Phase 2 (NB10)*
**Purpose:** Per-genome plant host assignments parsed from NCBI isolation source
```
Columns: genome_id, gtdb_species_clade_id, compartment, host_species, ncbi_isolation_source, genus, phylum
```
**Hosts identified:** rice (286 species), *Arabidopsis* (184), wheat (122), maize (98), soybean (84), potato/tomato (~57 each), and 14 others (≥10 species each).

**Reusability:** Bridge between pangenome and host-specific community studies.

---

### Novel-OG Annotation (NB09)

#### 12. **novel_og_annotations.csv** (26.0 KB, 50 rows)
**Purpose:** Aggregate functional annotations for the 50 plant-enriched eggNOG OGs

#### 12a–f. **novel_og_eggnog_annotations.csv** (275.5 MB, 1.2M rows), **novel_og_bakta.csv** (681 KB, 12,580 rows), **novel_og_interproscan.csv** (374 KB, 4,455 rows), **novel_og_domains.csv** (383 KB, 4,455 rows), **novel_og_go_terms.csv** (46 KB, 1,544 rows), **novel_og_pathways.csv** (63 KB, 2,317 rows)
**Purpose:** Per-source detailed annotations contributing to the aggregate

**Reusability:** All 50 OGs are functionally characterized (cytochrome c oxidase, Fe-S cluster, ion transport, energy metabolism dominate); none are hypothetical. **Verified to survive real per-species genome-size + phylum control: 48/50 at q<0.05 BH-FDR** (see `genome_size_control.csv`).

---

#### 13. **top50_og_species.csv** (3.5 MB, 25,124 rows)
**Purpose:** Species × 50 plant-enriched OGs presence/absence matrix
```
Columns: gtdb_species_clade_id, COG0026, COG0109, ... (50 COGs)
```

**Reusability:** Rapid feature extraction for ML; the per-species ground-truth used in the Phase 2b genome-size control.

---

#### 14. **enrichment_results.csv** (848 KB, 5,671 rows)
**Purpose:** Genome-wide eggNOG OG enrichment in plant-associated vs. non-plant species

#### 14b. **novel_plant_markers.csv** (11.4 KB, 50 rows)
**Purpose:** The 50 plant-enriched OGs surviving phylum-level logistic regression

#### 14c. **logistic_phylo_controlled.csv** (7.8 KB, 50 rows)  *— Phase 1 NB03*
**Purpose:** Phylum-controlled logistic regression results for the 50 OGs

---

### Phase 2b Statistical Controls (April 24–25, 2026)

These files document the closure of all five paired-adversarial-review issues. They supersede the corresponding Phase 2 draft analyses.

#### 15. **c1_cluster_robust.csv** (2.6 KB, 17 rows)  *— item 18 closure*
**Purpose:** Cluster-robust GLM (cluster=genus) for 17 markers — proper Wald inference, no L1 shrinkage
```
Columns: marker, n_pos, coef_plant, se_plant_robust, p_plant, or_plant, ci_lo, ci_hi,
          q_plant_bh, survives_strict, note
```
**Result:** 8/14 markers significant at q<0.05 BH-FDR with 95% Wald CIs excluding zero (ACC deaminase OR=8.01, T3SS OR=2.71, N-fix OR=2.71, phenazine OR=2.12, CWDEs, phosphate-sol, effector). Three-tier interpretation when combined with within-genus shuffle (`sensitivity_shuffle.csv`).

#### 15b. **regularized_phylo_control.csv** (1.3 KB, 17 rows)  *— Phase 2b draft (kept for comparison)*
**Purpose:** L1-regularized logit (NB14 Cell 2). Bootstrap CIs are biased near zero (Chatterjee & Lahiri 2011) — use `c1_cluster_robust.csv` as the canonical version.

#### 15c. **sensitivity_shuffle.csv** (1.2 KB, 15 rows)
**Purpose:** Within-genus label shuffling — strictest species-level phylogenetic null test. **3/15 markers survive** (nitrogen fixation, ACC deaminase, T3SS).

#### 15d. **sensitivity_results.csv** (0.2 KB, 1 row)
**Purpose:** Aggregate sensitivity scalars (PERMANOVA exclude-top-3 R², n, etc.).

---

#### 16. **genome_size_control.csv** (8.9 KB, 50 rows)  *— item 17 closure*
**Purpose:** Real per-species genome-size + phylum control for the 50 novel OGs (NB14 Cell 3, replacing the earlier circular Bernoulli simulation flagged by adversarial review)
```
Columns: og_id, n_pos_species, prev_plant_observed, prev_nonplant_observed,
          coef_plant_controlled, coef_genome_size, odds_ratio_controlled,
          p_plant, se_plant, q_plant, survives_strict, note
```
**Result:** 48/50 OGs survive at q<0.05 BH-FDR with |coef|>0.2; 2 fail to fit due to singular matrix (perfect separation by phylum). Top OR's: COG1845 (cytochrome ox ctaE) = 6.58, COG0843 = 6.15, COG0654 = 6.12, etc.

---

#### 17. **h1_dbrda_results.csv** (0.2 KB, 1 row), **h1_compartment_dispersions.csv** (0.2 KB, 3 rows)  *— item 20 closure*
**Purpose:** PERMANOVA + PERMDISP + db-RDA decomposition for H1 location-vs-dispersion separation
```
Columns: permanova_F, permanova_p, permanova_R2, permdisp_F, permdisp_p,
          dbrda_R2, dbrda_p, location_fraction, n_species, n_compartments
```
**Result:** Location-only db-RDA R² = 0.060 (84% of total PERMANOVA 0.071); PERMDISP F = 15.6 (p=0.001) confirms dispersion heterogeneity. Original Phase 1 R² = 0.527 was a panel + sampling artifact (86% loss after exclude-top-3-species per compartment).

---

#### 18. **complementarity_v2.csv** (120 KB, 2,346 rows)
**Purpose:** Prevalence-weighted GapMind complementarity (NB14, replacing NB06's max-aggregation)
```
Columns: genus_A, genus_B, complementarity_prev, is_cooccurring, n_co_samples, complementarity_max
```
**Result:** |Cohen's d| ≈ 0.4 (was reported as 7.54 in NB06 due to a Cohen's d formula error — divided by SD of permutation means, not raw pair SD). Direction (redundancy) robust under both methods; magnitude now credible. **Use this file, not the original `complementarity_network.csv`, for the canonical H3 result.**

---

#### 19. **species_validation.csv** (2.3 KB, 18 rows)  *— C3 closure*
**Purpose:** Species-level validation against 18 model organisms (7 known beneficial, 7 known pathogenic, 4 neutral)
```
Columns: search_term, gtdb_species, ground_truth, evidence, cohort_refined,
          n_pgp_refined, n_pathogen_refined, pathogen_ratio
```
**Result:** All 14 known beneficial + pathogenic species classified as dual-nature (categorical label uninformative at species level); Mann-Whitney U=9, p=0.027 on the continuous pathogen_ratio (N=7+7). Replaces the earlier 92.7% genus-level validation, which was tautological.

---

#### 20. **subclade_full_scan.csv** (3.2 KB, 18 rows)  *— item 19 closure*
**Purpose:** Full 65→18 species subclade × plant-association scan with Bonferroni and BH-FDR
```
Columns: species, n_genomes, n_subclades, n_plant, n_nonplant, best_subclade,
          best_plant_frac, fisher_p, chi2_p, min_E, frac_E_below_5, cochran_ok,
          testable, fisher_q_bh, passes_bonferroni
```
**Result:** 5/17 testable species pass Bonferroni-Fisher (X. vasicola, Mesorhizobium sp002294985, A. pusense, P. avellanae, X. campestris); 3 also Cochran-valid. **47/65 candidate species lack phylo-tree coverage in BERDL** — a database-level limitation, not a methodology issue.

#### 20b. **species_subclade_definitions_full.csv** (216 KB, 2,414 rows)
**Purpose:** Genome-level subclade assignments with MDS coordinates for the 18 species with phylo-tree data

#### 20c. **species_subclade_definitions.csv** (142 KB, 1,306 rows)  *— Phase 2 (5-species subset, kept for figure provenance)*

#### 20d. **subclade_enrichment_corrected.csv** (0.7 KB, 5 rows)  *— Phase 2b (5-species subset, replaced by full scan)*

---

#### 21. **h6_host_subclade_full.csv** (2.6 KB, 18 rows)  *— H6 follow-up*
**Purpose:** Subclade × plant-host scan for the 18 species with phylo data (within-species Bonferroni for pair search + across-species correction)
```
Columns: species, n_with_host, n_hosts, n_subclades_with_host, chi2_perm_p,
          min_E, cochran_ok, fisher_best_p, fisher_best_p_bonf_within,
          n_pairs_tested, best_pair, fisher_q_bh_across, passes_bonferroni_across
```
**Result:** 2/9 species pass both within- and across-species Bonferroni: **X. campestris × Brassica** (46/47 in best subclade, p=2.7×10⁻¹² raw) and **X. vasicola × Zea mays** (47/52, p=1.4×10⁻¹¹) — canonical pathovar-host specializations confirmed at the genomic level.

---

### Summary & Aggregation Datasets

#### 22. **pangenome_stats.csv** (1.8 MB, 27,702 rows)
**Purpose:** Pangenome-level statistics per species
```
Columns: gtdb_species_clade_id, no_genomes, no_core, no_aux_genome, no_singleton_gene_clusters, openness
```

#### 23. **complementarity_network.csv** (162 KB, 2,346 rows)  *— Phase 1 (use complementarity_v2.csv instead)*

#### 24. **genus_dossiers.csv** (7.6 KB, 30 rows), **genus_dossiers_plant_only.csv** (1.6 KB, 4 rows)
**Purpose:** Summarized genus-level phenotypes and marker profiles

#### 25. **genomic_architecture.csv** (2.5 KB, 23 rows)
**Purpose:** Per-function genomic architecture summary (core/accessory/singleton fractions by marker type)

#### 26. **species_compartment.csv** (2.5 MB, 26,511 rows)
**Purpose:** Dominant ecological niche per species

#### 27. **species_family_taxonomy.csv** (1.7 MB, 27,690 rows)  *— NB08*
**Purpose:** Species-level GTDB family assignments

#### 28. **compartment_profiles.csv** (8.7 KB, 96 rows)
**Purpose:** Per-marker × compartment Fisher enrichment results

#### 29. **genus_profiles.csv** (3.3 KB, 30 rows)
**Purpose:** Top plant-associated genus profiles

#### 30. **compartment_census_summary.csv** (0.1 KB, 9 rows)
**Purpose:** Compartment species counts (root 292, rhizosphere 160, phyllosphere 157, endophyte 29, plant_other 498, total plant 1,136)

---

### Environmental & Ecological Datasets

#### 31. **ncbi_env_pivot.csv** (27.5 MB, 279,547 rows)
**Purpose:** NCBI isolation source standardized to entity-attribute-value format

#### 32. **nmdc_soil_file_ids.csv** (2.6 MB, 25,890 rows), **nmdc_genus_abundance.csv** (2.2 MB, 49,279 rows)
**Purpose:** NMDC metagenome metadata + genus abundance

#### 33. **bacdive_metabolites_genera.csv** (3.9 MB, 137,599 rows)
**Purpose:** Compound utilization phenotypes by genus (BacDive)

---

### MGnify Cross-Validation (NB11)

#### 34. **mgnify_pangenome_bridge.csv** (854 KB, 20,473 rows)
**Purpose:** MGnify species → GTDB taxonomy bridge

#### 35. **mgnify_host_specificity.csv** (16 KB, 265 rows)
**Purpose:** Genus × rhizosphere biome presence (tomato/maize/barley/soil)

#### 36. **mgnify_mobilome.csv** (928 KB, 17,323 rows)
**Purpose:** Mobile element annotations (IS, plasmid, prophage, viral) — supports the H4 mobilome enrichment finding (3.7 vs 2.8 MEs/genome, p=1.5e-5)

#### 37. **mgnify_bgc_profiles.csv** (253 KB, 8,089 rows)
**Purpose:** Biosynthetic gene cluster profiles by genus (NRP/PKS/etc.) — 84 plant-associated genera identified as NRP/siderophore producers

#### 38. **mgnify_kegg_biome_profiles.csv** (77 KB, 2,630 rows), **mgnify_rhizo_vs_soil_cog.csv** (2.6 KB, 96 rows), **mgnify_soil_bgc_summary.csv** (610 KB, 13,584 rows)
**Purpose:** Cross-biome KEGG/COG/BGC summaries

---

### Other Files

- **transposase_singletons.csv** (104.4 MB, 986,464 rows) — Transposase/integrase singleton clusters; transposase co-occurrence OR=15.95 with marker singletons.
- **pfam_marker_hits.csv** (0 rows) — *Phase 1 artefact: empty due to versioned-Pfam-ID query bug in NB02; replaced by `pfam_recovery_hits.csv` after the LIKE-query fix in NB13.*
- **pfam_investigation_cache.csv** (1.2 KB, 36 rows) — NB08 Pfam investigation results.
- **subclade_og_enrichment.csv** (0.5 KB, 5 rows), **subclade_host_corrected.csv** (0.2 KB, 2 rows), **subclade_host_mapping.csv** (0 rows) — Phase 2 subclade artifacts; superseded by `subclade_full_scan.csv` and `h6_host_subclade_full.csv` for the canonical results.
- **phylo_control_results.csv** (0.4 KB, 14 rows) — Phase 2 NB10 phylo control attempt (0/14 converged; superseded by `c1_cluster_robust.csv`).

---

## Other Projects with Reusable Data

### High-Value Cross-Project Resources

#### Conservation vs. Fitness (22 MB)
**File:** `/home/aparkin/BERIL-research-observatory/projects/conservation_vs_fitness/data/fb_pangenome_link.tsv`
- **Purpose:** DIAMOND BBH pangenome ↔ fitness browser linkage
- **Scope:** ~30 organisms
- **Use case:** Cross-validate plant-microbe predictions against experimentally measured fitness

#### Functional Dark Matter (145 MB)
**Directory:** `/home/aparkin/BERIL-research-observatory/projects/functional_dark_matter/data/`
- `carrier_genome_map.tsv`: Uncharacterized ortholog carrier distributions
- `biogeographic_profiles.tsv`: Environmental patterns of dark matter genes
- **Use case:** Predict ecological roles of novel plant-associated genes

#### CF Formulation Design (35 MB)
**Directory:** `/home/aparkin/BERIL-research-observatory/projects/cf_formulation_design/data/`
- `asma_pa_virulence_profiles.tsv`: Pseudomonas virulence markers
- **Use case:** Validation of pathogenic marker predictions in cystic fibrosis-relevant taxa

#### Essential Genome (9.3 MB)
**Directory:** `/home/aparkin/BERIL-research-observatory/projects/essential_genome/data/`
- **Use case:** Overlay essential genes onto plant-microbiome ecotypes

#### ENIGMA SSO ASV Ecology (7.4 MB)
**Directory:** `/home/aparkin/BERIL-research-observatory/projects/enigma_sso_asv_ecology/data/`

#### PHB Granule Ecology (38 MB)
**Directory:** `/home/aparkin/BERIL-research-observatory/projects/phb_granule_ecology/data/`

#### Prophage Ecology (1.4 GB)
**Directory:** `/home/aparkin/BERIL-research-observatory/projects/prophage_ecology/data/`

#### Microbiome Grammar (800 KB)
**Directory:** `/home/aparkin/BERIL-research-observatory/projects/microbiome_grammar/data/`

---

## Cross-Project Pitfalls (from Phase 2b)

These have been added to `projects/plant_microbiome_ecotypes/docs/pitfalls.md` and are worth noting for any future BERDL work:

1. **`bakta_pfam_domains` silently omits ~half of marker Pfams** (especially T3SS/T4SS/T6SS components). Always cross-check `interproscan_domains.signature_acc` before drawing conclusions about absent functions.
2. **Versioned Pfam IDs**: `bakta_pfam_domains.pfam_id` stores versioned accessions (`PF00771.22`). Use `LIKE 'PF00771%'` rather than `IN ('PF00771')`.
3. **`phylogenetic_tree_distance_pairs` is sparse** — only ~28% of plant-associated species with ≥20 genomes have tree data. Pre-check coverage before any subclade analysis.
4. **Genome-ID prefix mismatch**: `phylogenetic_tree_distance_pairs.genome*_id` uses bare NCBI accessions (`GCA_*`, `GCF_*`), while `genome` and `ncbi_env` tables use GTDB-prefixed IDs (`GB_GCA_*`, `RS_GCF_*`). Add the prefix before joining.
5. **`species_compartment.csv` column is `dominant_compartment`, not `compartment`** — `genome_environment.csv` does have `compartment`.
6. **Cohen's d formula sensitivity**: dividing the mean difference by the SD of permutation means (instead of the raw pair-level SD) inflates apparent effect sizes by 10–20×. Use the raw pair-level SD as the denominator for cross-study comparability.

---

## Data Integration Recommendations

### For plant_microbiome_ecotypes Extensions

1. **Validate ecotype predictions using NMDC abundance data**
   - Join `species_cohort_refined.csv` (preferred over `cohort_assignments.csv`) with `nmdc_genus_abundance.csv`
   - Hypothesis: predicted beneficial genera should be abundant in soil; pathogenic should be rare

2. **Cross-validate with experimentally measured fitness**
   - Use `fb_pangenome_link.tsv` from `conservation_vs_fitness`
   - Subset to plant-associated organisms; compare predicted phenotypes with measured fitness

3. **Add HGT burden stratification**
   - Use `openness` from `pangenome_stats.csv`, `transposase_singletons.csv`, and `mgnify_mobilome.csv`
   - Hypothesis: PGP genes in high-openness genomes indicate recent adaptive acquisition

4. **Integrate metabolic models**
   - Merge `gapmind_plant_species.csv` with `complementarity_v2.csv` (not the original `complementarity_network.csv`)
   - Identify consortia with complementary biosynthetic capacity

5. **Defense system integration**
   - Use `prophage_ecology/data/enriched_lineages.tsv`
   - Test if plant-associated pathogenic markers co-occur with specific prophages

6. **Use canonical Phase 2b verdicts**
   - Read `hypothesis_verdicts_final.csv` for the authoritative state of H0–H7 rather than parsing chronological notebook outputs

---

## Data Access Notes

- **On-cluster use:** All data is locally accessible (no Spark needed for CSV reads)
- **File formats:** All CSV (UTF-8, comma-delimited)
- **Indexing:** `gtdb_species_clade_id` is the universal key across most files; `genome_id` for genome-level
- **Size warning:** `gapmind_plant_species.csv` (137 MB) and `novel_og_eggnog_annotations.csv` (276 MB) should be filtered before in-memory loading

**Last updated:** April 25, 2026 (Phase 2b refresh)
**Maintainer:** Adam Arkin (aparkin@berkeley.edu)
