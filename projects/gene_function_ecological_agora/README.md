# Gene Function Ecological Agora

*Innovation Atlas Across the Bacterial Tree*

## Research Question

Across the prokaryotic tree (GTDB r214; 293,059 genomes / 27,690 species), build a multi-resolution **innovation + acquisition-depth atlas of bacterial function classes**, anchored to clade phylogeny and environmental ecology. Per (clade × function-class) tuple, the atlas reports: production rate (paralog expansion above null), acquisition profile by depth (recent vs ancient gain events), MGE context, environmental ecology, and phenotype anchoring where data exist. Test whether regulatory and metabolic function classes show distinct acquisition-depth profiles, anchored to specific weak-prior hypotheses (Bacteroidota PUL, Mycobacteriota mycolic-acid, Cyanobacteria PSII, Alm 2006 TCS reproduction).

*Plan v2.9 reframed the central deliverable from a single "regulatory-vs-metabolic asymmetry" headline to the broader innovation/acquisition/ecology atlas with regulatory-vs-metabolic as one diagnostic among several. See `DESIGN_NOTES.md` v2.8 entry.*

## Status

**Project complete with synthesis + 9 adversarial review rounds + 1 standard berdl-review (2026-04-29, REPORT v3.5).** All five Phase 4 deliverables (P4-D1 through P4-D5) closed plus NB28 Final Synthesis pass: 7 data deliverables (`data/p4_pre_registered_verdicts.tsv`, `data/p4_deep_rank_pp_atlas.parquet`, `data/p4_genus_rank_quadrants_tree_proxy.tsv`, `data/p4_concordance_weighted_atlas.parquet`, `data/p4_conflict_analysis.tsv`, `data/p4_per_event_uncertainty.parquet`, `data/p4_leaf_consistency_lookup.parquet`) + 11 synthesis figures (Hero Atlas Innovation Tree + Three-Substrate Convergence Card + Acquisition-Depth Function Spectrum + Control-class signature plane; Supporting PSII rank-dependence ladder + Hypothesis Verdict Card + Function × Environment flow + Per-hypothesis leaf_consistency + Atlas confidence ridge; NB22-original atlas heatmap + four-quadrant summary) + REVIEW_9 follow-up sub-clade analysis (`data/p4_review9_mycolic_subclade_d.tsv` + `_genus_lc.tsv` + `_diagnostics.json`). Notable: the leaf_consistency layer (S7) revealed within-Mycobacteriaceae heterogeneity that family-rank P×P aggregation had obscured — the NB12 mycolic-acid Innovator-Isolated finding is driven by mycolic-positive sub-clades. NB29 sub-clade-restricted recomputation (REVIEW_9 I10 response): mycolic-positive sub-clade (10 of 13 genera) producer d=+0.394 vs family-rank d=+0.309 — modest amplification, original NB12 finding holds with sharpened framing ("mycolate-producing sub-clade Innovator-Isolated" rather than "Mycobacteriaceae as a family"). Two methodology elements added in synthesis (M26 tree-based parsimony donor inference at genus rank, distinct from M25-deferred composition-based inference; leaf_consistency as per-(rank × clade × ko) prevalence metric). **2 of 4 pre-registered weak-prior hypotheses confirmed** (NB12 Mycobacteriaceae × mycolic-acid Innovator-Isolated; NB16 Cyanobacteria × PSII Innovator-Exchange at class rank); both surviving D2 annotation-density residualization (P4-D5), grounded in expected biomes at p < 10⁻¹¹ (P4-D1 NB23), confirmed by BacDive phenotype anchors (P4-D1 NB24), and confirmed as non-phage-borne (P4-D2). Phase 1B Bacteroidota PUL falsified at deep-rank absolute-zero criterion but recovered as small consumer-z signal at the Sankoff-parsimony diagnostic; ecologically grounded (1.40× gut/rumen, p<10⁻³⁵). NB11 H1 (regulatory-vs-metabolic d≥0.3 asymmetry) REFRAMED at small effect size — direction supports Jain 1999 complexity hypothesis, independently empirically validated by Burch et al. 2023 (PMID:37232518). Alm 2006 r ≈ 0.74 quantitative reproduction NOT REPRODUCED at full GTDB scale (P4-D3: r=0.10–0.29 across four framings, n=18,989); methodology generalization holds (NB17 architectural concordance r=0.67). See [REPORT.md](REPORT.md) Final Synthesis section for the integrated narrative.

The full project history is preserved in REPORT.md as a phase-by-phase milestone trail (Phase 1A pilot → 1B full atlas → 2 KO atlas + M22 attribution → 3 architectural resolution + Cyanobacteria PSII → 4 phenotype/ecology grounding + MGE context + Alm reproduction + D2 residualization), with seven integrated adversarial review responses and 25 documented methodology revisions (M1–M25).

**Earlier milestone summaries** preserved below for context:

**Phase 1A complete (2026-04-26): `PASS_WITH_REVISION`.** Methodology validated on a 1,000-species × 1,200-UniRef50 pilot. Four methodology revisions (M1–M4) documented for Phase 1B.

**Phase 1B complete (2026-04-27): `PASS_REFRAMED` + qualified pass via tree-aware diagnostic.** Methodology validated at full GTDB scale (18,989 bacterial species × 100,192 UniRef50s × 5 ranks = 1.29 M producer scores; ~1 hour wall time). Pre-registered Bacteroidota PUL Innovator-Exchange hypothesis falsified at the absolute-zero criterion (0/4 deep ranks). Post-gate work surfaced two further corrections:

- **A close re-reading of Alm 2006** (`docs/alm_2006_methodology_comparison.md`) showed the project had been mis-stating Alm 2006's methodology in three load-bearing ways. The four-quadrant framework is *this project's construction*, not Alm 2006's; they worked at single-domain level (≈ UniRef50, comparable to ours, not at "family"); they used phylogenetic-tree-aware reconciliation (we had been using parent-rank dispersion permutation null).
- **A tree-aware diagnostic** (Sankoff parsimony on the GTDB-r214 tree, NB08c) recovers the expected direction (positive HGT > negative housekeeping at p = 2.1×10⁻⁵) where parent-rank dispersion had produced the order-rank anomaly. **Methodology framework not broken; the metric was wrong.** But effect size at UniRef50 remains small (Cohen's d = 0.15; below the d ≥ 0.3 threshold). Phase 2 KO aggregation must amplify to d ≥ 0.3 or the substrate-hierarchy claim is falsified and an M11 reconciliation-based redesign triggers.

**Phase 2 entry M18 amplification gate (2026-04-27): `PASS`.** NB09 extracted KO data at full GTDB scale (28M (species, KO) presence rows across 13,062 unique KOs). NB09b's first-pass M18 verdict was `MARGINAL` (best d = 0.21; direction reversed against expectation). NB09c's strict-class diagnostic re-classified housekeeping using KEGG-curated K-ID ranges and reused NB09b's Sankoff scores; verdict swung to `PASS` with **6/9 strict pairs at d ≥ 0.3** (best pair: pos_crispr_cas vs neg_trna_synth_strict, d = 3.56, 95% CI [2.93, 21.53]). Substrate-hierarchy claim survives: Cohen's d amplifies from 0.146 (UniRef50, NB08c) to 0.665–3.558 (KO, NB09c best pairs), a 4–25× amplification. M21 baked in: canonical clean housekeeping = tRNA-synth (`K01866-K01890`) + RNAP core (`{K03040, K03043, K03046}`); ribosomal dropped as load-bearing housekeeping due to bimodal contamination.

Twenty-one methodology revisions across Phase 1A → 1B → Phase 2 entry (M1–M21) baked into Phase 2 atlas. Three pre-registration omissions surfaced and corrected as project-discipline lessons (M2 dosage biology, M12 absolute-zero criterion, M14 misreading-of-Alm-2006). Four cheap diagnostics caught methodology issues that would have escalated otherwise (Phase 1A NB04b power analysis, Phase 1B NB08b discrimination, Phase 1B NB08c Sankoff metric, Phase 2 NB09c strict-class).

See [REPORT.md](REPORT.md) for milestone reports + diagnostic resolutions + Phase 2 M18 gate; [data/p1a_phase_gate_summary.md](data/p1a_phase_gate_summary.md) + [data/p1b_phase_gate_summary.md](data/p1b_phase_gate_summary.md) for Phase 1 formal gate decisions; [data/p2_m18c_gate_decision.json](data/p2_m18c_gate_decision.json) for the Phase 2 entry verdict; [docs/alm_2006_methodology_comparison.md](../../docs/alm_2006_methodology_comparison.md) for the BERIL-level methodology memo.

**Phase 2 atlas + M22 attribution complete (2026-04-27)**: NB10 produced 13.7M (rank × clade × KO) producer/participation scores + 17M Sankoff gain events at full GTDB scale; M21 sanity rail PASSES 6/6 strict pairs at full scale (d = 0.65 to 2.50). NB10b (M22) attributed 17M gains to recipient clade at every rank with acquisition-depth bins; per-class signatures clean: pos_crispr_cas at 58.7% recent / 2.4% ancient (HGT-active signature); neg_trna_synth_strict at 24.7% recent / 10.7% ancient (vertical-inheritance signature). The recent-to-ancient ratio is itself a class signature — the v2.9 atlas centerpiece is empirically validated.

**Phase 2 hypothesis tests (2026-04-27)**:
- **NB11 Tier-1 regulatory-vs-metabolic**: H1 REFRAMED. No test achieves d ≥ 0.3 between regulatory and metabolic KO pools; small signals (d=0.14-0.21) exist but below biological-significance threshold. **Notable novel observation**: KOs in *both* regulatory and metabolic pathways (mixed category) show 2× the Innovator-Exchange rate of pure regulatory or pure metabolic — pathway-overlap, not regulatory-vs-metabolic, is the asymmetry that exists.
- **NB12 Mycobacteriaceae × mycolic-acid**: **H1 SUPPORTED — Innovator-Isolated at family + order ranks**. Producer d = +0.309 [+0.293-axis], consumer d = −0.193, both significant after Bonferroni. **Striking acquisition-depth signature: 79.87% recent, 0% ancient gains** for Mycobacteriaceae mycolic-acid acquisitions (compare 48.79% recent, 3.68% ancient atlas-wide for mycolic-acid). The pre-registered Innovator-Isolated phenotype recovered with three concordant signals (effect size, significance, depth profile). The first pre-registered weak-prior hypothesis empirically supported in this project.

**Phase 3 closed (2026-04-28) at PASS_MIXED concordance.** NB13 Pfam audit confirmed `interproscan_domains` as substrate (`bakta_pfam_domains` had silent gaps for all 4 PSII Pfams + 7/33 markers total, matching the documented `[plant_microbiome_ecotypes]` pitfall). NB14 selected 10,750 candidate KOs from atlas off-(low,low) tuples; NB15 architecture census on 4 focused subsets (PSII, TCS HK, mycolic-acid, mixed-top-50) revealed a **novel architectural-promiscuity finding**: mixed-category KOs (NB11's elevated Innovator-Exchange) show 46 architectures/KO median vs PSII's 1 — *a KO's structural diversity correlates with its propensity to flow*. **NB16 Cyanobacteria × PSII Innovator-Exchange test: H1 SUPPORTED at class rank** (producer d=1.50, consumer d=0.70, MW p<10⁻³; acquisition-depth signature 2.05% ancient vs 14.9% atlas-wide PSII = the 7× lower ancient fraction is the *donor-origin signature* per Cardona et al. 2018). NB17 TCS HK architectural decomposition confirmed canonical Alm 2006 architecture (PF00512 + PF02518) at 25K gain events with the recent-skewed profile; KO ↔ architectural concordance at family rank: consumer r=0.67 confirmatory, producer r=0.09 exploratory. NB18 Phase 3 → Phase 4 gate verdict: PASS_MIXED. **2 of 4 currently-testable pre-registered hypotheses confirmed.**

**Phase 4 complete (2026-04-29)** — All 5 deliverables (P4-D1 phenotype/ecology grounding; P4-D2 MGE context per gain; P4-D3 Alm 2006 r ≈ 0.74 reproduction; P4-D4 pangenome-openness validation; P4-D5 D2 annotation-density residualization) closed. P4-D1 grounded all three confirmed atlas findings in expected biomes at p<10⁻¹¹ + phenotype anchors. P4-D2 confirmed pre-registered atlas KOs are not phage-borne (per-cluster MGE-machinery 0/0/0.57% for PSII/PUL/mycolic; PSII gene-neighborhood at random baseline 10.91% vs Poisson expected 10.6%). P4-D3 honestly recorded that Alm 2006 r ≈ 0.74 does NOT reproduce at full GTDB scale (r=0.10–0.29) while methodology generalization (architectural concordance r=0.67) holds. P4-D4 returns informative null at atlas scale — M22 lineage-level recent-acquisition and within-species pangenome openness measure distinct evolutionary phenomena. P4-D5 closes the long-standing D2 pre-registration debt: producer_z bias-immune (R²=0.000), consumer_z carries small bias (R²=0.053) that does not change any verdict. See REPORT.md Final Synthesis section.

## Overview

A multi-phase, multi-resolution atlas of clade-level functional innovation across GTDB r214, with explicit acquisition-depth attribution and environmental/phenotype anchoring. The atlas is built at three resolutions in a forced order: sequence-only (UniRef50), functional (KO), and architectural (Pfam multidomain architecture). Each phase's output gates and refines the next; the final synthesis (Phase 4) cross-validates assignments across resolutions and anchors the atlas to environmental ecology + metabolic phenotypes via integration with **NMDC**, **kescience_mgnify**, **kbase_ke_pangenome.gtdb_metadata** (environment), and **BacDive**, **kescience_webofmicrobes**, **kescience_fitnessbrowser** (phenotype).

**At deep ranks (≥ family)** the atlas reports **Producer × Participation categories** (Innovator-Isolated / Innovator-Exchange / Sink/Broker-Exchange / Stable) — direction-agnostic because per-family DTL reconciliation is out of scope at full GTDB scale. **At genus rank** Phase 3 runs composition-based donor inference on the architectural deep-dive candidate set, producing the full four-quadrant labels (Open / Broker / Sink / Closed) on that subset.

Four pre-registered weak-prior hypotheses span the regulatory-vs-metabolic divide:

- **Phase 1A pilot**: positive controls (AMR, CRISPR-Cas, Alm 2006 TCS) + negative controls (ribosomal, tRNA-synthetase, RNAP) validate methodology on 1K species × 1K UniRef50s
- **Phase 1B** (UniRef50): Bacteroidota → Innovator-Exchange on PUL CAZymes (deep-rank)
- **Phase 2** (KO): Mycobacteriota → Innovator-Isolated on mycolic-acid pathway (deep-rank)
- **Phase 3** (Pfam architecture): Cyanobacteria → Broker on PSII architectures (genus-rank, with donor inference)
- **Phases 2 & 3**: Alm 2006 two-component-system back-test (KO + architectural)

Total budget ~17 agent-weeks with four natural stop-points (Phase 1A pilot, Phase 1B, Phase 2, Phase 3) plus a final synthesis (Phase 4).

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — operational plan: phases, axis positions, hypotheses, query strategy
- [Design Notes](DESIGN_NOTES.md) — design record: critique of the brief, through-line argument, rejected alternatives, weak-prior acknowledgement
- [Report](REPORT.md) — Phase 1A milestone report; will expand as Phases 1B–4 land
- [Phase 1A Gate Summary](data/p1a_phase_gate_summary.md) — formal Phase 1A → 1B gate decision with M1–M4 revisions

## Reproduction

### Hardware + environment

- **BERDL JupyterHub** — on-cluster Spark Connect at `sc://jupyter-aparkin.jupyterhub-prod:15002` (token in `KBASE_AUTH_TOKEN` env var). 10 worker pods per env; `spark.driver.maxResultSize = 1024 MB` (default — see Spark-side caveat below).
- **Local driver**: ~16–32 GB RAM (the project's pandas spatial-merge OOM hit at ~24M rows × 9 cols ≈ 9 GB working set).
- **GTDB r214 species tree** (newick) used by Sankoff parsimony, loaded from `https://data.gtdb.ecogenomic.org/releases/release214/`.
- **Python deps**: `requirements.txt` (pyspark, pandas, numpy, scipy, matplotlib, scikit-learn).
- **MinIO staging area**: `s3a://cdm-lake/tenant-general-warehouse/microbialdiscoveryforge/projects/gene_function_ecological_agora/data/` for intermediate parquets between Spark and pandas (see Spark-side caveat).

### Notebook execution profile

| Notebook(s) | Phase | Runtime | Spark? | Notes |
|---|---|---|---|---|
| 01–03 (pilot) | 1A | ~10 min total | ✓ | 1K species × 1.2K UniRef50 pilot |
| 04, 04b (gates) | 1A | ~5 min | local | pandas + JSON gate verdict |
| 05 (full extract) | 1B | **~30–45 min** | ✓ | 28M (species, UniRef50) presence rows pulled |
| 06 (full atlas) | 1B | **~1 hour** | ✓ | 1.29M producer/consumer scores at full GTDB |
| 07–08c (PUL test + gates) | 1B | ~10 min | local | + Sankoff diagnostic |
| 09 (KO extract) | 2 | ~20 min | ✓ | 28M (species, KO) presence rows |
| 09b/c (M18 gates) | 2 | ~5 min | local | strict-class amplification test |
| **10 (KO atlas)** | 2 | **~15 min after broadcast-hint fix** | ✓ | 13.7M (rank × clade × KO) producer/consumer scores; **see Performance Caveats below** |
| **10b (M22 attribution)** | 2 | **~30 min** | ✓ | 17M Sankoff gain events with M22 recipient-rank attribution |
| 11, 12 (hypothesis tests) | 2 | ~5 min each | local | NB11 reg-vs-met + NB12 mycolic |
| 13–14 (Pfam audit + candidates) | 3 | ~15 min combined | ✓ | Phase 3 substrate decision + 10,750 candidate KOs |
| 15 (architecture census) | 3 | ~30 min | ✓ | 4 focused subsets across 833M IPS hits |
| 16 (Cyano PSII) | 3 | ~5 min | local | NB16 hypothesis test |
| 17 (TCS HK architectural) | 3 | ~5 min | local | NB17 backtest |
| 18 (Phase 3 gate) | 3 | ~5 min | local | gate verdict |
| 19 (P4-D3 Alm reproduction) | 4 | ~5 min | local | per-species HPK count + recent-LSE join |
| 20 (P4-D5 D2 residualization) | 4 | **~35 sec** | local | numpy OLS; pure pandas |
| 21 (P4-D4 pangenome openness) | 4 | **~25 sec** | local | pure pandas |
| 22 (P4-D1 audit + corrections) | 4 | ~10 min | ✓ | substrate audit (BacDive accession format, MGnify catalog, pangenome.ncbi_env discovery) |
| 23, 23b (env grounding + biome enrichment) | 4 | ~1 min combined | mostly local | env_per_species pull (Spark) + tests (pandas) |
| 24, 24b (BacDive phenotype) | 4 | ~30 sec | mostly local | BacDive phenotype pull + per-clade summaries |
| 25 (AlphaEarth env-cluster) | 4 | ~10 sec | local | k=10 K-means on 5,157 species |
| **26b/c (P4-D2 MGE machinery)** | 4 | **~30 min Spark + 30 sec finalize** | ✓ | bakta_annotations 132M-row scan with MGE keyword regex + KO + gene_cluster joins |
| **26f/g (P4-D2 PSII gene-neighborhood)** | 4 | **~25 min total** | ✓ | pangenome → genome-context cross-walk; 5 stages with MinIO checkpoints |
| **28a (synthesis verdicts + 4-cat atlas)** | Synth | ~10 sec | local | 13.7M atlas extraction |
| **28b (M26 tree-based donor inference)** | Synth | ~140 sec | local | algebraic per-(genus × KO) donor-event count |
| 28c (concordance + uncertainty) | Synth | ~80 sec | local | 8.6M atlas merge + 2.5M conflict classification |
| **28d (synthesis figures)** | Synth | ~70 sec | local | 7 figures incl. Hero 1 Atlas Innovation Tree |
| **28e (leaf_consistency build)** | Synth | ~30 sec Spark + 35 sec finalize | ✓ | 28M assignments → per-(rank × clade × ko) species count → join to 17M gains |
| 28f (leaf_consistency figures) | Synth | ~45 sec | local | H3-B + S7 + S8 |

**End-to-end estimate from cold start:** ~6–8 hours of wall time; ~3 hours of that is Spark-side (NB05, 06, 09, 10, 10b, 13, 26, 28e); ~5 hours is pandas-side (most of Phase 4). With cached intermediate parquets, the synthesis pass alone is **~5 minutes** (NB28a → 28f).

### Performance caveats (lessons learned, from `docs/pitfalls.md`-style entries)

1. **Spark-Connect driver result-size cap.** Default `spark.driver.maxResultSize = 1024 MB` is reached when joining 1B-row tables filtered to >200K elements then `toPandas()`. Workaround: write Spark result to MinIO via `coalesce(N).write.parquet(s3a://…)`, then read locally as parquet. Used throughout Phase 4 (NB10, 26b, 28e). Cannot be raised at runtime via `SET spark.driver.maxResultSize` — that's read-only after session start.

2. **Pandas spatial-merge OOM at ~10M+ rows.** Hit at NB26h (Bacteroidota PUL gene-neighborhood, 723K focal × 210K contigs → ~24M-row × 9-col merge ≈ 9 GB). Workaround: batched processing OR full-Spark Stage 6+ (do spatial filter in Spark, only collect aggregate). PSII (309 species, 27K focal) fit; PUL/mycolic at full Bacteroidota/Mycobacteriaceae did not.

3. **Spark `autoBroadcastJoinThreshold = -1` is harmful (not protective).** NB10 first attempts hung 17+ min until removed. Trust the optimizer for small-table joins; use explicit `F.broadcast(small_df)` hints when the optimizer doesn't auto-detect. The "defensive" disable from prior projects was actively counterproductive.

4. **JupyterHub kernel idle-timeout (~17–25 min).** Killed long-running notebooks silently. **Workaround pattern**: convert notebook to .py (`jupytext --to py`), run via `nohup` from a terminal, write intermediate parquets at each stage so partial results are recoverable. Used for NB10, 10b, 26.

5. **Driver Java heap ceiling.** Default `SPARK_OPTS` give `-Xmx4g`; raise via env if needed for heavy `coalesce` writes. Not hit in this project but documented.

### Reproduction order

```bash
# Phase 1A pilot (validation)
jupyter nbconvert --execute notebooks/01_p1a_pilot_data_extraction.ipynb --inplace
jupyter nbconvert --execute notebooks/02_p1a_null_model_construction.ipynb --inplace
jupyter nbconvert --execute notebooks/03_p1a_pilot_atlas.ipynb --inplace
jupyter nbconvert --execute notebooks/04_p1a_pilot_gate.ipynb --inplace

# Phase 1B (full GTDB)
jupyter nbconvert --execute notebooks/05_p1b_full_data_extraction.ipynb --inplace  # ~30-45 min
jupyter nbconvert --execute notebooks/06_p1b_full_atlas.ipynb --inplace  # ~1 hour
jupyter nbconvert --execute notebooks/07_p1b_bacteroidota_pul_test.ipynb --inplace
jupyter nbconvert --execute notebooks/08_p1b_phase_gate.ipynb --inplace
jupyter nbconvert --execute notebooks/08c_p1b_metric_diagnostic.ipynb --inplace

# Phase 2 (KO atlas + M22 attribution)
jupyter nbconvert --execute notebooks/09_p2_ko_data_extraction.ipynb --inplace
jupyter nbconvert --execute notebooks/09c_p2_m18_strict_class_retest.ipynb --inplace
nohup python3 -u notebooks/10_p2_ko_atlas.py > /tmp/nb10.log 2>&1     # NOT a notebook — Spark from .py
nohup python3 -u notebooks/10b_p2_m22_gain_attribution.py > /tmp/nb10b.log 2>&1
python3 notebooks/11_p2_regulatory_vs_metabolic.py  # local, ~5 min
python3 notebooks/12_p2_mycobacteriota_mycolic_acid.py  # local, ~5 min

# Phase 3 + 4 + Synthesis: see notebook profile table above
nohup python3 -u notebooks/28_p4_synthesis.py > /tmp/nb28.log 2>&1
# … etc
```

(Cells starting with `python3 ...` are .py format; those starting with `jupyter nbconvert` are .ipynb. The Phase 1B/Phase 2 atlas-construction scripts must run via `nohup` to survive JupyterHub idle-timeout.)

## Authors

- **Adam Arkin**
  - ORCID: 0000-0002-4999-2931
  - Affiliation: U.C. Berkeley / Lawrence Berkeley National Laboratory
