# Research Plan: Macro-Micro Nutrient Gene Co-occurrence

## Research Question

Do bacterial pangenomes that encode macro-nutrient acquisition machinery (phosphate/phosphonate transport, alkaline phosphatases, nitrogenase) disproportionately co-encode trace-metal handling genes (Cu, Fe, Zn, Co, Ni transport and homeostasis), and does this coupling intensify in lineages that synthesize phenazines — the bacterial Fe(III)-oxyhydroxide dissolution compounds upregulated under P starvation?

## Hypothesis

**H1:** Presence of P-acquisition, N-fixation, and phenazine biosynthesis gene families in species pangenomes is positively associated with presence of metal-handling gene families, at levels exceeding a permutation null that preserves species-level gene counts.

**H0:** Gene family group co-occurrence is no greater than expected by chance given the marginal prevalence of each group across species.

## Literature Context

- McRose & Newman (2021, *Science* 371:1033–1037): Phenazines enhance phosphorus bioavailability by reductively dissolving Fe(III)-oxyhydroxides under PhoB-regulated P starvation.
- Edayilam et al. (2018): P-stress induces root exudate changes that mobilize trace metals from Fe-oxyhydroxide surfaces.
- Wu et al. (2022): phzS detected in MAGs from P-limited reforestation soils.
- Dakora & Phillips (2002): Root organic acid exudation as a nutrient acquisition strategy in low-nutrient soils.

## Approach

### Step 1: Define gene family sets
Extract species-level presence/absence for 23 gene families across 4 functional groups from `kbase_ke_pangenome`, using Bakta KEGG KO, gene name, and PFAM domain annotations.

### Step 2: Co-occurrence matrix
Compute Jaccard index, phi coefficient, and Fisher's exact test for all pairwise group and individual gene combinations. Validate with 1,000-permutation null model.

### Step 3: Core vs. accessory enrichment
For species encoding both nutrient and metal genes, test whether co-occurring genes concentrate in core vs. auxiliary/singleton pangenome fractions using Fisher's exact test per species with Stouffer meta-analysis.

### Step 4: Phylogenetic stratification
Stratify co-occurrence by GTDB phylum/class/family. Test prediction that plant-associated and soil-dwelling lineages show stronger co-occurrence.

## Data Sources

- **Primary:** `kbase_ke_pangenome` — 132.5M gene clusters, 27,702 species pangenomes
- **Tables:** `gene_cluster`, `bakta_annotations`, `bakta_pfam_domains`, `gtdb_species_clade`

## Query Strategy

1. Main query: JOIN `gene_cluster` × `bakta_annotations`, GROUP BY `gtdb_species_clade_id`, CASE WHEN for each gene family criterion
2. PFAM queries: separate JOINs to `bakta_pfam_domains` with versioned PFAM IDs (`LIKE 'PFxxxxx.%'`)
3. Taxonomy: direct query on `gtdb_species_clade` with parsed GTDB_taxonomy string

## Expected Outcomes

- Significant positive co-occurrence for P×Metal, N×Metal, Phz×Metal
- Strongest individual signals for nifH×feoB (Fe cofactor dependency) and phoD×HMA
- Phenazine operon carriers concentrated in soil/rhizosphere lineages with near-universal metal gene complement
- Core-genome enrichment for P-acquisition genes; accessory placement for feoB/HMA

## Revision History

- **v1** (2026-05-07): Initial plan. Four-step analysis on `kbase_ke_pangenome` after pivot from Substrate C (fitnessbrowser lacks P-starvation data).
- **v2** (2026-05-07): Added phenazine biosynthesis gene family group (d) per user request, citing McRose & Newman 2021. Extended from 16 to 23 gene families.
- **v3** (2026-05-07): Analysis complete. All four steps executed. Results support H1 with caveats (phylogenetic non-independence not fully controlled).
