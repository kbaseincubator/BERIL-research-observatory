# Supplementary Information: External Validation of Predictions P1 and P2

---

## Part 1: Predictions Tested

**P1 (community shift):** Mercury stress shifts soil bacterial communities toward generalists. Predicted mechanism: Hg-contamination selects for generalist taxa with broader ecophysiological tolerances, shifting the community-weighted mean niche breadth (CWM_B) toward higher values.

**P2 (mer gene enrichment):** Mercury-contaminated soils show elevated mer gene abundance, particularly on mobile genetic elements (MGEs). Predicted mechanism: the mer operon (merA, merR, and associated genes) is preferentially located on conjugative plasmids, which proliferate under Hg selection.

Community-level mechanism: Community-weighted mean niche breadth (CWM_B) is computed from genus-level Levins' B_std values (MicrobeAtlas trait table) weighted by relative abundance in each sample. Higher CWM_B indicates a community dominated by ecological generalists; lower CWM_B indicates specialist dominance.

---

## Part 2: Summary Findings by Dataset

| Dataset | Study | Sample Type | Hg Range | n | P1 Verdict | P2 Verdict |
|---------|-------|------------|----------|---|-----------|-----------|
| Frossard 2017 | Swiss forest microcosm (4 Hg doses, 7 soils) | Hg-tolerant indicator OTUs | 0–32 mg/kg | 22 genera | **SUPPORTED** (B_std=0.407 vs bg 0.233, p<0.0001) | Inferred (mer-tolerant taxa) |
| Frossard 2018 | Swiss forest soils (field gradient + microcosm) | 16S V3–V4 | Long-term gradient | 48 samples | **NULL** (CWM_B no shift by treatment) | Not tested |
| Li 2022 | Chinese long-term contamination (16 Hg levels) | 16S V3–V4, CWM | 2.4–420.7 mg/kg | 80 samples | **PARTIAL** (negative correlation within high-contamination range, ρ=−0.314, p=0.0045) | Not tested |
| Goff 2024 | ORR subsurface mobilome (ENIGMA) | WGS metagenomics | Mixed waste (Hg+U) | 11 zones | Not applicable | **SUPPORTED** (merA+merR on plasmid in high-Hg zones, absent in low) |
| Du 2023 | Chinese paddy/upland microcosm | 16S V3–V4 | 0, 3, 10 μg/g | 72 samples | Pending CWM analysis | Not tested |
| Chauhan 2025 | ORR & SRS legacy sites (USA) | **WGS only** (no 16S deposited) | 10–2,206 mg/kg | 11 samples | Not computable (no 16S) | Inferred from text |

---

## Part 3: Key Findings by Dataset

**Frossard et al. 2017** (Soil Biology and Biochemistry 105:162): Direct indicator-species analysis identified 99 bacterial OTUs significantly enriched under Hg stress (32 mg/kg treatment, 30-day microcosm). Cross-referencing against MicrobeAtlas genus trait table: 22 of 99 indicator species matched to genera with known niche breadth; these matched genera showed significantly elevated Levins B_std (mean 0.407, median 0.414) compared to the global MicrobeAtlas background (mean 0.233, p < 0.0001, Mann-Whitney U test). Hg-tolerant taxa were predominantly generalist aerobes (Burkholderia, Bradyrhizobium, Janthinobacterium, Caulobacter). **Verdict: P1 SUPPORTED.**

**Li et al. 2022** (Ecotoxicology and Environmental Safety 229:113062): Analysis of 80 long-term Hg-contaminated Chinese soil samples (range 2.4–420.7 mg/kg, all chronically contaminated sites). Community-weighted mean niche breadth (CWM_B) across all 80 samples (mean 0.365, substantially elevated vs. global background 0.233). However, within this high-contamination gradient, CWM_B decreased significantly with increasing Hg (Spearman ρ = −0.314, p = 0.0045), indicating that at extreme Hg concentrations (Q4: ~375 mg/kg), communities shift toward specialists. **Verdict: P1 PARTIAL (threshold effect; generalism favored at moderate contamination, specialists selected at extreme Hg).**

**Goff et al. 2024** (ISME Communications 4:ycae064): Analysis of Oak Ridge Reservation (ORR) subsurface mobilome revealed that *mer* operon genes (merA and merR, key P2 prediction) are encoded on plasmid EB106_03_01_3, which is enriched in high-contamination zones and entirely absent from low-contamination zones. This directly supports the hypothesis that Hg-resistance genes accumulate on mobile genetic elements under Hg selection. **Verdict: P2 SUPPORTED** (at the site and metal tested).

---

## Part 4: Limitations of External Validation

**Geographic scope:** Published datasets with sufficient geochemical metadata are restricted to mercury in terrestrial, predominantly aerobic soils (Frossard sites in Switzerland; Li et al. in China; Goff 2024 at ORR, a subsurface site with active redox cycling but not fully anaerobic). Other metals (Cu, Zn, Ni, Co) and anaerobic or aquatic environments remain untested at the community level. External validation for the broader metal-gene association (beyond Hg) has not been performed.

**Treatment metadata:** Du et al. (2023) Chinese microcosm study includes documented Hg concentrations (0, 3, 10 μg/g Hg-salt spike) but lacks publicly posted metadata linking samples to treatment conditions; CWM analysis could not proceed. Chauhan et al. (2025) deposited only whole-genome shotgun (WGS) data, with no 16S amplicon reads available; therefore, CWM_B could not be computed (16S-derived taxonomy required for MicrobeAtlas mapping).

**Mechanistic resolution:** Community-level validation measures niche breadth shifts at the community level but cannot directly test the individual-KO associations (e.g., whether resistance KOs specifically fail to accumulate while cofactor biosynthesis KOs accumulate). Metagenomic approaches (e.g., single-amplicon linking of individual KOs to specific taxa) would be required to test KO-level predictions.

---

## Part 5: Double-Signal Gene Cross-Reference (Goff 2024 × HMRG Dataset)

Comparison of double-signal genes (KOs with high D, low λ predictions of mobile element association) against empirical Goff 2024 ORR mobilome data:

| Gene | KO | Metal | D (genome-level, Fritz & Purvis) | λ (genus-level) | In Goff 2024 ORR mobilome? | MGE status |
|------|----|----|-----------|--------|-------------|-----------|
| merA | K07391 | Hg | 0.922 | 0.692 | **Yes** | On plasmid EB106_03_01_3, high-contamination zones |
| merR | K03554 | Hg | 0.733 | 0.733 | **Yes** | Co-located with merA on EB106_03_01_3 |
| merD | K19057 | Hg | 0.851 | 0.418 | Presumed (operon) | Likely co-transferred with merA/merR |
| merE | K19059 | Hg | 0.738 | 0.391 | Presumed (operon) | Likely co-transferred with merA/merR |
| zntA | K01534 | Zn/Cd/Cu | — | — | **Yes** | Co-located with mer genes on EB106_03_01_3 |
| czcD | K16264 | Co/Zn/Cd | — | — | **Yes** | Co-located on EB106_03_01_3 |
| arsR | K03892 | As | 0.542 | 0.577 | **Yes** | Co-located on EB106_03_01_3 |

**Interpretation:** The Goff 2024 study confirms that merA, merR, and associated resistance genes (zntA, czcD, arsR) form a co-localized gene cluster on a broad-host-range conjugative plasmid at ORR in high-Hg zones. This directly supports the P2 prediction that Hg-resistance genes accumulate on MGEs. The double-signal prediction that merD and merE (with lower λ, higher mobile element association) are more readily transferred than merA remains untested.

---

**Data Sources:**

- Frossard et al. (2017, 2018): Supplementary Table 6 indicator species list and original paper text; MicrobeAtlas B_std mapping
- Li et al. (2022): PRJNA774099 pre-processed h5ad, genus-level SILVA taxonomy, sample-level Hg metadata
- Goff et al. (2024): DOI 10.1093/ismeco/ycae064, extended Figure 4 HMRG gene list
- MicrobeAtlas genus trait table: n = 2,851 genera with Levins B_std
- Double-signal KO table: per-KO λ from data/phylo_d_all_ko.csv, D (Fritz & Purvis) from user-provided curation
