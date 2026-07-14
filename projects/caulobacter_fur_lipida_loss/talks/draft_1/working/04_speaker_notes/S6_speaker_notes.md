# Speaker notes — substory `S6`

**Substory punchline:** Five partially independent layers compose one *Caulobacter*-specific program for surviving lipid A loss.
**Throughline:** A single envelope catastrophe — lipid A loss — triggers five partially independent adaptive layers (Fur-released transport, ChvI two-phase signaling, constitutive sphingolipid substitution, peptidoglycan remodeling, and cross-species structural unavailability) that together explain how *and why* *Caulobacter* alone tolerates the deletion.
**Tier:** STRONG
**Mode:** talk-30

---

## position 0 — section_divider — `Five partially independent layers compose one Caulobacter-specific program for surviving lipid A loss.`

We close the five-layer arc here. Across S1 through S5 the mechanism unfolded in sequence: Fur-released transport relief carries the Layer-1 fitness signal while the SspB-buffered respiratory arm does not; ChvI runs a two-phase cascade scheduling regulators before envelope-structural genes; a constitutive sphingolipid pool is delivered by maintained Lpt machinery; peptidoglycan synthesis downshifts while Pal-Tol is specifically induced; and the sphingolipid/ChvI route is structurally absent in A. baumannii, N. meningitidis, and M. catarrhalis — NCBI-confirmed at spt 7,0,0,0, cerR 6,0,0,0, ChvG 5,0,0,0, and ChvI 6,0,0,0.

The closing question this substory answers is whether those five layers, each tested independently against pre-registered thresholds, integrate into a single coherent explanation of how and why Caulobacter tolerates the Δlpxc deletion. The pre-registered scorecard in NB07_synthesis.ipynb is the integration artifact; it contains seven verdicts.

The phrase "partially independent" in the punchline is not hedging — it is the precise engineering description of the architecture. Each layer was tested in isolation. Any one could have failed without necessarily collapsing the others. What makes the integration argument credible is that the scorecard includes a REJECTED entry for CtpA and a NOT ENRICHED result for the SspB-buffered respiratory arm. Both failures are load-bearing: a scorecard with no rejections would be a scorecard with no standards. Precisely because CtpA was rejected at the pre-registered bar after adversarial review, and because the respiratory arm was demoted when it failed to clear the 33.25% genome background rate, the four-layer positive claim can be stated without overclaiming the evidence.

S6 unfolds in two slides: a methods slide that orients to the five evidence arms and names the adversarial-review corrections applied before the scorecard was finalized, then the scorecard table itself. Together they land the throughline.

---

## position 1 — methods_summary — `Synthesis: five evidence arms integrated against pre-registered thresholds`

The synthesis draws on five distinct evidence platforms, and the audience needs to know what each can and cannot claim before the verdicts appear.

Transcript evidence is from edgeR differential expression on the 4599-versus-4584 contrast — the Δlpxc rescued strain against the Δfur Δsspb intermediate — isolating the Δlpxc-specific transcriptional response against the combined Δfur Δsspb background. All significance thresholds were committed in RESEARCH_PLAN.md before any differential expression analysis ran: FDR less than 0.05 for transcript claims, |log2| greater than 1 for proteome calls.

Fitness evidence comes from the 198-experiment Caulobacter RB-TnSeq compendium accessed through BERDL's kescience_fitnessbrowser (Price 2018, Nature 557:503). The operative fitness criterion is hypergeometric enrichment against the 33.25% genome background — not the pre-registered ≥10% threshold, which sat below the background rate and was therefore uninformative as an enrichment test. That recalibration, surfaced by adversarial review, is recorded in REPORT Novel Contribution §7 as a methodological lesson for future fitness-browser projects.

The OM proteome is single-replicate per strain — one of the project's eleven named limitations. Direction is interpretable at |log2| greater than 1; per-protein significance statistics cannot be computed from a single observation. Protein-level signals for lptC2, Pal, LptD, and LptE all require the replicated proteomics scheduled for summer 2026 before they can be claimed at publication rigor.

Two adversarial-review corrections are integrated into the scorecard. First, CtpA was corrected from BORDERLINE to REJECTED: the 4599-versus-4584 p-value of 0.048 fails the BORDERLINE lower bound of 0.05, and CtpA was not detected in the OM proteome. Second, the Pal-Tol interpretation was reframed from an uncited Mg2+-bridging mechanism to Tan and Chng 2025 (Nat Commun 16:2293), which established that the primary Tol-Pal function is retrograde phospholipid transport for OM lipid homeostasis. Comparator absences were confirmed by NB06b NCBI annotation after PaperBLAST was diagnosed with an approximately 80% false-negative rate for Caulobacter's own lipid A biosynthesis genes. With those corrections applied, the scorecard on the next slide is the project's final integration output.

---

## position 2 — data_table — `Five-layer synthesis scorecard: four layers confirmed, CtpA rejected, SspB arm demoted`

The scorecard gives seven verdicts. Let me state each at its evidence level.

Layer 1's transport arm passes, marginally. The 32 concordant-strong Fur-released genes show 17 of 32 phenotype-bearing — 53.1% — versus the 33.25% genome background: fold enrichment 1.60 times, hypergeometric p=0.016. ChvT (CCNA_03108) carries |t|=43.7 under envelope stress; four TBDTs sit at |t| 9 to 28. Marginal is the right description: the enrichment is real but modest. The SspB-buffered Path B sits at 9 of 26 phenotype-bearing — 34.6%, fold 1.04 times, p=0.515 — indistinguishable from background. The respiratory ATP arm is demoted to hypothesis.

Layer 2 passes cleanly. The ChvI two-phase partition produced 20 unique-to-early genes, 10 both-phase genes including ChvI itself at logFC +1.45 (direct autoregulation evidence), and 49 late-consequence genes — all three cohorts above the pre-registered ≥10 threshold. The SigU sub-arm is partial: late-cohort functional coherence returned 24.5%, below the 50% relaxed criterion, Fisher p=0.243. SigU as late-cohort driver remains a hypothesis.

Layer 3 carries the project's strongest individual result. Zero of six sphingolipid biosynthesis genes are significantly upregulated; spt is down at −0.64 with FDR 0.002. The CPG pool is constitutive — not emergency-induced. CtpA is rejected at the pre-registered bar: 4599-versus-4584 p-value 0.048 fails the BORDERLINE lower bound of 0.05, and CtpA was not detected in the OM proteome.

Layer 4 passes strongly: 28 unique loci meeting the H4 threshold, dominated by downregulation (20 DOWN — FtsI, PbpZ, MurD, multiple endopeptidases), while Pal is specifically induced at +2.08 transcript log2 and +2.84 protein log2. Following Tan and Chng 2025 (Nat Commun 16:2293), Pal upregulation is consistent with increased retrograde phospholipid transport restoring OM lipid homeostasis when the LPS outer leaflet is gone. That mechanistic reading is inference from the cited paper; it is not a direct project measurement, and the protein-level Pal signal is single-replicate.

Layer 5 is NCBI-confirmed: spt 7,0,0,0; cerR 6,0,0,0; ChvG 5,0,0,0; ChvI 6,0,0,0 — consistent with Olea-Ozuna 2021 and 2024 and Greenwich 2023.

The synthesis closes the throughline: four main layers confirmed, one candidate rejected, one sub-arm demoted. Only Caulobacter simultaneously encodes the sphingolipid pathway, maintains ChvG-ChvI signaling, and carries Lpt transport capacity for CPG delivery. That combination, confirmed across five partially independent evidence arms, is why it alone tolerates the deletion — and why no piecemeal transfer of one layer to a comparator species would substitute for the full program.
