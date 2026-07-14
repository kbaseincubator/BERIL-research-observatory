# Report: Soil Microbial Dark Matter and the Clay Shield Null Result

## Status

Preliminary — clay shield and GDI analyses complete across all source notebooks.
NB05 spatial validation and NB06 figures pending.

## Key Findings

**Clay Shield Hypothesis — Null Result:**
- **5,441 soil samples** with clay content, mine proximity, nighttime lights, uranium,
  and functional gene counts (n_genes_by_counts).
- **All predictive models have negative out-of-sample R²**:
  - Soil & Climate: R² = −0.205 ± 0.197
  - Geochemical: R² = −0.331 ± 0.071
  - Industrial: R² = −0.221 ± 0.042
- **Shield efficiency test**: low-clay CV R² = −0.268, high-clay CV R² = −0.292;
  difference = 0.024 [95% CI: −0.423, 0.161] — **not significant, CI includes zero**.
- Clay appears as a consistent feature (importance ≈ 0.14) but does not improve
  predictive accuracy in high-clay soils.

**Genomic Discovery Index:**
- **GDI = OTU Richness / (Mean Genome Completeness + 1)** computed at 1° spatial bins.
- Highest GDI (genomic frontier): Forest (902.36), Cropland (890.82).
- Lower GDI (relatively well-mapped): Grassland (503.42), Wetland (525.13).
- **pH discovery bias**: frontier areas (GDI > 1000) have mean pH = 6.74 vs. mapped
  areas mean pH = 5.94 — **+0.8 pH unit gap**, indicating systematic under-sampling
  of alkaline soil microbiomes in public genomic databases.

## Interpretation

The clay shield hypothesis is **not supported** at global scale. Clay content shows
correlational associations with microbial functional potential and some interaction
with industrial stressors, but does not improve predictive accuracy in high-clay soils
relative to low-clay soils (CI includes zero). The negative out-of-sample R² across all
model families indicates that the functional potential variable is not predictable from
the measured stressors at this scale, likely due to spatial autocorrelation, batch
effects, and unmeasured confounders.

The GDI results reveal a systematic alkaline-soil sampling gap in public genomic
databases. Forest and cropland soils are diverse but poorly represented at the genomic
level. This has implications for any study drawing functional inferences from genome
reference databases in these biomes.

## Critical Assessment

**Negative out-of-sample R² diagnosis is incomplete.** All three predictive model
families achieve negative CV R², meaning they predict worse than the training mean.
Three possible causes have not been distinguished: (a) train/test distributional shift
due to spatial autocorrelation within GroupKFold folds, (b) high-leverage outlier
samples in test folds that dominate the MSE, or (c) genuine unpredictability of
functional gene counts from the measured predictors at global scale. These three causes
have different scientific implications — only (c) supports a strong null result
interpretation. Causes (a) and (b) would indicate a modelling failure, not a biological
null result.

**GDI formula validity.** GDI = Richness / (Mean_Completeness + 1) is a novel index
without published precedent. The formula gives a GDI of 902 even if there are zero
genomes (completeness = 0, denominator = 1). It conflates two distinct dimensions
(sampling gap and OTU richness) into one number in a way that could be dominated by
the richness term alone. An alternative — separate reporting of richness and completeness,
with a 2D scatter rather than a scalar index — would be more interpretable.

**Forest vs. Cropland GDI difference is small.** Forest (902.36) vs. Cropland (890.82)
is a 1.3% difference; without bootstrap CIs these are not meaningfully distinguishable.
The scientific claim should be framed as "Forest and Cropland are jointly the highest-GDI
biomes" rather than implying a ranked ordering.

**pH discovery bias (+0.8 units) needs reverse-causality check.** Alkaline soils may
have fewer genomes in databases simply because fewer samples from those pH ranges were
ever sequenced (sampling effort bias), not because alkaline microbes are harder to
assemble or less studied. Controlling for the number of 16S samples in each pH bin
before computing GDI would distinguish true assembly/annotation gaps from sampling gaps.

**Spark-required analyses:** All NB05 validations require re-running from the BERIL
Observatory 16S tables and `kbase_ke_pangenome` completeness data. No local CSV output
is available for these validations.

## Pending Validation

1. Negative R² decomposition: distinguish distributional shift, outlier leverage, and
   true unpredictability (requires re-run with spatial blocking)
2. Rarefaction-corrected GDI (uniform 16S sequencing depth before richness calculation)
3. Bootstrap 95% CIs on biome-level GDI rankings (requires raw data re-run)
4. pH discovery bias: control for number of 16S samples per pH bin
5. Report Forest vs. Cropland GDI with uncertainty before claiming ranked ordering
