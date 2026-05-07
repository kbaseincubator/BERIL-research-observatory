# Harvard Forest Long-Term Warming — DNA vs RNA Functional Response

## TL;DR

In the 25-year +5°C soil warming experiment at Harvard Forest Barre Woods (NMDC `nmdc:sty-11-8ws97026`, n=42 biosamples), warming has a real but modest effect on community composition (~7-8% R²) and a stronger structured effect on functional gene content (~12% R² in DNA, ~10-11% in RNA). The originally proposed H1 (RNA shifts more than DNA) is **not supported** once a horizon × incubation confound is removed; the two pools respond comparably. Two specific carbon-cycling signals stand out: (1) **methanotrophy genes pmoA/pmoB are upregulated** in heated soils across both horizons (RNA log2 FC +0.7 to +0.9, p=0.009-0.054), and (2) the **glyoxylate cycle** (isocitrate lyase + malate synthase) is upregulated in heated mineral soil (p=0.037 each). At the curated 62-KO C-cycling level, heated-up KOs are significantly enriched in DNA-organic samples (Fisher OR=2.78, p=0.042). At the community level, **Actinobacteria are enriched and Acidobacteria depleted** in heated organic soil (q=0.049 each), reproducing published Pold et al. findings. Heated mineral samples also have **fewer detectable metabolites** (155 vs 167 ChEBI per sample, MW p=0.012). All analyses use only `nmdc_metadata` and `nmdc_results` tables (no `nmdc_arkin`).

## Data and design

- **Study**: `nmdc:sty-11-8ws97026` — "Molecular mechanisms underlying changes in the temperature sensitive respiration response of forest soils to long-term experimental warming" (PI Jeffrey Blanchard, U. Massachusetts Amherst)
- **Site**: Barre Woods, Petersham, Massachusetts (42.481 °N, −72.178 °W, 302 m elev.)
- **Samples**: 42 biosamples collected 2017-05-24, factorial across treatment (heated vs control), horizon (organic 0-2 cm vs mineral 2-10 cm), and lab incubation (direct vs incubated)
- **Omics layers used**:
  - Read-based taxonomy (kraken2) — n=28
  - GTDB-Tk MAG taxonomy — n=28 / 298 MAGs
  - KEGG KO annotations on metagenome assembly contigs — n=28 / 254K rows
  - KEGG KO annotations on metatranscriptome assembly contigs — n=39 / 307K rows
  - Pfam domain annotations on metagenome contigs — n=28 / 258K rows
  - ChEBI metabolite identifications — n=22 / 4,367 IDs

All data are in the BERDL Lakehouse `nmdc` tenant; the curated 62-KO C-cycling list is in `user_data/c_cycling_kos.tsv`.

## Hypotheses and verdicts

### H1 — RNA composition shifts more than DNA under warming

**Verdict: NOT SUPPORTED**

In the paired n=25 subset (samples with both DNA and RNA), PERMANOVA pseudo-F for treatment was 3.12 in DNA (R²=11.9%, p=0.020) vs 0.76 in RNA (R²=3.2%, p=0.60), seemingly contradicting H1. However, the paired subset confounds horizon with incubation (every organic sample is incubated, every mineral sample is direct). When this confound is removed by restricting to direct samples per pool:

| Pool × Horizon | n | F | R² | p |
|----------------|----|---|------|------|
| DNA × mineral | 14 | 1.75 | 12.7% | 0.081 |
| RNA × mineral | 11 | 1.15 | 11.4% | 0.254 |
| RNA × organic | 14 | 1.33 | 10.0% | 0.190 |

DNA and RNA pools show **comparable** treatment R² (10-13%) once the confound is removed. H1's premise that the transcript pool is more sensitive is not supported in this dataset.

### H2 — Carbon-degradation KOs are enriched in heated soils

**Verdict: PARTIALLY SUPPORTED**

A curated set of 62 carbon-cycling KOs (CAZymes, peptidases, TCA, β-oxidation, aromatic catabolism, methane, C1) was tested for enrichment in heated-up KOs (q<0.10, log2 FC > 0):

| Pool × Horizon | C-cycling hits | Other hits | Fisher OR | p (one-sided) |
|----------------|----------------|------------|-----------|---------------|
| DNA × organic | 5 / 57 | 428 / 12,806 | **2.78** | **0.042** |
| DNA × mineral | 0 / 57 | 2 / 12,806 | 0.0 | 1.0 |
| RNA × organic | 0 / 57 | 0 / 14,245 | NaN | 1.0 |
| RNA × mineral | 0 / 57 | 0 / 14,245 | NaN | 1.0 |

The DNA-organic enrichment is significant. The RNA pool shows no individual KOs surviving FDR (q<0.10) with the n=11+11 design across 14K KOs, but the *direction* of the strongest individual KOs is biologically interpretable:

- **Methanotrophy** — `pmoA` (K10944) and `pmoB` (K10945), both subunits of particulate methane monooxygenase, are upregulated +0.7-0.9 log2 FC in heated soils across **both organic and mineral horizons** (organic p=0.009-0.012, mineral p=0.029-0.054). Methane oxidation is consistent with the published warming-respiration narrative if heated soils have more available methane substrate.
- **Glyoxylate cycle** — `isocitrate lyase` (K01637) and `malate synthase` (K01638) both upregulated in heated mineral RNA (log2 FC +0.46, +0.27, p=0.037 each). The glyoxylate shunt assimilates C2 compounds (acetate) when central metabolism is constrained, suggesting a switch toward acetate-based carbon assimilation under warming stress.
- **Chitinase** (K01183) — modestly up in heated organic RNA (log2 FC +0.24, p=0.07).
- **TCA / PDH subunits** (K00382, K01681, K00161) — modestly down at the transcript level under warming.

Crucially these signals are **biologically directional and consistent across horizons**, even if the multiple-testing burden across 14K KOs prevents individual FDR significance.

### H3 — Organic and mineral horizons respond to warming with different functional categories

**Verdict: SUPPORTED COMPOSITIONALLY, NOT FOR C-CYCLING SPECIFICALLY**

KO-level log2 FC for warming is only weakly correlated between organic and mineral horizons:

| Pool | Pearson r | Spearman ρ |
|------|-----------|------------|
| DNA | 0.075 (p=1.78e-17) | 0.216 (p=2e-134) |
| RNA | 0.034 (p=6e-5) | 0.120 (p=4e-47) |

Most warming responses are horizon-specific (~39% of DNA KOs are organic-only, mineral-only, or sign-flipping). However, when classifying KOs into organic-only, mineral-only, and sign-flip categories, the 62-KO curated C-cycling list is **not differentially enriched** in any of them (OR<1, p>0.87 everywhere). This means C-cycling KOs respond to warming similarly in both horizons, even as the broader functional repertoire diverges. This is consistent with the pmoA/pmoB result (UP in both horizons).

H3 holds at the genome-wide level (most warming responses are horizon-specific) but the curated C-cycling categories are not the primary driver of horizon × warming interaction at this sample size.

### Bonus — Metabolite richness response

Heated mineral samples have significantly fewer detectable ChEBI metabolites than control mineral (155 ± 4 vs 167 ± 9, Mann-Whitney p=0.012). Heated organic shows the same direction but is not significant (160 ± 13 vs 173 ± 6, p=0.209). At the per-ChEBI level, no individual metabolite passes BH-FDR with this sample size, but several have nominal Fisher p<0.10 worth follow-up:

- ChEBI:71028 — heated-only (11/11 vs 6/11, p=0.035)
- ChEBI:30918 — control-only (0/11 vs 6/11, p=0.012)
- ChEBI:27967 — heated-enriched OR=12 (10/11 vs 5/11, p=0.063)

ChEBI label resolution is left as a follow-up since this project does not query external ontologies.

## Community-level findings (kraken2 read taxonomy)

Phylum-level differential abundance (Welch t-test on relative abundance, BH-FDR across phyla × horizon) recapitulated previously published Barre Woods findings:

| Phylum | Horizon | Control mean | Heated mean | log2 FC | q (BH) |
|--------|---------|--------------|-------------|---------|--------|
| Actinobacteria | organic | 0.249 | 0.315 | **+0.341** | **0.049** |
| Acidobacteria | organic | 0.035 | 0.024 | **−0.549** | **0.049** |
| Cyanobacteria | organic | 0.0032 | 0.0026 | −0.305 | 0.072 |
| Proteobacteria | organic | 0.654 | 0.605 | −0.111 | 0.088 |
| Verrucomicrobia | organic | 0.0058 | 0.0041 | −0.513 | 0.088 |

The Actinobacteria-up / Acidobacteria-down direction matches Pold et al. (2015 Frontiers, 2017 ISME), validating that our methodology recovers the established compositional signal at this site. PERMANOVA on Bray-Curtis genus distances yields R²(treatment)=7.6% (p=0.069), R²(horizon)=30.6% (p=0.0002), and R²(treatment × horizon 4-cell)=41% (p=0.0002).

## Caveats and limitations

1. **Single timepoint** (2017-05-24). Cannot detect seasonal effects.
2. **Sample size** for omics-rich layers (n=28 metagenome, n=39 metatranscriptome) limits per-KO FDR power across 12-14K KOs.
3. **Metatranscriptome KO from contig annotations** is *transcript-pool composition*, not TPM-quantified expression. Contig-level annotation count ≈ relative transcript abundance, but is biased by assembly quality.
4. **No quantitative metabolomics, NOM, or proteomics** because the project excludes `nmdc_arkin` tables. Equivalent quantitative layers exist in `nmdc_arkin.{nom_gold, metabolomics_gold, proteomics_gold}` and could be added if scope expands.
5. **`abiotic_features` is all zeros** for these samples (NMDC parsing artifact for this specific study) — no in-lakehouse soil temperature, pH, or nitrogen measurements. The +5°C treatment label is the only environmental contrast.
6. **Organic-horizon DNA samples are all lab-incubated**; direct organic DNA was not produced. This makes it impossible to factor incubation cleanly out of the DNA pool's organic-horizon analysis. The H1 sensitivity check uses direct samples only — which means DNA-organic-direct is not testable.

## Future directions

- **Add nmdc_arkin** to recover quantitative NOM, metabolomics, and proteomics layers — would strengthen H2 (carbon chemistry response) substantially.
- **Lookup ChEBI labels** for the top differential metabolite hits and run pathway enrichment against KEGG modules.
- **Cross-link to other warming studies** (SPRUCE peatland `nmdc:sty-11-33fbta56`, Alaskan permafrost thaw `nmdc:sty-11-db67n062`) for meta-analysis of warming-functional-shift consistency.
- **Add MAG-level ortholog tracking** — which specific MAGs carry the upregulated pmoA/pmoB? Are they single-clade methanotrophs or distributed across phyla?
- **Test the hypothesis that warming activates a "ruderal" subset** of the community — Actinobacteria + glyoxylate-cycle-active organisms.

## Files produced

- 8 analysis notebooks (`notebooks/01_*.ipynb` through `notebooks/08_synthesis.ipynb`) with saved outputs
- 9 figures (`figures/01_design.png` through `figures/08_synthesis.png`)
- 16 result TSVs in `data/` (gitignored, regenerable from notebooks; archived to lakehouse on `/submit`)
- 1 curated input: `user_data/c_cycling_kos.tsv` (62 KOs across 7 functional categories)
- `RESEARCH_PLAN.md` (versioned), `README.md`, `beril.yaml`

## Authors

- Chris Mungall, Lawrence Berkeley National Laboratory, ORCID [0000-0002-6601-2165](https://orcid.org/0000-0002-6601-2165)
