# Discoveries Log

Running log of insights discovered during science projects. Tag each with `[project_name]`.

Periodically refactor stable insights into the appropriate structured doc (schema.md, pitfalls.md, performance.md).

---

## 2026-01

### [ecotype_analysis] Environment vs Phylogeny: Phylogeny usually dominates

Analysis of 172 species with sufficient data showed:
- Median partial correlation for environment effect: 0.0025
- Median partial correlation for phylogeny effect: 0.0143
- Phylogeny dominates in 60.5% of species
- Environment dominates in 39.5% of species

No significant difference between "environmental" bacteria (where lat/lon is meaningful) and host-associated bacteria (p=0.66).

### [ecotype_analysis] ANI extraction requires per-species iteration

Attempting to query ANI for all 13K+ genomes in a single IN clause fails/times out. Must iterate over species and query ANI for each species separately. See `docs/performance.md` for pattern.

### [pangenome_openness] Pangenome table has pre-computed stats

The `pangenome` table already contains `no_core`, `no_aux_genome`, `no_singleton_gene_clusters`, `no_gene_clusters` - no need to compute from gene_cluster table.

### [pangenome_openness] No correlation between openness and env/phylo effects

Tested whether open pangenomes (low core fraction) show different patterns. Results:
- rho=-0.05, p=0.54 for environment effect
- rho=0.03, p=0.73 for phylogeny effect
- No significant relationship found

### [integrity_checks] 12 orphan pangenomes are symbionts

The 12 pangenomes without matching species clades are mostly obligate symbionts:
- Portiera aleyrodidarum (whitefly symbiont)
- Profftella armatura (psyllid symbiont)
- Various uncultivated lineages (UBA, TMED, SCGC prefixes)

These are valid pangenomes but filtered from species metadata due to single-genome status.

### [cog_analysis] Universal functional partitioning in bacterial pangenomes

Analysis of 32 species across 9 phyla (357,623 genes) reveals a remarkably consistent "two-speed genome":

**Novel/singleton genes consistently enriched in:**
- L (Mobile elements): +10.88% enrichment, 100% consistency across species - STRONGEST SIGNAL
- V (Defense mechanisms): +2.83% enrichment, 100% consistency
- S (Unknown function): +1.64% enrichment, 69% consistency

**Core genes consistently enriched in:**
- J (Translation): -4.65% enrichment, 97% consistency - STRONGEST DEPLETION
- F (Nucleotide metabolism): -2.09% enrichment, 100% consistency
- H (Coenzyme metabolism): -2.06% enrichment, 97% consistency
- E (Amino acid metabolism): -1.81% enrichment, 81% consistency
- C (Energy production): -1.75% enrichment, 88% consistency

**Biological implications:**
- Core genes = ancient, conserved "metabolic engine" (translation, energy, biosynthesis)
- Novel genes = recent acquisitions for ecological adaptation (mobile elements, defense, niche-specific)
- Horizontal gene transfer (HGT) is the primary innovation mechanism, not vertical inheritance
- The massive L enrichment (+10.88%) suggests most genomic novelty comes from mobile elements
- Patterns hold universally across bacterial phyla, suggesting deep evolutionary constraint

**Hypothesis validation:** All 8 predictions from initial N. gonorrhoeae analysis confirmed across 32 species.

This represents a fundamental organizing principle of bacterial pangenome structure.

### [cog_analysis] Composite COG categories are biologically meaningful

Multi-function genes with composite COG assignments (e.g., "LV" = mobile+defense, "EGP" = amino acid+carb+inorganic ion) are not annotation artifacts:

- LV (mobile+defense): +0.34% enrichment, 76% consistency
- Suggests functional modules like "mobile defense islands"
- Should not be filtered out as noise - they represent genuine multi-functional genes

## 2026-02

### [fitness_modules] ICA reliably decomposes fitness data into biologically coherent modules

Robust ICA (30-50 FastICA runs + DBSCAN clustering) consistently finds 17-52 stable modules per organism across 32 bacteria. Within-module gene pairs show 17-138x higher correlation than random pairs, and 93.2% of modules have elevated cofitness vs genome-wide background. This validates ICA as a principled decomposition method for RB-TnSeq data.

### [fitness_modules] Membership thresholding is the critical parameter, not ICA itself

The initial D'Agostino K² normality-based thresholding gave 100-280 genes per module — biologically meaningless. The ICA components themselves were fine; the problem was deciding which genes "belong" to each module. Switching to an absolute weight threshold (|Pearson r| ≥ 0.3 with module profile, max 50 genes) reduced modules to 5-50 genes and dramatically improved all validation metrics:
- Cofitness enrichment: 59% → 93.2%
- Within-module correlation: 0.047 → 0.387 (DvH)
- Predictions: 2,423 low-quality → 878 high-quality

### [fitness_modules] Organisms with <200 experiments still produce valid modules

Caulo (198 experiments) showed the weakest signal in the pilot (2.9x correlation enrichment vs 31x for DvH), but organisms down to 104 experiments (Ponti) still produced stable modules. The key is capping components at 40% of experiments — higher ratios cause FastICA convergence failures and extreme slowness.

### [fitness_modules] Fitness Browser schema documentation has inaccuracies

Several table schemas differ from the documented schema:
- `keggmember` uses `keggOrg`/`keggId` (not `orgId`/`locusId`) — must join through `besthitkegg`
- `kgroupec` uses `ecnum` (not `ec`)
- `seedclass` has `orgId, locusId, type, num` (not subsystem/category hierarchy)
- `fitbyexp_*` tables are long format (not pre-pivoted as documented)

### [fitness_modules] Spark is accessible from CLI via berdl_notebook_utils

`from berdl_notebook_utils.setup_spark_session import get_spark_session` works from regular Python scripts on JupyterHub — not just notebook kernels. This enables running full analysis pipelines from the command line without `jupyter nbconvert`. The auto-import in `/configs/ipython_startup/00-notebookutils.py` only affects notebook kernels.

### [fitness_modules] Pan-bacterial module families exist across diverse phyla

Cross-organism module alignment using BBH ortholog fingerprints revealed 156 module families spanning 2+ organisms. The largest family spans 21 of 32 organisms across Proteobacteria, Bacteroidetes, Firmicutes, and Archaea — evidence of deeply conserved fitness regulons. 28 families span 5+ organisms.

This required using orthologs from ALL organisms in the analysis — an initial run using only 5-organism orthologs found just 27 families with no family spanning more than 4 organisms. The ortholog graph density is critical.

### [fitness_modules] Ortholog scope dramatically affects cross-organism analysis

Using BBH pairs from 5 organisms (10K pairs, 1,861 OGs) vs all 32 organisms (1.15M pairs, 13,402 OGs) produced radically different results:
- Module families: 27 → 156 (6x)
- Families spanning 5+ orgs: 0 → 28
- Family-backed predictions: 31 (4%) → 493 (56%)

Lesson: always extract orthologs for ALL organisms in the analysis, not just a pilot subset. The ortholog graph is not additive — adding organisms creates new transitive connections.

---

## Template

```markdown
### [project_name] Brief title

Description of what was discovered, why it matters, and any implications
for future analyses.
```
