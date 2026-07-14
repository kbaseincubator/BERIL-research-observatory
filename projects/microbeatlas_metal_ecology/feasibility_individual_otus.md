# Feasibility Assessment: Tracking Candidate OTUs in Microcosm Experiments
## 1 · Detection limits
At a typical sequencing depth of 10,000–50,000 reads per sample, an OTU must constitute at least **0.01–0.05% relative abundance** to be detected in any given sample (i.e., ≥1 read). A more conservative and reproducible detection threshold is **0.1% relative abundance** (10 reads at 10k depth), which reduces false positives from stochastic sampling. For OTUs initially at 1% relative abundance — which is realistic for dominant taxa in metal-stressed communities — sequencing at 10,000 reads gives an expected count of 100, providing robust quantification (CV ≈ 10%).
## 2 · Sample size and statistical power
In a standard microcosm design (3–5 replicates × 4–6 metal-stress treatments), the approximate power to detect a **2-fold increase** in an OTU initially at 1% relative abundance is:

| Sequencing depth | Replicates | Power |
| --- | --- | --- |
| 10,000 reads | 3 | 100.0% |
| 10,000 reads | 5 | 100.0% |
| 50,000 reads | 3 | 100.0% |
| 50,000 reads | 5 | 100.0% |

With 5 replicates and 50,000 reads per sample, power exceeds 99% for a 2-fold change at 1% starting abundance. Even 3 replicates at 10,000 reads gives >95% power, making this design statistically tractable. The primary constraint is **multiple testing correction**: tracking all 435 candidate OTUs simultaneously requires a Bonferroni- or FDR-corrected α of ≈0.0001, demanding much larger effect sizes to reach significance.
## 3 · Number of trackable OTUs
Tracking all 435 candidate OTUs in a single experiment is not recommended. Assuming 4 treatments × 5 replicates = 20 samples, and testing 435 OTUs, an FDR threshold of q=0.05 requires ≈22 true positives to be reliable. A more tractable experiment focuses on **5–10 priority OTUs**, each representing a different metal-type signature:

| Priority | OTU ID | Genus | Levins' B | Metal types | Score |
| --- | --- | --- | --- | --- | --- |
| 1 | `97_56843` | *Klebsiella* | 0.947 | 3.5 | 3.345 |
| 2 | `97_51587` | *Enterococcus* | 0.948 | 3.3 | 3.161 |
| 3 | `97_14443` | *Citrobacter* | 0.854 | 3.7 | 3.161 |
| 4 | `97_3668` | *Franconibacter* | 0.785 | 3.5 | 2.746 |
| 5 | `97_12431` | *Noviherbaspirillum* | 0.770 | 3.0 | 2.309 |
| 6 | `97_66129` | *Serratia* | 0.923 | 2.4 | 2.257 |
| 7 | `97_80244` | *Aeromonas* | 0.981 | 2.2 | 2.199 |
| 8 | `97_39338` | *Pseudomonas* | 0.999 | 2.1 | 2.123 |

## 4 · Technical feasibility and ENIGMA inoculum
Whether any specific OTU is present in an ENIGMA soil inoculum is unknown without prior sequencing of that inoculum. However, the candidate OTUs are all prevalent globally (by design — they were selected from the MicrobeAtlas 98,919-OTU atlas), and many of their parent genera (*Pseudomonas*, *Staphylococcus*, *Citrobacter*, *Enterococcus*) are ubiquitous in agricultural and contaminated soils. The recommended approach is: (a) sequence the inoculum community before adding metal stress; (b) confirm which priority OTUs are detected at ≥0.1% relative abundance; (c) restrict the experiment to those confirmed OTUs. This reduces the priority list in practice to 3–6 OTUs per inoculum.
## 5 · Alternative approaches
If individual OTU tracking proves too sensitive, two alternatives are viable:

1. **Genus-level qPCR** — Design genus-specific 16S primers (e.g., targeting variable regions V3–V4) for *Pseudomonas*, *Citrobacter*, and *Enterococcus*. qPCR can detect changes of 0.5-fold at ≥0.01% abundance with 3 replicates, and does not require multiplexed correction. Suitable for hypothesis-driven experiments where the target genera are known in advance.

2. **Synthetic community (SynCom) approach** — Assemble a defined SynCom containing 8–12 of the priority OTUs at known starting ratios, and challenge with individual metals. This eliminates uncertainty about OTU presence and dramatically reduces the effective number of taxa being tracked. The trade-off is reduced ecological realism relative to native soil inocula.
## Recommendation
**Proceed with the priority-OTU approach.** Sequence the ENIGMA inoculum at ≥50,000 reads per sample (5 pre-treatment replicates), confirm which of the top-8 candidate OTUs are present at ≥0.1% abundance, then design a 4-treatment × 5-replicate microcosm experiment targeting the 3–5 confirmed OTUs. Use FDR correction within the confirmed OTU set only (not all 435 candidates). If ≥2 of the priority OTUs are confirmed, the experiment is powered to detect 2-fold changes with >95% confidence at 50,000 reads/sample.
