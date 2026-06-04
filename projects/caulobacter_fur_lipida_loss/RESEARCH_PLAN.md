# Research Plan: The regulatory and proteomic architecture of Δ*fur*-permitted lipid A loss in *Caulobacter crescentus*

## How this question landed here

In *Caulobacter crescentus* NA1000, the LPS biosynthetic gene *lpxC* is essential under standard conditions, yet the gene can be eliminated if *fur* (the ferric uptake regulator) is also inactivated. The colleague who supplied this dataset, **Kathleen R. Ryan (UC Berkeley)**, is the senior author of the paper that first established this dependency — **Zik et al. 2022 *Cell Reports* (PMID 35649364)** — which showed that:

1. Δ*lpxC* viability requires both Δ*fur* and the presence of *anionic sphingolipids* (specifically ceramide phosphoglycerate, **CPG**, produced by the locus CCNA_01212/CCNA_01217–01223).
2. The published statement is explicit: "**Fur-regulated processes (not iron status per se)** underlie viability."
3. Δ*sspB* is part of the published mechanism, not a confound — the published rescued strain is Δ*lpxc* Δ*fur* Δ*sspB*, identical to strain 4599 here.

Two other published lines of evidence frame what is still unanswered:

- **Uchendu, Isom, Klein 2026** bioRxiv (`10.1101/2026.04.12.717747`) identifies three sphingolipid-specific IM transporter homologs — **CCNA_01213 (lptG2), CCNA_01214 (lptF2), CCNA_01226 (lptC2)** — embedded within the sphingolipid locus, and shows that LptF2/G2 share the *canonical* LPS ATPase **LptB** rather than encoding their own. The downstream periplasmic (LptA) and OM (LptD/E) components of canonical LPS transport may be co-opted for sphingolipid trafficking, but this has not been demonstrated transcriptionally or proteomically in an actual Δ*lpxc* strain.
- The Caulobacter Fur regulon spans ~250 derepressed and ~240 repressed genes (**Leaden et al. 2018**, PMID 30210482; **da Silva Neto et al. 2009**, PMID 19520766). Which *subset* of these is mechanistically critical for the Δ*lpxc* rescue is not known.
- ChvG-ChvI is the dominant envelope-stress regulatory system in Caulobacter (**Stein et al. 2021**, PMID 34124942; **Quintero-Yanes et al. 2022**, PMID 36480504), but no published paper links it to the Δ*fur* Δ*lpxc* rescue.

The orientation analysis in `notebooks/00_orientation.ipynb` produced four concrete findings that this plan responds to:

| Phase A finding | Implication |
|---|---|
| ChvI regulon strongly enriched in **both** 4584-vs-4580 (Stein fold=4.75, p=8e-9) and 4599-vs-4584 (Stein fold=4.56, p=**1.4e-15**) | ChvI is engaged as both cooperator and consequence — H1 has empirical support |
| Sphingolipid biosynthesis locus (*spt*, *bcerS*, *acp*, *cerR*, *acps*) is **not induced** — most genes slightly *down* in 4584 and 4599; lptF2/G2/lptC2 *down* in 4599 (FDR<0.05) | Rescue is not driven by biosynthesis upregulation — H3 needs reframing to *post-transcriptional flux + decoration enzyme substitution* |
| **CtpA / CCNA_03113 (LpxE-like) +0.58 logFC in 4599-vs-4584** (borderline), and **canonical Lpt apparatus is maintained or up** (MsbA-like CCNA_00307 +0.89 FDR=0.006; LptC-related CCNA_03716 +0.56 FDR=0.005) | Consistent with Zik 2022 (CtpA substitutes for LpxF) AND with Uchendu 2026 shared-component model |
| **SdpA lytic murein transglycosylase +4.8 log2 at the OM proteome** in 4672 vs 4659; PG-related enzymes prominent | Peptidoglycan remodeling is part of the *Caulobacter* response to lipid A loss — adds the fourth hypothesis (H4) |

These four findings, plus the existence of **198 RB-TnSeq experiments for *Caulobacter crescentus* NA1000 in `kescience_fitnessbrowser`** (orgId `Caulo`), make the rescoping below tractable from this dataset.

## Refined research question

Given that Zik 2022 establishes the high-level mechanism (Δ*fur* + anionic sphingolipid + Δ*sspB* permit Δ*lpxc*), what are the regulatory and proteomic constituents of the rescue, and what makes this route uniquely available to *Caulobacter* among the four Gram-negative species known to tolerate lipid A loss?

Specifically:
1. *Which* Fur regulon members are operationally required (vs. which are merely incidentally derepressed)?
2. *Is the existing sphingolipid pathway sufficient* at the transcript level, with rescue operating at the post-transcriptional / flux level? If yes, does CtpA upregulation account for the LpxF-like processing step?
3. *Is the canonical Lpt apparatus repurposed* for sphingolipid transport in the Δ*lpxc* state, as Uchendu 2026 predicts but did not directly test?
4. *Does peptidoglycan remodeling participate* — as it does in *A. baumannii* via the orthogonal Kang/Boll 2021 route?
5. *Why is this route uniquely Caulobacter*? Pangenome presence/absence of the sphingolipid biosynthesis + transport locus, the LpxE/CtpA substitute, and the relevant Fur-regulated genes across the four lipid-A-loss-tolerant species.

## Hypotheses

Each hypothesis is stated with H0/H1, the Phase A evidence already on hand, and the *specific* analyses required to resolve it.

### H1 — ChvG-ChvI envelope-stress regulon: cooperator and consequence

- **H0**: ChvI regulon induction in 4584 and 4599 is no greater than expected by chance given universe size and DEG cardinality.
- **H1**: ChvI regulon is *partially* induced when Fur+SspB are released (permissive condition), and *further* induced when lipid A is lost (consequence), with distinct gene subsets dominating each phase.

**Phase A evidence**: Stein 4.75-fold p=8e-9 (4584-vs-4580) and 4.56-fold p=1e-15 (4599-vs-4584); QY 3.18-fold (4584) and 2.87-fold (4599). H0 already rejected; the question is *which subset of ChvI targets is engaged at each phase*, whether **SigU** (ECF σ-factor, +3.13 in 4599-vs-4584) is the operational driver of the 4599-specific component, and whether the early-cooperator subset overlaps with the Fur regulon (suggesting Fur-ChvI co-regulation).

### H2 — A critical Fur regulon subset, rankable by phenotypic importance

- **H0**: The Δ*fur* contribution to Δ*lpxc* rescue is driven by *generic* derepression of the entire Fur regulon equally — no specific subset matters more than others.
- **H1**: A small, identifiable subset of Fur-released genes is mechanistically critical — genes whose loss is associated with strong fitness defects under iron limitation, oxidative stress, or envelope-disrupting conditions.

**Phase A evidence**: Massive Fur derepression (HutA +10.5, CCNA_02275 +9.8 transcript with +8.9 log2 protein cascade, multiple TBDTs, DUF4198 family). The transcriptome cannot distinguish "matters" from "merely derepressed" — but the **198 RB-TnSeq Caulobacter experiments in `kescience_fitnessbrowser`** can rank Fur-released genes by phenotypic importance. The clean Fur-only signal needs **Leaden 2018 SRP136695** re-analyzed (4584-vs-4580 is confounded by Δ*sspB*).

### H3 — Sphingolipid substitution operates by flux + processing, not biosynthesis

- **H0**: Δ*lpxc* rescue requires transcriptional induction of the sphingolipid biosynthesis pathway (i.e., the existing baseline expression is insufficient).
- **H1**: The constitutive sphingolipid pool is sufficient; rescue operates by (a) substrate flux rerouting in the absence of LpxC competition, and (b) **CtpA / LpxE-like CCNA_03113** providing the LpxF-equivalent head-group processing step; (c) the canonical Lpt apparatus is *maintained* (or modestly upregulated) for sphingolipid trafficking, consistent with Uchendu 2026's shared-component model.

**Phase A evidence**: spt down -0.64 (FDR=0.002), most sphingolipid biosynthesis loci down/stable. H0 — biosynthesis induction — is already rejected. CtpA +0.58 borderline-up in 4599-vs-4584. MsbA-like CCNA_00307 +0.89 (FDR=0.006), LptC-related CCNA_03716 +0.56 (FDR=0.005), canonical LptDFGE stable. H1 has prima facie support.

### H4 — Peptidoglycan remodeling participates in the lipid-A-loss response

- **H0**: PG remodeling enzymes do not show coordinated up-regulation in 4599 vs 4584.
- **H1**: A subset of PG-remodeling enzymes (lytic transglycosylases, PBPs, Ldts) shows coordinated upregulation in 4599 at transcript and/or protein level, evocative of (but mechanistically distinct from) the Kang/Boll 2021 PBP1A/LdtJ-LdtK route in *A. baumannii*.

**Phase A evidence**: **SdpA (lytic murein transglycosylase) +4.8 log2 at the OM proteome** in 4672 vs 4659. Additional PG-remodeling enzymes (DD-carboxypeptidase, PBP family) need a systematic check.

## Literature Context

See `references.md` for the full bibliography. Anchors used by this plan:

- **Zik et al. 2022** (PMID 35649364) — published mechanism; identifies the sphingolipid biosynthesis locus and the suppressor screen.
- **Uchendu et al. 2026** bioRxiv `10.1101/2026.04.12.717747` — sphingolipid IM transporter homologs and the shared-LptB model.
- **Olea-Ozuna et al. 2020/2024** (PMIDs 33063925, 39093898) — sphingolipid biosynthetic pathway and 11-gene cluster.
- **Dhakephalkar et al. 2023/2025** (PMIDs 37286040, 39829823) — CpgB/CpgD biochemistry.
- **Stein et al. 2021** (PMID 34124942) and **Quintero-Yanes et al. 2022** (PMID 36480504) — ChvI regulon definitions.
- **Greenwich et al. 2023** (PMID 37040790) — ChvG-ChvI conserved circuit review.
- **Leaden et al. 2018** (PMID 30210482) and **da Silva Neto et al. 2009** (PMID 19520766) — Caulobacter Fur regulon.
- **Moffatt et al. 2010** (PMID 20855724) and **Kang et al. 2021** (PMID 33402533) — *A. baumannii* LpxC viability + PBP1A/Ldt PG-remodeling.
- **Steeghs et al. 2001** (PMID 11742971) — *N. meningitidis* LPS-deficient.
- **Gao et al. 2008** (PMID 18795947) — *M. catarrhalis* late-acyltransferase deletion.
- **Sastry et al. 2019** (DOI 10.1038/s41467-019-13483-w) — iModulons methodology (no Caulobacter set yet).

## Data Sources

### Internal (user-supplied, already in `user_data/kr_caulobacter_envelope/clean/`)

| Table | Rows | Use |
|---|---|---|
| `fact_counts_raw.csv` | 34,974 | Raw counts; only if re-analyzing or QC |
| `fact_expression_cpm.csv` | 35,613 | TMM-CPM per locus per library |
| `fact_differential.csv` | 11,871 | edgeR DE per contrast |
| `om_proteome.csv` | 795 | Single-replicate OM proteome, three strains |
| `dim_feature.csv` | 4,020 | Annotation lookup |
| `chvi_regulon_quintero_yanes_2022.csv` | 594 | H1 reference regulon |
| `chvi_overexpression_regulon_stein_2021.csv` | 162 | H1 reference regulon |
| `strain_crosswalk.csv` | 3 | RNA-seq ↔ proteome strain ID join |

### External (BERDL — Spark SQL via `kescience_*` / `kbase_*` on-cluster)

| Table | Purpose | Estimated rows | Filter strategy |
|---|---|---|---|
| `kescience_fitnessbrowser.organism` | Confirm orgId='Caulo' for Caulobacter | 46 | `WHERE orgId = 'Caulo'` |
| `kescience_fitnessbrowser.experiment` | 198 Caulobacter experiments by `expGroup` | ~5000 | `WHERE orgId = 'Caulo'` (then group by expGroup) |
| `kescience_fitnessbrowser.fitbyexp_caulo` | Per-experiment fitness for Caulobacter | ~700k | `WHERE expName IN (...)`; `CAST(fit AS DOUBLE)` |
| `kescience_fitnessbrowser.genefitness` | Aggregate gene-level Caulobacter fitness | ~3800 | `WHERE orgId = 'Caulo'` |
| `kescience_fitnessbrowser.besthitkegg`, `keggmember`, `kgroupdesc` | Optional KO mapping | varies | two-hop join per pitfalls.md |
| `kescience_paperblast.gene`, `genepaper`, `snippet`, `curatedgene` | Gene-literature for any new candidate | varies | per-gene lookups |
| `kbase_ke_pangenome.*` (or BERDL pangenomes) | Cross-species comparative arm: presence/absence of sphingolipid locus, Fur regulon orthologs, Lpt apparatus, in A. baumannii / N. meningitidis / M. catarrhalis | TBD | by species filter |
| `kescience_alphafold` | Structure overlay for CtpA / LpxF substitutability claim | varies | per-protein |

### Auxiliary (to be ingested in NB01)

| Source | Identifier | Action |
|---|---|---|
| Leaden et al. 2018 Δ*fur* Caulobacter RNA-seq | **SRA SRP136695** | Pull (prefetch + fasterq-dump), HISAT2-align to NA1000, edgeR DE; output a *Fur-only* DEG signature that 4584-vs-4580 can be referenced against. **Significant compute — defer to `/cts`** (CTS task service). |

### Performance and pitfalls

- **Tier**: small Pandas for most steps; one BERDL Spark SQL pull per fitness/comparative analysis with explicit filters; CTS for SRA re-analysis.
- **Known pitfalls** (`docs/pitfalls.md`):
  - `kescience_fitnessbrowser.genefitness.fit` and `.t` are **strings** → always `CAST(... AS DOUBLE)`.
  - `kescience_fitnessbrowser.experiment.expGroup` (not `Group`).
  - `kescience_fitnessbrowser.kgroupdesc.desc` (not `description`).
  - KO mapping requires two-hop join through `besthitkegg` then `keggmember`.
  - `kescience_paperblast.year` is a string → `CAST(year AS INT)`.
- **Universal**: filter big tables before joining; avoid `.toPandas()` until the result is small.

## Analysis Plan

Notebooks are numbered, executed in JupyterHub with outputs committed (per `PROJECT.md`). Each notebook saves figures to `figures/NB{n}_*.png` and small derived tables to `data/NB{n}_*.csv` (excluded from git by the project gitignore rule; re-derived from the notebook on demand).

### NB01 — Leaden 2018 SRP136695 re-analysis (Fur-only DEG signature)

- **Goal**: Produce a clean Δ*fur*-only DEG signature (no Δ*sspB*, no Δ*rsaA*) to disambiguate Fur-specific vs SspB-specific effects in 4584-vs-4580.
- **Approach**:
  1. Submit a CTS task: `prefetch SRP136695 && fasterq-dump *.sra && fastp → HISAT2 (NA1000 ref, --very-sensitive) → featureCounts -Q 20 → edgeR TMM + glmQLFTest`.
  2. Bring DEG tables back to JupyterHub for join with the colleague's `fact_differential.csv`.
- **Outputs**:
  - `data/NB01_leaden2018_de_full.csv` — Fur-only DEGs at colleague's conventions
  - `data/NB01_fur_only_signature.csv` — high-confidence subset (|logFC|>1, FDR<0.05)
  - Comparison plot: scatter of 4584-vs-4580 logFC vs Leaden Δ*fur* logFC, colored by Fur regulon membership
  - `figures/NB01_fur_signature_scatter.png`

### NB02 — Fur-released gene fitness ranking via BERDL RB-TnSeq

- **Goal**: Rank Fur-released genes from NB01 (and from 4584-vs-4580) by phenotypic importance — i.e., which knockouts have strong fitness defects under iron limitation, oxidative stress, envelope-disrupting conditions, or carbon-restricted media. Tests H2.
- **Approach**:
  1. From `kescience_fitnessbrowser.experiment` with `orgId='Caulo'`, classify the 198 experiments by `expGroup` and the metadata condition strings. Tag the iron-limitation, oxidative-stress, envelope-stress, and carbon-shift conditions.
  2. Join `fitbyexp_caulo` to per-condition fitness summary statistics — mean, max-magnitude, and t-significance per gene per condition class.
  3. For each Fur-released gene from NB01 (and Phase A): compute the "phenotype rank" within the Fur regulon.
- **Outputs**:
  - `data/NB02_caulo_fitness_summary.csv` — per-gene fitness statistics per condition class
  - `data/NB02_fur_regulon_phenotype_rank.csv` — Fur-released genes ranked by phenotype magnitude
  - `figures/NB02_fur_regulon_phenotype_heatmap.png`
  - `figures/NB02_top_fur_genes_volcano.png` — genes in the top decile by fitness magnitude

### NB03 — ChvI regulon dissection and SigU as the operational driver

- **Goal**: Identify which subset of ChvI-induced genes is engaged in 4584-vs-4580 (cooperator) vs 4599-vs-4584 (consequence). Test whether SigU (CCNA_02977) drives the 4599-specific engaged subset. Tests H1.
- **Approach**:
  1. Partition the Stein + QY ChvI-induced regulons by phase of induction (early/cooperator: also up in 4584-vs-4580; late/consequence: only up in 4599-vs-4584).
  2. Functional annotation enrichment of each partition (use existing GO terms file + paperBLAST where useful).
  3. Identify *Caulobacter* SigU regulon members (literature + paperBLAST query) and test overlap with the late/consequence subset.
- **Outputs**:
  - `data/NB03_chvi_early_vs_late.csv` — ChvI gene-by-gene phase assignment
  - `data/NB03_sigU_overlap.csv` — SigU regulon ∩ late ChvI subset
  - `figures/NB03_chvi_phase_heatmap.png`
  - `figures/NB03_sigU_regulon_volcano.png`

### NB04 — Sphingolipid flux, CtpA, and the canonical Lpt apparatus

- **Goal**: Resolve H3 — confirm sphingolipid pathway is constitutive (not induced), CtpA upregulation is robust, and canonical Lpt apparatus is maintained or up. Cross-reference with OM proteome.
- **Approach**:
  1. Full sphingolipid biosynthesis + Uchendu transporter + CtpA expression panel: CPM, DE, and OM-proteome presence/abundance.
  2. Canonical Lpt apparatus (LptA-G, LptD/E, MsbA, the LptC-related CCNA_03716) expression and proteome.
  3. Compute coverage caveats (does the OM proteome detect any of these inner-membrane proteins?).
  4. Optional: AlphaFold structural overlay of CtpA vs LpxF (just inspection — no structural claim made).
- **Outputs**:
  - `data/NB04_sphingolipid_lpt_panel.csv` — combined transcript + protein evidence
  - `figures/NB04_sphingolipid_locus_heatmap.png`
  - `figures/NB04_lpt_apparatus_heatmap.png`
  - `figures/NB04_ctpA_per_strain.png`

### NB05 — Peptidoglycan remodeling (H4)

- **Goal**: Test whether PG-remodeling enzymes show coordinated upregulation in 4599. Compare to the *A. baumannii* PBP1A/Ldt route.
- **Approach**:
  1. Curate a PG-biosynthesis-and-remodeling gene set for Caulobacter from `dim_feature` description, COG, and PaperBLAST (PBPs, lytic transglycosylases SdpA/SdpB, Ldts, DD-carboxypeptidases, MurA-F).
  2. DE and OM-proteome behavior for each gene in 4584-vs-4580 and 4599-vs-4584.
  3. Cross-reference the *A. baumannii* PBP1A and LdtJ/LdtK orthologs in Caulobacter (paperBLAST + BLAST against canonical sequences).
- **Outputs**:
  - `data/NB05_pg_remodeling_panel.csv`
  - `figures/NB05_pg_remodeling_heatmap.png`

### NB06 — Comparative-species arm

- **Goal**: Why is this route uniquely Caulobacter? Catalogue presence/absence of the sphingolipid biosynthesis + transport locus, CtpA-like LpxF substitute, and the relevant Fur-released "critical" genes (from NB02) across *N. meningitidis*, *A. baumannii*, *M. catarrhalis*.
- **Approach**:
  1. Inventory BERDL genomes for the four species (`kbase_ke_pangenome` or similar — confirm in NB06).
  2. Build a presence/absence matrix for the focal gene sets (sphingolipid pathway, CtpA, Lpt apparatus, Fur-critical subset).
  3. Compare to the published alternative routes: *A. baumannii* PBP1A/LdtJ-LdtK (Kang 2021), *N. meningitidis* phospholipid + capsule (Steeghs 2001), *M. catarrhalis* late-acyltransferase (Gao 2008).
- **Outputs**:
  - `data/NB06_comparative_presence_absence.csv`
  - `figures/NB06_comparative_heatmap.png`

### NB07 — Figures and synthesis for REPORT.md

- **Goal**: Final figures (multi-panel where appropriate), and a structured findings summary for `/synthesize`.
- **Approach**: cross-reference NB01-06; build a 4-panel hypothesis summary; export to `figures/` ready for the report.

### Stop condition

Notebook execution proceeds through NB01 → NB06 → NB07. Plan revision triggered if NB01 (Fur-only signature) shows substantial disagreement with 4584-vs-4580 (e.g., the "Fur-released" signal we attributed to Δ*fur* is mostly Δ*sspB*), or if NB02 reveals no Fur-released gene with meaningful fitness phenotype (would weaken H2 substantially).

## Expected Outcomes

### Per hypothesis

| H | Supports H1 if … | Supports H0 if … | Caveats / confounders |
|---|---|---|---|
| H1 | ChvI-induced gene partition shows distinct early (cooperator) and late (consequence) cohorts; SigU regulon overlaps the late cohort | ChvI engagement is entirely correlated with general envelope stress without a phase structure | Stein/QY regulons are themselves overlapping (~30% of QY genes are in Stein); the ChvG-ChvI two-component circuit is itself co-regulated by other factors |
| H2 | A small (5-20 gene) Fur-released subset has strong RB-TnSeq fitness defects under iron-limitation, oxidative-stress, or envelope-stress conditions; the same subset is also induced in 4584-vs-4580 (and in Leaden Δ*fur*) | The Fur-released DEG set's fitness ranking is uniform — no enrichment of strong-phenotype genes vs background | FB conditions don't perfectly span "envelope stress"; some Fur-released genes are ncRNAs / unannotated and have no FB locus |
| H3 | Sphingolipid biosynthesis pathway is *not* induced; CtpA / CCNA_03113 is significantly up at FDR<0.05 at the transcript or protein level in 4599; canonical Lpt apparatus (MsbA-like, LptC-related, etc.) is maintained or up; OM proteome detects ≥3 sphingolipid-locus or Lpt-apparatus proteins | Sphingolipid pathway is induced (>2-fold) in 4584 or 4599; CtpA is not differentially regulated; canonical Lpt apparatus is down | OM proteome is single-replicate; CtpA borderline-significant in NB00 — needs the full proteome panel for a confident claim |
| H4 | ≥3 PG-remodeling enzymes show coordinated upregulation in 4599 at transcript or protein level | PG-remodeling enzymes show no coordinated direction | The Caulobacter PG-remodeling gene set isn't pre-curated; we'll have to define it from annotation + literature — risk of cherry-picking |

### Potential surprises

1. **A new ECF σ-factor / TCS not yet linked to envelope stress** could emerge from the top-DEG lists in 4599 (UrpR is already in the top 25 up; SigU likewise). NB03 will surface these explicitly.
2. **The "Fur-released critical subset"** might point at iron-homeostasis genes (TBDTs, ferritin/bacterioferritin, FrpB-like DUF4198 family), at sphingolipid-pathway accessory genes, or at completely uncharacterized loci. Genuine prior uncertainty.
3. **Comparative-species inventory** might reveal the sphingolipid biosynthesis locus IS present in one of the three non-Caulobacter species (most likely *A. baumannii* or *M. catarrhalis*) — which would weaken the "structurally unavailable" argument and require us to explain why it isn't used in those species.

## Confounders and limitations

- **The Δ*sspB* co-deletion is part of the published mechanism but adds analytical complexity.** NB01 (Leaden re-analysis) is the principal mitigation.
- **OM proteome is a single replicate per strain** — no per-protein statistics possible; we can only rank, never test. The colleague indicates more proteome replicates expected summer 2026.
- **CCNA locus tag normalization in Stein 2021** — 24/162 entries are gene symbols only, not CCNA tags; these are excluded from set-overlap analyses in NB03 (~15% data loss for the Stein set).
- **Single condition** (PYE rich-medium routine growth) — no iron-limitation, no envelope-stress, no oxidative-stress conditions in the colleague's RNA-seq. The Fur signal here is Δ*fur* (constitutive derepression), not a real iron-limitation response. The BERDL fitness data adds the multi-condition view that the transcriptome lacks.
- **Comparative-genomics arm depends on BERDL pangenome coverage** for the three non-Caulobacter species. If coverage is weak, we fall back to NCBI direct queries with explicit, named genomes.

## Revision History

- **v1** (2026-06-04): Initial plan. Reframed from the original "discover the mechanism" framing after Phase A literature review revealed Zik 2022 (PMID 35649364) as the published mechanism and identified `krr@berkeley.edu` as Kathleen R. Ryan, the senior author. H3 reframed from hopanoid substitution (PaperBLAST confirmed no Caulobacter hopanoid genes) to anionic-sphingolipid substitution (CPG). H4 added to capture peptidoglycan remodeling observed in NB00 (SdpA +4.8 log2 OM protein). Caulobacter RB-TnSeq fitness arm enabled (`kescience_fitnessbrowser` orgId='Caulo', 198 experiments).

## Authors

- Adam Arkin (University of California, Berkeley) — ORCID [0000-0002-4999-2931](https://orcid.org/0000-0002-4999-2931). Lead.
- Kathleen R. Ryan (UC Berkeley) — data provider and scientific collaborator; co-authorship pending publication discussion.
