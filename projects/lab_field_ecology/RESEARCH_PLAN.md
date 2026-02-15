# Research Plan: Lab Fitness Predicts Field Ecology at Oak Ridge

## Research Question

Do lab-measured fitness effects under contaminant stress predict the field abundance of Fitness Browser organisms across Oak Ridge groundwater sites with varying geochemistry?

## Hypotheses

- **H1**: FB organisms with more genes important for uranium/metal tolerance are more abundant at high-uranium/metal field sites.
- **H2**: The genus-level relative abundance of FB organisms correlates with site geochemistry that matches their lab-tested stress conditions.
- **H3**: Sites with extreme geochemistry (high uranium, high metals) have community compositions enriched in organisms that tolerate those conditions in the lab.

- **H0**: Lab fitness under contaminant stress does not predict field abundance. Community composition at Oak Ridge is determined by factors other than metal tolerance (e.g., carbon source availability, pH, redox state).

## Literature Context

The ENIGMA (Ecosystems and Networks Integrated with Genes and Molecular Assemblies) project studies microbial communities at the Oak Ridge Field Research Center (FRC), contaminated with uranium, mercury, nitrate, and other metals from Cold War-era activities. Price et al. (2018) generated genome-wide fitness data for 48 bacteria including several genera found at Oak Ridge. This project tests the ecological relevance of lab fitness data by asking whether it predicts field community patterns.

## Data Model

```
sample (4,346) --> location (596)
  |
  |-->  community (2,209) --> brick459 (ASV x community x count)
  |                              |
  |                              --> brick454 (ASV -> taxon at genus level)
  |
  --> brick010 (sample x molecule -> concentration_micromolar)
```

108 samples have BOTH geochemistry AND community data.

## Query Strategy

### NB01: Spark Extraction

| Table | Rows | What to extract |
|-------|------|----------------|
| `ddt_brick0000010` | 52,884 | Geochemistry: pivot to sample x molecule matrix |
| `ddt_brick0000459` | 867,946 | ASV counts per community (37 communities) |
| `ddt_brick0000454` | 627,241 | ASV -> genus taxonomy |
| `sdt_community` | 2,209 | Community -> sample links |
| `sdt_sample` | 4,346 | Sample -> location + date |

All queries are small enough for REST API or Spark Connect (.toPandas() safe).

### NB02-03: Local Analysis

Uses cached FB data from upstream projects plus extracted ENIGMA data from NB01.

## Analysis Plan

### NB01: Extract ENIGMA Data
Extract geochemistry, community abundance, ASV taxonomy, and sample metadata. Filter to 108 overlapping samples. Save as TSVs.

### NB02: Genus Abundance Matrix
Aggregate ASV counts to genus level. Compute relative abundance. Identify FB genera at Oak Ridge. Build genus x sample matrix.

### NB03: Lab Fitness vs Field Abundance
1. Per-genus correlation: genus abundance vs site uranium/metals
2. Metal tolerance score: lab fitness summary vs field abundance at contaminated sites
3. Community-level: high-uranium vs low-uranium site community comparison
4. Gene-level: metal tolerance genes in core vs accessory genome

## Known Pitfalls

- ASV taxonomy is 16S-based and resolves to genus level only -- species-level matching to FB organisms is not possible
- Community composition data uses different ASV sets across brick tables (459 vs 462 vs 479) -- use only one consistently
- Geochemistry is point-in-time measurements; community composition may reflect historical conditions
- FB organisms are lab strains, not environmental isolates -- genus-level matching assumes shared metal tolerance
- Prefer Spark Connect over REST API for data extraction (docs/pitfalls.md)
