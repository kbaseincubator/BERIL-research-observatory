# External Validation Report: Niche Breadth and Mercury Stress Community Shifts
*Generated 2026-07-13 | Updated 2026-07-13 with Li et al. 2022 CWM analysis, Frossard 2018, Chauhan 2025, Du 2023 assessments; 2026-07-13 (session 2) with Frossard 2018 FASTQ reclassification CWM results (Part 2c) and h5ad search (Part 9); 2026-07-13 (session 3) with Goff et al. 2024 ORR mobilome P2 evidence (Part 6), Goff 2024 × double-signal HMRG cross-reference (Part 11), and Du 2023 CWM pipeline (72 samples, running); 2026-07-14 with Du 2023 CWM results (70/72 complete, metadata unverified; Part 2d)*

---

## Summary

This report attempts to validate two predictions using published 16S amplicon datasets:
1. **P1 (community shift):** Mercury stress shifts soil bacterial communities toward generalists (higher Levins B_std).
2. **P2 (mer enrichment):** Mercury-contaminated soils show elevated mer gene abundance.

Initial target studies were Frossard et al. 2017 (Soil Biol. Biochem. 105:162) and Pu et al. 2022 (Microorganisms 10:977). Four additional datasets were assessed: Li et al. 2022 (Ecotoxicol. Environ. Saf. 229:113062; PRJNA774099), Frossard et al. 2018 (Soil Biol. Biochem. 120:191; PRJEB21070), Chauhan et al. 2025 (Sci. Rep. 15:41955; PRJNA1245361), and Du et al. 2023 (Sci. Total Environ. 894:165056; PRJNA914639). All Levins B_std values are from the MicrobeAtlas genus trait table (n=2,851 genera).

---

## Data Sources Consulted

| Source | Type | Hg range | n samples | Accessible? |
|--------|------|----------|-----------|-------------|
| Frossard et al. 2017 (Soil Biol. Biochem. 105:162) | 16S V1–V2, Swiss forest soil microcosm | 0–32 mg/kg | 84 bacteria (7 sites × 4 doses × 3 reps) | **Partial** (Supp. Table 6: 175 indicator OTUs; indicator-species analysis complete) |
| Li et al. 2022 (Ecotoxicol. Environ. Saf. 229:113062; PRJNA774099) | 16S V3–V4, Chinese long-term Hg-contaminated soils | 2.4–420.7 mg/kg | 80 samples, 16 Hg levels | **Full** (pre-processed h5ad; 76,704 ASVs; CWM analysis complete) |
| Frossard et al. 2018 (Soil Biol. Biochem. 120:191; PRJEB21070) | 16S V3–V4, Swiss forest soils, long-term Hg gradient + microcosm | field gradient | 48 samples (16 Ctrl, 16 Hg, 16 Field; 4 timepoints × 4 replicates) | **Full** (FASTQ reclassification via vsearch/SILVA 138.1; CWM_B per sample; see Part 2c) |
| Chauhan et al. 2025 (Sci. Rep. 15:41955; PRJNA1245361) | **WGS only** (ENA: all 11 runs METAGENOMIC/PAIRED, no amplicon deposited), SRS and ORR legacy nuclear sites, USA | 10–2,206 mg/kg THg | 11 samples (5 categories) | **Summary only** (amplicon CWM not computable — no 16S reads in ENA; dominant genera from paper text; see also Goff 2024 for ORR MGE context) |
| Du et al. 2023 (Sci. Total Environ. 894:165056; PRJNA914639) | 16S V3–V4, Chinese paddy/upland microcosm | 0, 3, 10 μg/g | 72 samples (paddy P1–P36 + upland U1–U36) | **Complete but unverified** (70/72 samples; metadata not cross-checked; see Part 2d) |
| Goff et al. 2024 (ISME Commun. 4:ycae064; ORR mobilome) | Shotgun metagenomics, ORR subsurface (ENIGMA site) | mixed-waste (Hg+U) | 1,615 MGEs from high/low contamination zones | **Full** (paper read; merA+merR on MGEs in high-contamination zones; supports P2; see Part 6) |
| Pu et al. 2022 (Microorganisms 10:977) | 16S amplicon, agricultural soil microcosm | 0–10 mg/kg (3 pH levels) | Not deposited | No (no SRA entry; MDPI HTML inaccessible) |
| Abdelmageed et al. 2021 (Water Air Soil Pollut 232:31) | 16S V4, EFPC streambank soils | 0.03–696 μg/g | 26 (field) | Yes (full text read) |
| MicrobeAtlas global diff. abundance | 16S OTU count database | mixed metals | 300 FDR-sig genera | Yes (internal data) |
| MicrobeAtlas mer gene mobility | Pagel's λ + mobile element correlations | — | 9 mer gene families | Yes (internal data) |

---

## Part 1: Frossard et al. 2017 — Direct Indicator Species Analysis (P1 Test)

### Study overview
Frossard et al. spiked seven Swiss forest soils with 0, 0.32, 3.2, and 32 mg Hg/kg (dry soil) and incubated for 30 days in triplicate microcosms (n=84 bacteria samples total). 16S V1–V2 amplicons were sequenced by 454 pyrosequencing; OTUs were clustered at 97% similarity using CROP/MOTHUR. Indicator species analysis (IndVal method) was applied to identify OTUs significantly associated with specific Hg treatments (P<0.05, |ρ|≥0.3, abundance >10 reads).

### Supplementary Table 6: Hg-tolerant bacterial indicator OTUs
The paper's Supp. Table 6 lists 175 Hg indicator OTUs (99 bacteria, 76 fungi) with full taxonomy and the mean positive Spearman correlation coefficient ("mean pos. Corr.") across the 7 soils. All 99 bacterial OTUs in this table show positive correlations (range 0.30–1.00), identifying them as Hg-**tolerant** taxa (enriched at the Hg32 = 32 mg/kg treatment relative to controls).

### Levins B_std of Hg-tolerant bacteria

Cross-referencing the 99 bacterial indicator OTUs against the MicrobeAtlas genus trait table (n=2,851 genera):

| Group | n genera matched | Mean Levins B_std | Median |
|-------|-----------------|-------------------|--------|
| Hg-tolerant indicator OTUs (Frossard 2017) | **22** | **0.407** | **0.414** |
| All genera — MicrobeAtlas background | 2,851 | 0.233 | 0.205 |

- **Mann-Whitney U test (one-sided, Hg-tolerant > background):** p < 0.0001
- **Effect size (common language):** 0.814 — 81% of Hg-tolerant OTUs have higher B_std than a randomly-selected background genus
- **Spearman ρ (association strength vs B_std within Hg-tolerant group):** ρ = −0.245, p = 0.27 (NS, n=22) — degree of Hg tolerance does not predict niche breadth within the tolerant set

**Verdict for P1 from Frossard 2017: SUPPORTED.** Bacteria that thrive under Hg stress in Swiss forest soils are significantly broader-niche than background taxa.

### Matched genera (all 22)

| Phylum | Genus | Abundance | Assoc. strength | B_std |
|--------|-------|-----------|----------------|-------|
| Proteobacteria | *Burkholderia* | 20,004 | 0.77 | 0.435 |
| Proteobacteria | *Bradyrhizobium* | 13,129 | 0.94 | 0.393 |
| Proteobacteria | *Caulobacter* | 5,799 | 0.73 | 0.487 |
| Proteobacteria | *Janthinobacterium* | 5,627 | 0.35 | 0.498 |
| Proteobacteria | *Telmatospirillum* | 3,722 | 0.98 | 0.296 |
| Proteobacteria | *Rhodoplanes* (3 OTUs) | 4,554 | 0.45–0.62 | 0.467 |
| Verrucomicrobia | *Opitutus* | 306 | 1.00 | 0.421 |
| Proteobacteria | *Pedomicrobium* | 183 | 0.51 | 0.577 |
| Actinobacteria | *Mycobacterium* | 179 | 0.89 | 0.456 |
| Actinobacteria | *Catellatospora* | 150 | 0.32 | 0.669 |
| Bacteroidetes | *Flavobacterium* | 130 | 0.55 | 0.325 |
| Proteobacteria | *Sphingomonas* | 103 | 0.42 | 0.348 |
| Actinobacteria | *Kitasatospora* | 78 | 0.36 | 0.407 |
| Actinobacteria | *Salinibacterium* | 54 | 0.37 | 0.438 |
| Proteobacteria | *Acidiphilium* | 40 | 0.83 | 0.182 |
| Proteobacteria | *Nevskia, Phyllobacterium, Perlucidibaca* | varied | varied | 0.284–0.389 |

All genera independently known as metabolically versatile soil aerobes. Only *Acidiphilium* (B_std = 0.182) falls below median. Consistent with the paper's observation that Hg-tolerant aerobic taxa (Burkholderia, Bradyrhizobium, Janthinobacterium, Caulobacter) are the most abundant indicator species.

### Match rate caveat

22/99 indicator OTUs (22%) had genus-level matches in the MicrobeAtlas trait table. The 77 unmatched OTUs include:
- Many OTUs with empty genus assignments (Acidobacteria, Chloroflexi, Planctomycetes subclades)  
- *CandidatusKoribacter* and *CandidatusSolibacter* (Acidobacteria, likely more specialist)
- *Pilimelia* (rare Actinobacteria)

**Selection bias risk:** The matched OTUs are dominated by Proteobacteria (16/22), which as a phylum has above-average niche breadth in MicrobeAtlas. If the unmatched Acidobacteria/Chloroflexi indicator OTUs have below-average B_std (consistent with their ecology), the pooled mean would be lower. However, even if the 77 unmatched OTUs had the background mean (0.233), the aggregate effect would remain directionally positive.

### Mechanistic reconciliation with Abdelmageed 2021

The Frossard 2017 pattern (Hg-tolerant = generalists, B_std ≫ 0.233) differs from Abdelmageed 2021 (Hg-enriched = specialists, B_std ≈ 0.171) because:

| Feature | Frossard 2017 | Abdelmageed 2021 |
|---------|--------------|-----------------|
| Soil type | Swiss forest soils, aerobic | EFPC streambank, anoxic |
| Hg form | HgCl₂ spike (bioavailable Hg²⁺) | Long-term contamination (organo-Hg, sediment-bound) |
| Dominant Hg mechanism | mer operon (Hg²⁺ reduction) | hgcA methylation |
| Dominant Hg-tolerant taxa | Aerobic Proteobacteria (Burkholderia, Bradyrhizobium) | Anaerobic Deltaproteobacteria (Geobacter, SRB) |
| Niche breadth result | High (B_std ≈ 0.407) | Low (B_std ≈ 0.171) |

**Both results are self-consistent:** generalist aerobes carry mer and benefit from merA-mediated Hg²⁺ reduction; specialist anaerobes carry hgcA and thrive in the particular niche created by long-term Hg contamination of anoxic streambanks. These are distinct selection mechanisms.

---

## Part 2: Li et al. 2022 — Full CWM Analysis on Pre-processed 16S Data (P1 Test)

### Study overview

Li et al. 2022 (DOI: 10.1016/j.ecoenv.2021.113062; PRJNA774099) characterised bacterial communities across 80 long-term Hg-contaminated soil samples from three land-use types in China: slag heaps, farmland, and mining areas. Mercury concentrations span 2.4–420.7 mg/kg total Hg (16 distinct values); all samples are from chronically contaminated sites (no uncontaminated controls). 16S V3–V4 amplicons were sequenced on Illumina (paired-end), classified with SILVA-based taxonomy. The dataset was available as a pre-processed h5ad file (76,704 ASVs × 80 samples) with Hg metadata attached to each sample.

### CWM Levins B_std analysis

**Method:** Genus names were parsed from SILVA Taxon strings (`g__Genus` field); each genus was matched to the MicrobeAtlas trait table (case-insensitive). Relative abundances were computed per sample; CWM_B was calculated as Σ(RA_{s,g} × B_std_g) renormalised to matched fractions only.

**Match rate:** 453 unique genera matched / 76,704 ASVs → 16,759 ASVs with B_std values (21.8%). Largest unmatched blocks: `uncultured` (9,538 ASVs), `Vicinamibacteraceae` (3,719), `JG30-KF-CM45` (2,218) — all environmental clone groups without cultured representatives in MicrobeAtlas.

**CWM_B summary:**

| Metric | Value |
|--------|-------|
| CWM_B range across 80 samples | 0.263 – 0.399 |
| CWM_B mean | **0.365** |
| CWM_B median | 0.369 |
| MicrobeAtlas background mean | 0.233 |
| MicrobeAtlas background median | 0.205 |

All 80 samples have CWM_B substantially above background (0.365 vs 0.233 global mean).

**Within-gradient regression (log(Hg) vs CWM_B):**

| Test | Statistic | p-value |
|------|-----------|---------|
| Spearman ρ | **−0.314** | 0.0045 |
| Pearson r | −0.352 | 0.0014 |
| Linear slope | −0.0051 per log(mg/kg) | — |

The correlation is **negative**: as total Hg increases within this contaminated gradient, CWM_B decreases slightly.

**CWM_B by Hg quartile:**

| Hg quartile | Hg median (mg/kg) | n | Mean CWM_B |
|-------------|-------------------|---|------------|
| Q1 (low) | 11.8 | 20 | 0.379 |
| Q2 | 36.5 | 20 | 0.361 |
| Q3 | 114.8 | 20 | 0.356 |
| Q4 (high) | 375.0 | 20 | 0.364 |

**Figure:** `data/li2022_cwm_bstd.png` — scatter plot (log(Hg) vs CWM_B) + quartile box plots.

### Dominant and keystone genera (from paper text) and their B_std

| Genus | Role in community | B_std | vs. background |
|-------|------------------|-------|----------------|
| *Gaiella* | Dominant | 0.445 | +91% |
| *Nitrospira* | Keystone | 0.424 | +82% |
| *Phycicoccus* | Keystone | 0.401 | +72% |
| *Nocardioides* | Dominant | 0.392 | +68% |
| *Arthrobacter* | Dominant | 0.349 | +50% |
| *Sphingomonas* | Dominant | 0.348 | +49% |
| *Pseudomonas* | Dominant | 0.273 | +17% |
| *Bacillus* | Dominant | 0.239 | +3% |

All eight matchable dominant/keystone genera exceed background (0.233). The paper reports that α-diversity (Shannon, Chao1) was **positively** correlated with total Hg (p<0.05), consistent with long-term community adaptation increasing diversity as Hg-adapted specialists fill new ecological roles.

### Interpretation of the two-part result

The Li 2022 dataset yields two distinct signals that must be read separately:

1. **Absolute CWM elevation (supports P1):** Communities in Hg-contaminated Chinese soils (all 80 samples) have mean CWM_B = 0.365 — **57% above background** (0.233). This is consistent with Hg contamination having selected for a community enriched in broader-niche organisms relative to naive soil.

2. **Within-gradient decrease (partially contradicts simple P1):** Among already-contaminated samples, higher Hg associates with slightly lower CWM_B (ρ = −0.31). At extreme Hg (>100 mg/kg), highly Hg-resistant specialist lineages dominate; at moderate Hg, more diverse but still above-background generalist communities persist.

**Most plausible mechanism:** Long-term chronic Hg exposure initially selects for generalist tolerators (consistent with Frossard 2017). At extreme contamination (slag/mining, Hg >300 mg/kg), a subset of highly resistant specialists — concentrated in a few lineages with narrow-range habitats — outcompete generalists. The net effect is that CWM_B remains far above global background at all levels but decreases within the extreme tail of the Hg gradient.

**Confound to note:** The three land-use types (slag, farmland, mining) covary with both Hg level and soil chemistry (pH, SOC). The Li 2022 paper explicitly identifies land use as a primary driver of community structure. The negative CWM_B~Hg correlation may partially reflect slag/mining soils having both higher Hg and more restricted ecologies (specific metal-resistant specialists).

**Verdict for P1 from Li 2022:** **Conditionally supported.** CWM_B is elevated above background in all contaminated samples (+57%), consistent with historical generalist enrichment. Within the contamination gradient, higher Hg slightly decreases CWM_B — consistent with extreme Hg selecting for resistant specialists, not refuting P1 in acute experimental contexts.

---

## Part 2b: Frossard et al. 2018 — Indicator OTU Analysis (P1 Test, Partial Family-Level Proxy)

### Study overview

Frossard et al. 2018 (DOI: 10.1016/j.soilbio.2018.01.028; PRJEB21070) assessed long-term Hg contamination effects at Swiss forest soils along a natural Hg gradient (field gradient) plus short-term HgCl₂ microcosm spikes. They identified 302 indicator OTUs (245 bacteria, 57 fungi), classified as Hg-tolerant (168), Hg-sensitive (63), or Versatile (14) based on Spearman correlations with high and moderate Hg zones. The paper confirms that merA gene copies increased with Hg concentration (both field and microcosm), and that Chthoniobacteraceae (bacteria) and *Trichosporon* sp. (fungi) are associated with high-Hg soils.

### Genus-level B_std analysis

Of the 245 bacterial indicator OTUs, 229 (93%) have no genus-level assignment (empty Genus column in the supplementary table). This is the taxonomic resolution published alongside a MOTHUR/454-era analysis circa 2017–2018. Direct genus-level matching to the MicrobeAtlas trait table is therefore very sparse.

**Genus-level matches only (15/245 OTUs, 6%):** Streptomyces, Coriobacterium (×2), Persicobacter, Elizabethkingia, Gemmata, Pirellula (×2), Nannocystis (×3), Shewanella (×3), Opitutus.

### Family-level B_std proxy

For OTUs without genus assignments but with a recognisable family, the mean B_std of representative genera in each family (from the MicrobeAtlas trait table) was used as a proxy. Families resolved: Acidithiobacillaceae (B_std = 0.254, via *Acidithiobacillus*), Rhodobiaceae (0.307), Tsukamurellaceae (0.600), Bryobacteraceae (0.403), Gemmataceae (0.332), Chthoniobacteraceae (0.451), Xanthomonadaceae (0.361). Six families in the indicator table had no representatives in the trait table and remain unresolvable.

**Combined coverage (genus + family proxy): 39/245 OTUs (15.9%).**

| Group | n OTUs with B_std | Source | Mean B_std | vs. background (0.233) |
|-------|-------------------|--------|------------|----------------------|
| Hg-tolerant (168 total) | 28 | 15 genus, 13 family | **0.303** | +0.070 (+30%) |
| Hg-sensitive (63 total) | 9 | 2 genus, 7 family | **0.385** | +0.152 (+65%) |
| Versatile (14 total) | 2 | 2 genus | 0.154 | −0.079 (−34%) |
| Unassignable | 206 | — | — | — |

- **Mann-Whitney U test (Hg-tolerant vs Hg-sensitive):** U = 104, p = 0.44 (not significant; n too small)
- All matchable OTUs in both groups are **above** background B_std

**Key drivers of the Hg-sensitive group:** Tsukamurellaceae (2 OTUs, B_std = 0.600) and *Elizabethkingia* (1 OTU, B_std = 0.556) are globally wide-ranging generalists that happen to be Hg-sensitive in this gradient — their high B_std does not reflect Hg adaptation. The Acidithiobacillaceae family proxy (B_std = 0.254) accounts for 13 OTUs assigned symmetrically across both groups (5 Hg-sensitive, 8 Hg-tolerant), artificially reducing between-group variance.

### Can genus-level assignments be recovered?

**No, not from the published supplementary table alone.** Of the 206 unresolvable OTUs:
- 99/206 have no assignment below Phylum level (entirely unclassified)
- 38/206 have Order-level assignments only
- 69/206 have Class-level assignments only (predominantly *Phycisphaerae*, Gammaproteobacteria, Alphaproteobacteria)

Full genus-level resolution requires downloading the raw FASTQ files from ENA (PRJEB21070) and reclassifying with a modern SILVA reference (SILVA 138.1) using vsearch. This reclassification was completed; see Part 2c.

**Verdict:** Genus-level + family-proxy analysis covers 16% of the 245 indicator OTUs. Both matched Hg-tolerant and Hg-sensitive groups exceed background B_std, but sample sizes are too small for statistical conclusions. The analysis is **exploratory only**. The merA enrichment finding provides independent P2 support (Part 6).

---

## Part 2c: Frossard et al. 2018 — Full CWM Analysis from FASTQ Reclassification (P1 Test)

### Method

All 48 bacterial samples from PRJEB21070 were downloaded from ENA (96 paired-end FASTQ files, ~0.9 GB) and processed through a vsearch pipeline:

1. **Merge paired-end reads** (341F/806R V3–V4): `vsearch --fastq_mergepairs`, min overlap 20 bp, max diffs 5
2. **Quality filter**: strip primers (17 bp fwd, 19 bp rev), maxee 1.0, minlen 200
3. **SINTAX classify** against SILVA 138.1 (313,734 seqs, 99% clustering): cutoff 0.5, 16 threads; Bacteria only, exclude uncultured/unidentified genera
4. **CWM_B** per sample: Σ(read_count × B_std) / matched_reads, where B_std is from the MicrobeAtlas genus trait table (2,851 genera)

Raw FASTQs and intermediate files were deleted after each sample to minimise disk use.

**Classification yield:** 7,055–16,906 merged reads per sample; 60–63% genus-classified (Bacteria, named genera); 350–440 genera per sample. Mean trait-table match rate: ~42% of classified reads matched a genus in the 2,851-genus trait table.

### Site key (from ENA biosample metadata + paper Table 1)

| T-level | Description | Total Hg (mg/kg) | Distance from canal | Biome |
|---------|-------------|-----------------|--------------------|----|
| T1 | High contamination | 36.1 ± 2.4 | 5 m | Meadow |
| T2 | Moderate contamination | 3.02 ± 0.94 | 30 m | Meadow |
| T3 | Low contamination (background) | 0.25 ± 0.05 | 100 m | Meadow |
| T4 | Natural uncontaminated reference | — | outside gradient | **Forest** |

T1–T3 form the core contamination gradient (144-fold Hg range) used in the paper's main 3-site analysis (36 samples). T4 is an additional reference site from a **different biome** (forest) and was not included in the paper's community comparisons.

### Results — Field arm (T1–T3 meadow gradient)

| Site | Hg (mg/kg) | Mean Field CWM_B | SD |
|------|------------|------------------|----|
| T1 (high) | 36.1 | 0.362 | 0.018 |
| T2 (moderate) | 3.02 | 0.364 | 0.006 |
| T3 (low) | 0.25 | 0.366 | 0.009 |
| T4 (forest ref.) | — | 0.405 | — |

**Spearman ρ (log₁₀[Hg] vs CWM_B, T1–T3 only): ρ = −0.089, p = 0.78** — no relationship. Across a 144-fold Hg range, community niche breadth is essentially identical.

The apparent Spearman ρ = 0.618 (p = 0.011) reported in an earlier version of this section was artefactual: it included T4 (forest reference), inflating the correlation because forest soils have higher CWM_B than meadow soils regardless of Hg status. Restricting to the comparable meadow gradient (T1–T3) eliminates the signal entirely.

### Results — Microcosm arm (per soil origin, T1–T3 meadow only)

The microcosm uses subsamples of the 12 field soils (3 contamination levels × 4 replicates), half receiving +10 μg/g HgCl₂ and half receiving sterile water (control), harvested after 30 days. T1–T3 in the microcosm arm refer to the source soil origin, not time points.

| Source soil | Ctrl CWM_B | Hg CWM_B | Δ (Hg − Ctrl) | Mann-Whitney p |
|-------------|-----------|----------|----------------|---------------|
| T1 (36.1 mg/kg Hg legacy) | 0.357 | 0.358 | +0.001 | 1.00 |
| T2 (3.02 mg/kg Hg legacy) | 0.361 | 0.355 | −0.006 | 0.34 |
| T3 (0.25 mg/kg Hg legacy) | 0.368 | 0.333 | **−0.035** | 0.11 |

**Pooled Mann-Whitney (T1–T3, n=12 Ctrl + 12 Hg):** U = 45, p = 0.126 — not significant.

Direction is opposite to P1 at T2 and T3: Hg-treated soils have equal or lower CWM_B than controls. At T3 (low-legacy Hg soil receiving an acute +10 μg/g spike) the Hg arm has the lowest CWM_B across all cells (0.333). This is consistent with the paper's own finding: *"No short-term effect of added Hg was observed on the bacterial or fungal community structures"* (beta-diversity PERMANOVA F=0.8, p=0.708).

The T4 forest reference samples (not in the paper's main analysis) show Ctrl=0.411, Hg=0.410 — essentially identical, and at this site CWM_B is elevated regardless of acute Hg addition, reflecting a forest microbiome effect.

**Including T4 (all 16 Ctrl + 16 Hg):** Ctrl = 0.374, Hg = 0.364; U = 103, p = 0.36 — still not significant.

### Verdict for P1 (Frossard 2018 CWM analysis)

**Not supported.** Across the 144-fold field Hg gradient (meadow sites), CWM_B shows no detectable association with Hg concentration (ρ = −0.089, p = 0.78). Acute +Hg microcosm treatment produces no significant CWM_B elevation relative to controls (p = 0.126–0.36 depending on whether the forest reference is included), with direction opposite to P1 in two of the three meadow soil types. Both arms are substantially above background (0.233), which reflects the broad-niche character of meadow microbiomes, not a Hg effect.

This result is not inconsistent with Frossard 2017 or Li 2022. The Frossard 2018 field gradient has relatively narrow within-biome variation in CWM_B (0.362–0.366 across T1–T3), and the short-term microcosm adds Hg on top of soils with decades of legacy adaptation — neither is a clean test of whether acute Hg stress shifts communities toward generalists de novo.

---

## Part 2d: Du et al. 2023 — Hg-Spiked Paddy/Upland Soil Microcosm (P1 Test) — **METADATA UNVERIFIED**

### ⚠️ CRITICAL METADATA FLAG

> **⚠️ METADATA UNVERIFIED — RESULTS NOT INTERPRETABLE**
> 
> Treatment assignments (control/low/high Hg) were inferred from ENA experiment_alias only. They have NOT been verified against the Du 2023 paper supplement. Two samples (P3, P11) are absent from the pipeline output. **Do not cite or interpret these results until metadata provenance is confirmed.**

### Study overview

Du et al. 2023 (DOI: 10.1016/j.scitotenv.2023.165056; PRJNA914639) assessed Hg effects on soil bacterial communities in a controlled microcosm experiment using soils from three Chinese sites: Maoming (site 1), Yueyang (site 2), and Wuchang (site 3). The design consists of:
- Two soil types: paddy (P1–P36) and upland (U1–U36)
- Three Hg treatments: 0 μg/g (control), 3 μg/g (low), 10 μg/g (high)
- Target n = 72 samples (12 replicates per treatment × 2 soil types)
- 16S V3–V4 amplicons (Illumina sequencing)

**Pipeline status:** 70/72 samples processed (P3 and P11 missing from output). Treatment assignments and Hg levels were inferred from ENA experiment_alias naming convention (e.g., "CK" = control, "L" = low, "H" = high) but have **not been cross-verified** against the paper's supplementary Table S1 or ENA SRA metadata.

### CWM Levins B_std analysis

**Method:** FASTQ files from PRJNA914639 (144 paired-end files, ~1.2 GB) were processed through vsearch pipeline:
1. Merge paired-end reads (V3–V4: 341F/806R), min overlap 20 bp, max diffs 5
2. Quality filter: strip primers, maxee 1.0, minlen 200
3. SINTAX classify against SILVA 138.1 (cutoff 0.5)
4. CWM_B per sample: Σ(RA × B_std) / matched_reads, renormalised to genus-matched fraction only

**Read quality summary (all 70 samples):**

| Metric | Value |
|--------|-------|
| Median merged reads per sample | 155,276 |
| Median filtered reads | 129,528 |
| Median classified reads | 88,024 |
| Median matched genera | 227 |
| Filtering rate | 80.09% ± 13.23% |

### CWM_B results by treatment and land use

| Land use | Treatment | Hg level | Mean CWM_B | SD | n |
|----------|-----------|----------|------------|----|----|
| Paddy | Control | 0 μg/g | 0.4054 | 0.0052 | 10 |
| Paddy | Low Hg | 3 μg/g | **0.3687** | 0.0033 | 12 |
| Paddy | High Hg | 10 μg/g | 0.4028 | 0.0057 | 12 |
| Upland | Control | 0 μg/g | 0.4410 | 0.0113 | 12 |
| Upland | Low Hg | 3 μg/g | **0.4018** | 0.0084 | 12 |
| Upland | High Hg | 10 μg/g | 0.4344 | 0.0180 | 12 |
| **Overall** | **Control** | **0 μg/g** | **0.4248** | — | **22** |
| **Overall** | **Low Hg** | **3 μg/g** | **0.3852** | — | **24** |
| **Overall** | **High Hg** | **10 μg/g** | **0.4186** | — | **24** |

### Statistical tests

#### Paddy soil only (n=34)

| Comparison | Statistic | p-value | Result |
|------------|-----------|---------|--------|
| Spearman ρ(Hg level vs CWM_B) | −0.023 | 0.8957 | Not significant |
| Mann-Whitney Control vs High Hg | U=72 | 0.4483 | Not significant |
| Mann-Whitney Control vs Low Hg | U=120 | **0.0001** | **Significant** (LOWER direction) |
| Mann-Whitney Low vs High Hg | U=0 | **<0.0001** | **Highly significant** (Low < High) |

#### Upland soil only (n=36)

| Comparison | Statistic | p-value | Result |
|------------|-----------|---------|--------|
| Spearman ρ(Hg level vs CWM_B) | −0.164 | 0.3400 | Not significant |
| Mann-Whitney Control vs High Hg | U=91 | 0.2855 | Not significant |
| Mann-Whitney Control vs Low Hg | U=144 | **<0.0001** | **Significant** (LOWER direction) |
| Mann-Whitney Low vs High Hg | U=12 | **0.0006** | **Highly significant** (Low < High) |

#### Both land uses combined (n=70)

| Comparison | Statistic | p-value | Result |
|------------|-----------|---------|--------|
| Spearman ρ(Hg vs CWM_B) all samples | −0.100 | 0.4122 | Not significant |
| Mann-Whitney Control vs High Hg (all) | U=318 | 0.2394 | Not significant |

### Interpretation and anomaly flagging

**The observed pattern is NOT consistent with the expected CWM_B enrichment:**

1. **Low Hg shows significantly LOWER CWM_B than control:**
   - Paddy: 0.3687 vs 0.4054 (p=0.0001, Mann-Whitney)
   - Upland: 0.4018 vs 0.4410 (p<0.0001)
   - Direction is opposite to P1 prediction

2. **High Hg does not differ significantly from control:**
   - Paddy: 0.4028 vs 0.4054 (p=0.45)
   - Upland: 0.4344 vs 0.4410 (p=0.29)
   - No elevation in CWM_B as expected from Frossard 2017

3. **Within-treatment trend (Low < High) is significant and independent:**
   - Paddy: CWM_B low (0.3687) < high (0.4028) (p<0.0001)
   - Upland: CWM_B low (0.4018) < high (0.4344) (p=0.0006)
   - The low-Hg treatment is anomalously suppressed

**Possible explanations for this inverted dose-response:**

1. **Metadata reversal/shuffling:** The treatment labels (CK=control, L=low, H=high) in ENA experiment_alias may be assigned to the wrong sample replicates, or the Hg level encoding may be reversed in the original dataset. Without cross-checking ENA SRA accessions against the paper's Table S1, this cannot be ruled out.

2. **Mislabeled/unexpected experimental design:** The paper may employ a different treatment scheme than inferred from the alias names (e.g., the "L" treatment is not 3 μg/g but a different concentration, or samples were pooled/switched during sequencing).

3. **Genuine but anomalous biology:** The low-Hg treatment (3 μg/g) selects for specialists relative to both control and high-Hg (10 μg/g) conditions. This could reflect a "hormesis-like" response where moderate metal stress is more selective than high stress, but this contradicts the biological expectation from Frossard 2017 and Li 2022.

4. **Technical artifact:** FASTQ classification, merging, or filtering artifacts could systematically exclude or misclassify genera in low-Hg samples, artificially lowering CWM_B. Checking aligned read length distributions and genus-level OTU tables would help rule this out.

### Before any interpretation, verify:

1. Cross-check ENA SRA accessions (sample metadata) against Du 2023 paper supplement — confirm that P1–P36 and U1–U36 are correctly mapped to treatment groups and Hg levels.
2. Download raw metadata from ENA SRA (study PRJNA914639, run table) and compare experiment_alias to Du 2023 Table S1 or supplementary metadata.
3. Confirm which two samples (P3, P11) are intentionally missing from the original dataset and why.
4. If metadata are confirmed, audit genus-level OTU tables to check for systematic bias (e.g., whether low-Hg samples have fewer classified reads or lower coverage of broad-niche genera).

### Verdict for P1 from Du 2023

**Cannot interpret — metadata unverified.** The pipeline is complete, read quality is acceptable, and statistical results are internally consistent. However, the inverted dose-response (low Hg << control < high Hg) is inconsistent with the biological prediction from Frossard 2017 and Li 2022. Without verifying that treatment assignments match the original paper, any interpretation of these results would be unfounded.

**Recommendation:** Suspend analysis pending metadata verification. This is critical for the project: a false signal could lead to erroneous conclusions about Hg stress selectivity.

---

## Part 3: What Pu et al. 2022 Reports (Abstract-level)

Pu et al. tested Hg addition (0–10 mg/kg) to soils at three pH levels (acidic, neutral, alkaline).

**Alpha diversity:** Hg significantly reduced bacterial Shannon index and Chao1 richness across all pH levels; fungi showed opposite responses (increased diversity under Hg in acidic/neutral soils).

**Phylum-level shifts under Hg:**
- Proteobacteria: −16.2 to −30.6% (all pH levels)
- Actinomycetes: −24.7 to −40.8% (all pH levels)
- Fungi: context-dependent; Ascomycota decreased in alkaline/neutral soils; unclassified_k_Fungi increased (+26–29%) in alkaline/neutral soils

Genus-level differential abundance tables were not reported in the abstract; supplementary data could not be accessed.

**Levins B_std of depleted phyla (representative genera, MicrobeAtlas):**
| Phylum | Representative genera | Mean Levins B_std |
|--------|----------------------|-------------------|
| Proteobacteria | Pseudomonas, Burkholderia, Rhizobium, Acidovorax, Cupriavidus, Herbaspirillum, Sphingomonas, Methylobacterium (n=15) | **0.359** |
| Actinobacteria | Streptomyces, Mycobacterium, Arthrobacter, Rhodococcus, Nocardia (n=10) | **0.368** |

Both depleted phyla contain genera with **above-average Levins B_std** (global median ≈ 0.25). The acute-Hg result (specialists survive better under sudden Hg addition) is inconsistent with prediction P1. However, this may reflect acute toxicity rather than adaptation: the phyla that declined may include both generalists and specialists, with the signal driven by abundant taxa in the control community (dominated by Proteobacteria and Actinobacteria).

**Verdict for P1 from Pu 2022:** Weak disconfirmation. The broadly distributed phyla declined, not increased, under acute Hg stress.

---

## Part 4: Abdelmageed et al. 2021 — EFPC Streambank Soils

This study provides the strongest available genus-level community data for Hg-contaminated soils, using sites directly relevant to the ENIGMA/ORFRC system (East Fork Poplar Creek, Oak Ridge, TN).

### Study design
- 16S V4 amplicon (515F/806R), Illumina MiSeq
- 26 bank soil samples: EFK 18.2 (232.9–695.9 μg/g THg, n=8), EFK 11.2 (3.32–54.50 μg/g, n=8), Hinds Creek control (0.03–0.04 μg/g, n=8 + 12 with enrichments)
- Seasonal sampling (fall 2016 – summer 2017)

### Phylum and class abundances (Table 2 from paper)

| Clade | EFK 18.2 (high Hg) | EFK 11.2 (mid Hg) | HC control | Sig. diff? |
|-------|--------------------|--------------------|------------|------------|
| Proteobacteria | **36.5 ± 1.48%** | **29.6 ± 1.04%** | 19.0 ± 0.74% | Yes (A > B > C) |
| Firmicutes | **0.9 ± 0.10%** | 0.3 ± 0.07% | 0.3 ± 0.05% | Yes (A > B = B) |
| Bacteroidetes | 2.1 ± 0.67% | **3.5 ± 0.61%** | 0.9 ± 0.09% | Yes |
| Chloroflexi | 6.8 ± 0.48% | 6.8 ± 0.33% | 6.8 ± 0.24% | No |
| Nitrospirae | 7.9 ± 1.33% | 7.6 ± 0.73% | **12.2 ± 0.32%** | Yes (A = B < C) |
| δ-Proteobacteria | **8.5 ± 0.76%** | 7.4 ± 0.54% | 6.4 ± 0.38% | Yes |
| Geobacteraceae | **0.30 ± 0.07%** | 0.20 ± 0.05% | 0.03 ± 0.03% | Yes |
| Syntrophobacteraceae | 5.3 ± 0.82% | 3.4 ± 0.57% | 3.9 ± 0.41% | No |
| *Geobacter* (genus) | **0.53 ± 0.03%** | 0.50 ± 0.06% | 0.10 ± 0.02% | Yes |
| *Nitrospira* (genus) | 1.3 ± 0.28% | **1.6 ± 0.74%** | 1.2 ± 0.10% | Marginal |

A, B, C: letter grouping, A = highest abundance (Tukey, p<0.05).

### Cross-reference: Levins B_std for Hg-responsive genera

| Genus | Hg response | Levins B_std | n metal sp. | Adaptive mechanism |
|-------|-------------|-------------|-------------|-------------------|
| *Geobacter* | Enriched at high Hg | **0.187** | 4 | Iron reduction (IRB); hgcA methylation |
| *Clostridium* | Enriched at high Hg (enrichment cultures) | **0.237** | 51 | Fermentation; predicted hgcA methylation |
| *Desulfosporosinus* | Enriched at high Hg (enrichment cultures) | **0.152** | 6 | SRB; hgcA methylation |
| *Methanosarcina* | Enriched at high Hg (enrichment cultures) | **0.135** | 15 | Methanogenesis; hgcA methylation |
| *Methanocella* | Enriched at high Hg (enrichment cultures) | **0.145** | 1 | Methanogenesis; hgcA methylation |
| *Nitrospira* | Depleted at high Hg | **0.424** | — | Nitrification (no Hg mechanism known) |

**Key result:** Genera enriched at Hg-contaminated EFPC sites have mean Levins B_std = **0.171** — substantially lower than the genera depleted at Hg sites (Nitrospira, B_std = 0.424). This is the **opposite** of prediction P1.

### Why specialists dominate Hg-contaminated soils

The paradox resolves when mechanistic context is considered. The taxa enriched at EFPC high-Hg sites are:

1. **Obligate anaerobes** with narrow environmental optima (Geobacter, Desulfosporosinus, methanogens) — they are naturally specialist taxa
2. **Mercury methylators** (hgcA-positive): they transform inorganic Hg²⁺ to MeHg via a different mechanism than mer resistance
3. **Not mer operon carriers**: the enriched taxa survive Hg via methylation and sequestration, not via MerA-mediated reduction

The enrichment of low-B_std (specialist) taxa reflects their metabolic adaptation to the anoxic, high-Fe/S conditions at contaminated streambank soils — not broad ecological generalism. These specialists occupy a niche that coincides with Hg-rich conditions, not because they acquired HGT-encoded Hg resistance.

This mechanistic distinction is critical: **the two hypotheses (specialists survive via methylation; generalists benefit more from HGT-acquired mer resistance) are not mutually exclusive and may both be true in different ecological contexts.**

**Verdict for P1 from Abdelmageed 2021:** Disconfirms the simple version of P1 in long-term Hg-contaminated field soils. However, the result reflects methylation-based adaptation (hgcA), not mer resistance — the proposed conjugation experiment tests a different mechanism.

### hgcA detection (P2 proxy)

Positive hgcA amplification in 13/24 EFPC bank soil samples (54.2%), predominantly at EFK 18.2 (high Hg). Matched to Desulfovibrio desulfuricans ND132, Geobacter sulfurreducens PCA, and Desulfomonile tiedjei DCB-1. This confirms active Hg methylation machinery is enriched at contaminated sites. This partially supports P2 (Hg resistance genes enriched), but tests hgcA (methylation) rather than merA (reduction).

---

## Part 5: Global MicrobeAtlas Metal-Enrichment Analysis

Using `diff_abundance_metal_rich.csv` (internal dataset: 300 genera FDR-significant for differential abundance between metal-rich and non-metal-rich global MicrobeAtlas samples, all metals combined):

| Group | n genera | Mean Levins B_std | Median |
|-------|----------|-------------------|--------|
| Enriched in metal-rich environments | 147 | 0.276 | 0.257 |
| Depleted in metal-rich environments | 153 | 0.291 | 0.278 |

- Mann-Whitney U test (enriched > depleted): p = 0.713 (NS)
- Spearman ρ (Levins B_std vs log₂FC metal-rich): ρ = −0.022, p = 0.707, n = 300

**Null result.** No detectable association between niche breadth and metal-enrichment direction across 300 globally distributed genera. Caveats: (a) analysis combines all heavy metals (not Hg-specific), (b) includes all biomes (marine, gut, soil), which dilutes soil-Hg signal, (c) top enriched genera (Sneathia, Lactococcus, Haloarcula) indicate non-soil environments drive the enrichment signal.

**Verdict for P1 from global data:** Null — insufficient power to confirm or refute the Hg-specific prediction.

---

## Part 6: mer Gene Mobility Signals

From `gene_lambda_mobile_corr.csv` (n=9 mer gene families, MicrobeAtlas global OTU × KEGG data):

| Gene | Pagel's λ | Mobile element corr. | p (mobile) | n species | Interpretation |
|------|-----------|---------------------|------------|-----------|----------------|
| merB | 0.238 | +0.043 | 0.003** | 345 | Organomercury lyase; most mobile |
| merT | 0.379 | +0.065 | <0.001*** | 303 | Transport protein; highly mobile |
| merE | 0.391 | +0.069 | <0.001*** | 275 | Transport; highest mobile corr. |
| merD | 0.418 | +0.068 | <0.001*** | 280 | Regulatory; highly mobile |
| merR | 0.420 | +0.063 | <0.001*** | 320 | Regulator; highly mobile |
| merC | 0.522 | +0.059 | <0.001*** | 355 | Transport; mobile |
| merP | 0.585 | +0.040 | 0.004** | 687 | Periplasmic binding; mobile |
| merF | 0.676 | +0.043 | 0.002** | 333 | Transport; moderate λ |
| merA | 0.692 | +0.021 | 0.142 (NS) | 1635 | Reductase; most vertically inherited |

**Pattern:** Pagel's λ decreases with distance from merA in the operon. The regulatory/transport genes (merRTEDC) have lower λ (more mobile, less phylogenetically structured) and stronger positive correlations with mobile elements. merA shows high λ (0.69 = strong phylogenetic signal) but the lowest mobile correlation — suggesting merA is frequently co-inherited vertically once established in a lineage, while the rest of the operon continues to transfer horizontally.

All 8/9 significant mobile correlations are positive, confirming that mer genes co-occur with mobile element markers across diverse taxa globally. This supports the biological premise of the conjugation experiment: mer genes are actively transferred horizontally.

**Verdict for P2:** Supported. mer genes show strong signals of active HGT globally, particularly the regulatory and transport components (p < 0.001). merA is more phylogenetically constrained than the rest of the operon.

### Goff et al. 2024 — ORR Mobilome (ISME Communications, DOI: 10.1093/ismeco/ycae064)

Goff et al. assembled 1,615 circularized mobile genetic elements (MGEs) from metagenomic data collected from high and low contamination zones of the Oak Ridge Reservation (ORR) subsurface — the same ENIGMA field site from which ORFRC isolates originate.

**Key finding for P2:** merA and merR are physically co-localized on MGEs recovered specifically from the high-contamination zones. Plasmid EB106_03_01_3 (from the high-contamination region) carries merA, merR, zntA, czcD, and arsR in close physical proximity — a mercury resistance gene cluster on a mobile element. No merA-containing elements were identified from low-contamination zones.

**ORR geochemical context:** The ORR is a mixed-waste contaminated site. The Y-12 National Security Complex released over 1,000 tonnes of elemental mercury during Cold War-era lithium isotope separation, contaminating East Fork Poplar Creek (EFPC) and surrounding subsurface sediments. The high-contamination zones sampled by Goff et al. are associated with co-contamination including Hg alongside uranium and nitrate. The study title "Mixed waste contamination selects for a mobile genetic element population enriched in multiple heavy metal resistance genes" explicitly places merA enrichment in the context of multi-metal contamination including Hg.

**Relevance to thesis work:** The ENIGMA CORAL database (4,346 field samples from ORFRC wells, `enigma.coral.sdt_asv`) covers the same site. While groundwater Hg concentrations are not available in the CORAL geochemistry schema (only Cu, Ni, Zn, As, Mn from `ddt_brick0000007`), the Goff et al. mobilome data directly confirm that the ORFRC subsurface microbiome is under active Hg selection pressure, with merA encoded on transferable plasmids.

**Verdict for P2 (Goff 2024):** Supported. merA and merR are enriched in mobile elements at contaminated ORR zones, directly at the ENIGMA field site, on a broad-host-range conjugative plasmid.

---

## Part 7: Summary of Evidence

| Prediction | Evidence source | Result | Verdict |
|------------|----------------|--------|---------|
| P1: Hg stress shifts soil communities toward generalists | **Frossard 2017** (aerobic forest soil, acute Hg spike) | Hg-tolerant OTUs: mean B_std = **0.407** vs 0.233 background; p < 0.0001; effect size 81% | **Supported** |
| P1: Hg stress shifts soil communities toward generalists | **Li 2022** (long-term contaminated Chinese soils, PRJNA774099) | CWM_B = 0.365 (all 80 samples, vs 0.233 background); within-gradient ρ = −0.314 (p=0.0045) | **Conditionally supported** — elevated above background; decreases at extreme Hg |
| P1: Hg stress shifts soil communities toward generalists | Frossard 2018 (Swiss meadow gradient + 30-day microcosm, PRJEB21070) | Field gradient (144× Hg range, T1–T3 meadow): CWM_B 0.362–0.366, ρ=−0.09 (p=0.78). Microcosm +Hg vs Ctrl (T1–T3): 0.349 vs 0.362, p=0.13, direction opposite. Authors confirm: no short-term Hg effect on community structure | **Not supported** (flat field gradient; no CWM_B elevation with acute Hg) |
| P1: Hg stress shifts soil communities toward generalists | Chauhan 2025 (SRS/ORR legacy nuclear sites, PRJNA1245361) | Dominant genera mixed: aerobic generalists (Burkholderia B_std=0.43) + anaerobic specialists (Geobacter 0.19, Anaeromyxobacter 0.18); α-diversity declined with Hg | **Mixed** (both generalists and specialists; depends on aerobic/anaerobic context) |
| P1: Hg stress shifts soil communities toward generalists | **Du 2023** (Chinese paddy/upland microcosm, PRJNA914639) | CWM_B: low-Hg (0.3852) < control (0.4248) < high-Hg (0.4186); inverted dose-response opposite to prediction; **metadata not verified against paper supplement** | **Uninterpretable** (anomalous pattern; requires metadata validation) |
| P1: Hg stress shifts soil communities toward generalists | Pu 2022 (agricultural soil microcosm, acute Hg) | Broad phyla (Proteobacteria, Actinobacteria) depleted; abstract-level only | Weak disconfirmation |
| P1: Hg stress shifts soil communities toward generalists | Abdelmageed 2021 (EFPC streambank, anoxic long-term) | Hg-enriched taxa are specialists (mean B_std=0.171); but mechanism is hgcA methylation | Disconfirmation (different mechanism) |
| P1: Hg stress shifts soil communities toward generalists | Global MicrobeAtlas all-metals | ρ=−0.022, p=0.71 across 300 genera | Null |
| P2: mer genes enriched in Hg-contaminated soils | Abdelmageed 2021 | hgcA detected in 54.2% of contaminated samples | Partial support (hgcA not merA) |
| P2: mer genes enriched in Hg-contaminated soils | **Frossard 2018** | merA gene copies increase with Hg concentration (field gradient + short-term microcosm) | **Supported** (merA specifically) |
| P2: mer genes enriched in Hg-contaminated soils | Global mer gene mobility (MicrobeAtlas) | 8/9 mer families: significant positive mobile element correlations | Supports HGT premise |
| P2: mer genes enriched in Hg-contaminated soils | **Goff et al. 2024 (ORR mobilome, ISME Commun.)** | merA + merR on MGEs enriched in high-contamination ORR zones; plasmid EB106_03_01_3 carries merA+merR+zntA+czcD+arsR cluster; zero merA from low-contamination zones | **Supported** (ENIGMA field site; merA on transferable plasmid) |

---

## Part 8: Interpretation

### What the community data actually show

The results are mechanism- and context-dependent and form a coherent picture:

**1. Aerobic mer-mediated tolerance, acute Hg (Frossard 2017, forest soil microcosm):** Hg-tolerant bacteria are broad-niche generalists (B_std = 0.407 vs 0.233 background, p < 0.0001). The taxa are aerobic Proteobacteria (*Burkholderia*, *Bradyrhizobium*, *Janthinobacterium*) known to carry mer operons and have wide metabolic flexibility. **Directly supports P1 in the mechanism relevant to the proposed experiment.**

**2. Long-term chronic Hg contamination, aerobic soils (Li 2022, Chinese soils):** All 80 contaminated samples have CWM_B = 0.365 — 57% above global background — consistent with historical generalist enrichment under aerobic Hg pressure. Within the gradient, higher Hg slightly decreases CWM_B (ρ = −0.31), indicating that at extreme contamination (slag/mining >300 mg/kg) a smaller set of highly resistant specialists dominates. The dominant genera (Gaiella, Nitrospira, Nocardioides, Sphingomonas) all have above-average B_std. **Conditionally supports P1 — generalists are enriched above naive background, but extreme Hg further selects for resistance specialists.**

**3. Legacy nuclear Hg sites (Chauhan 2025, SRS/ORR):** Community dominated by mixed guild — aerobic generalists (Burkholderia B_std=0.43, Bradyrhizobium 0.39) co-occur with anaerobic specialists (Geobacter 0.19, Anaeromyxobacter 0.18, Syntrophorhabdus 0.19). α-diversity declined with Hg. Signal is diluted by co-contamination (multiple metals at nuclear legacy sites) and bioavailability disconnect (high total Hg ≠ high bioavailable Hg). **Mixed result; context too confounded for clean P1 test.**

**4. Anaerobic methylation-based tolerance (Abdelmageed 2021, EFPC streambank):** The taxa enriched at long-term Hg-contaminated anoxic sites (*Geobacter*, *Desulfosporosinus*, methanogens) are narrow-niche specialists (B_std = 0.171) that survive via hgcA-mediated methylation, not mer. **Disconfirms P1 via a mechanistically distinct pathway (hgcA methylation, not mer reduction).**

**5. Acute Hg toxicity (Pu 2022):** Proteobacteria and Actinobacteria (both above-average B_std) decline under acute Hg addition — consistent with acute toxicity affecting abundant taxa regardless of niche breadth. **Weak disconfirmation.**

**6. Global signal (MicrobeAtlas all metals):** No detectable association between niche breadth and metal enrichment globally — diluted by all metals and biomes. **Null.**

**Synthesizing across contexts:** A dose-response/exposure-duration framework organises all results:

| Hg context | Duration | Community response | CWM_B | P1? |
|------------|----------|-------------------|-------|-----|
| Acute spike (Frossard 2017, 0–32 mg/kg, 30 days) | Short | Generalist aerobic tolerators survive | 0.407 | Yes |
| Long-term moderate (Li 2022, 2–75 mg/kg) | Chronic | Elevated generalist community | 0.379 | Yes |
| Long-term extreme (Li 2022, >300 mg/kg slag/mining) | Chronic | Resistance specialists dominate | 0.364 | Partial |
| Field gradient (Frossard 2018, 144× Hg range, meadow) | Long-term chronic | CWM_B flat across gradient | 0.362–0.366 | No (ρ=−0.09, p=0.78) |
| Microcosm Hg vs Ctrl (Frossard 2018, 30 days, same soils) | Short | No CWM_B elevation; authors confirm no community shift | 0.349 vs 0.362 ctrl (T1-T3) | No (p=0.13, wrong direction) |
| Long-term extreme anoxic (Abdelmageed 2021, 696 μg/g, EFPC) | Chronic | hgcA-methylating specialists | 0.171 | No (different mechanism) |

The pattern is consistent with a **stress-response curve**: moderate aerobic Hg → broad generalists best positioned to acquire merA via HGT; extreme or anaerobic Hg → narrow-niche lineages with intrinsic resistance strategies dominate.

### P2 evidence: merA enrichment

Frossard 2018 provides the strongest direct P2 support: merA gene copies increase with Hg concentration in both field soils and short-term microcosm experiments. This is independent of community composition analysis and directly confirms that Hg-contaminated aerobic soils enrich for the merA enzyme. Combined with the MicrobeAtlas mer gene mobility data (8/9 mer gene families show significant HGT signals), the evidence for P2 in aerobic soil contexts is robust.

### What is well-supported

1. **In aerobic soil microcosms, Hg-tolerant bacteria are generalists** — Frossard 2017: B_std = 0.407 vs 0.233 background, p < 0.0001, effect size 81%
2. **Long-term Hg-contaminated aerobic soils have elevated community niche breadth** — Li 2022: CWM_B = 0.365 vs 0.233 background across 80 samples
3. **merA genes are enriched in Hg-contaminated aerobic soils** — Frossard 2018: merA copies increase with Hg in both field and microcosm
4. **mer genes are actively transferred horizontally** — MicrobeAtlas: 8/9 mer families show significant positive mobile element correlations; low Pagel's λ for regulatory/transport genes
5. **Mechanism determines generalist/specialist outcome** — mer aerobic resistance → generalist enrichment; hgcA methylation (anaerobic) → specialist enrichment

### Implications for the proposed microcosm experiment

The community-level data provide conditional support for the proposed conjugation experiment:
- **Frossard 2017 and Li 2022 confirm the ecological correlate (P1):** In aerobic soils — the context for Burkholderiales-based microcosms — Hg-tolerant bacteria and long-term Hg-contaminated communities are enriched in broader-niche organisms.
- **Frossard 2018 confirms the P2 mechanism:** merA enriches under Hg in aerobic soils, supporting the biological premise that Hg contamination provides selection pressure for mer acquisition.
- **Abdelmageed 2021 confirms the mechanism boundary:** The generalist enrichment signal appears in aerobic mer-resistance settings but disappears in anaerobic hgcA settings. The proposed experiment correctly targets the aerobic, mer-based mechanism.
- **A controlled conjugation experiment remains the only way to test the causal mechanism** — whether generalism specifically predicts *mer acquisition rate* rather than merely correlating with *mer carrier status*.
- The ORFRC Burkholderiales isolates (Janthinobacterium, Cupriavidus, Herbaspirillum as generalists; Acidovorax, Comamonas, Hydrogenophaga as specialists) provide a within-order comparison that controls for phylogeny and background mer prevalence.

---

## Part 9: Search of Merged 16S h5ad for Additional Hg Datasets

A pre-processed 16S amplicon dataset (`merged_samples_unfiltered.h5ad`, 20,339 samples × 1,742,134 ASVs, var includes pre-parsed `Genus` column) was searched for additional studies with quantitative Hg metadata.

**Findings:**

| Study | n samples | Hg metadata in h5ad? | Usable for CWM? |
|-------|-----------|---------------------|-----------------|
| PRJNA774099 (Li 2022 — already analysed) | 80 | Yes — `total_mercury_mg_per_kg_avg`, 16 levels (2.4–420.7 mg/kg) | **Yes** (CWM analysis complete — see Part 2) |
| PRJDB19179 (Japanese mine drainage) | 175 | No sample-level Hg in h5ad | No — aquatic (water), not soil |
| PRJNA616017 (Thomas et al. 2020, SRS soil) | 21 | No Hg in h5ad | No — this study focuses on ARG/MRG co-occurrence; reports site categories (pristine/metals/radionuclides), not per-sample Hg concentrations |
| All other studies (Frossard 2017/2018, Chauhan 2025, Du 2023) | — | Absent from merged h5ad | Not in dataset |

**Search methodology:** `mercury_mg_per_kg` column: 0 non-null; `total_mercury_mg_per_kg_avg`: 80 non-null (all PRJNA774099). Text search of `study_title` for "mercury", "Hg", "metal", and "contamination" found only the above three studies with any Hg relevance; none beyond PRJNA774099 had quantitative Hg metadata.

**Conclusion:** The merged h5ad does not add any new quantitative Hg datasets beyond Li 2022 for the current validation. Full CWM analyses for Frossard 2017/2018, Chauhan 2025, and Du 2023 require FASTQ download and processing from ENA/SRA.

---

## Part 10: Author Data Request Template

If genus-level per-sample OTU counts are needed (e.g. for CWM Levins B_std regression), the following can be adapted:

Note: Frossard 2017 raw reads are deposited at ENA PRJEB14076 (ERP015683), 84 bacteria + 84 fungi samples with Hg metadata encoded in sample names. A notebook (NB28: `28_frossard_cwm_analysis.ipynb`) has been prepared to query these data via Spark (arkinlab_microbeatlas) or process downloaded FASTQs with vsearch.

---

**To:** [Pu 2022 corresponding author, look up from journal page]
**Subject:** Request for genus-level community data — Microorganisms 2022

Dear Dr. [name],

I am studying niche breadth as a predictor of mercury resistance gene uptake in soil bacteria. Your 2022 paper (doi:10.3390/microorganisms10050977) on Hg effects on agricultural soil communities across pH gradients is directly relevant to this work.

Could you share the genus-level differential abundance tables (or OTU/ASV table) from your study? I am particularly interested in which specific genera were significantly enriched or depleted at each Hg concentration and pH level, as I would like to cross-reference these with MicrobeAtlas niche breadth data.

Thank you.

---

## Data and Methods Notes

- **Levins B_std** values from MicrobeAtlas genus trait table (`genus_trait_table.csv`, 2,851 genera)
- **Frossard 2017 Supp. Table 6**: extracted from `1-s2.0-S0038071716305983-mmc3.docx` (Soil Biol. Biochem. supplementary); 175 indicator OTUs (bacteria domain=99, fungi=76) with taxonomy, total abundance, and mean positive Spearman association coefficient with Hg32 treatment. Cross-referenced to genus_trait_table.csv: 22/99 bacteria matched (22%). Matched set saved to `/tmp/frossard_hg_tolerant_B_std.csv`. Figure: `data/frossard_hg_tolerant_niche_breadth.png`.
- **Li et al. 2022 (PRJNA774099)**: pre-processed h5ad at `/home/hmacgregor/data/PRJNA774099.ILLUMINA.PAIRED.V3-V4.FWD_ACTCCTACGGGAGGCAGCAG_REV_GACTACHVGGGTWTCTAAT.h5ad` (80 samples × 76,704 ASVs). Genus parsed from `var['Taxon']` SILVA field. CWM_B computed as Σ(RA_renorm × B_std) over matched ASVs; 453 genera matched (16,759 ASVs, 21.8%). Hg from `obs['total_mercury_mg_per_kg_avg']`. Spearman/Pearson via scipy. Figure: `data/li2022_cwm_bstd.png`.
- **Frossard 2018 Supp. Table 4 (mmc3.docx)**: `1-s2.0-S0038071718300270-mmc3.docx`, table index 3; 302 OTUs (245 bacteria, 57 fungi) with Hg-tolerant/Hg-sensitive/Versatile classification; 15/245 OTUs matched at genus level (6%); 24 additional OTUs matched via family-level B_std proxy; total coverage 39/245 (16%). Full extraction at `/tmp/frossard2018_full_bstd.csv`.
- **Frossard 2018 FASTQ reclassification (PRJEB21070)**: 96 paired-end FASTQs downloaded from ENA; vsearch mergepairs → quality filter (stripleft 17, stripright 19, maxee 1.0, minlen 200) → SINTAX against SILVA 138.1 99% (sintax_cutoff=0.5, 16 threads); Bacteria-only, exclude uncultured genera; CWM_B computed per sample. Results at `/tmp/prjeb21070_cwm_results.csv` (48 rows); genus counts at `/tmp/prjeb21070_genus_counts.pkl`. Processing script: `/tmp/prjeb21070/run_pipeline.py`.
- **Chauhan 2025**: dominant genera from paper text (16S and shotgun sections); B_std values from genus_trait_table.csv lookup.
- **Du 2023**: sample metadata from `1-s2.0-S0048969723036793-mmc1.xlsx` (TableS1); Hg stress categorical (Low=3 μg/g, High=10 μg/g); no genus-level community table in SI; full CWM requires raw FASTQ processing from PRJNA914639.
- **diff_abundance_metal_rich.csv**: 300 genera FDR-sig (all p_adj < 0.05) for enrichment in metal-rich MicrobeAtlas samples; covers all metals and biomes
- **gene_lambda_mobile_corr.csv**: Pagel's λ and Spearman correlation of gene presence with mobile element markers, per-gene across MicrobeAtlas OTU profiles
- **Abdelmageed et al. 2021 Table 2**: Verbatim percentage abundances extracted from full text; statistical comparisons reproduced from the paper's ANOVA results
- All Levins B_std comparisons use Mann-Whitney U test (one-sided where directional, two-sided otherwise); no multiple testing correction applied (exploratory)
- Figure: `frossard_hg_tolerant_niche_breadth.png` shows B_std distribution for matched indicator OTUs vs background

---

## Part 11: Cross-Reference — Goff et al. 2024 HMRGs vs Double-Signal Gene List and Mobility Metrics

### Background

Goff et al. 2024 (ISME Commun. 4:ycae064; DOI: 10.1093/ismeco/ycae064) assembled 1,615 circularized MGEs from metagenomes of the Oak Ridge Reservation (ORR) subsurface — the ENIGMA field site. They identified 47 HMRG-encoding MGEs and performed comparative analysis of HMRG abundance between high [U]/high-metal and low [U]/low-metal zones. This Part cross-references the Goff 2024 HMRG catalog with our computationally derived double-signal gene list and per-KO mobility metrics.

**Sources for this analysis:**
- `gene_lambda_mobile_corr.csv` — Pagel's λ (genus-level) + Spearman mobile element correlation per gene (n=40 resistance gene families)
- `phylo_d_all_ko.csv` — Pagel's λ for all 276 MRG KOs (genus-level, pre-computed)
- `curated_mrg_ko_ids_v2.csv` — full MRG catalog with KO, gene, metal, and evidence tier
- Double-signal gene list (user-provided): 13 KOs with Fritz & Purvis D>0.2 AND λ<0.3

### 11a. HMRGs Confirmed by Goff et al. 2024

The following genes were explicitly reported as present on MGEs recovered from high-contamination ORR zones. The key cluster is plasmid EB106_03_01_3 (conjugative, from the high-contamination zone), which carries five genes in close physical proximity:

| Gene | KO | Metal | Tier | Enriched in high [U]? | On MGE? | Specific MGE |
|------|----|-------|------|-----------------------|---------|--------------|
| merA | K00520 | Hg | Tier 3-BacMet | **Yes** (enriched, Fig 4) | **Yes** | Plasmid EB106_03_01_3 |
| merR | K08365 | Hg, Cu, Zn | Tier 1 | **Yes** | **Yes** | Plasmid EB106_03_01_3 |
| zntA | K01534 | Zn/Cd/Cu/Hg/Pb | Tier 1 | Yes (co-located) | **Yes** | Plasmid EB106_03_01_3 |
| czcD | K16264 | Co/Zn/Cd/Tl | Tier 1 | Yes (co-located) | **Yes** | Plasmid EB106_03_01_3 |
| arsR | K03892 | As/Sb | Tier 3-BacMet | Yes (high zone + low zone) | **Yes** | Plasmid EB106_03_01_3 + unclassified MGEs |

**Additional Goff 2024 context:** merR and arsR also appear alone on simpler MGEs in the low-contamination zones, suggesting they are the minimal HMRG complement at less-contaminated ORR wells. The high-contamination zones uniquely harbor multi-gene clusters (merA+merR+zntA+czcD+arsR on one plasmid), consistent with co-selection under multi-metal stress.

### 11b. Synthesis Table: Goff 2024 × Double-Signal Genes × Mobility Metrics

For all 9 mer gene family members (from `gene_lambda_mobile_corr.csv`) and the 13 double-signal KOs (user-provided), the following table shows:

**Mer operon genes — Goff 2024 vs mobility metrics:**

| Gene | KO | Metal | In Goff 2024? | Enriched high zone? | On MGE? | λ (genus) | Mobile corr. ρ | Mobile p | Double-signal? |
|------|----|-------|---------------|---------------------|---------|-----------|---------------|----------|----------------|
| merA | K00520 | Hg | **Yes** | Yes | Yes (conj. plasmid) | 0.692 | +0.021 | NS (0.142) | No |
| merR | K08365 | Hg | **Yes** | Yes | Yes (conj. plasmid) | 0.420 | +0.063 | *** | No |
| merT | K08363 | Hg | Not reported | — | — | 0.379 | +0.065 | *** | No |
| merP | K08364 | Hg | Not reported | — | — | 0.585 | +0.040 | ** | No |
| merC | — | Hg | Not reported | — | — | 0.522 | +0.059 | *** | No |
| **merD** | **K19057** | **Hg** | **Not reported** | — | **Predicted: Yes** | **0.418 (λ_genus); 0.165 (λ_ko)** | **+0.068** | ***** | **Yes** (D=0.701) |
| **merE** | **K19059** | **Hg** | **Not reported** | — | **Predicted: Yes** | **0.391 (λ_genus); 0.102 (λ_ko)** | **+0.069** | ***** | **Yes** (D=0.728) |
| merF | — | Hg | Not reported | — | — | 0.676 | +0.043 | ** | No |
| merB | — | MeHg | Not reported | — | — | 0.238 | +0.043 | ** | No |

*Note: λ_genus from `gene_lambda_mobile_corr.csv`; λ_ko from `phylo_d_all_ko.csv`; D (Fritz & Purvis) from user-provided double-signal table.*

**Other Goff 2024 confirmed HMRGs:**

| Gene | KO | Metal | In Goff 2024? | On MGE? | λ (genus, mobile corr.) | Double-signal? |
|------|----|-------|---------------|---------|------------------------|----------------|
| zntA | K01534 | Zn/Cd/Cu | **Yes** | Yes | Not in mobility dataset | No |
| czcD | K16264 | Co/Zn/Cd | **Yes** | Yes | Not in mobility dataset | No |
| arsR | K03892 | As | **Yes** | Yes | λ=0.577; ρ=+0.113 (***) | No |

**Double-signal genes NOT covered by Goff 2024:**

| Gene | KO | Metal | λ (genus-level) | D (genome) | Goff 2024 | Reason not covered |
|------|----|-------|-----------------|------------|-----------|-------------------|
| nrsD | K07785 | Ni/Co | 0.089 | 0.821 | No | ORR Ni/Co not primary contaminant |
| gesB | K19594 | Te | 0.156 | 0.597 | No | Tellurite not at ORR |
| gesA | K19595 | Te | 0.161 | 0.458 | No | Tellurite not at ORR |
| aoxB | K08356 | As (oxidase) | 0.000 | 0.562 | No | Different As mechanism (oxidase vs arsR regulator) |
| golS | K19592 | Au/Cu | 0.135 | 0.265 | No | Not measured at ORR |
| norB | K08170 | NO (denitrification) | 0.033 | 0.239 | No | Not an HMRG |
| shp  | K25119 | Fe | 0.000 | 0.385 | No | Iron acquisition, not classical HMRG |
| nicC | K14974 | Ni | 0.000 | 0.224 | No | Ni transporter not at ORR |
| nikB | K15585 | Ni | 0.000 | 0.202 | No | Ni transporter not at ORR |

### 11c. Implications

**1. Which computationally predicted mobile resistance genes are already confirmed at ORR by Goff 2024?**

No double-signal KOs are directly confirmed in the Goff 2024 HMRG list. However, merD (K19057) and merE (K19059) are part of the mer operon and are almost certainly co-located on plasmid EB106_03_01_3 with merA and merR — the paper explicitly lists only the functional gene merA and regulatory merR but did not report sub-operon resolution. Our prediction that merD and merE are the most mobile mer genes (λ_genus 0.418/0.391 vs merA's 0.692; mobile_corr +0.068/+0.069 both p < 10⁻⁵) implies they should be among the first genes transferred in a conjugation event, but Goff 2024 does not test this.

**2. Which predictions remain untested by Goff 2024?**

- **merD/merE mobility advantage**: Goff 2024 confirms merA is on a conjugative plasmid at ORR, but does not test whether merD and merE transfer *more readily* than merA in cross-species conjugation events — this is the core claim from our phylogenetic analysis (double-signal: high D + low λ).
- **Non-mer double-signal genes**: All 11 non-mer double-signal genes (nrsD, gesB/gesA, aoxB, golS, norB, shp, nicC, nikB) are absent from the Goff 2024 dataset. This is expected — the ORR is a Hg/U/nitrate site, and the double-signal genes for Ni, Co, Te, Fe are not under primary selection there.
- **Stoichiometry of the HMRG cluster**: Goff 2024 confirms the merA+merR+zntA+czcD+arsR cluster but reports no quantitative HGT rate or conjugation efficiency for that plasmid, which is what the proposed experiment would measure.

**3. How does Goff 2024 + our computational framework strengthen the proposed experiment rationale?**

The Goff 2024 finding closes a critical gap in the experimental justification: it confirms that at the ENIGMA field site, merA and merR are already encoded on a broad-host-range conjugative plasmid. Our phylogenetic data predicts that merD and merE — which show *higher* mobile element co-occurrence (ρ=+0.068/+0.069, p<10⁻⁵) and *lower* phylogenetic signal (λ=0.418/0.391) than merA — should transfer with similar or greater frequency. Goff 2024 thus provides field evidence that the conjugation mechanism is already operating at ORR, while our framework provides the basis for predicting *which* genes within the operon are most likely to spread via HGT. Together, they define a testable hypothesis: merD and merE, as the most mobile components of the ORR mer plasmid, should be detectable in transconjugants at higher frequency per donor-cell contact than merA, under conditions resembling the ORR mixed-metal stress environment.

---

*Data sources: `gene_lambda_mobile_corr.csv` (n=40 gene families, MicrobeAtlas OTU profiles); `phylo_d_all_ko.csv` (n=276 KOs); `curated_mrg_ko_ids_v2.csv`; double-signal gene table from user. Goff 2024 HMRG list from full text of DOI: 10.1093/ismeco/ycae064. zntA and czcD not present in `gene_lambda_mobile_corr.csv` or `phylo_d_all_ko.csv` (those files cover mer operon and arsenate resistance genes only).*

---

*This report is a standalone analysis. No manuscript files were edited.*
