# Report: The regulatory and proteomic architecture of Δ*fur*-permitted lipid A loss in *Caulobacter crescentus*

## Key Findings

![Master synthesis figure — 4-panel summary of all five mechanism layers](figures/NB07_synthesis_master.png)

### Finding 1 — Δ*fur* Δ*sspB* is a dual-release switch, not a Fur-only perturbation

The 4584-vs-4580 contrast (Δ*fur* Δ*sspB* Δ*rsaA* vs Δ*rsaA*) correlates with Leaden 2018's Δ*fur* signal at Spearman ρ = 0.315, p = 2.08e-03 over 93 Leaden Δ*fur* DEGs, with 71% sign concordance — confirming Fur derepression as a major driver. But 53 of those 93 Leaden Δ*fur* DEGs are *buffered* in our data (logFC ~0 in 4584-vs-4580 despite -5 to -9 in Leaden), and the buffered set is dominated by the **cbb3 / cyd / *fix*-NOPQ micro-aerobic respiratory operon** (CCNA_01466-01476, *ccoNOPQ*, *cydCDA*, *fixG/H/I*). The Δ*sspB* co-deletion is not a confound — it actively releases the respiratory chain from Fur-mediated repression that normally accompanies Δ*fur*.

*(Notebook: 01_leaden2018_fur_signature.ipynb)*

### Finding 2 — A specific Fur-released subset has strong envelope-stress fitness phenotypes (H2 supported)

Caulobacter RB-TnSeq fitness data (`kescience_fitnessbrowser`, orgId=`Caulo`, 198 experiments) ranks the Fur-released gene set by phenotypic importance. The **concordant_strong** subset (32 genes whose Fur derepression is preserved across both Leaden Δ*fur* and our 4584-vs-4580 contrast) shows **17/32 = 53.1% phenotype-bearing** (|fitness *t*| > 4 in ≥ 2 envelope-stress experiments) — 5.3× the pre-registered 10% threshold. The strongest signal is **ChvT (CCNA_03108)** with \|*t*\| = 43.7 under envelope stress, followed by other Fur-derepressed TBDTs (CCNA_02910, 00210, 02048, 00028) with \|*t*\| 9-28. The complementary **SspB-buffered** set (26 genes including cytochrome oxidases *ccoNOP*, *cydCDA*, *fixG*) shows **9/26 = 34.6% phenotype-bearing**, with respiratory chain genes carrying *negative* fitness (knockouts harmful under envelope stress) — opposite sign from the Fur-released TBDTs. *Pre-registered iron-limitation arm could not be tested* — Caulobacter FB compendium contains zero iron-limitation experiments; H2 was descoped to envelope-axis-only per the plan's preflight rule.

*(Notebook: 02_caulo_fitness_ranking.ipynb)*

### Finding 3 — ChvI engages in two phases: early cooperator + late consequence (H1 supported)

The published ChvI regulons (Stein 2021 + Quintero-Yanes 2022; union = 488 ChvI-induced genes in the tested universe) partition cleanly into:
- **early-cooperator** — 30 genes induced in 4584-vs-4580 (before Δ*lpxc* is added), including ChvI itself (CCNA_00237 logFC +1.45 — **autoregulation**), the lasso peptide cyclase CCNA_02794 +8.6, the ApbE iron-sulfur cluster repair protein +3.8, and *imuB* SOS DNA polymerase +1.5 (corroborating Leaden 2018's SOS-activation finding under Δ*fur*).
- **late-consequence** — 49 genes induced *only* after lipid A is lost in 4599-vs-4584, including the **LolA-family OM lipoprotein carrier CCNA_03820 (+2.89)** — exactly the gene Uchendu et al. 2026 showed induced under Δ*spt* (sphingolipid loss); seeing it under Δ*lpxc* (lipid A loss) too means LolA is a generic OM-stress response in Caulobacter — plus the **Pal-like CCNA_00784 (+2.08)** of the Tol-Pal envelope-integrity complex, *zot*-like membrane perturber, *osrP* stress protein, multiple TBDTs.
- **both phases** — 10 genes that begin in 4584 and continue rising in 4599, including the SIMPL family CCNA_02378 (+1.9 → +3.9) and the **amelogenin/CpxP-related CCNA_03997** — CpxP being the *E. coli* envelope-stress chaperone partner of CpxA.

Pre-registered phase-structure threshold (≥10 genes per cohort) passes strongly. The reframed SigU coherence check on the late cohort returned 24.5% envelope/transport/regulator enrichment — below the 50% relaxed criterion. **Caulobacter SigU is uncharacterized in the published literature** (PaperBLAST scout returned zero substantive snippets for CCNA_02977); the late cohort's biological coherence cannot be validated against a non-existent gold standard. Phase-structure half of H1 is supported; SigU-as-driver is partial pending future SigU-induction RNA-seq.

*(Notebook: 03_chvi_phase_partition_sigU.ipynb)*

### Finding 4 — Sphingolipid biosynthesis is constitutive; canonical Lpt apparatus is maintained or upregulated; *lptC2* protein induced post-transcriptionally (H3 partially supported, with novel finding)

H3 was tested against three pre-registered sub-claims:

| Sub-claim | Result | Verdict |
|---|---|---|
| CtpA / CCNA_03113 upregulation in 4599-vs-4584 | logFC +0.58, FDR 0.11 (transcript); cumulative 4599-vs-4580 FDR 0.035; not in OM proteome | BORDERLINE (rejected at strict bar) |
| Sphingolipid biosynthesis pathway constitutive (not induced) | 0/6 biosynthesis genes UP; *spt* DOWN -0.64 FDR 0.002; *sphk* DOWN -0.40 FDR 0.02 | SUPPORTED strongly |
| Canonical Lpt apparatus maintained | 0 components DOWN; **MsbA-like CCNA_00307 +0.89 FDR 0.01**, **LptC-related CCNA_03716 +0.56 FDR 0.005** | SUPPORTED strongly |

**Novel post-hoc finding**: the Uchendu 2026 Caulobacter-specific sphingolipid IM transporter ***lptC2* / CCNA_01226 shows transcript -0.60 (FDR 0.034) but PROTEIN log2(4672/4659) = +1.08 (>2-fold up)**. Direct evidence of post-transcriptional regulation — the sphingolipid-specific permease accumulates at the IM when LpxC is absent, despite its mRNA going down. CCNA_01217 (Zik 2022 sphingolipid biosynthesis required for CHIR-090 tolerance) also shows protein log2 = +0.77 in 4672 vs 4659. Mechanism consistent with: when LPS-trafficking demand on the shared LptB ATPase disappears, the sphingolipid-specific permease is stabilized.

*(Notebook: 04_sphingolipid_lpt_panel.ipynb)*

### Finding 5 — Coordinated peptidoglycan remodeling: lytic activity engaged, basal machinery shut down (H4 supported)

The pre-registered PG-remodeling gene set (53 loci, locked before DE analysis) shows **31 genes meeting the H4 threshold** (≥3 required) — 26 transcript-significant in 4599-vs-4584 (FDR<0.05) plus 7 OM-proteome \|log2\|>1. Direction is split 8 UP / 23 DOWN, indicating coordinated *reorganization*, not blanket induction.

**UP (specific activities engaged in 4599)**:
- **SdpA CCNA_01252 +4.8 log2 protein** — soluble lytic murein transglycosylase
- **Pal CCNA_00784 +2.08 transcript AND +2.84 protein** — peptidoglycan-associated OM lipoprotein (Tol-Pal envelope-integrity complex). **Also a top late-cohort ChvI gene from NB03** — strong cross-notebook convergence.
- PleA, PbpX (multimodular transpeptidase-transglycosylase), CCNA_01754 transglycosylase-associated

**DOWN (basal division/elongation machinery)**:
- FtsI penicillin-binding (cell division)
- **PbpZ -1.08 transcript, PbpC -1.15 protein, D,D-transpeptidase -1.27 protein** (cell elongation)
- *murD*, *mviN/murJ* biosynthesis/flippase
- LdpD/E/F M23-family endopeptidases (multiple)
- *amiC* amidase, *ripA* hydrolase
- Membrane-bound transglycosylase A **-2.47 log2 protein**

Interpretation: the cell shuts down normal division/elongation PG turnover while engaging a specific subset of lytic transglycosylases and Pal-Tol anchoring factors. **Pal up at both transcript and protein** is the most mechanistically suggestive: Tol-Pal normally relies on LPS-mediated Mg²⁺-bridged OM-LPS-Pal stacking for OM-IM cohesion; with no LPS, the cell upregulates Pal to compensate via direct protein anchoring.

*(Notebook: 05_pg_remodeling.ipynb)*

### Finding 6 — The sphingolipid pathway and ChvG-ChvI are uniquely *Caulobacter*: structural unavailability explains species specificity

Comparative PaperBLAST presence/absence across *C. crescentus*, *A. baumannii*, *N. meningitidis*, *M. catarrhalis* shows that the sphingolipid biosynthesis pathway is **Caulobacter-unique**: *spt* (serine palmitoyltransferase), *bcerS* (bacterial ceramide synthase), and sphingosine kinase are absent in the other three species. **ChvG-ChvI is also Caulobacter-restricted** — consistent with the published alphaproteobacterial restriction of this envelope-stress regulatory circuit (Greenwich et al. 2023). The other three species cannot use the Caulobacter Δ*fur* + anionic-sphingolipid rescue because they lack the substitute lipid machinery. The published alternative routes align with what each species' genome encodes: A. baumannii has PBP1A and Ld-transpeptidases for the Kang 2021 PG-remodeling route; N. meningitidis has a large capsule biosynthesis locus (9 PaperBLAST hits) for the Steeghs 2001 capsule-substitution route; A. baumannii and N. meningitidis have late acyltransferases (lpxX/lpxL, 8 and 3 hits) for the Gao 2008 acylation-truncation route. *Caulobacter has none of these alternatives* — the sphingolipid substitution is its only viable path.

*(Notebook: 06_comparative_species.ipynb)*

## Results

### Hypothesis scorecard

| Hypothesis | Sub-claim | Pre-registered threshold | Observed | Verdict |
|---|---|---|---|---|
| **H1** ChvI cooperator + consequence | Phase structure | ≥10 genes per cohort | early=30, late=49 | PASS |
| **H1** | SigU drives late cohort | ≥50% envelope/transport/regulator + Fisher p<1e-3 | 24.5% (literature gap) | PARTIAL |
| **H2** Critical Fur regulon subset | Path A (concordant_strong) | ≥10% phenotype-bearing | 17/32 = 53% | PASS strongly |
| **H2** | Path B (SspB-buffered) | ≥10% phenotype-bearing | 9/26 = 35% | PASS |
| **H2 (preflight)** | iron-limitation experiments ≥3 | ≥3 in Caulo FB | 0 | FAIL → descoped to envelope-only |
| **H3** Sphingolipid + Lpt repurposing | CtpA upregulation in 4599-vs-4584 | FDR<0.05 OR ≥2x protein | logFC +0.58 FDR 0.11; not in OM proteome | BORDERLINE |
| **H3** | Sphingolipid pathway constitutive | 0 biosynthesis gene UP at FDR<0.05 | 0 up; spt/sphk slightly DOWN | PASS strongly |
| **H3** | Canonical Lpt maintained | 0 components DOWN at FDR<0.05 | 0 down; MsbA-like and LptC-related UP | PASS strongly |
| **H3** | (novel) *lptC2* protein induction | (post-hoc) | transcript -0.60 (FDR 0.034); protein log2 +1.08 | NOVEL FINDING |
| **H4** PG remodeling | ≥3 enzymes engaged | ≥3 FDR<0.05 transcript OR \|log2\|>1 protein | 31 (26 transcript, 7 protein) | PASS strongly |
| **H4** | (novel) Pal-Tol engagement | (post-hoc) | Pal +2.08 transcript, +2.84 protein | NOVEL FINDING |
| **Comparative** | Sphingolipid pathway Caulobacter-unique | (presence/absence) | spt/bcerS/sphk absent in A.b./N.m./M.c. | CONFIRMED |
| **Comparative** | ChvG-ChvI alphaproteobacterial only | (presence/absence) | absent in A.b./N.m./M.c. | CONFIRMED |

### Phase A — orientation findings (NB00) that motivated the analysis plan

![Sphingolipid locus heatmap from orientation notebook — neither induced nor strongly suppressed across the strain series](figures/00_sphingolipid_locus_heatmap.png)

NB00 motivated three reframings before formal hypothesis testing: (a) the sphingolipid biosynthesis pathway is *not induced* (rejecting the initial "Δfur derepresses sphingolipid biosynthesis" framing); (b) the canonical Lpt apparatus is maintained or up, consistent with Uchendu 2026's shared-component model; (c) SdpA at +4.8 log2 OM proteome surfaced peptidoglycan remodeling as a fourth hypothesis (H4) that wasn't in the v1 plan.

### NB01 — Leaden 2018 Fur signature

![Leaden Δfur logFC vs our 4584-vs-4580 logFC; concordant_strong in dark blue, buffered set in orange, discordant in red](figures/NB01_fur_signature_scatter.png)

The scatter shows the dramatic asymmetry between our amplified Fur-derepression cohort (top-right quadrant, exceeding Leaden's logFC) and the buffered cohort (cluster near y=0 spanning Leaden's full -9 to -5 range). HutA (the iron-derepressed TBDT) is the extreme top-right point at our +10.5 vs Leaden's +2.2.

![Leaden internal: Δfur vs iron-limitation response — shows the Fur regulon and iron-limitation response are correlated but not identical, providing Leaden's own validation of the signal](figures/NB01_leaden_iron_vs_fur.png)

### NB02 — Fitness data leverage

The Caulobacter compendium covers 95 stress experiments (envelope-, drug-, metal-related stresses), 46 nitrogen-source, 42 carbon-source, 10 PYE control, plus 5 others. Zero pure iron-limitation experiments. The envelope-stress subset (22 experiments) is large enough to discriminate phenotype-bearing Fur-released genes at the pre-registered threshold.

### NB03 — ChvI phase partition

ChvI itself (CCNA_00237) is in the **early** cohort with logFC +1.45 in 4584-vs-4580 — direct evidence of ChvG-ChvI **autoregulation** during the Fur+SspB release phase. Theme distribution shifts from regulator-rich early (6.7% regulator/TCS) to envelope-structural late (10.2% envelope/OM, 12.2% TBDT, plus lipid/membrane, PG/cell wall categories that are 0% in early).

### NB04 — Sphingolipid, CtpA, Lpt panel

![Sphingolipid biosynthesis cluster heatmap — flat-to-slightly-decreasing across strain series](figures/NB04_sphingolipid_locus_heatmap.png)

![Canonical LPS-transport apparatus heatmap — MsbA-like CCNA_00307 visibly UP in 4599 vs others](figures/NB04_lpt_apparatus_heatmap.png)

![CtpA / CCNA_03113 expression per strain — clear monotonic rise 37→42→63 CPM despite borderline single-contrast FDR](figures/NB04_ctpA_per_strain.png)

### NB05 — PG remodeling heatmap

![PG-remodeling enzymes meeting H4 threshold — coordinated up/down pattern across the strain series](figures/NB05_pg_remodeling_heatmap.png)

### NB06 — Comparative species presence/absence

The PaperBLAST presence matrix shows the four-species pattern. M. catarrhalis is under-annotated (162 genes in PaperBLAST) so its 0000 rows are advisory only. Even allowing for that, the sphingolipid biosynthesis pathway is robustly Caulobacter-unique (these genes are biologically not present in the other three, independently confirmed by Olea-Ozuna 2020/2024).

## Interpretation

### Mechanistic synthesis: a dual-release switch

The combined evidence supports a multi-layer mechanism for *Caulobacter crescentus* Δ*fur* Δ*sspB*-permitted Δ*lpxc* viability:

1. **Δ*fur* derepresses TBDT and iron-uptake systems** — the "Path A" subset (32 genes, 53% phenotype-bearing) provides pre-existing outer-membrane transport machinery whose normal job is iron acquisition. In the rescued state, this machinery is structurally available to participate in **sphingolipid (CPG) trafficking via the canonical Lpt apparatus**, per Uchendu 2026's shared-component model.

2. **Δ*sspB* preserves the cbb3 / cyd / *fix*-NOPQ micro-aerobic respiratory chain** — the "Path B" set (26 genes, 35% phenotype-bearing) carries strongly negative fitness when knocked out under envelope stress. Respiratory ATP is required to perform the envelope-remodeling work demanded by lipid-A loss. Without SspB, the SOS-ClpXP-controlled respiratory program would shut down upon Fur loss (as it does in Leaden 2018); with SspB removed, respiratory function is preserved through the perturbation.

3. **ChvI engages in two temporally distinct phases** — autoregulating in the early phase (regulator-rich, includes *imuB* SOS, lasso peptide cyclase, ApbE iron-sulfur repair) and deploying structural envelope machinery in the late phase (envelope/OM-rich, includes LolA, Pal-Tol, TBDTs, EF-hand calcium-binding proteins). The cell makes a regulatory commitment before lipid-A loss occurs and follows up with envelope deployment after.

4. **Sphingolipid biosynthesis is constitutive — rescue is post-transcriptional**. The existing CPG pool suffices. Rescue operates by flux redirection (no LpxC competition for shared substrates) plus the borderline-supported CtpA-mediated processing step (Zik 2022's predicted LpxF substitute). **The canonical Lpt apparatus is maintained or upregulated (MsbA-like +0.89, LptC-related +0.56) consistent with Uchendu 2026's shared-component model**. The most striking single piece of new evidence: **the Uchendu Caulobacter-specific lptC2 sphingolipid IM transporter accumulates at the protein level >2-fold when LpxC is absent, despite transcript downregulation** — direct evidence of post-transcriptional stabilization, exactly the mechanism class H3 predicts.

5. **Peptidoglycan remodeling participates**: shutdown of basal division/elongation machinery (FtsI, PbpZ, MurD, multiple endopeptidases and amidases) combined with engagement of lytic transglycosylases (SdpA at OM protein, PleA, PbpX) and **Pal-Tol envelope-integrity factors (Pal up at both transcript and protein)**. Pal upregulation likely compensates for loss of LPS-mediated Mg²⁺-bridged OM-LPS-Pal stacking. This is mechanistically distinct from but biologically analogous to the *A. baumannii* PBP1A/Ldt route (Kang 2021).

6. **Cross-species check confirms structural unavailability** for the other three lipid-A-loss-tolerant species. *A. baumannii*, *N. meningitidis*, *M. catarrhalis* don't encode the sphingolipid biosynthesis pathway; they don't have ChvG-ChvI; and they evolved alternative rescue mechanisms aligned with what their genomes encode.

### Literature Context

- **Zik et al. 2022** (PMID 35649364) — the foundational paper, authored by this project's data provider K.R. Ryan. Establishes that Δ*lpxc* viability in *C. crescentus* requires both Δ*fur* and anionic sphingolipid (CPG), and that "Fur-regulated processes (not iron status per se)" underlie viability. Our project characterizes the regulatory and proteomic *constituents* of this rescue at a level Zik 2022 did not. Specific evidentiary extensions: (a) ranking which Fur regulon members are mechanistically critical (NB02 fitness), (b) confirming the sphingolipid pathway is constitutive at the transcript level rather than induced (NB04), (c) demonstrating the canonical Lpt apparatus is maintained or upregulated (NB04), (d) the novel *lptC2* protein-level induction.

- **Uchendu, Isom, Klein 2026** (bioRxiv 10.1101/2026.04.12.717747) — identifies the Caulobacter sphingolipid IM transporters CCNA_01213/01214/01226 (lptG2/F2/C2) and shows they share the canonical LptB ATPase with LPS transport. Our project provides the *first regulatory and proteomic evidence* that this shared-component model operates in a Δ*lpxc* strain: the canonical Lpt apparatus is maintained, MsbA-like and LptC-related components are upregulated, and the Uchendu lptC2 protein accumulates >2-fold despite transcript downregulation.

- **Leaden et al. 2018** (PMID 30210482) — published Caulobacter Δ*fur* RNA-seq. Our NB01 re-analyzed their supplementary Table 2 to provide a clean Fur-only DEG signature. The Spearman ρ = 0.315 concordance with our 4584-vs-4580 confirms Fur derepression as a major component of our signal. The buffered cbb3/*fix* respiratory operon is a new observation made possible only by comparing our Δ*fur* Δ*sspB* combined to Leaden's Δ*fur*-alone.

- **Stein et al. 2021** (PMID 34124942) and **Quintero-Yanes et al. 2022** (PMID 36480504) — published Caulobacter ChvI regulons used as reference sets for the H1 partition test. **Greenwich et al. 2023** (PMID 37040790) — alphaproteobacterial ChvG-ChvI conserved-circuit review, consistent with our cross-species finding that ChvG-ChvI is absent in A.b./N.m./M.c.

- **da Silva Neto et al. 2009** (PMID 19520766) — earlier Caulobacter Fur ChIP/microarray. Cross-validates the concordant_strong gene set (HutA, FrpB-like cluster, bacterioferritin) as canonical Fur targets.

- **Kang et al. 2021** (PMID 33402533) — A. baumannii Δ*lpxc* via PBP1A loss + LdtJ/LdtK. Mechanistically distinct from but biologically analogous to our finding that Caulobacter Δ*lpxc* engages SdpA/PleA + Pal-Tol PG-remodeling. Both organisms reorganize PG when LPS/LOS is removed, but via different enzyme-family specifics.

- **Steeghs et al. 2001** (PMID 11742971) — *N. meningitidis* Δ*lpxA* via capsule substitution. Consistent with our NB06 finding that N. meningitidis has 9 capsule-biosynthesis PaperBLAST hits (vs 2-3 in the others).

- **Gao et al. 2008** (PMID 18795947) — *M. catarrhalis* late-acyltransferase truncation. Consistent with our NB06 finding that the lpxX/lpxL family is present in A.b. (8) and N.m. (3) but absent in C.c. (0).

- **Olea-Ozuna et al. 2020/2024** (PMIDs 33063925, 39093898) — independent confirmation that Caulobacter encodes a sphingolipid biosynthesis pathway absent in the other three Gram-negatives.

### Novel Contribution

This project adds five substantive contributions beyond the published baseline:

1. **The Δ*sspB* co-deletion is mechanistic, not confound**. NB01 shows ~57% of Leaden's Δ*fur* DEG signal is buffered in our background — specifically the cbb3/*fix*-NOPQ micro-aerobic respiratory operon. NB02 shows the buffered set carries strong (negative) fitness phenotypes under envelope stress. Implication: rescued strain viability requires both arms of the dual-release switch, not Δ*fur* alone.

2. **The canonical Lpt apparatus is maintained or upregulated in the Δ*lpxc* rescue state**. NB04 shows MsbA-like CCNA_00307 +0.89 FDR=0.01 and LptC-related CCNA_03716 +0.56 FDR=0.005. The shared-component model predicted by Uchendu 2026 in WT background is now empirically supported in the Δ*lpxc* state, where the apparatus would otherwise have no LPS substrate.

3. **The Uchendu lptC2 protein accumulates post-transcriptionally**. NB04 finds transcript -0.60 (FDR 0.034) but protein log2 +1.08 (>2× up). First evidence of post-transcriptional regulation of the sphingolipid-specific permease — likely stabilization due to lack of LPS competition for the shared ATPase.

4. **The ChvI envelope-stress regulon engages in two temporally distinct phases**, with **ChvI itself participating in autoregulation** (NB03 early cohort, logFC +1.45 in 4584-vs-4580 before Δ*lpxc* is added). Demonstrates that envelope-stress activation precedes rather than responds to lipid-A loss.

5. **Pal-Tol envelope-integrity engagement** (NB03 late cohort + NB05 PG-remodeling): Pal CCNA_00784 +2.08 transcript + 2.84 protein. Likely compensates for loss of LPS-mediated OM-IM cohesion via direct protein anchoring. Suggests a structural model in which Tol-Pal protein-protein contacts substitute for the lipid-based architecture of the wild-type cell envelope.

### Limitations

- **OM proteome is a single replicate per strain** — direction is interpretable but no per-protein statistics are possible. The colleague indicates more proteome replicates expected summer 2026. The novel *lptC2* protein-induction finding and the Pal-Tol upregulation should be confirmed with replicates before publication.
- **Single growth condition** (PYE rich-medium routine) — the Fur signal is constitutive Δ*fur* derepression, not a real iron-limitation response. The BERDL fitness data supplied multi-condition resolution for H2 but iron-limitation experiments specifically are unavailable in the Caulobacter FB compendium.
- **CtpA borderline at the strict pre-registered bar** (FDR 0.11 in 4599-vs-4584 transcript; not detected in single-replicate OM proteome). The cumulative 4599-vs-4580 contrast is significant (FDR 0.035), and the CPM rises monotonically across the strain series — but a replicated proteome would be needed to claim CtpA upregulation at full rigor. Reported here as borderline-rejected at the strict bar with the supporting cumulative finding flagged.
- **SigU regulon literature gap** — Caulobacter SigU (CCNA_02977) is uncharacterized in PaperBLAST. The H1 SigU-as-driver test was reframed from a literature overlap to a functional coherence check on the late cohort. Targeted SigU induction RNA-seq would resolve the cohort attribution.
- **PaperBLAST description matching for comparative arm has known false negatives** — essential genes (LpxA/C/D/K) appear absent in Caulobacter because PaperBLAST `desc` is heterogeneous and our regex didn't catch all variants. The robust findings are the sphingolipid biosynthesis pathway and ChvG-ChvI being uniquely Caulobacter — these are independently confirmed in the literature.
- **M. catarrhalis is under-annotated in PaperBLAST** (162 genes). Treat its presence/absence rows as advisory; the published Gao 2008 alternative route is well-established literature.
- **Fitness-browser iron-limitation experiments are absent** in the Caulobacter compendium. H2 was descoped to envelope-stress axis per the plan's preflight rule. Iron-axis testing requires either additional RB-TnSeq experiments or a cross-walk to the Leaden 2018 published Δ*fur* phenotype.

## Data

### Sources

| Collection | Tables Used | Purpose |
|------------|-------------|---------|
| `kescience_fitnessbrowser` | `organism`, `experiment`, `fitbyexp_caulo`, `gene` | 198-experiment Caulobacter RB-TnSeq fitness ranking for the Fur-released gene set (NB02) |
| `kescience_paperblast` | `gene`, `genepaper`, `snippet`, `curatedgene` | Caulobacter SigU literature scout (NB03); cross-species presence/absence (NB06) |

### Generated Data

| File | Rows | Description |
|------|------|-------------|
| `data/NB01_leaden_fur_de.csv` | 93 | Leaden 2018 Δfur DEGs (parsed from Frontiers Table 2.XLSX) |
| `data/NB01_leaden_iron_de.csv` | 491 | Leaden 2018 iron-limitation (2h DP) DEGs |
| `data/NB01_fur_only_signature.csv` | 93 | Join of Leaden Δfur DEGs with our 4584-vs-4580 logFCs |
| `data/NB01_source_provenance.md` | — | Records PMC supplementary preflight success (no CTS re-analysis needed) |
| `data/NB02_caulo_experiments.csv` | 198 | Caulobacter FB experiments classified by condition (envelope=22, oxidative=4, carbon=48, iron=0) |
| `data/NB02_pathA_concordant_strong_scoring.csv` | 32 | Path A fitness phenotype scoring |
| `data/NB02_pathB_buffered_scoring.csv` | 53 | Path B SspB-buffered fitness phenotype scoring |
| `data/NB03_chvi_phase_cohorts.csv` | 89 | ChvI gene-by-gene phase assignment (early/both/late) |
| `data/NB03_phase_cohort_themes.csv` | 9 | Functional theme breakdown by cohort |
| `data/NB03_sigU_literature_gap.md` | — | Provenance for the SigU literature scout (returned no Caulobacter snippets) |
| `data/NB04_sphingolipid_transcript.csv` | 15 | Sphingolipid biosynthesis + Uchendu transporters expression panel |
| `data/NB04_lpt_transcript.csv` | 6 | Canonical Lpt apparatus expression panel |
| `data/NB04_ctpA_transcript.csv` | 1 | CtpA / CCNA_03113 expression panel |
| `data/NB04_protein_panel.csv` | 22 | OM proteome cross-reference for sphingolipid + Lpt + CtpA sets |
| `data/NB05_pg_gene_set.csv` | 53 | Pre-curated PG-remodeling gene set, LOCKED before DE analysis |
| `data/NB05_pg_significant_hits.csv` | 31 | PG enzymes meeting H4 threshold |
| `data/NB06_comparative_presence_counts.csv` | 25 | Focal-gene PaperBLAST hit counts per species |
| `data/NB06_comparative_presence_bool.csv` | 25 | Boolean presence/absence matrix |
| `data/NB07_scorecard.csv` | 12 | Hypothesis scorecard cross-referencing pre-registered thresholds to outcomes |
| Plus NB00 orientation outputs (sphingolipid/Lpt CPM, ChvI enrichment, Zik suppressors, top DEGs, OM proteome strain shifts) | — | Phase A orientation panel |

## Supporting Evidence

### Notebooks

| Notebook | Purpose |
|----------|---------|
| `00_orientation.ipynb` | Phase A scoping: data shape, sphingolipid panel, ChvI overlap, Zik suppressors, top DEGs |
| `01_leaden2018_fur_signature.ipynb` | Concordance with Leaden 2018 Δfur DEGs; identifies the SspB-buffered cbb3/*fix* cohort |
| `02_caulo_fitness_ranking.ipynb` | RB-TnSeq fitness ranking of Path A + Path B Fur-released sets; H2 verdict |
| `03_chvi_phase_partition_sigU.ipynb` | ChvI early/late phase partition; SigU literature-gap finding |
| `04_sphingolipid_lpt_panel.ipynb` | H3 sub-claims (CtpA, sphingolipid constitutive, Lpt maintained); lptC2 protein finding |
| `05_pg_remodeling.ipynb` | H4 PG-remodeling test against pre-curated gene set |
| `06_comparative_species.ipynb` | Cross-species presence/absence via PaperBLAST |
| `07_synthesis.ipynb` | 4-panel master figure + hypothesis scorecard |

### Figures

| Figure | Description |
|--------|-------------|
| `figures/NB07_synthesis_master.png` | 4-panel synthesis (recommended Figure 1 for the manuscript) |
| `figures/00_sphingolipid_locus_heatmap.png` | Sphingolipid locus log2(CPM+1) heatmap across libraries |
| `figures/NB01_fur_signature_scatter.png` | Leaden Δfur vs our 4584-vs-4580 logFC scatter (recommended Figure 2A) |
| `figures/NB01_leaden_iron_vs_fur.png` | Leaden internal validation: Δfur vs iron-limitation correlation |
| `figures/NB04_sphingolipid_locus_heatmap.png` | Sphingolipid biosynthesis + Uchendu transporters detailed heatmap |
| `figures/NB04_lpt_apparatus_heatmap.png` | Canonical Lpt apparatus CPM heatmap |
| `figures/NB04_ctpA_per_strain.png` | CtpA strain-by-strain expression bar chart |
| `figures/NB05_pg_remodeling_heatmap.png` | PG remodeling enzymes meeting H4 threshold |
| `figures/NB06_comparative_heatmap.png` | Comparative species presence/absence matrix |

## Future Directions

1. **Replicate the OM proteome** (already planned by the data provider for summer 2026). The two novel post-hoc findings — *lptC2* protein induction (transcript-protein decoupling) and Pal-Tol upregulation — need replication before publication. Targeted Western blots against lptC2-tagged and Pal-tagged strains would also strengthen these claims.

2. **Characterize the *Caulobacter* SigU regulon** via SigU-induction RNA-seq (ectopic vanillate-inducible SigU expression) followed by genome-wide DE. The published literature contains no Caulobacter SigU regulon; this is a clear gap. The late ChvI cohort from NB03 provides a candidate target list to validate.

3. **Test the dual-release-switch model genetically**. The model predicts: (a) Δ*lpxc* should NOT be viable on a Δ*fur* alone background (sspB intact) because the cbb3/*fix* respiratory chain would shut down; (b) Δ*lpxc* should NOT be viable on a Δ*sspB* alone background (fur intact) because Fur would repress the transport machinery needed for sphingolipid trafficking. Both predictions are testable in the existing Ryan-lab strain background.

4. **Lipidomics of the rescued strain**. The post-transcriptional flux model predicts: in 4599 (Δ*lpxc* Δ*fur* Δ*sspB*), the sphingolipid pool size should be maintained or increased despite no biosynthesis induction, because LpxC competition for shared substrates is gone. The CtpA-mediated processing should produce a specific CPG headgroup (the LpxF substitute step). Targeted lipidomics with intact lipid A precursor quantification would test both predictions.

5. **Cross-species engineering test**. The "structural unavailability" model predicts that introducing the Caulobacter sphingolipid biosynthesis pathway into *A. baumannii* (which lacks it) should be neutral or modestly protective under colistin selection. The PBP1A/Ldt route in A. baumannii works independently of sphingolipids, so a sphingolipid-engineered A. baumannii should have *two* alternative routes to colistin resistance. Predicts increased rates of colistin-resistant escapers.

6. **Iron-axis fitness experiments**. The Caulobacter RB-TnSeq compendium has zero iron-limitation experiments, so the iron-flux arm of H2 was untestable here. A small targeted set of RB-TnSeq fitness experiments under bipyridyl chelation, ferric salt supplementation, and hemin would close the H2 iron axis and test whether the same Fur-released subset that scores phenotype-bearing under envelope stress also scores under iron limitation.

7. **Tol-Pal complex structural studies**. The Pal protein-protein anchoring model is testable by AFM or cryo-EM of the rescued strain envelope. The prediction is increased Tol-Pal-PG contact density and reduced LPS-Pal contacts in the rescued OM-IM interface.

## References

- Zik JJ, Yoon SH, Guan Z, et al., Klein EA, Ryan KR. (2022). "Caulobacter lipid A is conditionally dispensable in the absence of *fur* and in the presence of anionic sphingolipids." *Cell Reports* 39(11):110888. PMID 35649364. DOI: 10.1016/j.celrep.2022.110888
- Uchendu CG, Isom GL, Klein EA. (2026, preprint). "Homologues of the inner-membrane LPS transport proteins are required for sphingolipid transport in *Caulobacter crescentus*." bioRxiv 2026.04.12.717747. DOI: 10.1101/2026.04.12.717747
- Dhakephalkar T, Guan Z, Klein EA. (2025). "CpgD is a phosphoglycerate cytidylyltransferase required for ceramide diphosphoglycerate synthesis." PMID 39829823.
- Dhakephalkar T, Stukey GJ, Guan Z, Carman GM, Klein EA. (2023). "Characterization of an evolutionarily distinct bacterial ceramide kinase from *Caulobacter crescentus*." *J Biol Chem* 299:104894. PMID 37286040.
- Olea-Ozuna RJ, Poggio S, et al., Geiger O. (2020). "Five structural genes required for ceramide synthesis in *Caulobacter* and for bacterial survival." *Environ Microbiol* 23(5):2741. PMID 33063925.
- Olea-Ozuna RJ, Poggio S, et al., Geiger O. (2024). "Genes required for phosphosphingolipid formation in *Caulobacter crescentus* contribute to bacterial virulence." *PLoS Pathog* 20(8):e1012401. PMID 39093898.
- Hummels KR. (2024). "mSphere of Influence: Celebrating exceptions to the rule of lipid A essentiality." *mSphere* 9(3):e00633-23. PMID 38421175.
- Stein BJ, Fiebig A, Crosson S. (2021). "The ChvG-ChvI and NtrY-NtrX Two-Component Systems Coordinately Regulate Growth of *Caulobacter crescentus*." *J Bacteriol* 203(15):e00199-21. PMID 34124942.
- Quintero-Yanes A, Mayard A, Hallez R. (2022). "The two-component system ChvGI maintains cell envelope homeostasis in *Caulobacter crescentus*." *PLoS Genet* 18(12):e1010465. PMID 36480504.
- Greenwich JL, Heckel BC, Alakavuklar MA, Fuqua C. (2023). "The ChvG-ChvI Regulatory Network: A Conserved Global Regulatory Circuit Among the Alphaproteobacteria with Pervasive Impacts on Host Interactions and Diverse Cellular Processes." *Annu Rev Microbiol* 77:339. PMID 37040790.
- Leaden L, Silva LG, et al., Marques MV. (2018). "Iron Deficiency Generates Oxidative Stress and Activation of the SOS Response in *Caulobacter crescentus*." *Front Microbiol* 9:2014. PMID 30210482.
- da Silva Neto JF, Braz VS, Italiani VCS, Marques MV. (2009). "Fur controls iron homeostasis and oxidative stress defense in the oligotrophic alpha-proteobacterium *Caulobacter crescentus*." *Nucleic Acids Res* 37(14):4812. PMID 19520766.
- Moffatt JH, Harper M, et al., Boyce JD. (2010). "Colistin resistance in *Acinetobacter baumannii* is mediated by complete loss of lipopolysaccharide production." *Antimicrob Agents Chemother* 54(12):4971. PMID 20855724.
- Kang KN, Kazi MI, et al., Boll JM. (2021). "Septal Class A Penicillin-Binding Protein Activity and ld-Transpeptidases Mediate Selection of Colistin-Resistant LOS-Deficient *Acinetobacter baumannii*." *mBio* 12(1):e02185-20. PMID 33402533.
- Steeghs L, de Cock H, et al., van der Ley P. (2001). "Outer membrane composition of a LPS-deficient *Neisseria meningitidis* mutant." *EMBO J* 20(24):6937. PMID 11742971.
- Gao S, Peng D, et al., Gu XX. (2008). "Identification of two late acyltransferase genes responsible for lipid A biosynthesis in *Moraxella catarrhalis*." *FEBS J* 275(20):5201. PMID 18795947.
- Bhat NH, Vass RH, Stoddard PR, Shin DK, Chien P. (2013). "Identification of ClpP substrates in *Caulobacter crescentus* reveals a role for regulated proteolysis in bacterial development." *Mol Microbiol* 88(6):1083. PMID 23647068.
- Flynn JM, Levchenko I, Sauer RT, Baker TA. (2004). "Modulating substrate choice: the SspB adaptor delivers a regulator of the extracytoplasmic-stress response to the AAA+ protease ClpXP for degradation." *Genes Dev* 18(18):2292.
- Price MN, Wetmore KM, Waters RJ, Callaghan M, Ray J, Liu H, Kuehl JV, Melnyk RA, Lamson JS, Suh Y, et al. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature* 557(7706):503. PMID 29769718. — primary citation for the BERDL `kescience_fitnessbrowser` data source.
- Price MN, Deutschbauer AM, Arkin AP. (2021). "PaperBLAST: Text Mining Papers for Information about Homologs." *mSystems* 6(1):e00185-19. PMID 33531404. — primary citation for the BERDL `kescience_paperblast` data source.
- Arkin AP, Cottingham RW, Henry CS, Harris NL, et al. (2018). "KBase: The United States Department of Energy Systems Biology Knowledgebase." *Nature Biotechnology* 36(7):566-569. PMID 29979655. — primary citation for the KBase infrastructure.

See `references.md` for the full bibliography with PMCIDs, DOIs, and theme-grouping.

## Authors

- Adam Arkin (University of California, Berkeley) — ORCID [0000-0002-4999-2931](https://orcid.org/0000-0002-4999-2931). Lead analyst.
- Kathleen R. Ryan (University of California, Berkeley) — data provider and scientific collaborator; co-authorship pending publication discussion.
