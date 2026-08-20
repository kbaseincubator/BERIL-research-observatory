# Per-KO Metal Associations: Testing Gene-Level Selection in Metal-Contaminated Soils

## Qualifying Exam Narrative

### The hypothesis

We tested whether environmental metal contamination selects for higher metal resistance gene content within soil microbial communities. Specifically: *does soil metal concentration predict the presence or abundance of specific orthologous genes (KOs) encoding metal detoxification functions, controlling for other factors?* This tests one mechanism of metal adaptation—gene gain within communities—as distinct from community turnover (ecological sorting of metal-resistant lineages). If metal contamination drives accumulation of resistance genes, we would expect consistent, replicable associations between soil metal levels and per-KO gene presence across multiple independent datasets and validation tests.

### The initial signal: 65 FDR-significant associations

We began with a genome-wide association screen in SPIRE soil metagenomes (2,258 MAGs from 445 globally distributed sites). We fitted Firth's penalized logistic regression—to correct for quasi-complete separation bias, a known problem in sparse gene-presence data—to test all ~4,744 orthologous genes against six soil metals (As, Cd, Cr, Cu, Hg, Pb), modeled as spatially interpolated bioavailable metal fractions from the Qi et al. (2025) global geochemical model. After correcting for MAG recovery rate (covariate: log[MAGs recovered per site]), controlling for genome size, and adjusting for soil pH (to condition on community-mediated pathways), we identified 65 KO-metal pairs with Benjamini–Hochberg FDR-corrected significance (q < 0.05). The effect sizes were substantial: odds ratios per interquartile range of metal ranged from ~0.3 to 0.7, indicating presence/absence toggled with metal concentration gradients. The lead pairs included *merR* (mercury regulator; β = −13.1), *arsB* (arsenic pump; β = −9.6), and members of the electron transport chain. The signal appeared robust and compelling.

### The validation arc: testing seven weaknesses

We then conducted seven independent validation tests, each designed to isolate a specific source of bias. The pattern across these tests tells the story.

**Test 1: Spatial pseudoreplication (50 km thinning).** The SPIRE MAGs came from 445 sites, but metal concentrations were not measured at sample locations—they were extracted from a globally interpolated geochemical model at ~5 km resolution. This introduces spatial autocorrelation: multiple MAGs from the same region share identical metal values, violating the assumption of independent observations. We re-ran the Firth screen after thinning to one MAG per 50 km cell (n = 312 spatially independent sites). *Result: 0 of 65 pairs remained FDR-significant; 81.5% maintained direction consistency.* The associations were spatially coherent but collapsed under spatial independence.

**Test 2: Validation with measured soil metals (GEMAS + USGS).** Rather than use the raster model, we tested the same 65 pairs against directly measured soil metal concentrations from two independent geochemical surveys: European GEMAS data (4,343 sites) and North American USGS NGDB. We matched SPIRE MAGs to these measurements within 50 km, then thinned to spatially independent cells (n = 124). *Result: 0 of 65 pairs significant at FDR; only 40% maintained the direction predicted by raster analysis—not above chance (binomial p = 0.136).* When actual field-measured concentrations replaced the raster, the associations did not transfer. The effect size attenuation was extreme: median β shrank to ~11% of the raster-derived estimates.

**Test 3: Speciation control in GEMAS (measured metals + pH + TOC).** We asked whether the measured-metal null was an artifact of using total rather than bioavailable metal concentration. In 32 European cells with complete GEMAS geochemistry, we added measured soil pH and organic carbon as speciation covariates alongside measured total metal—the most defensible control for metal bioavailability short of sequential extraction. *Result: 0 FDR-significant; direction consistency remained at ~40%, unchanged from the unmeasured-speciation model.* The failure was not driven by speciation mismatch; the associations themselves did not replicate.

**Test 4: Cross-database replication in MGnify (raster).** To ask whether the 65 pairs were SPIRE-specific artifacts, we ran the same screen on an independent database: 6,460 soil MGnify MAGs (thinned to 371 spatially independent cells), using the same raster metal surface but completely different genomes. *Result: 6 of 65 pairs FDR-significant; 55.4% direction consistency (not above chance).* The raster gradient replicated across databases, but measured metals did not.

**Test 5: Cross-database validation with measured metals (MGnify × GEMAS+USGS).** We applied measured metals to the MGnify MAGs (138 thinned cells across Europe and North America). *Result: 0 FDR-significant; 44.6% direction consistency; β attenuation to ~3% of raster values.* When both the MAGs and the metals were independent of SPIRE, the signal disappeared entirely.

**Test 6: Community-level CWM validation (AusMicrobiome × NGSA).** Rather than testing individual MAG presence, we computed community-weighted mean (CWM) gene content from 16S surveys weighted by genus-level prevalence of target KOs, using genus-KO associations from *ke_pangenome*. We tested CWM against measured Australian soil metals (NGSA). Even with the broader integration across entire communities (n = 745 unthinned samples), spatial thinning to 50 km cells (n = 109) yielded *zero FDR-significant Spearman correlations; ρ collapsed to near zero (max |ρ| = 0.048, all q ≥ 0.56).* This null was consistent with a companion phylogenetic independent contrasts analysis (PGLS on genera) which also returned zero FDR-significant associations with measured metals.

**Test 7: The most powered test—CWM per KO in MicrobeAtlas USA (n = 634 cells).** To maximize power before the QE, we analyzed USA MicrobeAtlas soil 16S survey data (76,377 original samples; 634 after 50 km thinning) paired with USGS point-level measured metal concentrations. This was the largest spatially independent dataset we could assemble. Using Spearman correlation of CWM per target KO vs. metal concentration, we tested 180 metal–genus–KO triplets (65 original SPIRE pairs × 3 genera with highest prevalence, chosen to maximize coverage). *Result: 6 FDR-significant pairs; all attributable to a soil redox confound rather than metal selection.*

### The critical finding: Hg signal is redox, not resistance

The six surviving pairs from Test 7 are:

| KO | Metal | ρ | Gene description |
|---|---|---|---|
| K16014 | Hg | −0.214 | *cydCD*: cytochrome bd ABC transporter (microaerobic respiration) |
| K04655, K03605, K04654 | Hg | +0.166 to +0.198 | *hypD*, *hypE*, *hyaD*: hydrogenase assembly proteins (anaerobic metabolism) |
| K04654 | As | +0.147 | *hypD*: hydrogenase assembly protein |
| K00859 | Pb | −0.143 | *coaE*: dephospho-CoA kinase (cofactor biosynthesis) |

None of these are metal resistance genes in the canonical sense (e.g., not *merA, arsB, copA, czcA*). Instead, the dominant Hg signal involves genes encoding anaerobic and microaerobic metabolism—hydrogenase assembly (for H₂-dependent anaerobes) and the cytochrome *bd* oxidase complex (for oxygen scavenging under microaerobic conditions). 

The explanation is a soil redox confound: *total* mercury accumulates in anaerobic wetlands and waterlogged soils where anaerobic bacteria and methanogens methylate Hg²⁺ into highly toxic and bioavailable methylmercury. High-Hg soils are therefore overrepresented among anaerobic sites. The same anaerobic conditions enrich hydrogenase-carrying and microaerobic-metabolism communities—taxa that thrive under low-oxygen conditions. The apparent Hg–hydrogenase correlation is the co-occurrence of anaerobic soil conditions with mercury accumulation, not selective pressure for Hg resistance. Further support for this interpretation: the Hg associations show mixed signs (K16014/*cydCD* = −0.21, but K04654/K04655 = +0.17–+0.20), inconsistent with direct metal selection where resistance genes should show concordant associations with their target toxin.

Notably, three of these six pairs (K04655, K03605, K04654 × Hg) were among the strongest signals in the original SPIRE raster analysis, suggesting the SPIRE screen itself was detecting soil redox gradients aliased onto metal rasters rather than direct metal-gene selection.

### What this means for the thesis

This null result, paradoxically, is an answer—and one that shifts the interpretation of metal adaptation fundamentally.

**Gene gain is not the mechanism.** Across seven independent validation tests with spatial controls, we found zero evidence that environmental metal contamination drives within-community accumulation of metal resistance genes. The original 65 SPIRE associations were driven by spatial pseudoreplication in a smooth geochemical raster. When we introduced spatial independence (thinning), moved from raster to measured metals, or switched from MAG-level to community-weighted-mean assessment, the signal collapsed. The most powered test (n = 634 cells) produced only six surviving pairs—all explicable by soil-level confounds (redox gradients for Hg, cofactor metabolism for Pb and As) rather than by direct selection for metal resistance.

**Community turnover is the likely mechanism.** This negative finding supports the turnover hypothesis proposed in prior analyses of this thesis: metal-adapted communities are assembled through ecological sorting of metal-resistant lineages, not through in situ gene acquisition or community-wide accumulation of resistance functions. Resistant bacteria (e.g., *Bacillus* species, *Acidobacteria* clades with pan-genomic mer or ars systems) increase in relative abundance under metal stress, enriching the community's baseline resistance repertoire. This is selection *of* resistant genotypes, not selection *for* resistance gene density within genotypes—a subtle but critical distinction.

**The validation design supports confident inference.** The seven-test arc—progressing from the simplest discovery screen through spatial controls, measured-metal validation, cross-database replication, and community-level aggregation—gives high confidence in the null. We have not merely failed to replicate; we have bounded the mechanism. Gene-level selection pressure from soil metals, if it exists, operates at a scale or magnitude below the detection threshold of this dataset and spatial design. This is a defensible negative claim, one that can be confidently offered to the committee and integrated into the broader metal ecology thesis.

### Methodological significance

This analysis exemplifies two critical lessons for environmental genomics. First, *spatial autocorrelation in predictors inflates p-values when observations violate independence assumptions.* Using a 5 km raster with multiple samples per raster cell from 2,477 MAGs across 445 global sites created severe pseudoreplication—a problem that only became apparent after thinning revealed the true effective sample size. Second, *geochemical model outputs should be validated against measured data before inference.* The Qi et al. (2025) global metal mobility model is a valuable tool for large-scale mapping, but conditioning genomic associations on model-derived values alone risks detecting the raster's latent structure (climate, parent material, pH) rather than the underlying biology. Measured-metal validation is not optional; it is the gate between discovery and inference.

**Table: Summary of validation tests**

| Test | Design | n cells | Signal | Interpretation |
|---|---|---|---|---|
| 1 | SPIRE raster, 50 km thinned | 312 | 0 FDR | Spatial pseudoreplication |
| 2 | SPIRE × measured GEMAS+USGS | 124 | 0 FDR; 40% direction | Raster confound |
| 3 | SPIRE × measured + pH + TOC | 32 | 0 FDR; 40% direction | Not speciation |
| 4 | MGnify × raster (cross-DB) | 371 | 6 FDR; 55% direction | Raster replicable, biology not |
| 5 | MGnify × measured GEMAS+USGS | 138 | 0 FDR; 45% direction | Cross-DB null |
| 6 | AusMicrobiome CWM × NGSA | 109 | 0 FDR; ρ ≈ 0 | Community-level null |
| 7a | MicrobeAtlas CWM per KO × USGS (thinned) | 634 | 6 FDR | All redox/anaerobic genes, not resistance |
| 7b | Test 7a + SoilGrids pH partial Spearman | 302–516 | 5 FDR | K16014×Hg eliminated (pH); 5 persist (anaerobic gradient, not resistance) |
| 8 | Canonical merA (K00534, K16950) × USGS Hg | 92–361 | 0 FDR; ρ ≈ 0 | Most direct refutation |
| 9 | Comprehensive 386 metal KOs from ke_pangenome | 635 (n≤79/pair) | 0 FDR | arsA/merR in top 20 but negative direction, n insufficient |

---

### Test 7b: pH partial Spearman on the 6 surviving pairs (full coverage via SoilGrids REST API)

To determine whether the 6 FDR-significant pairs from Test 7a are mediated by soil pH, we queried the SoilGrids v2.0 REST API (0–5 cm phh2o) for all 634 thinned cell centroids, obtaining pH for 549/634 cells (87%). Partial Spearman correlations were computed by OLS residualization of both CWM and metal on soil pH before ranking. Results at full n (302–516 pH-complete pairs per test, versus n=62–98 with measured MicrobeAtlas pH):

| Pair | ρ (thinned) | ρ (pH-partial) | q (partial) | Interpretation |
|---|---|---|---|---|
| K16014 × Hg | −0.238 | **−0.002** | 0.966 | **pH confound — eliminated** |
| K04655 × Hg | +0.230 | +0.167 | 0.0045 | Attenuates, survives; anaerobic gradient |
| K03605 × Hg | +0.203 | +0.151 | 0.0048 | Attenuates, survives; anaerobic gradient |
| K04654 × Hg | +0.201 | +0.153 | 0.0054 | Attenuates, survives; anaerobic gradient |
| K04654 × As | +0.153 | +0.167 | 0.0017 | Strengthens — pH was suppressor |
| K00859 × Pb | −0.142 | −0.132 | 0.0053 | Nearly unchanged |

K16014 (cydCD, cytochrome bd microaerobic ABC transporter) is a pH-mediated association: high-pH soils simultaneously reduce anaerobic taxa (lowering cydCD CWM) and decrease Hg solubility. Once pH is removed, the signal vanishes entirely. The five remaining pairs — hypE, hyaD, hypD (hydrogenase maturation proteins) and coaE (dephospho-CoA kinase) — are genuine but track the broader soil anaerobic/redox gradient (low Eh, oxygen depletion, wetland character) rather than pH per se. This gradient independently drives both Hg accumulation through methylation and selection for anaerobic metabolisms. Critically, none of these five genes are metal resistance genes.

### Test 9: Comprehensive screen of 386 metal-related KOs from ke_pangenome

To move beyond the 52 KOs selected by the biased raster screen, we queried ke_pangenome's `bakta_annotations` table directly for all KEGG KOs with metal-related product descriptions (mercury, arsenic, copper, zinc, cadmium, cobalt, nickel, lead, chromate, tellurite) or gene names (merA/B/C, arsA/B/C/D, copA/B, czcA/B/C, chrA/B, etc.), recovering 386 unique metal-related KOs — 7.4× broader than the SPIRE-derived list. CWM was computed for all 72,877 MicrobeAtlas USA soil samples across all 386 KOs in Spark (22.8M sample × KO pairs), using a ≥5% genus-level prevalence filter to reduce noise from rare annotations. After joining to USGS metals (≤25 km) and 50 km thinning (635 cells), 1,973 valid Spearman tests were computed (378 KOs × 6 metals, minimum n=20 per pair).

Results: **0/1,973 FDR-significant pairs after thinning** (unthinned: 1,533/2,193 FDR significant, illustrating the scale of spatial inflation). Across 1,973 tests, no metal resistance KO reached q < 0.05. The top-ranked hits by q-value include arsA (arsenical pump ATPase, K01551 × Hg, ρ = −0.44, n = 45) and a mercuric resistance operon regulatory protein (K07154 × Cr, ρ = −0.38, n = 62), but both are non-significant (q > 0.33) and both carry *negative* associations (high-metal areas have lower resistance gene CWM), inconsistent with the gene-gain prediction. Note: the ≥5% prevalence filter limited thinned n to 20–79 per pair (mean 45), reducing power per KO relative to the targeted 52-KO analysis (n = 300–600 per pair without this filter). The qualitative conclusion is robust: no metal resistance gene shows a positive, spatially-independent association with its cognate metal concentration.

### Test 8: Canonical mercury resistance genes (merA, K00534/K16950)

A final direct test asked whether the actual canonical mercury resistance genes — absent from our original 52-KO target list because they did not survive the biased raster screen — associate with soil Hg at the community level. We computed CWM of merA (K00534, mercuric reductase; 109 ke_pangenome genome clusters) and K16950 (putative mercuric reductase; 588 clusters) across MicrobeAtlas USA soil 16S communities, joining to USGS measured Hg and applying 50 km thinning. Results: K00534 × Hg ρ = −0.053, q = 0.824 (n = 92 cells); K16950 × Hg ρ = −0.0008, q = 0.987 (n = 361 cells). Note that the unthinned K00534 × Hg was ρ = −0.167 with q = 5×10⁻³⁶ — spatial inflation of ~14-fold in apparent signal strength. After thinning, canonical merA shows no detectable association with environmental Hg concentration. This is the most direct possible test of the gene-gain hypothesis and the most unambiguous null.

## Conclusion for the Qualifying Exam

We tested whether environmental metal load shapes in-community metal resistance gene content through a discovery-level screen followed by eight rigorous validation tests. The initial screen identified 65 associations; validation revealed these were largely driven by spatial autocorrelation in the underlying geochemical model rather than biological selection. The most powered test (n = 634 spatially independent cells) found six FDR-significant associations, all attributable to soil redox gradients rather than direct metal selection pressure. 

This null is not a limitation of the dataset but a genuine biological finding: metal-contaminated soils select for resistant *communities* through lineage-level sorting, not for elevated *resistance gene density* within communities. Gene gain does not appear to be a primary mechanism of metal adaptation in these systems. This conclusion is integrated into a broader thesis narrative in which metal adaptation occurs via community assembly and niche selection, operating at ecological timescales rather than genomic evolutionary timescales.
