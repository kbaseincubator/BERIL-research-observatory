# Research Plan: Self-Sufficiency, Anaerobic Toolkit, and Cultivation Bias in Clay-Confined Cultured Bacterial Genomes

## Research Question

Do BERDL's cultured bacterial genomes from clay-confined deep-subsurface environments — predominantly cultivated from porewater, borehole, and clay-mineral isolates — recapitulate the genomic signatures the recent literature has identified for the deep terrestrial subsurface (biosynthetic self-sufficiency; H₂-driven anaerobic chemolithoautotrophy via Wood–Ljungdahl + group 1 [NiFe]-hydrogenase + dissimilatory sulfate reduction; porewater-vs-rock-attached community dichotomy)? And, given that BERDL's clay cohort reflects cultivation-accessible organisms, can we directly test the porewater-bias hypothesis suggested by comparing Bagnoud (2016) and Mitzscherling (2023)?

## Literature Context

The deep terrestrial subsurface is anaerobic, predominantly chemolithoautotrophic, and H₂-driven; the reductive acetyl-CoA (Wood–Ljungdahl) pathway dominates carbon fixation, hydrogenase content increases quantitatively with depth, and the canonical genomic signature is **biosynthetic self-sufficiency** — full amino-acid biosynthesis, N-fixation, and C-fixation in a single genome — rather than streamlining (Beaver & Neufeld 2024; Becraft 2021 on *Ca.* Desulforudis audaxviator). At the Mont Terri Opalinus Clay site, in-situ H₂ injection drove a minimalistic food web in porewater dominated by autotrophic Desulfobulbaceae and Rhodospirillaceae expressing the complete Wood–Ljungdahl pathway, group 1 [NiFe]-hydrogenase, and Sat–AprAB–DsrAB; three MAGs recurred across seven boreholes, providing direct evidence of an indigenous Opalinus core community (Bagnoud 2016, 2015). Crucially, Mitzscherling et al. (2023) showed that **rock-attached and porewater communities differ qualitatively at the same site**: Opalinus rock surfaces are dominated by iron-reducing *Geobacter* and *Geothrix* (4.3–10.2%) tracking pyrite content (r=0.84), with sulfate reducers <0.2%; SRB lineages live in the porewater fraction. Compacted bentonite interiors are largely dormant *Bacillus* spores (Engel 2019; Beaver 2024), with active SRB life only at the bentonite–groundwater interface. Cultured-isolate genomic studies of deep-subsurface Firmicutes (e.g., *Pelosinus* HCF1: Beller 2012; *Desulfosporosinus* spp.: Vandieken 2017, Hilpmann 2023) confirm versatile [NiFe]/[FeFe]-hydrogenase complements coupled to dissimilatory nitrate, Cr(VI), and Fe(III) reduction — consistent with the predicted deep-subsurface metabolic toolkit. Counter-evidence to streamlining comes from Props (2019), Cortez (2022), and Podowski (2022), each documenting that streamlining occurs in some oligotrophic niches but not others. Together, this body of work generates testable predictions for how BERDL's ~56 cultured clay-isolated genomes — biased toward cultivable porewater organisms — should differ from surface-soil congeners. See [references.md](references.md) for the full annotated bibliography.

## Hypotheses

### H1 — Biosynthetic self-sufficiency
- **H0**: Clay-isolated bacterial genomes show no greater biosynthetic completeness than phylogenetically matched soil baseline. Mean GapMind amino-acid pathway completeness, nitrogen-fixation gene presence, and CO₂-fixation pathway completeness are equal across cohorts.
- **H1**: Clay-isolated genomes show significantly greater biosynthetic completeness (higher mean GapMind amino-acid pathway-complete count, higher rate of *nifHDK* presence, higher rate of complete Wood–Ljungdahl) than phylogenetically matched soil baseline — consistent with the Beaver & Neufeld (2024) self-sufficiency synthesis.
- **Test**: Wilcoxon rank-sum on per-genome counts; logistic regression with phylum as covariate; effect-size reported as Cohen's *d* on standardized metrics.

### H2 — Joint anaerobic toolkit at depth
- **H0**: Within the clay cohort, deep-confined isolates (Opalinus, bentonite, other deep-rock) show no greater enrichment of the literature-defined anaerobic toolkit (Wood–Ljungdahl + group 1 [NiFe]-hydrogenase + dissimilatory sulfate reduction Sat-AprAB-DsrAB) than shallow agricultural-clay isolates (Coalvale, Cerrado).
- **H1**: Deep-confined isolates jointly carry all three modules at higher rates than shallow-clay and surface-soil baseline — directly testing the Bagnoud (2016) Opalinus + Beaver & Neufeld (2024) review prediction that hydrogenase content scales with depth and Wood–Ljungdahl is the dominant subsurface C-fixation route.
- **Test**: Per-genome binary toolkit score (0–3 modules complete); Cochran–Armitage trend test across depth classes (surface soil → shallow clay → deep clay); marker-by-marker Fisher's exact with BH-FDR.

### H3 — Porewater-bias signature
- **H0**: BERDL's clay-isolated cohort reflects an unbiased mixture of rock-attached and porewater organisms; SRB-marker (*dsrAB-aprAB*) prevalence and IRB-marker (*omcS, mtrC, mtrA, pilA*) prevalence are at parity, matching the natural community frequencies reported by Mitzscherling (2023).
- **H1**: BERDL's clay-isolated cohort is biased toward the porewater signature documented by Bagnoud (2016) — SRB markers are present at significantly higher rates than IRB markers, and the distribution diverges from Mitzscherling's rock-attached IRB-dominance pattern. This is a positive prediction from cultivation bias: porewater organisms are more cultivable than rock-attached *Geobacter* and *Geothrix*.
- **Test**: Two-by-two Fisher's exact (cohort × marker class) against Mitzscherling-derived expected frequencies; bootstrap CI on SRB-vs-IRB ratio; this is the most directly diagnostic hypothesis for our cohort, and has clear "yes/no" interpretation.

## Cohort Definition

### Anchor — clay-confined deep-subsurface cultured isolates (target n ≈ 25–40)

Sources, in priority order, all reachable from `kbase_ke_pangenome.ncbi_env` joined to `kbase_ke_pangenome.genome` via `accession ↔ ncbi_biosample_id`:

| Sub-cohort | Source filter | Expected n | Lit anchor |
|---|---|---|---|
| Mont Terri Opalinus | `isolation_source` LIKE 'Opalinus%' | 8 | Bagnoud 2015, 2016; Mitzscherling 2023; Moll 2017; Lutke 2013 |
| Bentonite formations | `isolation_source` LIKE '%bentonite%' OR LIKE '%Clay (bentonite)%' | ~3–5 | Engel 2019, 2023; Pedersen 2000, 2009; Stroes-Gascoyne 1997 |
| Other deep clay (Callovo-Oxfordian, kaolin) | `isolation_source` LIKE '%Callovo%' OR LIKE '%kaolin%' | ~2–4 | Shelobolina 2007 (kaolin lenses) |
| BacDive deep-clay strains | `kescience_bacdive.isolation` clay sample_type with non-agricultural cat3 (#Geologic, #Subsurface) → genus → GTDB linkage | ~10–20 | Vandieken 2017; Beaver 2021 |

### Shallow-clay contrast (target n ≈ 12–20)

Surface agricultural and pedogenic clay isolates: Coalvale silty clay (n=8), Cerrado clay soil (n=1), and BacDive clay-soil entries with `cat3 = #Soil` and rhizosphere/agricultural context.

### Soil/sediment baseline (n ≈ 1,000–2,000 species, phylum-stratified)

Random per-phylum stratified sample from the 5,151 species linked to soil/sediment biosamples in `ncbi_env`. Used as the reference distribution for H1 enrichment tests; per-phylum balance is essential because the literature warns of strong phylogenetic confounding (Mitzscherling 2023; *Pelosinus*/*Desulfosporosinus* concentration in subsurface lineages).

### Compartment annotation

Each anchor cohort genome is tagged with a `compartment` field (`porewater_borehole`, `rock_attached`, `bentonite_buffer`, `clay_sediment`, `unknown`) inferred from the biosample isolation_source string — this is the metadata feature H3 leverages directly.

## Query Strategy

### Tables Required

| Table | Purpose | Rows | Filter |
|---|---|---|---|
| `kbase_ke_pangenome.ncbi_env` | Cohort assembly via isolation_source/env_* | 4.1M | `attribute_name IN (...)` + LIKE on content |
| `kbase_ke_pangenome.genome` | biosample_id ↔ genome_id ↔ species clade | 293K | join from cohort accession list |
| `kbase_ke_pangenome.gtdb_metadata` | Genome size, GC%, CheckM completeness | 293K | join on genome_id |
| `kbase_ke_pangenome.gtdb_taxonomy_r214v1` | Phylum for stratification | 293K | join on genome_id |
| `kbase_ke_pangenome.gene_cluster` | Cluster IDs + core/aux flags per species | 132M | filter by `gtdb_species_clade_id IN (cohort)` |
| `kbase_ke_pangenome.gene_genecluster_junction` | Genome → cluster membership | 1B | filter by `genome_id IN (cohort)` |
| `kbase_ke_pangenome.eggnog_mapper_annotations` | KEGG/COG/PFAM by cluster representative — H1/H2 marker presence | 94M | filter by `query_name IN (cohort_clusters)` |
| `kbase_ke_pangenome.gapmind_pathways` | Amino-acid pathway completeness — primary H1 metric | 305M | filter by `genome_id IN (cohort)` |
| `kescience_bacdive.isolation` + `taxonomy` | BacDive clay-strain expansion of cohort | 58K + 97K | LIKE filter on sample_type + cat3, then GCA→GTDB |

### Marker definitions (literature-grounded)

| Marker module | Genes/PFAMs/KEGG | Lit source |
|---|---|---|
| **Wood–Ljungdahl C-fix** | KEGG K00198 (acsA / cooS-CO dehydrogenase), K00194 (acsB), K00197 (acsC), K15022 (acsD), K15023 (acsE) — require ≥4/5 for "complete" | Beaver & Neufeld 2024 review; Bagnoud 2016 Desulfobulbaceae c16a |
| **Group 1 [NiFe]-hydrogenase** | PFAM PF00374 (Hyd_Beta) + PF14720 (Hyd_Small), KEGG K06281 (hyaA) / K06282 (hyaB) | Bagnoud 2016; Beaver & Neufeld 2024 (depth-enriched) |
| **Dissimilatory sulfate reduction** | KEGG K11180 (dsrA), K11181 (dsrB), K00394 (aprA), K00395 (aprB), K00958 (sat) — require ≥4/5 for "complete" | Bagnoud 2016 Desulfobulbaceae c16a |
| **Iron reduction (rock-attached)** | KEGG K07811 (omcS — Geobacter), K17324 (mtrC — Shewanella), K17323 (mtrA), PFAM PF14534 (Cytochrom_NNT, multi-heme c-type) | Mitzscherling 2023; Butler 2010 Geobacter |
| **N-fixation (self-sufficiency)** | KEGG K02588 (nifH), K02586 (nifD), K02591 (nifK) | Becraft 2021 D. audaxviator |
| **Amino-acid biosynthesis completeness** | GapMind pathway-level `score_simplified = 1` (complete) per pathway, summed per genome | Beaver & Neufeld 2024 self-sufficiency synthesis |

### Anti-pitfall checklist (from `docs/pitfalls.md` & `docs/performance.md`)
- `--` in species IDs: use exact equality, not LIKE patterns
- Never full-scan `gene` (1B) or `gene_genecluster_junction` (1B) — always filter by `genome_id` or `gene_cluster_id`
- `gapmind_pathways` (305M rows) — two-stage aggregation per `pangenome_pathway_geography` pattern: first per genome-pathway MAX score, then per genome SUM completeness
- Cast string columns to numeric (CheckM completeness, GC%)
- Disable `autoBroadcastJoinThreshold` if joins involving `kbase_uniprot.uniprot_identifier` exceed `maxResultSize`
- Avoid `.toPandas()` on intermediate Spark results
- `score_simplified = 1` corresponds to score_category = 'complete' in GapMind — confirmed pattern from `pangenome_pathway_geography` project

### Performance Plan

- **Tier**: Direct Spark on JupyterHub (current environment).
- **Estimated complexity**: Moderate. Cohort genome list is ≤200, so per-genome filters perform well on `gene_genecluster_junction` and `gapmind_pathways`. The per-species query for soil baseline (1000+ species) uses the `pangenome_pathway_geography` two-stage aggregation pattern.
- **Largest job**: H3 ortholog set (NB07) — DIAMOND BBH on cluster-rep proteomes for ~50 cohort + 200 baseline genomes → ~3–6 hours; can batch by phylum or use `kbase_uniref90` cluster IDs as a faster surrogate for orthology.
- **Cache strategy**: NB01 outputs `cohort_assignments.tsv`; NB02 outputs `genome_features.parquet` keyed on genome_id; later notebooks read these locally without re-querying Spark.

## Analysis Plan

### NB01 — Cohort assembly (Spark)
- **Goal**: Identify clay-confined / shallow-clay / soil-baseline cohorts; tag each genome with `compartment` and `depth_class`; link to pangenome `genome_id`.
- **Inputs**: `ncbi_env`, `bacdive.isolation` + `taxonomy`, `genome`, `gtdb_metadata`, `gtdb_taxonomy_r214v1`.
- **Outputs**: `data/cohort_assignments.tsv` with columns `genome_id, species_clade_id, phylum, class, order, family, genus, species, cohort_class (anchor_deep / anchor_shallow / soil_baseline), sub_cohort (opalinus / bentonite / cerrado / coalvale / soil_random), compartment (porewater / rock / buffer / sediment / unknown), depth_class (surface / shallow / deep / deep_rock), source_keyword, raw_isolation_source, ncbi_biosample_id`.
- **Notebook section count**: ~8 (env query → bacdive linkage → soil-baseline sampling → write).

### NB02 — Genome feature extraction (Spark)
- **Goal**: For each cohort genome, extract per-genome marker presence (Wood–Ljungdahl, [NiFe]-hydrogenase, dsrAB-aprAB-sat, *nifHDK*, multi-heme cytochromes), GapMind amino-acid pathway completeness, and QC metrics (size, GC%, completeness, contamination).
- **Inputs**: `eggnog_mapper_annotations` (filtered by cohort cluster IDs from `gene_cluster`), `gapmind_pathways`, `gtdb_metadata`.
- **Outputs**: `data/genome_features.parquet` keyed on `genome_id`.

### NB03 — Soil baseline construction (Spark + local)
- **Goal**: Build phylum-stratified random soil-baseline (target 4× anchor cohort size per phylum) so H1/H2 tests have a comparable reference distribution.
- **Inputs**: cohort_assignments.tsv (anchor phyla); `ncbi_env` + `genome` (soil/sediment biosamples).
- **Outputs**: `data/baseline_features.parquet`.

### NB04 — H1 test: self-sufficiency (local)
- **Goal**: Test whether anchor cohort shows greater biosynthetic completeness than baseline.
- **Method**: Per-genome metrics: GapMind amino-acid pathway-complete count, full-Wood–Ljungdahl indicator, *nifHDK* presence, genome size. Wilcoxon rank-sum and logistic regression with phylum covariate. Effect-size = Cohen's *d* on standardized metrics.
- **Outputs**: `data/h1_self_sufficiency.tsv`, `figures/h1_violin_pathway_completeness.png`, `figures/h1_genome_size_vs_completeness.png`.

### NB05 — H2 test: joint anaerobic toolkit (local)
- **Goal**: Quantify per-genome toolkit score (0–3 modules complete: WL, hyd, dsr) across cohort tiers.
- **Method**: Cochran–Armitage trend test (depth class as ordered factor); per-marker Fisher's exact with BH-FDR; visualize as stacked-bar of toolkit score by depth class.
- **Outputs**: `data/h2_toolkit_score.tsv`, `figures/h2_toolkit_by_depth.png`, `figures/h2_marker_forest.png`.

### NB06 — H3 test: porewater-bias signature (local)
- **Goal**: Test whether anchor cohort shows the Bagnoud porewater signature (SRB-enriched) or the Mitzscherling rock-attached signature (IRB-enriched).
- **Method**: Compute per-genome SRB-marker (dsrAB+aprAB) and IRB-marker (omcS or mtrC or 4+ multi-heme cytochrome) booleans. Compute SRB:IRB ratio in cohort. Compare to expected frequencies derived from Mitzscherling 2023 (rock surface: SRB <0.2%, IRB 4–10%) via Fisher's exact and bootstrap CI. Stratify by `compartment` field.
- **Outputs**: `data/h3_srb_irb.tsv`, `figures/h3_srb_vs_irb_scatter.png`, `figures/h3_compartment_breakdown.png`.

### NB07 — Recurrent ortholog discovery (local + Spark for BBH)
- **Goal**: Following Bagnoud (2016)'s observation that 3 MAGs recurred across 7 Mont Terri boreholes, identify orthogroups present in ≥70% of anchor cohort and <20% of phylum-matched baseline.
- **Method**: Use `kbase_uniref90` cluster IDs as a fast orthology surrogate (avoids DIAMOND all-vs-all). For each cohort genome, list its UniRef90 clusters via `bakta_db_xrefs` or eggNOG annotations. Compute per-cluster presence rate. Filter; annotate hits with eggNOG / KEGG.
- **Outputs**: `data/h_ortho_clay_core.tsv`, `figures/h_ortho_presence_heatmap.png`.

### NB08 — Synthesis (local)
- **Goal**: Integrate H1/H2/H3 + ortholog results, contextualize with `references.md`, produce a summary figure for REPORT.md.
- **Outputs**: `figures/summary_figure.png`, draft REPORT.md text.

## Expected Outcomes

### If H1 supported
The clay cohort encodes more complete biosynthetic pathways and *nifHDK* than soil baseline, replicating the *Ca.* Desulforudis audaxviator pattern at population scale and supporting the Beaver & Neufeld (2024) self-sufficiency synthesis. **If H1 not supported**, BERDL's cultured cohort either (a) is dominated by cultivable facultative organisms that don't carry the deep-subsurface signature (cultivation bias), (b) lacks the deep, isolated, oligotrophic taxa where self-sufficiency is most pronounced, or (c) the signature exists at the obligate-anaerobe lineage level but is diluted by phylogenetic mixing.

### If H2 supported
The triple-marker anaerobic toolkit is preferentially carried by deep-confined isolates, in line with Bagnoud (2016)'s minimalistic Opalinus food web and Beaver & Neufeld (2024)'s depth-enriched hydrogenase pattern. **If not supported**, the toolkit may be present across all anaerobic isolates regardless of depth (i.e., it tracks oxygen exclusion broadly, not depth specifically) — still a useful negative result.

### If H3 supported
BERDL's clay cohort is porewater-biased, consistent with cultivation accessibility. This validates the cultivation-bias caveat for any genome-resolved subsurface microbiome study and points to the importance of MAG-based augmentation for rock-attached community representation. **If not supported**, BERDL contains a more balanced rock-attached representation than expected — an interesting positive result enabling rock-attached gene-content analysis.

### Potential confounders
- **Phylogenetic confounding**: Mont Terri and bentonite cohorts are *Desulfosporosinus*-, *Pelosinus*-, *Sporomusa*-heavy; H1/H2 signals must be controlled for phylum and ideally genus.
- **Cultivation bias** (the H3 hypothesis itself): BERDL's cultured cohort underrepresents *Geobacter*/*Geothrix* rock-attached lineages and CPR/DPANN episymbionts; conclusions only generalize to cultivable cohorts.
- **Sample size**: n ≈ 25–40 anchor cohort is small; Fisher tests have power for moderate-large effects only. We will report effect sizes alongside p-values and treat marginal H1/H2 findings as descriptive, with H3 as the most robustly testable hypothesis.
- **Annotation gaps**: GapMind covers amino acid + small carbon pathways but not core dissimilatory respiration — H2 markers are drawn from KEGG/PFAM, not GapMind. eggNOG cluster-rep annotations propagate within 90% AAI clusters and may miss strain-level marker variants.
- **Compartment annotation uncertainty**: `isolation_source` text is sometimes ambiguous (e.g., "Opalinus Clay rock" could be rock-attached or porewater drilled into rock). H3 is run with both strict and loose compartment definitions for sensitivity.

## Revision History

- **v1** (2026-04-30): Initial plan, derived from a 32-paper literature review (see `references.md`).

## Authors

David Lyon (ORCID: [0000-0002-1927-3565](https://orcid.org/0000-0002-1927-3565)) — KBase
