# Plant Microbiome Ecotypes — Compartment-Specific Functional Guilds and Their Genetic Architecture

## Research Question

What is the genomic basis for plant-microbe associations across different plant compartments (rhizosphere, root, leaf/phyllosphere, endophyte) and specific plant hosts? Can we classify plant-associated microbial genera into beneficial, neutral, pathogenic, and dual-nature cohorts with mechanistic hypotheses, identify which plant-interaction functions are associated with horizontal gene transfer vs. stable vertical inheritance, and characterize within-species strain variation in plant-adaptation genes?

## Hypotheses

**H0_phylo (Phylogenetic Null)**: Functional differences between plant-associated and non-plant species are explained by phylogenetic distance alone. Tested with genus-level fixed effects across all hypotheses.

**H1 (Compartment Specificity)**: Different plant compartments harbor microbial communities with distinct functional profiles. Rhizosphere species are enriched in nutrient acquisition (phosphate solubilization, siderophores, nitrogen fixation), while phyllosphere species are enriched in stress resistance and carbon storage pathways.
- *Go/no-go*: Requires >=30 species per compartment after NB01 census. Falls back to broad plant-vs-non-plant contrast if not met.

**H2 (Cohort Genetic Architecture)**: Beneficial functions (PGP genes) are predominantly core genome (>46.8% baseline), while pathogenicity determinants (T3SS effectors, toxins) are more often accessory/singleton (<46.8% baseline).

**H3 (Metabolic Complementarity)**: Co-occurring plant-associated genera in NMDC soil communities show higher metabolic complementarity (GapMind pathway gap-filling) than random genus pairs, after controlling for phylogenetic distance. Tested with refined cohort definitions and pathway *presence* (not just completeness).

**H4 (Mobility & Adaptation)**: Compartment-specific adaptation genes show higher singleton/accessory enrichment and more frequent co-occurrence with mobile elements. Validated with MGnify mobilome data where available.

**H5 (Novel Interactions)**: Data-driven enrichment at the eggNOG OG level identifies gene families beyond known PGP/pathogenicity markers that distinguish plant-associated from non-plant species, surviving phylum-level fixed effects. Novel OGs are functionally annotated via InterProScan, eggNOG descriptions, and MGnify BGC cross-reference.

**H6 (Host Specificity)**: Plant-associated species show host-plant preferences detectable from isolation metadata and validated against MGnify crop-specific rhizosphere catalogues. Within-species subclades carrying plant-adaptation genes are enriched in plant-derived isolates.

**H7 (Strain-Level Adaptation)**: Within key plant-associated species, accessory gene clusters carrying plant-interaction functions segregate by subclade, with plant-adapted subclades distinguishable from non-plant subclades by OG presence/absence patterns correlated with isolation source.

## Data Sources

### Phase 1 (NB01–NB08, completed)

| Source | Scale | Key Tables |
|--------|-------|------------|
| BERDL Pangenome | 293K genomes, 27.7K species | genome, gene_cluster, pangenome, gtdb_taxonomy |
| Bakta Annotations | 132M cluster reps | bakta_annotations, bakta_pfam_domains |
| eggNOG v6 | 93M annotations | eggnog_mapper_annotations |
| GapMind Pathways | 305M predictions | gapmind_pathways |
| GTDB Metadata | 293K genomes | gtdb_metadata (isolation_source) |
| NCBI Environment | 4.1M EAV rows | ncbi_env |
| BacDive | 97K strains | isolation, metabolite_utilization, sequence_info |
| NMDC | 6.4K samples | taxonomy_features, kraken_gold, study_table |

### Phase 2 (NB09–NB15, planned)

| Source | Scale | Key Tables |
|--------|-------|------------|
| InterProScan | 18 domain databases | interproscan_domains, interproscan_go, interproscan_pathways |
| MGnify Genomes | 518K genomes, 56K species | kescience_mgnify.species, genome, gene_mobilome, gene_bgc, genome_kegg_module, genome_cog |
| Pangenome (genome-level) | 1B gene-cluster junctions | gene, gene_genecluster_junction, genome_ani, phylogenetic_tree_distance_pairs |
| NMDC Extended | abiotic + metabolomics | nmdc_arkin.abiotic_features, metabolomics_gold |

**MGnify plant-relevant biomes:**
- Tomato rhizosphere: 666 genomes, 579 species
- Maize rhizosphere: 431 genomes, 336 species
- Barley rhizosphere: 103 genomes, 86 species
- Soil (reference): 20,908 genomes, 19,472 species
- 408 species overlap with pangenome at species level; 1,226 genera overlap

**MGnify limitations:**
- Rhizosphere/soil biomes have 1 genome per sample — no sample-level co-occurrence possible
- `gene_eggnog` not populated for soil or tomato-rhizosphere biomes
- BGC, mobilome, defense annotations only available for soil biome (not rhizosphere biomes)
- MGnify is a genome catalogue (functional trait profiles), not a community abundance dataset

## Marker Gene Sets

### Refined Panel (Phase 2, NB10)

Phase 1 used 91 markers including ubiquitous bacterial functions (flagella, chemotaxis, T6SS, biofilm, quorum sensing) that caused 100% dual-nature classification of non-plant genera like Escherichia and Salmonella. Phase 2 refines to plant-specific markers only:

#### Plant-Specific PGP (retain)
- **Nitrogen fixation**: nifH, nifD, nifK (+ KEGG module M00377 completeness check)
- **ACC deaminase**: acdS
- **Phosphate solubilization**: pqqA-E
- **IAA biosynthesis**: ipdC
- **Hydrogen cyanide**: hcnA-C
- **Siderophores**: entA-F, pvdA/S
- **Acetoin/butanediol (ISR)**: budA-C, alsD/S
- **DAPG biocontrol**: phlA-D
- **Phenazine biocontrol**: phzA-G

#### Plant-Specific Pathogenic (retain, with module completeness)
- **T3SS effectors/structural**: hrcC/J/N/V, hrpA/B/L (+ KEGG module M00332 completeness; require ≥50% module genes)
- **T4SS**: virB1-11, virD2/D4
- **Coronatine toxin**: cmaA/B, cfa6/7
- **Cell wall degrading enzymes**: pelA-E, pehA (pectinase); celA/B (cellulase)
- **Effectors/avirulence**: product keyword search

#### Reclassified to General Bacterial (remove from cohort scoring)
- Flagella (fliC, flgE, flhA) — ubiquitous motility
- Chemotaxis (cheA/W/R/Y) — ubiquitous motility
- Quorum sensing (luxI/R) — ubiquitous signaling
- Biofilm (bcsA, pelA) — ubiquitous surface attachment
- T6SS (tssB/C/E/F/G/H/K/M) — primarily inter-bacterial competition
- T2SS (gspD/E/F) — general secretion

#### Annotation Recovery (Phase 2, NB09–NB10)
- Query `interproscan_domains` with versioned Pfam IDs to recover T3SS/CWDE domain hits missed in NB02
- Query KEGG module completeness (not just individual KOs) for multi-gene systems
- Use eggNOG `Description` and `Preferred_name` fields for functional annotation of novel OGs

## Notebook Structure

### Phase 1: Completed (NB01–NB08)

| NB | Title | Status | Key Output |
|----|-------|--------|------------|
| 01 | Genome Census | Done | 1,136 plant-associated species across 4 compartments |
| 02 | Marker Gene Survey | Done | 588K marker clusters; 60.3% dual-nature (overly broad) |
| 03 | Enrichment Analysis | Done | 50 novel OGs (unannotated); 94.2% Fisher saturation |
| 04 | Compartment Profiling | Done | PERMANOVA R²=0.53; phylo control FAILED (code error) |
| 05 | Genomic Architecture | Done | H2 supported (p=3.4e-125); H4 partial (mixed proxy signal) |
| 06 | Complementarity | Done | H3 NOT supported (redundancy, not complementarity) |
| 07 | Cohort Synthesis | Done | 25.2% dual-nature (composite); 92.7% validation |
| 08 | Adversarial Revisions | Done | Sensitivity, negative controls, HGT deep dive |

**Phase 1 gaps identified during adversarial review:**
1. 50 novel OGs reported as bare COG IDs — never functionally annotated
2. Plant host species discarded from isolation_source — only compartment extracted
3. InterProScan domains never queried — missed Pfam/domain recovery
4. NB04 phylogenetic control failed (missing logit import)
5. GapMind returned 0% completeness — no fallback analysis
6. Co-occurrence limited to NMDC; MGnify not used
7. Genome-level compartment assignments dropped — lost strain resolution
8. KEGG module completeness never checked for multi-gene systems
9. Marker panel too broad — ubiquitous bacterial functions inflate dual-nature

### Phase 2: Planned (NB09–NB15)

**Compute environment**: All Phase 2 notebooks run on-cluster (BERDL JupyterHub) with `spark = get_spark_session()` (no import). NB12 requires per-species iteration for billion-row table joins — follow Pattern 2 from `docs/performance.md`.

#### NB09 — Novel OG Functional Annotation (Spark + local)
**Goal**: Determine what the 50 novel plant-enriched OGs actually are.
- Query `eggnog_mapper_annotations` for `Description`, `Preferred_name`, `COG_category`, `KEGG_ko`, `PFAMs`, `CAZy` for gene clusters carrying each novel OG
- Query `interproscan_domains` for domain architecture of representative gene clusters
- Query `interproscan_go` and `interproscan_pathways` for GO terms and pathway assignments
- Cross-reference with MGnify `genome_kegg_module`: do novel OGs correlate with specific KEGG modules in soil/rhizosphere species?
- Cross-reference with MGnify `gene_bgc`: do any novel OGs overlap with biosynthetic gene clusters in soil genomes?
- Literature search for any characterized members of top 10 OGs
- Generate mechanistic hypotheses per OG
- **Output**: `data/novel_og_annotations.csv`, `data/novel_og_domains.csv`

**Tables**: eggnog_mapper_annotations (93M), interproscan_domains, interproscan_go, interproscan_pathways, kescience_mgnify.genome_kegg_module, kescience_mgnify.gene_bgc

#### NB10 — Refined Markers, Host Species & Annotation Recovery (Spark + local)
**Goal**: Fix the marker panel, extract host plant species, recover missing annotations.
- Re-parse `gtdb_metadata.ncbi_isolation_source` to extract plant host species (regex for Oryza, Arabidopsis, Zea, Solanum, Triticum, Glycine, etc.)
- Extract actual `ncbi_env.host` values (not just boolean is_plant)
- Save genome-level compartment + host assignments (not just species majority-vote)
- Query `interproscan_domains` with versioned Pfam IDs to recover T3SS/T6SS/CWDE domain hits
- Query KEGG module completeness for multi-gene systems (M00332/T3SS, M00333/T4SS, M00377/nif)
- Reclassify all 25,660 species with refined marker panel (plant-specific only, module completeness gating)
- Validate negative controls: Escherichia, Salmonella should now be neutral or pathogenic, not dual-nature
- Validate positive controls: Rhizobium, Azospirillum should still classify as beneficial or dual-nature
- Re-run H3 precursor: with refined cohorts, how many PGP-only vs. pathogen-only genera exist in NMDC data?
- **Output**: `data/genome_host_species.csv`, `data/species_marker_matrix_v2.csv`, `data/species_cohort_refined.csv`, `data/interproscan_marker_hits.csv`

**Tables**: gtdb_metadata (293K), ncbi_env (4.1M), interproscan_domains, eggnog_mapper_annotations (KEGG modules), bakta_annotations

#### NB11 — MGnify Integration & Cross-Validation (Spark + local)
**Goal**: Integrate MGnify genome catalogues for host-specific trait profiles, mobilome, and BGC data.
- Bridge MGnify species to pangenome via GTDB taxonomy normalization (408 species, 1,226 genera)
- Compare plant-associated species: pangenome isolation_source classification vs. MGnify biome membership
- Host-specificity from MGnify: which species/genera appear in tomato but not maize rhizosphere (and vice versa)?
- KEGG module profiles: functional differences between tomato vs. maize vs. barley rhizosphere species
- 17 shared genera across all 3 rhizosphere biomes — characterize their core functional profile
- Pull `gene_mobilome` for overlapping soil species — real mobile element data for H4 validation
- Pull `gene_bgc` for soil species — biosynthetic gene cluster profiles (polyketide, NRP, terpene, siderophore)
- Cross-validate novel OGs (NB09): do they appear in MGnify functional annotations for rhizosphere species?
- **Output**: `data/mgnify_pangenome_bridge.csv`, `data/mgnify_host_specificity.csv`, `data/mgnify_mobilome.csv`, `data/mgnify_bgc_profiles.csv`

**Tables**: kescience_mgnify.species, genome, gene_mobilome, gene_bgc, genome_kegg_module, genome_cog, genome_cazy

#### NB12 — Within-Species Subclade OG Analysis (Spark + local)
**Goal**: Test whether plant-adaptation genes segregate by subclade within key species (H7).
- Select top 10-15 plant-associated species with ≥20 genomes (Pseudomonas_E, Rhizobium, Bradyrhizobium, Streptomyces, Mesorhizobium, Bacillus, Burkholderia, etc.)
- For each species: build genome × gene_cluster presence/absence matrix via `gene` → `gene_genecluster_junction`
- Define subclades via ANI clustering from `genome_ani` (or phylogenetic tree distances where available)
- Map isolation source and host plant (from NB10) onto subclades
- Fisher's exact test: are novel OGs (NB09) and plant-specific markers (NB10) enriched in plant-derived subclades?
- For species in both MGnify and pangenome: do MGnify rhizosphere genomes cluster into specific subclades?
- Genome size control: are subclade-level enrichments confounded by genome size differences?
- **Output**: `data/subclade_og_enrichment.csv`, `data/subclade_host_mapping.csv`, `data/species_subclade_definitions.csv`

**Tables**: gene (1B, per-species batches), gene_genecluster_junction (1B, per-species), genome_ani (421M, per-species), phylogenetic_tree_distance_pairs (22.6M), gtdb_metadata

#### NB13 — Expanded Co-occurrence & Interaction Network (Spark + local)
**Goal**: Re-test H3 with refined cohorts and expanded environmental context.
- Pull NMDC `abiotic_features` for 348 soil/rhizosphere samples (pH, temperature, dissolved oxygen, ammonium)
- Build co-occurrence network from NMDC taxonomy_features (save the co-occurrence matrix this time)
- Network topology: identify modules (Louvain clustering), hub genera (betweenness centrality), keystone species
- With refined cohorts (NB10), re-test PGP-pathogen C-score exclusion — expect more PGP-only genera now
- Re-test H3 complementarity with: (a) refined cohorts, (b) pathway *presence* not completeness, (c) genus-prevalent pathways (≥50% of species, not max-aggregated)
- Environmental gradient analysis: partial Mantel test — co-occurrence vs. environmental distance, conditioned on phylogeny
- Cross-reference: are hub/keystone genera in the MGnify rhizosphere catalogues (NB11)?
- Pull NMDC metabolomics_gold where available — do co-occurring genera correlate with specific metabolite profiles?
- **Output**: `data/cooccurrence_matrix.csv`, `data/network_topology.csv`, `data/abiotic_features.csv`, `data/complementarity_v2.csv`

**Tables**: nmdc_arkin.abiotic_features, metabolomics_gold, taxonomy_features, study_table

#### NB14 — Execute Deferred Controls (local + Spark)
**Goal**: Close out Phase 1 control gaps.
- Fix NB04 `logit` import, re-run genus-level logistic regression for H1 compartment enrichments
- Sensitivity: exclude top-3 genome-rich species per compartment, re-test H1
- Permutation: shuffle environment labels within genera, compare to observed enrichments
- Variance decomposition: phylogeny vs. ecology (nested PERMANOVA or redundancy analysis)
- GapMind fallback: test pathway *presence* (binary) across compartments instead of completeness scoring
- **Output**: `data/deferred_controls.csv`, `data/phylo_ecology_decomposition.csv`

**Tables**: gapmind_pathways (305M, filtered), species_compartment, species_marker_matrix

#### NB15 — Revised Synthesis (local)
**Goal**: Integrate Phase 2 findings into complete project narrative.
- Updated hypothesis verdicts (H0–H7) with annotated OGs, refined cohorts, MGnify validation, subclade evidence, stronger controls
- Revised genus dossiers: host plant associations, subclade structure, BGC profiles, mobilome evidence, network position
- Final microbe × plant host × compartment × gene × interaction summary table
- Compare Phase 1 vs. Phase 2 findings explicitly: what changed with refined markers?
- Update REPORT.md with Phase 2 findings
- **Output**: Updated `REPORT.md`, `data/cohort_assignments_v2.csv`, `data/genus_dossiers_v2.csv`

## Methodological Safeguards

### Phase 1 (original, partially executed)
1. **Phylogenetic control**: Phylum-level fixed effects in NB03 (genus-level intractable); family-level attempted in NB08 (insufficient variation)
2. **NCBI sampling bias**: Species-level prevalence used; sensitivity excluding top-3 genome-rich species deferred to NB14
3. **Multiple testing**: BH-FDR across all hypothesis-specific tests; pre-filter OGs to >= 5% prevalence
4. **Compartment classification quality**: Go/no-go checkpoint passed (3/4 compartments ≥30 species)
5. **Mobility proxy limitations**: Three proxy signals compared; mixed results acknowledged

### Phase 2 (new)
6. **Marker specificity control**: Negative control genera (Escherichia, Salmonella, Staphylococcus, Clostridioides, Mycoplasma, Pelagibacter, Bifidobacterium) must classify as neutral or pathogenic with refined panel; dual-nature indicates marker leakage
7. **KEGG module completeness gating**: Multi-gene systems (T3SS, T4SS, nitrogen fixation) require ≥50% module genes present to score as positive; prevents partial-system false positives
8. **Cross-collection validation**: Pangenome plant associations validated against MGnify rhizosphere catalogues; discrepancies investigated
9. **Subclade genome-size control**: Within-species OG enrichment tests include genome size as covariate
10. **GapMind aggregation correction**: Genus-level pathway scores use prevalence-weighted aggregation (≥50% of species must have pathway) instead of max aggregation
11. **Deferred Phase 1 controls executed**: Top-3 species sensitivity, within-genus label shuffling, phylogeny vs. ecology decomposition (NB14)

## Execution Deviations (Phase 1)

The following planned safeguards were modified or deferred during Phase 1 execution:

1. **Phylogenetic control level**: Genus-level fixed effects were computationally intractable with 27K species. Phylum-level control (28 phyla) was used in NB03; family-level was attempted in NB08 but showed insufficient within-family variation.
2. **NB04 phylogenetic control**: Genus-level logistic regression in NB04 failed due to a code error (undefined `logit` import). H1 compartment enrichments lack phylogenetic control beyond PERMANOVA. Fixed in NB14.
3. **Three safeguards deferred**: (a) sensitivity excluding top-3 genome-rich species, (b) within-genus label shuffling, (c) phylogeny vs. ecology variance decomposition. Executed in NB14.
4. **NB08 added**: An adversarial revisions notebook (not in original plan) was added to address concerns about marker specificity, genome size confounding, negative controls, and HGT deep dive.

## Key Constraints

1. The GeNomad mobile element table is NOT in BERDL. Phase 1 used transposase/integrase proxies. Phase 2 supplements with MGnify `gene_mobilome` data (soil biome only, 4,219 genomes).
2. MGnify rhizosphere/soil biomes have 1 genome per sample — no sample-level co-occurrence. MGnify is used as a functional trait catalogue and for host-specific species lists, not co-occurrence analysis.
3. MGnify `gene_eggnog` is not populated for soil or tomato-rhizosphere biomes. Functional comparison uses `genome_kegg_module` and `genome_cog` instead.
4. MGnify BGC and mobilome data exist only for soil biome, not the three rhizosphere biomes.

## Verification

### Phase 1 (completed)
1. ✅ NB01: compartment sample sizes ≥30 (3/4 pass; endophyte=29 triggers fallback)
2. ✅ NB02: known PGP organisms carry expected markers (Rhizobium 66/68, Pseudomonas 405/406)
3. ✅ NB03: enrichment volcano has expected positive controls
4. ✅ NB05: PGP core fractions in expected range (~65%)
5. ❌ NB06: complementarity scores did NOT exceed random null (H3 rejected)
6. ✅ NB07/NB08: validation against known organisms 92.7% agreement

### Phase 2 (planned)
7. NB09: top novel OGs have interpretable functional annotations (not all "hypothetical protein")
8. NB10: negative controls (Escherichia, Salmonella) classify as neutral/pathogenic with refined panel
9. NB10: ≥50 species have plant host species annotations
10. NB11: ≥100 species overlap between pangenome and MGnify rhizosphere catalogues
11. NB12: ≥5 species show significant subclade × plant-association OG enrichment
12. NB13: refined cohorts produce ≥5 PGP-only genera in NMDC for C-score analysis
13. NB14: deferred controls produce consistent results with Phase 1 findings (or explain discrepancies)

## Revision History

- **v1** (2026-04-22): Initial plan with H0–H5, NB01–NB07
- **v2** (2026-04-24): Added NB08 adversarial revisions, execution deviations
- **v3** (2026-04-24): Phase 2 plan. Added H6 (host specificity), H7 (strain-level adaptation), NB09–NB15. New data sources: MGnify (kescience_mgnify), InterProScan, NMDC extended (abiotic_features, metabolomics). Refined marker panel removing ubiquitous bacterial functions. Incorporated missed opportunities from Phase 1 adversarial review.
- **v4** (2026-04-25): Phase 2b complete. Notebooks NB13–NB15 added; paired adversarial review (`docs/adversarial_review_2026-04-24.md`) closed all five flagged issues plus extended H6 + H7 to the full available species set. Earlier verdict / status notes in this file are *historical* — see `REPORT.md` §11 and `data/hypothesis_verdicts_final.csv` for the current canonical verdicts. Specifically: PERMANOVA R²=0.527 (line ~109) was a panel + sampling artifact (panel-adjusted db-RDA R²≈0.06, location-only); 92.7% genus-level validation (line ~112, ~260) was tautological and is replaced by species-level validation (Mann-Whitney p=0.027 on N=7+7); NB04 phylo-control gap and DESIGN.md safeguards (lines ~165, ~191, ~201, ~202, ~241) are closed via NB14 L1 + within-genus shuffle + cluster-robust GLM and the NB14 GapMind prevalence-weighted re-test. Items 17, 18, 19, 20, 21 of the open-issues list are all closed; no methodological items remain open from any review round.

## Authors

- Adam P. Arkin (ORCID: 0000-0002-4999-2931) — U.C. Berkeley / Lawrence Berkeley National Laboratory
