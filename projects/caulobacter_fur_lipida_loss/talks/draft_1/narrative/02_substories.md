# Substory clusters — `caulobacter_fur_lipida_loss` / talk mode `talk-30`

**Throughline:** A single envelope catastrophe — lipid A loss — triggers five partially independent adaptive layers (Fur-released transport, ChvI two-phase signaling, constitutive sphingolipid substitution, peptidoglycan remodeling, and cross-species structural unavailability) that together explain how *and why* *Caulobacter* alone tolerates the deletion.
**Tier:** STRONG
**Mode budget:** 25-32 slides per SPEC §5

## Mode-capacity check

- **Boilerplate slides:** 10 (title 1 + 1 divider per substory ×6 + cross_tenant_integration 1 + acknowledgments 1 + references 1; qa_anticipated optional, +3 appendix → 31, still ≤ max)
- **Per-substory content target:** 3 (talk-30); sized asymmetrically by cluster density (S1=4, S2=3, S3=4, S4=2, S5=3, S6=2)
- **Required slides:** 28 (boilerplate 10 + per-substory content 18)
- **Mode max:** 32

**Capacity verdict:** `fits`

> **Compression note (not overflow).** TL2 is a five-layer architecture, so this clusters into 6 substories (five layers + a synthesis closer) — above the talk-30 *typical* 3–4. It fits the budget (28/32, landing on the default target of 28), but per-layer treatment is compressed to 2–4 content slides each rather than the 3–5 a talk-45 would allow. This is the cost the throughline gate accepted when TL2 was chosen over the sphingolipid-centered TL1; no critical analysis is dropped. If the speaker later finds the per-layer real estate too thin at delivery, escalating to talk-45 (the plan's originally requested mode) restores 3–5 slides per layer.

## Substory clusters

### S1 — Fur-released transport relief carries the Layer-1 fitness signal

**Question:** When lipid A is lost, does Fur derepression reshape envelope transport — and does that relief carry a measurable fitness signal?

**Conclusion for next substory:** Fur-released transport relief is real and fitness-bearing in Path A transporters, but the SspB-buffered respiratory arm shows no fitness signal.

**Punchline:** Fur-released transport relief, not the respiratory arm, carries the Layer-1 fitness signal.

**Critical analyses covered:**

- A25: NB00 cross-layer orientation panel (sphingolipid/Lpt CPM, ChvI overlap, Zik suppressors, top DEGs, OM proteome shifts) — REPORT §Phase A / NB 00_orientation.ipynb
- A1: Leaden 2018 Δ*fur* concordance (ρ=0.315, p=2.08e-03, 71% sign concordance, 93 DEGs) — REPORT §Finding 1 / NB 01_leaden2018_fur_signature.ipynb cell 5
- A2: SspB-buffered cbb3/cyd/*fix*-NOPQ operon (53/93 Leaden DEGs buffered) — REPORT §Finding 1 / NB 01 cell 5
- A3: Genome-background phenotype-bearing rate = 33.25% (n=3943, K=1311) — REPORT §Finding 2 / NB 02_caulo_fitness_ranking.ipynb
- A4: Path A (concordant_strong, n=32) hypergeometric enrichment 17/32=53.1%, fold 1.60×, p=0.016 — REPORT §Finding 2 table / NB 02b_h2_hypergeometric_verdict.ipynb cell 1
- A5: Path B (SspB-buffered, n=26) NOT enriched: 9/26=34.6%, fold 1.04×, p=0.515 — REPORT §Finding 2 table / NB 02b cell 1
- A6: Path A per-gene fitness t-stats (ChvT |t|=43.7; TBDTs |t| 9–28) — REPORT §Finding 2 / NB 02 cell 9
- A7: Zero iron-limitation experiments in Caulo FB compendium (0/198); H2 iron arm descoped — REPORT §Finding 2 preflight / NB 02 cell 5

**Cluster rationale:** This opening arc orients the audience to the whole envelope landscape (A25 sets the cross-layer stage) and then establishes the first adaptive layer honestly. Fur derepression is genuinely concordant with the Leaden 2018 Δ*fur* signature (A1), and one specific buffered operon is identified (A2) — but the fitness data sharpen rather than confirm the naïve "respiratory ATP" story: against a 33.25% genome background (A3), only the Path A transporter set is enriched (A4), driven by very large per-gene effects (A6, ChvT |t|=43.7), while the SspB-buffered respiratory arm (Path B) shows *no* fitness enrichment (A5). A7 closes the iron axis as untestable in this compendium. The sequence therefore moves from "Fur releases transport" to "the operative, fitness-bearing relief is transport, not respiration" — a negative result (A5) that strengthens rather than weakens the layer. The marginal Path A enrichment (A4, p just below 0.05 against a threshold mis-set below background) is presented at its actual evidence level rather than overstated.

**Proposed slide budget:** 4 content slides + 1 divider (per SPEC §6.2)

**Slide kinds anticipated** (slide_compose refines):

- `section_divider` — Q-slide (names the Question; SPEC §6.2 non-negotiable)
- `data_figure` (A-slide — NB00 orientation/landscape panel, A25; cross-layer scoping)
- `data_figure` (R-slide — Fur–Leaden concordance scatter, A1)
- `data_table` (R-slide — Path A vs Path B hypergeometric + per-gene fitness, A3/A4/A5/A6)
- `claim_evidence` (C-slide — transport relief carries the signal; respiratory arm demoted; states the Conclusion-for-next)

---

### S2 — ChvI runs a two-phase envelope-stress cascade

**Transition from prior:** S1 established that Fur-released *transport* relief carries the Layer-1 fitness signal while the SspB-buffered respiratory arm does not. S2 asks how the ChvI envelope-stress regulator organizes the response over time.

**Question:** How does the ChvI envelope-stress two-component system organize the transcriptional response to lipid A loss over time?

**Conclusion for next substory:** ChvI drives a two-phase program — regulators early, envelope-structural genes late — but the membrane substitute itself is set elsewhere.

**Punchline:** ChvI runs a two-phase cascade: regulators first, envelope-structural genes second.

**Critical analyses covered:**

- A8: ChvI two-phase disjoint partition: 20 unique-early + 10 both-phase + 49 late (=79) — REPORT §Finding 3 / NB 03_chvi_phase_partition_sigU.ipynb cell 4
- A9: ChvI autoregulation: ChvI (CCNA_00237) in both-phase set at logFC +1.45 — REPORT §Finding 3 / NB 03 cell 5
- A10: SigU as late-cohort driver: coherence 24.5%, Fisher p=0.243 — REPORT §Finding 3 / NB 03 cell 10
- A11: Phase theme shift: regulator-rich early (6.7%) → envelope-structural late (10.2% OM, 12.2% TBDT) — REPORT §Finding 3 / NB 03 cell 6

**Cluster rationale:** This layer shows the *temporal organization* of the response. The disjoint partition (A8) cleanly separates early and late ChvI cohorts above the pre-registered ≥10/cohort threshold, and ChvI's own both-phase autoregulation (A9) anchors the regulator as actively sustained. The theme shift (A11) is the narrative payload — the early phase is regulator-rich, the late phase turns envelope-structural (OM and TBDT genes). A10 is presented at its honest, demoted level: SigU is an attractive candidate late driver but fails the relaxed coherence criterion (Fisher p=0.243, no gold standard for an uncharacterized *Caulobacter* SigU), so it is named as a hypothesis, not a finding. The arc concludes that ChvI *schedules* the envelope rebuild but does not itself specify the lipid-A substitute — handing the substitute question to S3.

**Proposed slide budget:** 3 content slides + 1 divider (per SPEC §6.2)

**Slide kinds anticipated** (slide_compose refines):

- `section_divider` — Q-slide (names the Question)
- `data_figure` (R-slide — two-phase partition 20+10+49, A8)
- `data_figure` (R-slide — phase theme shift early→late + ChvI autoregulation, A9/A11; SigU A10 shown at demoted level)
- `claim_evidence` (C-slide — two-phase cascade established; substitute set elsewhere; states the Conclusion-for-next)

---

### S3 — A constitutive sphingolipid pool, moved by repurposed Lpt, substitutes for lipid A

**Transition from prior:** S2 traced the ChvI two-phase program but located the actual membrane substitute elsewhere. S3 asks what molecularly replaces lipid A in the outer membrane.

**Question:** What molecular substitute replaces lipid A in the *Caulobacter* outer membrane, and is its biosynthesis newly induced or already in place?

**Conclusion for next substory:** A constitutive anionic-sphingolipid pool substitutes for lipid A, transported by maintained Lpt machinery — not an inducible emergency response.

**Punchline:** A constitutive sphingolipid pool, moved by repurposed Lpt machinery, substitutes for lipid A.

**Critical analyses covered:**

- A13: Sphingolipid biosynthesis constitutive: 0/6 UP; *spt* −0.64 FDR 0.002; *sphk* −0.40 FDR 0.02 — REPORT §Finding 4 table / NB 04_sphingolipid_lpt_panel.ipynb cell 3
- A14: Canonical Lpt maintained at transcript: MsbA-like CCNA_00307 +0.89 FDR 0.01; LptC-related CCNA_03716 +0.56 FDR 0.005 — REPORT §Finding 4 table / NB 04 cell 3
- A15: Lpt protein discordance: LptD log2(4672/4659)=−0.47; LptE=−0.78 (decline) — REPORT §Finding 4 protein table / NB 04 cell 6
- A16: *lptC2* (CCNA_01226) pilot: transcript −0.60 FDR 0.034; protein +1.08 vs intermediate, +0.66 vs WT — REPORT §Finding 4 pilot / NB 04 cells 3,6
- A17: CCNA_01217 protein log2 +0.77 (vs intermediate), +0.74 (vs WT) — REPORT §Finding 4 / NB 04 cell 6
- A12: CtpA (CCNA_03113) +0.58 transcript, p=0.048, FDR=0.109; protein not detected — REJECTED at pre-reg bar — REPORT §Finding 4 table / NB 04 cell 5

**Cluster rationale:** This is the load-bearing layer — the central contribution. The arc establishes that the substitute is *constitutive*, not emergency-induced: none of the six sphingolipid-biosynthesis genes is up and two are significantly down (A13), so the anionic-sphingolipid pool is already standing. The transport apparatus is the second half of the mechanism — canonical Lpt components are maintained/up at transcript (A14), consistent with repurposing the LPS-export machinery to ship the sphingolipid substitute. The honest tension lives here: the single-replicate OM proteome shows Lpt protein-level discordance (A15, LptD/LptE decline against transcript), and the *lptC2* and CCNA_01217 pilots (A16, A17) are direction-only single-replicate signals labeled suggestive. A12 (CtpA, the LpxF-substitute candidate) is carried explicitly as REJECTED at the pre-registered FDR bar — the evidence-leveling beat the throughline promised lives in this one slide rather than a separate "how-we-know" arc. The layer concludes that the substitute is constitutive and Lpt-borne.

**Proposed slide budget:** 4 content slides + 1 divider (per SPEC §6.2)

**Slide kinds anticipated** (slide_compose refines):

- `section_divider` — Q-slide (names the Question)
- `data_figure` (R-slide — sphingolipid-biosynthesis constitutive heatmap, A13)
- `data_figure` (R-slide — Lpt transcript maintained vs protein discordance, A14/A15)
- `data_table` (R-slide — *lptC2* / CCNA_01217 pilots + CtpA rejected-at-bar evidence-leveling, A16/A17/A12)
- `claim_evidence` (C-slide — constitutive substitute + repurposed Lpt; states the Conclusion-for-next)

---

### S4 — Peptidoglycan synthesis downshifts with targeted Pal-Tol induction

**Transition from prior:** S3 established the constitutive sphingolipid substitute and its maintained Lpt transport. S4 asks whether the peptidoglycan layer itself remodels to accommodate the rebuilt envelope.

**Question:** Does the peptidoglycan layer remodel to accommodate the rebuilt envelope, and in which direction does that remodeling run?

**Conclusion for next substory:** Peptidoglycan synthesis is broadly downshifted with targeted Pal-Tol induction — a coordinated remodel that raises why only *Caulobacter* survives it.

**Punchline:** Peptidoglycan synthesis downshifts with targeted Pal-Tol induction — a coordinated wall remodel.

**Critical analyses covered:**

- A18: PG remodeling: 28 unique loci meet H4 threshold (≥3 required; 25 transcript + 6 protein) — REPORT §Finding 5 / NB 05_pg_remodeling.ipynb cell 5
- A19: PG direction: 20 DOWN (FtsI, PbpZ/C, MurD, endopeptidases) + inductions (SdpA +4.8 protein; Pal +2.08 transcript/+2.84 protein) — REPORT §Finding 5 / NB 05 cells 5,8
- A20: Pal-Tol mechanistic interpretation (retrograde PL transport per Tan & Chng 2025) — REPORT §Interpretation §8 / NB 03/NB 05 convergence

**Cluster rationale:** This layer demonstrates that the envelope rebuild reaches the cell wall. The gene set was locked pre-DE and clears the H4 threshold with room to spare (A18, 28 loci vs ≥3). The directional story (A19) is the operative finding — broad downshift of synthesis machinery (FtsI, PbpZ/C, MurD, endopeptidases) alongside specific inductions, notably Pal — and is presented at its evidence level (protein-side inductions are single-replicate; two regex false positives were flagged and removed). A20 supplies the mechanistic reading: the Pal-Tol induction, convergent across NB03 and NB05, fits retrograde phospholipid transport (Tan & Chng 2025), framed as literature-grounded interpretation rather than project-internal proof. The arc concludes that the wall is *coordinately* remodeled — completing the four-layer intra-organism response and setting up the cross-species "why only Caulobacter" question.

**Proposed slide budget:** 2 content slides + 1 divider (per SPEC §6.2)

**Slide kinds anticipated** (slide_compose refines):

- `section_divider` — Q-slide (names the Question)
- `data_figure` (R-slide — PG remodeling heatmap: 28 loci, 20 DOWN + Pal/SdpA inductions, A18/A19)
- `claim_evidence` (C-slide — coordinated downshift + Pal-Tol engagement, A20 interpretation; states the Conclusion-for-next)

---

### S5 — Caulobacter's sphingolipid/ChvI route is taxonomically restricted

**Transition from prior:** S4 showed a coordinated peptidoglycan remodel completing the four-layer intra-organism response. S5 asks why this whole program is available to *Caulobacter* but not to other lipid-A-loss-tolerant Gram-negatives.

**Question:** Why can *Caulobacter* tolerate lipid A loss when other Gram-negatives cannot — is the sphingolipid/ChvI route structurally unavailable to them?

**Conclusion for next substory:** The sphingolipid pathway and ChvG-ChvI are taxonomically restricted; comparator species lack the route entirely and use alternative strategies instead.

**Punchline:** Caulobacter's sphingolipid/ChvI route is taxonomically restricted — comparators lack it and use other routes.

**Critical analyses covered:**

- A21: Sphingolipid pathway *Caulobacter*-unique: NCBI *spt* (7,0,0,0); *cerR* (6,0,0,0) — REPORT §Finding 6 / NB 06b_ncbi_annotation_presence.ipynb cell 3
- A22: ChvG-ChvI alphaproteobacterial-restricted: NCBI ChvG (5,0,0,0); ChvI (6,0,0,0) — REPORT §Finding 6 / NB 06b cell 3
- A23: Comparator alternative routes (A.b. PBP1A/Ldt — Kang 2021; N.m. capsule — Steeghs 2001; M.c. late-acyltransferase — Gao 2008) — REPORT §Finding 6 / NB 06_comparative_species.ipynb cell 3
- A24: PaperBLAST ~80% false-negative diagnosis for *Caulobacter* lipid A genes (LpxA/C/D/B/K 0 in PB, 11–18 in NCBI) — REPORT §NB06b table / NB 06b cell 3

**Cluster rationale:** This layer answers the throughline's "why *Caulobacter* alone" half. NCBI presence/absence confirms both halves of the route are taxonomically restricted: the sphingolipid biosynthesis genes appear only in *Caulobacter* among the comparators (A21) and ChvG-ChvI is alphaproteobacterial-restricted (A22) — meaning the other lipid-A-loss-tolerant species *cannot* run this program. A23 closes the logic by showing those species solve the problem differently (PBP1A/Ldt remodeling, capsule, late acyltransferase). A24 is the method-robustness slide that makes the absence-based argument trustworthy: PaperBLAST under-calls *Caulobacter*'s own lipid A genes ~80% of the time, so the comparator absences are verified against NCBI rather than taken from PaperBLAST alone — the headline claim depends on absences where NCBI confirms. The arc concludes that structural unavailability, not chance, explains the species-specificity.

**Proposed slide budget:** 3 content slides + 1 divider (per SPEC §6.2)

**Slide kinds anticipated** (slide_compose refines):

- `section_divider` — Q-slide (names the Question)
- `data_figure` (R-slide — comparative presence/absence heatmap: sphingolipid + ChvG-ChvI across species, A21/A22)
- `two_column_compare` (R/A-slide — comparators' alternative routes vs PaperBLAST FN method-robustness check, A23/A24)
- `claim_evidence` (C-slide — route taxonomically restricted; comparators use alternatives; states the Conclusion-for-next)

---

### S6 — Five partially independent layers compose one Caulobacter-specific program (FINAL substory)

**Transition from prior:** S5 established that the sphingolipid/ChvI route is taxonomically restricted, with comparators using other strategies. S6 asks whether the five layers, taken together, compose one coherent explanation of how *and why* *Caulobacter* tolerates the deletion.

**Question:** Do the five adaptive layers integrate into a single coherent mechanism that explains both how and why *Caulobacter* tolerates lipid A loss?

**Punchline:** Five partially independent layers compose one *Caulobacter*-specific program for surviving lipid A loss.

**Critical analyses covered:**

- A26: 4-panel synthesis master figure + pre-registered hypothesis scorecard — REPORT §Key Findings figure / NB 07_synthesis.ipynb

**Cluster rationale:** The closing substory lands the throughline. The 4-panel synthesis master figure (A26, recommended Figure 1) maps the five layers onto a single envelope cross-section and pairs it with the pre-registered hypothesis scorecard, so the audience sees the integrated mechanism *and* the honest evidence ledger (which sub-claims passed, which were partial, which — CtpA — were rejected) in one frame. This is a deliberately single-analysis cluster: A26 is the project's integration artifact and is the natural payoff slot for a five-layer architecture throughline, so it earns its own divider rather than being folded into S5. Its R-slide is the master figure; its C-slide states the throughline's integrated claim — that the layers are *partially independent* (each could in principle fail separately) yet *jointly Caulobacter-specific*, which is precisely why the deletion is tolerated here and nowhere else.

**Proposed slide budget:** 2 content slides + 1 divider (per SPEC §6.2)

**Slide kinds anticipated** (slide_compose refines):

- `section_divider` — Q-slide (names the integrating Question)
- `data_figure` (R-slide — 4-panel synthesis master figure + hypothesis scorecard, A26)
- `big_idea` (C-slide — five layers compose one Caulobacter-specific program; lands the throughline)
