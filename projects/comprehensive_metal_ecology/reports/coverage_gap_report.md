# Data Integration Gap Report

**Project:** comprehensive_metal_ecology  
**Date:** 2026-07-16  
**Script:** `analysis_coverage_gaps.py`

---

## Gap 1 — Functional subset coverage

### What was checked

Within the 1,543-genus primary PGLS panel, genera were classified as present or absent in the `resistance_per_mb` (67.9% coverage, n=1,047) and `cofactor_per_mb` (54.6% coverage, n=842) subcategory predictors. The groups were compared on B_std, genome size, primary KO density, and MicrobeAtlas sample count.

### Findings

**Resistance subset (496 genera absent)**

| Variable | Present (n=1,047) | Absent (n=496) | Mann–Whitney p |
|----------|-------------------|----------------|----------------|
| B_std | 0.217 (IQR 0.11–0.34) | 0.245 (IQR 0.15–0.38) | 1.8 × 10⁻⁶ |
| Genome (Mb) | 3.50 (IQR 2.67–4.49) | 3.45 (IQR 2.52–4.56) | 0.37 |
| ko_per_mb_primary | 8.41 (IQR 6.30–11.17) | 7.34 (IQR 5.53–9.41) | 4.8 × 10⁻¹¹ |
| n_soil_samples | 909 (IQR 226–5,213) | 546 (IQR 140–2,424) | 8.2 × 10⁻⁷ |

The genera missing from the resistance subset have significantly lower primary KO density, fewer MicrobeAtlas detections, and slightly higher B_std. The B_std difference runs in the direction opposite to the cofactor finding: the missing resistance genera lean generalist, not specialist. Notably, extreme specialists (B_std < 0.1) are under-represented among the missing genera (10.9%) compared with those present (20.3%). Phylum composition is broadly similar — Proteobacteria and Firmicutes both around 42–44% and 21%, respectively.

**Cofactor subset (701 genera absent)**

| Variable | Present (n=842) | Absent (n=701) | Mann–Whitney p |
|----------|-----------------|----------------|----------------|
| B_std | 0.227 (IQR 0.11–0.35) | 0.223 (IQR 0.14–0.35) | 0.110 |
| Genome (Mb) | 3.72 (IQR 2.99–4.73) | 3.09 (IQR 2.30–4.14) | 3.0 × 10⁻¹⁹ |
| ko_per_mb_primary | 8.40 (IQR 6.36–11.07) | 7.50 (IQR 5.68–9.78) | 3.5 × 10⁻⁷ |
| n_soil_samples | 1,147 (IQR 269–6,652) | 537 (IQR 139–2,128) | 2.1 × 10⁻¹³ |

The cofactor subset is missing genera with significantly smaller genomes (−17% in median Mb, p=3.0×10⁻¹⁹), lower primary KO density, and fewer detections, but critically **B_std is not significantly different** (p=0.110). The missing genera are not systematically more or less specialist — they are simply less well-represented in the genomic database.

The phylum distribution, however, shows a substantial bias. Genera present in the cofactor subset are 51.9% Proteobacteria, while absent genera are 31.8% Proteobacteria and 29.7% Firmicutes. Firmicutes are markedly under-represented in the cofactor-covered set (14.5% vs 29.7%). This is mechanistically expected: the seven cofactor KOs are primarily cobalamin and Fe–S cluster genes, which are constitutively present in metabolically diverse Proteobacteria but may be absent or replaced by non-KO-annotated alternatives in small-genome Firmicutes.

### Interpretation

**For the resistance result (null, β ≈ 0):** The subset bias is mild. Missing genera have slightly higher B_std (more generalist) and lower KO density. If these genera were included and had no resistance KOs detected, they would add noise without changing direction. The null result is conservative: if anything, including the more-generalist missing genera would reinforce β ≈ 0.

**For the cofactor result (β = −0.013, p = 0.010):** The B_std distributions of present and absent genera are statistically indistinguishable (p = 0.11), so the regression is not sampling a biased slice of the B_std axis. However, the Firmicutes under-representation (29.7% absent vs 14.5% present) means the cofactor signal is dominated by Proteobacteria. Whether Firmicutes would show the same cofactor–niche association is unknown. This is the more important caveat to flag: the cofactor result characterises metabolically complex, larger-genome lineages and may not extend to smaller-genome Firmicutes that often lack the relevant KOs entirely.

**Overall assessment:** The coverage gap is partly a power issue (fewer genera → wider confidence intervals) and partly a Firmicutes representation issue for the cofactor subset. It is not a B_std sampling bias. The core findings are unlikely to reverse, but the cofactor result should be qualified as applying primarily to Proteobacteria-dominated lineages.

---

## Gap 2 — Unmatched genera

### What was checked

The 1,543-genus PGLS panel was compared against all MicrobeAtlas genera with B_std data (genus_trait_table, n=2,851) to identify the 1,308 genera with niche breadth but no GTDB KO density. These were characterised by B_std, MicrobeAtlas sample count, phylum distribution, and rarity profile. A SILVA–GTDB name reconciliation was also performed using the `gtdb_genus_lower` column in the trait table.

### Findings

**Scale of the gap**

| Dataset | n genera | Notes |
|---------|----------|-------|
| genus_microbeatlas_sample_counts (all MA) | 3,433 | All genera seen in 16S samples |
| genus_trait_table (B_std-qualified, ≥5 samples) | 2,851 | Genera with computed B_std |
| PGLS panel (GTDB KO density + B_std) | 1,543 | Final analysis set |
| Unmatched (B_std-qualified, no GTDB KO) | 1,308 | 45.9% of trait-table genera |

**B_std and sample counts**

Unmatched genera have significantly lower B_std (median 0.176 vs 0.225, p=3.6×10⁻¹¹) — they are systematically more specialist than matched genera. They are also substantially less abundant in MicrobeAtlas (median 1,656 vs 7,585 sample detections, p=1.7×10⁻⁷⁶). Despite their lower detection frequency, unmatched genera account for 29.4% of total sample detections across the full trait table — not a trivial fraction.

**Rarity profile**

Most unmatched genera are not ultra-rare:

| Threshold | Unmatched | Matched |
|-----------|-----------|---------|
| < 10 detections | 1.0% | 0.0% |
| < 50 detections | 6.7% | 0.4% |
| < 100 detections | 11.1% | 0.8% |
| < 500 detections | 29.4% | 6.5% |

Only 11% of unmatched genera are detected in fewer than 100 samples. The majority are moderately common organisms, not ultra-rare environmental sequences.

**Top unmatched genera by detection frequency**

The 20 most common unmatched genera include ecologically significant organisms with >100,000 sample detections, high B_std values (0.3–0.6), and broad biome coverage:

*Actinomarinicola* (205k detections), *Hyphomicrobium* (204k, methylotrophic denitrifier), *Gaiella* (199k, widespread soil), *Nitrospira* (196k, nitrite oxidiser), *Solirubrobacter* (182k, radiation-resistant soil), *Dongia* (179k), *Sporichthya* (173k), *Conexibacter* (160k), *Asprobacter* (154k), *Stenotrophobacter* (152k), *Steroidobacter* (149k, steroid-degrading), *Pedomicrobium* (147k), *Aquihabitans* (145k), *Ilumatobacter* (141k), *Nitrososphaera* (131k, ammonia-oxidising archaeon), *Tumebacillus* (128k).

These are not obscure environmental sequences. *Nitrospira*, *Hyphomicrobium*, *Nitrososphaera*, and *Steroidobacter* are functionally well-characterised soil and aquatic taxa that are absent from the PGLS panel not because they are rare but because their genomes have not been assembled into the GTDB-annotated pangenome at genus level. *Nitrososphaera* is archaeal (Thaumarchaeota) and excluded by design from the bacterial analysis; the rest are genuinely unrepresented in GTDB r214 at the level of the genus cluster used.

**Phylum distribution**

| Phylum | Matched | Unmatched |
|--------|---------|-----------|
| Proteobacteria | 42.8% | 33.7% |
| Firmicutes | 21.4% | 16.0% |
| Actinobacteria | 13.2% | 11.1% |
| Bacteroidetes | 11.7% | 15.6% |
| Cyanobacteria | 1.7% | 3.5% |
| Euryarchaeota | 0.0% | 7.8% |

Euryarchaeota (7.8% of unmatched) are archaeal and excluded by the prokaryote analysis scope. Among bacteria, Proteobacteria are under-represented in the unmatched pool; Bacteroidetes and Cyanobacteria are modestly over-represented.

**Taxonomy reconciliation: naming gap or true absence?**

Among the 869 unmatched genera with a `gtdb_genus_lower` entry in the trait table, zero had a GTDB name that matched any genus in the PGLS panel. Among matched genera, zero showed a SILVA name differing from their GTDB name. The SILVA–GTDB name collision rate is effectively zero for matched genera. Unmatched genera genuinely lack GTDB genus-level pangenome entries — the gap is a true absence from the genomic database, not a taxonomy reconciliation artefact.

### Interpretation

The 50% genus-match rate overstates the limitation in one direction and understates it in another.

**Overstated:** The unmatched genera are not predominantly ultra-rare or unculturable. Most have hundreds to hundreds-of-thousands of 16S detections. Calling them "disproportionately rare, unculturable, or environmentally restricted" is partly true but misses the substantial fraction of common, ecologically important genera that simply lack GTDB genus-level pangenome coverage. The actual reason for absence is taxonomic fragmentation — GTDB r214 may split or not have assembled these genera at the genus-cluster level used by `kbase.ke_pangenome`.

**Understated in one respect:** The unmatched genera are significantly more specialist (lower B_std, p=3.6×10⁻¹¹). The PGLS analysis characterises the more generalist half of the prokaryotic microbiota. If KO density in specialist lineages behaves differently — for example, if extreme specialists have very high or very low per-Mb metal-gene investment for reasons unrelated to niche — the overall β estimate may not generalise to the full microbiota.

**Effect on conclusions:** The directional prediction (cofactor negative, resistance null) is grounded in the 1,543 genera that happen to be well-represented in both the 16S amplicon database and the GTDB-annotated genomic database. Given that the unmatched genera include metabolically important soil organisms (*Nitrospira*, *Hyphomicrobium*, *Pedomicrobium*) with diverse functional repertoires, whether these taxa would show the same cofactor–niche relationship is genuinely unknown. This is the strongest form of the gap-2 limitation: not rarity, but the systematic exclusion of biogeochemically important genera that lack pangenome coverage.

---

## Summary

| Gap | Severity | Bias type | Effect on conclusions |
|-----|----------|-----------|----------------------|
| Resistance coverage (67.9%) | Low | Mild: absent genera slightly more generalist and lower KO density | Null result likely unaffected; if anything, more conservative |
| Cofactor coverage (54.6%) | Moderate | Firmicutes under-represented (29.7% absent vs 14.5% present); B_std not biased | Cofactor signal is Proteobacteria-dominated; generalisability to Firmicutes unknown |
| Unmatched genera (~50%) | Moderate | Missing genera significantly more specialist (B_std p=3.6×10⁻¹¹); not ultra-rare | Entire PGLS characterises the generalist-enriched portion of microbiota; functionally important soil genera absent |

The findings do not indicate that the paper's central results are wrong. They indicate that the results apply to the genomically well-represented, relatively generalist fraction of the prokaryotic diversity present in 16S surveys, and that the cofactor signal in particular is dominated by Proteobacteria-class taxa. Both points warrant explicit statement in the manuscript.
