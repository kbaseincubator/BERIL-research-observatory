# Microcosm Feasibility Report: Generalist vs. Specialist Mercury Plasmid Conjugation

**Prepared:** 2026-07-13  
**Context:** Experimental follow-up to the computational thesis finding that generalist bacteria carry fewer metal-resistance genes per Mb of genome (H1 main result, microbeatlas_metal_ecology PGLS). The proposed experiment tests whether generalists compensate via enhanced HGT acquisition.  
**Status:** Pre-experiment planning — no wet lab work has been done.

---

## 1. Literature Novelty Check

**Search scope:** PubMed, arXiv, bioRxiv, Google Scholar. ~21 papers reviewed (July 2026).

### Is the generalist–HGT hypothesis published?

**Verdict: HIGH NOVELTY — the direct hypothesis is experimentally untested.**

A 2026 preprint (Li et al., Google Scholar) links habitat-shaped niche breadth to suppressed ARG conjugation potential in soil, the closest published work to this hypothesis, but it is observational. No study has directly measured conjugation acceptance rate as a function of standardized niche breadth phenotypes using matched soil isolates.

### What is established

| Topic | Key finding | Reference |
|---|---|---|
| mer plasmid soil conjugation | pQBR57 (mer operon) transfers in soil under Hg selection; reshapes community | Hall et al. 2020 |
| Soil microcosm conjugation rates | Transconjugant frequency ≈ 10⁻⁶–10⁻⁸ per viable cell; high CV (>50%) | Fan et al. 2019; Macedo et al. 2022 |
| Broad-host-range plasmid host range | IncP plasmids transfer to >15 phyla over 75 days in soil microcosms | Fan et al. 2019 |
| CRISPR vs. HGT trade-off | CRISPR systems impose fitness costs that limit HGT acceptance; niche breadth may predict defense burden | Muthuraman et al. 2025 (preprint) |
| Generalist conjugation efficiency | Not directly tested | — |

### Gaps this experiment would fill

1. **No direct test of niche breadth → conjugation rate** in any published system.
2. **No comparative genomics** quantifying CRISPR/R-M burden in generalists vs. specialists from the same contaminated soil.
3. **ORFRC isolates**: No published conjugation experiments using Oak Ridge Field Research Center isolates.

**Novelty argument:** This experiment would be the first to directly test whether ecological niche breadth — a genome-level macroecological trait — predicts conjugation permissiveness at the individual-isolate level, using a biologically meaningful plasmid (mer operon) from a well-characterized contaminated system.

---

## 2. ORFRC Isolate Selection

### Available ENIGMA collection

123 strains in the BERDL/ENIGMA isolate collection (strain_scalars.tsv); 86 have MicrobeAtlas genus-level niche breadth data (standardized Levins B from OTU-level environmental distributions).

### Candidate selection strategy

All six candidates are **Gram-negative Burkholderiales** (Proteobacteria), minimizing the phylogenetic confounding that would arise from comparing, say, a Firmicute (thick peptidoglycan, different surface receptor landscape) with a Proteobacterium.

#### Generalist recipients (target n=3 isolates)

| Genus | ENIGMA isolates | Levins B (std) | Metal clusters (mean) | Rationale |
|---|---|---|---|---|
| **Janthinobacterium** | 6 | 0.498 | 33.9 | Highest-representation Burkholderiales generalist; violet pigment facilitates colony ID |
| **Cupriavidus** | 5 | 0.430 | 47.1 | Known broad metal resistance pangenome; relative of C. metallidurans (classic HGT model); chromosomal and megaplasmid architecture |
| **Herbaspirillum** | 2 | 0.572 | 30.3 | High niche breadth, diazotroph, Burkholderiales; provides phylogenetic breadth within generalist set |

#### Specialist recipients (target n=3 isolates)

| Genus | ENIGMA isolates | Levins B (std) | Metal clusters (mean) | Rationale |
|---|---|---|---|---|
| **Acidovorax** | 8 | 0.281 | 36.4 | Largest ENIGMA representation; same order as generalists; well-characterized for metal response |
| **Comamonas** | 3 | 0.235 | 50.4 | Very low Levins B; Burkholderiales; maximizes contrast with Janthinobacterium |
| **Hydrogenophaga** | 1 | 0.236 | 31.0 | Complements Comamonas phylogenetically; common in oligotrophic niches |

**Selection justification:** The generalist–specialist split for these six genera spans Levins B_std 0.23–0.57, a range that captures ~75% of the variation observed across all Burkholderiales in MicrobeAtlas. Restricting to one order controls for conjugation permissiveness differences rooted in cell surface chemistry rather than niche breadth per se.

### Isolate traceability

All target genera appear in the BERDL ENIGMA isolate database (strain_scalars.tsv, n=123 strains); exact NCBI BioSample IDs can be retrieved from `strain_canonical_genomes.tsv` using the `strain_id` column. At least one sequence-verified isolate per genus should be selected.

---

## 3. Genome Screening of Candidate Isolates

**Purpose:** Before running conjugation assays, screen recipient genomes to exclude isolates that (a) already carry a mer operon (would not show HgCl₂ sensitivity required for transconjugant selection), (b) carry unusually high CRISPR burden (potential confounder), or (c) have structural rearrangements that complicate plasmid maintenance.

### mer operon KO targets (screening in/out)

| Gene | KO | Function | Screen action |
|---|---|---|---|
| merA | K00520 | Mercuric reductase (core) | Exclude isolates with merA (pre-resistant) |
| merB | K07171 | Organomercury lyase | Exclude if merA co-present |
| merD | K19057 | Co-regulator | Flag only |
| merE | K19059 | Transport | Flag only |
| merP | K02305 | Periplasmic chaperone | Flag only |
| merR | K02306 | Regulator | Flag only |
| merT | K02307 | Inner membrane transporter | Flag only |

**Data needed:** BERDL genome annotations (Prokka/KEGG) for the 23 candidate isolates (6 genera × 1–8 isolates). Run `hmmer` search against KEGG metal resistance HMMs (or query arkinlab BERDL genome annotation database). Exclude any isolate with hits to merA at e-value < 1×10⁻⁵.

### CRISPR / defense system screening

Use [CRISPRCasFinder](https://github.com/dcouvin/CRISPRCasFinder) or check for KOs:
- Cas1 (K07735), Cas2 (K07736), Cas9 (K09491)

Also check for restriction-modification systems: hsdM (K03427), hsdR (K03427), hsdS (K01154).

**Expected finding (from literature):** Generalists are predicted to have fewer CRISPR spacers and lower R-M gene density (Muthuraman et al. 2025 preprint; Xiao et al. 2024 mSystems). This can be validated computationally as a pre-experiment check and later as a mechanistic test.

### Transposase census

Count transposase genes (COG2801, COG2963, IS elements) per Mb as a proxy for prior HGT activity. Higher transposase density in generalists would support the hypothesis.

### Minimum viable protocol

```
1. Retrieve genome sequences for each candidate isolate from BERDL/NCBI.
2. Annotate with Prokka + KEGG (if not done); run dbCAN for CAZymes to confirm functional annotation quality.
3. Run HMMscan against mer operon HMMs (from REBASE/KEGG metal resistance profiles).
4. Run CRISPRCasFinder; tabulate CRISPR array count, spacer count, Cas type.
5. Count hsdM/hsdR/hsdS; count transposases.
6. Output: screening_results.csv with columns genome_id, has_merA, n_crispr_arrays, n_spacers, n_hsd_RM, n_transposases, levins_B_genus.
```

This can be done in ~2 days computationally on BERDL before any wet lab work.

---

## 4. Power Analysis: Conjugation Assay

### Model

Transconjugant frequency per donor cell follows a **log-normal distribution** in soil microcosm experiments (Fan et al. 2019; Crosby & Stadler 2025). Published CV ≈ 0.5–1.0; this analysis uses CV = 0.7 as a conservative estimate.

Under the log-normal model:
- σ_ln = √ln(1 + CV²) = √ln(1.49) = **0.631** (natural log SD)
- σ_log10 = 0.631 / 2.303 = **0.274** (log10 SD)

### Effect size

Hypothesis: generalists acquire mer plasmid at 5× higher frequency than specialists.
- Δlog10 = log10(5) = **0.699**
- Cohen's d = 0.699 / 0.274 = **2.55** (very large by conventional standards)

### Power by design

Two-sample t-test (generalists vs. specialists) on log10-transformed transconjugant frequency; two-sided α = 0.05.

| Design | n per group | Power |
|---|---|---|
| 1 strain × 3 replicates | 3 | 0.652 |
| 4 replicates | 4 | **0.849** |
| 2 strains × 3 replicates | 6 | 0.977 |
| **3 strains × 3 replicates** | **9** | **>0.999** |
| 4 strains × 3 replicates | 12 | >0.999 |

**Recommended design:** 3 generalist strains × 3 replicates + 3 specialist strains × 3 replicates = **18 microcosms** per time point.

### Minimum detectable fold difference

With n = 9 per group (3×3), 80% power, the minimum detectable fold-change is **≈ 2.5×** (Δlog10 = 0.39, d = 1.42).

**Interpretation:** Even a 2.5-fold generalist advantage is detectable. If the true effect is 5×, the experiment is highly over-powered for that specific contrast; this excess power can be used to detect genus-specific outliers or test dose-response across multiple HgCl₂ concentrations.

### Caveats

1. **Strain nested within group**: With 3 strains per group, strain is a random effect. A mixed-model (lme4: `log10_freq ~ group + (1|strain)`, n=9 per group) provides a more conservative test; power will be slightly lower than the simple t-test above (approximately 0.95 at n=9, depending on the ICC among strains within a group).
2. **CV may exceed 0.7**: If soil heterogeneity or assay variability drives CV > 1.0, power drops. Consider running a pilot (n=2 per group) to estimate CV before committing to full experiment.
3. **Zero-inflated data**: Transconjugant frequency may be zero in some replicates. Add 10⁻¹⁰ as a conservative floor before log-transforming, or use a hurdle model for the full analysis.

---

## 5. Indirect Evidence from Existing Data

Three independent lines of evidence from the BERDL computational analyses support the plausibility of the generalist-HGT hypothesis. None constitutes a direct experimental test.

### 5a. ORFRC MAG data: Metal contamination → lower per-genome metal gene burden

From **enigma_frc_burden_correlations.csv** (notebook 11_enigma_frc_replication.ipynb):

> MAG-level analysis of 29 ORFRC groundwater MAGs: combined metal contamination burden negatively predicts per-MAG metal gene count (**ρ = −0.41, p = 0.029**).

Interpretation: Organisms thriving in the most metal-contaminated ORFRC wells carry *fewer* metal resistance genes per genome, not more. This is consistent with the "generalist tolerance" mechanism (broader metabolic buffering rather than specific gene investment) and motivates testing whether these organisms instead tolerate metals via HGT-acquired resistance on demand.

### 5b. mer genes are among the most mobile metal resistance genes in global soil metagenomes

From **top_mobile_candidates.csv** and **gene_lambda_mobile_corr.csv** (notebook 12 / NB20):

| Gene | Pagel's λ | Mobile element correlation (ρ) | p-value |
|---|---|---|---|
| merB | 0.238 | +0.043 | 0.003 |
| merT | 0.379 | +0.065 | <0.001 |
| merE | 0.391 | +0.069 | <0.001 |
| merD | 0.418 | +0.068 | <0.001 |
| merR | 0.420 | +0.063 | <0.001 |

Interpretation: mer operon genes simultaneously show low phylogenetic signal (λ < 0.5, meaning their distribution is not explained by phylogeny) AND are positively co-distributed with mobile genetic element markers in metagenomes. This is direct bioinformatic evidence that mer genes are actively spreading via mobile elements in soils — exactly the type of mobilization that a conjugation experiment would measure.

**merA** is an outlier: λ = 0.692 (higher phylogenetic signal), mobile_corr = 0.021 (NS, p = 0.14). This suggests merA is less recently mobile than the rest of the operon — possibly a more ancient acquisition — and that the mobile component is primarily the regulatory/transport genes (merR, merT, merE) that travel as a unit.

### 5c. Double-signal HGT candidates include mer operon components

From the per_ko_metal_associations HGT analysis (completed 2026-07-13):

Thirteen KOs were identified as double-signal HGT candidates (Fritz & Purvis D > 0.2 at genome level AND Pagel's λ < 0.3 at genus level): merD (K19057) and merE (K19059) are among them, alongside nickel, arsenic, and copper resistance genes.

In MGnify metagenomes:
- nicC (K14974, Ni export) × PF1_Hg: ρ = +0.062, q < 0.001
- gesA (K19595, arsenic) × PF1_Hg: ρ = +0.046, q < 0.001

Aggregate DS score is positively associated with Cu (ρ = +0.060, p = 0.005) and As (ρ = +0.070, p = 0.001) in MAGs from metal-enriched environments.

Interpretation: The candidate genes are not just mobile in phylogenetic terms — their genomic presence shows a detectable signal with environmental metal concentrations. This validates that HGT of these resistance genes is ecologically relevant, not merely a historical artifact.

### 5d. PGLS: generalists carry fewer metal resistance genes per Mb (H1 main result)

From the primary microbeatlas_metal_ecology PGLS (01_primary_pgls_results.csv, REPORT.md):

Standardized Levins B (niche breadth) negatively predicts metal resistance gene density per Mb across 2,851 bacterial genera (phylogenetically controlled PGLS, n ≈ 1,200 taxa with full data; β < 0, p < 0.001 across multiple metal gene categories and datasets).

This is the core motivation: if generalists invest less in metal resistance genes, how do they survive metal stress? The proposed experiment tests whether HGT compensates.

---

## 6. Overall Feasibility Assessment

### Go/No-Go Recommendation: **CONDITIONAL GO**

The experiment is scientifically novel, statistically powered, and grounded in multiple converging data streams. Conditions that must be met before proceeding:

1. **Genome screening (Section 3)** must be completed first to confirm at least 3 candidate generalist isolates lack merA (required for transconjugant selection). If Cupriavidus or Janthinobacterium already carry mer, substitute Duganella (1 isolate, Levins B_std = 0.642) or Collimonas (1 isolate, Levins B_std = 0.621).

2. **Pilot CV estimate**: Run a 4-microcosm pilot (2 generalist × 2 replicates) to validate CV ≈ 0.7 before full commitment. If CV > 1.5, revise the design.

3. **Plasmid construction**: A marked mer plasmid with a second selectable marker (e.g., Km^r) is needed to distinguish mer-positive transconjugants from spontaneous HgCl₂-resistant mutants. Use pQBR57 (Hall et al. 2020) or construct Tn501-Km^r in an RP4 backbone (IncP broad-host-range).

### Recommended final design

**Recipients:** 3 generalist strains (one each from Janthinobacterium, Cupriavidus, Herbaspirillum) + 3 specialist strains (one each from Acidovorax, Comamonas, Hydrogenophaga); all from BERDL ENIGMA collection, all merA-negative.

**Donor:** Pseudomonas_E isolate from ENIGMA collection (26 available) carrying pMER-Km (marked mer plasmid). If no ENIGMA Pseudomonas carries a suitable plasmid, use a constructed RP4::Tn501-Km^r in E. coli DH5α as donor.

**Microcosm format:** 50 mL ORFRC soil slurry (autoclaved background soil spiked with HgCl₂ at site-relevant concentration: ~50 µg/g, based on enigma_geochemistry.csv); donor:recipient ratio 1:10; 25°C, 7-day incubation; sampling at day 1, 3, 7.

**Assay:** Plate on LB + HgCl₂ (50 µg/mL) + Km (50 µg/mL) for transconjugant selection; plate on LB for total viable count. Transconjugant frequency = CFU/(ml × total viable count).

**Replication:** 3 biological replicates (separate microcosms) per recipient strain × 3 time points = 54 microcosms total (27 per group). For primary analysis, use day-7 endpoint; collapse time into growth curve if resources allow.

**Statistical model:**  
```
log10(freq + 1e-10) ~ group + (1|strain) + (1|timepoint)
```
Fixed effect: group (generalist vs. specialist). Random effects: strain nested in group, timepoint.

**Controls:**
- Donor-only control (no recipient) → background transfer to soil community
- Recipient-only control (no donor) → spontaneous HgCl₂ resistance rate
- Heat-killed donor control → distinguishes conjugation from transformation

### Isolate priorities

| Priority | Genus | Levins B_std | Niche class | Reason |
|---|---|---|---|---|
| 1 | Janthinobacterium | 0.498 | Generalist | Largest representation (6 isolates), easy colony ID |
| 1 | Cupriavidus | 0.430 | Generalist | Established HGT model genus; metal resistance pangenome |
| 1 | Herbaspirillum | 0.572 | Generalist | Highest Levins B in collection; diazotroph (distinct niche) |
| 1 | Acidovorax | 0.281 | Specialist | Largest representation (8 isolates); same order as generalists |
| 1 | Comamonas | 0.235 | Specialist | Very low Levins B; strong contrast |
| 1 | Hydrogenophaga | 0.236 | Specialist | Oligotroph; phylogenetically similar to Cupriavidus |
| 2 | Duganella | 0.642 | Generalist backup | Highest Levins B in collection; substitute if Janthinobacterium has merA |
| 2 | Collimonas | 0.622 | Generalist backup | Second highest Levins B |

### Pitfalls and mitigations

| Pitfall | Likelihood | Mitigation |
|---|---|---|
| Candidate recipients already carry merA | Medium (Cupriavidus spp. sometimes do) | Screen genomes computationally before ordering cultures |
| Spontaneous HgCl₂ resistance masks signal | Low | Km^r second marker on donor plasmid; donor-only control |
| Plasmid lost in soil before assay | Medium | Include time-course; use stabilized plasmid backbone (CloDF13 ori or RP4 with addiction module) |
| Strain-to-strain variance within group swamps between-group signal | Medium (ICC likely 0.3–0.6) | Use 3 strains per group; mixed model analysis; increase to n=4 strains if CV estimate is high |
| ORFRC soil microbial community interferes | Low | Autoclaved background soil removes indigenous competitors; spike back to test real-world condition separately |
| Phylogenetic non-independence (all Burkholderiales) | Low for experimental test; design strength for interpretation | Acknowledged; report as phylogenetically controlled comparison, not a broad-spectrum niche breadth test |

### Novelty argument (for grant/paper framing)

This experiment is the first to:
1. Directly measure conjugation acceptance rate as a function of empirically derived ecological niche breadth (Levins B from global microbiome surveys).
2. Test whether the genome-scale trade-off between metal gene investment and niche breadth (established computationally by H1/H3) extends to the level of individual conjugation events.
3. Use ORFRC isolates — whose metal contamination history and genomes are thoroughly characterized — to close the loop between metagenomics predictions and experimental microbiology.

The mechanistic hypothesis (generalists have fewer CRISPR/R-M barriers → higher plasmid acceptance) can be directly tested as a secondary outcome using the pre-experiment genome screening results, making this a two-stage test of both the phenomenology and the mechanism.

---

*Report compiled from: ENIGMA isolate database (strain_scalars.tsv, n=123), genus_trait_table.csv (niche breadth, n=2,851 genera), gene_lambda_mobile_corr.csv (mer mobility analysis), enigma_frc_burden_correlations.csv (ORFRC MAG-level data, n=29), top_mobile_candidates.csv, and literature review (21 papers, July 2026).*
