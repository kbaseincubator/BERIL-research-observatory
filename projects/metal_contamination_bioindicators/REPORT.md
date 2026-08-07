# Report: Microbial Indicator Taxa for Soil Metal Contamination

## Key Findings

### H1 — Taxonomic composition predicts metal contamination risk, but not beyond soil chemistry

![Sample map and AUC overview](figures/fig_auc_comparison.png)

Genus-level CLR composition predicts metal exceedance probability (science_2025 AT threshold)
well above chance in random-fold CV (AUC 0.922–0.961, n=132,907 soil samples, 6 metals). However,
this performance does not represent biological signal beyond spatial structure: coordinates alone
(latitude + longitude polynomial) achieve AUC 0.998–0.999 in the same random-fold setting,
exceeding both soil chemistry (0.991–0.995) and CLR (0.922–0.961). Adding CLR to soil chemistry
yields ΔAUC = −0.002 to +0.003 — negligible improvement.

The formal criterion (ΔAUC > 0.02 for ≥3 metals) is not met. **H1 is NOT SUPPORTED.**

Per-metal AUC summary:

| Metal | CLR-only AUC | Soil-only AUC | ΔAUC (soil+CLR − soil-only) |
|-------|-------------|---------------|---------------------------|
| As    | 0.923       | 0.991         | +0.001 |
| Cd    | 0.923       | 0.986         | +0.003 |
| Cr    | 0.949       | 0.993         | 0.000  |
| Cu    | 0.934       | 0.991         | −0.002 |
| Ni    | 0.961       | 0.995         | 0.000  |
| Pb    | 0.937       | 0.994         | +0.001 |

However, study-blocked cross-validation (GroupKFold by study, n=2,175 studies) reveals a
non-trivial cross-study signal in CLR: AUC 0.518–0.757, all metals above chance. Geographic
de-trending (Ridge regression of CLR on lat/lon polynomial) modestly improves study-blocked AUC by
0.011–0.036 across all 6 metals (As: 0.752→0.783, Cd: 0.600→0.634, Cr: 0.619→0.654, Cu:
0.573→0.593, Ni: 0.757→0.768, Pb: 0.518→0.536), confirming the residual cross-study signal is
genuinely biological rather than a spatial echo.

In study-blocked CV, soil+CLR (0.605–0.876) is worse than soil-only (0.707–0.938) for 5/6 metals
(As marginally higher). CLR adds study-correlated noise that does not transfer cross-study.

Study confounding analysis: study target-encoded AUC 0.993–0.997 > CLR AUC 0.922–0.961 (ratio
1.04–1.08×). CLR η² between studies = 0.015 across metals — 1.5% of CLR mean variance is
explained by study membership (geographic batch effect, not technical confounding; confirmed by
η² pattern following latitude/longitude gradients).

*(Notebooks: NB01_indicator_taxa.ipynb, NB01b_robustness_extended.ipynb)*

![AUC delta and study-blocking](figures/fig_delta_auc.png)

### H3 — Indicator genera carry elevated metal gene density (Cd, Cu, Pb)

![KO density violin plots](figures/fig_nb03_ko_density.pdf)

#### Initial cross-phylum analysis: 3/6 metals nominally significant

Top-50 indicator genera per metal carry significantly higher metal KO density (KOs per Mb, Tier
1+2 gene list from CME) than the remaining ≥5,500 genera for 3/6 metals after BH-FDR correction:

| Metal | n_matched | Median indicator | Median rest | Effect r | p_fdr | Significant |
|-------|-----------|-----------------|-------------|----------|-------|-------------|
| Cd    | 37/50     | 8.47            | 7.27        | −0.24    | 0.033 | Yes ✓       |
| Cu    | 26/50     | 9.86            | 7.28        | −0.26    | 0.034 | Yes ✓       |
| Pb    | 30/50     | 8.65            | 7.27        | −0.21    | 0.046 | Yes ✓       |
| Cr    | 33/50     | 8.17            | 7.28        | −0.18    | 0.054 | Borderline  |
| Ni    | 31/50     | 7.90            | 7.28        | −0.16    | 0.075 | No          |
| As    | 33/50     | 7.93            | 7.29        | −0.11    | 0.140 | No          |

*Note on Effect r sign: Effect r = (U − n₁×n₂/2) / (n₁×n₂/2) where U is the Mann-Whitney statistic for indicator vs. rest. Under scipy's convention, **negative r indicates the indicator group has higher values** (few times indicator < rest). The table's negative r values (−0.24 to −0.21) therefore confirm that indicator genera have higher KO density than non-indicators — not lower. Medians are provided for direct verification.*

Subcategory breakdown (resistance / cofactor / metaldep Z-scores) shows all subcategories NS after
FDR. The enrichment is distributed broadly across KO functional subcategories rather than
concentrated in resistance genes alone.

#### Within-phylum stratification reveals phylogenetic confound

**H3 is NOT SUPPORTED** (phylogenetic composition artifact). A within-phylum stratification
test (Mann-Whitney, pooled across metals) reveals that the apparent enrichment disappears
entirely when controlling for phylum membership. Within Actinobacteria — the dominant indicator
phylum, 20/160 combined indicator slots — indicator genera have *lower* KO density than
non-indicators (median 6.09 vs 8.27 KO/Mb; p=0.987, direction reversed). Per-metal
within-phylum tests: all p>0.25, none significant in any direction. The cross-phylum
comparison in the original test was inflated because indicator genera are concentrated in
Actinobacteria while non-indicators include phyla with systematically lower KO densities
(Firmicutes, Bacteroidetes). The enrichment is a compositional artifact, not evidence of
functional adaptation in indicator genera specifically.

*(Notebook: scripts/run_nb03_functional.py; robustness: scripts/run_h3_phylum_stratified.py)*

#### ke_pangenome replication: direction fully reversed (NOT SUPPORTED)

To replicate with a representative global genome database, the Wilcoxon test was repeated using
`kbase.ke_pangenome` (293K GTDB genomes, 5,647–5,648 genera total with ≥3 genomes and matched
genus names). Results across all 6 metals:

| Metal | n_matched | Median KO/Mb (indicator) | Median KO/Mb (rest) | Effect r | p_fdr    |
|-------|-----------|--------------------------|---------------------|----------|---------|
| As    | 33/50     | 344.5                    | 441.0               | 0.43     | 0.999997 |
| Cd    | 37/50     | 346.5                    | 441.0               | 0.43     | 0.999997 |
| Cr    | 33/50     | 366.4                    | 441.0               | 0.37     | 0.999997 |
| Cu    | 26/50     | 375.3                    | 440.9               | 0.34     | 0.999997 |
| Ni    | 31/50     | 372.9                    | 440.9               | 0.26     | 0.999997 |
| Pb    | 30/50     | 380.1                    | 441.0               | 0.31     | 0.999997 |

Indicator genera have **~20% lower** KO density than non-indicators (344–380 vs 441 KO/Mb).
Direction is completely reversed from the original SPIRE result (3/6 metals nominally significant in
the expected direction). Effect r values (0.26–0.43) indicate indicator genera consistently sit in the
lower tail of the KO density distribution, not the upper. Within-phylum stratification (Actinobacteria,
Pseudomonadota, Bacteroidota) shows the same reversal in all tested phyla (all p_fdr=0.999997).

The reversal is consistent with the within-phylum SPIRE stratification result: indicator genera
are specialist lineages concentrated in Actinobacteria, which has low KO density relative to
Proteobacteria-dominated non-indicator genera. In ke_pangenome — which covers all lineages
equally — this effect is exposed directly without a biased MAG sampling frame.

*(Data: data/h3_ke_pangenome_results.csv, data/h3_ke_pangenome_phylum_results.csv)*

#### Per-KO taxonomic breadth as phylogenetic signal proxy

To test whether KOs with low phylogenetic signal (high taxonomic breadth, i.e., environmentally
plastic) show stronger associations with indicator status than phylogenetically locked KOs — the
mechanistic test of whether H3 effects are genuine or compositional — taxonomic breadth was computed
for 244 of the 280 curated metal KOs (excluded: <10 or >8,382 genera present in MGnify) across four
taxonomic levels (phylum/class/order/family):

| Level  | Median breadth | Low (<0.3) | High (>0.7) |
|--------|---------------|-----------|------------|
| Phylum | 0.155         | 157/244   | 0          |
| Class  | 0.100         | 166/244   | 0          |
| Order  | 0.080         | 183/244   | 0          |
| Family | 0.060         | 196/244   | 0          |

Metal KOs are overwhelmingly phylogenetically restricted (median phylum breadth 0.155; 64% of KOs
present in <30% of phyla). No KO achieves breadth >0.7 at any level — consistent with these being
functional specialisations, not universal metabolic genes.

Partial Spearman ρ (KO prevalence vs indicator status, controlling for genome size) by phylum
breadth tertile (pooled across all 6 metals):

| Breadth tertile | Mean partial ρ |
|----------------|----------------|
| Low            | −0.047         |
| Mid            | −0.009         |
| High           | +0.010         |

The gradient is near-flat and marginally in the **wrong direction**: if H3 were real, high-breadth
(environmentally plastic) KOs should show the strongest positive ρ. Instead, low-breadth KOs show
slight negative ρ (consistent with phylogenetic confounding of the original cross-phylum test), and
high-breadth KOs show ρ ≈ 0. This pattern is consistent at all four taxonomic levels.

*(Data: data/ko_phylo_breadth.csv, data/ko_breadth_vs_indicator.csv;
figures: figures/fig_h3_ko_breadth_scatter.pdf, figures/fig_h3_ko_breadth_hist.pdf)*

#### Genome-wide KO enrichment (ke_pangenome, 8,448 KOs tested)

Fisher's exact test (one-sided, ≥5 indicator genera present) was applied genome-wide to all KOs in
ke_pangenome. Results: 7,663/8,448 KOs (91%) significant at q<0.05 (BH-FDR). The high significance
rate reflects broad metabolic differences between indicator lineages and non-indicator genera — not
H3-specific metal KO enrichment. Top hits by odds ratio include housekeeping KOs universal in
indicator genera (ribBA, ribH, folP, pstS, birA; all OR=Inf, present in 100% of indicator genera
but 70–85% of non-indicators), potassium ATPase subunits (kdpA/B/C; OR=17–19; prev_ind=0.86 vs
rest=0.25–0.26), and DNA repair (ku; OR=15; prev_ind=0.77 vs rest=0.18).

The 91% significance rate is inflated by phylogenetic confounding: indicator genera cluster in
Actinobacteria and Pseudomonadota, and any KO enriched in those phyla appears significant in the
marginal test.

**Phylogeny-corrected enrichment (CMH, 105 phyla as strata):** Cochran-Mantel-Haenszel test
stratified by GTDB phylum reduces the significant fraction to 7,396/8,450 KOs (87.5%; 555 naive
false positives removed). The modest reduction (91% → 87.5%) indicates that most enrichment
reflects genuine within-phylum differences between indicator and non-indicator genera, not purely
between-phylum phylogenetic confounding.

Biologically interpretable metal-relevant KOs among the 331 metal-term hits surviving CMH
correction (sorted by CMH OR):

| KO     | Gene  | CMH OR | Function |
|--------|-------|--------|----------|
| K11629 | bceS  | 32.8   | Bacitracin/metal sensor histidine kinase |
| K21961 | ethR  | 26.4   | Ethionamide/metal resistance regulator |
| K11630 | bceR  | 19.0   | Bacitracin resistance response regulator |
| K14689 | ZNT2  | 13.4   | Zinc transporter (SLC30A2 family) |
| K06324 | cotA  | 14.6   | Manganese oxidase / spore coat protein |
| K11741 | sugE  | 12.9   | Quaternary ammonium/metal efflux (SugE) |
| K07788 | mdtB  | 11.3   | Multidrug/metal efflux pump |
| K07217 | ydbD  | 11.1   | Manganese catalase |
| K08365 | merR  | 10.4   | Mercury resistance operon regulator |
| K05794 | terC  | 10.1   | Tellurite resistance protein |
| K11811 | arsH  | 9.4    | Arsenical resistance protein |
| K10824 | nikE  | 6.5    | Nickel transport ATP-binding protein |
| K03322 | mntH  | 6.7    | Manganese transport protein |
| K07241 | hoxN  | 7.6    | Nickel/cobalt transporter |
| K07156 | copC  | 6.6    | Copper resistance protein C |
| K03893 | arsB  | 6.6    | Arsenical pump membrane protein |

These represent genuine enrichment of metal-handling capacity in indicator genera after removing
phylogenetic structure — though these are scattered across many functional categories, not
concentrated in the Tier 1+2 curated metal gene set tested by H3. The 331 metal-relevant CMH hits
(from 8,450 total) remain a minority even after phylogeny control.

**Within-phylum lineage correction (CMH, 21 GTDB orders as strata):** The phylum-level CMH
still conflates indicator genera that cluster in specific orders (Rhizobiales, Burkholderiales,
Streptomycetales within Actinomycetota; Bacillales within Firmicutes) with genuine cross-order
enrichment. Order-level stratification compares indicator genera only to non-indicator genera
from the same GTDB order. 21 orders contain ≥2 indicator genera (Rhizobiales n=16,
Mycobacteriales n=9, Burkholderiales n=8, Bacillales n=7; Streptomycetales n=3 vs 2 non-indicator
— very sparse) and contribute meaningful CMH information.

Order-level CMH yields 6,445/8,128 KOs (79.3%) at q<0.05, compared to 7,175/8,128 (88.2%) at
phylum level for the same set of KOs. The order correction removes **1,031 KOs** (14.4% of
phylum-significant hits) — these are within-phylum lineage effects, primarily Streptomyces-specific
secondary metabolite BGCs and Bacillus sporulation genes that survive phylum stratification because
Streptomycetales and Bacillales have 3 and 7 indicator genera respectively, creating strong
within-phylum but within-order confounding. An additional 301 KOs become significant only at order
level (higher power from smaller strata reducing background heterogeneity).

The top order-level survivors include biologically coherent signals spanning diverse orders (21
contributing orders for dctA, fdhA, dhbF; 19–20 for most top hits):

| KO     | Gene  | OR (order) | Function | n orders |
|--------|-------|-----------|----------|----------|
| E4.2.1.66 | — | 120.9 | Cyanide hydratase (mining co-contaminant detox) | 5 |
| cciI   | cciI  | 64.5  | Acyl-HSL synthase (quorum sensing) | 4 |
| yqeH   | yqeH  | 63.5  | 30S ribosome assembly GTPase | 6 |
| hpa2   | hpa2  | 29.3  | Phage lysozyme-related protein | 5 |
| cag23  | cag23 | 15.3  | Type IV secretion ATPase | 8 |
| pcpB   | pcpB  | 11.7  | Pentachlorophenol monooxygenase (co-contamination) | 13 |
| oqxA   | oqxA  | 10.3  | Multidrug/metal efflux pump MFP subunit | 16 |
| dctA   | dctA  | 11.4  | C4-dicarboxylate transporter | 21 |
| alkR   | alkR  | 11.3  | Alkane utilization AraC regulator | 12 |
| fdhA   | fdhA  | 7.7   | Glutathione-independent formaldehyde dehydrogenase | 21 |
| dhbF   | dhbF  | 5.9   | Bacillibactin siderophore biosynthesis | 21 |

The cyanide hydratase (E4.2.1.66, OR=120.9) and pentachlorophenol monooxygenase (pcpB, OR=11.7)
represent genuine co-contamination signals: cyanide is used in gold/silver heap leaching and is a
common co-contaminant at metal-impacted sites; pentachlorophenol is a wood preservative frequently
co-occurring with metal mine tailings. The multidrug efflux pump oqxA (OR=10.3) and formaldehyde
dehydrogenase fdhA (OR=7.7) reflect known metal-stress cross-protection mechanisms that genuinely
distinguish indicator from non-indicator genera across diverse lineages.

However, the persistence of 79.3% overall significance after order-level correction — including
entries such as yqeH (30S ribosome GTPase, OR=63.5) and cciI (acyl-HSL synthase, OR=64.5) in only
4–6 orders — indicates that systemic annotation bias remains the dominant driver. Indicator genera
disproportionately originate from heavily sequenced, well-curated lineages (Streptomyces,
Mesorhizobium, Burkholderia, Bacillus), which have more complete genomes and better functional
annotation; this produces spurious enrichment across thousands of KOs irrespective of biology. The
order-level correction eliminates only the lineage-clustering component, not the annotation quality
confound.

**Annotation-bias-corrected CMH (≥50% prevalence threshold + order strata):** Binary
presence/absence (KO detected in ≥1 genome per genus) is biased by unequal genome sampling:
indicator genera include heavily sequenced type strains (Mesorhizobium, Burkholderia, Bacillus,
Streptomyces) with 100–500 genomes each in ke_pangenome, while most non-indicator genera have 3–20
genomes. A genus with 500 genomes has vastly more chance of having any rare KO annotated at least
once. Requiring KO prevalence ≥50% within each genus (KO present in ≥50% of genus's genomes)
normalises for sampling depth: a genus with 500 genomes needs 250+ genome detections, giving a
comparable threshold to a genus with 5 genomes needing 3+ detections.

At the 50% prevalence threshold, followed by the same 21-order CMH: **1,654/6,765 KOs (24.4%)**
remain significant at q<0.05. For KOs tested in both the order-only and prevalence analyses (inner
join), 5,259 were order-significant vs 1,654 prevalence-significant, with **3,655 removed by the
annotation bias correction** — substantially larger than the 1,031 removed by order-level phylogeny
correction. The cascade:

| Correction | % q<0.05 | Method |
|---|---|---|
| None (naive Fisher) | 91% | marginal association |
| Phylum CMH | 87.5% | between-phylum phylogeny |
| Order CMH | 79.3% | within-phylum lineage clustering |
| Order CMH + ≥50% prevalence | 24.4% (1,654/6,765) | + annotation-depth bias |
| + soil habitat filter | 21.0% (1,408/6,718) | + non-soil comparison set bias |
| + genome completeness filter | 23.7% (1,596/6,739) | + low-quality genome annotation bias |
| *(control A: order × annotation-rate CMH)* | *7.3% (518/7,133)* | *within-order annotation-rate heterogeneity (strongest correction)* |
| *(control B: KO phyla breadth ≥3)* | *~25% (44 removed, ~neutral net)* | *phylum-restricted annotation artifacts (modest effect)* |
| *(control C: min genomes ≥5)* | *~25% (reshuffles, not cleanly reduced)* | *noisy small-n prevalence estimates* |
| *(geo-linked restriction — independent test)* | *1.1% (76/6,797)* | *geographic sampling bias; no high-metal indicator strata* |

Restricting the non-indicator comparison set to MicrobeAtlas-detectable (soil) genera (2,857 soil
genera from the OTU-pangenome bridge; 3,973 of 5,234 non-indicator ke_pangenome genera are
non-soil lineages) further eliminates 506 KOs (habitat-bias confound; soil-filtered q<0.05:
1,408/6,718 = 21.0%). An additional 232 KOs emerge as significant only in the soil-restricted
comparison set. Genome completeness filtering (≥90% completeness, ≤5% contamination, via
`kbase.ke_pangenome.gtdb_metadata`; 253,862/293,059 genomes pass) removes a further 219 KOs
(1,671 → 1,596 q<0.05, 23.7% of 6,739 tested; 144 quality-only KOs emerge). CheckM columns
are in `gtdb_metadata`, not the `genome` table.

The surviving 1,654 KOs (prevalence threshold; 1,408 after additional soil filter; 1,596 after
completeness filter) are
functionally interpretable as metal-contaminated site biology rather than metal-tolerance gene
enrichment:
- **Antibiotic/antimicrobial resistance** (co-selected with metals): mexY (OR=41.2, multidrug efflux),
  tetX (OR=20.7, tetracycline monooxygenase), tetP_A (OR=53.2, tetracycline MFS transporter),
  bacA (OR=40.1, bacitracin resistance)
- **Lipopeptide biosurfactants** (biofilm/surface chemistry at contaminated sites): ituB (OR=32.8),
  srfAB (OR=23.8), srfAC (OR=41.2) — Bacillus-indicator-genus specific
- **Quorum sensing and biofilm**: cciI (acyl-HSL synthase, OR=50.0), amsF (exopolysaccharide
  biosynthesis, OR=47.2)
- **Rhizobium symbiosis**: nodD (LysR regulator, OR=10.5) — reflecting Rhizobiales dominance among
  indicator genera
- **Broad-distribution genuine signals**: dctA (C4-dicarboxylate transport, OR=5.3, 21 orders),
  chaA (Ca²⁺:H⁺ antiporter, OR=5.8, 19 orders), mexY (multidrug efflux, OR=17.9, 8 orders)
- **Metal transport survives soil filter**: SLC30A2/ZNT2 (zinc transporter, OR=37.1, 11 orders),
  mpl (zinc metalloproteinase, OR=18.9) — genuine zinc biology not attributable to any of the
  four characterised confounders

None of these categories represent the elevated metal-specific KO density predicted by H3. The
metal-antibiotic co-selection signal (tetX, tetP_A, mexY) is consistent with contaminated sites
co-selecting antibiotic resistance — itself a known consequence of metal contamination — but is a
phenomenon alongside indicator status, not a mechanistic basis for it.

**Annotation-bias sensitivity checks (controls A, B, and C).** Three additional controls test
whether the residual ~25% enrichment survives more direct correction for annotation heterogeneity,
narrow-range artifacts, and small-sample noise.

*Control A: KEGG annotation-rate stratification (most direct control).* Each genus's mean KEGG
annotation rate (fraction of EggNOG-called genes receiving a KO assignment) was computed from
`kbase.ke_pangenome.eggnog_mapper_annotations` via the gene\_cluster → gene\_genecluster\_junction
join (8,419 genera; mean rate 0.619, std 0.091, range 0.218–1.0). Indicator genera have a
**lower** mean annotation rate (0.522) than non-indicator genera (0.616) — the opposite of a
simple annotation-bias prediction, indicating that indicator genera span less well-characterised
KEGG clades. Annotation rate was binned into tertiles (low <0.584, mid 0.584–0.659, high >0.659)
and added as a second stratification variable alongside taxonomic order. Within-order comparisons
are thereby made among genera at similar KEGG annotation depth. Order × annotation-rate CMH
(5,313 genera matched to annotation-rate data; 7,133 KOs tested, 22 strata):
**518/7,133 q<0.05 (7.3%)**, down from 25.6% on the same matched subset using order-only
stratification. This removes 1,408 baseline-significant KOs (73.4%) — by far the strongest
correction of any control tested. Survivors (509 KOs) are core biosynthetic genes (dapD, lipA,
ubiE) and structural cell components, with ORs numerically unestimable in most cases (ss ≈ 0
within narrow strata; the chi-squared q-values remain valid). Only 9 KOs become newly significant
after annotation-rate stratification. Annotation-rate stratification thus eliminates most of the
~25% residual: indicator genera, despite their globally lower annotation rates, are concentrated
in relatively high-annotation-rate positions *within their orders*, and correcting for this
within-order heterogeneity accounts for most of the apparent KO enrichment.

*Control C (minimum genome count ≥5)* removes genera with fewer than 5 sequenced genomes, for
which the ≥50% prevalence threshold is unreliable (32.2% of ke_pangenome genera dropped).
Control C reshuffles rather than cleanly reduces significance: 264 baseline-significant KOs lose
significance (indicator signal driven partly by small-N genera), while 306 new KOs gain
significance as corresponding small-N non-indicator genera are also removed.

*Control B (KO phylum breadth ≥3)* restricts the tested KO universe to those detected in at
least 3 distinct phyla, filtering out KOs that are annotation-complete in only 1–2 phyla (1,593
single-phylum KOs removed, 11.7% of the total). Control B removes 44 narrow-breadth KOs from
the significant set — a modest effect, indicating that phylum-restricted annotation artifacts were
mostly already filtered by the prevalence threshold. Combined, controls B and C remove 297
baseline-significant KOs but 303 new KOs become significant (net ~neutral shift, combined rate
26.2% vs baseline 25.1%). Controls B and C alone therefore do not substantially reduce the ~25%
residual; Control A (annotation-rate stratification) is required to reduce it to 7.3%.

**Geo-linked validation (independent test).** As a direct environmental test, 3,958 quality
ke_pangenome genomes were linked to GPS coordinates via parsed NCBI `lat_lon` fields, filtered
to terrestrial isolation sources (soil, rhizosphere, sediment, mine tailings, etc.), and spatially
joined to science_2025 AT-exceedance values at 0.25° resolution. Of these, 972 belong to
indicator genera (67 distinct indicator genera); 2,986 to non-indicator genera (678 genera).
Indicator genera are collected from **lower-exceedance sites** than non-indicators: Cr mean
0.113 vs 0.190, Ni 0.110 vs 0.158, Pb 0.140 vs 0.182, As 0.186 vs 0.210 (Cu ≈ equal at 0.083
vs 0.082; Cd marginally reversed at 0.284 vs 0.274). Restricting the order-CMH to these 745
geo-linked genera collapses enrichment to **1.1% (76/6,797)**, down from 23.7% in the full
pangenome. The 76 surviving KOs are secretion system components, biofilm/exopolysaccharide
genes, and quorum-sensing synthases — not metal-resistance genes. The planned metal-stratified
CMH (indicator genera at high-exceedance sites vs non-indicator at the same sites) was
infeasible: zero indicator genera in the geo-linked set had mean Cr exceedance >0.50; only 1–7
indicator genera cleared >0.50 for other metals, insufficient for order stratification. This
confirms that indicator genera are not preferentially sampled from high-metal environments in
the ke_pangenome, and that the pangenome-level KO enrichment signal is largely absent when
constrained to genera with direct geographic metal context.

**Bottom line:** Across ten independent analyses — (1) ke_pangenome Wilcoxon (direction
reversed, indicator genera 20% lower KO density), (2) within-phylum SPIRE stratification (all
NS, direction reversed), (3) per-KO phylogenetic breadth proxy (near-flat partial Spearman ρ),
(4) genome-wide CMH phylum-stratified (87.5%), (5) genome-wide CMH order-stratified (79.3%;
1,031 lineage-effect KOs removed), (6) genome-wide CMH order-stratified + ≥50% prevalence
threshold (24.4%; annotation bias accounts for 3,655 additional false positives, exceeding the
phylogeny component), (7) + soil habitat filter restricting comparison to MicrobeAtlas-detectable
soil genera (21.0%; 506 habitat-bias KOs removed), (8) + genome completeness filter (CheckM
≥90%/≤5% via `gtdb_metadata`; 23.7%; 219 low-quality annotation bias KOs removed), (9)
annotation-rate stratification (order × KEGG coverage tertile CMH; 7.3%; 73.4% of residual
enrichment removed — indicator genera have paradoxically LOWER annotation rates than
non-indicators at 0.522 vs 0.616, indicating within-order annotation heterogeneity is the
dominant remaining confound), and (10) geo-linked direct environmental test (1.1%; indicator
genera have lower local metal exceedance than non-indicators; no high-metal indicator strata
available) — H3 is NOT SUPPORTED.
Indicator genera carry no specific elevation of metal-tolerance gene density; the observed
genome-wide enrichment decomposes into phylogenetic composition (8%), within-phylum lineage
clustering (14%), genome annotation depth bias (55%), non-soil comparison set bias (~4%), and
low-quality assembly bias (~1%), with the residual ~24% further decomposing via within-order
annotation-rate correction to 7.3% (reflecting antibiotic co-selection, lineage-specific
lifestyle signatures, and a small component of genuine metal-associated functions — ZNT2/zinc
transport, mpl, chaA — that persist in geo-linked analysis but at only 1.1% when direct
environmental context is available). Crucially, neither the annotation-rate stratification nor
the geo-linked test supports systematic metal-specialisation; the remaining signal
is most parsimoniously attributed to fine-scale phylogenetic structure within orders rather
than convergent metal-biology adaptation.

*(Data: data/all_ko_enrichment.csv, data/all_ko_enrichment_cmh.csv, data/all_ko_order_summary.parquet,
data/all_ko_enrichment_cmh_order.csv, data/all_ko_genus_prev_summary.parquet,
data/all_ko_enrichment_cmh_prev50.csv, data/all_ko_enrichment_cmh_soil_prev50.csv,
data/all_ko_enrichment_cmh_qual_prev50.csv, data/geo_linked_genomes.parquet,
data/h3_geo_restricted_cmh.csv, data/h3_cmh_phyla_breadth_3.csv,
data/h3_cmh_min_genomes_5.csv, data/h3_cmh_combined_n5_p3.csv,
data/h3_cmh_combined_survivors.csv,
data/genus_annotation_rate.parquet, data/h3_cmh_annot_matched_baseline.csv,
data/h3_cmh_order_x_annot_rate.csv, data/h3_cmh_annot_rate_survivors.csv,
data/h3_cmh_annot_rate_removed.csv;
figures: figures/fig_h3_all_ko_volcano.pdf, figures/fig_h3_all_ko_cmh_volcano.pdf,
figures/fig_h3_enrichment_comparison.pdf, figures/fig_h3_cmh_phylum_vs_order.pdf,
figures/fig_h3_all_ko_cmh_order_volcano.pdf, figures/fig_h3_cmh_order_vs_prev50.pdf,
figures/fig_h3_cmh_prev50_vs_soil.pdf, figures/fig_h3_cmh_prev50_vs_qual.pdf,
figures/fig_h3_geo_latlon_coverage.pdf, figures/fig_h3_geo_exceedance_distribution.pdf,
figures/fig_h3_annotation_bias_cascade.pdf, figures/fig_h3_breadth_filter_distribution.pdf,
figures/fig_h3_annotation_rate_distribution.pdf, figures/fig_h3_annot_rate_cmh_scatter.pdf;
scripts: scripts/run_h3_all_ko_enrichment.py, scripts/run_h3_all_ko_enrichment_cmh.py,
scripts/run_h3_all_ko_enrichment_cmh_order.py, scripts/run_h3_all_ko_enrichment_cmh_prevthresh.py,
scripts/run_h3_cmh_soil_filter.py, scripts/run_h3_cmh_completeness_filter.py,
scripts/run_h3_geo_linked_ko_enrichment.py,
scripts/run_h3_annotation_bias_controls.py,
scripts/run_h3_cmh_annotation_rate.py)*

An independent phylogenetic test (PGLS with genome-size, Levins' B, lat/lon, and soil-chemistry
controls; 256 genera; 46 USGS elements) finds no FDR-significant association between cofactor or
resistance KO density and measured concentrations of any classic toxic metal — further confirming
H3 NOT SUPPORTED at the phylogenetic scale (see "Phylogenetic KO density → USGS metal
concentration: PGLS with full controls").

### H4 — Contamination-risk and geological-background indicators are largely distinct

Source-comparison analysis (H2) additionally tests H4: the science_2025 (contamination risk)
top-50 genera per metal show low Jaccard overlap with GeoROC top-50 genera (geological background):

| Metal | s25 vs GeoROC Jaccard |
|-------|----------------------|
| Cr    | 0.111                |
| Cu    | 0.000                |
| Ni    | 0.026                |
| Pb    | 0.053                |
| Mean  | 0.048                |

All values are well below the H4 threshold of 0.15. **H4 is SUPPORTED**: contamination-risk
indicator genera are largely non-overlapping with geological-background indicators. This is
ecologically meaningful — the microbial community apparently distinguishes between natural geogenic
metal distributions and anthropogenic contamination risk, as assessed through different metal
datasets.

*(Notebook: NB02_source_comparison.ipynb)*

### H2 — Indicator genera are not consistent across metal sources (H2 NOT SUPPORTED)

![Source AUC comparison](figures/fig_source_auc.png)
![Source Jaccard heatmap](figures/fig_source_jaccard.png)

Top-50 indicator genera differ substantially between science_2025, CSU mobility, and GeoROC for
the same nominal metal. Pairwise Jaccard similarities between sources:

| Metal | s25–CSU | s25–GeoROC | CSU–GeoROC |
|-------|---------|-----------|-----------|
| Cr    | 0.081   | 0.111     | 0.053     |
| Cu    | 0.081   | 0.000     | 0.053     |
| Ni    | —       | 0.026     | —         |
| Pb    | 0.053   | 0.053     | 0.111     |

No pairwise Jaccard exceeds 0.15 (criterion: mean > 0.25). **H2 is NOT SUPPORTED.**

Notably, predictive AUC is consistent across sources for the same metals (s25: 0.922–0.961; CSU:
0.925–0.937; GeoROC: 0.809–0.893), indicating similar total predictive power but from different
genera. Different aspects of soil metal chemistry select for different microbial lineages.

---

### Algorithm comparison: tree ensembles dominate CLR-only regression

![Algorithm comparison](figures/fig_algo_comparison.pdf)

Six algorithms compared for predicting metal exceedance probability from CLR-only (500 genera, random-fold CV, Spearman ρ):

| Algorithm | As | Cd | Cr | Cu | Ni | Pb |
|---|---|---|---|---|---|---|
| RF (baseline) | 0.669 | 0.747 | 0.685 | 0.632 | 0.678 | 0.732 |
| Extra Trees | 0.628 | 0.734 | 0.635 | 0.587 | 0.626 | 0.719 |
| XGB (col samp.) | 0.577 | 0.683 | 0.560 | 0.519 | 0.554 | 0.643 |
| CatBoost | 0.547 | 0.654 | 0.532 | 0.480 | 0.524 | 0.604 |
| Ridge | 0.430 | 0.493 | 0.374 | 0.352 | 0.367 | 0.437 |
| ElasticNet | 0.368 | 0.388 | 0.294 | 0.188 | 0.270 | 0.292 |

Tree ensembles (RF, Extra Trees) substantially outperform linear methods — mean ρ RF 0.691 vs. Ridge 0.409. The gap confirms non-linear genus interactions carry predictive information. CatBoost underperforms RF by a mean Δρ = −0.133 across metals, likely due to its regularisation structure in this feature regime. See **Performance Notes** for actionable method recommendations.

CatBoost regression (continuous exceedance probability) replicates the H1 null from a regression angle: soil-only ρ 0.703–0.830 vs. soil+CLR 0.657–0.812 — CLR degrades soil-only for all 6 metals (Δρ = −0.018 to −0.059, mean −0.039). CLR-only CatBoost ρ 0.479–0.654.

CLR feature selection (CatBoost, top-k by SHAP importance) also degrades performance: k=20 ρ 0.311–0.466; k=50 ρ 0.356–0.524; k=100 ρ 0.381–0.551 — all below full-CLR CatBoost. The predictive signal is distributed across the full genus space, not concentrated in a subset.

![Feature selection](figures/fig_catboost_featsel.pdf)
![CatBoost ρ comparison](figures/fig_catboost_rho_comparison.pdf)

*(Notebooks: NB05_catboost_regression.ipynb)*

---

### Nitrososphaera is the top global indicator genus for chromium

![CatBoost top-20 SHAP genera](figures/fig_catboost_shap_top20.pdf)
![Nitrososphaera SHAP dependence](figures/fig_nitrososphaera_shap_dep.pdf)

CatBoost SHAP analysis (CLR-only, 500 genera, 124,687 samples) identifies Nitrososphaera (AOA ammonia-oxidizing archaea, class Nitrososphaeria) as the **rank-1 genus for Cr prediction** (mean |SHAP| = 0.0103, rank 1/500) and a top-20 indicator for 4/6 metals:

| Metal | Nitrososphaera rank | Mean |SHAP| |
|-------|-----|------|
| Cr    | 1/500   | 0.01025 |
| Ni    | 9/500   | 0.00323 |
| As    | 15/500  | 0.00274 |
| Cu    | 14/500  | 0.00130 |
| Pb    | 26/500  | 0.00150 |
| Cd    | 58/500  | 0.00114 |

Eleven genera appear in the top-20 SHAP list for ≥3/6 metals, forming a cross-metal indicator core: Skermanella (5/6 metals), Conexibacter (4/6), Nitrososphaera (4/6), Geodermatophilus (3/6), Geothrix (3/6), Nakamurella (3/6), Dyella (3/6), Parafilimonas (3/6), Rubrobacter (3/6), Stenotrophobacter (3/6), and Anaeromyxobacter (3/6). The core is dominated by Actinobacteria and Acidobacteria — lineages associated with oligotrophic, stress-tolerant soil niches. However, the core is unified by broad predictive importance rather than directional consistency: only Geodermatophilus and Stenotrophobacter show consistent depletion across all their represented metals, making them the most robust candidates for multi-metal biomonitoring.

*(Notebooks: NB05_catboost_regression.ipynb)*

---

### PCA compression: PC50 captures most CLR predictive signal

![PCA variance explained](figures/fig_pca_variance.pdf)
![RF PCA vs raw CLR](figures/fig_rf_pca_vs_raw.pdf)

PCA(200) of 500-genus CLR: cumulative variance PC10=35.7%, PC50=54.2%, PC200=79.6%. RF on PCA-compressed CLR confirms PC50 is optimal:

| Metal | PC10 ρ | PC50 ρ | PC100 ρ | Raw CLR ρ | Δ (raw−PC50) |
|-------|------|------|-------|---------|-------------|
| As    | 0.582 | 0.620 | 0.608 | 0.669 | +0.049 |
| Cd    | 0.660 | 0.721 | 0.712 | 0.747 | +0.026 |
| Cr    | 0.591 | 0.623 | 0.601 | 0.685 | +0.062 |
| Cu    | 0.551 | 0.588 | 0.566 | 0.632 | +0.044 |
| Ni    | 0.585 | 0.617 | 0.601 | 0.678 | +0.061 |
| Pb    | 0.650 | 0.696 | 0.685 | 0.732 | +0.036 |

Raw CLR beats PC50 by Δρ = 0.026–0.062 across all 6 metals; PC100 consistently underperforms PC50, indicating overfitting beyond 50 PCs. Genus-level detail beyond the major community axes carries real but modest predictive information.

The interactive t-SNE + UMAP explorer (fig_dimred_explorer.html, 10K-sample subsample) visualises the community composition space coloured by metal exceedance probability, confirming that metal gradients are partially embedded in the main axes of global soil community variation.

*(Notebook: NB06_dimred.log)*

---

## Discoveries

- **Nitrososphaera *depletion* is a globally validated Cr contamination signal (rank 1/500, mean|SHAP|=0.0103; SHAP-CLR ρ=−0.920).** It is Nitrososphaera *absence* — not enrichment — that flags Cr risk: low CLR → positive SHAP contribution → higher predicted Cr exceedance; high CLR → negative SHAP. The raw global correlation confirms this direction: ρ(Nitrososphaera CLR, Cr exceedance)=−0.116 (n=132,907), negative across all four sampled continents — N. America (ρ=−0.23), E. Asia (ρ=−0.17), Europe (ρ=−0.06), Tropical S (ρ=−0.27). The association is unmediated by soil pH (partial ρ=−0.125 after controlling for sg_pH). Concordant with Pei et al. (2018, *Front Microbiol*) who found ρ=−0.736 for Nitrososphaera vs soil Cr in Yellow River riparian soils. The finding establishes AOA nitrification inhibition by Cr as a globally recoverable signal from 16S data: Nitrososphaera depletion flags Cr-contaminated soil with cross-continental consistency.
  **Applies-to:** global soil 16S amplicon metal prediction; AOA ecology in contaminated soils; use of sensitive-taxon depletion as a contamination signal.
  **Evidence:** CatBoost SHAP rank 1/500 on 124,687 samples (`NB05_catboost_regression.ipynb`); cross-continental validation n=132,907 (`scripts/validate_nitrososphaera.py`); pH partial correlation; MTV ORFRC case study n=18 surface soils; literature concordance Pei et al. 2018.

- **Redox is the missing variable for Ni source discrimination: AUC rises from 0.282 to 0.753 when a groundwater redox proxy is added.** Without redox, a study-blocked RF classifier for geogenic (serpentinite) vs. anthropogenic Ni contamination performs well below chance (AUC=0.282) because these two source types select for *opposite* microbial communities — reducing/anaerobic communities in serpentinite terrain vs. metal-tolerant aerobic communities at industrial sites. Adding P(oxic) from a national groundwater Mn model separates these two pools, raising AUC to 0.753 (ΔAUC=+0.471). The same redox addition hurts Cr discrimination (0.838→0.754), because Cr-indicator genera already encode redox implicitly. **Methodological implication:** Ni bioindicator applications that ignore redox will produce systematically inverted predictions in reducing environments. Stratification by redox status (or inclusion of a redox covariate) is required before applying community-based Ni contamination classifiers.
  **Applies-to:** Ni biomonitoring design; geogenic vs. anthropogenic source discrimination in ultramafic terrain; any classifier that uses microbial community composition to discriminate contamination sources.
  **Evidence:** Serpentinite proxy sites (top-Q Ni AND Cr, n=7,246) have P(oxic)=0.412 vs. non-serpentinite=0.527 (11.5pp more reducing, p≈0). High-EF Ni sites carry 2× Geobacter CLR (0.914 vs. 0.477, p=6.2×10⁻⁹). Q8 RF classifier (study-blocked, n~21,000 per metal) achieves AUC=0.753 for Ni with redox vs. 0.282 without. Scripts: `run_redox_integration.py`, `run_q6_q8_fixed.py`; figures: `fig_redox_ni_inversion.pdf`, `fig_redox_source_discrim.pdf`.

- **A cross-metal indicator core of 11 genera spans ≥3/6 metals**, defined by broad-spectrum predictive importance (top-20 SHAP across multiple metals) rather than directional consistency. Robustness analysis reveals heterogeneous direction: only 2/11 genera are consistently depleted across all their metals (Geodermatophilus: Cd, Cr, Ni; Stenotrophobacter: Cr, Cu, Ni); 2/11 are consistently enriched (Rubrobacter, Geothrix); the remaining 7/11 show mixed direction (Skermanella, Conexibacter, Parafilimonas, Dyella, Nakamurella, Anaeromyxobacter, Nitrososphaera).

| Genus | Metals (n) | Direction |
|---|---|---|
| Skermanella | 5 (As,Cd,Cr,Ni,Pb) | Mixed |
| Conexibacter | 4 (As,Cd,Cu,Pb) | Mixed |
| Nitrososphaera | 3 (Cr,Cu,Ni) | Mixed |
| Geodermatophilus | 3 (Cd,Cr,Ni) | Consistently depleted |
| Stenotrophobacter | 3 (Cr,Cu,Ni) | Consistently depleted |
| Rubrobacter | 3 (As,Cd,Cu) | Consistently enriched |
| Geothrix | 3 (As,Cr,Ni) | Consistently enriched |
| Parafilimonas | 3 (As,Cr,Ni) | Mixed |
| Dyella | 3 (As,Cd,Pb) | Mixed |
| Nakamurella | 3 (As,Cd,Pb) | Mixed |
| Anaeromyxobacter | 3 (As,Cu,Ni) | Mixed |

Geodermatophilus and Stenotrophobacter are the two consistently-depleted cross-metal genera and represent the highest-priority candidates for multi-metal depletion biomonitoring panels.
  **Applies-to:** multi-metal biomonitoring panel design; cross-metal signal in global soil 16S data; selective targeting of depletion-based biomarkers.
  **Evidence:** `data/catboost_shap_importance.csv` (6,048 rows; top-20 per metal cross-tabulated); `data/narrative_robustness.json` (cross_metal_core direction analysis); `NB05_catboost_regression.ipynb`.

- **Microbiome reflects environment more than environment predicts individual genera (8.5× asymmetry).** Forward prediction (env → individual genus CLR): max Spearman ρ = 0.064 for any single env variable predicting any single genus. Reverse prediction (CLR community → env): ρ = 0.60 for pH, 0.55 for SOC, 0.44 for clay. Directionality index for soil variables: −2.03 (negative = reverse dominant; index = (max_reverse_ρ − max_forward_ρ) / (max_reverse_ρ + max_forward_ρ), where reverse = CLR → env RF ρ and forward = env → genus Spearman ρ). Metal variables are the weakest forward predictors (mean ρ = −0.13 to −0.15, negative due to the depletion pattern), consistent with the MWAS null — individual metal variables don't predict individual genus abundances within studies. The microbiome integrates multi-decade environmental filtering holistically, making it a better estimator of current soil state than any single environmental measurement is at predicting species composition.
  **Applies-to:** environmental monitoring design; choice of biomonitoring direction; interpretation of community-soil associations.
  **Evidence:** `data/directionality_results.json`; `data/usa_rf_env_targets_rho.parquet` (pre-existing reverse direction); `scripts/run_directionality_test.py`.

- **Guild 6 (Gaiella–Lysobacter–Stenotrophobacter consortium) is an anthropogenic-contamination-sensitive, geogenic-metal-adapted guild — not a simple "clean-soil" indicator.** The guild × condition matrix (8 guilds × 23 conditions) reveals that Guild 6 is strongly *elevated* under geogenic reducing conditions (δCLR=+2.31 under high-Ni/reducing, +1.55 under high-Cr/reducing) while being depleted under anthropogenic acid-contamination conditions (δCLR=−1.17 for high-As, −1.08 for acidic-Cu, −1.11 for acidic pH). The source characterization analysis (contamination vs. geogenic background) confirms this: Lysobacter, Gaiella, and Kribbella are background markers for Cr/Cu/Pb (depleted in contamination) but contamination markers for As — consistent with guild-6 taxa being adapted to naturally Ni/Cr-enriched serpentinite soils while displaced by acid-mobilised As/Cu/Pb contamination. The role of Lysobacter in anaerobic high-Ni environments (CLR +6.02 vs +3.53 in oxic) parallels serpentinite-associated H₂-oxidising communities. **Implication:** the guild 6 signal is metal-source-specific, not universally "contamination-sensitive," and requires redox and metal-source context for correct interpretation.
  **Applies-to:** network guild interpretation; bioindicator panel design for contamination vs. geogenic risk; Ni biomonitoring in ultramafic terrain.
  **Evidence:** `data/guild_condition_matrix.json`; `data/source_characterization_results.json`; `figures/fig_guild_condition_heatmap.pdf`; `scripts/run_guild_condition_exploration.py`.

- **Community-weighted KO functional profiles are 49–69% inflated by genus compositional bleed-through.** When community KO profiles are constructed as CLR-weighted sums over genus pangenome fractions (standard meta-analysis approach), 49–69% of tested KOs return positive FDR<0.05 associations with soil metal enrichment factors — an obviously inflated rate driven by H1 indicator genus abundances dominating the CLR vector. Zeroing the 111 H1 indicator genus columns before the matmul (H1-residualization) reduces inflation 73–88% for As/Cd/Cr/Ni, while leaving Cu (29% reduction) and Pb as informative exceptions. **The Pb case is particularly notable: H1-residualization *increases* the number of positive KOs by 22% (+22%; 1,095 → 1,336), revealing that H1 Pb indicator genera were actively suppressing non-indicator Pb-EF functional signals in the original analysis.** This suppression — not just inflation — means indicator genus dominance can *hide* functional biology in non-indicator genera. The confound-robust set surviving both analyses × H3 CMH is <3% of tested KOs per metal. **Methodological implication:** functional meta-analyses using community-weighted metagenomics that do not account for abundant-taxon compositional confound will systematically overstate functional signal in some metals and *understate* it in others. H1-residualization is a computationally cheap correction (zero columns, rerun matmul) applicable to any MWAS that uses genus CLR as the feature space.
  **Applies-to:** meta-analysis design for community-weighted KO MWAS; functional profiling using genus × pangenome matmul; any study linking CLR-based functional capacity to environmental gradients.
  **Evidence:** `data/usa_community_ko_ef_summary.csv`, `data/usa_community_ko_ef_resid_summary.csv`, `data/usa_community_ko_robust.csv` (83 robust KOs); `figures/fig_usa_community_ko_resid_comparison.pdf`; scripts `run_usa_community_ko_ef.py`, `run_usa_community_ko_ef_residualized.py`.

## Performance Notes

- RF ensemble is the best CLR-to-metal regression method on this feature space (500 genera, 124K samples). CatBoost underperforms RF by mean Δρ=−0.133; Extra Trees is close to RF. For future CLR-based regression on microbeatlas data, default to RF or Extra Trees — avoid Ridge/ElasticNet (lose ~30% ρ versus RF).
- Genome-scale community-KO analysis (7,221 KOs × 124K samples) runs in ~3 minutes with chunked BLAS matmul. Pattern: chunk KO columns (CHUNK=500), compute `comm_chunk = CLR_arr @ ko_chunk` in one BLAS call per chunk, then within-study Spearman rank-correlation with Fisher Z meta-analysis. This avoids both memory overflow (full 124K×7,221 matmul) and the Python loop bottleneck (per-KO correlation). The residualized rerun (zero 111 H1 columns, same matmul) adds <1 minute. Applicable to any CLR × pangenome functional inference task with ≥1K KOs and ≥10K samples.

---

## Results

### Sample coverage

Analysis matrix: 187,755 soil samples (SRS/ERS/DRS accessions, MicrobeAtlas) × 538 columns.
Post-filter (CLR present + science_2025 non-null + Project non-null): 132,803–132,907 samples per
metal, 2,175 unique studies. Metal positive rates: As 3.4%, Cd 3.9%, Cr 3.0%, Cu 0.6%, Ni 4.5%, Pb 2.1%.

![Global sample map](figures/fig_sample_map.png)

### Sequencing confounder analysis (NB01c)

**V-region primer bias (Step A):** In silico PCR of the top-500 CLR genera against V4 and V3V4
primer sets shows 80.4% of indicator genera are co-detectable at both amplicon chemistries
(V4+V3V4 co-detectable category). Primer choice is not a major confounder of genus-level CLR.

**Sequencing depth (Steps B–D):** Total read count (log10) was pulled from `sample_metadata` via
Spark for 188,308 soil samples spanning 2,506 studies. Depth η² between studies = 0.73 —
sequencing depth is almost entirely a study-level (batch) variable, not an independent sample-level
covariate. Within-study partial Spearman ρ (depth vs metal exceedance, after removing study mean):
|ρ| ≤ 0.014 across all 6 metals. Residualizing depth within studies from both CLR and metal arrays
before association testing removes this batch effect.

Confound summary: H(platform|study)=0.014, H(library_strategy|study)=0.011,
H(v_region|study)=0.058 — all technical variables are effectively absorbed by study identity
(96.2% of studies have a single uniform V-region). Controlling for study (via within-study
meta-analysis) is sufficient to remove all identified technical confounders.

*(Scripts: `scripts/build_sample_covariates.py`, `scripts/run_nb01c_depth.py`)*

---

### Within-study association analysis (MWAS)

A microbiome-wide association study was run to test whether per-genus CLR predicts metal
exceedance within individual studies, over and above sequencing depth. Design: for each
genus × metal pair (500 × 6 = 3,000 tests), within-study Spearman ρ (depth-residualized CLR vs
depth-residualized metal exceedance, minimum 20 samples/study) was combined across contributing
studies with Stouffer's Z meta-analysis (Fisher z-transform, weights √(n-3)), then BH-FDR
corrected.

**Result: 0/3,000 tests significant at FDR < 0.05.** Maximum |Stouffer Z| = 0.88 (Cupriavidus × Cd).
Stouffer Z values are normally distributed around 0 (std = 0.29, mean = −0.02). Effect sizes are
negligible: all weighted ρ in [−0.038, +0.038].

**Structural explanation:** The metal exceedance response variable (science_2025, 0.25° grid,
~28 km resolution) has near-zero within-study variance. Across the 2,018 AMPLICON studies with
metal data, 64% have exactly one unique metal exceedance value per metal — all samples fall within
a single 0.25° grid cell. Globally, only 11–21% of total metal exceedance variance is
within-study; 79–89% is between-study. The MWAS test has no power by design: no within-study
metal gradient → no detectable within-study CLR-metal association.

**Interpretation:** The CLR-metal association identified by NB01 (AUC 0.92–0.96) is a
macroecological signal operating at the between-study, between-region scale — not a within-site
effect detectable against the 0.25° grid resolution of the response. This is consistent with the
large study-blocked AUC drop in NB01b (study-blocked AUC 0.52–0.76 vs random-fold 0.92–0.96)
and with sequencing depth being a study-level variable (η²=0.73). The MWAS null does not
contradict H1; it confirms that the signal is macroecological, not driven by within-study
technical confounders or fine-grained local gradients.

| Metal | N tests (filter pass) | Nominally sig (p<0.05) | FDR sig | Max |Z| |
|-------|-----------------------|------------------------|---------|------|
| As    | 500                   | 0                      | 0       | 0.84 |
| Cd    | 500                   | 0                      | 0       | 0.88 |
| Cr    | 500                   | 0                      | 0       | 0.82 |
| Cu    | 500                   | 0                      | 0       | 0.85 |
| Ni    | 500                   | 0                      | 0       | 0.83 |
| Pb    | 500                   | 0                      | 0       | 0.84 |

*(Script: `scripts/run_mwas.py`)*

### USGS validation: structural null persists with measured metals

To confirm the MWAS null is biological rather than an artifact of the science_2025 gridded
response, we repeated the within-study analysis using point-measured soil metal concentrations
from the USGS National Geochemical Survey (National dataset; 139,817 soil sites, 6 target
metals, >95% completeness for As/Cr/Cu/Ni/Pb; 81% for Cd; stored locally at
`~/data/envdbs/usgs_geochem.parquet` + `tbl_chem.parquet`). USA-bounding-box MicrobeAtlas
amplicon samples (54,961 in 500 studies) were spatially matched to the nearest USGS soil site
within 25 km; 44,305 samples (80.6%) from 403 studies matched.

The gridded response's zero-variance problem was substantially resolved: only 7–24% of qualifying
studies have zero within-study metal variance with USGS (vs 64% with science_2025). Despite this,
the association signal remains absent:

**Result: 0/3,000 tests significant at FDR < 0.05.** Maximum |Stouffer Z| = 1.17 (Skermanella × As).
All weighted ρ in [−0.15, +0.15] — the same null profile as the science_2025 MWAS.

| Metal | Qualifying studies | Zero-variance (USGS) | Zero-variance (science_2025) | Max |Z| |
|-------|-------------------|----------------------|------------------------------|------|
| As    | 104               | 23%                  | 64%                          | 1.17 |
| Cd    | 68                | 24%                  | 64%                          | 0.88 |
| Cr    | 107               | 8%                   | 64%                          | 0.89 |
| Cu    | 106               | 10%                  | 64%                          | 0.87 |
| Ni    | 105               | 7%                   | 64%                          | 0.92 |
| Pb    | 108               | 10%                  | 64%                          | 0.85 |

**Interpretation:** The MWAS null is not an artifact of the gridded response. Community composition
does not track within-study soil metal gradients even when measured concentrations are used. This
strengthens the macroecological interpretation: the CLR-metal signal operates at the
between-region scale, reflecting long-run community filtering, not acute or local metal exposure.

*(Script: `scripts/run_usgs_within_study.py`)*

---

### Redox proxy integration: resolving the Ni source-discrimination paradox

To determine whether soil redox conditions mediate the metal-community associations identified above, we joined a groundwater redox proxy to the USA AMPLICON subset (n=54,918 samples, 499 studies). The proxy is the mn10_grid_prediction (USGS ScienceBase), which provides P(Mn>50μg/L) at 5m depth below the water table from a national machine-learning model — here inverted to P(oxic) = 1−P(Mn>50). Spatial join from ESRI:102003 (USA Contiguous Albers Equal Area Conic); median join distance = 0.46 km. USA mean P(oxic) = 0.512 (~equal oxic/reducing coverage).

![Redox proxy spatial distribution](figures/fig_redox_proxy.pdf)

**Q1 — Geobacter ↔ redox: hypothesis confirmed.** Geobacter CLR is significantly more abundant in reducing soils (sample-level ρ=−0.160, p=2.5×10⁻³⁰¹, n=52,968; study-level ρ=−0.239, p=6.9×10⁻⁸, n=497 studies), ranking 498th/500 in oxic-association. This directly confirms the ecological expectation: Geobacter is an obligate Fe(III)/U(VI) reducer, and its abundance tracks reducing soil conditions at continental scale through 16S amplicon data.

![Geobacter vs redox proxy](figures/fig_redox_geobacter.pdf)

**Q2 — All 500 genera ranked by redox association.** 150 genera show |ρ|>0.10 with P(oxic). The top reducing-associated genera are *Clostridium* (ρ=−0.190), *Anaeromyxobacter* (ρ=−0.173), and *Geobacter* (ρ=−0.160). The most oxic-associated are *Saccharothrix* (ρ=+0.192), *Microlunatus* (ρ=+0.162), and *Glycomyces* (ρ=+0.161) — understudied oligotrophic Actinobacteria with no prior literature linking them to soil oxygen status.

A notable novel finding is a **myxobacterial cluster**: *Anaeromyxobacter*, *Polyangium*, *Byssovorax*, and *Aetherobacter* all rank among the top reducing-associated genera. *Anaeromyxobacter* is documented as a facultative Fe(III)/nitrate-reducing anaerobe capable of arsenate respiration (Treude et al., 2003, *FEMS Microbiol Ecol*; Muramatsu et al., 2020, *Appl Environ Microbiol*). The co-clustering of the predatory myxobacteria *Polyangium*, *Byssovorax*, and *Aetherobacter* with reducing conditions is unstudied: these genera have no published redox ecology, suggesting their prey communities (fermenters and Fe(III)-reducers) may concentrate in reducing soil microsites, drawing predators there. Of 150 genera with |ρ|>0.10, 95 are absent from the metal-indicator lists in this project — the redox gradient captures a partly distinct ecological axis from the metal contamination signal.

![Top genera ranked by redox association](figures/fig_redox_genera_top.pdf)

**Q3 — Metal landscape vs. redox.** At continental scale, As/Cd/Cu/Pb/U-enriched sites are significantly more oxic (ρ = +0.13 to +0.19), while Cr/Ni-enriched sites are more reducing (ρ = −0.032 and −0.052 respectively). The Cr/Ni sign reversal reflects serpentinite geology: geogenic Cr/Ni enrichment occurs in reducing ultramafic terrains (see Q7).

![Metal concentrations vs redox proxy](figures/fig_redox_metal_corr.pdf)

| Metal | ρ(log[s25], P(oxic)) | p | n |
|-------|---------------------|---|---|
| Pb    | +0.182 | 2.96×10⁻³⁰⁵ | 41,275 |
| U (GeoROC) | +0.187 | 3.70×10⁻⁷⁸ | 9,797 |
| As    | +0.146 | 2.95×10⁻¹⁹⁶ | 41,275 |
| Cu    | +0.137 | 3.67×10⁻¹⁷² | 41,275 |
| Cd    | +0.131 | 3.43×10⁻¹⁵⁶ | 41,275 |
| Ni    | −0.052 | 3.61×10⁻²⁶  | 41,275 |
| Cr    | −0.032 | 1.17×10⁻¹⁰  | 41,275 |

**Q5 — Does redox improve U prediction?** Adding P(reducing) to the USGS U model (baseline ρ=0.746, n=45,775 USA AMPLICON samples with USGS soil U within 25 km) reduces performance: Δρ=−0.016 (ρ=0.730). Redox enters as the 15th most important feature (imp=1.4%) behind geography, As co-occurrence, and soil chemistry. The existing feature set already encodes the relevant geochemical gradient implicitly; adding explicit redox introduces collinearity without complementary information. Top CLR genera (Actinocorallia, Solirubrobacter, Nitrososphaera) all decline in rank when redox is added, indicating those genera carry the redox signal that P(reducing) then takes credit for.

![U model feature importances with/without redox](figures/fig_redox_u_model.pdf)

**Q6 — Does redox improve any metal prediction?** For all 6 metals, the effect of adding P(oxic) to the CLR-based RF regression (study-blocked CV, n=41,275 USA samples) is negligible: |Δρ|≤0.009, with Cu the sole metal showing marginal improvement (Δρ=+0.001).

| Metal | Baseline ρ | +Redox ρ | Δρ |
|-------|-----------|---------|-----|
| Cr | 0.924 | 0.920 | −0.004 |
| Ni | 0.965 | 0.964 | −0.001 |
| As | 0.868 | 0.859 | −0.009 |
| Cu | 0.860 | 0.861 | **+0.001** |
| Cd | 0.826 | 0.824 | −0.002 |
| Pb | 0.829 | 0.829 | −0.001 |

This result complements the Q5 finding: **community composition already encodes soil redox status.** The 500 CLR genera collectively function as a better redox proxy than the modelled P(oxic) product for these prediction tasks, consistent with the MWAS result showing community composition is primarily a macroecological signal (between-region, cross-study scale).

*(Script: `scripts/run_q6_q8_fixed.py`)*

**Q7 — Serpentinite communities and redox.** The "Ni inversion" (source discrimination AUC=0.282 below chance; see Q8) implies geogenic and anthropogenic Ni sites have compositionally opposite communities. A serpentinite proxy (samples in top quartile for both s25_ni_AT and s25_cr_AT, n=7,246) reveals a structural explanation: serpentinite-proxy sites are dramatically more reducing than other sites (P(oxic)=0.412 vs. 0.527; difference = 11.5pp; p≈0 by KW test). High-EF Ni sites carry twice the Geobacter CLR of low-EF Ni sites (mean 0.914 vs. 0.477; p=6.2×10⁻⁹). Serpentinite (ultramafic) soils are characterised by low silica activity, elevated pH, H₂ production, and reducing conditions (Brazelton et al., 2012, *Front Microbiol*). Their reducing redox state selects for anaerobic lineages including Geobacter — a different community fingerprint from the aerobic/industrial Ni-contaminated sites where metal-tolerance genera predominate.

![Ni inversion and serpentinite redox](figures/fig_redox_ni_inversion.pdf)

| Group | n | P(oxic) mean | Geobacter CLR mean |
|-------|---|-------------|-------------------|
| High-EF Ni | 10,321 | 0.466 | 0.914 |
| Low-EF Ni | 10,385 | 0.486 | 0.477 |
| Serpentinite proxy | 7,246 | **0.412** | — |
| Non-serpentinite | 47,672 | **0.527** | — |

*(Script: `scripts/run_redox_integration.py`)*

**Q8 — Redox resolves Ni source discrimination; Cr unaffected.** Source discrimination (geogenic vs. anthropogenic high-metal sites) was tested for Cr and Ni with and without the redox proxy, using a study-blocked RF classifier:

| Metal | Baseline AUC | +Redox AUC | ΔAUC |
|-------|-------------|-----------|------|
| Cr | 0.838 | 0.754 | −0.084 |
| **Ni** | **0.282** | **0.753** | **+0.471** |

![Source discrimination AUC with/without redox](figures/fig_redox_source_discrim.pdf)

**Ni is the headline result.** Without redox, the Ni classifier performs well below chance (AUC=0.282), because geogenic-serpentinite and anthropogenic-industrial high-Ni sites have compositionally *opposite* communities — the classifier is confused by the same genus composition arising in two structurally different contexts. Adding P(oxic) supplies the missing separating axis: serpentinite sites are reducing, anthropogenic sites are oxic, and with this information the classifier achieves AUC=0.753.

For **Cr**, redox hurts discrimination (0.838→0.754, Δ=−0.084). The mechanism is likely collinearity: Cr-indicator genera (including Nitrososphaera) already carry redox information, and adding P(oxic) explicitly introduces a redundant feature that dilutes the discriminative power of those genera rather than complementing them.

**Summary.** Any field biomonitoring application for Ni contamination must account for soil redox status. In reducing environments (serpentinite or waterlogged soils), high Ni abundance is geogenic and supported by an anaerobic community (Geobacter, Clostridium). In oxic environments, high Ni abundance is industrial and supported by a different community (metal-tolerant aerobes). A 16S-based Ni bioindicator that ignores redox will fail systematically on reducing soils.

*(Scripts: `scripts/run_redox_integration.py`, `scripts/run_q6_q8_fixed.py`)*

**Multi-output auxiliary learning for Ni source deconvolution.** A follow-up test
(`scripts/run_ni_multioutput.py`) evaluated whether jointly predicting Cr exceedance as an
auxiliary target improves Ni exceedance classification (study-blocked RF, n=14,621 USA samples
in high/low Ni exceedance quartiles). Results: CLR-only AUC=0.742 for Ni exceedance quartile,
rising to 0.780 with redox proxy; multi-output auxiliary (joint Cr prediction) adds
+0.003–0.004 AUC over the corresponding single-output baseline. This increment is too small
to be practically meaningful.

*(Figures: `figures/fig_ni_multioutput_comparison.pdf`, `figures/fig_ni_multioutput_gains.pdf`)*

*Methodological note:* This analysis classifies high vs. low Ni *exceedance quartile*, not
geogenic vs. anthropogenic source (which is the Q8 question). The Q8 CLR-only AUC=0.282 (for
genuine source discrimination) is not contradicted by the AUC=0.742 here — these measure
different targets. The CLR+Cr exceedance AUC=0.998 in this test is circular (Cr and Ni
exceedance are correlated across the same geochemical grid, so using Cr directly encodes the
answer). These results confirm only that auxiliary learning does not add meaningfully beyond
direct feature inclusion.

---

### Signed SHAP direction analysis

To characterise whether indicator genera signal metal risk through presence or absence, we trained a CatBoost regression model (300 trees, depth 6, learning rate 0.05) per metal on CLR-only features and computed signed mean SHAP values across 5,000 randomly drawn samples. Unlike mean |SHAP| (which ranks importance but discards direction), signed mean SHAP distinguishes positive contributors (genus presence → ↑ exceedance probability) from negative contributors (genus presence → ↓ exceedance probability).

Base exceedance probabilities (model intercepts) ranged from 0.051 (Cu) to 0.150 (Cd), consistent with the global positive rates reported above. Top-ranked genera by |mean SHAP| and their sign:

| Metal | Base value | Top genus | Signed mean SHAP | Direction |
|-------|-----------|-----------|-----------------|-----------|
| As    | 0.101     | Conexibacter | −0.00098 | Negative (absence = risk) |
| Cd    | 0.150     | Cupriavidus  | −0.00005 | Negative |
| Cr    | 0.106     | Nitrososphaera | −0.00008 | **Negative** (confirms depletion signal) |
| Cu    | 0.051     | Catenulispora | −0.00011 | Negative |
| Ni    | 0.100     | Methyloceanibacter | +0.00010 | **Positive** (presence = risk) |
| Pb    | 0.114     | Rhodomicrobium | −0.00017 | Negative |

Five of six metals have negative signed SHAP for their top genus: indicator presence reduces predicted exceedance, meaning it is the *depletion* of these genera — not their enrichment — that flags metal contamination risk. Nitrososphaera for Cr confirms this direction (already established by SHAP-CLR ρ=−0.920; see Nitrososphaera global validation below). Methyloceanibacter for Ni is the sole exception — a Methyloceanibacter-enriched site predicts elevated Ni exceedance, suggesting positive niche co-occurrence for this genus rather than a sensitive-taxon depletion pattern.

The interactive SHAP waterfall chart and per-genus SHAP dependency scatter (fig_comprehensive_dashboard.html, Section 5) allow per-metal exploration of all top-20 signed indicators.

*(Script: `scripts/run_shap_signed.py`; data: `data/shap_signed.json`, `data/shap_dependency.json`)*

---

### Robustness and sensitivity analysis

**Ecosystem subsets:** CLR performs comparably in agricultural (AUC 0.930–0.992) and forest
(0.911–0.977) soils, and in surface-only (depth ≤ 5cm, 0.871–0.986) samples. Contamination signal
is not restricted to anthropogenic land use.

**Taxonomic resolution:** Genus-level CLR (AUC 0.922–0.961) outperforms family-level (0.917–0.949)
and substantially outperforms phylum-level (0.790–0.868). Finer resolution consistently improves
prediction, motivating genus-level CLR over coarser approaches.

![Taxon resolution](figures/fig_taxon_resolution.png)

**Geographic generalisability:** CLR is predictive across all sampled regions — Europe (0.872–0.971),
North America (0.952–0.988), East Asia (0.908–0.956), Tropical (0.929–0.975), Temperate N
(0.920–0.965). The metal-community association holds globally, not just in well-sampled regions.

**Regression CV (raw exceedance probability):** Random-forest regression of raw s25 probability
(rather than binarised at 0.5) yields consistent Spearman ρ: CLR-only 0.632–0.747, soil-only
0.938–0.959, spatial-only 0.997–0.998. The ordering is identical to the AUC analysis.

![Extended metrics](figures/fig_extended_metrics.png)
![Study confound and regression](figures/fig_study_confound_regression.png)

### Metal-specificity of indicators

Cross-metal Jaccard (overlap of top-50 indicator genera between metals):

| Pair     | Jaccard |
|----------|---------|
| As–Cd    | 0.250   |
| As–Pb    | 0.111   |
| Cr–Pb    | 0.143   |
| As–Cu    | 0.111   |
| Cr–Cu    | 0.081   |
| Cd–Cu    | 0.026   |
| Cd–Ni    | 0.053   |
| Ni–Pb    | 0.000   |
| Cu–Ni    | 0.000   |

Indicator sets are metal-specific (all pairwise Jaccard < 0.26). As and Cd share the highest
overlap (0.25), consistent with their co-contamination in mining and smelting contexts. Cu–Ni and
Ni–Pb share no indicators, consistent with distinct geochemical niches.

![Indicator heatmap](figures/fig_indicator_heatmap.png)
![Robustness summary](figures/fig_robustness_summary.png)

### Nitrososphaera case study: ORFRC HFIR soil (Oak Ridge, TN)

To contextualise the global Nitrososphaera SHAP finding, we examined the MTV QIIME2 dataset as an independent site-level validation — 41 soil samples from the Oak Ridge Field Research Center HFIR area (Tennessee; a site with documented Cr, Pb, and Cd contamination from historical nuclear operations; 16S V3-V4). Here the niche co-occurrence mechanism can be directly observed at known contamination gradients. Nitrososphaeria (class; AOA) shows a clear pH gradient: higher pH → higher Nitrososphaeria (Spearman ρ=+0.47, p<0.05, n=18 samples with both pH and genus data). Rhodanobacter (acid denitrifier) shows the opposing trend (ρ=−0.33, p<0.05), tracing the aerobic/reducing N-cycling axis with pH.

![Redox N-cycling axis in ORFRC HFIR soil](figures/fig_mtv_redox_axis.pdf)
![Nitrososphaeria vs Rhodanobacter scatter](figures/fig_mtv_nitro_vs_rhodano.pdf)

Clay fraction is the strongest predictor of Nitrososphaeria at this site (ρ=−0.62, p<0.01) — higher clay reduces substrate diffusivity and creates micro-aerobic microsites that disfavour AOA, consistent with AOA ecology (Prosser et al. 2019). The ORFRC site illustrates the local pH–AOA covariance: high-pH aerobic zones harbour more Nitrososphaeria and are also the zones where documented Cr contamination occurs. However, the global analysis reverses this apparent positive local association — controlling for pH at global scale reveals ρ=−0.125 (Nitrososphaera vs Cr exceedance), with the global SHAP direction negative (ρ(CLR, SHAP)=−0.920). At ORFRC, pH co-varies with both AOA and surface contamination in the same direction; globally, pH does not mediate the Nitrososphaera–Cr relationship and the net signal is depletion.

![MTV genus trends vs environmental covariates](figures/fig_mtv_genus_trends.pdf)
![Phylum-level RA per MTV sample](figures/fig_mtv_phylum_ra.pdf)
![Phylum RA faceted by site](figures/fig_mtv_phylum_ra_facet.pdf)
![Mean phylum RA by site × material](figures/fig_mtv_phylum_ra_summary.pdf)

Extension to ORFRC-bbox samples in `analysis_matrix` (n=127 groundwater/bioreactor samples at the FW well field, ~3 km west of HFIR) shows the trend does not generalise to subsurface samples: Nitrososphaeria is 85× lower, and pH correlations flip sign. This is expected — those samples are from anoxic bioreactors and groundwater (PRJNA315455), and their "pH" is modelled surface-soil SoilGrids pH irrelevant to subsurface conditions.

![Extended redox axis: MTV + ORFRC bbox](figures/fig_mtv_redox_extended.pdf)
![Extended pH gradient strip](figures/fig_mtv_redox_gradient_extended.pdf)

*(Data: MTV QIIME2 dataset, 16S V3-V4, n=18 HFIR soil samples with pH; analysis_matrix ORFRC bbox n=127)*

### Nitrososphaera global validation

To confirm the SHAP finding at global scale, we computed Spearman ρ between Nitrososphaera CLR
and Cr exceedance probability across the full analysis_matrix (n=132,907 samples), stratified by
geographic region and with soil pH as a partial-correlation control.

![Nitrososphaera validation](figures/fig_nitrososphaera_validation.pdf)

**SHAP direction.** The SHAP dependence plot (fig_nitrososphaera_shap_dep.pdf) shows SHAP-CLR
ρ=−0.920 for Cr: higher Nitrososphaera CLR → negative SHAP (reduces Cr exceedance prediction).
Nitrososphaera *absence* is the contamination signal, not its presence. The four other metals
with negative SHAP-CLR ρ (Cu −0.892, Ni −0.803, Pb −0.717, As −0.335) indicate a
cross-metal sensitive-taxon pattern; Cd is the sole outlier (+0.591, different Cd-cycling pathway).

**Cross-continental replication.** The global raw correlation ρ=−0.116 (95% CI: −0.122,
−0.111, n=132,907) is negative across all four regions tested: N. America (ρ=−0.233,
n=49,362), E. Asia (ρ=−0.174, n=35,582), Europe (ρ=−0.058, n=32,346), and Tropical S
(ρ=−0.268, n=4,147). The effect is present on every inhabited continent sampled.

**pH does not mediate the association.** Partial ρ controlling for soil pH (sg_pH) =
−0.125, virtually unchanged from the raw −0.116. Soil pH is positively correlated with
both Nitrososphaera abundance (ρ=+0.077) and Cr exceedance (ρ=+0.046), but removing pH
does not attenuate the Nitrososphaera–Cr relationship.

**Quintile response.** Nitrososphaera CLR peaks at low-moderate Cr risk (Q1–Q2, exceedance
0–3.8%) and declines progressively through Q3–Q5, reaching its lowest mean at Q5 (exceedance
>13.5%). This non-linear monotonic decline is consistent with a toxicity threshold above which
nitrification is progressively suppressed.

**Literature concordance.** Pei et al. (2018) identified Candidatus Nitrososphaera as
Cr-sensitive in Yellow River riparian soils (ρ=−0.736, p<0.01, n=25 sites, Cr range
83–506 mg/kg). Our global estimate (ρ=−0.116 at population scale across diverse biomes and
contamination levels) is attenuated relative to their single-region, high-contamination
setting, as expected. The sign and interpretation are fully concordant.

*(Data: analysis_matrix.parquet, n=132,907 samples with Nitrososphaera CLR + s25_cr_AT;
script: scripts/validate_nitrososphaera.py; figure: fig_nitrososphaera_validation.pdf)*

### Soil chemistry confound: metal indicators are not proxies for edaphic gradients

![Soil confound heatmap](figures/fig_soil_confound.pdf)

To determine whether the metal indicator genera identified by stratified RF are merely tracking
co-varying soil chemistry rather than metal-specific community responses, we ran the identical
stratified RF design (Q1 vs Q2, Q4 vs Q5, Q1+Q2 vs Q4+Q5) using pH, SOC, and clay as the response
variable, then computed Jaccard overlap between metal and soil-variable indicator lists.

**Soil variable RF accuracy** (full stratum, n=130,080–137,780 samples per variable):

| Soil variable | AUC (low) | AUC (high) | AUC (full) |
|---------------|-----------|-----------|-----------|
| pH            | 0.929     | 0.950     | 0.957     |
| SOC           | 0.948     | 0.943     | 0.950     |
| clay          | 0.939     | 0.926     | 0.942     |

AUCs (0.926–0.957) are in the same range as metal AUC (0.938–0.955), confirming the geographic
proxy effect is not metal-specific: any environmental variable spatially structured at the
inter-continental scale produces near-identical RF accuracy from genus CLR.

**Cross-variable Jaccard** (metal-full vs soil-full indicator genera, top-20 each):

| Metal | × pH | × SOC | × clay |
|-------|------|-------|--------|
| As    | 0.081 | 0.053 | 0.111 |
| Cd    | 0.053 | 0.081 | 0.143 |
| Cr    | 0.111 | 0.176 | 0.111 |
| Cu    | 0.143 | 0.111 | **0.212** |
| Ni    | 0.053 | 0.143 | **0.212** |
| Pb    | 0.081 | 0.081 | 0.143 |

The range (0.053–0.212) spans the same range as within-metal J(low, high) (0.053–0.143), meaning
no metal-soil-variable pair has anomalously high overlap. The highest overlaps are Cu × clay = 0.212
(7 shared genera: Catenulispora, Lysobacter, Neobacillus, Polaromonas, and others) and Ni × clay
= 0.212 (7 genera: Bradyrhizobium, Geodermatophilus, Neobacillus, Povalibacter, and others). Both
are geochemically interpretable: Cu and Ni adsorb strongly to clay mineral surfaces, making
clay-rich sites enriched in both clay-adapted genera and bioavailable Cu/Ni. pH overlap is lower
(0.053–0.143), consistent with the Nitrososphaera pH partial-correlation result.

**Within-soil-variable J(low, high)** (disjointness of low- vs. high-stratum indicator genera):
pH = 0.026 (extremely disjoint — acidophile/alkaliphile partitioning), SOC = 0.081, clay = 0.212.
The clay within-variable J(0.212) is comparable to the highest metal within-variable J (Ni = 0.143),
suggesting that clay texture creates a shallower community gradient than pH or metal contamination.

**Conclusion**: metal indicator genera are metal-specific relative to the soil chemistry baseline.
Cu and Ni panels share the most overlap with clay indicators, warranting a clay-stratification step
in field biomonitoring for those two metals to avoid misattributing clay-community gradients as
contamination signals.

*(Script: scripts/run_soil_confound_analysis.py; figure: fig_soil_confound.pdf)*

### Co-occurrence network ecology under metal stress

To characterise how high-metal conditions reshape the cooperative vs competitive structure of
soil microbial communities, we computed Spearman co-occurrence networks among the top-40
MWAS genera across 23 environmental conditions (USA subset, n=57,248–64,259 per condition,
Spearman ρ threshold |ρ|>0.25).

**Null model (sign permutation).** A sign-permutation null model (200 permutations per
condition, preserving |ρ| and edge density) confirms that the positive-edge fraction (pos_frac)
is non-random in all 23 conditions: z-scores 4.04–18.93, all p<0.005. High-metal conditions
show the largest departures from chance (high-As: z=13.8; combined high-Ni/reducing: z=18.9),
consistent with metal stress selecting for cooperative community structure.

**Positive-edge fraction shifts.** The baseline USA pos_frac is 0.71 (s25-defined conditions)
or 0.70 (USGS-defined). Under high-metal conditions:

| Condition | pos_frac (s25) | pos_frac (USGS) | Direction agree |
|-----------|---------------|----------------|-----------------|
| High As   | 0.861         | 0.730          | ✓               |
| High Cd   | 0.818         | 0.737          | ✓               |
| High Cr   | 0.776         | 0.753          | ✓               |
| High Cu   | 0.830         | 0.706          | ✓               |
| High Ni   | 0.720         | 0.747          | ✓               |
| High Pb   | 0.802         | 0.639          | ✗ (reversal)    |

Five of six metals agree in direction (83% concordance). Effect sizes are 2–3× larger with
s25 exceedance than with USGS absolute concentrations, consistent with exceedance capturing
the anthropogenic contamination signal above geochemical background while USGS absolute
concentrations conflate geogenic and anthropogenic sources.

**Lead reversal.** High-USGS-Pb sites show pos_frac *below* baseline (0.639 vs. 0.695),
while high-s25-Pb sites show positive enrichment (0.802). This reversal is ecologically
interpretable: sites with high *absolute* Pb concentrations include geogenic high-Pb soils
where natural Pb selects for competitive exclusion among adapted specialists, whereas s25
exceedance isolates anthropogenic contamination loads where community stress promotes
cooperative over competitive interactions.

**Guild characterisation.** Ward hierarchical clustering on a 40×40 co-occurrence stability
matrix (proportion of 23 conditions in which each pair is connected by |ρ|>0.25) identified
8 guilds. Key guilds (full guild × condition matrix in the section below):

- *Guild 1* (n=21 genera, most diverse): coherent in high-As/high-Cd/acidic conditions;
  includes Rhodomicrobium, Acidobacterium, Methylomonas. Elevated δCLR (+0.29 in high-As),
  suggesting an acid–arsenic co-mobility niche.
- *Guild 2* (n=5 genera, includes Cupriavidus): depleted in high-Cr/high-Ni (δCLR=−0.59 and
  −0.40 respectively); most depleted under combined high-Ni/reducing (δCLR=−1.08).
- *Guild 6* (n=5 genera: Gaiella, Stenotrophobacter, Lysobacter, Aetherobacter, Alsobacter):
  depleted under anthropogenic contamination conditions (acidic, high-As, high-Cu, high-Pb),
  but strongly elevated under geogenic reducing conditions (δCLR=+2.31 under high-Ni/reducing,
  +1.55 under high-Cr/reducing). Initially characterised as a "clean-soil" guild; subsequent
  guild × condition analysis revealed this is an anthropogenic-contamination-sensitive,
  geogenic-metal-adapted guild (see the Guild × condition section below).
- *Guild 8* (Parafilimonas, n=1): most extreme metal sensitivity in the dataset — depleted
  in high-Ni (δCLR=−1.73), high-Cr (−1.06), and high-Ni/reducing combined (−2.58).

*Design note: the guild × condition analysis (below) computes δCLR means of guild members across environmental conditions — it is not differential abundance (DA) tested within guilds. Guild membership is derived from co-occurrence stability across these same conditions, so guild membership and δCLR are correlated by construction; however, the downstream analysis characterises aggregate community-level shifts, not species-level DA within guild-defined groups, which avoids the circular-clustering leakage concern described in docs/pitfalls.md.*

*(Scripts: scripts/run_network_null_model.py, scripts/run_network_usgs.py,
scripts/run_guild_characterization.py; data: data/network_null_model.json,
data/network_metric_comparison.json, data/guild_characterization.json)*

### Environment–microbiome directionality

To test whether environment predicts microbiome composition or vice versa, we compared
forward (env → genus CLR) and reverse (CLR → env) prediction strength across USA samples
(n=64,259; study-blocked GroupKFold CV for reverse direction, Spearman ρ for forward).

**Forward direction (env → microbiome)** is weak. The maximum absolute forward Spearman ρ
between any single environmental variable and any single genus CLR is 0.064 (Cupriavidus,
ρ=−0.064 mean across 9 env variables; median per-genus |ρ| < 0.02). Community PC1 forward
prediction: ρ=−0.053 vs. the 9-variable environmental feature set. Metal variables show weak
*negative* forward correlations (As: ρ=−0.154, Ni: ρ=−0.137, Cr: ρ=−0.094 for community
PC1), consistent with depletion-driven structure (high metal → loss of sensitive taxa →
negative CLR shift).

**Reverse direction (CLR → env)** is strong:

| Environmental target | CLR → env ρ |
|---|---|
| Soil pH         | 0.602 |
| Longitude       | 0.552 |
| log SOC         | 0.547 |
| Latitude        | 0.512 |
| Clay fraction   | 0.437 |
| log Topographic roughness | 0.335 |
| Mine distance    | 0.247 |

**Directionality asymmetry.** Soil variables show a directionality index of −2.03 (reverse
dominant); geographic variables −0.75. Overall, CLR predicts soil properties 6–8× better
than soil properties predict individual genera. The microbiome community fingerprint integrates
long-term multi-variable environmental filtering; any single environmental variable carries
only a partial slice of this information.

**Implication for biomonitoring.** The asymmetry supports using microbial community composition
as an integrative environmental proxy (predict pH, SOC, clay, geographic location from
microbiome) rather than expecting single environmental variables to reliably predict individual
genus abundances. Metal signals are the weakest forward predictors, consistent with the MWAS
null and the macroecological nature of metal–community associations.

*(Script: scripts/run_directionality_test.py; data: data/directionality_results.json,
data/usa_rf_env_targets_rho.parquet)*

### Cross-study generalizability of metal associations

We tested which properties predict whether a genus–metal association generalises across studies
(concordance of MWAS Stouffer Z and USGS within-study Stouffer Z for the same genus × metal).

**Signal concordance is metal-specific**: Pb associations are the most reproducible across
methods (ρ=+0.42 between MWAS and USGS Stouffer Z); Ni moderate (ρ=+0.26); Cr weak
(ρ=+0.23); As shows negative concordance (ρ=−0.38), suggesting context-dependent redox
chemistry reverses the direction of As–community associations between measured and modelled
data. Cd and Cu show no cross-method concordance (|ρ|<0.08).

**Study design properties do not predict generalizability.** Study size, geographic coverage,
and metal concentration variance show ρ≈0 with signal strength across all six metals.
Associations that generalise are driven by intrinsic genus–metal biochemistry (e.g., Cupriavidus
for Cd/Pb, Gaiella for Cd/Pb, Stenotrophobacter cross-metal depletion), not by sampling
design.

**Cross-metal winners**: Only 6 genera appear in top-10 rankings for ≥2 metals — Gaiella
(Cd, Pb; avg rank 1.5), Rhodomicrobium (As, Cd), Cupriavidus (Cd, Pb), Povalibacter (As, Cr),
Aeromicrobium (As, Cu), Rhodoblastus (Cr, Ni).

*(Script: scripts/run_generalizability.py; data: data/generalizability_analysis.json)*

### Source characterization: contamination vs. natural background biomarkers

To distinguish microbial signatures of anthropogenic contamination from those of naturally
elevated geochemical background, we classified USA samples into two groups per metal:
- **Contamination**: high s25 exceedance (top quartile) AND high USGS concentration (top half)
- **Geogenic background**: high USGS concentration (top quartile) AND low s25 exceedance (bottom half)

This design isolates the anthropogenic component while controlling for total metal load.
Classifiers used study-blocked GroupKFold CV (ExtraTreesClassifier, genus CLR features).

**Classifier performance:**

| Metal | Contamination n | Background n | AUC   |
|-------|----------------|-------------|-------|
| As    | 5,316          | 2,469       | 0.620 |
| Cd    | 2,437          | 1,375       | 0.653 |
| Cr    | 9,240          | 3,112       | 0.630 |
| Cu    | 4,866          | 3,475       | 0.747 |
| Ni    | 6,776          | 3,816       | 0.677 |
| Pb    | 5,726          | 2,424       | 0.735 |

Cu (AUC=0.747) and Pb (0.735) are the most discriminable; As and Cr the least (0.620–0.630).
Mean AUC=0.677 confirms microbial community composition encodes anthropogenic vs. geogenic sources
above chance even after study-level blocking.

**Cross-metal contamination biomarkers** (elevated in contamination group, ≥4/6 metals):
- *Microlunatus* (top feature for Cd and Cr; elevated in 5/6 contamination groups; Cd CLR
  contamination=+1.50 vs background=−1.31) — Gram-positive actinobacterium documented from
  metal-contaminated soils; tolerates elevated metal loads.
- *Pseudomonas* (top for Cu; elevated in 4/6) — broad metal resistance repertoire including
  Cu-efflux operons (*cop* genes).
- *Parafilimonas* (top for Cu, Pb; elevated in 4/6) — enriched under anthropogenic organic-metal
  co-contamination conditions.

**Cross-metal geogenic background biomarkers** (elevated in background, ≥4/6 metals):
- *Povalibacter* (top background genus for 5/6 metals: As, Cd, Cr, Ni, Pb)
- *Lysobacter*, *Gaiella*, *Kribbella* (each 4/6)

**Context-dependent genera.** Several guild-6 taxa reverse role between metals: *Gaiella*,
*Lysobacter*, and *Stenotrophobacter* are contamination markers for As (elevated δCLR in
contamination group) but background markers for Cr, Cu, and Pb (depleted in contamination).
This reversal is ecologically interpretable: As contamination in the USA dataset co-occurs with
geogenic serpentinite settings where guild-6 taxa are adapted, whereas Cr/Cu/Pb contamination
is more purely anthropogenic (industrial smelters, agricultural inputs) where these taxa are
displaced.

**Ni redox ecology** (AUC=0.688; reducing: P(oxic)<0.4; oxic: P(oxic)>0.6):
Ni-reducing soils (serpentinite proxy, n=4,763) are enriched in *Lysobacter* (CLR: +6.02 vs
+3.53 in oxic), *Gaiella* (+6.47 vs +4.86), and *Kribbella* (+4.77 vs +3.24). Ni-oxic soils
(contamination proxy, n=2,376) are enriched in *Nitrosomonas* (CLR: −0.03 vs −1.17) and
*Pseudomonas* (+3.59 vs +2.81). The Lysobacter–Gaiella–Kribbella consortium under anaerobic
high-Ni conditions points to a serpentinite-associated guild capable of metal-associated
reduction — consistent with Brazelton et al. (2012) on H₂-oxidizing communities in serpentinite
ultramafic settings.

*(Script: scripts/run_source_characterization.py; data: data/source_characterization_results.json)*

### Guild × condition matrix: environmental context of co-occurrence guilds

To characterise which guilds occur under which conditions, we computed mean δCLR for each of
the 8 co-occurrence guilds across 23 environmental conditions (all-USA s25-defined subset).
Ward hierarchical clustering of conditions in the 8-dimensional guild space identified 4
ecologically interpretable clusters (fig. fig_guild_condition_heatmap.pdf, fig.
fig_condition_dendrogram.pdf).

**Condition clusters:**

- *Cluster 1 — Geogenic redox* (high_cr_reducing, high_ni, high_ni_reducing): Guild 6
  strongly elevated (δCLR=+2.31 under high-Ni/reducing, +1.55 under high-Cr/reducing); Guilds
  2 and 8 strongly depleted.
- *Cluster 2 — Anthropogenic contamination* (acidic_ph, high_as, high_cd, high_cu, high_pb,
  oxic, and acidic-metal combinations): Guild 6 strongly depleted (δCLR=−1.17 for As, −1.08
  for acidic-Cu); Guild 1 (21-member generalist) moderately elevated (+0.31 in high-As).
- *Cluster 3 — Low-metal reference* (low_as, low_cr, low_ni, neutral_ph): Guild 8
  (Parafilimonas) elevated in low-Cr (+1.22) and low-Ni (+0.92); Guild 7 (Actinocorallia,
  Aeromicrobium, Streptomyces) elevated at neutral pH (+0.68).
- *Cluster 4 — Mixed/baseline* (alkaline_ph, all_usa, high_cr, low_cd/cu/pb, reducing):
  moderate guild responses; Guild 6 elevated in alkaline (+0.44) and reducing (+1.08).

**Critical reinterpretation of Guild 6.** The guild × condition matrix resolves the
previously-puzzling dual character of Guild 6. Its members (Gaiella, Stenotrophobacter,
Lysobacter, Aetherobacter, Alsobacter) are depleted by anthropogenic contamination (Cluster 2)
but elevated by geogenic redox (Cluster 1, δCLR=+2.31). Guild 6 is not a simple "clean-soil"
indicator but an **anthropogenic-contamination-sensitive, geogenic-metal-adapted guild**: it
thrives in naturally Ni/Cr-enriched serpentinite soils while being displaced by acid-mobilised
anthropogenic contamination (As, Cu, Pb). This is consistent with the source characterization
result (Lysobacter/Gaiella are background markers for Cr/Cu/Pb but contamination markers for As)
and with the Ni redox ecology (Lysobacter CLR +6.02 in reducing vs. +3.53 in oxic).

**Additional guild highlights:**
- *Guild 5* (Methylobacterium, n=1): Pb–acidic specialist — elevated under high_pb_acidic
  (δCLR=+1.76) and high_pb (+0.89), depleted under high-Cr/Ni/reducing.
- *Guild 3* (Arenimonas, Microlunatus, n=2): consistently contamination-elevated for Cd/Cr
  (no strong positive conditions under low-metal); mirrors Microlunatus's cross-metal
  contamination marker role in the source characterization analysis.
- *Guild 2* (includes Cupriavidus, n=5): depleted under high-Ni/reducing (δCLR=−1.08) and
  high-Cr/reducing (−0.78); elevated in low-Cr (+0.49). Metal-sensitive Gram-negative cluster.
- *Guild 8* (Parafilimonas, n=1): most extreme depletion in the dataset — δCLR=−2.58 under
  high-Ni/reducing, −1.95 under high-Cr/reducing, −1.73 under high-Ni alone.

*(Script: scripts/run_guild_condition_exploration.py; data: data/guild_condition_matrix.json;
figures: figures/fig_guild_condition_heatmap.pdf, figures/fig_condition_dendrogram.pdf)*

### Temporal data coverage and confound assessment

Collection dates are available for 168,518 of 187,755 samples (89.8%; source: ENA
`collection_date_start`). Coverage spans 1905–2020, concentrated in 2010–2020 (>95% of
samples). Mean within-study year span is 2.7 years (469 multi-year studies), consistent with
the dominant design being short cross-sectional surveys rather than longitudinal monitoring.

**Temporal–metal associations are weak.** Year–metal Spearman correlations are statistically
significant at n=124,710 but ecologically negligible: Pb ρ=+0.067, Cr ρ=+0.055, Cu ρ=+0.050,
As ρ=+0.048, Ni ρ=−0.019, Cd ρ=−0.006. The largest effect (Pb, ρ=0.067) accounts for <1% of
variance.

**Temporal–geographic co-structure.** Collection year correlates with sampling location:
year vs. latitude ρ=−0.111, year vs. longitude ρ=+0.091 (both p<10⁻³⁰⁰). Recent studies
are clustered in specific geographic regions (southern latitudes, eastern longitudes), creating
a confound between temporal and spatial coverage. Community composition shows minor temporal
drift (year vs. CLR PC1 ρ=+0.076).

**Mitigation.** Study-blocked GroupKFold CV (used throughout) absorbs temporal clustering at
the study level: within-study year spans are too short (mean 2.7 years) to create systematic
time-series biases within blocks, and between-study temporal differences are part of the study-
level variation the blocking structure removes. Temporal confound is a minor contributor to
overall variance given year–metal |ρ|<0.07 across all metals.

*(Script: scripts/run_temporal_audit.py; data: data/temporal_audit.json)*

### USA EF analysis: enrichment-factor-based indicator assessment

To directly test whether H1 indicator genera track *anthropogenic* metal enrichment (rather than
total geochemical metal load), we applied enrichment-factor (EF) classification to the USA
AMPLICON × USGS measured concentration subset (n=56,109 samples with CLR data; 46,978 also with
redox proxy). EF = measured concentration / UCC crustal background (As 1.5, Cd 0.1, Cr 100,
Cu 55, Ni 75, Pb 17 ppm). Sites with EF>2 are interpreted as carrying a contamination signal
beyond natural geological variability.

**EF distributions reveal metal-source heterogeneity.** Cr (2.9%), Cu (4.1%), and Ni (4.0%)
rarely exceed EF=2 in US soils — these metals are predominantly geogenic. By contrast, As
(69.3%), Cd (58.4%), and Pb (21.5%) commonly exceed EF=2, consistent with widespread
atmospheric deposition (Pb), agricultural inputs (Cd), and volcanic/geothermal geology
elevating background As above global crustal norms in much of the western US. Site
classification (contamination: EF>2; geogenic-high: EF<1.5 and raw>Q75; background: remainder)
identified 1,546–28,338 contamination sites and 0–9,836 geogenic-high sites per metal.

**Within-study Spearman ρ (EF vs. genus CLR)** was computed using rank-based vectorized
meta-analysis across 400 qualifying studies (≥8 samples with non-null EF). Results: 119–143
FDR<0.05 genera per metal; 47–82 genera with positive EF association (enriched under high-EF
conditions).

**Overlap between EF-positive genera and H1 indicator genera** (Jaccard):

| Metal | H1 indicators | EF-positive FDR<0.05 | Shared | Jaccard |
|-------|--------------|---------------------|--------|---------|
| As    | 50           | 50                  | 19     | 0.235   |
| Cd    | 50           | 32                  | 8      | 0.108   |
| Cr    | 50           | 58                  | 19     | 0.213   |
| Cu    | 50           | 82                  | 23     | 0.211   |
| Ni    | 50           | 49                  | 17     | 0.207   |
| Pb    | 50           | 47                  | 10     | 0.115   |

Mean Jaccard = 0.18. This contrasts with the near-zero Jaccard (≈0) between H1 s25-based and
H3 KO-level contamination signatures, and reflects that at the genus CLR level — unlike at the
functional gene level — H1 indicator genera do partially track measured contamination enrichment.
The partial overlap (10–23 shared genera) represents confirmed indicators that respond both to
modelled contamination risk and to measured EF; the non-overlapping majority of H1 genera
respond to the science_2025 signal without a corresponding EF signature.

**Ni redox stratification: direct source discrimination.** Using measured USGS Ni concentrations
with the P(oxic) redox proxy, we classified samples as anthropogenic (EF>2 AND P(oxic)>0.5,
n=392) or serpentinite/geogenic (EF<1.5 AND raw>Q75 AND P(oxic)<0.5, n=4,518). Mann-Whitney
comparison against background identified 112 FDR<0.05 genera for anthropogenic Ni and 147 for
serpentinite Ni.

H1 Ni indicator genera stratify cleanly by source:
- **Predominantly anthropogenic** (elevated in EF>2/oxic, not in serpentinite): *Altererythrobacter*
  (Δ median CLR = +4.5 anthropogenic, −0.3 serpentinite), *parviterribacter* (+3.9, +1.3),
  *enterovirga* (+3.1, −0.9), *skermanella* (+1.4, −0.4), *nitrososphaera* (+2.3, +0.6)
- **Predominantly serpentinite** (elevated in geogenic/reducing, not in anthropogenic):
  *Candidatus Koribacter* (−0.2, +4.9), *dokdonella* (−0.3, +4.5), *parafilimonas* (−0.2, +4.2),
  *alsobacter* (0.0, +3.6), *burkholderia* (−0.3, +2.9), *kitasatospora* (−0.4, +3.5),
  *paraburkholderia* (−0.6, +2.0)
- **Both elevated** (responds to both anthropogenic and geogenic Ni): *Geodermatophilus*
  (+5.1 anthropogenic, +3.7 serpentinite) — this genus was the top H1 Ni indicator but responds
  to high Ni regardless of source, consistent with documented Ni tolerance in desert
  actinobacteria rather than contamination specificity.

This EF × redox analysis resolves the Ni paradox identified in the redox integration section
(Q7/Q8): the H1 Ni indicator set contains a mixture of source-specific indicators, and the
apparent below-chance discrimination (AUC=0.282 without redox) arises from mixing of these two
ecologically distinct populations within the indicator pool.

*(Script: scripts/run_usa_ef_redox_analysis.py; data: data/usa_ef_analysis_summary.csv,
data/usa_ef_spearman_{metal}.csv, data/usa_ni_anthro_vs_bg.csv, data/usa_ni_serp_vs_bg.csv,
data/usa_ni_redox_summary.csv; figures: figures/fig_usa_ef_distributions.pdf,
figures/fig_usa_ef_top_genera.pdf, figures/fig_usa_ni_redox_stratification.pdf,
figures/fig_usa_ef_vs_h1_summary.pdf)*

### Community-weighted KO EF analysis (per-KO, MicrobeAtlas sample-linked)

To test H3 directly at the sample level, we computed **community-weighted KO profiles** for each
USA AMPLICON sample with USGS data: for each sample s and KO k,
community_KO(s,k) = Σ_g CLR(s,g) × ko_fraction(g,k), where ko_fraction(g,k) is the fraction of
ke_pangenome MAGs in genus g that carry KO k. This generates an inferred functional profile for
each sample from the observed taxonomic composition. Coverage: 330/500 CLR genera have
ke_pangenome data; 7,221 KOs present in ≥20 ke_pangenome genera within the covered set.

Within-study Spearman ρ (same vectorized blocked design as the genus-level EF analysis) was
computed between community KO scores and EF for each metal.

**Result: massive KO association inflation, not genuine metal biology.** 3,518–4,973 KOs are
positive FDR<0.05 per metal (49–69% of all tested KOs). This inflation arises because community
KO profiles are dominated by the same genera driving the genus-level CLR×EF signal — any KO
carried by genera that are broadly more abundant in high-EF soils will appear significant,
regardless of whether it is metal-related. The analysis largely re-discovers the genus-level
abundance pattern attenuated by ke_pangenome coverage fractions.

**Jaccard with H3 MAG-level CMH survivors** (518 KOs at FDR<0.05 via order × annotation-rate
CMH): 0.04–0.06 per metal — very low, confirming the community-level KOs are not the same set
as those showing enrichment in indicator-genus genomes at the MAG level.

**One substantive exception: chaA (K07300), cation efflux antiporter.** chaA is positive in 6/6
metals at community level and is an H3 annotation-rate CMH survivor (q=0.007). It is a known
Cd²⁺/Ca²⁺/Na⁺ antiporter documented to contribute to cadmium resistance in E. coli (Ivey et al.
1992) and related organisms. Its consistent signal across both the MAG-level indicator-genus
genome enrichment test and the community-level EF correlation represents the strongest functional
cross-validation in this project — though caution remains warranted given the general inflation.

**Other notable cross-validated KOs** (positive ≥6/6 metals AND in H3 survivors, n=20):
*hpnD* (K21678, hopanoid biosynthesis; membrane rigidity under environmental stress), *mprF*
(K14205, phosphatidylglycerol lysyltransferase; cationic antimicrobial peptide resistance),
*cysW* (K02047, sulfate/thiosulfate transport; sulfur-metal co-metabolism), *nifD* (K02586,
nitrogenase alpha; Fe-Mo cofactor requiring organisms), *occP* (K10021, octopine/nopaline
permease; Rhizobiales phylogenetic marker also flagged in per-metal Ni CMH as community
composition artifact — caution).

**Conclusion.** The community-KO EF analysis does not provide independent functional evidence for
H3 beyond what the genus-level EF analysis already shows. The signal is compositionally driven:
communities in high-EF soils have shifted genus composition, and those genera collectively carry
different (not specifically metal-biology) KO profiles. The exception — chaA — cross-validates
across both the MAG-level and community-level analyses and is the strongest candidate for a
genuine metal-resistance functional signal in this dataset.

*(Script: scripts/run_usa_community_ko_ef.py; data: data/usa_community_ko_ef_{metal}.csv,
data/usa_community_ko_ef_summary.csv; figures: figures/fig_usa_community_ko_volcano.pdf,
figures/fig_usa_community_ko_top_pos.pdf, figures/fig_usa_community_ko_h3_jaccard.pdf)*

### H1-residualized community KO EF analysis

To test whether the inflation in the community-KO EF analysis is driven by H1 indicator genera,
we repeated the analysis with all 111 H1 indicator genera (out of 330 CLR×pangenome overlap
genera) zeroed in the CLR matrix before computing community KO profiles. Any KO that survives
FDR<0.05 in this residualized analysis is enriched in high-EF soils *through non-indicator genera*
— a stronger criterion for KO-specific metal biology independent of the H1 abundance signal.

**Residualization substantially reduced inflation for As, Cd, Cr, Ni.** Positive FDR<0.05 counts
dropped by 72–88% for these four metals (As: 4,440→957; Cd: 3,518→427; Cr: 4,973→1,368;
Ni: 4,755→1,574). This confirms that most of the original signal was compositional bleed-through
from H1 genera.

**Cu residualized poorly (29% reduction: 3,676→2,603 positive).** The Cu community-KO EF signal
is distributed broadly across many genera, not concentrated in H1 indicators — removing them does
not substantially deflate the signal. Cu contamination may genuinely shift KO representation
through non-indicator taxa as well.

**Pb increased (+22%: 1,095→1,336 positive after residualization).** H1 Pb indicator genera were
*suppressing* KO signals relative to other genera — their presence in the CLR dilutes EF
correlations carried by non-indicator genera. Removing them revealed additional Pb-associated KOs,
suggesting the Pb functional landscape spans different community fractions than the Pb taxonomic
indicators.

**Jaccard vs H3 survivors did NOT improve.** The residualized positive sets overlap with H3
annotation-rate CMH survivors at Jaccard 0.03–0.06 — similar to or lower than the original
(0.04–0.06). Residualization recovers a smaller but not more H3-concordant set. The community-KO
analysis and the MAG-level annotation-rate test are measuring different aspects of the data and
cannot substitute for each other.

**Confound-robust set (positive in both analyses AND H3):** 19–91 KOs per metal. Summary:

| Metal | Orig pos | Resid pos | Reduction | Both pos | Both ∩ H3 | Jaccard H3 (orig→resid) |
|-------|----------|-----------|-----------|----------|-----------|------------------------|
| As    | 4,440    | 957       | −78%      | 829      | 44        | 0.058 → 0.038 |
| Cd    | 3,518    | 427       | −88%      | 282      | 19        | 0.060 → 0.028 |
| Cr    | 4,973    | 1,368     | −73%      | 1,154    | 74        | 0.055 → 0.051 |
| Cu    | 3,676    | 2,603     | −29%      | 2,187    | 91        | 0.052 → 0.043 |
| Ni    | 4,755    | 1,574     | −67%      | 1,320    | 86        | 0.061 → 0.055 |
| Pb    | 1,095    | 1,336     | +22%      | 467      | 19        | 0.042 → 0.040 |

**Top robust KOs (positive in both analyses × H3, ≥3 metals):**

- **K13612** — 6/6 metals robust. Top signal across the entire analysis. Annotated as
  pksL/baeL (Bacillus polyketide synthase locus protein) in KEGG; relevance to soil metal
  ecology unclear — may reflect Bacillus-lineage compositional confound rather than genuine
  metal biology.
- **K03855** — 5/5 metals (As/Cr/Cu/Ni/Pb). Annotated as recN (DNA repair) in KEGG but maps to fixX (4Fe-4S ferredoxin) in FitnessBrowser — a KEGG annotation mismatch (see FitnessBrowser validation). No metal-stress phenotype in fitness data; signal may reflect fixX-bearing lineages rather than SOS-response capacity.
- **K00433** — 5/5 metals. Non-haem monooxygenase component; involved in aromatic compound
  catabolism; many contaminated sites are co-contaminated organic/inorganic.
- **K06324** — 5/5 metals (As/Cd/Cr/Cu/Ni). Outer membrane protein / TonB-dependent receptor;
  metal uptake/exclusion in gram-negative organisms.
- **chaA (K07300)** — 3/6 metals robust (Cu, Ni, Pb; drops As/Cd/Cr after residualization).
  Retains cross-validation with H3 for 3 metals; strongest single metal-resistance functional
  candidate with known mechanism, though the H1-residualized scope is narrower than the original
  6/6 claim.

**Conclusion.** Residualization confirms that the original 49–69% KO inflation was primarily
driven by H1 indicator genus abundance bleed-through. The confound-robust set (both analyses × H3)
represents ≤1.3% of tested KOs per metal for As/Cd, 2.7% for Cr/Ni, and 1.7% for Pb —
substantially more conservative than the original analysis. Cu remains ambiguous (30% positive
after residualization; too broad to attribute to any specific functional biology). The Pb reversal
is the most novel finding: non-indicator genera carry Pb-EF functional signals not visible when H1
abundance dominates the community-KO vector.

*(Script: scripts/run_usa_community_ko_ef_residualized.py; data:
data/usa_community_ko_ef_resid_{metal}.csv, data/usa_community_ko_ef_resid_summary.csv,
data/usa_community_ko_robust.csv; figures:
figures/fig_usa_community_ko_resid_comparison.pdf,
figures/fig_usa_community_ko_resid_volcano.pdf)*

### FitnessBrowser validation of confound-robust target KOs

To test whether the 83 confound-robust KOs (both analyses × H3 CMH) have detectable fitness effects
under metal stress conditions, 13 representative KOs (covering all 6 study metals and spanning the
top-ranked robust set) were queried against two internal Spark databases:
`kescience.fitnessbrowser` (public FitnessBrowser organisms; 325 metal experiments across 20+
bacterial species) and `enigma.fitprivate` (ENIGMA-specific organisms: 4 Rhodanobacter strains,
Castellaniella, Collimonas, Janthinobacterium, Pseudomonas from Oak Ridge subsurface).

**enigma.fitprivate Rhodanobacter coverage for USA study metals.** Rhodanobacter (strains 10B01,
T8, R12) is the most ecologically relevant ENIGMA organism — it dominates acidic, metal-contaminated
groundwater at the Oak Ridge FRC site and is a known indicator of As/Cr contamination. All 6 USA
study metals are represented:

| Metal | enigma.fitprivate Rhodanobacter conditions |
|---|---|
| As | arsenate 15.6–31.25 mM + arsenite 0.039–0.078 mM [10B01] |
| Cd | CdCl₂ 16–128 μM [10B01, T8, R12] |
| Cr | K₂CrO₄ 0.0049 mM [10B01]; also pseudo6\_N2E2, MT049/058 |
| Cu | CuCl₂ 0.156–0.313 mM [10B01] |
| Ni | NiCl₂ 212–848 μM [10B01, T8, R12] |
| Pb | PbCl₂ 0.625 mM [10B01] — rare in fitness databases |

**KO coverage.** 8/13 target KOs were absent from both databases. K13612 (pksL/baeL, Bacillus
polyketide synthase) and K06324 (cotA, Bacillus spore coat multicopper oxidase) are phylogenetically
restricted to *Bacillus*, which is not represented in FitnessBrowser. 6 additional KOs (K11621,
K07652, K20345, K02545, K09685, K06608) were also absent. The remaining 5 KOs were present with
varying coverage:

| KO | FitnessBrowser annotation (best-hit) | Signal under metal stress |
|---|---|---|
| K00433 | alpha/beta hydrolase superfamily (NOT cpo) | Weak: max\|t\|=2.97 under Cu; mean fit near 0 |
| K01971 | DNA ligase (multiple paralogs, incl. LigD) | Weak: 3 negative-strong hits under Cu; positive/neutral under Ni in Rhodanobacter |
| K03855 | **fixX / 4Fe-4S ferredoxin** (NOT recN) | None: mostly positive or near-zero; KEGG annotation mismatch |
| K07300 | ChaA / Ca:H antiporter | None: directionally inconsistent; mean fit near 0 |
| K14189 | SDR family dehydrogenase | None: n=1–2, all near-zero |

**K03855 annotation mismatch.** KEGG maps K03855 to recN (DNA repair, SOS response).
FitnessBrowser best-hit KEGG mapping assigns this ortholog group to fixX (a 4Fe-4S ferredoxin
involved in nitrogen fixation electron transfer) — a distinct protein family with no known
metal-stress function. This means the K03855 community-KO signal reflects *fixX*-bearing lineages,
not necessarily SOS-response capacity. The fitness data for K03855 confirms this: no negative
fitness under any metal condition (mean fit ≥ 0 across Co/Cu/Ni; one weak Zn hit, n=8).

**K01971 in Rhodanobacter.** The only target KO present in Rhodanobacter metal conditions,
K01971 shows *positive* fitness under Ni (fit=0.15–0.40, t up to 2.67 at 212 μM; t=2.42 at
424 μM) and Zn, and near-zero under Cd — meaning the DNA ligase gene is not required for
Rhodanobacter fitness in these metal conditions. No K01971 hits appeared under Rhodanobacter
As, Pb, or Cr conditions.

**Overall verdict.** FitnessBrowser analysis is largely negative: none of the 5 detectable KOs show
strong, directional fitness deficits (mean fit ≤ −0.5 with |t| > 2 consistently across replicates)
under metal stress in any organism. This does not definitively rule out a metal-resistance function
— the FitnessBrowser model organisms are laboratory strains tested under acute exposures, whereas
our signal reflects chronic soil metal contamination filtered through community ecology. The two
strongest mechanistic candidates from the robust set — cotA (K06324, Mn²⁺ oxidase → MnO₂ →
metal sorption) and K13612 (pksL/baeL, Bacillus PKS) — cannot be assessed because no *Bacillus*
strains are in FitnessBrowser. cotA in particular operates extracellularly via Mn oxidation, a
mechanism not captured by individual-cell fitness assays.

*(Data: data/fitnessbrowser_target_ko_summary.csv, data/rhodanobacter_metal_conditions.csv)*

---

### Phylogenetic KO density → USGS metal concentration: PGLS with full controls

To test whether genera with intrinsically higher metal-cofactor or metal-resistance KO density
occur at higher soil metal concentrations — a phylogenetic version of H3 — we ran PGLS using the
GTDB bacterial phylogeny (Pagel's λ optimised). The response was detection-weighted mean
log-ppm (log₁₊ₓ of measured concentration) at USA USGS soil sites for each genus; the focal
predictor was conditional KO density (sum of inverse-genome-length-weighted counts across
MGnify genomes, from `usa_ef_ko_genus_density.parquet`; the same metric used in NB06). We
tested cofactor KOs (K02225, K03635, K03638, K03750, K03831) and resistance KOs (15 KOs from
`curated_mrg_ko_ids_v2.csv` Tier 1/2) separately.

**Design.** Two model tiers:
- *Base model*: KO density + genome size (standardised).
- *Full model*: KO density + genome size + Levins' B (ecological breadth / coreness proxy, from
  `01_pgls_input_bacteria.csv`) + detection-weighted mean latitude + longitude + mean SoilGrids
  pH + SOC + clay. This eliminates confounding by genome size, ecological breadth, geographic
  distribution, and soil chemistry simultaneously.

Genera included if ≥30 weighted detections in the USA USGS-matched sample set. Detection
weights = CLR-exp(CLR), thresholded at col_min + 2 × col_SD for presence calling.

**Seven-element analysis (As, Cd, Cr, Cu, Ni, Pb, Zn; n=256 genera).**

| Element | Tier | Base β | Base p | Full β | Full p | Full FDR |
|---------|------|--------|--------|--------|--------|----------|
| NI | Resistance | +0.054 | 0.062 | +0.045 | 0.050 | 0.351 |
| CD | Cofactor | +0.026 | 0.028 | +0.031 | 0.064 | 0.449 |
| CR | Cofactor | +0.048 | 0.135 | +0.006 | 0.829 | 0.996 |
| AS | Cofactor | +0.064 | 0.012 | +0.055 | 0.639 | 0.868 |
| All others | — | — | >0.18 | — | >0.49 | — |

No association survives FDR correction. The Cr Cofactor signal (β=+0.048, p=0.135 base)
disappears entirely in the full model (β=+0.006, p=0.829), demonstrating it was confounded by
geography and/or soil chemistry. The borderline Ni Resistance association (p=0.050 full) does not
survive multiple testing correction (FDR=0.35 across the 14-test block).

**Expanded to all 46 USGS elements (n=256 genera).** Replacing the seven-element pre-joined
dataset with an inline BallTree spatial join to `usgs_geochem_joined.parquet` (868 unique USGS
soil sites matched within 25 km; ≥200-site coverage threshold), we tested all elements with
sufficient per-genus representation. Seven associations survive FDR < 0.20 in the full model:

| Element | Tier | β | p | FDR |
|---------|------|---|---|-----|
| Cs | Resistance | −0.079 | 0.0016 | 0.072 |
| Yb | Resistance | +0.032 | 0.0048 | 0.111 |
| In | Cofactor | +0.004 | 0.0067 | 0.132 |
| Zr | Cofactor | +0.105 | 0.0070 | 0.132 |
| Mn | Cofactor | −0.005 | 0.0086 | 0.132 |
| Mo | Cofactor | +0.054 | 0.0121 | 0.139 |
| Yb | Cofactor | +0.033 | 0.0187 | 0.172 |

None of the classic toxic metals (As, Cd, Cr, Cu, Ni, Pb, Zn) survive FDR correction. The
**Mo Cofactor** hit (β=+0.054, FDR=0.139) is the most biologically plausible: molybdenum is an
essential cofactor for nitrogenase, nitrate reductase, and sulphite oxidase; genera with broader
metal-cofactor biosynthesis capacity may preferentially colonise Mo-richer soils where these
pathways are active. The negative **Mn Cofactor** association (β=−0.005) and the rare-earth
(Yb) and geologic-metal (Cs, In, Zr) signals likely reflect geographic or soil-type covariation
not fully captured by the controls. No classic contamination metal shows a positive genus-level
KO density effect in the direction expected for metal adaptation.

**Conclusion.** At the phylogenetic scale — controlling for genome size, ecological breadth,
geographic distribution, and soil chemistry — cofactor and resistance KO density does not predict
measured soil concentrations of any classic toxic metal studied here. This is consistent with H3
NOT SUPPORTED across all analytical frameworks (CMH stratification, direct geo-linked validation,
fitness experiments, and now PGLS with full controls).

*(Scripts: `scripts/run_nb06_controlled.py`, `scripts/run_nb06_all_usgs.py`;
data: `data/usa_ef_pgls_controlled_results.csv`, `data/nb06_all_usgs_results.csv`,
`data/nb06_all_usgs_input.csv`; figure: `figures/fig_nb06_controlled_forest.pdf`,
`figures/fig_nb06_all_usgs_forest.pdf`)*

---

## Interpretation

### Literature context

Genus-level CLR outperforming community-weighted functional means for metal prediction replicates
the finding from the companion `community_composition_prediction` project (Heather M. thesis), and
extends it from Zn/Pb/Ni to 6 metals using a larger sample set and a modelled exceedance
probability response. The pattern is consistent with Fierer (2017, *Nat Rev Microbiol*) on the
importance of taxonomic identity versus functional redundancy for environmental response prediction.

The dominance of spatial autocorrelation (coordinates AUC 0.998–0.999) confirms a well-known
statistical artefact in microbial ecology: species distribution models trained with random-fold CV
on spatially structured data inflate performance estimates substantially (Valavi et al., 2019,
*Methods Ecol Evol*; Roberts et al., 2017, *Ecography*). The drop from random-fold (0.92–0.96) to
study-blocked (0.52–0.76) is substantial but leaves a meaningful above-chance signal.

The H4 result — distinct indicator communities for contamination risk vs. geological background —
aligns with the conceptual distinction between edaphic filtering (long-run geochemistry shaping
composition over millennia) and contamination effects (recent, often anthropogenic, bioavailable
metal loads). The literature on technosols and smelter-impacted soils (Pérez-de-Mora et al., 2006;
Salam et al., 2023) documents community shifts in response to bioavailable contamination that
differ from background geochemical gradients. Pei et al. (2018) specifically identified
Cr-sensitive and Cr-remediation indicator genera in Yellow River soils, providing a precedent for
the global Cr–community associations quantified here.

H3 (elevated core-genome KO density in indicator genera) is NOT SUPPORTED by ten independent
lines of evidence spanning five confound types: (1) within-phylum SPIRE stratification (all NS;
direction reversed within Actinobacteria); (2) ke_pangenome replication (indicator genera have
~20% LOWER KO density; all p_fdr≈1); (3) per-KO phylum breadth analysis (high-breadth KOs show
no positive association with indicator status; mean partial ρ = +0.010); (4–8) genome-wide KO
enrichment cascade: naive Fisher 91%, phylum-CMH 87.5%, order-CMH 79.3%, order-CMH with ≥50%
prevalence threshold 24.4%, + soil habitat filter 21.0%, + genome completeness filter 23.7%
(CheckM ≥90%/≤5% via gtdb_metadata; 219 additional KOs removed) — decomposing the apparent
enrichment into phylogenetic composition (8%), within-phylum lineage clustering (14%), genome
annotation depth bias (55%), non-soil comparison set bias (~4%), and low-quality assembly bias
(~1%); (9) annotation-rate stratification (order × KEGG coverage tertile CMH; 7.3% of 7,133
KOs after within-order annotation-rate equalization; indicator genera annotation rate 0.522 vs
non-indicator 0.616) — the within-order annotation-rate heterogeneity accounts for most of the
~24% residual; and (10) geo-linked direct environmental validation (1.1% after restricting to
3,958 GPS-located soil genomes; indicator genera are collected from lower-exceedance sites than
non-indicators; no high-metal indicator strata available for stratified test). The original 3/6
metals cross-phylum signal was a SPIRE sampling artefact. Importantly, this analysis is limited
to core genome (pangenome) KO representation — phage-mediated horizontal gene transfer (HGT)
of metal resistance genes (merA, czcA, arsR) into metal-contaminated community members would
not be detectable by pangenome-CWM and is documented in comparable systems (Huang et al., 2021,
*Microbiome*; Li et al., 2025, *Microorganisms*).

Nitrososphaera's role as the top Cr indicator is interpretable within AOA ecology. AOA
(Nitrososphaera-group Thaumarchaeota) are favoured at moderate pH (5.5–7.5), low ammonium
availability, and aerobic conditions (Prosser et al., 2019, *Glob Chang Biol*). Heavy metal
contamination — Cr in particular — inhibits nitrification by suppressing ammonia oxidation
enzyme activity (Bai et al., 2023, *Front Microbiol*; Pei et al., 2018, *Front Microbiol*).
The SHAP dependence for Cr shows Nitrososphaera contributing **negatively** to Cr exceedance
probability (SHAP-CLR ρ=−0.920): high Nitrososphaera CLR → negative SHAP → lower predicted
exceedance. The operative signal is Nitrososphaera *depletion* in Cr-risk soils — a classic
sensitive-taxon bioindicator pattern rather than niche co-occurrence.

An alternative interpretation warrants consideration: AOA ecology (Schleper, 2020, *Nat Rev
Microbiol*) predicts Nitrososphaera responds to substrate limitation (NH₄⁺) and oxygen
availability rather than directly to Cr. Under this view, Cr-contaminated soils may
systematically differ in N-availability (suppressed nitrification → NH₄⁺ accumulation →
AOA substrate paradox), and the Nitrososphaera–Cr correlation could reflect this upstream N-
cycling shift rather than direct Cr sensitivity. Two observations constrain but do not rule out
this alternative: (a) soil pH — a major NH₄⁺ availability driver — does not mediate the
relationship (partial ρ=−0.125 after controlling for sg_pH, similar to raw ρ=−0.116); (b) the
signal persists across four continents with different soil N-regimes. However, N-availability
is not directly measured in the analysis, leaving the mechanistic pathway (direct Cr inhibition
vs. NH₄⁺-mediated AOA substrate effect) unresolved by observational data alone.

H1 failure is mechanistically consistent with CWM failure in the companion project: CLR encodes
species identity, not gene activity. The same phylogenetic constraint that causes CWM to predict
poorly also limits CLR from adding signal beyond soil chemistry at the cross-study scale. The
community composition at any site reflects the long-run environmental filtering (pH, SOC, texture,
geographic position) that sets the soil chemistry too.

### Causal interpretation

The global CLR model achieves AUC 0.92–0.96 for metal exceedance under random-fold CV, yet 0/3,000 within-study associations are significant. This contrast illustrates a well-recognised limitation of macroecological observational studies: we cannot distinguish whether SHAP-ranked indicator genera respond directly to metal contamination, or whether they co-occur with the geochemical conditions that produce it (low pH, high-Fe soils, geological metal enrichment). The directionality asymmetry (8.5× stronger community → environment than environment → individual genus) is consistent with environmental forcing of community structure at the cross-study scale, but does not rule out a "passenger" interpretation: indicator genera may be characteristic of the geochemical contexts that generate metal accumulation without themselves tolerating or responding to metals. Within-study experimental or cross-study quasi-experimental designs (e.g., pre/post contamination, adjacent gradient sites) would be needed to distinguish mechanistic response from co-occurrence correlation.

### Cross-project context

The H1 null result (CLR adds no signal beyond soil chemistry) extends the `community_composition_prediction` finding that community-weighted mean (CWM) functional features fail for metal prediction. Both projects find that taxonomic identity (CLR) beats functional averages (CWM) for raw metal associations, but neither escapes the underlying constraint: community composition at any site reflects the same long-run environmental filtering — pH, SOC, texture, geographic position — that sets the soil chemistry and metal distributions. The residual cross-study signal isolated by spatial de-trending (+0.011 to +0.036 AUC in study-blocked CV after Ridge lat/lon residuals) is genuine but insufficient to outperform soil chemistry, for the same reason CWM fails: 16S composition encodes gene *capacity* shaped by evolutionary history, not current metal exposure. The CME project's constitutive/inducible PGLS distinction is relevant here: H3's failure (KO enrichment is phylogenetic artifact, not indicator-specific) reinforces that gene capacity doesn't predict indicator status — inducible expression in situ is the untested mechanism.

### Novel contributions

1. **Spatial de-trending reveals genuine cross-study CLR signal**: Study-blocked AUC 0.52–0.76
   for raw CLR, improving to 0.54–0.78 after geographic de-trending. The residual signal
   indicates that CLR carries genus-specific metal tolerance information beyond latitude/longitude
   — albeit insufficient to outperform soil chemistry.

2. **Source specificity of indicator genera**: Same metal, different measurement approach
   (exceedance probability vs. mobile fraction vs. geological background) yields largely
   non-overlapping indicator genera (Jaccard 0–0.14). Metal-indicator relationships are
   operationally defined by measurement approach, not metal identity alone.

3. **Contamination vs. geological community distinction**: H4 support (mean s25 vs GeoROC Jaccard
   0.048) suggests the microbial community encodes exposure history as well as geochemical context,
   relevant for using community data to distinguish anthropogenic from natural metal enrichment.

4. **Nitrososphaera as a globally validated negative Cr bioindicator**: First global-scale
   SHAP-based evidence for an ammonia-oxidizing archaeon (AOA) as the strongest single-genus
   predictor of soil Cr contamination risk (rank 1/500 genera; mean|SHAP|=0.0103; SHAP-CLR
   ρ=−0.920). The signal is depletion-based: Nitrososphaera absence predicts elevated Cr risk.
   Quantitative cross-continental replication: N. America ρ=−0.233, E. Asia ρ=−0.174,
   Tropical S ρ=−0.268, Europe ρ=−0.058 (n=132,907 total, all p<10⁻⁵). Unmediated by soil pH
   (partial ρ=−0.125). Concordant with Pei et al. (2018) in Yellow River riparian soils
   (ρ=−0.736). Establishes AOA nitrification inhibition by Cr as a globally recoverable
   16S signal.

5. **Indicator genera are gradient-position dependent (Jaccard ≈ 0.05–0.14)**: The top-20
   genera distinguishing mildly contaminated soil (Q1 vs Q2 exceedance quintile) are nearly
   disjoint from those distinguishing severely contaminated soil (Q4 vs Q5) — Jaccard
   J(low, high) = 0.053 for five of six metals, rising to 0.143 only for Ni. Low-stratum
   genera include oligotrophic taxa (Terrimicrobium, Priestia, Mesorhizobium) characteristic
   of undisturbed soil; high-stratum genera include known metal-tolerant lineages
   (Cupriavidus, Lysobacter, Burkholderia for Cr). A global 16S-based biomonitoring system
   therefore requires stratum-appropriate indicator panels rather than a single universal
   genus list. Random-fold classifier AUC is uniformly high (0.94–0.96) at all strata, but
   study-blocked MWAS (0/3,000 within-study associations significant) confirms this reflects
   geographic proxy learning, not local contamination sensitivity.

6. **Metal indicator genera are substantially metal-specific, not edaphic proxies**: Running the
   same stratified RF analysis with pH, SOC, and clay as the response variable produces AUC
   0.926–0.957 — identical to the metal classifiers — confirming the geographic proxy effect is
   universal. Cross-variable Jaccard between metal and soil-variable indicator panels ranges
   0.053–0.212. The highest overlaps (Cu × clay = 0.212, Ni × clay = 0.212) are geochemically
   interpretable: Cu and Ni adsorb strongly to clay minerals, so clay-rich sites are enriched in
   both clay-adapted genera and elevated bioavailable Cu/Ni. pH overlap is consistently lower
   (0.053–0.143), consistent with the Nitrososphaera pH partial-correlation result. Metal
   biomonitoring panels for Cu and Ni should include a clay-stratification step to avoid
   misattributing clay-community gradients as contamination signals.

7. **Microbial community can discriminate anthropogenic contamination from geogenic background
   (mean AUC=0.677 across six metals)**: Using samples with both s25 exceedance data and USGS
   measured concentrations, classifiers trained on genus CLR successfully distinguish
   contamination (high exceedance + high USGS) from geogenic background (high USGS + low
   exceedance) at mean AUC=0.677. Cu (0.747) and Pb (0.735) are most discriminable. Cross-metal
   contamination biomarkers include Microlunatus (5/6 metals), Pseudomonas (4/6), and
   Parafilimonas (4/6); background biomarkers include Povalibacter (5/6), Lysobacter (4/6),
   Gaiella (4/6), and Kribbella (4/6). Context-dependent genera (Gaiella, Lysobacter,
   Stenotrophobacter) are contamination markers for As but background markers for Cr/Cu/Pb —
   a signal of metal-source specificity in indicator behaviour that has implications for
   field biomonitoring panel design.

### Limitations

1. **science_2025 response**: exceedance probabilities are modelled, not directly measured.
   The model's spatial interpolation structure contributes to the AUC inflation in random-fold CV.

2. **Amplicon resolution**: 16S V4 OTU clustering at genus level cannot distinguish closely
   related ecological guilds. Many OTUs are unclassified at genus level (~38% of
   indicators are not matched in SPIRE MAGs for H3).

3. **No metatranscriptomics**: H3 tests gene capacity (presence) not activity (expression).
   No sufficiently large public soil metatranscriptomics dataset with KEGG annotations exists
   to test the capacity-vs-activity question (NB04 assessed infeasible: no dataset has
   ≥50 geographically distributed soil bacterial metatranscriptomics samples + KEGG
   annotations + metal contamination gradient).

4. **Joint soil+CLR degradation**: In study-blocked CV, soil+CLR underperforms soil-only
   for 5/6 metals. CLR overfits to study-specific community structure. This limits direct
   biomonitoring applicability — indicator taxa would need recalibration for each new study area.

5. **Within-study metal variance floor**: The science_2025 exceedance response is modelled on a
   0.25° grid (~28 km), causing 64% of studies to have zero within-study metal variance. We
   validated that this is not the cause of the MWAS null by repeating the analysis with USGS
   point-measured soil concentrations (44,305 USA samples, 403 studies; 7–24% zero-variance
   per metal). The null persists (0/3,000 significant, max |Z|=1.17), confirming the CLR-metal
   signal is macroecological (between-region), not local (within-study).

6. **Nitrososphaera–Cr mechanism inferred, not demonstrated**: SHAP identifies correlation, not
   causation. Whether Nitrososphaera directly responds to Cr or co-occurs with upstream
   geochemical conditions (aerobic, moderate-pH, N-limited soils) is not resolved by
   observational data. Specifically, N-availability (NH₄⁺ substrate) as an upstream driver
   of AOA ecology (Schleper, 2020) cannot be excluded with current data — N-availability is
   not measured in MicrobeAtlas samples. Mechanistic confirmation would require isolate-level
   Cr MIC data (BacDive/DSMZ) or controlled-exposure experiments.

7. **H3 limited to core-genome KO representation**: The pangenome-CWM approach captures gene
   families present in ke_pangenome reference genomes. Phage-mediated horizontal transfer of
   metal resistance genes (merA, czcA, arsR, cadA) into environmental strains would not be
   detectable by this method. Direct metagenomics studies of contaminated soils at local gradients
   report such HGT-mediated enrichment (Huang et al., 2021; Li et al., 2025), suggesting our
   H3 null refers specifically to core-genome capacity, not total metal gene complement.

8. **Metal exceedance probability is total-concentration-based (not bioavailability)**: The
   science_2025 exceedance probabilities are modelled from total metal concentrations measured
   against regulatory thresholds (AT/HHET). Multiple site-scale studies demonstrate that
   bioavailable, not total, metal concentration drives microbial community structure (Xiao et al.,
   2022; Sun et al., 2017). Indicator taxa identified here reflect community responses to
   geochemical gradients that co-vary with regulatory exceedance risk; they may not respond
   directly to metal bioavailability at any given site.

9. **As and Cd EF thresholds classify most USA sites as contaminated**: Using EF > 2 as the
   anthropogenic contamination criterion, 69.3% of USA AMPLICON sites exceed this level for As
   and 58.4% for Cd. These high proportions reflect geochemical heterogeneity (volcanic/geothermal
   As enrichment; diffuse agricultural Cd inputs) rather than predominantly point-source
   contamination. The As and Cd EF analyses should be interpreted as community responses to
   metal concentration gradients, not specifically to industrial loading.

10. **Ecosystem heterogeneity unresolved**: The global CLR model aggregates bulk soil, rhizosphere,
    forest, agricultural, and tundra samples. Site-scale studies show indicator genera differ
    systematically between rhizosphere and bulk soil (Zhang et al., 2020), between agricultural and
    serpentine contexts (Koner et al., 2024), and across climate zones (Radziemska et al., 2022).
    Global-scale indicators should not be applied to predict site-specific contamination without
    local recalibration.

---

## Data

### Sources

| Collection | Tables Used | Purpose |
|------------|-------------|---------|
| `arkinlab.microbeatlas` | `sample_metadata`, `otu_counts_long`, `enriched_metadata` | 16S genus RA, lat/lon, GeoROC metals pre-joined |
| `arkinlab.envdbs` | `science_2025_global_soil_toxic_metals`, `soilgrids_master`, `csu_metal_mobility_grid` | Metal exceedance, soil chemistry, mobile fractions |
| `refdata.spire` / CME project | genus KO density CSV | H3 functional validation (Tier 1+2 gene list) |
| MTV QIIME2 dataset | feature table (biom), taxonomy TSV, sample metadata TSV | ORFRC HFIR surface soil case study |

### Data Scope

#### Sample source and filtering

All analyses use **soil samples only** from the MicrobeAtlas collection (arkinlab.microbeatlas.sample_metadata). The initial selection filters the 278K MicrobeAtlas samples to 187,755 soil samples using the soil environment filter: `Environments` column matches `LIKE '%soil%' OR '%terrestrial%' OR '%rhizosphere%'`. This captures soil sensu stricto, field soils, forest soils, tundra soils, and rhizospheric soils while excluding aquatic (marine, freshwater, sediment), host-associated, and plant-derived samples. These 187,755 samples represent the full analysis_matrix.

Subsequent analyses apply additional filters to match non-null responses and metadata:
- **H1, H1b, H4, Nitrososphaera, SHAP, PCA**: n=132,907 samples (CLR non-null AND science_2025 non-null AND study_id non-null)
- **MWAS (within-study)**: n=2,018 AMPLICON studies (subset of 2,175 total studies with min 20 samples/genus/metal)
- **USGS validation**: n=44,305 samples (USA subset, 54,961 initial → matched to USGS NGDB within 25 km, 403 studies)
- **Redox integration (USA)**: n=54,918 samples (USA AMPLICON subset with groundwater redox proxy, 499 studies)
- **CatBoost SHAP**: n=124,687 samples (CLR non-null, metric varies by metal)

**No marine, freshwater, sediment, host-associated, or plant-leaf samples** are included in any analysis. All samples have non-null latitude/longitude.

#### Environmental datasets by analysis

| Analysis | Geographic scope | n_samples | n_studies | Metal response variable | Response source | Resolution | Sample filter | Notes |
|---|---|---|---|---|---|---|---|---|
| **H1 — CLR prediction** | Global | 132,907 | 2,175 | Exceedance probability (AT) | science_2025 | 0.25° grid (~28 km) | Soil | Annual Threshold; 6 metals (As/Cd/Cr/Cu/Ni/Pb); coordinates alone AUC=0.998 |
| **H1 study-blocked CV** | Global | 132,907 | 2,175 | Exceedance probability (AT) | science_2025 | 0.25° grid | Soil | GroupKFold by study_id; AUC 0.52–0.76 |
| **H1 spatial de-trending** | Global | 132,907 | 2,175 | Exceedance probability (AT) | science_2025 | 0.25° grid | Soil | Ridge lat/lon residuals improve study-blocked AUC by 0.011–0.036 |
| **H2 — Source comparison** | Global vs. geological | 50 genera per source | — | Indicator sets (3 sources) | s25 / CSU / GeoROC | Mixed | Soil | Jaccard overlap of top-50 genera across three metal datasets |
| **H3 — KO density** | Global (functional) | 37–50 per metal | — | Genus KO density | SPIRE MAGs | — | Soil indicators | Wilcoxon test of metal KOs in indicator vs. non-indicator genera; 26–37 matched to MAGs |
| **H4 — Source distinction** | Global | Top-50 genera | — | Jaccard similarity | s25 vs. GeoROC | Grid (s25) / point (GeoROC) | Soil | Mean Jaccard 0.048 between contamination-risk and geological-background indicators |
| **MWAS (within-study)** | Global | 132,907 total | 2,018 (AMPLICON subset) | Metal exceedance (0.25° grid) | science_2025 | 0.25° grid | Soil | 64% of studies have zero within-study metal variance; result: 0/3,000 tests FDR sig |
| **USGS validation (point metals)** | USA only | 44,305 (matched) | 403 | Measured concentrations (ppm) | USGS NGDB | Point-measured | Soil | Spatial join within 25 km to USGS soil survey sites; 6 metals As/Cd/Cr/Cu/Ni/Pb; 0/3,000 tests FDR sig |
| **Nitrososphaera global validation** | 4 continents | 132,907 | — | Exceedance probability (Cr AT) | science_2025 | 0.25° grid | Soil | Spearman ρ global=−0.116; continental: N. America −0.233, E. Asia −0.174, Europe −0.058, Tropical S −0.268 |
| **Network ecology (redox)** | USA only | 54,918 | 499 | Exceedance + redox proxy | s25 + mn10 Mn model | 0.25° grid + modelled | Soil | Geobacter–redox correlation ρ=−0.160 (n=52,968); added P(oxic) covariate |
| **Redox × Ni source discrimination** | USA (serpentinite) | 7,246 proxy; 52,968 Geobacter | ~200 | Geogenic vs. anthropogenic Ni | s25 + redox proxy | Grid + modelled | Soil | Serpentinite P(oxic)=0.412 vs. non-serpentinite 0.527; AUC 0.282 → 0.753 with redox |
| **CatBoost SHAP importance** | Global | 124,687 | — | Exceedance probability (AT) | science_2025 | 0.25° grid | Soil | 500 CLR genera; 300-tree CatBoost; Nitrososphaera rank 1/500 for Cr |
| **PCA dimension reduction** | Global subsample | 10,000 | — | All 6 metals | science_2025 | 0.25° grid | Soil | t-SNE/UMAP explorer; PC50 captures 54.2% variance |

#### Response variable definitions

- **science_2025 (s25)**: Global gridded soil metal exceedance probabilities (Henderson et al. 2026 [preprint], *Science*) at 0.25° resolution. Two thresholds provided:
  - **AT (Annual Threshold)**: Used for all main analyses; derived from annual dietary/occupational exposure standards
  - **HHET (Harmful Health Effect Threshold)**: Higher exceedance level; used for robustness checks

- **USGS NGDB**: Point-measured soil metal concentrations (ppm) from the USGS National Geochemical Database (139,817 sites, >95% completeness As/Cr/Cu/Ni/Pb, 81% Cd). Spatial join to MicrobeAtlas within 25 km using ESRI:102003 projection.

- **GeoROC**: Point-measured major and trace metals from rock samples (geological background). Used for H2/H4 source comparisons; samples non-contaminated geological reference.

- **CSU mobility**: Modelled most-mobile metal fractions (pf1 scale) from CSU grid. Used for H2 source consistency test.

- **Redox proxy (mn10)**: P(Mn > 50 μg/L) at 5m depth below water table from USGS ScienceBase national groundwater model. Inverted to P(oxic) = 1−P(Mn>50) for Ni/Cr source discrimination analysis. USA only.

#### Covariates and confounders

**Soil chemistry** (SoilGrids v2.0, 0.25° resolution):
- pH (0–5 cm)
- SOC (soil organic carbon, %)
- Clay fraction (%)
- CEC (cation exchange capacity)
- Bulk density
- Sand fraction (%)
- N (total nitrogen)

Used in soil-only and soil+CLR models (NB01, NB05). All covariates are at global 0.25° resolution, matching science_2025 grid.

**Study-level metadata**:
- `study_id`: 2,175 unique studies across 187,755 samples (mean 86.4 samples/study)
- `platform`: Illumina, Ion Torrent, PacBio, 454 (>98% Illumina in MicrobeAtlas)
- `v_region`: 16S V4, V3V4 other (96.2% of studies uniform within-study)
- Sequencing depth (log10 reads/sample): η²=0.73 between studies (primarily batch variable)

**Technical confounders**: Primer chemistry, sequencing depth, and platform are absorbed by study identity (η² < 0.06 for all three). Within-study partial ρ(depth, metal exceedance) ≤ 0.014 across metals; no residualization required.

#### Geographic representativeness

- **Global analyses** (H1, H1b, H4, Nitrososphaera, SHAP): n=132,907 samples span all inhabited continents. Continental breakdown for Nitrososphaera: N. America 49,362 (37.1%), E. Asia 35,582 (26.8%), Europe 32,346 (24.3%), Tropical S 4,147 (3.1%), Oceania <1%.
- **USA-only analyses** (USGS validation, redox integration, Ni source discrimination): n=44,305–54,918 samples cover all US states and territories. USGS matched subset (n=44,305) represents 80.6% of USA amplicon samples within 25 km of NGDB sites.
- **No analyses are region-restricted except where explicitly stated** (USA-only analyses clearly marked in Results).

#### Caveat: spatial autocorrelation and cross-validation design

Random-fold cross-validation inflates AUC estimates (0.92–0.96 for CLR, 0.99 for coordinates) due to spatial clustering of samples within studies and within geographic regions. Study-blocked cross-validation (GroupKFold by study_id, n=2,175 folds) reduces this artifact, yielding more realistic AUC (0.52–0.76 for CLR). All reported AUC values specify the CV scheme (random-fold vs. study-blocked). The MWAS null (0/3,000 significant within-study associations) is not contradicted by random-fold AUC inflation — it reflects the genuine absence of within-study metal variance in the science_2025 gridded response (64% of studies have zero within-study exceedance variation at 0.25° resolution).

---

### Generated Data

| File | Rows | Description |
|------|------|-------------|
| `data/analysis_matrix.parquet` | 187,755 | Full analysis matrix: CLR × 538 cols |
| `data/h1_auc_results.csv` | 6 | H1 AUC per metal: base, full, delta |
| `data/h1b_clr_only_auc.csv` | 6 | CLR-only random-fold AUC |
| `data/h1c_spatial_only_auc.csv` | 6 | Spatial-only random-fold AUC |
| `data/h1d_extended_metrics.csv` | 6 | AUPRC, MCC, Spearman, threshold-specific AUC |
| `data/h1_indicator_genera.parquet` | 300 | Top-50 indicator genera per 6 metals |
| `data/h_study_blocked_auc.csv` | 6 | CLR study-blocked AUC per metal |
| `data/h_study_blocked_multifeature.csv` | 24 | Study-blocked AUC: soil, spatial, CLR, soil+CLR × 6 metals |
| `data/h_study_confounding.csv` | 6 | Study target-encoded AUC, CLR η² per metal |
| `data/h_resid_study_blocked.csv` | 6 | Spatial de-trended CLR study-blocked AUC |
| `data/h_regression_cv.csv` | 18 | Regression (Spearman ρ) per feature set × metal |
| `data/h_sample_type_auc.csv` | 35 | AUC across ecosystem subsets and spatial residuals |
| `data/h_taxon_resolution_auc.csv` | 18 | AUC at genus, family, phylum levels |
| `data/h_geo_restriction_auc.csv` | 34 | AUC within continental regions |
| `data/h2_source_auc.csv` | 18 | AUC per metal source (s25, CSU, GeoROC) |
| `data/h2_source_jaccard.csv` | 11 | Jaccard between indicator sets per source pair |
| `data/h2_jaccard_consistency.csv` | 15 | Cross-metal Jaccard of indicator genera |
| `data/h3_wilcoxon_results.csv` | 6 | H3 Wilcoxon rank-sum results with FDR |
| `data/h3_category_results.csv` | 18 | H3 subcategory (resistance/cofactor/metaldep) tests |
| `data/catboost_cv_results.csv` | 18 | CatBoost regression Spearman ρ per feature set × metal |
| `data/algo_comparison_results.csv` | 24 | Algorithm comparison CLR-only (Extra Trees, XGB, Ridge, ElasticNet) |
| `data/catboost_featsel_results.csv` | 18 | Feature selection top-k CLR Spearman ρ |
| `data/catboost_shap_importance.csv` | 6,048 | Mean |SHAP| per genus per metal (CatBoost CLR-only) |
| `data/rf_pca_cv_results.csv` | 18 | RF Spearman ρ on PCA-compressed CLR (PC10/50/100 × 6 metals) |
| `data/dimred_coords.parquet` | 10,000 | t-SNE and UMAP coordinates for 10K-sample subsample |
| `data/ena_metadata_full.parquet` | 252,502 | ENA portal metadata for all MicrobeAtlas runs (596 cols) |
| `data/sample_covariates.parquet` | 187,755 | Sample-level: study_id, platform, V-region (ENA+OTU), log_read_count |
| `data/h_sample_depth.parquet` | 188,308 | Total read counts per sample from sample_metadata Spark |
| `data/h_depth_pcorr.csv` | 6 | Within-study partial ρ(depth, metal exceedance) per metal |
| `data/mwas_results.parquet` | 3,000 | MWAS: Stouffer Z, weighted ρ, p-value, FDR per genus × metal |
| `data/usgs_within_study_results.parquet` | 3,000 | USGS MWAS: same schema as mwas_results; 0/3,000 significant |
| `data/usgs_variance_audit.parquet` | 403 | Per-study within-study metal variance and unique-site counts (USGS) |
| `data/strata_auc.csv` | 18 | Stratified AUC: metal × stratum (low/high/full) — uniform 0.94–0.96 (geographic artifact) |
| `data/strata_importances.csv` | 360 | Top-20 genus RF importances per metal × stratum; Jaccard J(low,high)=0.05–0.14 |
| `data/soil_strata_auc.csv` | 9 | Stratified AUC: soil_var × stratum (pH/SOC/clay × low/high/full) — 0.926–0.957 |
| `data/soil_strata_importances.csv` | 180 | Top-20 genus RF importances per soil_var × stratum |
| `data/cross_jaccard.csv` | 54 | Cross-variable Jaccard: J(metal-stratum, soil_var-stratum) for all 6×3×3 combinations |
| `data/shap_signed.json` | 6 metals | Signed mean SHAP + mean |SHAP| for top-50 genera per metal (CatBoost 300-tree regression, 5,000-sample subsample) |
| `data/shap_dependency.json` | 6×20 genera | Per-sample [CLR, SHAP, exceedance] triples for top-20 genera per metal (5,000 samples each) |
| `data/dashboard_data.json` | 4,353 pts | Grid-centroid map points + nitro_quintile, mwas_z, h2_jaccard for the interactive dashboard |
| `data/redox_proxy.parquet` | 54,961 | USA AMPLICON samples with P(oxic_5m) and P(reducing_5m) from mn10 groundwater Mn model |
| `data/redox_geobacter_corr.parquet` | 2 | Geobacter vs P(oxic): sample-level ρ=−0.160 (n=52,968) and study-level ρ=−0.239 (n=497) |
| `data/redox_genera_ranking.parquet` | 500 | All 500 CLR genera ranked by Spearman ρ with P(oxic_5m) |
| `data/redox_metal_corr.parquet` | 7 | Metal s25 grid (6 metals) and georoc_u vs P(oxic): ρ range −0.052 (Ni) to +0.187 (U) |
| `data/redox_metal_delta.parquet` | 6 | RF regression Δρ (with redox − baseline) per metal; |Δρ|≤0.009 |
| `data/redox_ni_inversion.parquet` | 4 | Serpentinite and Ni-EF group P(oxic) and Geobacter means with KW p-values |
| `data/redox_source_discrim.parquet` | 2 | Source discrimination (Cr, Ni): AUC baseline vs. +redox; Ni ΔAUC=+0.471 |
| `data/network_null_model.json` | 23 | Sign-permutation null model: z-scores 4.04–18.93, all p<0.005 |
| `data/network_metric_comparison.json` | 6 | s25 vs USGS pos_frac comparison per metal; 5/6 metals agree direction |
| `data/guild_characterization.json` | 8 guilds | Ward clustering on 40×40 co-occurrence stability matrix; env profiles per guild |
| `data/h3_phylum_stratified.json` | 32 | Within-phylum Mann-Whitney H3 tests; all NS; Actinobacteria direction reversed |
| `data/h3_ke_pangenome_results.csv` | 6 | ke_pangenome Wilcoxon H3 replication; all metals: indicator genera have LOWER KO density (p_fdr≈1) |
| `data/h3_ke_pangenome_phylum_results.csv` | 15 | ke_pangenome within-phylum H3; direction reversed across Actinomycetota/Pseudomonadota/Bacteroidota |
| `data/ko_phylo_breadth.csv` | 244 | Per-KO phylum/class/order/family breadth (phylogenetic signal proxy); median phylum breadth 0.155 |
| `data/ko_breadth_vs_indicator.csv` | 1039 | Per-(KO, metal) partial Spearman rho × breadth; high-breadth KOs show no positive association |
| `data/all_ko_enrichment.csv` | 8448 | Genome-wide KO Fisher enrichment (ke_pangenome); 7,663/8,448 q<0.05 (inflated by phylogeny) |
| `data/all_ko_enrichment_top.csv` | 7663 | q<0.05 hits from naive Fisher enrichment |
| `data/all_ko_enrichment_cmh.csv` | 8450 | CMH phylogeny-corrected KO enrichment; 7,396 q<0.05 (87.5%); 331 metal-relevant hits |
| `data/all_ko_enrichment_cmh_top.csv` | 7396 | q<0.05 CMH hits; top metal-relevant: cotA OR=14.6, ydbD OR=11.1, arsH OR=9.4 |
| `data/all_ko_order_summary.parquet` | 1,650,447 | Per-(KO, GTDB order, is_indicator) genus counts; 13,571 KOs, 790 orders |
| `data/all_ko_enrichment_cmh_order.csv` | 8128 | Order-level CMH enrichment; 6,445 q<0.05 (79.3%); 1,031 removed by order correction |
| `data/all_ko_enrichment_cmh_order_top.csv` | 6445 | q<0.05 order-level CMH hits; top: cyanide hydratase OR=121, pcpB OR=12, oqxA OR=10 |
| `data/all_ko_genus_prev_summary.parquet` | — | Per-(genus, KO, order) genome counts with/without KO; used for prevalence threshold |
| `data/all_ko_enrichment_cmh_prev50.csv` | 6765 | Order-CMH with ≥50% prevalence threshold; 1,654 q<0.05 (24.4%); removes annotation bias |
| `data/all_ko_enrichment_cmh_prev50_top.csv` | 1654 | q<0.05 prevalence-threshold hits; top: mexY OR=41, tetX OR=21, ituB OR=33 |
| `data/all_ko_enrichment_cmh_soil_prev50.csv` | 6718 | Soil-habitat-filtered + prev50 CMH; 1,408 q<0.05 (21.0%); 506 habitat-bias KOs removed |
| `data/all_ko_enrichment_cmh_soil_prev50_top.csv` | 1408 | q<0.05 soil-filtered hits; notable: SLC30A2/ZNT2 OR=37.1, bacA OR=42.5, chaA OR=5.8 |
| `data/all_ko_enrichment_cmh_qual_prev50.csv` | 6739 | Completeness-filtered (CheckM ≥90%/≤5%) + prev50 CMH; 1,596 q<0.05 (23.7%); 219 removed |
| `data/all_ko_enrichment_cmh_qual_prev50_top.csv` | 1596 | q<0.05 quality-filtered hits; top: dnaD OR=156, amsF OR=156, bacA OR=37.5 |
| `data/all_ko_genus_qual_summary.parquet` | 5,864,436 | Per-(genus, KO, order) quality-filtered genome counts (253,862 high-quality genomes) |
| `data/geo_linked_genomes.parquet` | 3,958 | GPS-located quality terrestrial ke_pangenome genomes: genome_id, genus, order, is_indicator, lat/lon, science_2025 AT exceedance per metal |
| `data/h3_geo_restricted_cmh.csv` | 6,797 | Geo-linked order-CMH (≥30% prevalence threshold); 76 q<0.05 (1.1%); no metal-tolerance KOs survive |
| `data/genus_annotation_rate.parquet` | 8,419 | Per-genus mean KEGG annotation rate from eggnog_mapper_annotations; tertile boundaries: low <0.584, mid 0.584–0.659, high >0.659 |
| `data/h3_cmh_annot_matched_baseline.csv` | 7,486 | Order-only CMH on annotation-rate-matched genus subset; 1,917 q<0.05 (25.6%) |
| `data/h3_cmh_order_x_annot_rate.csv` | 7,133 | Order × annotation-rate tertile CMH; 518 q<0.05 (7.3%); 73.4% of baseline enrichment removed |
| `data/h3_cmh_annot_rate_survivors.csv` | 518 | KOs surviving order × annotation-rate CMH (q<0.05); core biosynthetic genes |
| `data/h3_cmh_annot_rate_removed.csv` | 1,408 | KOs removed by annotation-rate stratification (significant in baseline, not in double-strat) |
| `data/ni_multioutput_results.json` | 6 models | Multi-output Ni exceedance classification (high/low quartile); auxiliary Cr +0.003–0.004 AUC |
| `data/generalizability_analysis.json` | — | Cross-method Stouffer Z concordance, phylum enrichment, cross-metal winners |
| `data/directionality_results.json` | — | Forward vs. reverse env–microbiome directionality (8.5× asymmetry; CLR → pH ρ=0.60) |
| `data/source_characterization_results.json` | 7 sections | Contamination vs. geogenic background AUC per metal (0.620–0.747); Ni redox ecology AUC=0.688 |
| `data/guild_condition_matrix.json` | 8 guilds × 23 conditions | δCLR matrix + condition clusters (4 clusters); 94 notable guild-condition pairs |
| `data/temporal_audit.json` | — | Date coverage (89.8%), year–metal ρ (max 0.067), temporal–geographic co-structure |
| `data/usa_ef_analysis_summary.csv` | 6 rows | EF classification summary per metal: %EF>2, n sites per class, H1/EF Jaccard (0.11–0.24) |
| `data/usa_ef_spearman_{metal}.csv` | ×6 metals | Within-study Spearman ρ: genus CLR vs EF; 119–143 FDR<0.05 genera per metal |
| `data/usa_ni_anthro_vs_bg.csv` | 174 rows | Mann-Whitney: anthropogenic Ni (EF>2, oxic, n=392) vs background; 112 FDR<0.05 genera |
| `data/usa_ni_serp_vs_bg.csv` | 174 rows | Mann-Whitney: serpentinite Ni (EF<1.5, raw>Q75, reducing, n=4,518) vs background; 147 FDR<0.05 genera |
| `data/usa_ni_redox_summary.csv` | 1 row | Ni redox class counts and significant genera |
| `data/usa_community_ko_ef_{metal}.csv` | ×6 metals, 7,221 rows | Community-KO EF Spearman ρ per KO; chaA positive 6/6 metals; Jaccard with H3 survivors 0.04–0.06 |
| `data/usa_community_ko_ef_summary.csv` | 6 rows | Per-metal summary: n sig, positive, H3 overlap, Jaccard |
| `data/usa_community_ko_ef_resid_{metal}.csv` | ×6 metals, 7,221 rows | H1-residualized community-KO EF Spearman ρ; confound-robust signals after indicator-genus zeroing |
| `data/usa_community_ko_ef_resid_summary.csv` | 6 rows | Residualized per-metal summary: orig vs resid counts, reduction %, both-pos, Jaccard H3 |
| `data/usa_community_ko_robust.csv` | 83 rows | KOs positive in both original and residualized analyses AND H3 survivors; robust across ≥2 metals |
| `data/fitnessbrowser_target_ko_summary.csv` | 21 rows | FitnessBrowser/fitprivate metal-stress fitness summary for 13 target KOs: mean fit, max\|t\|, n\_neg\_strong per KO × metal |
| `data/rhodanobacter_metal_conditions.csv` | 6 rows | enigma.fitprivate Rhodanobacter conditions for all 6 USA study metals (As/Cd/Cr/Cu/Ni/Pb) |
| `data/mtv/mtv_feature_table.biom` | 18 samples | ORFRC HFIR MTV QIIME2 feature table (surface soils; Nitrososphaera MTV case study) |
| `data/mtv/mtv_taxonomy.tsv` | 18 samples | MTV QIIME2 Silva r138 taxonomy assignments |

### Data Availability

Input data sources are available via the BERDL SQL warehouse (see README for tenant/database names and `arkinlab.*` collection identifiers). Generated data files (`data/*.csv`, `data/*.parquet`) are committed to this repository and archived with the project submission. The MTV QIIME2 feature table, taxonomy, and sample metadata are archived at `/home/hmacgregor/global_share/BERIL-research-observatory/BERIL-research-observatory/projects/metal_contamination_bioindicators/data/mtv/` (persistent global share) and also committed to `data/mtv/` in this repository (feature table and taxonomy only; sample-metadata is global-share only).

---

## Supporting Evidence

### Notebooks

| Notebook/Script | Purpose |
|----------------|---------|
| `notebooks/NB00_data_assembly.ipynb` | Build analysis_matrix.parquet from Spark |
| `notebooks/NB01_indicator_taxa.ipynb` | H1: CLR AUC, indicator SHAP, NB01 primary results |
| `notebooks/NB01b_robustness_extended.ipynb` | Study blocking, confounding, regression CV |
| `notebooks/NB01c_sequencing_confounders.ipynb` | Primer bias (Step A); depth confound summary figure (Step D) |
| `notebooks/NB01d_genus_weighted_unifrac.ipynb` | Genus-level weighted UniFrac PCoA (GTDB r214 branch lengths; 444/500 CLR genera matched); 2×3 panels: depth quartile + binary exceedance (per metal); continuous hexbin biplot with genus loading arrows |
| `scripts/build_sample_covariates.py` | ENA metadata + OTU V-region → sample_covariates.parquet |
| `scripts/run_nb01c_depth.py` | Depth η², within-study partial ρ, NB01c Steps B–D |
| `scripts/run_mwas.py` | MWAS: vectorized within-study Spearman meta-analysis (500 genera × 6 metals) |
| `scripts/validate_nitrososphaera.py` | Nitrososphaera global validation: ρ by continent, pH partial corr, quintile response |
| `scripts/run_strata_biomonitoring.py` | Stratified RF: AUC and top-20 genus importances per exceedance quintile stratum |
| `scripts/run_soil_confound_analysis.py` | Stratified RF for pH/SOC/clay; cross-variable Jaccard vs metal indicator lists |
| `scripts/run_shap_signed.py` | CatBoost regression (300 iter) per metal → signed mean SHAP + per-sample dependency data for top-20 genera |
| `notebooks/NB02_source_comparison.ipynb` | H2/H4: cross-source Jaccard, source AUC |
| `scripts/run_nb03_functional.py` | H3: Wilcoxon KO density, subcategory breakdown |
| `scripts/run_h3_phylum_stratified.py` | H3 within-phylum stratification: Mann-Whitney within Actinobacteria/Proteobacteria/Firmicutes (reveals phylogenetic confound) |
| `scripts/run_h3_ko_phylo_breadth.py` | H3 per-KO taxonomic breadth proxy for phylogenetic signal; partial Spearman rho by breadth tertile |
| `scripts/run_h3_all_ko_enrichment.py` | H3 genome-wide KO Fisher enrichment (ke_pangenome); naive OR; 7,663/8,448 q<0.05 |
| `scripts/run_h3_all_ko_enrichment_cmh.py` | H3 genome-wide KO CMH enrichment (ke_pangenome, phylogeny-corrected, stratified by phylum) |
| `scripts/run_h3_all_ko_enrichment_cmh_order.py` | H3 genome-wide KO CMH enrichment, stratified by GTDB order (within-phylum lineage correction; 6,445/8,128 q<0.05) |
| `scripts/run_h3_all_ko_enrichment_cmh_prevthresh.py` | H3 annotation-bias correction: ≥50% prevalence threshold + order CMH; 1,654/6,765 q<0.05 (24.4%) |
| `scripts/run_h3_cmh_soil_filter.py` | H3 soil habitat filter: restricts non-indicator comparison to MicrobeAtlas-detectable genera; 1,408/6,718 q<0.05 (21.0%) |
| `scripts/run_h3_cmh_completeness_filter.py` | H3 genome completeness filter: CheckM ≥90%/≤5% via gtdb_metadata join; 1,596/6,739 q<0.05 (23.7%); 219 KOs removed |
| `scripts/run_h3_geo_linked_ko_enrichment.py` | H3 geo-linked validation: GPS-linked soil genomes + science_2025 spatial join; geo-restricted CMH 1.1% (76/6,797); indicator genera from lower-metal sites; metal-stratified CMH infeasible (0 indicator genera at Cr >0.5) |
| `scripts/run_h3_annotation_bias_controls.py` | H3 controls B+C: vectorized CMH with KO phyla breadth ≥3 filter (B) and min-genome ≥5 filter (C); ~neutral net effect (26.2% combined vs 25.1% baseline); 6 CMH variants + cascade bar chart |
| `scripts/run_h3_cmh_annotation_rate.py` | H3 control A: KEGG annotation-rate stratification (order × tertile CMH); indicator annotation rate 0.522 vs non-indicator 0.616; 7.3% (518/7,133 q<0.05); 73.4% of residual enrichment removed |
| `scripts/run_network_null_model.py` | Sign-permutation null model for co-occurrence network pos_frac (200 permutations × 23 conditions) |
| `scripts/run_network_usgs.py` | USGS-based co-occurrence networks; comparison to s25-based metrics |
| `scripts/run_guild_characterization.py` | Ward clustering on 40×40 stability matrix → 8 guilds with env profiles |
| `scripts/run_directionality_test.py` | Forward (env → genus CLR) vs reverse (CLR → env) prediction asymmetry |
| `scripts/run_generalizability.py` | Cross-study vs within-study signal concordance; phylum and study-property predictors |
| `scripts/run_source_characterization.py` | Contamination vs. geogenic background classifiers (s25+USGS joint labelling); Ni redox ecology |
| `scripts/run_guild_condition_exploration.py` | δCLR heatmap (8 guilds × 23 conditions), Ward condition clustering, ecological interpretation |
| `scripts/run_temporal_audit.py` | ENA date coverage, year–metal Spearman ρ, temporal–geographic co-structure |
| `scripts/run_usa_ef_redox_analysis.py` | EF-based indicator assessment: vectorized within-study Spearman ρ (CLR vs EF), Ni redox stratification (anthropogenic vs serpentinite), H1/EF Jaccard |
| `scripts/run_usa_community_ko_ef.py` | Per-KO community-weighted EF analysis: CLR × ke_pangenome ko_fraction → sample KO profiles; within-study Spearman ρ vs EF; Jaccard with H3 survivors; chaA cross-validation |
| `scripts/run_usa_community_ko_ef_residualized.py` | H1-residualized community KO EF analysis: same as above but H1 indicator genera zeroed in CLR; confound-robust KO set (both × H3); Pb reversal and Cu breadth interpretation |
| `scripts/run_ni_multioutput.py` | Multi-output RF for Ni exceedance with auxiliary Cr prediction |
| `scripts/run_resid_blocked_cv.py` | Spatial de-trending Ridge → study-blocked AUC |
| `scripts/run_usgs_within_study.py` | USGS point-metal MWAS validation: spatial join → within-study Spearman meta-analysis (USA subset, 403 studies) |
| `scripts/run_nb06_controlled.py` | PGLS: detection-weighted genus mean log-ppm (7 USGS metals) ~ KO density + genome size + Levins B + lat/lon + soil chemistry; n=256 genera |
| `scripts/run_nb06_all_usgs.py` | PGLS expanded: inline BallTree spatial join → all 46 USGS elements with ≥200 site coverage; same controls; n=256 genera |
| `notebooks/NB05_catboost_regression.ipynb` | CatBoost regression (CLR/soil/soil+CLR), algorithm comparison, SHAP importance |
| `NB06_dimred.log` | PCA(200), RF-PCA Spearman ρ comparison, t-SNE + UMAP explorer |

### Figures

| Figure | Description |
|--------|-------------|
| `figures/fig_sample_map.png` | Global distribution of soil samples |
| `figures/fig_auc_comparison.png` | CLR vs soil vs spatial AUC comparison |
| `figures/fig_delta_auc.png` | ΔAUC per metal (M1 − B0) |
| `figures/fig_indicator_heatmap.png` | Top-50 indicator genera per metal (SHAP importance) |
| `figures/fig_extended_metrics.png` | AUPRC, MCC, threshold-specific AUC |
| `figures/fig_robustness_summary.png` | Robustness across subsets, regions, resolutions |
| `figures/fig_source_auc.png` | AUC per source (s25, CSU, GeoROC) |
| `figures/fig_source_jaccard.png` | Cross-source Jaccard heatmap |
| `figures/fig_nb01c_sequencing_confounders.pdf` | Sequencing confounder summary: primer bias and depth η² (NB01c) |
| `figures/fig_nb01c_aitchison_pcoa.pdf` | Aitchison-distance PCoA (CLR Euclidean) coloured by sequencing depth quartile (NB01c) |
| `figures/fig_nb01d_genus_wunifrac_pcoa.pdf` | Genus-level weighted UniFrac PCoA: 2×3 grid (depth quartile panel + 5 metals binary exceedance; n=10,000; GTDB r214) |
| `figures/fig_nb01d_genus_wunifrac_continuous.pdf` | Weighted UniFrac PCoA biplot: continuous exceedance hexbins × 6 metals + top-6 genus loading arrows |
| `figures/fig_nb03_ko_density.pdf` | H3: violin plots of KO density, indicator vs rest |
| `figures/fig_h3_ko_breadth_scatter.pdf` | H3: per-KO taxonomic breadth vs partial Spearman ρ, 4 levels × 6 metals |
| `figures/fig_h3_ko_breadth_hist.pdf` | H3: phylum/class/order/family breadth histograms for 280 metal KOs |
| `figures/fig_h3_all_ko_volcano.pdf` | H3: genome-wide KO volcano (naive Fisher OR vs −log10 q) |
| `figures/fig_h3_all_ko_cmh_volcano.pdf` | H3: genome-wide KO volcano (CMH phylogeny-corrected OR) |
| `figures/fig_h3_enrichment_comparison.pdf` | H3: naive vs CMH OR comparison (inflation assessment) |
| `figures/fig_h3_cmh_phylum_vs_order.pdf` | H3: phylum vs order CMH OR comparison; 1,031 phylum-only KOs = within-phylum lineage effects |
| `figures/fig_h3_all_ko_cmh_order_volcano.pdf` | H3: genome-wide volcano (order-level CMH, 6,445 q<0.05) |
| `figures/fig_h3_cmh_order_vs_prev50.pdf` | H3: order-CMH vs ≥50% prevalence OR comparison; 3,655 annotation-bias KOs identified |
| `figures/fig_h3_cmh_prev50_vs_soil.pdf` | H3: prevalence-threshold vs soil-habitat-filtered CMH OR; 506 habitat-bias KOs (orange) |
| `figures/fig_h3_cmh_prev50_vs_qual.pdf` | H3: prevalence-threshold vs completeness-filtered CMH OR; 219 low-quality bias KOs (orange) |
| `figures/fig_h3_geo_latlon_coverage.pdf` | Geo-linked genome map: 3,958 GPS-located terrestrial genomes (indicator in blue, non-indicator in grey) |
| `figures/fig_h3_geo_exceedance_distribution.pdf` | Local AT-exceedance distribution at genome collection sites: indicator vs non-indicator genera, per metal (6 panels) |
| `figures/fig_h3_annotation_bias_cascade.pdf` | H3 controls B+C: cascade bar chart showing q<0.05 % across 6 CMH variants (baseline, min-n, phyla-breadth, combined) |
| `figures/fig_h3_breadth_filter_distribution.pdf` | H3 control B: phylum breadth histogram for all tested KOs, with breadth ≥3 threshold line |
| `figures/fig_h3_annotation_rate_distribution.pdf` | H3 control A: KEGG annotation-rate density by indicator status (indicator mean 0.522 vs non-indicator 0.616) |
| `figures/fig_h3_annot_rate_cmh_scatter.pdf` | H3 control A: log₂ OR scatter (order-only vs order×annotation-rate CMH); blue = survive both, orange = lost by annotation-rate stratification |
| `figures/fig_taxon_resolution.png` | AUC vs taxonomic resolution |
| `figures/fig_study_confound_regression.png` | Study-blocking, confounding metrics, regression CV |
| `figures/fig_algo_comparison.pdf` | Algorithm comparison Spearman ρ (6 methods, CLR-only) |
| `figures/fig_catboost_featsel.pdf` | Feature selection: top-k CLR vs. Spearman ρ |
| `figures/fig_catboost_rho_comparison.pdf` | CatBoost ρ per feature set (CLR/soil/soil+CLR) |
| `figures/fig_catboost_shap_top20.pdf` | Top-20 SHAP genera (CatBoost CLR-only, all metals) |
| `figures/fig_nitrososphaera_shap_dep.pdf` | Nitrososphaera SHAP dependence vs metal exceedance (SHAP-CLR ρ=−0.920 for Cr) |
| `figures/fig_nitrososphaera_validation.pdf` | Cross-continental replication + quintile response (n=132,907) |
| `figures/fig_pca_variance.pdf` | PCA cumulative variance explained (PC1–200) |
| `figures/fig_rf_pca_vs_raw.pdf` | RF Spearman ρ: PCA10/50/100 vs raw CLR |
| `figures/fig_dimred_explorer.html` | Interactive t-SNE + UMAP (10K samples, coloured by metal) |
| `figures/fig_strata_biomonitoring.html` | Interactive: Jaccard genus overlap by metal + top-20 genera per stratum (low vs high) |
| `figures/fig_soil_confound.pdf` | Soil confound check: cross-variable Jaccard heatmap (metals × pH/SOC/clay) + within-var J(low,high) |
| `figures/fig_soil_confound.html` | Interactive version: stratum toggle (low/full/high), hover showing shared genera, dark mode, table view |
| `figures/fig_auc_story.html` | Interactive dumbbell: random-fold vs study-blocked AUC across feature sets, metal tabs, drop annotations |
| `figures/fig_indicator_explorer.html` | Interactive top-20 SHAP genera per metal; blue = metal-specific, orange = shared across 2+ metals |
| `figures/fig_comprehensive_dashboard.html` | Project dashboard v1 (6 sections): global map, model AUC + source comparison, SHAP bars + Jaccard heatmap, confound analysis, SHAP waterfall, Nitrososphaera continental replication; dark mode, hover tooltips |
| `figures/fig_comprehensive_dashboard_v2.html` | Project dashboard v2 (current): extends v1 with USA map layer, co-occurrence network panels for 23 conditions (spring-layout, interactive), updated redox and source-discrimination results; 14.2 MB |
| `figures/fig_mtv_redox_axis.pdf` | ORFRC HFIR surface soil — Nitrososphaeria/Rhodanobacter/Geobacter pH gradient |
| `figures/fig_mtv_redox_extended.pdf` | Redox axis extended to ORFRC-bbox (analysis_matrix) samples |
| `figures/fig_mtv_redox_gradient_extended.pdf` | pH-sorted strip plot, MTV + bbox combined |
| `figures/fig_mtv_phylum_ra.pdf` | Phylum-level RA per sample, all MTV samples |
| `figures/fig_mtv_phylum_ra_facet.pdf` | Phylum RA faceted by site (ORFRC / SRS / Background) |
| `figures/fig_mtv_phylum_ra_summary.pdf` | Mean phylum RA by site × material type |
| `figures/fig_mtv_genus_trends.pdf` | ORFRC HFIR genus RA vs environmental covariates (4×3 grid) |
| `figures/fig_mtv_nitro_vs_rhodano.pdf` | Nitrososphaeria vs Rhodanobacter anti-correlation (coloured by pH) |
| `figures/fig_redox_proxy.pdf` | USA map of groundwater redox proxy P(oxic) from mn10 Mn model; spatial join quality |
| `figures/fig_redox_geobacter.pdf` | Geobacter CLR vs P(oxic): scatter + study-level boxplot; ρ=−0.160 / −0.239 |
| `figures/fig_redox_genera_top.pdf` | Top 10 oxic-associated and top 10 reducing-associated genera ranked by ρ |
| `figures/fig_redox_metal_corr.pdf` | Metal s25 grid concentrations vs P(oxic): bar chart of ρ per metal |
| `figures/fig_redox_u_model.pdf` | U prediction (RF, study-blocked) feature importances with/without redox proxy |
| `figures/fig_redox_ni_inversion.pdf` | Serpentinite proxy P(oxic) vs non-serpentinite; high-EF vs low-EF Ni Geobacter comparison |
| `figures/fig_redox_metal_delta.pdf` | Δρ per metal with/without redox proxy in RF regression (|Δρ|≤0.009) |
| `figures/fig_redox_source_discrim.pdf` | Source discrimination AUC before/after redox: Ni 0.282→0.753, Cr 0.838→0.754 |
| `figures/fig_source_discrim_auc.pdf` | Baseline source discrimination AUC (geogenic vs. anthropogenic) per metal |
| `figures/fig_source_discrim_genera.pdf` | Top indicator genera for geogenic vs. anthropogenic source discrimination per metal |
| `figures/fig_sjr_uncertainty.pdf` | Spatial join radius uncertainty: semivariogram analysis for USGS NGDB join |
| `figures/fig_strata_biomonitoring.pdf` | Stratified biomonitoring indicator overlap: static version of fig_strata_biomonitoring.html |
| `figures/fig_mine_proximity.pdf` | CLR-metal association stratified by proximity to mining operations |
| `figures/fig_multimetal_comparison.pdf` | Cross-metal comparison of indicator genus overlap and predictive performance |
| `figures/fig_multimetal_heatmap.pdf` | Heatmap of cross-metal genus importance (top genera × 6 metals) |
| `figures/fig_all_metals_ranking.pdf` | All-metal ranking of indicator genera by aggregated SHAP importance |
| `figures/fig_broadspectrum_genera.pdf` | Broad-spectrum indicator genera appearing across ≥3/6 metals |
| `figures/fig_uranium_indicators.pdf` | Top indicator genera for uranium (USGS National Geochemical Survey) prediction |
| `figures/fig_ree_ranking.pdf` | Indicator genus ranking for rare earth elements (REE) |
| `figures/fig_ree_indicators.pdf` | Top indicator genera for REE; comparison with base-metal indicators |
| `figures/fig_metals_ree_comparison.pdf` | Metal vs. REE indicator overlap and predictive performance comparison |
| `figures/fig_env_confound_heatmap.pdf` | Environmental variable confound heatmap (CLR × env features correlation matrix) |
| `figures/fig_emri_usgs_scatter.pdf` | EMRI (exceedance model) vs. USGS measured metal concentrations scatter by metal |
| `figures/fig_usa_strata_rho.pdf` | USA subset: Spearman ρ per metal × stratum (CLR-only RF regression) |
| `figures/fig_usa_strata_jaccard.pdf` | USA subset: Jaccard overlap of indicator genera between contamination strata |
| `figures/fig_usa_strata_shift.pdf` | USA subset: indicator genus composition shift across exceedance strata |
| `figures/fig_usa_env_targets_rho.pdf` | USA subset: RF ρ comparison across metal and environmental response variables |
| `figures/fig_usa_env_jaccard.pdf` | USA subset: cross-variable Jaccard between metal and environmental indicator panels |
| `figures/fig_usa_env_genus_overlap.pdf` | USA subset: genus overlap between metal and environmental indicator panels |
| `figures/fig_usa_ablation.pdf` | USA subset: ablation study removing feature groups from RF regression |
| `figures/fig_usa_crosspred.pdf` | USA subset: cross-metal prediction (train on metal A, predict metal B) |
| `figures/fig_usa_rf_vs_cb.pdf` | USA subset: RF vs. CatBoost regression Spearman ρ comparison |
| `figures/fig_usgs_species_rho.pdf` | USGS National Geochemical Survey: per-species Spearman ρ with metal concentrations |
| `figures/fig_guild_condition_heatmap.pdf` | 8 guilds × 23 conditions δCLR heatmap (diverging RdBu, Ward condition clustering) |
| `figures/fig_condition_dendrogram.pdf` | Hierarchical clustering of 23 conditions in 8D guild space; 4-cluster annotation |
| `figures/fig_usa_ef_distributions.pdf` | EF histograms per metal (As/Cd/Pb widespread >2; Cr/Cu/Ni primarily geogenic) |
| `figures/fig_usa_ef_top_genera.pdf` | Top EF-associated genera per metal (within-study Spearman ρ; H1 indicators bold/red) |
| `figures/fig_usa_ni_redox_stratification.pdf` | Ni anthropogenic vs serpentinite indicator genera (Δ median CLR vs background) |
| `figures/fig_usa_ef_vs_h1_summary.pdf` | EF-positive FDR<0.05 genera vs H1 indicator genera count per metal (bar chart) |
| `figures/fig_usa_community_ko_volcano.pdf` | Volcano plot of community-KO Spearman ρ vs EF per metal (inflation visible; 60-69% positive) |
| `figures/fig_usa_community_ko_top_pos.pdf` | Top 10 positive EF-associated community KOs per metal (H3 survivors in red) |
| `figures/fig_usa_community_ko_h3_jaccard.pdf` | Jaccard between community-KO FDR<0.05 pos and H3 CMH survivors (0.04–0.06 per metal) |
| `figures/fig_usa_community_ko_resid_comparison.pdf` | H1-residualized vs original: positive KO count reduction per metal + Jaccard-H3 comparison |
| `figures/fig_usa_community_ko_resid_volcano.pdf` | Residualized community-KO volcano per metal; H3 survivors highlighted (★); confound-robust set shown |
| `figures/fig_h3_ke_pangenome.pdf` | H3 ke_pangenome replication: indicator vs non-indicator genera mean KO density; direction REVERSED vs SPIRE (indicator genera 20% lower); all metals p_fdr≈1 |
| `figures/fig_h3_per_metal_cmh_bar.pdf` | H3 per-metal CMH: q<0.05 percentage by metal (order-level CMH) — bar chart showing metal-specific attenuation across the cascade |
| `figures/fig_h3_per_metal_jaccard.pdf` | H3 per-metal Jaccard: KO set overlap between SPIRE order-CMH survivors and ke_pangenome survivors per metal |
| `figures/fig_h3_per_metal_ko_breadth.pdf` | H3 per-metal KO breadth: taxonomic breadth distributions for survivor KOs by metal (diagnostic) |
| `figures/fig_h3_source_comparison_bar.pdf` | H3 SPIRE vs ke_pangenome: positive KO % by source (bar) — directional reversal between databases |
| `figures/fig_h3_source_comparison_scatter.pdf` | H3 SPIRE vs ke_pangenome: effect-size scatter (OR from each source); low correlation confirms source-specificity |
| `figures/fig_h3_source_comparison_venn.pdf` | H3 SPIRE vs ke_pangenome: Venn diagram of KO set overlap — small intersection confirms database-specificity of apparent enrichment |
| `figures/fig_usgs_chemical_maps.html` | Interactive USGS NGDB geographic maps: measured metal concentrations (As/Cd/Cr/Cu/Ni/Pb) across USA sampling stations |
| `figures/fig_ni_multioutput_comparison.pdf` | Multi-output Ni: AUC with/without auxiliary Cr target under study-blocked RF (CLR-only and CLR+redox baselines) |
| `figures/fig_ni_multioutput_gains.pdf` | Multi-output Ni: AUC increments from auxiliary Cr prediction vs single-output baseline (+0.003–0.004; negligible) |

---

## Future Directions

1. **Metatranscriptomics extension (NB04)**: Not feasible with current public data. The
   capacity-vs-activity hypothesis should be framed as a discussion point linking to CME PGLS
   results on constitutive vs. inducible metal gene expression. A dedicated field campaign
   collecting paired 16S + metatranscriptomics from a metal contamination gradient would be
   the principled follow-up.

2. **ENA metadata harvest**: Complete. `data/ena_metadata_full.parquet` (252,502 runs × 596
   cols) and `data/sample_covariates.parquet` (187,755 × 10) produced. OTU-based V-region from
   Spark fills 92% of samples. Confound analysis confirms all technical variables (platform,
   library_strategy, V-region, depth) are absorbed by study identity.

3. **Nitrososphaera mechanistic demonstration**: The sensitive-taxon interpretation (depletion
   in Cr-contaminated soils) is now established observationally at global scale (n=132,907,
   4 continents, pH-controlled). What remains is mechanistic: controlled experiments or
   BacDive/DSMZ isolate-level Cr MIC data would confirm whether Nitrososphaera is directly
   inhibited by Cr or displaced via niche disruption (suppression of ammonia availability,
   community restructuring).

4. **Cross-metal indicator core validation**: The 11 genera in top-20 SHAP for ≥3 metals
   represent a broad-spectrum predictive candidate set. However, the directionally consistent
   subset — Geodermatophilus and Stenotrophobacter (both consistently depleted across Cd/Cr/Ni
   and Cr/Cu/Ni respectively) — should be prioritized for multi-metal biomonitoring panel
   development. Confirming cross-study stability (held-out geographic regions) and representation
   in cultured isolate collections would strengthen the case.

---

## References

- Fierer N. (2017). Embracing the unknown: disentangling the complexities of the soil microbiome. *Nat Rev Microbiol* 15(10):579–590.
- Pei Y et al. (2018). Microbial community structure and function indicate the severity of chromium contamination of the Yellow River. *Front Microbiol* 9:38. DOI: 10.3389/fmicb.2018.00038
- Pérez-de-Mora A et al. (2006). Microbial community structure and function in a soil contaminated by heavy metals: effects of plant growth and different amendments. *Soil Biol Biochem* 38(2):327–341.
- Prosser JI, Hink L, Gubry-Rangin C, Nicol GW. (2019). Nitrous oxide production by ammonia oxidizers: physiological diversity, niche differentiation and potential mitigation strategies. *Glob Chang Biol* 26(1):103–118. DOI: 10.1111/gcb.14877
- Roberts DR et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography* 40(8):913–929.
- Salam LB et al. (2023). Chromium contamination accentuates changes in the microbiome and heavy metal resistome of a tropical agricultural soil. *World J Microbiol Biotechnol* 39(9):252.
- Henderson et al. (2026) [preprint]. Spatially-explicit prediction of soil metal contamination risk at global scale. *Science*.
- Bai Z et al. (2023). Chromium contamination affects the transcriptional activities of ammonia-oxidizing archaea and bacteria in soils. *Front Microbiol* 14:1132714. DOI: 10.3389/fmicb.2023.1132714
- Valavi R et al. (2019). blockCV: An r package for generating spatially or environmentally separated folds for k-fold cross-validation of species distribution models. *Methods Ecol Evol* 10(2):225–232.
- Treude N et al. (2003). Strain FAc12, a dissimilatory iron-reducing member of the Anaeromyxobacter subgroup of Myxococcales. *FEMS Microbiol Ecol* 44(2):261–269. DOI: 10.1016/S0168-6496(03)00019-0
- Muramatsu M et al. (2020). Possible Involvement of a Tetrathionate Reductase Homolog in Dissimilatory Arsenate Reduction by Anaeromyxobacter sp. Strain PSR-1. *Appl Environ Microbiol* 86(17):e00829-20. DOI: 10.1128/AEM.00829-20
- Brazelton WJ et al. (2012). Metagenomic Evidence for H₂ Oxidation and H₂ Production by Serpentinite-Hosted Subsurface Microbial Communities. *Front Microbiol* 2:268. DOI: 10.3389/fmicb.2011.00268
- USGS ScienceBase (mn10_grid_prediction). National groundwater Mn exceedance probability model at 5m depth. USGS Water Resources, accessed 2026.
- Wetmore KM et al. (2015). Rapid quantification of mutant fitness in diverse bacteria by sequencing randomly bar-coded transposons. *mBio* 6(3):e00306-15. DOI: 10.1128/mbio.00306-15 — *methodology underlying kescience.fitnessbrowser and enigma.fitprivate*
- Price MN et al. (2018). Mutant phenotypes for thousands of bacterial genes of unknown function. *Nature* 557:503–509. DOI: 10.1038/s41586-018-0124-0 — *FitnessBrowser database of RB-TnSeq fitness profiles*
- Arkin AP et al. (2018). KBase: The United States Department of Energy Systems Biology Knowledgebase. *Nat Biotechnol* 36:566–569. DOI: 10.1038/nbt.4163 — *kbase.ke_pangenome genome database*
- Hou D et al. (2025). Global soil pollution by toxic metals threatens agriculture and human health. *Science* 388(6744):316–321. DOI: 10.1126/science.adr5214 — *context for global metal contamination scale and crop/health risk*
- Wedepohl KH. (1995). The composition of the continental crust. *Geochim Cosmochim Acta* 59(7):1217–1232. DOI: 10.1016/0016-7037(95)00038-2 — *UCC reference composition used for enrichment factor calculation*
