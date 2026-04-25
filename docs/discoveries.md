# Discoveries Log

Running log of insights discovered during science projects. Tag each with `[project_name]`.

Periodically refactor stable insights into the appropriate structured doc (schema.md, pitfalls.md, performance.md).

---

## 2026-04

### [ibd_phage_targeting] Regex-on-pathway-names vs curator-validated class hierarchy: same data, opposite conclusion

A NB07a H3a (b) test of "do CD-up pathways concentrate in IBD-mechanism themes" gave opposite verdicts depending on category-schema choice — same DA outputs, same statistical test, same nulls.

- **v1.7 (regex on pathway descriptive names)**: 7 a-priori IBD categories matched 44 of 409 prevalence-filtered pathways. CD-up = 52 pathways, of which only 3 in the 7-category set. "≤ 3 of 7 categories" test was structurally degenerate (null also at 100 % top-3). **Verdict: FAIL** — H3a (b) "not supported, structurally degenerate."
- **v1.8 (MetaCyc class hierarchy from ModelSEEDDatabase MetaCyc_Pathways.tbl + 12-theme IBD overlay)**: 357/409 (87 %) of pathways had MetaCyc class data; 262/409 (64 %) assigned to ≥ 1 IBD theme. Per-theme Fisher's exact (CD-up × in-theme) with BH-FDR across 12 themes. **Verdict: SUPPORTED — iron/heme acquisition is the dominant CD-up theme (OR = 8.1, FDR 7e-6; 15 of 52 CD-up pathways)**. Drove a four-way convergence with NB05 *E. coli* Yersiniabactin/Enterobactin MIBiG matches, NB07a heme-biosynthesis attribution to *E. coli*, and AIEC-iron-acquisition literature.

The reason v1.7 missed iron biology: regex on "PWY-5920: superpathway of heme biosynthesis from glycine" doesn't match "iron." MetaCyc's curator-validated class hierarchy correctly puts PWY-5920 under `HEME-SYN`, `Heme-b-Biosynthesis`, `Cofactor-Biosynthesis`, `Tetrapyrrole-Biosynthesis`. v1.7's "0_other" bucket was hiding 15+ heme/iron pathways.

**Generalizable rule** (now plan norm N17 in `ibd_phage_targeting`): for any pathway / gene / metabolite category-enrichment test, prefer curator-validated ontology / class hierarchy over name-pattern regex when one is available. Regex on descriptive names becomes a sensitivity check, not the primary categorization. ModelSEEDDatabase ships a usable MetaCyc class hierarchy at `/global_share/KBaseUtilities/ModelSEEDDatabase/Biochemistry/Aliases/Provenance/MetaCyc_Pathways.tbl` (90 %+ coverage of HUMAnN3 outputs). KEGG BRITE and GO biological-process subontology cover analogous categorization needs for KEGG / EC-level data.

**Operational lesson**: the v1.7 "FAIL — degenerate" verdict should have been read as a flag to revisit the schema, not a true refutation. NB07a/b correctly noted the structural underpoweredness — but the v1.7 verdict was technically correct given the v1.7 schema, even though the v1.8 schema reverses it. **A "structurally degenerate" verdict is an invitation to fix the schema, not to conclude on the science.**

### [meta] Adversarial review applies at plan-revision scope, not just notebook scope

The NB04 → NB04b-h rigor-repair arc established that pairing standard `/berdl-review` with an adversarial reviewer (general-purpose Agent with explicit "find flaws" framing) is a project-hygiene rule for **notebook commits**. The `ibd_phage_targeting` v1.6 → v1.7 plan revision establishes the same pattern at the **plan-revision scope**:

- v1.6 was a careful Pillar 3 plan refresh after Pillar 2 closure, written by an experienced agent, sounded principled.
- Adversarial review of v1.6 (general-purpose Agent reading the plan + REPORT + FAILURE_ANALYSIS + actual mart parquet inspection) found **4 critical + 10 important issues** structurally analogous to NB04's failure pattern: feature leakage in N14 dual-basis (same-axis ecotype basis is leakage-poisoned), "4-substudy meta-viable" inherited from NB04e without re-verification for pathway data (actually 3+1), H3a thresholds without null distributions, H3a-new mislabeled "butyrate-producer ↔ pathobiont" with 4 of 6 named anchors not actually butyrate producers, H3b strain-adaptation collapses to species-level on cMD by construction, H3e n=67 across 3 sites (not 130-subject HMP2). Every category of issue NB04 had at notebook scope, v1.6 had at plan scope.

**Generalizable rule**: any plan revision whose downstream notebooks will be load-bearing for clinical / experimental / external claims should be reviewed by both a standard reviewer (mostly catches surface flaws) AND a paired adversarial reviewer (catches structural / inferential issues — feature leakage, missing nulls, hard-coded verdict logic, sample-size overclaims, label-vs-data mismatches). The cost of catching these issues at plan scope is much lower than catching them at notebook scope (NB04 → NB04b-h was 7 notebooks; v1.6 → v1.7 was a single plan-edit pass).

**Operational pattern**: `bash tools/review.sh <project> --type plan` for the standard plan reviewer; `Agent(subagent_type=general-purpose, prompt=<find-flaws brief>)` for the adversarial; reconcile both before notebook execution. A `--type plan --adversarial` flag for `/berdl-review` would consolidate this into a single command.

**Both NB04 and v1.6 had these recurring features that adversarial review caught and standard didn't**:
- Effect-size thresholds without null distributions (NB04: Jaccard 0.14; v1.6: |ρ| > 0.4)
- Substudy / cohort sample-size claims that don't match the data on inspection
- Hypothesis labels that don't match the operationalized test (NB04: "H2c RESOLVED" treats n.s. as positive; v1.6: "butyrate-producer" anchors with mostly non-butyrate-producers)
- Same-axis feature leakage in stratified analyses (NB04: cluster on taxa + test taxa; v1.6: stratify pathway DA by pathway-feature ecotype)
- Falsifiability rules that pass under random data ("≤ 5 categories of 7" is loose enough to pass on random allocation)

The pattern is mostly about pre-registration discipline: what's the actual sample size given the actual data, what's the null distribution against which any positive claim is being made, what does each operational threshold mean given that null. Standard review treats these as advanced questions; adversarial review treats them as the entry-level diligence.

### [ibd_phage_targeting] NB04 rigor failure: 33 within-ecotype Tier-A candidates collapsed to 3 rock-solid candidates under independent-evidence gating

**Quantified cost of feature leakage + confound non-adjustment in Pillar 2.** NB04 reported a 33-species within-ecotype Tier-A list (18 E1, 15 E3) with the H2c *C. scindens* paradox marked "RESOLVED by stratification." Two rigor-repair notebooks (NB04b + NB04c) applied three evidence filters to every candidate:

1. Bootstrap CI lower-bound > 0.3 on within-ecotype CLR-Δ (repair for "n.s. → RESOLVED" decision-logic bug)
2. LinDA (Zhou et al. 2022, pure-Python) CD↑ with FDR < 0.10 in the same ecotype (repair for single-method DA)
3. Within-substudy CD-vs-nonIBD meta-analysis across 4 IBD sub-studies CD↑ AND ≥ 66 % sign concordance (confound-free independent check; see `docs/pitfalls.md` cMD substudy-nesting entry)

Only evidence-stream (3) is independent of the ecotype definition that generated NB04. Results:

- **E1**: 0 of 18 candidates passed all three filters. All 14 E1 candidates that passed (1) + (2) had *negative* effects under the confound-free contrast — they are ecotype-markers, not CD drivers. The within-ecotype DA "lifted" them to CD↑ via feature leakage + compositional bias compound.
- **E3**: **3 of 15 candidates passed all three filters**: *Mediterraneibacter gnavus* (within-substudy CD↑ +5.13, LinDA E3 +1.64), *Flavonifractor plautii* (within-substudy +1.89, LinDA +2.91), *Blautia wexlerae* (within-substudy +0.91, LinDA +2.00). These are the trustworthy Tier-A.
- **H2c (paradox resolution)**: directly contradicted. *C. scindens* is genuinely CD↑ under within-substudy confound-free analysis (pooled CLR-Δ +1.18, FDR 1e-8, 4/4 sign concordance). The NB04 within-ecotype n.s. call was a leakage self-selection artifact (LOO refit in NB04b showed *C. scindens* CD↑ in both E1 and E3 once ecotype definition excluded the test species).
- **H2b (ecotype divergence)**: survives strongly. Permutation-null p = 0.000 (observed Jaccard 0.104 vs null mean 0.785 ± 0.054). Stratification divergence is a real effect; NB04's effect-size framing was the wrong statistic.

**Implication for Pillar 2 scope**: per-ecotype Tier-A reduces from "33 candidates across both E1 and E3" to "3 candidates, E3 only." E1 needs a reformulated analytical approach before NB05 — the current within-ecotype DA is not a usable target list. Candidate approaches: (a) rebuild ecotypes on a functional (pathway / KEGG) feature matrix to break the taxonomic-feature leakage; (b) run within-IBD-substudy CD-vs-nonIBD stratified by ecotype as the primary analysis (requires substudy × ecotype × diagnosis cells with ≥ 10 samples each, needs checking); (c) broaden to UC-vs-HC + CD-vs-HC combined as IBD-vs-control for power.

**Applies to**: the next three Pillar 2 deliverables in `ibd_phage_targeting` (Tier-A scoring, cocktail draft prep for UC Davis patients). The ecotype framework itself is still usable for patient stratification (NB02 H1b stands); only the within-ecotype DA has been invalidated for target-selection use.

See `projects/ibd_phage_targeting/FAILURE_ANALYSIS.md` for the full arc and methodology lessons.

### [meta] Standard `/berdl-review` is over-optimistic on methodologically nuanced projects — pair with adversarial review for high-stakes claims

`tools/review.sh` (the reviewer behind `/berdl-review` and `/submit`) operates with a "find-strengths-and-suggestions" framing inherited from the system prompt at `.claude/reviewer/SYSTEM_PROMPT.md`. On the `ibd_phage_targeting` project, two reviewers ran on the same state of the project:

- **Standard `/berdl-review`** (claude-sonnet-4): concluded "exceptional methodological sophistication," "no critical issues," and recommended proceeding to Pillars 3–5 with the existing Tier-A candidate list.
- **Adversarial review** (general-purpose agent with explicit "find flaws, don't be diplomatic" framing on the same files): identified **5 critical issues + 6 important issues**, including (a) feature leakage in within-cluster DA — the analysis clustered samples on taxon abundances then tested the same taxa within cluster; (b) hard-coded "RESOLVED" verdict logic that treated `n.s.` results as positive evidence; (c) zero confounder adjustment despite citing Vujkovic-Cvijin 2020 which calls for it; (d) Jaccard 0.14 reported as supporting H2b without any null distribution; (e) ecotype framework with 48.9 % cross-method agreement and no external replication.

The standard reviewer is excellent at catching surface flaws (missing sections, undocumented dependencies, broken figures, simple statistical errors) and is appropriate for routine submissions. It is **systematically weak** at structural / inferential issues — selection-on-outcome confounding, missing null distributions, post-hoc choice of decision rules, narrative-vs-evidence mismatch. These require an explicit adversarial framing that the default reviewer prompt does not invoke.

**Recommendation**: for any project whose conclusions inform downstream decisions (clinical, experimental, computational), pair `/berdl-review` with a separately-spawned adversarial reviewer and reconcile the two outputs before final synthesis. A proposed enhancement to `/submit`: an optional `--adversarial` flag that runs both reviewers and produces a combined report. Until that lands, the manual pattern is `bash tools/review.sh <proj>` followed by `Agent(subagent_type=general-purpose, prompt=<adversarial brief>)`.

**Applies to**: any BERDL project whose REPORT.md will be cited by downstream work, used to design experiments, or shared externally. The standard review remains the right default for in-progress / iteration-mode work.

### [ibd_phage_targeting] OvR-AUC can overstate per-patient classifier usefulness when a cohort-axis variable dominates the feature set

Training-cohort OvR-AUC is a weak proxy for "does this classifier help at the patient level" whenever the cohort includes a strong cohort-axis variable that is constant (or nearly so) on the held-out patients. Concrete observation from `ibd_phage_targeting` NB03:

- Classifier trained on pooled HC + IBD samples to predict K=4 ecotype from {`is_ibd`, `sex`, `age`} achieves macro OvR AUC 0.80 in 5-fold CV — exceeds the 0.70 "passes" threshold.
- Applied to UC Davis patients (100 % IBD, `is_ibd = 1` constant): only 41 % agreement with the metagenomic projection from NB02. The classifier predicts E1 for 19/22 patients because the dominant learned rule is "IBD → E1 most of the time" (the marginal mode among IBD training samples).
- The AUC counted HC-vs-IBD separability toward its score; the UC Davis test requires the harder IBD-internal separability (E1 transitional vs E3 severe). These are not the same problem.

**Generalizable fix**: before quoting a classifier AUC as a measure of clinical utility, apply the classifier to an independent cohort with the cohort-axis variable held fixed. The agreement rate on that cohort is the translation-honest metric. Applies to any project building clinical classifiers on pooled disease+control data.

### [ibd_phage_targeting] Kaiju vs MetaPhlAn3 classifier-mismatch asymmetrically breaks CLR+GMM projection but not LDA projection

When projecting a held-out cohort processed with a different taxonomic classifier (Kaiju NCBI-NR read classification) onto a reference embedding trained on a different classifier (MetaPhlAn3 marker-gene relative abundance), the two ecotype methods (LDA on pseudo-counts, GMM on CLR + PCA) behave very differently:

- **LDA on pseudo-counts** is robust. Absence = not-detected; no Kaiju-vs-MetaPhlAn3 abundance-scale or feature-completeness mismatch forces a particular projection coordinate. UC Davis Kuehl samples project to E0, E1, E3 in plausible biological proportions (27 / 42 / 31 %).
- **GMM on CLR + PCA** is fragile. Kuehl detects only 54 % of training species; 70 % of training species have no Kuehl detection. The CLR transform imputes these zeros with a small pseudocount, and when these sparse vectors go through PCA, they land consistently in the region of feature space occupied by one dominant Gaussian cluster — *regardless of actual biology*. All 26 Kuehl samples project to E3 at GMM confidence > 0.97, an artifact.

**Implication**: when projecting across classifier namespaces, use pseudo-count / sparse-data-robust methods (LDA, MMvec, etc.) as primary; CLR-based methods (ANCOM-BC projection, GMM on CLR) as advisory at best. This generalizes beyond IBD — any project that trains on one microbiome classifier and projects another (MetaPhlAn ↔ Kraken, MetaPhlAn ↔ Kaiju, 16S ↔ WGS) faces this asymmetry.

### [ibd_phage_targeting] Cross-method ARI is the right K-selection criterion for microbiome ecotype models

Both LDA training perplexity (sklearn `LatentDirichletAllocation`) and GMM BIC (on CLR + PCA-20) are *monotone* with K on this data — they always prefer the largest K available. Held-out perplexity (5-fold) gives the same monotone signal at this sample size (~8.5K samples), so it doesn't help distinguish overfitting from genuine structure. The discriminating signal is **cross-method adjusted Rand index between LDA and GMM at each K**: it has structure (peaks, valleys) precisely because the two methods only agree on K's that reflect real data partitions, not method-specific artifacts. For `ibd_phage_targeting`, ARI peaks at K=7 (0.140) and K=4 (0.131); a parsimony rule (smallest K within 0.02 of the peak) selects K=4. This is the K that gives the most interpretable, biologically clean ecotypes (E0 healthy, E1 Bacteroides2 disease, E2 Prevotella, E3 severe Bacteroides). Generalizable to any project doing microbiome ecotype discovery with two different model families: prefer the K where they agree most, not the K each prefers individually.

### [ibd_phage_targeting] Four-ecotype framework on curatedMetagenomicData IBD reproduces published structure with disease-stratifying signal

K=4 LDA-GMM consensus on 8,489 CMD MetaPhlAn3 samples (5,333 HC + 3,156 IBD/other) yields four ecotypes that align with published gut-microbiome enterotype literature (Vandeputte 2017, Lloyd-Price 2019) and cleanly separate disease from healthy:

| Ecotype | n | Defining species | Diagnosis pattern |
|---|---|---|---|
| E0 — Diverse commensal | 3,604 | F. prausnitzii / R. bromii / B. uniformis / Bifidobacterium balanced | 66.8 % of HC |
| E1 — Bacteroides2 transitional | 2,601 | P. vulgatus / B. uniformis / B. dorei | 48 % CD, 58 % UC, 100 % T1D, 97 % T2D, 67 % nonIBD |
| E2 — Prevotella copri enterotype | 920 | P. copri 28 % | 16.9 % of HC, ~0 % disease (non-Western healthy) |
| E3 — Severe Bacteroides-expanded | 1,364 | P. vulgatus 14 % + B. fragilis 3.6 % | 50 % CD, 40 % UC, 67 % IBD acute flare, 38 % CDI |

CD and UC patients distribute across E1 and E3 rather than concentrating in any single ecotype — this is the patient-stratification signal that downstream within-ecotype analyses will exploit. Healthy samples concentrate in E0 + E2 (84 % combined). The Bacteroides2 ecotype's correlation with metabolic disease (T1D, T2D) AND IBD echoes the broader "low-diversity disease state" hypothesis. **`data/ecotype_assignments.tsv` is the consumable artifact for downstream notebooks.**

### [ibd_phage_targeting] `docs/collections.md` understates the BERDL catalog by several phage- and metagenome-relevant databases

Live `SHOW DATABASES` against the lakehouse returned 138 databases; the committed `docs/collections.md` omits several that matter for gut-microbiome / phage work:

- `kescience_mgnify` — EBI MGnify (metagenomics service), relevant for IBD-cohort cross-validation. This is also the answer to a mis-recalled `ke_science_magnify` — it's `mgnify`, not `magnify`.
- `phagefoundry_ecoliphages_genomedepot` (plus a duplicate `_genomedepot` variant) — E. coli phage genome collection, directly relevant for AIEC targeting. PhageFoundry has 7 databases in the tenant, not the 5 documented.
- `kescience_interpro` — InterPro domain annotations, primary source for virulence-factor classification.
- `kescience_pubmed` — literature text mining (sibling to `kescience_paperblast`).
- `pangenome_bakta` — a separate Bakta-pangenome slice distinct from `kbase_ke_pangenome`.
- `arkinlab_microbeatlas` — 464K global 16S samples, useful prevalence / biogeography baseline.
- `protect_integration` — second Protect-tenant database beyond `protect_genomedepot`.
- `u_kazakov__klebsiella_genomedepot` and `u_kazakov__strain_modelling` — user-owned Klebsiella phage-host work worth checking with the owner.

Recommend updating `docs/collections.md` with a full `SHOW DATABASES`-derived inventory; current coverage appears hand-curated and lags behind the live catalog.

### [ibd_phage_targeting] `schema_overview.yaml` + per-table `*.yaml` dictionaries is a useful convention for large local data marts

The UC Davis / Arkin CrohnsPhage data mart ships with a `lineage.yaml` (ETL provenance + changelog + known gaps), a `schema_overview.yaml` (table inventory by category), per-table `*.yaml` dictionaries (columns, dtypes, null counts, unique counts, sample values), and a `ref_missing_data_codes` table with sentinel codes (`PENDING_DAVE_LAB`, `PENDING_KUEHL`, `PENDING_HMP2_RAW`, etc.) that distinguish real NULLs from known-pending data. This pattern makes large local marts agent-readable without any live queries. Worth proposing as a BERIL convention for projects that accumulate their own data tables.

### [ibd_phage_targeting] Preliminary cross-cohort DA flags *C. scindens* as CD-enriched — a compositional / stratification artifact, not biology

The v2 preliminary IBD report (2026-03-28) called *C. scindens* CD-enriched at log₂FC = +2.67 from pooled Mann-Whitney DA. But *C. scindens* is a well-documented protective species (secondary bile-acid producer via 7α-dehydroxylation, TGR5 activator, ~79 % prevalence in healthy individuals, inhibits *C. difficile*). Three likely mechanisms produce this false call: (1) compositional / relative-abundance artifact — Ruminococcaceae loss in severe patients inflates relative abundance of surviving C. scindens strains; (2) strain heterogeneity — not all C. scindens strains carry the `bai` operon; species-level presence ≠ functional presence; (3) ecotype mixing — pooled analysis averages across patient subgroups with different microbiomes. Compositional-aware DA (ANCOM-BC / MaAsLin2 / LinDA) run *within* patient ecotypes is the proposed fix. This is the canonical example for why `ibd_phage_targeting` treats pre-computed `ref_*` tables as starting points requiring verification, not ground truth.

### [enigma_sso_asv_ecology] 16S community similarity maps contamination plume at meter scale
The SSO 3×3 well grid (~6 m span) shows significant distance-decay (Mantel ρ=0.323, p=0.029) driven by the east-west axis rather than the hillslope gradient. A diagonal corridor of wells (U3-M6-L7) shares community composition along the NE→SW plume flow path. Genus-level functional inference maps the thermodynamic redox ladder (denitrification → iron reduction → fermentation) onto the physical grid. M5 hosts a *Rhodanobacter* denitrification hotspot (7.7%) at the plume mixing zone. GW communities are temporally stable (well R²=49.9%, date R²=0.8% over 9 days). This demonstrates that 16S community data can delineate subsurface contamination flow paths at sub-decameter resolution.

### [enigma_sso_asv_ecology] SSO geochemistry not in BERDL despite 221 registered samples
221 METALS/ICTOC/ISOTOPES/NH3NO2 sample tubes from the SSO Subsurface Observatory campaign are registered in ENIGMA CORAL (`sdt_sample`) but zero `Assay Geochemistry` processes are linked — the analytical measurement values were never ingested. This is the key validation dataset for the plume model.

### [enigma_sso_asv_ecology] Nitrifier × iron oxidizer coupling (ρ=+0.95) at plume entry
*Candidatus Nitrosotalea* (archaeal ammonia oxidizer) and *Sideroxydans* (iron oxidizer) co-occur almost perfectly across the 9 SSO wells (ρ=+0.95), concentrated at U3. Both are chemolithotrophs exploiting reduced compounds arriving in the contamination plume. This tight coupling suggests shared environmental niche at the oxic plume fringe.

---

## 2026-03

### [amr_environmental_resistome] Resistance mechanism composition is strongly environment-dependent across 14,723 species

Efflux pumps constitute 21% of AMR in human gut species but only 1% in aquatic (η²=0.127). Metal resistance constitutes 45% in soil/aquatic but 6% in human gut (η²=0.107). Clinical species have 68% accessory (acquired) AMR vs soil 43%. Within 823 multi-environment species, clinical strain fraction predicts total AMR (rho=0.465, p=2.2e-45). K. pneumoniae has 1,115 AMR clusters (only 7 core) across 13,637 genomes. All findings survive family-level phylogenetic control (20/141 families significant). This is the largest genomic AMR-environment analysis to date, extending Gibson et al. (2015, 6K genomes) by 50×.

### [amr_cofitness_networks] AMR support networks enriched for flagellar motility and amino acid biosynthesis

Cofitness analysis of 801 AMR genes across 28 organisms reveals that AMR cofitness neighborhoods are enriched for flagellar motility (GO:0071973, 5 organisms FDR<0.05), flagellum assembly (GO:0044780, 5 orgs), histidine biosynthesis (GO:0000105, 3 orgs), and tryptophan biosynthesis (GO:0000162, 3 orgs). This enrichment is undetectable with old FB SEED annotations (0/280 significant) — only InterProScan GO (68% coverage) reveals it. Support networks are organism-specific (cross-mechanism Jaccard 0.375 >> within-mechanism 0.207, MWU p=4.3e-13). AMR genes are in larger-than-average ICA modules (median 46 vs 27, p=1.7e-8). The co-regulation with motility and biosynthesis suggests AMR costs reflect competition for the proton motive force.

### [amr_fitness_cost] AMR genes impose a universal +0.086 fitness cost across 25 bacteria

Random-effects meta-analysis of 801 AMR genes across 25 organisms shows a pooled fitness shift of +0.086 [+0.074, +0.098] when AMR genes are knocked out — all 25/25 organisms positive. This cost is mechanism-independent (KW p=0.89), conservation-independent (core = accessory, p=0.33), and tier-independent (bakta_amr = keyword, p=0.26). The uniformity suggests compensatory evolution has equalized costs to an irreducible floor. However, mechanism strongly predicts conservation status (metal resistance 44% accessory vs efflux 13%, χ²=69.3, p=1.4e-13) — acquisition history, not cost, determines whether AMR genes are core or accessory. Efflux genes (broad-spectrum) show a stronger antibiotic-dependent fitness flip than enzymatic inactivation genes (narrow-spectrum): +0.094 vs −0.001, MWU p=0.007.

### [amr_strain_variation] Acquired AMR genes track phylogeny more strongly than intrinsic

Mantel tests across 1,261 species show non-core (acquired) AMR genes have stronger phylogenetic signal (median r=0.222) than core (intrinsic) genes (median r=0.117), paired t-test p=7.0e-16. This contradicts the standard model that acquired resistance is phylogenetically random via HGT. Instead, once a lineage acquires resistance elements, they are stably maintained and vertically inherited, creating clonal AMR lineages. Note: core genes have near-zero Jaccard variance by definition (>=95% prevalence), which partly suppresses their distance-based signal.

### [amr_strain_variation] Over half of within-species AMR genes are rare (<5% prevalence)

Across 1,305 species and 180,025 genomes, 51.3% of AMR gene-species occurrences are rare (<=5% prevalence), 41.3% variable (5-95%), and only 7.5% fixed (>=95%). Median pairwise Jaccard distance between strains = 0.435 — strains within the same species share less than 60% of their AMR repertoire. Atlas Core genes are 77% fixed within species; Singletons are 79% rare — validating the cross-species conservation classification at strain resolution.

### [amr_strain_variation] Resistance islands are widespread — 54% of species, mean 6.2 genes

1,517 resistance islands detected across 705/1,305 species, with mean phi coefficient = 0.827 (very tight co-occurrence). 88% contain multiple resistance mechanisms (efflux + enzymatic inactivation most common). Maximum island = 43 genes. These multi-mechanism islands provide coordinated defense against multiple drug classes.

### [amr_strain_variation] AMR variability weakly anti-correlates with pangenome openness

Spearman rho = -0.193, p = 2.2e-12. Species with more open pangenomes have slightly *lower* AMR variability — unexpected. Likely because open-pangenome species accumulate more rare/singleton AMR genes below the 5% threshold, deflating the variability index (which measures the 5-95% zone).

### [truly_dark_genes] Only 16.3% of "dark matter" resists modern annotation

Of 39,532 Fitness Browser dark genes with pangenome links, bakta v1.12.0 reclassifies 33,105 (83.7%). Just 6,427 are "truly dark" — both FB and bakta agree: hypothetical protein. Truly dark genes are structurally distinct: shorter (121 vs 194 aa), less conserved (43% vs 73% core), fewer orthologs (29% vs 64%), higher GC deviation (d=0.247). These properties are consistent with recent HGT outpacing annotation databases.

### [truly_dark_genes] Truly dark genes cluster in genomic "dark islands"

41% of neighbors of truly dark genes are also hypothetical, 12% are within 2 genes of mobile elements (transposases, integrases, phage proteins). This suggests dark genes concentrate in recently acquired genomic islands rather than being randomly distributed.

### [truly_dark_genes] Stress enrichment hypothesis rejected — nutrient/community enrichment instead

Contrary to expectation, truly dark genes with strong fitness phenotypes are depleted in stress conditions (OR=0.53, p<0.001) and enriched in nutrient, mixed community, and iron conditions. This suggests novel metabolic or inter-species interaction functions rather than stress responses.

### [truly_dark_genes] 96% of truly dark genes have partial annotation clues

Only 246/6,427 (3.8%) truly dark genes have zero annotation clues. 84.7% have database cross-references, 43.5% have eggNOG hits (though 55% of COG assignments are "S"/unknown), 29.3% have cross-organism orthologs, 9.5% are in ICA fitness modules.

### [bakta_reannotation] Bakta and eggNOG are complementary annotation sources

Comprehensive comparison of bakta v1.12.0 vs eggNOG-mapper across 132.5M gene clusters:
- **EggNOG wins** on enrichment-style annotations: COG (51% vs 8.2%), KEGG (38.5% vs 17.3%), Pfam (63% vs 7.7%)
- **Bakta wins** on GO terms (15% vs 7.4%), product descriptions (71.2% vs 70.4%), and UniRef50 links (79.2%, unique)
- **Union raises coverage** from ~70% to 77.3% for "any functional annotation"
- Bakta rescues 11.2M clusters (of 39.2M) that eggNOG misses entirely

### [bakta_reannotation] Bakta's lower COG/KEGG/Pfam coverage is by design, not a bug

Confirmed by bakta developer Oliver Schwengers across GitHub issues #350, #385, #391, #393:
- **PSC pre-computed annotations are sparse**: only ~14% of PSC entries have COG, ~19% have KEGG. PSC DB is optimized for product descriptions, not functional categories.
- **COG 2024 broke direct mapping**: COG 2024 no longer provides representative sequences, forcing lossy indirect WP accession→IPS→PSC mapping.
- **Pfam skipped by design**: HMMER only runs on hypotheticals (~7.7%). The 92% with PSC matches never get Pfam searched.
- **DIAMOND fast < HMM sensitivity**: bakta's PSC uses DIAMOND fast mode; eggNOG uses HMM-based ortholog assignment.
- Developer planned to integrate eggNOG into PSC representatives (issue #325) — may have partially happened in DB v6.0 but limited impact.
- The Arche benchmark paper (Alonso-Reyes & Albarracin 2025, PMID 40811208) independently confirmed bakta's conservative annotation transfer vs. other tools.

### [bakta_reannotation] UniRef50 bridge has limited value with current BERDL UniProt

- Only 33.3% of bakta's 17.6M distinct UniRef50 IDs exist in `kbase_uniprot.uniprot_identifier`
- The bridge reaches RefSeq (71%), OrthoDB (46%), STRING (40%), KEGG (36%) of matched IDs
- **Missing from bridge**: GO, EC, InterPro, Pfam — importing full UniProt would unlock these
- For now, eggNOG remains the better source for COG/KEGG/Pfam enrichment analysis

### [bakta_reannotation] Spark broadcast joins fail on uniprot_identifier (2.5B rows)

Any join that touches `kbase_uniprot.uniprot_identifier` can exceed `spark.driver.maxResultSize` (1GB) via broadcast exchange. Fix: `SET spark.sql.autoBroadcastJoinThreshold = -1` to force sort-merge joins. See `data/bakta_reannotation/scripts/compare_bakta_eggnog.py` for the pattern.

---

## 2026-01

### [ecotype_analysis] Environment vs Phylogeny: Phylogeny usually dominates

Analysis of 172 species with sufficient data showed:
- Median partial correlation for environment effect: 0.0025
- Median partial correlation for phylogeny effect: 0.0143
- Phylogeny dominates in 60.5% of species
- Environment dominates in 39.5% of species

No significant difference between "environmental" bacteria (where lat/lon is meaningful) and host-associated bacteria (p=0.66).

### [ecotype_analysis] ANI extraction requires per-species iteration

Attempting to query ANI for all 13K+ genomes in a single IN clause fails/times out. Must iterate over species and query ANI for each species separately. See `docs/performance.md` for pattern.

### [pangenome_openness] Pangenome table has pre-computed stats

The `pangenome` table already contains `no_core`, `no_aux_genome`, `no_singleton_gene_clusters`, `no_gene_clusters` - no need to compute from gene_cluster table.

### [pangenome_openness] No correlation between openness and env/phylo effects

Tested whether open pangenomes (low core fraction) show different patterns. Results:
- rho=-0.05, p=0.54 for environment effect
- rho=0.03, p=0.73 for phylogeny effect
- No significant relationship found

### [integrity_checks] 12 orphan pangenomes are symbionts

The 12 pangenomes without matching species clades are mostly obligate symbionts:
- Portiera aleyrodidarum (whitefly symbiont)
- Profftella armatura (psyllid symbiont)
- Various uncultivated lineages (UBA, TMED, SCGC prefixes)

These are valid pangenomes but filtered from species metadata due to single-genome status.

### [cog_analysis] Universal functional partitioning in bacterial pangenomes

Analysis of 32 species across 9 phyla (357,623 genes) reveals a remarkably consistent "two-speed genome":

**Novel/singleton genes consistently enriched in:**
- L (Mobile elements): +10.88% enrichment, 100% consistency across species - STRONGEST SIGNAL
- V (Defense mechanisms): +2.83% enrichment, 100% consistency
- S (Unknown function): +1.64% enrichment, 69% consistency

**Core genes consistently enriched in:**
- J (Translation): -4.65% enrichment, 97% consistency - STRONGEST DEPLETION
- F (Nucleotide metabolism): -2.09% enrichment, 100% consistency
- H (Coenzyme metabolism): -2.06% enrichment, 97% consistency
- E (Amino acid metabolism): -1.81% enrichment, 81% consistency
- C (Energy production): -1.75% enrichment, 88% consistency

**Biological implications:**
- Core genes = ancient, conserved "metabolic engine" (translation, energy, biosynthesis)
- Novel genes = recent acquisitions for ecological adaptation (mobile elements, defense, niche-specific)
- Horizontal gene transfer (HGT) is the primary innovation mechanism, not vertical inheritance
- The massive L enrichment (+10.88%) suggests most genomic novelty comes from mobile elements
- Patterns hold universally across bacterial phyla, suggesting deep evolutionary constraint

**Hypothesis validation:** All 8 predictions from initial N. gonorrhoeae analysis confirmed across 32 species.

This represents a fundamental organizing principle of bacterial pangenome structure.

### [cog_analysis] Composite COG categories are biologically meaningful

Multi-function genes with composite COG assignments (e.g., "LV" = mobile+defense, "EGP" = amino acid+carb+inorganic ion) are not annotation artifacts:

- LV (mobile+defense): +0.34% enrichment, 76% consistency
- Suggests functional modules like "mobile defense islands"
- Should not be filtered out as noise - they represent genuine multi-functional genes

## 2026-02

### [respiratory_chain_wiring] ADP1 uses qualitatively different respiratory configurations per carbon source

Each of ADP1's 8 carbon sources requires a distinct set of respiratory chain components. Quinate requires only Complex I (all other components dispensable). Acetate requires Complex I + cytochrome bo3 + ACIAD3522 + more (the most demanding). Glucose requires no specific component (full redundancy). This is not a quantitative gradient — it's qualitatively different wiring per substrate class.

### [respiratory_chain_wiring] NADH flux rate, not total yield, determines Complex I essentiality

Quinate produces fewer NADH per carbon (0.57) than glucose (1.50), yet Complex I is more essential on quinate. The resolution: β-ketoadipate pathway products (succinyl-CoA + acetyl-CoA) enter the TCA cycle simultaneously, creating a concentrated NADH burst that exceeds NDH-2's reoxidation capacity. Glucose distributes NADH across Entner-Doudoroff + TCA steps where NDH-2 suffices.

### [respiratory_chain_wiring] Respiratory chain wiring is metabolic, not transcriptional

Proteomics shows all three NADH dehydrogenases are expressed at similar levels under standard conditions: Complex I mean 27.6 (66th percentile), NDH-2 27.0 (59th), ACIAD3522 26.2 (48th) — all within 1.4 units of each other around the genome median (26.4). The cell doesn't switch respiratory configurations by regulating dehydrogenase expression. Instead, all three run simultaneously and the one that becomes limiting depends on the NADH flux rate from the carbon source. This is a passive, flux-based wiring system rather than an active regulatory switch.

### [respiratory_chain_wiring] ADP1 has three NADH dehydrogenases with non-overlapping condition requirements

Complex I (13 subunits, proton-pumping): quinate-essential, glucose-dispensable. NDH-2 (1 subunit, non-pumping): no growth data but predicted backup for glucose. ACIAD3522 (NADH-FMN oxidoreductase): acetate-lethal (0.013), quinate-fine (1.39). Each handles a different metabolic regime — division of labor in electron transport.

### [aromatic_catabolism_network] Aromatic catabolism requires 7× more support genes than pathway genes

The β-ketoadipate pathway in ADP1 has 8 core genes, but 51 genes total show quinate-specific growth defects — a 7:1 support-to-pathway ratio. The support genes organize into 3 biochemically rational subsystems: Complex I (21 genes, NADH reoxidation), iron acquisition (7 genes, Fe²⁺ for ring-cleavage dioxygenase), and PQQ biosynthesis (2 genes, cofactor for quinate dehydrogenase). This quantifies a general principle: the metabolic infrastructure required to run a pathway dwarfs the pathway itself.

### [aromatic_catabolism_network] FBA models miss 59% of condition-specific essential genes

Of the 51 quinate-specific genes, 30 (59%) have no FBA reaction mappings — PQQ biosynthesis, iron acquisition, transcriptional regulators, and respiratory chain components are invisible to the metabolic model. For Complex I specifically, FBA predicts 1.76× higher flux on aromatics but 0% essentiality, because FBA's linear programming cannot represent the threshold effect of losing a single subunit from a multi-subunit complex.

### [aromatic_catabolism_network] Complex I dependency is on NADH flux, not aromatic chemistry

Cross-species ortholog-transferred fitness data shows Complex I defects are largest on acetate (-1.55 vs background) and succinate (-1.39), not aromatics. ADP1's quinate-specificity likely reflects an alternative NADH dehydrogenase (NDH-2) that compensates on lower-NADH-flux substrates. The "aromatic support network" is really a "high-NADH-flux bottleneck network."

### [aromatic_catabolism_network] Two DUF proteins are candidate Complex I accessory factors

ACIAD3137 (UPF0234/YitK) and ACIAD2176 (DUF2280) correlate at r > 0.98 with Complex I genes across 8 growth conditions. Both lack FBA reaction mappings and have no assigned metabolic function. Their near-perfect co-fitness with the nuo operon suggests physical or regulatory association with Complex I.

### [respiratory_chain_wiring] ACIAD3522 is the most condition-specific gene in the ADP1 genome

ACIAD3522 (NADH-FMN oxidoreductase) has a growth ratio of 0.013 on acetate — essentially lethal — while showing no defect on quinate (1.39) or glucose (1.39). This is the largest condition-specific effect of any single gene in the 2,034-gene growth matrix. FBA predicts zero flux through ACIAD3522 on all conditions. Its biological role is unknown but the extreme acetate specificity suggests it catalyzes an NADH-linked reaction that is uniquely required for acetate catabolism.

### [respiratory_chain_wiring] NDH-2 compensation hypothesis not supported cross-species

After correcting NDH-2 false positives (filtering text-matched candidates to organisms with ≤2 hits per genome), the cross-species compensation test reverses: organisms WITH validated NDH-2 show LARGER Complex I aromatic deficits (mean -0.297) than those without (-0.156, p=0.52). The initial analysis (10/14 organisms with NDH-2, apparent support for compensation) was driven by misannotated Complex I subunits leaking through the text filter in 5 organisms. This demonstrates the importance of validating text-based gene identification — a finding that looked supportive was actually an annotation artifact.

### [adp1_deletion_phenotypes] 625 condition-specific genes map precisely to expected metabolic pathways

31% of dispensable genes have condition-specificity scores ≥ 1.0. Top condition-specific genes for each carbon source are the enzymes biochemically predicted to be required: urease subunits for urea, protocatechuate 3,4-dioxygenase for quinate, Entner-Doudoroff enzymes for glucose, glyoxylate shunt for acetate, lactate-responsive regulator for lactate. This validates the growth matrix as a high-quality functional genomics dataset.

### [adp1_deletion_phenotypes] ADP1 phenotype landscape is a continuum, not discrete modules

Hierarchical clustering of 2,034 genes by their 8-condition growth profiles produces an optimal K=3 with silhouette=0.24 — no discrete functional modules. The phenotype landscape is a gradient, with one exception: 24 genes form a tight quinate-specific module (the aromatic degradation pathway). Gene essentiality varies continuously across conditions, supporting the Guzman et al. (2018) "adaptive flexibility" framework.

### [adp1_deletion_phenotypes] Missing dispensable genes are shorter, less annotated, and less conserved

Of 2,593 TnSeq-dispensable genes, 272 (10.5%) lack growth data from the deletion collection. These are systematically different: shorter (813 vs 981 bp), less annotated (91% vs 100% RAST), and less conserved in the pangenome (76.5% core vs 93.3%, p=1.4e-20). Hypothetical proteins are massively enriched (q=2.4e-25). The deletion collection has a bias toward well-characterized, conserved genes.

### [fitness_modules] ICA reliably decomposes fitness data into biologically coherent modules

Robust ICA (30-50 FastICA runs + DBSCAN clustering) consistently finds 17-52 stable modules per organism across 32 bacteria. 94.2% of modules show significantly elevated within-module cofitness (Mann-Whitney U, p < 0.05; mean |r| = 0.34 vs background 0.12). Genomic adjacency enrichment averages 22.7× across organisms, confirming modules capture operon-like co-regulated gene groups.

### [fitness_modules] Membership thresholding is the critical parameter, not ICA itself

The initial D'Agostino K² normality-based thresholding gave 100-280 genes per module — biologically meaningless. The ICA components themselves were fine; the problem was deciding which genes "belong" to each module. Switching to an absolute weight threshold (|Pearson r| ≥ 0.3 with module profile, max 50 genes) reduced modules to 5-50 genes and dramatically improved all validation metrics:
- Cofitness enrichment: 59% → 94.2%
- Within-module |r|: 0.047 → 0.34 (mean across 32 organisms)
- Modules became biologically coherent (22.7× genomic adjacency enrichment)

### [fitness_modules] Organisms with <200 experiments still produce valid modules

Caulo (198 experiments) showed the weakest signal in the pilot (2.9x correlation enrichment vs 31x for DvH), but organisms down to 104 experiments (Ponti) still produced stable modules. The key is capping components at 40% of experiments — higher ratios cause FastICA convergence failures and extreme slowness.

### [fitness_modules] Fitness Browser schema documentation has inaccuracies

Several table schemas differ from the documented schema:
- `keggmember` uses `keggOrg`/`keggId` (not `orgId`/`locusId`) — must join through `besthitkegg`
- `kgroupec` uses `ecnum` (not `ec`)
- `seedclass` has `orgId, locusId, type, num` (not subsystem/category hierarchy)
- `fitbyexp_*` tables are long format (not pre-pivoted as documented)

### [fitness_modules] Spark is accessible from CLI via berdl_notebook_utils

`from berdl_notebook_utils.setup_spark_session import get_spark_session` works from regular Python scripts on JupyterHub — not just notebook kernels. This enables running full analysis pipelines from the command line without `jupyter nbconvert`. The auto-import in `/configs/ipython_startup/00-notebookutils.py` only affects notebook kernels.

### [fitness_modules] Pan-bacterial module families exist across diverse phyla

Cross-organism module alignment using BBH ortholog fingerprints revealed 156 module families spanning 2+ organisms. The largest family spans 21 of 32 organisms across Proteobacteria, Bacteroidetes, Firmicutes, and Archaea — evidence of deeply conserved fitness regulons. 28 families span 5+ organisms.

This required using orthologs from ALL organisms in the analysis — an initial run using only 5-organism orthologs found just 27 families with no family spanning more than 4 organisms. The ortholog graph density is critical.

### [fitness_modules] Ortholog scope dramatically affects cross-organism analysis

Using BBH pairs from 5 organisms (10K pairs, 1,861 OGs) vs all 32 organisms (1.15M pairs, 13,402 OGs) produced radically different results:
- Module families: 27 → 156 (6x)
- Families spanning 5+ orgs: 0 → 28
- Family-backed predictions: 31 (4%) → 493 (56%)

Lesson: always extract orthologs for ALL organisms in the analysis, not just a pilot subset. The ortholog graph is not additive — adding organisms creates new transitive connections.

### [fitness_modules] PFam domains are essential for module enrichment — KEGG KOs are too fine-grained

The initial enrichment pipeline (KEGG + SEED + TIGRFam, min_annotated=3) annotated only 8.2% of modules (92/1,116). Root cause: KEGG KO groups average ~1.2 genes per term, so modules with 5-50 members almost never have 3+ genes sharing the same KO. Adding PFam domains (which have 814 terms with 2+ genes vs TIGRFam's 88) and lowering the overlap threshold to 2 increased annotation to 79.7% (890/1,116). PFam is the dominant annotation source — it provides domain-level functional labels that match module granularity.

Impact on downstream analysis:
- Predictions: 878 → 6,691 (7.6×), now covering all 32 organisms
- Annotated families: 32 → 145 out of 156 (93%)
- Three organisms (Caulo, Methanococcus_S2, Korea) went from 0 enrichments to 24-29 enriched modules

### [fitness_modules] Module-ICA is complementary to sequence-based methods, not competitive

Held-out KO prediction benchmark across 32 organisms showed ortholog transfer dominates at gene-level function prediction (95.8% precision, 91.2% coverage), while Module-ICA has <1% precision at the KO level. This is expected and informative, not a failure: modules capture **process-level co-regulation** (validated by 94.2% cofitness enrichment and 22.7× adjacency enrichment), not specific molecular function. An ABC transporter module correctly groups binding, permease, and ATPase subunits — but each has a different KO. The right framing for module-based predictions is "involved in [biological process]" not "has function [specific KO]."

### [fitness_modules] Enrichment min_annotated threshold must match annotation granularity

The min_annotated parameter (minimum overlapping genes to test for enrichment) must be calibrated to the annotation database's granularity. For gene-specific annotations (KEGG KOs: ~1 gene/term), min_annotated=3 eliminates nearly all tests. For domain-level annotations (PFam: many genes share domains), min_annotated=2 works well with FDR correction. Fisher's exact test handles small counts correctly — the statistical validity comes from FDR correction across all tests, not from requiring large overlaps per test.

### [conservation_vs_fitness] Essential genes are modestly enriched in core pangenome clusters

Across 33 diverse bacteria, putative essential genes (no transposon insertions in RB-TnSeq) are 86.1% core vs 81.2% for non-essential genes (median OR=1.56, 18/33 significant after BH-FDR). The enrichment is real but modest — most genes in well-characterized bacteria are core regardless of essentiality. The signal is strongest in organisms with larger clades (more genomes = more reliable core classification).

### [conservation_vs_fitness] Essential-core genes are functionally distinct from essential-auxiliary

Essential genes that map to core clusters are 41.9% enzymes and only 13.0% hypothetical — they are the well-characterized metabolic backbone (ribosomes, DNA replication, cell wall, cofactor biosynthesis). Essential-auxiliary genes (essential but not in all strains) are only 13.4% enzymes and 38.2% hypothetical. Essential-unmapped genes (strain-specific, no pangenome match) are 44.7% hypothetical — prime targets for functional discovery.

### [conservation_vs_fitness] SEED functional categories distinguish essential from non-essential

Essential-core genes are enriched in Protein Metabolism (+13.7 pp vs non-essential), Cofactors/Vitamins (+6.2 pp), Cell Wall (+3.9 pp). They are depleted in Carbohydrates (-7.9 pp), Amino Acids (-5.6 pp), Membrane Transport (-4.0 pp) — functions that are conditionally important rather than universally essential. This aligns with Rosconi et al. (2022) who found pan-genome composition influences essentiality in *S. pneumoniae*.

### [conservation_vs_fitness] FB aaseqs download uses different locus tags than the gene table for some organisms

The Fitness Browser aaseqs file (fit.genomics.lbl.gov/cgi_data/aaseqs) uses RefSeq-style locus tags (e.g., ABZR86_RS*) for some organisms, while the FB `gene` table uses the original annotation locus tags (e.g., N515DRAFT_*). This caused a complete join failure for Dyella79 (0% merge rate). Only 1 of 34 organisms was affected, but any pipeline joining aaseqs-derived data with gene table data should verify locus tag consistency.

### [fitness_effects_conservation] Fitness importance and pangenome conservation form a continuous gradient

Across 194,216 protein-coding genes in 43 bacteria, there is a clear 16-percentage-point gradient from essential genes (82% core) to always-neutral genes (66% core). The same pattern holds when binning by strongest negative fitness effect (min_fit < -3 → 78% core vs min_fit near 0 → 66%) and by fitness breadth (important in 20+ conditions → 79% core vs 0 conditions → 66%). This establishes that the essentiality-conservation link from `conservation_vs_fitness` is not binary but quantitative.

### [fitness_effects_conservation] Core genes are MORE likely to be burdens, not less

Counter to the expectation that accessory genes impose a carrying cost, core genes are more likely to show positive fitness effects when deleted (24.4% ever beneficial vs 19.9% for auxiliary; OR=0.77 for auxiliary vs core, p=5.5e-48). Core genes participate in more pathways and trade-off situations — they help in some conditions but cost in others. This challenges the "streamlining" model where accessory genes are metabolic burdens.

### [fitness_effects_conservation] Condition-specific fitness genes are more core, not more accessory

Genes with strong condition-specific phenotypes (from the FB `specificphenotype` table) are 77.3% core vs 70.3% for genes without specific phenotypes (OR=1.78, p=1.8e-97). This contradicts the intuition that condition-specific fitness = niche-specific genes = accessory genome. Instead, core genes are more likely to have detectable condition-specific effects because they are embedded in well-characterized, essential pathways.

### [module_conservation] Fitness modules are enriched in core genome genes

ICA fitness modules (co-regulated gene groups) are 86.0% core vs 81.5% baseline across 29 organisms (Fisher OR=1.46, p=1.6e-87; per-organism paired Wilcoxon p=1.0e-03, 22/29 organisms show enrichment). 59% of modules are >90% core genes. Co-regulated fitness response units are preferentially embedded in the conserved genome — the core genome is not just structurally conserved but functionally coherent at the module level.

### [module_conservation] Module family breadth does NOT predict conservation

Surprisingly, module families spanning more organisms do not have higher core fractions (Spearman rho=-0.01, p=0.914). The baseline core rate (~82%) is so high that there is no room for a gradient — families are nearly all core regardless of breadth. This is a ceiling effect, not evidence against the conservation-function relationship.

### [module_conservation] Essential genes are absent from ICA modules

0 essential genes appear in any of the 1,116 fitness modules across 32 organisms. ICA decomposes fitness variation, so genes with no fitness data (essential = no transposon insertions) are invisible to it. This means fitness modules capture only the non-essential portion of the genome's functional architecture.

### [core_gene_tradeoffs] Trade-off genes are enriched in the core genome

25,271 genes (17.8%) are true trade-offs — important (fit < -1) in some conditions, burdensome (fit > 1) in others. These are 1.29x more likely to be core (OR=1.29, p=1.2e-44). Core genes have more trade-offs because they participate in more pathways with condition-dependent costs and benefits. This explains why core genes are simultaneously more burdensome AND more essential than accessory genes.

### [core_gene_tradeoffs] The burden paradox is function-specific, not universal

The core-burden paradox is driven by specific functional categories: RNA Metabolism (+12.9pp), Motility/Chemotaxis (+7.8pp), Protein Metabolism (+6.2pp) all show core genes as more burdensome. But Cell Wall reverses: non-core cell wall genes are MORE burdensome (-14.1pp). The paradox is not a uniform property of the core genome but reflects the trade-off architecture of specific functional systems.

### [core_gene_tradeoffs] 28,017 "costly + conserved" genes = natural selection signature

Genes that are both burdensome in the lab AND core in the pangenome represent the strongest evidence for purifying selection in natural environments. They're costly to maintain, yet every strain keeps them — nature requires them in conditions not captured by the lab. By contrast, 5,526 genes are costly + dispensable (candidates for ongoing gene loss), and 21,886 are neutral + dispensable (niche-specific).

### [essential_genome] 15 gene families are essential in ALL 48 bacteria

Cross-organism essential gene analysis across 48 diverse bacteria (221,005 genes, 17,222 ortholog families) reveals 15 families that are essential in every organism: ribosomal proteins (rpsC, rplW, rplK, rplB, rplA, rplF, rps11, rpsJ, rpsI, rpsM), chaperonin (groEL), CTP synthase (pyrG), translation elongation factor G (fusA), valyl-tRNA synthetase (valS), and geranyltranstransferase (SelGGPS). These represent the irreducible essential core of bacterial life.

### [essential_genome] Only 5% of ortholog families are universally essential

Of 17,222 ortholog families across 48 bacteria, only 859 (5.0%) are universally essential — essential in every organism where the family has members. 4,799 families (27.9%) are variably essential (essential in some organisms, non-essential in others), and 11,564 (67.1%) are never essential. Variable essentiality (the majority of essential families) demonstrates that genomic context profoundly shapes which genes an organism requires for viability.

### [essential_genome] Orphan essential genes are 58.7% hypothetical — top functional discovery targets

7,084 essential genes have no orthologs in any other FB organism. Of these, 58.7% are annotated as hypothetical proteins — the least characterized yet most functionally important genes in each organism. By contrast, universally essential genes are only 8.2% hypothetical. The orphan essentials are prime candidates for novel biology.

### [essential_genome] Universally essential families are overwhelmingly core in the pangenome

Universally essential genes are 91.7% core vs 80.7% for non-essential genes. 71% of universally essential families are 100% core across all genomes in their species. Orphan essentials (no orthologs) are only 49.5% core — they are strain-specific essential functions that haven't been conserved across species.

### [essential_genome] Module transfer predicts function for 1,382 hypothetical essential genes

By finding non-essential orthologs that participate in ICA fitness modules, we generated 1,382 function predictions for hypothetical essential genes across 48 organisms. All predictions are backed by cross-organism module family conservation. This demonstrates that module context from non-essential orthologs can illuminate the function of essential genes that are invisible to fitness-based methods.

### [ecotype_env_reanalysis] Clinical sampling bias does NOT explain weak environment-gene content signal

The `env_embedding_explorer` project showed that human-associated samples dampen AlphaEarth geographic signal (2.0x vs 3.4x for environmental). We hypothesized this bias explained the weak environment effect in the ecotype analysis (median partial correlation 0.003). However, stratifying 213 species by dominant environment type (47% human-associated, 21% environmental) shows the opposite: human-associated species have *higher* partial correlations (median 0.084) than environmental species (0.051). Mann-Whitney p=0.83. The original conclusion — phylogeny dominates — holds regardless of sample environment. The geographic signal in embeddings and the environment-gene content relationship are distinct phenomena.

### [ecotype_env_reanalysis] 47% of ecotype species are human-associated by genome-level classification

Using isolation_source harmonization (12 categories from 5,774 values), 106/224 species in the ecotype analysis are majority human-associated (gut + clinical). Only 47/224 (21%) are majority environmental (Soil, Marine, Freshwater, Extreme, Plant). This is a more systematic classification than the original manual species-level categorization, and confirms the clinical bias but shows it doesn't confound the ecotype results.

### [env_embedding_explorer] AlphaEarth embeddings encode geographic signal, but strength depends on sample type

Environmental samples (Soil, Marine, Freshwater, Extreme, Plant) show a 3.4x ratio in embedding cosine distance between nearby (<100 km, mean=0.27) and far (>10K km, mean=0.90) genome pairs. Human-associated samples (gut, clinical) show only a 2.0x ratio (0.37 vs 0.75). Hospitals worldwide have similar satellite imagery (urban built environment), so human-associated genomes have more homogeneous embeddings regardless of geography. The pooled "All samples" curve (2.0x ratio) is dominated by the 38% human-associated fraction and substantially underestimates the true geographic signal in the embeddings.

**Implication**: Any analysis using AlphaEarth embeddings as environment proxies should stratify by sample type, or at minimum exclude human-associated samples. The weak environment signal found in `ecotype_analysis` (median partial correlation 0.0025) may be partially explained by this clinical bias.

### [env_embedding_explorer] 38% of AlphaEarth genomes are human-associated — strong clinical sampling bias

Of 83,287 genomes with AlphaEarth embeddings, 38% are human-associated (clinical 20%, gut 16%, other 2%). Environmental categories are much smaller (soil 7%, marine 7%, freshwater 7%). This reflects NCBI's bias toward pathogen sequencing — clinical isolates have good geographic metadata from epidemiological tracking, which is why they disproportionately have embeddings.

### [env_embedding_explorer] 36% of AlphaEarth coordinates may be institutional addresses, but some are legitimate field sites

30,469 genomes (36.6%) cluster at coordinates with >50 genomes of >10 species. However, several flagged locations are legitimate DOE/research field sites: Rifle, CO (1,883 genomes, DOE IFRC), Saanich Inlet (1,529, oceanographic time series), Siberian soda lakes (812, extremophile campaigns). The heuristic needs refinement — checking isolation_source homogeneity at each location would better distinguish field sites from institutional addresses.

### [env_embedding_explorer] 4.6% of AlphaEarth genomes have NaN embedding dimensions

3,838 of 83,287 genomes have NaN in at least one of the 64 embedding dimensions. The cause is unclear — possibly missing satellite imagery at those coordinates, or coordinates that fall outside satellite coverage (polar regions, ocean). These must be filtered before any embedding-based analysis.

### [enigma_contamination_functional_potential] Primary contamination-functional tests are null, but defense signal appears in coverage-aware sensitivity models

In the ENIGMA contamination-functional project (108 overlap samples), primary univariate associations were non-significant across defense, stress, metabolism, and mobilome outcomes in both mapping modes. However, after adding mapped-coverage-aware sensitivity models, contamination-defense association became significant (coverage-adjusted OLS contamination p = 3.98e-4 relaxed, 3.54e-3 strict; high-coverage subset Spearman p = 0.0207 relaxed, 0.0098 strict). This indicates the strongest signal is conditional on mapping coverage/model specification rather than broad across all outcomes.

### [enigma_contamination_functional_potential] Independent strict vs relaxed feature construction materially changes mode-specific outputs

When strict and relaxed mapping modes were computed independently in NB02 (instead of reusing strict outputs), 1,140 of 1,590 genus-feature pairs differed between modes (~71.7%), and site stress scores differed for all 108 samples. Strict-vs-relaxed sensitivity is therefore analytically meaningful and should not be approximated by copied feature tables.

### [enigma_contamination_functional_potential] Species-proxy bridge is currently coverage-limited under genus-only ENIGMA taxonomy

`enigma_coral.ddt_brick0000454` currently provides taxonomy through `Genus` (no species/strain rows). A species-proxy mode (`species_proxy_unique_genus`) that keeps only unique genus->single GTDB clade mappings retained 150 genera, but mapped abundance collapsed to mean 0.031 (vs 0.343 in strict/relaxed genus modes). In this low-coverage regime, defense trend was positive (rho=0.169) but non-significant (p=0.081), indicating that true species-level gains likely require higher-resolution ENIGMA taxonomy or metagenomic mapping.

### [enigma_contamination_functional_potential] Confirmatory defense tests remain null after global FDR; strongest signal remains exploratory and coverage-dependent

After adding explicit confirmatory vs exploratory labels in NB03 and applying global BH-FDR across all reported p-values, confirmatory defense Spearman tests in genus-level modes remained null (p=0.546/0.483; q=0.862/0.849). The strongest surviving signal was exploratory: relaxed coverage-adjusted defense model retained q=0.046, while strict and other sensitivity signals attenuated above q<0.1. Interpretation should therefore prioritize null confirmatory evidence and frame positive results as exploratory.

### [enigma_contamination_functional_potential] Confirmatory null is robust to contamination-index choice

Re-testing confirmatory defense endpoint under four index constructions (all-metals composite, uranium-only, top-3 variance metals, PCA-PC1) did not produce significant confirmatory associations after FDR correction (all q=0.546 across 8 confirmatory-variant tests). This indicates the null confirmatory result is not an artifact of one specific contamination-index formulation.

---

### [nmdc_community_metabolic_ecology] Black Queen Hypothesis is detectable at community scale in environmental metabolomics

Spearman correlation of community-weighted GapMind amino acid biosynthesis completeness against
ambient amino acid metabolomics across 131 NMDC soil samples:

- **11/13 tested aa pathways trend in BQH-predicted direction** (negative r = lower community
  completeness co-occurs with higher ambient metabolite concentration); binomial sign test
  p = 0.011
- **Two pathways reach FDR significance** (BH-corrected q < 0.05): leucine (r = −0.390, q = 0.022,
  n = 62) and arginine (r = −0.297, q = 0.049, n = 80)
- Both FDR-significant pathways are among the most energetically expensive to synthesize (leucine:
  37 ATP equivalents; arginine: 26 ATP equivalents) — consistent with BQH predicting loss is
  most favored when the benefit of gene retention is lowest
- Methionine shows the largest effect (r = −0.496) but is underpowered (n = 18, q = 0.117)
- **leu signal is robust** to soil-only stratification (q = 0.022 unchanged) and to study-level
  blocking (dataset is 95% single-study; see below)
- Tyrosine is an anti-BQH outlier (r = +0.42, ns): likely explained by phenylalanine hydroxylation
  providing an alternative tyrosine source that decouples biosynthesis completeness from pool size

First demonstration that community-weighted pangenome completeness scores correlate with measured
metabolite pools at landscape scale using public multi-omics data.

### [nmdc_community_metabolic_ecology] Carbon utilization pathways, not amino acid pathways, are the primary axis of ecosystem metabolic differentiation

PCA of 220-sample × 80-pathway GapMind completeness matrix:

- **PC1 = 49.4% of variance** captures near-complete Soil vs Freshwater separation (Mann-Whitney
  p < 0.0001; median PC1 Soil = +3.86, Freshwater = −6.28)
- PC1 loadings are dominated by carbon utilization pathways (glucuronate, fumarate, succinate,
  cellobiose, galactose) — **not** amino acid pathways
- Amino acid pathways load more strongly on PC2 (16.6%), separating sub-clusters within Soil
- 17/18 aa pathways are significantly differentiated across ecosystem types (q < 0.05 KW),
  but the primary driver is carbon substrate availability, not biosynthesis capacity

Implication: when community metabolic potential is used as a feature space, carbon substrate range
is the dominant ecological axis and will confound aa pathway analyses unless controlled for.
Use PC1-residualized or ecosystem-stratified analyses for BQH-type tests.

### [nmdc_community_metabolic_ecology] NMDC metabolomics overlap is dominated by a single study

Study-level analysis of the 131-sample H1 dataset revealed that **95% of samples (125/131) come
from one NMDC study** (nmdc:sty-11-r2h77870). The remaining 6 samples are from a second study.
This means:
- Cross-study LC-MS protocol heterogeneity is effectively absent as a confounder (contrary to
  the naive expectation for NMDC metabolomics)
- The leucine BQH signal is internally consistent within one analytical protocol
- Future multi-study NMDC metabolomics analyses should count study-level sample representation
  before treating the aggregate as cross-study data

### [nmdc_community_metabolic_ecology] NMDC metabolomics KEGG annotation rate is ~2%; string matching required

Only ~2% of compounds in `nmdc_arkin.metabolomics_gold` have KEGG compound IDs populated.
Pathway matching must rely on compound name substring patterns rather than KEGG-based ontologies.
Key caveats:
- Substring matching introduces collision risk (e.g., `'leucine'` matches inside `'isoleucine'`) —
  use first-match-wins ordering with longer/more specific patterns before shorter ones
- Chorismate itself is rarely detected; shikimic acid and 3-dehydroshikimic acid serve as upstream
  proxies but reflect precursor availability, not chorismate pool size
- Three aa pathways remain untestable (cys, his, lys) due to absent compound detections in the
  175-sample overlap cohort

See also `docs/pitfalls.md` for the isoleucine/leucine substring collision fix.

---

### [pangenome_pathway_geography] Ecological niche breadth strongly predicts metabolic pathway diversity

Analysis of 1,872 bacterial species with complete pangenome, GapMind pathway, and AlphaEarth embedding data reveals:

**H1: Pangenome openness → pathway completeness** (r=0.107, p=3.6e-6)
- Weak but significant positive correlation
- Open pangenomes (high accessory/core ratio) have slightly more complete pathways
- Stronger relationship with pathway VARIABILITY (std dev): r=0.066, p=0.004
- Suggests accessory genes enable metabolic heterogeneity within species

**H2: Niche breadth → pathway completeness** (r=0.392, p=7.1e-70) — STRONGEST SIGNAL
- Moderate positive correlation using AlphaEarth embedding diversity
- Embedding variance (ecological diversity) has even stronger effect: r=0.412, p=1.8e-77
- Geographic distance alone: r=0.360, p=1.8e-58 (weaker than embedding-based metrics)
- Species with broader ecological niches require more complete metabolic toolkits

**H3: Pangenome openness → niche breadth** (r=0.324, p=5.6e-47)
- Moderate positive correlation
- Open pangenomes correlate with broader ecological niches
- Core fraction shows strong NEGATIVE correlation with niche breadth: r=-0.445, p=1.4e-91
- Pangenome flexibility enables adaptation to diverse environments

**Key insight**: AlphaEarth embedding diversity is a better predictor of metabolic completeness than geography alone. The embeddings capture ecological context (soil vs marine vs clinical), not just geographic distance. This explains why embedding variance (r=0.412) outperforms geographic range (r=0.360) in predicting pathway completeness.

**Data coverage limitation**: Only 6.8% of species (1,872/27,690) have sufficient AlphaEarth coverage (≥5 genomes with embeddings). This is due to missing lat/lon metadata for most NCBI genomes, especially clinical isolates.

### [functional_dark_matter] 55.9% of dark gene ortholog groups are kingdom-level — present across multiple phyla

Full pangenome analysis (27,690 species, NB11b) reveals that over half of functionally dark gene OGs are pan-bacterial, present in thousands of species across multiple phyla. Species counts range from 1 to 27,482 (median 135). This demonstrates that functional dark matter is not a minor annotation gap but a fundamental limitation in understanding broadly conserved biology. The top-ranked unknowns (COG0468, COG0443, COG0491) are present in virtually all sequenced bacterial genomes yet have zero functional evidence.

### [functional_dark_matter] Only 7.5% of dark genes are truly unknown — most have converging evidence

The darkness spectrum classification across 57,011 dark genes shows T1 Void (zero evidence) is only 4,273 genes (7.5%). The majority — T4 Penumbra (22,500, 39.5%) — have 3-4 converging lines of evidence (fitness phenotype, domain annotation, ortholog group, module membership). The "dark matter problem" is not monolithic: most genes have substantial clues, and the key bottleneck is targeted experimental validation, not computational inference.

### [functional_dark_matter] Lab fitness phenotypes predict environmental distribution at 61.7% concordance

Across 47 testable dark gene clusters, 29 (61.7%) show directional concordance between lab fitness condition and carrier genome environment (Fisher's combined p=0.031). NMDC independent validation confirmed all 4 pre-registered abiotic predictions (nitrogen~nitrogen, pH~pH, anaerobic~dissolved_oxygen) and all 7 pre-registered trait predictions. This provides the first systematic evidence that Fitness Browser lab phenotypes reflect real ecological function, validating fitness data as a proxy for in situ importance.

### [functional_dark_matter] Cross-organism concordance confirms dark genes behave like real functional genes

65 dark gene ortholog groups show conserved fitness effects across 3+ organisms. Dark gene concordance levels are statistically indistinguishable from annotated genes (Mann-Whitney p=0.17). Motility-related dark genes show the strongest cross-organism concordance, suggesting conserved but incompletely annotated chemotaxis machinery.

### [functional_dark_matter] MR-1 is the single highest-value organism for dark gene characterization

Shewanella MR-1 contributes 25/100 top fitness-active candidates, 587 scored dark genes total, and covers 20.8% of the top-500 in just 3 experiments (stress, nitrogen, carbon). This reflects deep condition coverage (121 conditions), a large dark gene complement, and high fitness effect magnitudes (142 genes with |fit| >= 4). For conservation-weighted prioritization (Route B), S. meliloti ranks first (1,630 OGs, 195 kingdom-level gaps) due to its broader coverage of conserved unknowns.

### [functional_dark_matter] Dual-route covering sets share 39/42 organisms but differ in ordering

Evidence-weighted (Route A, NB09) and conservation-weighted (Route B, NB11) covering sets both select 42 organisms covering ~95% of priority, sharing 39 organisms. Route A puts MR-1 first (deep condition evidence); Route B puts S. meliloti first (most kingdom-level gaps). The complementarity enables both targeted hypothesis testing (Route A) and novel function discovery (Route B) from largely the same organism set.

### [functional_dark_matter] Extended covering set spans 6 phyla but Bacillota OGs are subsets of Pseudomonadota coverage

Adding 25 non-FB organisms (Bacillota, Actinomycetota, Campylobacterota) to the covering set candidate pool selects 50 organisms spanning 6 phyla (vs 4 for FB-only). P. aeruginosa PAO1 ranks #1 (3,713 OGs) and M. tuberculosis reaches #6 (first Actinomycetota). However, Bacillota organisms (B. subtilis, S. aureus) are NOT selected because their kingdom-level OGs are already covered by Pseudomonadota selections. They remain valuable for studying genes in native Gram-positive context, but don't contribute unique OG coverage.

### [pseudomonas_carbon_ecology] Host-associated Pseudomonas show dramatic loss of plant-derived sugar pathways

Analysis of 433 *Pseudomonas* species (12,732 genomes) using GapMind carbon pathway predictions reveals that the *P. aeruginosa* group has near-complete loss of plant-derived sugar catabolism compared to the *P. fluorescens/putida* group. 43 of 62 pathways differ significantly (FDR < 0.05), with the largest effects in xylose (+74 pp), ribose (+64 pp), arabinose (+63 pp), galacturonate (+60 pp), and myo-inositol (+59 pp). Amino acid catabolism remains near-universal (>99.5%) in both groups, consistent with Palmer et al. (2007) showing CF sputum is amino acid-dominated.

Among free-living species, carbon profiles are significantly associated with isolation environment (PERMANOVA p = 0.006), but predictive accuracy is modest (RF balanced accuracy 0.41 vs 0.25 chance). D-serine, arabinose, rhamnose, and fucose are the most discriminating pathways.

---

## 2026-02

### [pathway_capability_dependency] Pathway completeness ≠ metabolic dependency

Four-category classification of 7 FB organisms × 23 GapMind pathways reveals:
- 35.4% Active Dependencies (complete + fitness-important)
- 41.0% Latent Capabilities (complete but fitness-neutral in rich media)
- 14.9% Incomplete but Important
- 8.7% Missing

Key insight: ALL Latent Capabilities become fitness-important under condition-specific analysis (nitrogen limitation, stress, carbon source shifts). This validates the core_gene_tradeoffs finding that lab fitness underestimates natural selection on metabolic genes.

### [pathway_capability_dependency] Variable pathways strongly predict pangenome openness

Pan-bacterial analysis (2,810 species, ≥10 genomes each):
- Spearman(variable pathways, openness): rho=0.327, p=7.2e-71
- Partial Spearman controlling for genome count: rho=0.530, p=2.83e-203
- Signal holds across 18/21 phylogenetic groups tested
- Amino acid biosynthesis pathways (leu, val, arg, lys, thr) show largest accessory dependence gap (~0.14)

This is much stronger than the pangenome_openness project's null result for environmental/phylogenetic predictors of openness. Metabolic pathway variability is a genuine predictor.

### [pathway_capability_dependency] FB-native KEGG annotations bypass pangenome link table

The Fitness Browser's own KEGG tables (`besthitkegg` + `keggmember` + `kgroupec`) provide direct gene-to-KEGG KO-to-EC-to-pathway mapping for all 48 FB organisms. This is much simpler than the DIAMOND blastp pipeline used by conservation_vs_fitness to build a link table, and covers more organisms. The chain: besthitkegg → keggmember → kgroupec → keggconf → GapMind pathway.

### [pathway_capability_dependency] Metabolic ecotypes: median 4 per species

Hierarchical clustering of 225 species (≥50 genomes, ≥3 variable pathways) by GapMind pathway profiles:
- Median 4 metabolic ecotypes per species, max 8
- More ecotypes correlate with pangenome openness (partial rho=0.322, p=8.0e-07)
- Top ecotyped species: *Alistipes onderdonkii* (8), *Barnesiella intestinihominis* (8)

### [counter_ion_effects] Counter ions in metal salts are NOT the primary confound in RB-TnSeq metal fitness data

39.8% of metal-important genes are also NaCl-important across 19 organisms and 14 metals, but this overlap reflects shared stress biology (cell envelope, ion homeostasis, DNA repair) rather than chloride counter ion contamination. The definitive evidence: zinc sulfate (0 mM Cl⁻) shows 44.6% NaCl overlap and the highest DvH profile correlation (r=0.715) — higher than most chloride-delivered metals.

### [counter_ion_effects] Metal Fitness Atlas core enrichment is robust to shared-stress correction

After removing the ~40% of metal-important genes that overlap with NaCl stress, the core genome enrichment persists for 12 of 14 metals. Essential metals (Mo, W, Se, Hg) actually show stronger enrichment after correction (e.g., Mo delta +0.132 → +0.145). The original atlas conclusion (OR=2.08) is not an artifact.

### [counter_ion_effects] DvH metal-NaCl correlation hierarchy reveals a general-to-specific toxicity gradient

Whole-genome fitness correlation with NaCl: Zn (r=0.72) > Mn (0.55) > Cu (0.53) > Co (0.50) > Hg (0.48) > Ni (0.45) > Al (0.42) > Mo (0.40) > U (0.35) > Se (0.34) > Cr (0.32) > W (0.30) > Fe (0.09). Metals that broadly displace cofactors share more genes with ionic stress; metals targeting specific pathways (Mo/W for molybdopterin, Fe for iron-sulfur clusters) are distinct from general stress.

### [counter_ion_effects] SynE is an outlier in NaCl overlap due to dose-response experiment design

*Synechococcus elongatus* has 12 NaCl dose-response experiments (0.5–250 mM), far more than any other organism (1–6). This makes the `n_sick >= 1` threshold much easier to satisfy, producing an 88.6% shared-stress rate. Excluding SynE, overall overlap drops from 39.8% to 36.7%. Analyses using NaCl fitness data should account for experiment count when setting importance thresholds.

### [fw300_metabolic_consistency] Tryptophan overflow: converging evidence from four databases

FW300-N2E3 produces tryptophan (WoM: Increased), has 231 genes with significant fitness when grown on tryptophan (FB), has a complete tryptophan biosynthesis pathway (GapMind), yet 0/52 *P. fluorescens* strains in BacDive can utilize tryptophan as a carbon source. This convergence of four independent lines of evidence makes a compelling case for tryptophan overflow metabolism serving a cross-feeding or signaling function rather than a catabolic one. The finding is consistent with Fritts et al. (2021) and Ramoneda et al. (2023) who showed amino acid cross-feeding is widespread in soil communities and tryptophan auxotrophy is particularly common.

### [fw300_metabolic_consistency] GapMind 13/13 perfect concordance with experimental data

All 13 WoM-produced metabolites that could be mapped to GapMind pathways had "complete" pathway predictions, and all 13 also showed growth in FB experiments. This perfect agreement validates GapMind's accuracy for *Pseudomonas fluorescens* FW300-N2E3, consistent with Price et al. (2022, 2024). The matched metabolites are common amino acids and organic acids with well-characterized pathways.

### [fw300_metabolic_consistency] 94% concordance is structurally driven — BacDive is the only informative component

The 94% mean concordance across four databases decomposes into: FB 21/21 = 100% (structural), GapMind 13/13 = 100% (structural), BacDive 3/7 = 43% (informative). Overall 37/41 comparisons are concordant (90.2%). A binomial test comparing BacDive utilization of WoM-produced metabolites (43%) against the species baseline (27.5%) shows no significant difference (p=0.40). The high concordance is largely inevitable given that FB always shows growth for metabolites used as sole C/N sources, and GapMind predicts complete pathways for common amino acids.

### [fw300_metabolic_consistency] Pleiotropic fitness genes are amino acid biosynthesis housekeeping, not substrate-specific

The top 18 genes significant across all 21 FB metabolite conditions are amino acid biosynthesis enzymes: homoserine O-acetyltransferase (methionine), ATP phosphoribosyltransferase (histidine), dihydroxy-acid dehydratase (branched-chain), isopropylmalate dehydrogenase (leucine), shikimate dehydrogenase (aromatic), imidazoleglycerol-phosphate dehydratase (histidine). These are essential for growth on *any* minimal medium. The ~370 genes significant in only 1-2 conditions are the truly substrate-specific ones. This distinction is critical for interpreting WoM↔FB integration.

## 2026-02

### [metal_specificity] 55% of metal-important genes are genuinely metal-specific

Of 7,609 metal-important gene records across 24 organisms, 4,177 (55%) are sick under metal stress but have a <5% sick rate across 5,945 non-metal experiments (antibiotics, osmotic, carbon sources, etc.). The remaining 38% are "general sick" (important across many conditions) and 7% are "metal+stress" (shared with other stresses). This demonstrates that the Metal Fitness Atlas's metal-important gene set is not dominated by general stress response — the majority are genuine metal tolerance determinants.

### [metal_specificity] Metal-specific genes are core-enriched but less so than general stress genes (CMH p=0.011)

Metal-specific genes are 84.8% core (pooled) vs 90.2% for general sick genes — a statistically significant difference (Cochran-Mantel-Haenszel p=0.011). Both categories are enriched above the 79.8% baseline. This partially supports the Metal Atlas's two-tier model: general stress response (Tier 1) is more core than specialized metal resistance (Tier 2), but both are predominantly core. The accessory genome contributes only modestly to metal resistance machinery.

### [metal_specificity] UCP030820, YebC, and DUF1043 are the most metal-specific novel candidates

Among the top novel candidates from the Metal Atlas, three stand out as metal-specific rather than pleiotropic: UCP030820/OG01015 (67% metal-specific, oxidoreductase, 7 metals), YebC/OG01383 (58%, transcriptional regulator/translation factor, 6 metals, 11 organisms), and DUF1043-YhcB/OG03264 (50%, cell division protein, 5 metals). In contrast, YfdZ (15%) and the Mla/Yrb system (0-25%) are pleiotropic — important for many conditions, not just metals. DUF39 (0%, sick rate 0.64) is a general fitness factor despite spanning 8 metals.

### [metal_specificity] YebC metal-specificity may link to proline-rich metal transporter translation

YebC was recently shown to be a translation factor for proline-rich proteins (Ignatov et al. 2025). Many metal homeostasis proteins (P-type ATPases CopA/ZntA, CDF transporters) contain proline-rich cytoplasmic loops. Hypothesis: YebC is specifically needed under metal stress because upregulation of proline-rich metal transporters creates a translation bottleneck that YebC resolves. Under non-metal conditions these transporters are not highly expressed and YebC is dispensable.

### [metal_specificity] Essential metals show high metal-specificity when DvH is properly included

Initial analysis showed 0% metal-specificity for essential metals (Mo, W, Se, Mn), seemingly due to DvH's 608 non-metal experiments making specificity impossible. After fixing a locusId type mismatch that had silently excluded DvH, essential metals show 47-61% metal-specificity: Manganese (61%), Molybdenum (61%), Tungsten (57%), Selenium (46%). The experiment-count bias is real but less severe than initially thought.

### [bacdive_metal_validation] Metal tolerance scores predict isolation from metal-contaminated environments (d=+1.0, p=0.006)

Bacteria isolated from heavy metal contamination sites have metal tolerance scores a full standard deviation above the environmental baseline (Cohen's d = +1.00, Mann-Whitney p=0.006, n=10). The effect is dose-dependent: heavy metal (+1.00) > waste/sludge (+0.57) > all contamination (+0.43) > industrial (+0.20). This validates the Metal Fitness Atlas's genome-based prediction method against real-world isolation ecology. The signal holds within Pseudomonadota and Actinomycetota after phylogenetic stratification.

### [bacdive_metal_validation] 43% of BacDive strains link to pangenome species via name matching

Species name matching (exact + GTDB suffix removal) links 42,227 BacDive strains (43.4% of 97K) to 6,426 GTDB pangenome species. The bridge enables cross-referencing BacDive phenotypic data with pangenome-derived predictions without Spark queries. The 56.6% unmatched strains reflect GTDB's different species boundaries from LPSN/DSMZ taxonomy.

### [bacdive_metal_validation] Host-associated bacteria score higher than environmental (contradicts expectation)

Host-associated bacteria (n=12,086) have slightly but significantly higher metal tolerance scores than environmental bacteria (d=+0.14, p<0.0001). This contradicts the expectation that host niches have lower metal exposure. The likely explanation is genome size confounding: BacDive host-associated strains are dominated by Pseudomonadota pathogens with large genomes and correspondingly more KEGG-annotated gene clusters, inflating the normalized metal score.

## 2026-03

### [snipe_defense_system] SNIPE antiphage defense found in 1,696 species across 33 phyla

Survey of DUF4041 (PF13250) in the 293K-genome BERDL pangenome found 4,572 gene clusters across 1,696 species and 33 phyla — far exceeding the >500 homologues reported in Saxton et al. 2026 (*Nature*). 86.7% are accessory or singleton genes, consistent with mobile defense island carriage. The patchy distribution across many phyla and families supports horizontal gene transfer.

### [snipe_defense_system] SNIPE nuclease is PF13455 (Mug113), not PF01541 (canonical GIY-YIG)

The SNIPE nuclease domain belongs to Pfam family PF13455 (Mug113), not PF01541 (canonical GIY-YIG restriction enzymes/DNA repair). Both are in the GIY-YIG clan (CL0418) but are distinct families. This explains why zero gene clusters show DUF4041 + PF01541 co-occurrence — it's biological truth, not an annotation artifact. The paper describes the nuclease as "GIY-YIG" at the superfamily level, but never cites Pfam accessions. Verified via InterPro/UniProt analysis of the *E. coli* SNIPE protein (A0A0A1A5Z2: PF13250 at positions 232–333, PF13455 at positions 443–520).

### [snipe_defense_system] PhageFoundry strain_modelling contains Gaborieau et al. 2024 phage-host interaction data

The `phagefoundry_strain_modelling` database (separate from the GenomeDepot annotation browsers) contains experimental data from Gaborieau et al. 2024 (*Nature Microbiology*): 188 *E. coli* strains × 96 phages = 17,672 binary infection outcomes, plus an ML model (AUC=0.883) with SHAP importances for 1,582 gene cluster features. Lambdavirus 411_P1 (phage lambda) infects only 1/188 strains (0.5%), vs. 43.4% for Myoviridae — consistent with widespread ManYZ receptor loss making lambda-mediated infection rare.

### [snipe_defense_system] ManXYZ is a mannose/glucosamine transporter, NOT a fructose transporter

Fitness Browser data (168 experiments, *E. coli* K-12 Keio collection) shows ManXYZ knockouts have severe fitness defects on D-mannose (fit = -3.93) and D-glucosamine (fit = -2.75) but are dispensable for D-fructose (fit = +0.18 to +0.66). This contradicts the UniProt annotation "fructose import across plasma membrane" (GO:0005354) for ManX. The mannose/glucosamine specificity is critical for understanding why SNIPE targets the ManYZ pore — it's the mannose transporter that phage lambda exploits for DNA injection, not a general sugar transporter.

### [snipe_defense_system] Methanococcus maripaludis JJ has a full two-domain SNIPE protein with fitness data

The Fitness Browser contains one archaeal SNIPE protein in *Methanococcus maripaludis* JJ (locus MMJJ_RS01635), annotated with both PF13250 (DUF4041) and PF13455 (Mug113/GIY-YIG nuclease), plus PF10544 (DUF2525). This is a full two-domain SNIPE protein with 129 experiments of fitness data — the first SNIPE homologue with genome-wide knockout phenotypes available for analysis.

### [snipe_defense_system] SNIPE detected in Klebsiella with ManYZ co-occurrence

PhageFoundry Klebsiella genome browser contains 1 DUF4041 annotation (3 proteins at 558 aa — same length as *E. coli* SNIPE) and 4,619 PTS_EIIC (PF02378/ManY family) annotations. Klebsiella is the only PhageFoundry species with both SNIPE and the ManX-family PTS domain (PF00358). This is clinically relevant — SNIPE could affect phage therapy efficacy in this key pathogen.

## Template

### [webofmicrobes_explorer] WoM action 'E' encodes de novo metabolite production, distinct from 'I' (increased)

The Web of Microbes database uses a 4-action encoding system. For organisms, 'E' (Emerged) means the metabolite was absent from the control medium and now detected — genuine de novo biosynthesis. 'I' (Increased) means the metabolite was present in the control and its level went up. E and I are mutually exclusive (0 overlap across 10,744 observations). For the control ("The Environment"), 'D' means Detected in medium and 'N' means Not detected. Critically, there is NO "Decreased" (consumption) action for any organism in the 2018 WoM snapshot — all 742 'D' observations belong to the control. This means the database records only production, not consumption.

### [webofmicrobes_explorer] WoM ENIGMA isolates have direct Fitness Browser strain matches

Two WoM organisms are exact strain matches to FB organisms: Pseudomonas sp. FW300-N2E3 = `pseudo3_N2E3` (5,854 genes, 211 experiments) and Pseudomonas sp. GW456-L13 = `pseudo13_GW456_L13` (5,243 genes, 106 experiments). E. coli BW25113 = `Keio` is also the same strain. These enable direct metabolite-to-gene-fitness linking. The FB conditions for these organisms include carbon source experiments (L-alanine, L-proline, sodium D-lactate, etc.) that test the same metabolites WoM detects as produced — 109 metabolite-condition name overlaps.

### [webofmicrobes_explorer] 68.5% of identified WoM metabolites link to ModelSEED molecules

Of 257 identified (non-unknown) WoM compounds, 69 match ModelSEED molecules by exact name and 107 by formula, totaling 176 (68.5%). This enables reaction-level annotation for the majority of WoM metabolites.

```markdown
### [project_name] Brief title

Description of what was discovered, why it matters, and any implications
for future analyses.
```

## 2026-03

### [cf_formulation_design] Metabolic overlap explains 27% of PA14 inhibition in planktonic culture

Across 142 CF airway isolates, metabolic overlap with PA14's amino acid preferences (proline, histidine, ornithine, glutamate, aspartate) predicts planktonic inhibition (r=0.384, p=2.3e-6, R²=27.4%). However, the strongest FDA-safe inhibitors (S. salivarius, N. mucosa, G. sanguinis) show 57-74% more inhibition than metabolic overlap predicts, indicating dual-mechanism (metabolic + direct antagonism) organisms are the best formulation candidates.

### [cf_formulation_design] PA14 outgrows all commensals on every tested amino acid — no simple prebiotic exists

PA14 is a metabolic generalist: it outgrows the average commensal on all 20 tested amino acids plus glucose and lactate (selectivity ratio <1.0 for all). Competitive exclusion requires community-level niche coverage (3+ organisms), not individual superiority.

### [cf_formulation_design] Sugar alcohols are genomically predicted prebiotics for CF protective microbiomes

GapMind pathway comparison reveals 6 carbon sources where formulation commensals have 100% pathway completeness but PA14 has 0%: xylitol, myoinositol, xylose, arabinose, fucose, rhamnose. These are FDA-GRAS and xylitol is already used in CF airway products. Patient metatranscriptomics confirms commensal-specific PTS sugar transport expression in vivo.

### [cf_formulation_design] Rothia dentocariosa and Neisseria mucosa are naturally lung-adapted

In the BERDL pangenome, 38% of R. dentocariosa genomes and 33% of N. mucosa genomes are from respiratory sources — disproportionately lung-associated compared to other formulation species. These two anchor the FDA-safe formulation (highest inhibition + highest engraftability + lung tropism).
### [bacdive_phenotype_metal_tolerance] BacDive phenotypes are phylogenetic proxies for metal tolerance

Classical microbiology phenotypes (Gram stain, oxygen tolerance, enzyme activities) from BacDive capture real metal tolerance signal (R²=0.16 alone, 7/10 significant after FDR) but are entirely phylogenetically confounded — adding phenotype features to a taxonomy-based model provides zero improvement (delta R²=-0.009). The genome's metal resistance gene count is the true predictor (full model R²=0.63). Urease-positive bacteria surprisingly have *lower* metal tolerance (d=-0.18), driven by Actinomycetes lineage composition. This validates genome-based prediction (Metal Fitness Atlas) over phenotype-based screening for metal tolerance assessment.

### [pgp_pangenome_ecology] pqqC–acdS is a vertically inherited, soil-enriched rhizosphere module

Across 27K GTDB species, pqqC (phosphate solubilization) and acdS (ACC deaminase) co-occur at OR = 7.24 — far stronger than any other PGP gene pair — and are both strongly enriched in soil/rhizosphere environments (acdS OR = 7.0, pqqC OR = 2.9). Counterintuitively, all 13 PGP genes are predominantly **core** (29.7% mean accessory vs 53.2% genome-wide), rejecting the HGT hypothesis and indicating vertical inheritance. Nitrogen fixation (nifH) forms a separate ecological guild: negatively associated with pqqC and hcnC, and depleted in soil relative to aquatic environments. The trp→ipdC coupling (OR = 2.81) holds in non-soil species but reverses in soil species, likely because soil PGPB acquire tryptophan exogenously from root exudates.

### [pgp_pangenome_ecology] nbconvert crashes Spark kernels — use CSV caching in notebooks

Running `jupyter nbconvert --execute` on notebooks that call `spark.sql(...).toPandas()` on large result sets causes the kernel to die (DeadKernelError). Workaround: add cache-check logic to Spark cells (`if os.path.exists(path): load CSV else run Spark`) so nbconvert can execute the notebook locally from cached CSVs after the initial JupyterHub run. The live Spark outputs should be captured interactively on JupyterHub, not via nbconvert.
