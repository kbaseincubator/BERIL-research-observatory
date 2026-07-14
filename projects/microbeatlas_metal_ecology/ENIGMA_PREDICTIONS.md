# ENIGMA Metal-Resistance OTU Predictions
_MicrobeAtlas Metal Ecology Project · BERIL Research Observatory_

---

## 1. Global analysis summary

A global meta-analysis of 463,972 16S amplicon samples (98,919 OTUs at 97% identity) linked to GTDB r214 pangenome metal-AMR annotations reveals that **metal-resistance diversity is environmentally labile** (Pagel's λ = 0.335 for # metal types, Bacteria), while nitrification is strongly phylogenetically conserved (λ = 1.000). Ecological niche breadth shows intermediate signal (λ = 0.787). Only 902 of 3,160 genera (29%) carry detectable metal AMR genes; among these, a composite score (niche breadth × metal diversity) identifies **435 candidate OTUs** spanning 215 in the top-10% by both metrics and 220 nitrifier positive controls.

## 2. Candidate genera — metal resistance summary

_(Only genera with ≥1 candidate OTU shown; max 15 rows. Full table: `data/metal_resistance_table_refined.csv`)_

| Genus | OTUs | Rep. OTU | Metal types | Key genes (≤2 per metal) |
| --- | --- | --- | --- | --- |
| *Pseudomonas* | 56 | `97_39338` | Ag, As, Cr, Cu, Hg, other | Ag: silA, silB | As: arsD, arsB | Cr: chrA | Cu: copA, copC | Hg: merP, merA | o… |
| *Staphylococcus* | 33 | `97_9189` | As, Cd, Hg, Te, other | As: arsB, arsC | Cd: cadC | Hg: merA, merB | Te: tcrB | other: cadD, mco |
| *Serratia* | 12 | `97_66129` | Ag, As, Hg, other | Ag: silA, silC | As: arsC, arsD | Hg: merA, merP | other: blaSPR, silE |
| *Alkalihalobacillus* | 11 | `97_81636` | Hg, other | Hg: merA | other: merF |
| *Stenotrophomonas* | 9 | `97_86512` | As, Cr, Cu, Hg, other | As: arsD | Cr: chrA | Cu: copA, copB | Hg: merA, merP | other: blaL1, bla |
| *Faecalibacterium* | 9 | `97_50582` | As, Hg | As: arsD | Hg: merA, merC |
| *Klebsiella* | 6 | `97_56843` | Ag, As, Hg, Te, other | Ag: silA, silB | As: arsC, arsD | Hg: merA, merP | Te: tcrB | other: pcoA, pcoS |
| *Noviherbaspirillum* | 6 | `97_12431` | As, Hg, other | As: arsD | Hg: merP | other: arsN2 |
| *Citrobacter* | 5 | `97_14443` | Ag, As, Cr, Hg, other | Ag: silP, silA | As: arsC, arsD | Cr: chrA | Hg: merA, merP | other: silS, pcoR |
| *Priestia* | 5 | `97_74217` | As, Hg, other | As: arsD | Hg: merA, merT | other: merR1, merF |
| *Enterococcus* | 4 | `97_51587` | Ag, As, Cd, Cu, Hg, Te, other | Ag: silA, silB | As: arsD, arsB | Cd: cadC, cadA | Cu: copB, copA | Hg: merA, me… |
| *Escherichia* | 3 | `97_26` | Ag, As, Hg, other | Ag: silA, silB | As: arsR, arsC | Hg: merA, merD | other: sslE, pcoD |
| *Aeromonas* | 3 | `97_80244` | Ag, As, Hg, other | Ag: silA, silB | As: arsD, arsC | Hg: merP, merA | other: cphA, merF |
| *Chelatococcus* | 3 | `97_4453` | Hg, other | Hg: merA | other: merF |
| *Rhodopseudomonas* | 3 | `97_329` | Hg, other | Hg: merA | other: merF |

## 3. Testable hypotheses

For the 8 highest-priority OTUs (top-scoring by niche breadth × metal-type diversity), each hypothesis specifies: metal condition, expected direction, representative OTU, and mechanism.

**Klebsiella** `97_56843` — Under **Ag or Te stress**, relative abundance should increase ≥2-fold vs. metal-free controls (n_metal_types = 3.53; metals: Ag, As, Hg, Te). Mechanism: resistance determinants `silA/B, arsC, merA/P, tcrB` neutralise metal toxicity, creating competitive advantage over susceptible community members.

**Enterococcus** `97_51587` — Under **Cu or Cd stress**, relative abundance should increase ≥2-fold vs. metal-free controls (n_metal_types = 3.33; metals: Ag, As, Cd, Cu, Hg, Te). Mechanism: resistance determinants `arsD/B, cadC/A, copB/A, merA` neutralise metal toxicity, creating competitive advantage over susceptible community members.

**Citrobacter** `97_14443` — Under **As or Hg stress**, relative abundance should increase ≥2-fold vs. metal-free controls (n_metal_types = 3.7; metals: Ag, As, Cr, Hg). Mechanism: resistance determinants `silP/A, arsC/D, chrA, merA/P` neutralise metal toxicity, creating competitive advantage over susceptible community members.

**Franconibacter** `97_3668` — Under **Ag or As stress**, relative abundance should increase ≥2-fold vs. metal-free controls (n_metal_types = 3.5; metals: Ag, As, Hg). Mechanism: resistance determinants `silP/A, arsC, pcoA/B` neutralise metal toxicity, creating competitive advantage over susceptible community members.

**Noviherbaspirillum** `97_12431` — Under **As stress**, relative abundance should increase ≥2-fold vs. metal-free controls (n_metal_types = 3.0; metals: As, Hg). Mechanism: resistance determinants `arsD, merP, arsN2` neutralise metal toxicity, creating competitive advantage over susceptible community members.

**Serratia** `97_66129` — Under **Hg stress**, relative abundance should increase ≥2-fold vs. metal-free controls (n_metal_types = 2.44; metals: Ag, As, Hg). Mechanism: resistance determinants `silA/C, arsC/D, merA/P` neutralise metal toxicity, creating competitive advantage over susceptible community members.

**Aeromonas** `97_80244` — Under **As+Hg co-stress**, relative abundance should increase ≥2-fold vs. metal-free controls (n_metal_types = 2.24; metals: Ag, As, Hg). Mechanism: resistance determinants `silA/B, arsD/C, merP/A` neutralise metal toxicity, creating competitive advantage over susceptible community members.

**Pseudomonas** `97_39338` — Under **Cu stress**, relative abundance should increase ≥2-fold vs. metal-free controls (n_metal_types = 2.13; metals: Ag, As, Cr, Cu, Hg). Mechanism: resistance determinants `copA/C, arsD/B, chrA, merP/A` neutralise metal toxicity, creating competitive advantage over susceptible community members.

## 4. Experimental feasibility

**Detection limit:** ≥0.1% relative abundance (≥10 reads at 10,000 reads/sample). OTUs at 1% abundance are quantified with CV ≈ 10%; rarer OTUs risk stochastic dropout and should not be tracked without ≥50,000 reads/sample.

**Statistical power:** For an OTU at 1% abundance, a 2-fold increase is detectable with >99% power using 3 replicates at 10,000 reads. The binding constraint is **multiple testing**: tracking all 435 candidates requires FDR correction that demands large effects. Restrict tracked OTUs to the pre-confirmed shortlist of 5–10.

**ENIGMA inoculum:** Sequence inoculum pre-treatment (5 replicates, ≥50,000 reads). Confirm which of the 8 shortlisted OTUs are detectable at ≥0.1%; restrict experiment to confirmed OTUs (expected: 3–5). Apply FDR correction within that set only.

**Recommended design:**
- 4–6 metal-stress treatments (single metal + 1 co-contamination control)
- 5 replicates per treatment × ≥50,000 reads/sample
- 7- and 14-day time points
- Primary endpoint: relative abundance fold-change vs. metal-free control
- Backup: genus-level qPCR for *Pseudomonas*, *Citrobacter*, *Enterococcus* if OTU-level tracking fails

Full feasibility document: `feasibility_individual_otus.md`  
Full hypotheses with mechanistic detail: `data/hypotheses_refined.md`  
Honorable mentions (no candidate OTUs): `data/honorable_mentions.md`
