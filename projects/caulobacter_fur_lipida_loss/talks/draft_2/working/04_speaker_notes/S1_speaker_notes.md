# Speaker notes — substory `S1`

**Substory punchline:** Δfur derepression, not iron limitation, drives the lipid A-loss-permissive envelope state.
**Throughline:** Δfur derepression is the demonstrable driver of the lipid A-loss-permissive envelope state, and everything downstream is the supporting (and still-open) mechanism it sets in motion.
**Tier:** STRONG
**Mode:** talk-30

---

## position 0 — section_divider — `Δfur derepression, not iron limitation, drives the lipid A-loss-permissive envelope state.`

This section stakes the load-bearing claim of the talk: the Fur transcription factor, through constitutive derepression of its regulon rather than through any iron-starvation response, creates the envelope state that makes lipid A loss viable in Caulobacter crescentus. Everything downstream in the talk — the fitness-based subset ranking, the two-phase ChvI response, the sphingolipid substitution, the peptidoglycan reorganization — is built on this premise. If the audience takes one structural idea from S1, it is that the driver is genetic (the Δfur allele) not physiological (iron deprivation).

The primary evidence is a cross-study concordance. Our 4584-vs-4580 transcriptome correlates with Leaden et al. 2018's published Δfur RNA-seq across their 93 differentially expressed genes at Spearman ρ = 0.315, p = 2.08e-03, with 71% sign concordance. That concordance is the fingerprint of the Fur-derepression program operating constitutively in our strain — amplified by the dual Δfur ΔsspB release, but directionally aligned with Leaden's Δfur-alone signal. It anchors the driver claim.

Three analyses carry this section in order. The strain-design contrast — 4580 → 4584 → 4599 — leads, because the audience cannot interpret any expression contrast without understanding what each deletion does. The Leaden concordance scatter (NB01 cell 5) follows as the direct cross-study evidence. The iron-limitation discrimination from Leaden's own internal comparison and Zik et al. 2022's genetic-necessity result close the section by ruling out iron status as the explanation and establishing that Δfur is required for, not merely correlated with, lipid A-loss viability.

One scope caveat to carry into the subsequent slides: the transcriptome was collected under a single PYE-rich growth condition. The Fur derepression we observe is constitutive to the Δfur allele, but its magnitude under iron-deplete or minimal-medium conditions has not been measured in this project. Iron-limitation experiments are absent from the Caulobacter Fitness Browser compendium. REPORT §Limitations names this single-condition boundary explicitly. It is the key partial-evidence constraint on the iron-discrimination result; the strain-design logic and Zik 2022 anchoring, by contrast, are direct evidence whose scope is the Ryan-lab genetic system. The first content slide walks through the 4580 → 4584 → 4599 strain logic before any expression data appears.

---

## position 1 — workflow_diagram — `Three-strain series isolates the Δfur derepression signal in the lipid A-loss state`

Before any transcriptomics, the strain-series logic must be clear — every expression contrast in this talk derives from three genotypes, and the biological meaning of each contrast depends on understanding what each deletion contributes.

Strain 4580 carries ΔrsaA, which removes the crystalline S-layer protein that normally dominates the Caulobacter outer membrane. This cleans up the transcriptomic and proteomic background — the S-layer's extreme expression would otherwise mask subtler signals — while leaving Fur, SspB, and lipid A synthesis fully intact. Strain 4580 is the denominator in every comparison shown in this talk.

Strain 4584 adds Δfur and ΔsspB on top of the 4580 background. Δfur constitutively releases the Fur regulon: TonB-dependent transporters, iron-uptake systems, and iron-storage proteins that Fur normally represses under iron-replete conditions. ΔsspB removes the ClpXP adaptor that degrades SspB-tagged substrates; in Caulobacter this protects the cbb3/cyd/fix-NOPQ micro-aerobic respiratory operon at the transcript level — visible as the orange buffered cluster on the concordance scatter on the next slide. Critically, strain 4584 is lipid A-replete: the organism grows normally with a full outer membrane. The 4584-vs-4580 contrast is the clean readout of the combined Δfur + ΔsspB release, measured without the confound of lipid A loss.

Strain 4599 adds ΔlpxC to the 4584 background, deleting the committed step in lipid A biosynthesis entirely. Zik et al. 2022 (PMID 35649364) established that this genotype is viable only in a Δfur background — Fur-intact strains with ΔlpxC are inviable. The 4599-vs-4584 contrast captures the ΔlpxC-specific envelope response layered on the Fur-set state, and that contrast is the substrate for substories S3 and S4.

Two design caveats belong here. First, the outer membrane proteome is single-replicate per strain. REPORT §Limitations states: "OM proteome is single-replicate per strain — no per-protein statistics; only direction is interpretable." Proteomics in this talk are direction-only observations throughout; transcript-level DE (edgeR) is the statistically replicated layer. Second, both proteome contrasts involve the Ryan-lab strains in the ΔrsaA background, which may differ from the NA1000 background Leaden used — a source of some of the unexplained variance in the concordance ρ. The next slide presents the core concordance result and makes this variance interpretable.

---

## position 2 — data_figure — `Spearman ρ=0.315 concordance with Leaden Δfur signal confirms constitutive derepression (n=93 DEGs)`

This scatter is the central evidence for S1. The x-axis is Leaden et al. 2018's published Δfur logFC — from PMID 30210482, supplementary Table 2 — across the 93 genes they identified as significant Δfur DEGs. The y-axis is our 4584-vs-4580 logFC for the same 93 genes, computed in NB01_leaden2018_fur_signature.ipynb cell 5. The Spearman ρ = 0.315, p = 2.08e-03, with 71% sign concordance: 71% of the genes derepressed in Leaden's Δfur-alone strain are also upregulated in our Δfur ΔsspB strain, and most of the genes strongly repressed in Leaden are blunted near zero in ours.

Two geometric features carry the interpretation. The dark-blue concordant-strong cluster in the top-right quadrant extends further up our y-axis than along Leaden's x-axis — our strain shows amplified Fur derepression relative to Leaden's Δfur-alone. The extreme outlier in that quadrant is HutA, the heme-hemoglobin TonB-dependent transporter, at our logFC +10.5 versus Leaden's +2.2 — a nearly fivefold amplification reflecting the combined dual-release effect of Δfur and ΔsspB together. The orange buffered cluster sits near y = 0 across the full Leaden x-axis range of −5 to −9. These are 53 of the 93 Leaden Δfur DEGs blunted in our data, dominated by the cbb3/cyd/fix-NOPQ micro-aerobic respiratory operon (CCNA_01466–01476: ccoNOPQ, cydCDA, fixGHI). The ΔsspB arm is doing measurable transcript-level work, shielding this specific operon from Fur-driven shutdown in our strain.

The speaker must be ready to defend ρ = 0.315 against "that's a modest correlation." REPORT §Finding 1 frames this as "confirming Fur derepression as a major driver" — not the sole driver, and not a full explanation of the transcriptome shift. Unexplained variance comes from the ΔsspB contribution, from strain-background differences between the Ryan-lab strains and Leaden's NA1000, and from the single PYE-rich growth condition. The honest answer to a push on ρ: this is one of several converging lines of evidence. The concordance is real and statistically supported; its framing as "major driver confirmed" is accurate and deliberately scoped. The iron-discrimination result on the next slide closes the alternative explanation and provides the complementary genetic anchor from Zik 2022.

The next slide uses Leaden's own iron-limitation comparison to establish that what we observe is constitutive Δfur allele derepression — not an iron-status readout — and anchors the whole substory with Zik's genetic necessity result.

---

## position 3 — claim_evidence — `Constitutive Δfur derepression, not iron limitation, sets the permissive envelope state`

This slide closes S1 with three converging pieces of evidence. Together they rule out iron limitation as the primary explanation for our signal and establish Δfur as a genetic necessity for lipid A-loss viability — not a correlate of low iron availability.

The grounding for the first piece comes from inside Leaden's own 2018 paper. Leaden measured both a Δfur transcriptome and an iron-limitation transcriptome — induced by 2,2'-dipyridyl chelation — in the same C. crescentus NA1000 background. Comparing those two logFC axes directly, the figure shows the responses overlap but are not identical: the Δfur genetic response includes gene movements that iron chelation alone does not produce. This non-identity, documented within a single paper and single genetic background, is Leaden's own internal evidence that constitutive Δfur allele derepression is a biologically distinct state from iron-starvation response.

The second bullet makes the SspB arm concrete at the gene level. Of the 93 Leaden Δfur DEGs, 53 are buffered in our Δfur ΔsspB data — near-zero logFC in our strain despite logFC −5 to −9 in Leaden. These 53 are dominated by the cbb3/cyd/fix-NOPQ micro-aerobic respiratory operon: CCNA_01466–01476, encoding ccoNOPQ, cydCDA, fixGHI. ΔsspB protects this operon at the transcript level. Whether that protection is mechanistically critical for the Δlpxc rescue is precisely what S2 tests with Caulobacter Fitness Browser enrichment analysis, so the speaker should name this as the bridge to S2 rather than claiming it here.

The third piece is the genetic anchor from Zik et al. 2022 (PMID 35649364). Their suppressor genetics established that Δlpxc rescue requires the Δfur allele. REPORT §Literature Context quotes their language directly: "Alterations in Fur-regulated processes, rather than iron status per se, underlie the ability to survive when lipid A synthesis is blocked." That genetic necessity — Δfur required, not merely correlated — is the chain the rest of this talk pulls on.

The scope caveat on the iron-discrimination result must be stated plainly: REPORT §Limitations names this as a single-condition scope boundary. The Leaden iron-limitation comparison was performed in the NA1000 background under dipyridyl chelation — not in our Ryan-lab strain under our growth conditions. Whether the Δfur-vs-iron-limitation distinction holds in magnitude or gene-membership under minimal medium or bipyridyl chelation in our strain background is untested. This is directional support — consistent with constitutive derepression — not a multi-condition proof. Iron-limitation experiments are also absent from the Caulobacter Fitness Browser compendium, so the fitness-based analysis in S2 is envelope-stress-only. With the Fur driver established, S2 asks which subset of the 32 Fur-released concordant-strong genes actually enriches for envelope-stress fitness phenotypes above the 33.25% genome background.
