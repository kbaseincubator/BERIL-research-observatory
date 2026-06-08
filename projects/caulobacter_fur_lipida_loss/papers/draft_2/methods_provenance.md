# Methods Provenance

Auto-generated from `extract_methods.py` over `/home/aparkin/BERIL-research-observatory/projects/caulobacter_fur_lipida_loss`. Each fact below traces to a notebook cell or RESEARCH_PLAN section. The Methods agent (Phase 3) uses this as the factual basis for the Methods section; it MUST NOT claim any method that cannot be pointed to here.

## Design Intent (from RESEARCH_PLAN.md)

### Hypotheses _(intent: hypothesis)_

Each hypothesis is stated with H0/H1, the Phase A evidence already on hand, and the *specific* analyses required to resolve it.

### H1 — ChvG-ChvI envelope-stress regulon: cooperator and consequence

- **H0**: ChvI regulon induction in 4584 and 4599 is no greater than expected by chance given universe size and DEG cardinality.
- **H1**: ChvI regulon is *partially* induced when Fur+SspB are released (permissive condition), and *further* induced when lipid A is lost (consequence), with distinct gene subsets dominating each phase.

**Phase A evidence**: Stein 4.75-fold p=8e-9 (4584-vs-4580) and 4.56-fold p=1e-15 (4599-vs-4584); QY 3.18-fold (4584) and 2.87-fold (4599). H0 already rejected; the question is *which subset of ChvI targets is engaged at each phase*, whether **SigU** (ECF σ-factor, +3.13 in 4599-vs-4584) is the operational driver of the 4599-specific component, and whether the early-cooperator subset overlaps with the Fur regulon (suggesting Fur-ChvI co-regulation).

### H2 — A critical Fur regulon subset, rankable by phenotypic importance

- **H0**: The Δ*fur* contribution to Δ*lpxc* rescue is driven by *generic* derepression of the entire Fur regulon equally — no specific subset matters more than others.
- **H1**: A small, identifiable subset of Fur-released genes is mechanistically critical — genes whose loss is associated with strong fitness defects under iron limitation, oxidative stress, or envelope-disrupting conditions.

**Phase A evidence**: Massive Fur dere

_(truncated; full text in RESEARCH_PLAN.md)_

### Analysis Plan _(intent: analysis_plan)_

Notebooks are numbered, executed in JupyterHub with outputs committed (per `PROJECT.md`). Each notebook saves figures to `figures/NB{n}_*.png` and small derived tables to `data/NB{n}_*.csv` (excluded from git by the project gitignore rule; re-derived from the notebook on demand).

### NB01 — Leaden 2018 SRP136695 re-analysis (Fur-only DEG signature)

- **Goal**: Produce a clean Δ*fur*-only DEG signature (no Δ*sspB*, no Δ*rsaA*) to disambiguate Fur-specific vs SspB-specific effects in 4584-vs-4580.
- **Approach** (preflight first to avoid wasted compute):
  1. **Preflight (NB01a, in-notebook, fast)** — try to find a pre-published DEG table before re-analyzing from raw reads:
     a. Fetch Frontiers in Microbiology PMC supplementary files for PMC6120978 (`https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6120978/`) via WebFetch / `wget` — Frontiers typically attaches Supplementary Table S1 (DEG matrix) directly.
     b. Check GEO at `https://www.ncbi.nlm.nih.gov/geo/?term=SRP136695` for an author-provided processed-count or DEG table.
     c. If a DEG table is found, normalize it to (locustag, logFC, pvalue, fdr) and skip step 2.
  2. **Re-analysis (CTS, only if preflight fails)**:
     - **CTS budget dry-run**: submit a 1-sample SRA prefetch test first (~10 min). Confirm runtime and storage extrapolate within quota (estimated full job: 6 samples × ~30 min HISAT2 = ~3 h wall, ~150 GB transient).
     - Full pipeline: `prefetch SRP136695 → fasterq-dump → fastp → HISAT2 (NA1000 ref, -

_(truncated; full text in RESEARCH_PLAN.md)_

## Statistical Tests Detected

### Fisher's exact test

- `scipy.stats.fisher_exact` in **notebooks/03_chvi_phase_partition_sigU.ipynb** (cell 10, line 19) — kw: alternative='greater'

### Pearson correlation

- `scipy.stats.pearsonr` in **notebooks/01_leaden2018_fur_signature.ipynb** (cell 4, line 12)
- `scipy.stats.pearsonr` in **notebooks/01_leaden2018_fur_signature.ipynb** (cell 5, line 17)

### Spearman rank correlation

- `scipy.stats.spearmanr` in **notebooks/01_leaden2018_fur_signature.ipynb** (cell 4, line 11)
- `scipy.stats.spearmanr` in **notebooks/01_leaden2018_fur_signature.ipynb** (cell 5, line 16)

## Software and Versions

_(no requirements.txt / pyproject.toml / environment.yml found at project root)_

## Imports by Notebook

- **notebooks/00_orientation.ipynb**: matplotlib.pyplot, numpy, pandas, pathlib, scipy.stats, seaborn
- **notebooks/01_leaden2018_fur_signature.ipynb**: matplotlib.pyplot, numpy, openpyxl, pandas, pathlib, scipy.stats, seaborn
- **notebooks/02_caulo_fitness_ranking.ipynb**: berdl_notebook_utils.setup_spark_session, matplotlib.pyplot, numpy, pandas, pathlib, re, scipy.stats, seaborn
- **notebooks/02b_h2_hypergeometric_verdict.ipynb**: numpy, pandas, pathlib, scipy.stats
- **notebooks/03_chvi_phase_partition_sigU.ipynb**: matplotlib.pyplot, numpy, pandas, pathlib, re, scipy.stats, seaborn
- **notebooks/04_sphingolipid_lpt_panel.ipynb**: matplotlib.pyplot, numpy, pandas, pathlib, seaborn
- **notebooks/05_pg_remodeling.ipynb**: matplotlib.pyplot, numpy, pandas, pathlib, re, seaborn
- **notebooks/06_comparative_species.ipynb**: berdl_notebook_utils.setup_spark_session, matplotlib.pyplot, numpy, pandas, pathlib, re, seaborn
- **notebooks/06b_ncbi_annotation_presence.ipynb**: Bio, numpy, pandas, pathlib, time
- **notebooks/07_synthesis.ipynb**: matplotlib.gridspec, matplotlib.pyplot, numpy, pandas, pathlib, seaborn

## Spark / K-BERDL Queries

### notebooks/02_caulo_fitness_ranking.ipynb, cell 1, line 19

_K-BERDL via Spark (remote execution; query string only, not full execution path)_

```sql
SELECT 1 AS one
```

### notebooks/02_caulo_fitness_ranking.ipynb, cell 2, line 2

_K-BERDL via Spark (remote execution; query string only, not full execution path)_

```sql
SELECT expName, expDesc, expDescLong, expGroup,
           media, aerobic, liquid, condition_1, units_1, concentration_1,
           condition_2, units_2, concentration_2,
           condition_3, units_3, concentration_3,
           condition_4, units_4, concentration_4
    FROM kescience_fitnessbrowser.experiment
    WHERE orgId = 'Caulo'
```

### notebooks/02_caulo_fitness_ranking.ipynb, cell 6, line 1

_K-BERDL via Spark (remote execution; query string only, not full execution path)_

```sql
SELECT locusId, sysName, gene, desc, scaffoldId, begin, end, strand, type
    FROM kescience_fitnessbrowser.gene
    WHERE orgId = 'Caulo'
```

### notebooks/02_caulo_fitness_ranking.ipynb, cell 7, line 1

_K-BERDL via Spark (remote execution; query string only, not full execution path)_

```sql
SELECT expName, locusId,
           CAST(fit AS DOUBLE) AS fit,
           CAST(t   AS DOUBLE) AS t
    FROM kescience_fitnessbrowser.fitbyexp_caulo
```

## Parameters and Thresholds

- `PROJ = (non-literal: Path('/home/aparkin/BERIL-research-observatory/projects/caul)` in **notebooks/00_orientation.ipynb** (cell 1, line 12)
- `DATA_IN = (non-literal: Path('/home/aparkin/data/kr-caulobacter-envelope/clean'))` in **notebooks/00_orientation.ipynb** (cell 1, line 13)
- `DATA_OUT = (non-literal: PROJ / 'data')` in **notebooks/00_orientation.ipynb** (cell 1, line 14)
- `FIG = (non-literal: PROJ / 'figures')` in **notebooks/00_orientation.ipynb** (cell 1, line 15)
- `SPHINGO = (non-literal: ['CCNA_01212', 'CCNA_01213', 'CCNA_01214', 'CCNA_01217', 'CC)` in **notebooks/00_orientation.ipynb** (cell 4, line 1)
- `SPHINGO_NAME = (non-literal: {'CCNA_01212': 'bcerS', 'CCNA_01213': 'lptG2 (Uchendu)', 'CC)` in **notebooks/00_orientation.ipynb** (cell 4, line 3)
- `SUPPRESSORS = (non-literal: ['CCNA_00497', 'CCNA_01068', 'CCNA_01553', 'CCNA_03733'])` in **notebooks/00_orientation.ipynb** (cell 11, line 1)
- `PROJ = (non-literal: Path('/home/aparkin/BERIL-research-observatory/projects/caul)` in **notebooks/01_leaden2018_fur_signature.ipynb** (cell 1, line 14)
- `USERDATA = (non-literal: Path('/home/aparkin/data/kr-caulobacter-envelope'))` in **notebooks/01_leaden2018_fur_signature.ipynb** (cell 1, line 15)
- `DATA_OUT = (non-literal: PROJ / 'data')` in **notebooks/01_leaden2018_fur_signature.ipynb** (cell 1, line 16)
- `FIG = (non-literal: PROJ / 'figures')` in **notebooks/01_leaden2018_fur_signature.ipynb** (cell 1, line 17)
- `LEADEN_PATH = (non-literal: USERDATA / 'raw' / 'Table 2.XLSX')` in **notebooks/01_leaden2018_fur_signature.ipynb** (cell 1, line 18)
- `n_total = (non-literal: len(joined))` in **notebooks/01_leaden2018_fur_signature.ipynb** (cell 5, line 9)
- `n_with_ours = (non-literal: joined['log2fc_ours'].notna().sum())` in **notebooks/01_leaden2018_fur_signature.ipynb** (cell 5, line 10)
- `VERDICT = (non-literal: 'PASS — Δfur is a major driver' if rho_s >= 0.3 else 'FAIL —)` in **notebooks/01_leaden2018_fur_signature.ipynb** (cell 5, line 28)
- `PROJ = (non-literal: Path('/home/aparkin/BERIL-research-observatory/projects/caul)` in **notebooks/02_caulo_fitness_ranking.ipynb** (cell 1, line 14)
- `DATA_OUT = (non-literal: PROJ / 'data')` in **notebooks/02_caulo_fitness_ranking.ipynb** (cell 1, line 15)
- `FIG = (non-literal: PROJ / 'figures')` in **notebooks/02_caulo_fitness_ranking.ipynb** (cell 1, line 16)
- `IRON_RE = (non-literal: re.compile('fe\\b|iron|2,2.bipyridyl|ferric|ferrous|hemin|fe)` in **notebooks/02_caulo_fitness_ranking.ipynb** (cell 4, line 2)
- `OXIDATIVE_RE = (non-literal: re.compile('h2o2|hydrogen peroxide|peroxide|paraquat|menadio)` in **notebooks/02_caulo_fitness_ranking.ipynb** (cell 4, line 3)
- `ENVELOPE_RE = (non-literal: re.compile('vancomycin|bacitracin|polymyxin|colistin|deoxych)` in **notebooks/02_caulo_fitness_ranking.ipynb** (cell 4, line 4)
- `CARBON_RE = (non-literal: re.compile('glucose|fructose|galactose|sucrose|maltose|lacto)` in **notebooks/02_caulo_fitness_ranking.ipynb** (cell 4, line 5)
- `n_iron = (non-literal: exps['cond_classes'].str.contains('iron', regex=False, na=Fa)` in **notebooks/02_caulo_fitness_ranking.ipynb** (cell 5, line 2)
- `n_env = (non-literal: exps['cond_classes'].str.contains('envelope', regex=False, n)` in **notebooks/02_caulo_fitness_ranking.ipynb** (cell 5, line 3)
- `n_ox = (non-literal: exps['cond_classes'].str.contains('oxidative', regex=False, )` in **notebooks/02_caulo_fitness_ranking.ipynb** (cell 5, line 4)
- `n_carbon = (non-literal: exps['cond_classes'].str.contains('carbon', regex=False, na=)` in **notebooks/02_caulo_fitness_ranking.ipynb** (cell 5, line 5)
- `PREFLIGHT_PASS = (non-literal: n_env >= 3 and n_iron >= 3)` in **notebooks/02_caulo_fitness_ranking.ipynb** (cell 5, line 7)
- `n_strong = (non-literal: (in_class['t'].abs() > t_threshold).sum())` in **notebooks/02_caulo_fitness_ranking.ipynb** (cell 9, line 12)
- `max_abs_t = (non-literal: abs(best_t))` in **notebooks/02_caulo_fitness_ranking.ipynb** (cell 9, line 18)
- `max_abs_t = (non-literal: np.nan)` in **notebooks/02_caulo_fitness_ranking.ipynb** (cell 9, line 21)
- `PROJ = (non-literal: Path('/home/aparkin/BERIL-research-observatory/projects/caul)` in **notebooks/02b_h2_hypergeometric_verdict.ipynb** (cell 1, line 6)
- `DATA = (non-literal: PROJ / 'data')` in **notebooks/02b_h2_hypergeometric_verdict.ipynb** (cell 1, line 7)
- `PROJ = (non-literal: Path('/home/aparkin/BERIL-research-observatory/projects/caul)` in **notebooks/03_chvi_phase_partition_sigU.ipynb** (cell 1, line 14)
- `DATA_IN = (non-literal: Path('/home/aparkin/data/kr-caulobacter-envelope/clean'))` in **notebooks/03_chvi_phase_partition_sigU.ipynb** (cell 1, line 15)
- `DATA_OUT = (non-literal: PROJ / 'data')` in **notebooks/03_chvi_phase_partition_sigU.ipynb** (cell 1, line 16)
- `FIG = (non-literal: PROJ / 'figures')` in **notebooks/03_chvi_phase_partition_sigU.ipynb** (cell 1, line 17)
- `KEYWORD_SETS = (non-literal: {'TBDT / OM receptor': 'TonB.dependent|tbd|outer.membrane.re)` in **notebooks/03_chvi_phase_partition_sigU.ipynb** (cell 6, line 8)
- `n_total = (non-literal: len(annotated_df))` in **notebooks/03_chvi_phase_partition_sigU.ipynb** (cell 6, line 21)
- `n_hit = (non-literal: mask.sum())` in **notebooks/03_chvi_phase_partition_sigU.ipynb** (cell 6, line 26)
- `PROJ = (non-literal: Path('/home/aparkin/BERIL-research-observatory/projects/caul)` in **notebooks/04_sphingolipid_lpt_panel.ipynb** (cell 1, line 12)
- `DATA_IN = (non-literal: Path('/home/aparkin/data/kr-caulobacter-envelope/clean'))` in **notebooks/04_sphingolipid_lpt_panel.ipynb** (cell 1, line 13)
- `DATA_OUT = (non-literal: PROJ / 'data')` in **notebooks/04_sphingolipid_lpt_panel.ipynb** (cell 1, line 14)
- `FIG = (non-literal: PROJ / 'figures')` in **notebooks/04_sphingolipid_lpt_panel.ipynb** (cell 1, line 15)
- `SPHINGOLIPID = (non-literal: {'CCNA_01212': 'bcerS — bacterial ceramide synthase', 'CCNA_)` in **notebooks/04_sphingolipid_lpt_panel.ipynb** (cell 2, line 2)
- `LPT_APPARATUS = (non-literal: {'CCNA_00307': 'MsbA-like phospholipid/LPS ABC transporter',)` in **notebooks/04_sphingolipid_lpt_panel.ipynb** (cell 2, line 21)
- `CTPA = (non-literal: {'CCNA_03113': 'CtpA — C-terminal processing protease; LpxE-)` in **notebooks/04_sphingolipid_lpt_panel.ipynb** (cell 2, line 31)
- `PROJ = (non-literal: Path('/home/aparkin/BERIL-research-observatory/projects/caul)` in **notebooks/05_pg_remodeling.ipynb** (cell 1, line 13)
- `DATA_IN = (non-literal: Path('/home/aparkin/data/kr-caulobacter-envelope/clean'))` in **notebooks/05_pg_remodeling.ipynb** (cell 1, line 14)
- `DATA_OUT = (non-literal: PROJ / 'data')` in **notebooks/05_pg_remodeling.ipynb** (cell 1, line 15)
- `FIG = (non-literal: PROJ / 'figures')` in **notebooks/05_pg_remodeling.ipynb** (cell 1, line 16)
- `PG_SYMBOLS = (non-literal: {'murA', 'murB', 'murC', 'murD', 'murE', 'murF', 'murG', 'mu)` in **notebooks/05_pg_remodeling.ipynb** (cell 2, line 2)
- `DESC_PATTERN = (non-literal: re.compile('transglycosylase|transpeptidase|penicillin.bindi)` in **notebooks/05_pg_remodeling.ipynb** (cell 2, line 21)
- `n_trans_sig = (non-literal: len(trans_sig))` in **notebooks/05_pg_remodeling.ipynb** (cell 5, line 2)
- `n_prot_sig = (non-literal: len(prot_sig))` in **notebooks/05_pg_remodeling.ipynb** (cell 5, line 3)
- `n_total_meeting = (non-literal: len(meeting_set))` in **notebooks/05_pg_remodeling.ipynb** (cell 5, line 7)
- `PROJ = (non-literal: Path('/home/aparkin/BERIL-research-observatory/projects/caul)` in **notebooks/06_comparative_species.ipynb** (cell 1, line 14)
- `DATA_OUT = (non-literal: PROJ / 'data')` in **notebooks/06_comparative_species.ipynb** (cell 1, line 15)
- `FIG = (non-literal: PROJ / 'figures')` in **notebooks/06_comparative_species.ipynb** (cell 1, line 16)
- `SPECIES = (non-literal: {'C_crescentus': 'caulobacter', 'A_baumannii': 'acinetobacte)` in **notebooks/06_comparative_species.ipynb** (cell 1, line 21)
- `FAMILIES = (non-literal: [('spt — serine palmitoyltransferase', 'serine.palmitoyltran)` in **notebooks/06_comparative_species.ipynb** (cell 2, line 2)
- `n_hits = (non-literal: int(df['n'].iloc[0]))` in **notebooks/06_comparative_species.ipynb** (cell 3, line 12)
- `PROJ = (non-literal: Path('/home/aparkin/BERIL-research-observatory/projects/caul)` in **notebooks/06b_ncbi_annotation_presence.ipynb** (cell 1, line 10)
- `DATA = (non-literal: PROJ / 'data')` in **notebooks/06b_ncbi_annotation_presence.ipynb** (cell 1, line 11)
- `SPECIES_TAXIDS = (non-literal: {'C_crescentus': '565050[Organism:exp] OR "Caulobacter vibri)` in **notebooks/06b_ncbi_annotation_presence.ipynb** (cell 1, line 13)
- `FOCAL = (non-literal: [('spt — serine palmitoyltransferase', ['"serine palmitoyltr)` in **notebooks/06b_ncbi_annotation_presence.ipynb** (cell 1, line 22)
- `SPHINGO = (non-literal: ['spt — serine palmitoyltransferase', 'bcerS — bacterial cer)` in **notebooks/06b_ncbi_annotation_presence.ipynb** (cell 5, line 1)
- `CHV = (non-literal: ['ChvG — sensor kinase', 'ChvI — response regulator'])` in **notebooks/06b_ncbi_annotation_presence.ipynb** (cell 5, line 6)
- `LPT = (non-literal: ['LpxA — UDP-GlcNAc acyltransferase', 'LpxC — UDP-GlcNAc dea)` in **notebooks/06b_ncbi_annotation_presence.ipynb** (cell 5, line 8)
- `PROJ = (non-literal: Path('/home/aparkin/BERIL-research-observatory/projects/caul)` in **notebooks/07_synthesis.ipynb** (cell 1, line 13)
- `DATA = (non-literal: PROJ / 'data')` in **notebooks/07_synthesis.ipynb** (cell 1, line 14)
- `FIG = (non-literal: PROJ / 'figures')` in **notebooks/07_synthesis.ipynb** (cell 1, line 15)

## Summary

- Notebooks scanned: 10
- Scripts scanned: 0
- Code cells total: 90
- Code cells skipped (parse errors): 0
- Statistical test calls: 5 (3 unique)
- Modules imported (unique): 12
- Spark queries: 4
- Packages with version info: 0
