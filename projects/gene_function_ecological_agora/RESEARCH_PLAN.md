# Research Plan: Gene Function Ecological Agora

*Innovation Atlas Across the Bacterial Tree*

## Research Question

Across the prokaryotic tree (GTDB r214; 293,059 genomes / 27,690 species), do clades specialize in the *kind* of functional innovation they produce, and is the producer/consumer asymmetry observed by Alm, Huang & Arkin (2006) for two-component systems a general feature of regulatory function classes but not metabolic ones?

## Hypothesis

- **H0**: Clades do not specialize in functional innovation type. Producer and consumer scores are tightly correlated across function classes (the producer/consumer plane collapses to a diagonal), and function class category (regulatory vs metabolic) is not a significant predictor of quadrant occupancy.
- **H1**: Clades specialize. The four-quadrant structure (Closed Innovator / Broker / Sink / Open Innovator) is real and discriminable, with regulatory function classes more often populating the Open Innovator quadrant per Alm 2006, and metabolic function classes distributing across all four quadrants depending on system-specific physical, ecological, or biochemical constraints.

The fallback (diagonal) form is itself a finding — *that* prokaryote innovation is correlated in/out at clade level even when category is not predictive — and is a publishable Phase-1 outcome.

## Literature Context

- **Alm, Huang & Arkin 2006** (PLOS CB 2(11):e143) — original producer/consumer asymmetry on TCS HKs across 207 genomes. The mandatory back-test target.
- **Treangen & Rocha 2011** (PLOS Gen 7(1):e1001284) — HGT, not duplication, drives prokaryotic family expansion. Reframes paralog count as HGT signal at long timescales.
- **Smillie et al. 2011** (Nature 480:241) — ecology drives gene-exchange networks. Documents Bacteroidota → Firmicutes CAZyme transfer in the human gut; informs Phase 1 pre-registered prediction.
- **Puigbò, Wolf & Koonin 2009, 2010** (J Biol 8:59; GBE 2:745) — tree and net components of prokaryote evolution. Foundational atlas-style framing.
- **Popa et al. 2011** (Genome Res 21:599) — directed networks for HGT inference; informs the directed clade-to-clade flow graph deliverable.
- **Coleman et al. 2021** (Science 372:eabe0511) — rooted phylogeny resolves early bacterial evolution; informs deep-rank validation choices.
- **Szöllősi et al. 2013** (Syst Biol 62:386, 901) — gene tree-species tree reconciliation, applied here only on principled subsamples (constraint).
- **Morel et al. 2024** (Bioinformatics 40:btae162) — AleRax for DTL reconciliation. Available as a last-resort sub-sample tool, not at full GTDB scale.
- **Metcalf et al. 2014** (eLife 3:e04266) — antibacterial-gene transfer across the tree of life. Informs validation framing for pure-import systems as secondary controls only.

## Approach: Three-Phase Multi-Resolution Atlas, Forced Order

The plan tests the central question at three resolutions, in a forced order. Each phase's output gates and refines the next; the final atlas is the cross-resolution synthesis.

### Through-Line Logical Argument

1. **Existence before resolution**. The atlas claim only matters if the four-quadrant structure is real and not an artifact of EggNOG annotation density. The lowest-bias resolution at which existence can be tested is sequence-only (UniRef50). Phase 1 must come first.
2. **Sequence existence does not answer the headline**. The regulatory-vs-metabolic question is functional, and UniRef50 has no functional grain. KO is the natural functional resolution. But KO results inherit the annotation-density bias Phase 1 was designed to bypass; therefore Phase 1's UniRef50→KO projection table tells Phase 2 which KOs are *sequence-anchored* (run as primary) vs *annotation-driven only* (run as rail).
3. **Alm 2006 is at architectural resolution, and architecture is expensive**. Phfam multidomain architecture is the resolution where Alm 2006's HK paralog finding lives. Architecture-level scoring is ~2× the cost of KO-level. Therefore Phase 3's targets are inherited from Phase 2: the KOs where Phase 2 finds a strong quadrant signal AND multiple architectures co-exist.
4. **Cross-resolution synthesis is the deliverable**, not an epilogue. Concordance across three resolutions is the strongest atlas claim; conflict is the most informative failure mode.

### Each Phase Is a Stop-Point

Each phase produces a publishable artifact. Phase 1 alone, if structure is absent, is a publishable negative result with a clean methodological contribution. Phase 1+2 alone, if Phase 3 turns out to be unaffordable, is a publishable functional atlas. The full sequence is the most ambitious version.

---

## Phase 1 — Existence Test (UniRef50, sequence-only)

**Question**: Does the four-quadrant pattern exist when annotation-density bias is stripped out? Does the regulatory-vs-metabolic prior already fail at the sequence level via a documented metabolic-system test case?

### Substrate
- **A. Function-class unit**: UniRef50 cluster (sequence-only)
- **B1. Within-clade family unit**: UniRef90 cluster nested in UniRef50; paralog count = distinct UniRef90s within UniRef50 within clade above tree-aware null
- **B2. Cross-clade orthology**: UniRef90 co-membership
- **C. Direction inference**: Fully direction-agnostic; per-clade × UniRef50 acquisition signal only

### Bias Control Stack
- D1: One genome per species (GTDB representative)
- D2: Per-genome annotated-fraction regressed out as nuisance covariate
- D3: Per-clade effective N reported alongside every score
- D4: GTDB rank-level topology-support filter (rank used as depth scaffold)
- **KO-projection rail** (in lieu of UniRef50 self-rail): post-hoc map UniRef50 → dominant KO via majority vote, rerun headline test with KO labels as commentary check
- Sensitivity: per-clade rarefaction; jackknife on clade members

### Pre-registered Prediction (Phase 1)

**Bacteroidota → Open Innovator quadrant for PUL (polysaccharide-utilization-locus) UniRef50 clusters**, defined as UniRef50 clusters whose dominant Pfam projection is in the CAZy GH/CBM family set.

**Prior strength**: WEAK. (See Prior Calibration below.)

**Reasoning**: Smillie et al. 2011 documented elevated Bacteroidota → Firmicutes CAZyme HGT in the human gut. Bacteroidota are described as CAZyme-paralog innovators. Both ingredients (high producer + high outflow) point to Open Innovator.

**Falsification**: Bacteroidota producer score on PUL UniRef50s falls below the atlas median (not Open Innovator), OR Firmicutes acquisition signal for Bacteroidota-resident PUL UniRef50s is not significantly above signal from non-Bacteroidota donors at q<0.05.

**Prior Calibration** (alternatives we cannot rule out):
- *Broker*: low producer + high outflow, if Bacteroidota CAZyme expansion is HGT-driven inwards rather than de novo paralog-driven.
- *Closed Innovator*: high producer + low outflow, if the Smillie 2011 outflow signal is restricted to gut-resident Bacteroidota and the broader phylum (rumen, soil, marine) does not export.
- *On-diagonal*: no specialization detectable above null.

**What we genuinely don't know**: Whether "PUL UniRef50 cluster" is a coherent enough function unit for a quadrant verdict, vs collapsing into noise from heterogeneous CAZy families. The Phase 1 rarefaction will tell us.

### Phase 1 Output Products (Phase 2 handoff)
- `data/p1_uniref50_atlas.parquet` — clade × UniRef50 producer/consumer scores with confidence intervals
- `data/p1_uniref50_quadrants.tsv` — quadrant assignment per clade × UniRef50 (Closed / Broker / Sink / Open / on-diagonal)
- `data/p1_uniref50_to_ko_projection.tsv` — UniRef50 → dominant KO mapping with concordance score (the Phase-2 input)
- `data/p1_bacteroidota_pul_test.tsv` — pre-registered hypothesis verdict
- `data/p1_null_model_diagnostics.parquet` — rarefaction curves, effective N, D2 residualization diagnostics

### Phase 1 Gate to Phase 2
- **Pass strong-form**: ≥30% of UniRef50s show non-trivial quadrant structure (off-diagonal at q<0.05) AND Bacteroidota PUL = Open Innovator → Phase 2 proceeds with strong-form regulatory-vs-metabolic test (the prior holds in part).
- **Pass reframed**: structure exists AND Bacteroidota PUL is **not** Open Innovator → Phase 2 reframes to test "*which* metabolic classes share the regulatory pattern, and what predicts which?" The strong-form prior collapses; the question becomes empirical.
- **Stop**: structure not detected → fall back to the diagonal claim, document as Phase-1 negative result, halt the atlas project. Phase 2 and Phase 3 do not run.

### Phase 1 Notebooks
1. `01_p1_data_extraction.ipynb` — extract gene_cluster → UniRef50 / UniRef90 mapping from `bakta_db_xrefs`, GTDB taxonomy, dedup to species reps, per-genome annotation density
2. `02_p1_null_model_construction.ipynb` — build tree-aware null for paralog expansion and acquisition; rarefaction curves; D2 residualization
3. `03_p1_uniref50_atlas.ipynb` — compute clade × UniRef50 producer/consumer scores; quadrant assignment
4. `04_p1_bacteroidota_pul_test.ipynb` — pre-registered hypothesis verdict + KO-projection rail check
5. `05_p1_phase_gate.ipynb` — Gate decision summary for Phase 2

### Phase 1 Effort
~4 agent-weeks.

---

## Phase 2 — Functional Resolution (KO, paralog-explicit)

**Question**: Does the four-quadrant pattern map onto KO-defined functional categories the way the regulatory-vs-metabolic prior predicts? Does the Alm 2006 TCS back-test reproduce at KO level on the GTDB substrate?

### Substrate
- **A. Function-class unit**: KO from `eggnog_mapper_annotations.kegg_ko`
- **B1. Within-clade family unit**: UniRef90 cluster within KO; paralog count = distinct UniRef90s per KO per clade
- **B2. Cross-clade orthology**: UniRef90 co-membership
- **C. Direction inference**: Acquisition-only at family rank and above; composition-based donor flag (codon usage Δ, GC% Δ vs clade norm) at genus rank as advisory only — *direction is not inferable at deep ranks given the constraint that no full DTL recon runs at GTDB scale*

### Bias Control Stack
- D1–D4 mandatory
- **UniRef50 sanity rail** (mandatory): every KO-headline result rerun with UniRef50 cluster identity collapsed in place of KO, using Phase 1's projection table
- Sensitivity: rank-by-rank stability check (does the headline hold at family rank vs class rank?); UniRef90/UniRef50 cross-validation on headline KOs

### Phase 1 Handoff Use
- `p1_uniref50_to_ko_projection.tsv` defines the **sequence-anchored KO subset**: KOs where ≥80% of mapped UniRef50 clusters concur on KO assignment. Headline regulatory-vs-metabolic test runs on this subset (primary). Full KO set runs as rail (secondary).
- KO quadrants computed in Phase 2 are compared against KO-projected-from-UniRef50 quadrants from Phase 1. Concordance ≥75% across sequence-anchored KOs is a soft sanity threshold.

### Pre-registered Prediction (Phase 2)

**Mycobacteriota → Closed Innovator quadrant for the mycolic-acid pathway KO set** (KEGG ko00540 + FAS-II + mycolyl transferase KOs).

**Prior strength**: WEAK-TO-MODERATE.

**Reasoning**: Mycolic-acid biosynthesis is a cell-envelope-coupled autocatalytic process whose intermediates require host enzymatic context for incorporation. The pathway is a defining trait of the *Corynebacteriales* sensu lato, and there is no documented case of a non-mycolic-acid lineage acquiring functional mycolic-acid biosynthesis. This points to high lineage-specific paralog expansion + low outflow.

**Falsification**: >5% of mycolyl-transferase UniRef90 clusters in the atlas have presence in non-Mycobacteriota clades at frequencies above the tree-aware null at q<0.05, OR the *M. tuberculosis* lineage's producer score is below the median of all Mycobacteriota for these KOs.

**Prior Calibration** (alternatives we cannot rule out):
- *Sink*: low producer + high inflow, if the Mycobacteriota mycolic-acid pathway is largely inherited unchanged from a *Corynebacteriales* common ancestor with no recent paralog expansion (cell-envelope already mature).
- *On-diagonal*: pathway evolves at the same rate as the genome-wide null in this clade.

**What we genuinely don't know**: Whether "mycolic-acid pathway KO set" includes enough of the actual cell-envelope machinery to give a quadrant verdict that is biologically interpretable, or whether the KEGG pathway is too partial.

### Phase 2 Output Products (Phase 3 handoff)
- `data/p2_ko_atlas.parquet` — clade × KO producer/consumer scores
- `data/p2_ko_quadrants.tsv` — quadrant assignments
- `data/p2_regulatory_vs_metabolic_test.tsv` — pre-registered headline test on KO category labels
- `data/p2_mycolic_acid_test.tsv` — pre-registered hypothesis verdict
- `data/p2_alm_2006_backtest.tsv` — TCS HK reproduction at KO level
- `data/p2_architectural_deepdive_candidates.tsv` — KOs with strong quadrant signal AND ≥2 distinct Pfam architectures (the Phase-3 input)

### Phase 2 Gate to Phase 3
- **Pass**: regulatory-vs-metabolic asymmetry confirmed at KO level AND Alm 2006 back-test reproduces → Phase 3 architectural deep-dive proceeds as generalization confirmation.
- **Pass reframed**: regulatory-vs-metabolic asymmetry **falsified** at KO level → Phase 3 reframes to "what *does* discriminate Open vs Closed?" using the deep-dive candidates.
- **Stop**: Alm 2006 back-test fails at KO level (TCS does not reproduce the Open Innovator HK paralog pattern) → halt; methodological failure to be diagnosed before any architectural analysis.

### Phase 2 Notebooks
6. `06_p2_ko_data_extraction.ipynb` — KO assignments from `eggnog_mapper_annotations`; UniRef90 nesting within KO
7. `07_p2_ko_atlas.ipynb` — clade × KO producer/consumer scores; quadrant assignment; sanity rail using Phase-1 projection
8. `08_p2_regulatory_vs_metabolic_test.ipynb` — headline test on KO category labels
9. `09_p2_mycolic_acid_test.ipynb` — pre-registered hypothesis verdict
10. `10_p2_alm_2006_backtest.ipynb` — TCS HK reproduction
11. `11_p2_phase_gate.ipynb` — gate decision + architectural deep-dive candidate selection

### Phase 2 Effort
~5 agent-weeks.

---

## Phase 3 — Architectural Resolution & Direction (Pfam architecture, hybrid direction)

**Question**: Does the four-quadrant structure survive at Pfam multidomain architecture resolution? Can Open Innovator be discriminated from Broker via genus-rank composition-based donor inference?

### Substrate
- **A. Function-class unit**: Pfam multidomain architecture (ordered set of Pfam domains)
- **B1. Within-clade family unit**: paralog-explicit; UniRef90 within architecture within clade
- **B2. Cross-clade orthology**: Pfam architecture identity (exact ordered match)
- **C. Direction inference**: Hybrid two-level. Phyletic-incongruence detects clade-pair acquisition events. Composition-based donor inference (codon usage Δ, dinucleotide signature) attempted **only for events called at genus rank**, with explicit confidence intervals. Genus-rank events are <10% of total; donor identity beyond genus is not reported.

### Bias Control Stack
- D1–D4 mandatory
- **Pfam-completeness audit** (mandatory pre-flight): for every architecture in the deep-dive candidate set, cross-check `bakta_pfam_domains` vs `eggnog_mapper_annotations.PFAM`. Flag discrepancies >20%. Recompute via HMMER on `gene_cluster.faa_sequence` for any flagged headline architecture. *Note: per docs/pitfalls.md [bakta_reannotation], 12/22 marker Pfams were silently missing from `bakta_pfam_domains` in a prior project; this audit is non-negotiable.*
- UniRef50 robustness rail
- Sensitivity: PIC on producer scores; per-clade jackknife on architecture census

### Phase 2 Handoff Use
- `p2_architectural_deepdive_candidates.tsv` defines the architecture census target. Phase 3 does not run a full GTDB-scale Pfam architecture census; it runs the deep-dive on the candidate KOs from Phase 2. This makes Phase 3 ~30–40% cheaper than a standalone architectural atlas.

### Pre-registered Prediction (Phase 3)

**Cyanobacteria → Broker quadrant for photosystem II Pfam architectures** (PF00124 + PF02530 + PF02533 set, plus extended PSII protein architectures).

**Prior strength**: WEAK.

**Reasoning**: PSII protein components are evolutionarily ancient and well-conserved within Cyanobacteria (low recent paralog expansion expected). The PSII assembly was donated to anoxygenic photosynthesis lineages (Chloroflexota) via documented ancient HGT. Both ingredients (low producer + high outflow) point to Broker rather than Open Innovator.

**Falsification**: Cyanobacteria producer score > 75th percentile of the atlas for PSII architectures (would shift to Open Innovator), OR Chloroflexota PSII architecture acquisition signal is not significantly above null at q<0.05.

**Prior Calibration** (alternatives we cannot rule out):
- *Open Innovator*: high producer + high outflow, if Cyanobacteria show meaningful recent PSII paralog expansion (e.g., psbA copy variation across Synechococcus / Prochlorococcus lineages) above the tree-aware null.
- *Closed Innovator*: high producer + low outflow, if the PSII outflow to Chloroflexota is older than our depth resolution and the recent HGT signal is dominated by within-Cyanobacteria diversification.
- *Sink*: highly unlikely given the established "PSII originated in Cyanobacteria" consensus, but listed for completeness.

**What we genuinely don't know**: Whether the Pfam-architecture grain captures PSII as a coherent unit (the assembly involves >20 distinct proteins; multiple architectures per PSII complex), and whether HMMER recompute will be needed for the headline Pfams.

### Phase 3 Output Products
- `data/p3_pfam_architecture_atlas.parquet` — clade × architecture producer/consumer scores on the candidate set
- `data/p3_pfam_architecture_quadrants.tsv` — quadrant assignments
- `data/p3_cyanobacteria_psii_test.tsv` — pre-registered hypothesis verdict
- `data/p3_genus_rank_donor_inference.tsv` — composition-based donor inference at genus rank with confidence intervals
- `data/p3_alm_2006_architectural_backtest.tsv` — full HK Pfam architecture census within the candidate set; comparison to Phase-2 KO-level back-test
- `data/p3_pfam_completeness_audit.tsv` — audit results, recompute decisions

### Phase 3 Gate to Phase 4
Unconditional. Synthesis runs on whatever Phase 3 produces, including failure outcomes. Failure is part of the atlas.

### Phase 3 Notebooks
12. `12_p3_pfam_completeness_audit.ipynb` — pre-flight audit of `bakta_pfam_domains` for headline architectures; HMMER recompute decision
13. `13_p3_architecture_atlas.ipynb` — clade × architecture producer/consumer scores on candidate set
14. `14_p3_cyanobacteria_psii_test.ipynb` — pre-registered hypothesis verdict
15. `15_p3_genus_rank_donor_inference.ipynb` — composition-based donor inference + confidence intervals
16. `16_p3_alm_2006_architectural_backtest.ipynb` — TCS HK reproduction at architecture level

### Phase 3 Effort
~5 agent-weeks (reduced from a standalone ~7–8 due to Phase-2 candidate targeting).

---

## Phase 4 — Cross-Resolution Synthesis

**Question**: At which resolutions and for which clades × function classes do the quadrant assignments concord? Where they conflict, what does the conflict reveal?

No new data extraction. Phase 4 joins Phase 1 / 2 / 3 outputs.

### Phase 4 Output Products
- `data/p4_cross_resolution_concordance.tsv` — for each (clade × function-class) tuple represented at multiple resolutions, list quadrant at each resolution + concordance score
- `data/p4_concordance_weighted_atlas.parquet` — final 4-quadrant heatmap and directed flow network with confidence weights from cross-resolution agreement
- `data/p4_conflict_analysis.tsv` — clade × function tuples where resolutions disagree, with hypotheses for why
- `figures/p4_atlas_heatmap.png` — final clade × function-class heatmap
- `figures/p4_function_flow_network.png` — directed clade-to-clade function-flow graph
- `figures/p4_four_quadrant_summary.png` — named clades populating each quadrant per Deliverable 4
- `data/p4_pre_registered_verdicts.tsv` — three pre-registered hypotheses (Phase 1: Bacteroidota PUL; Phase 2: Mycobacteriota mycolic-acid; Phase 3: Cyanobacteria PSII) as supported / falsified / equivocal with explicit evidence
- `REPORT.md` — final synthesis writeup

### Phase 4 Notebooks
17. `17_p4_cross_resolution_concordance.ipynb` — quadrant assignment join across phases
18. `18_p4_atlas_visualization.ipynb` — heatmap + directed network + four-quadrant summary
19. `19_p4_synthesis_writeup.ipynb` — pre-registered verdicts, conflict analysis, final figures

### Phase 4 Effort
~2 agent-weeks (synthesis writing, comparative analysis, figures).

---

## Data Sources

### BERDL tables (`kbase_ke_pangenome` unless noted)
- `genome` (293K rows) — genome → gtdb_species_clade_id, has_sample
- `gtdb_taxonomy_r214v1` (293K rows) — full lineage per genome
- `gtdb_metadata` (293K rows) — CheckM completeness, contamination, GC%, assembly level
- `gtdb_species_clade` (28K rows) — clade-level ANI stats
- `gene_genecluster_junction` (1B rows) — genome → gene_cluster_id (filter required, never full-scan)
- `gene_cluster` (133M rows) — cluster representatives, faa_sequence, fna_sequence, isCore/isAccessory/isSingleton flags
- `eggnog_mapper_annotations` (94M rows) — KO, COG, EC, KEGG, PFAM per cluster
- `bakta_db_xrefs` (572M rows) — gene_cluster_id → UniRef50/UniRef90/UniRef100 (filter required, disable autoBroadcast on `kbase_uniprot.uniprot_identifier` joins)
- `bakta_pfam_domains` (19M rows) — Pfam domains per gene_cluster_id (subject to completeness audit)
- `kbase_uniref50` (100K rows) — UniRef50 cluster table
- `kbase_uniref90` (100K rows) — UniRef90 cluster table
- `genome_ANI` (421M rows) — pairwise within-species ANI (used for D4 within-species genome ranking)
- `ncbi_env` (4M rows) — environmental metadata where genome.has_sample = true (advisory only)

### External
- **GTDB r214 species tree** (newick) — downloaded externally from `https://data.gtdb.ecogenomic.org/releases/release214/`. Loaded into project for topology-support filtering at the rank level. Not stored in BERDL.
- **HMMER** (last-resort tool) — for Pfam recompute on architectures flagged by the Phase 3 audit.
- **AleRax** (Morel et al. 2024) — held in reserve for principled subsamples only; not used at full GTDB scale per constraint.

### Cross-database joins
- `eggnog_mapper_annotations.query_name` ↔ `gene_cluster.gene_cluster_id`
- `bakta_db_xrefs.gene_cluster_id` ↔ `gene_cluster.gene_cluster_id`
- `gene_genecluster_junction.gene_cluster_id` ↔ `gene_cluster.gene_cluster_id`
- `gene_genecluster_junction.gene_id` ↔ via `kbase_genomes.name` if needed
- GTDB lineage: `gtdb_taxonomy_r214v1` parsed to species / genus / family / order / class / phylum / domain rank scaffold

## Query Strategy

### Performance Plan
- **Tier**: Direct Spark on BERDL JupyterHub (on-cluster). REST API not used for headline queries.
- **Pattern**: per-species iteration for gene-level extraction (per docs/performance.md Pattern 2); per-KO IN-clause for moderate KO subsets (Pattern 1)
- **Critical pitfalls** (from docs/pitfalls.md):
  - Species IDs contain `--` — use exact equality or LIKE with prefix
  - Never full-scan `gene` (1B), `gene_genecluster_junction` (1B), `genome_ani` (421M), `bakta_db_xrefs` (572M)
  - Disable autoBroadcast on `kbase_uniprot.uniprot_identifier` joins to avoid maxResultSize errors
  - Match Spark import to environment (on-cluster: `spark = get_spark_session()` no import)
  - Cast string-typed numeric columns before comparison
- **Materialization**: per-phase intermediate parquet under `data/` for re-entrant analysis; Phase 1 outputs are read-only inputs to Phase 2; Phase 1+2 outputs are read-only inputs to Phase 3; all phases are read-only inputs to Phase 4

### Null Model Specification (the methodological core)

The phrase "tree-aware null" in the original brief hides several distinct null models. This plan commits to:

- **Producer null (paralog expansion)**: For each (clade, function class), the expected paralog count is drawn from a *clade-matched neutral family null* — paralog counts of UniRef50/90 clusters with the same overall presence frequency in the same clade, sampled to match clade size. This null does not require a copy-number birth-death model and is robust to local rate variation. Implementation in Phase 1 NB02.
- **Consumer null (acquisition)**: For each (clade, function class), the expected acquisition count is drawn from a *phyletic-distribution permutation null* — fix the number of clades a cluster appears in, permute which clades, recompute incongruence with GTDB rank scaffold. Implementation in Phase 1 NB02 (shared with producer null).
- **Topology-support filter** (D4): A function-class event is only called at the deepest rank where the GTDB tree's bootstrap support exceeds 0.7 *and* the rank's effective N is ≥10. Below 10, the event is dropped from depth stratification (still counted in flat tally).
- **Annotation-density covariate** (D2): Per-genome annotated-fraction is residualized out via OLS *before* score computation, not after.

These choices are committed to here because methodological vagueness on the null model is the most likely route to a non-falsifiable atlas (per critique #2 in DESIGN_NOTES.md).

## Analysis Plan

19 numbered notebooks across 4 phases. Notebook prefix encodes phase (`p1_` / `p2_` / `p3_` / `p4_`). All notebooks committed with saved outputs (BERIL hard requirement). Each phase ends with a phase-gate notebook that summarizes the decision and produces the handoff data file consumed by the next phase.

### Inter-Phase Reproducibility Contract
- All Phase-N outputs are written to `data/pN_*.parquet` or `data/pN_*.tsv`
- Phase-(N+1) notebooks must declare their Phase-N input dependency in the header markdown cell
- No Phase-(N+1) notebook reads from a Phase-N notebook directly; the only inter-phase contract is the file products listed in this plan

## Expected Outcomes (per phase)

### Phase 1
- **If H1**: Bacteroidota → Open Innovator on PUL UniRef50s; the four-quadrant structure exists at sequence level. Sets up Phase 2 strong-form test.
- **If H0 with structure**: structure exists but Bacteroidota PUL goes elsewhere (Broker / Closed / Sink). The strong-form regulatory-only prior is already weakened. Phase 2 reframes.
- **If H0 without structure**: no four-quadrant structure detectable. Project halts at Phase 1 with a publishable negative result on the diagonal-collapse fallback.

### Phase 2
- **If H1**: regulatory-vs-metabolic asymmetry confirmed at KO level AND mycolic-acid → Closed Innovator. Sets up Phase 3 generalization confirmation.
- **If H0 reframed**: asymmetry not confirmed but specific clade × KO patterns are real. Phase 3 reframes.
- **If methodological failure**: Alm 2006 TCS back-test fails at KO level → halt for diagnosis.

### Phase 3
- **If H1**: Cyanobacteria → Broker on PSII architectures AND TCS reproduction holds at architecture level. Atlas is internally consistent.
- **If conflict**: architecture-level result conflicts with KO-level. The disagreement itself is informative for the synthesis.

### Phase 4
- Final atlas: clade × function-class quadrant assignments at three resolutions, with cross-resolution concordance/conflict map and named-quadrant verdicts.
- **Three pre-registered verdicts** as supported / falsified / equivocal.
- **Falsifiable production**: even where pre-registered verdicts are falsified, the atlas produces concrete falsifiable quadrant verdicts on clades × functions where no quantitative prior currently exists (per the "weak prior" framing in DESIGN_NOTES.md).

## Potential Confounders

- **EggNOG annotation density** (the dominant confounder): mitigated via three-resolution design and explicit D2 residualization.
- **CPR / DPANN under-representation**: acknowledged scope limit. Atlas does not claim coverage of poorly-sampled lineages at deep ranks. D3 effective-N reporting flags this per phase.
- **Reference genome inflation within species**: mitigated via D1 (one genome per species before scoring).
- **GTDB topology weak support at deep ranks**: mitigated via D4 rank-level support filter.
- **UniRef cluster boundary instability across UniRef releases**: mitigated by committing to UniRef release version at start; rerun would change Phase 1 output.
- **Pfam-completeness in `bakta_pfam_domains`**: mitigated via Phase 3 mandatory audit + HMMER recompute fallback.
- **Direction inference at deep ranks**: not attempted (acknowledged limit, not confounder).

## Total Budget

| Phase | Effort | Cumulative | Stop point? |
|---|---|---|---|
| Phase 1 | ~4 weeks | 4 | Yes — publishable existence test |
| Phase 2 | ~5 weeks | 9 | Yes — publishable functional atlas |
| Phase 3 | ~5 weeks | 14 | Yes — publishable architectural validation |
| Phase 4 | ~2 weeks | 16 | Final synthesis |

**Total ~16 agent-weeks**, with three natural commit points at which the project can be paused.

## Revision History

- **v1** (2026-04-26): Initial plan. Three-phase forced-order atlas; pre-registered hypotheses with weak-prior calibration; design reasoning captured separately in DESIGN_NOTES.md.

## Authors

- **Adam Arkin**
  - ORCID: 0000-0002-4999-2931
  - Affiliation: U.C. Berkeley / Lawrence Berkeley National Laboratory
