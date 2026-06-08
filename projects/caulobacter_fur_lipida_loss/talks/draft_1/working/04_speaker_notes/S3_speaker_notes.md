# Speaker notes — substory `S3`

**Substory punchline:** A constitutive sphingolipid pool, moved by repurposed Lpt machinery, substitutes for lipid A.
**Throughline:** A single envelope catastrophe — lipid A loss — triggers five partially independent adaptive layers (Fur-released transport, ChvI two-phase signaling, constitutive sphingolipid substitution, peptidoglycan remodeling, and cross-species structural unavailability) that together explain how *and why* *Caulobacter* alone tolerates the deletion.
**Tier:** STRONG
**Mode:** talk-30

---

## position 0 — section_divider — `A constitutive sphingolipid pool, moved by repurposed Lpt machinery, substitutes for lipid A.`

S2 established that ChvI runs a two-phase cascade — regulators deployed early, envelope-structural genes late — but left unanswered what the late structural program actually installs in the outer leaflet. That hand-off is precise: ChvI schedules the envelope rebuild; S3 names what fills the lipid A vacancy.

The question entering Layer 3 is grounded in Zik et al. 2022 (Cell Reports 39:110888, PMID 35649364), which showed that Δlpxc viability in the Δfur background requires anionic sphingolipid ceramide phosphoglycerate (CPG), and that "alterations in Fur-regulated processes, rather than iron status per se, underlie the ability to survive when lipid A synthesis is blocked." What Zik 2022 left open was whether CPG supply is constitutive or emergency-induced — and whether the Lpt transport machinery is actively maintained to traffic CPG, or shut down once there is no LPS substrate to move.

Two competing models were testable. An emergency-induction model predicts CPG biosynthesis genes going up in the rescued strain when lipid A disappears — the cell making more substitute on demand. A constitutive-pool model predicts no biosynthesis induction: the CPG pool is already present in wild type, and when the lipid A slot vacates, existing CPG is rerouted to fill it. The Lpt repurposing model predicts the transport apparatus remains maintained or goes up at transcript, consistent with the Uchendu 2026 demonstration that Lpt paralog homologs are required for sphingolipid transport in lipid-A-deficient Caulobacter.

The honest tension entering this layer: the protein-level data for the Lpt apparatus produce a discordant picture, and the CtpA LpxF-substitute candidate from Zik 2022 was tested at a pre-registered bar and rejected. Layer 3 therefore contains one strong positive finding (constitutive CPG pool), one genuine transcript-protein tension (canonical Lpt), two directional pilot observations (lptC2, CCNA_01217), and one explicit rejection (CtpA) — a textured picture that collectively establishes what can and cannot be said about the substitute mechanism at this evidence level. The next slide establishes the measurement design before the audience sees any data.

---

## position 1 — methods_summary — `Methods: H3 sub-claims tested across transcript contrast and single-replicate OM proteome`

The H3 evidence runs two data types in parallel: the 4599-vs-4584 edgeR transcript contrast — Δlpxc rescued versus Δfur Δsspb intermediate — and a single-replicate outer membrane proteome comparing strains 4672 (rescued), 4659 (intermediate), and 4580 (wild-type baseline). The transcript contrast is the primary H3 readout; the proteome is a post-hoc cross-check that became load-bearing once the Lpt protein findings emerged.

For the transcript arm, six sphingolipid biosynthesis genes were queried: serine palmitoyltransferase spt, sphingosine kinase sphk, bacterial ceramide synthase bcerS, and the cpgA/B/D head-group cluster. The test is falsification-forward — if any of the six is significantly UP in 4599-vs-4584, the constitutive-pool model is wrong. Six canonical Lpt apparatus components were queried in the same contrast, asking whether any are DOWN, since Lpt downregulation would contradict the repurposing hypothesis. Significance threshold for transcript: FDR < 0.05 via edgeR. Gene sets and thresholds were locked before differential expression analysis ran.

For CtpA specifically, the BORDERLINE criterion was pre-registered before results were examined: transcript pvalue between 0.05 and 0.15 AND protein detected in the OM proteome. Both parts were required for a BORDERLINE verdict; failing either gave REJECTED. This criterion was designed to capture a borderline transcript signal corroborated by protein detection — a deliberately conservative bar given Zik 2022's prediction of CtpA as a LpxF-substitute processing enzyme.

The OM proteome spans 22 proteins from the sphingolipid, Lpt, and CtpA gene sets across the three strains. It is single-replicate — stated upfront and carried through every protein-level claim in this layer. Only direction is interpretable; per-protein statistics are unavailable. This corresponds to REPORT.md Limitation L#2: single-replicate OM proteome findings are directional signals, not statistical conclusions. Replicated proteomics to resolve the Lpt protein ambiguity are planned for summer 2026. edgeR version was not pinned in the project notebooks and is cited as the DE framework used throughout.

---

## position 2 — data_figure — `Sphingolipid biosynthesis is constitutive: 0 of 6 genes UP; spt and sphk mildly DOWN`

When this heatmap appears, the headline result is immediate: the sphingolipid biosynthesis locus is flat to slightly declining across the rescue strain series — not induced.

From REPORT.md §Finding 4: 0 of 6 sphingolipid biosynthesis genes is significantly upregulated in the 4599-vs-4584 contrast at FDR < 0.05. The two most sensitive readouts — serine palmitoyltransferase spt and sphingosine kinase sphk — are both significantly DOWN: spt logFC −0.64 FDR 0.002, sphk logFC −0.40 FDR 0.02. Both p-values are from the single 4599-vs-4584 contrast designed to isolate the Δlpxc-specific response. These are among the few genome-wide significant hits in the biosynthesis panel, and they go in the wrong direction for any emergency induction model. The REPORT scorecard records this as "PASS strongly" for the constitutive sub-claim.

The biology encoded here is the central mechanistic claim of Layer 3. The cell does not respond to losing lipid A by making more CPG biosynthesis transcript. The existing CPG pool — constitutive, present in wild type — is what sustains the outer-membrane substitution. This rules out the simplest emergency-response framing. Zik 2022 showed CPG is required for Δlpxc viability; this layer shows CPG supply is constitutive, not demand-responsive. Olea-Ozuna 2021 established the five structural genes required for ceramide synthesis in Caulobacter and for bacterial survival — those genes are in this locus, and none are induced here. Substitution is flux-driven, not transcriptionally programmed.

One critical caveat must land in delivery: we tested transcript-level regulation only. Post-transcriptional mechanisms — enzyme stabilization, allosteric flux redistribution, or substrate competition relief when LPS synthesis stops consuming shared precursors — are not excluded by these data. The constitutive-transcript finding forecloses transcriptional induction; it does not foreclose post-translational flux routing through the existing biosynthetic machinery. The audience should leave this slide knowing the CPG pool is always-on, not knowing the full flux story. The next slide turns to whether the Lpt transport apparatus is maintained to ship that standing pool across the periplasm to the outer leaflet.

---

## position 3 — data_table — `Lpt transcript upregulated; LptD/LptE protein decline and CtpA absence define the layer's limits`

This table carries both the strongest positive result of Layer 3's second half and the layer's two genuine limits — and every row needs to be delivered at its actual evidence level.

At the transcript level, the Lpt apparatus story is clear and consistent with the Uchendu 2026 shared-component model. Zero Lpt components are significantly down in 4599-vs-4584; two are meaningfully up. MsbA-like CCNA_00307 shows logFC +0.89 FDR 0.01; LptC-related CCNA_03716 shows logFC +0.56 FDR 0.005. These are the exact Lpt paralogs that Uchendu 2026 (bioRxiv 2026.04.12.717747) demonstrated are required for inner-membrane sphingolipid transport in Caulobacter. Upregulation at transcript is direct evidence consistent with the Lpt repurposing model, and these two rows are highlighted in the table.

At the protein level, the two canonical Lpt proteins detected in the OM proteome both decline. LptD (CCNA_01760) log2(4672/4659) = −0.47; LptE (CCNA_03866) log2(4672/4659) = −0.78. This is discordant with the transcript signal and is the genuine unresolved tension in Layer 3. A parsimonious reading: canonical Lpt normally loads LPS substrate; remove the substrate and the LPS-specific machinery is less occupied or actively turned over at protein level. But single-replicate proteomics cannot discriminate substrate-limitation from active downregulation — both hypotheses remain open. The verdict is labeled DISCORDANT, not PASS, and this is REPORT.md Limitation L#2 applied directly to the most visible table row.

The lptC2 (CCNA_01226) observation: transcript logFC −0.60 FDR 0.034, protein log2(4672/4659) = +1.08 versus intermediate — noting that lptC2 protein was already DOWN −0.42 log2 in the intermediate strain, so the net change relative to WT baseline is +0.66 log2, not +1.08. CCNA_01217 (Zik 2022 sphingolipid gene required for CHIR-090 tolerance) shows protein +0.77 versus intermediate and +0.74 versus WT. Both are single-replicate pilot observations labeled PILOT; they are consistent with post-transcriptional stabilization of sphingolipid-transport machinery when LpxC competition for the shared LptB ATPase disappears, but they do not establish it statistically.

CtpA: pvalue = 0.048 in 4599-vs-4584 fails the BORDERLINE lower bound (required pvalue > 0.05); CtpA protein was not detected in the OM proteome. Both parts of the pre-registered criterion failed. The notebook outputs CTPA VERDICT: REJECTED. The LpxF-substitute hypothesis from Zik 2022 remains open — this dataset did not address it at the bar we committed to.

---

## position 4 — claim_evidence — `Constitutive CPG pool and maintained Lpt transcript define the substitute mechanism; CtpA rejected`

Layer 3 synthesizes to a two-part mechanism stated at its actual evidence level. CPG supply is constitutive — strong, direct evidence. The Lpt transport apparatus is maintained at transcript and consistent with the repurposing model — strong, direct evidence at that data type — with a genuine protein-level discordance pending replicated proteomics. CtpA was tested at a pre-registered bar and explicitly rejected.

The first finding — 0 of 6 sphingolipid biosynthesis genes UP; spt logFC −0.64 FDR 0.002; sphk logFC −0.40 FDR 0.02 — carries the layer's strongest evidence. It forecloses the emergency-induction model and establishes that CPG substitution is a standing capability of wild-type Caulobacter, not a rescue-specific transcriptional response. The REPORT scorecard records this sub-claim as "SUPPORTED strongly." The speaker can deliver this declaratively.

The second finding — MsbA-like CCNA_00307 logFC +0.89 FDR 0.01 and LptC-related CCNA_03716 logFC +0.56 FDR 0.005 — is also a direct transcript-level finding, consistent with the Uchendu 2026 shared-component model. The speaker must immediately follow with the protein discordance: LptD log2(4672/4659) = −0.47 and LptE = −0.78 both decline in the single-replicate proteome, which is the genuine unresolved tension. We are not claiming the canonical Lpt apparatus is definitively maintained at the protein level. The transcript evidence is consistent with repurposing; the protein story requires replicated proteomics before a stronger claim is warranted. Replicated proteomics are planned for summer 2026 (REPORT Limitation L#2).

The third element — CtpA REJECTED — is the rejection the throughline committed to surface honestly. Transcript pvalue = 0.048 fails the BORDERLINE lower bound of 0.05 in the pre-registered 4599-vs-4584 contrast; CtpA is not detected in the OM proteome. Both parts of the pre-registered criterion failed. Naming this explicitly in delivery is what makes the five-layer throughline trustworthy: the project applied a pre-registered bar, one hypothesis failed it, and we say so. Zik 2022's LpxF-substitute prediction remains an open question; this dataset did not address it at the committed threshold.

With the molecular substitute identified at its honest evidence level, S4 asks whether the peptidoglycan layer itself remodels to accommodate the rebuilt outer membrane — specifically whether synthesis shuts down broadly, and whether the Pal-Tol anchoring complex is specifically engaged to compensate for the loss of LPS-mediated membrane cohesion.
