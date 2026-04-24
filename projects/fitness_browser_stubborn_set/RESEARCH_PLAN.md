# Research Plan: The Fitness Browser Stubborn Set — Curator-Like Genes Left Unannotated

## Research Question

Using the current BERDL `kescience_fitnessbrowser.reannotation` table (1,762 curator re-annotations across 36 organisms) as a labeled "positive" set, can we identify the genes that *look like* curator targets — by the same evidence signals — but were NOT re-annotated, and can BERDL-native evidence tell us which of those left-alone genes are actually **improvable now** vs. **unresolvable from existing evidence**?

We ignore the 2018 paper's 456-gene TableS12 set. It is historical; the live curator-accumulated `reannotation` table is the only reference set that matters.

## Hypothesis

- **H0**: The 1,762 reannotated genes do not separate from the rest of the Fitness Browser by any weighted combination of BERDL-native evidence signals (specific phenotype, strong fitness, cofitness, and their magnitudes). There is no classifier that simultaneously (a) recovers ≥90% of the reannotated set and (b) yields a stubborn candidate pool under ~10K genes — implying curator decisions cannot be reconstructed from these signals alone.

- **H1**: A weighted classifier fit on the continuous evidence features (`in_specificphenotype`, `max_abs_fit`, `max_abs_t`, `n_strong_experiments`, `n_moderate_experiments`, `max_cofit`) can achieve the **dual target of ≥90% recall on the 1,762 reannotated set AND a stubborn candidate pool < ~10K genes**. Within that stubborn set, secondary BERDL-native evidence (ortholog phenotype conservation, informative domain, KEGG KO description, SEED annotation, MetaCyc pathway) separates genes where a new annotation is plausibly proposable from genes where existing evidence is genuinely insufficient.

### Dual target (operational definition of "tractable")

- **Recall** ≥ 90% of reannotated genes score above threshold.
- **Stubborn pool size** < 10,000 genes (non-reannotated in the candidate pool).

If neither a weighted score over the raw features nor a hand-tuned compound rule can hit both, we document the frontier (the recall-vs-pool-size tradeoff curve) as the finding, and pick the best available operating point before moving to NB02.

## Approach Overview

### Stage 1 — Threshold derivation (NB01)

We treat the 1,762 reannotated genes as **positive examples** and fit a weighted classifier over continuous BERDL-native evidence features.

**Evidence features** (per gene, computed once in `notebooks/00_extract_gene_features.py` and saved locally as parquet so the notebook is pandas-only):

| Feature | Type | Source |
|---|---|---|
| `in_specificphenotype` | binary 0/1 — Price's precomputed specific-phenotype flag | `specificphenotype` |
| `max_abs_fit` | continuous — largest \|fit\| across experiments | `genefitness` (CAST DOUBLE) |
| `max_abs_t` | continuous — largest \|t\| across experiments | `genefitness` (CAST DOUBLE) |
| `n_strong_experiments` | count — experiments with \|fit\|≥2 AND \|t\|≥5 | `genefitness` |
| `n_moderate_experiments` | count — experiments with \|fit\|≥1 AND \|t\|≥5 | `genefitness` |
| `max_cofit` | continuous [0,1] — largest cofit with any partner in same org | `cofit` (CAST DOUBLE) |

**Classifier candidates** (NB01 will fit all three and pick the one that hits the dual target):

1. **Simple counting rule** (baseline): binary criteria C1 = `in_specificphenotype`, C2 = `n_strong_experiments ≥ 1`, C3 = `max_cofit ≥ 0.75`; `score = C1 + C2 + C3`; threshold chosen to hit ≥90% recall. Empirically (preliminary results) this gives 96% recall at score ≥ 1 (41K stubborn — too big) or 85% recall at score ≥ 2 (18K stubborn — still too big), so the simple rule alone cannot hit both targets.
2. **Logistic regression** on all 6 continuous features with `class_weight='balanced'`. Use the predicted probability as the score; threshold = smallest probability that keeps recall ≥ 90%. Report learned weights for interpretability.
3. **Hand-tuned compound rule** — e.g., tighter cofit cutoff (≥ 0.85 instead of ≥ 0.75), or requiring at least one of {specific, strong} plus something. NB01 will enumerate a small set of compound rules around the recall-vs-pool tradeoff frontier.

**Candidate pool** = `{ genes above the chosen classifier's threshold }`.
**Stubborn set** = `candidate_pool ∖ reannotation`.

Preliminary observations from the extract that motivate this design:
- 73% of reannotated genes are in `specificphenotype` (1,291/1,729 with fitness data)
- 85% have any strong phenotype (1,472/1,729)
- Of the 471 reannotated not in `specificphenotype`, 73% have max cofit ≥ 0.75 (mean max cofit = 0.85) — cofitness is an independent curator signal
- 62/1,729 reannotated genes (3.6%) have NONE of the three binary signals — those are curated on other grounds (conserved ortholog phenotype alone, comparative-genomics operon context) and may be unrecoverable from these features; the 90% recall target implicitly accepts losing roughly those.

### Stage 2 — Evidence scoring on the stubborn set (NB02)

For each stubborn-set gene, compute a **second layer** of BERDL-native evidence flags that Price's curators could have consulted:

| Flag | Signal | Source |
|---|---|---|
| `conserved_cofit` | Any `(locusId, hitId)` cofit > 0.6 whose orthologs also cofit > 0.6 | `cofit` + `ortholog` (self-join) |
| `conserved_specific_phenotype` | Gene appears in `specog` with multiple orgs sharing the same `expGroup`/`condition` | `specog` |
| `informative_domain` | Any `genedomain` hit with `ec IS NOT NULL` OR `definition` that is not "domain of unknown function" | `genedomain` |
| `informative_kegg_ko` | KO with non-"uncharacterized" `kgroupdesc.desc` — **two-hop join** via `besthitkegg → keggmember → kgroupdesc`. Note: `kgroupdesc.desc` (not `description`); `kgroupec.ecnum` (not `ec`). | `besthitkegg`, `keggmember`, `kgroupdesc`, `kgroupec` |
| `informative_seed` | `seedannotation.seed_desc` that is not "hypothetical" — description-level only; we explicitly do NOT attempt the subsystem hierarchy (`seedannotationtoroles → seedroles`) in this project | `seedannotation` |
| `metacyc_pathway_hit` | EC from `genedomain` or `kgroupec.ecnum` links through `metacycreaction.ecnumber` → `metacycpathwayreaction.reaction_id` → `metacycpathway` | `genedomain`/`kgroupec` → `metacycreaction` → `metacycpathwayreaction` → `metacycpathway` |

### Stage 3 — Partition + annotation-category analysis (NB03)

**Existing annotation is a descriptive dimension, NOT a filter.** We keep all stubborn-set genes and characterise the categories of their existing `gene.desc`:

| Category | Definition (regex-style on `gene.desc`, lower-cased) |
|---|---|
| `hypothetical` | contains "hypothetical", "uncharacterized", or is empty / bare locus tag |
| `DUF` | matches "DUF\d+" or "domain of unknown function" or "UPF\d+" |
| `vague` | contains "putative", "predicted", or "probable" without a specific function |
| `named_enzyme` | has an enzyme class / EC-style name (e.g., "...-ase", ligase, reductase, transporter, kinase) |
| `named_other` | any other concrete functional name |

Then partition the stubborn set on evidence (not on existing annotation):
- **Improvable-now**: ≥1 conservation signal (`conserved_cofit` OR `conserved_specific_phenotype`) AND ≥1 informative functional signal (`informative_domain` OR `informative_kegg_ko` OR `informative_seed` OR `metacyc_pathway_hit`).
- **Unresolvable-from-evidence**: no conservation AND no informative signal.
- **Mixed**: everything else (transparency bucket).

**Reporting grid** — contingency table of `existing-annotation-category × evidence-partition`:

|  | Improvable | Unresolvable | Mixed |
|---|---|---|---|
| hypothetical | N | N | N |
| DUF | N | N | N |
| vague | N | N | N |
| named_enzyme | N | N | N |
| named_other | N | N | N |

The scientific questions this table answers:
- **How many hypotheticals remain hypothetical?** (hypothetical × unresolvable cell) — these are the genuinely dark genes with strong curator-like evidence but no resolvable function.
- **How many previously-mis-annotated genes were reassigned?** — measured in the 1,762 reannotated set by comparing the pre-reannotation `gene.desc` category to the curator's new annotation. The `named_enzyme` and `named_other` reannotations that got a *different* specific function are the "correction" cases; the `hypothetical`/`DUF`/`vague` ones that got a specific function are the "new-name" cases.
- **Improvable named genes** (named_* × improvable) are candidates for *correction* — existing name may be wrong given fitness + cofit evidence.
- **Improvable hypotheticals** (hypothetical × improvable) are candidates for *assignment* — proposing a new name based on existing evidence.

### Stage 4 — Spot-check (NB04)

Sample ~20 Improvable candidates across organisms and functional classes; produce per-gene dossiers (fitness heatmap for driving condition, top cofitness partners with their annotations, best ortholog + its phenotype, domain hits, KEGG KO). Qualitative sanity check that the partition makes biological sense.

## Literature Context

**Primary reference**: Price MN et al. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature* 557(7706):503-509. DOI: [10.1038/s41586-018-0124-0](https://doi.org/10.1038/s41586-018-0124-0). PMID: 29769716.

**Authoritative thresholds** (from [Fitness Browser help page](https://fit.genomics.lbl.gov/cgi-bin/help.cgi)):
- Usable t-score: `|t| ≥ 4`
- Strong phenotype: `|fit| > 2`
- Specific phenotype: `|fit| > 1 AND |t| > 5 AND |fit|₉₅ < 1 AND |fit| > |fit|₉₅ + 0.5` (precomputed in `specificphenotype` — we use the precomputed table rather than recomputing)
- Significant cofitness: `cofit > 0.75 AND rank ∈ {1, 2}`
- Conserved cofitness: `cofit > 0.6 AND cofit_ortholog > 0.6`

**Adjacent prior work in this repo** (distinct framings; we do not duplicate):
- [projects/truly_dark_genes](../truly_dark_genes/) — bakta v1.12.0 re-annotation (new compute). We stay BERDL-native.
- [projects/functional_dark_matter](../functional_dark_matter/) — GapMind pathway gaps + domain matching. We are curator-decision-boundary.
- [projects/fitness_effects_conservation](../fitness_effects_conservation/) — fitness vs. core/accessory.
- [projects/cofitness_coinheritance](../cofitness_coinheritance/) — cofit structure.

Cross-project reuse: in NB03 we will refer to `functional_dark_matter`'s 17,344-gene strong-phenotype-dark set and `truly_dark_genes`' 6,427 bakta-resistant set via their lakehouse archives (not by re-derivation); the overlap with our stubborn set is a secondary characterisation, not a core finding.

## Query Strategy

### Tables required (all `kescience_fitnessbrowser` unless noted)

| Table | Purpose | Est. Rows | Filter Strategy |
|---|---|---|---|
| `reannotation` | **Reference positive set (1,762)** | 1,762 | Direct load |
| `gene` | Locus metadata + existing description (for NB03 filter) | 228,709 | Filter to candidate loci |
| `genefitness` | Per-experiment fitness + t (strings; CAST) | 27,410,721 | GroupBy (`orgId`, `locusId`) with filters — one pass |
| `specificphenotype` | Precomputed Price specific-phenotype flag | 38,525 | Direct join |
| `cofit` | Per-pair cofitness within organism | 13,656,145 | Always filter by `orgId` + `locusId` |
| `specog` | Conserved specific phenotype across orthologs | varies | Join for `conserved_specific_phenotype` |
| `ortholog` | BBH orthologs across organisms | millions | Self-join on `cofit` for `conserved_cofit` |
| `genedomain` | TIGRFam/Pfam/CDD domain hits | millions | Join on candidate loci |
| `besthitkegg` | FB locus → KEGG gene | 200,074 | **Two-hop KO mapping** (see pitfall) |
| `keggmember` | KEGG gene → KO | 82,687 | Second hop |
| `kgroupdesc` | KO → description (**`desc` not `description`**) | 4,938 | Join on `kgroup` |
| `kgroupec` | KO → EC (**`ecnum` not `ec`**) | 2,513 | Join on `kgroup` |
| `seedannotation` | SEED description per locus (`seed_desc`) | 177,519 | Description-level only |
| `metacycreaction` | EC → reaction | 20,793 | Filter on EC |
| `metacycpathwayreaction` | Reaction ↔ pathway linking table (**required middle hop**) | varies | Chain |
| `metacycpathway` | Pathway metadata | 3,512 | Join on `pathway_id` |

### Performance plan

- **Primary environment**: BERDL JupyterHub for notebooks (direct Spark access). Local iteration via `/berdl-query` with proxy chain for interactive SQL checks only; all notebook cells use `get_spark_session()` from either JupyterHub or the local `.venv-berdl` drop-in (see `PROJECT.md` for the exact import rules).
- **Estimated complexity**: Moderate. The heaviest step is the one-pass aggregation over `genefitness` (27M rows) in NB01 — a groupBy on `(orgId, locusId)` with max/count aggregations. Spark handles this efficiently; no `.toPandas()` on large intermediates.
- **Filters**: always filter `cofit` by `orgId` before any expensive operation. Candidate-pool filtering in NB02 reduces the working set from 228K genes to the stubborn set size before any self-join or multi-hop join.

### Known pitfalls (from [docs/pitfalls.md](../../docs/pitfalls.md))

- `genefitness.fit`, `.t`, `cofit.cofit` are stored as **strings** → CAST to DOUBLE before ABS/compare.
- FB KO mapping is a **two-hop join** (`besthitkegg` → `keggmember`).
- `kgroupdesc` column is `desc` (not `description`).
- `kgroupec` column is `ecnum` (not `ec`).
- `experiment.expGroup` (not `Group`).
- `seedannotationtoroles` joins on `seed_desc` — we avoid this hierarchy and stay at description level.
- MetaCyc pathway linkage requires `metacycpathwayreaction` as a middle table between `metacycpathway` and `metacycreaction`.

## Analysis Plan

### Extract 00 — `notebooks/00_extract_gene_features.py` (Spark, plain Python)
- **Goal**: Pull all per-gene evidence features from Spark Connect into a local pandas parquet so notebooks are pandas-only (avoids Spark Connect + nbconvert JSON-serialization bugs). Includes `gene.desc` / `gene.gene` for annotation-category analysis.
- **Expected output**: `data/gene_evidence_features.parquet`.

### Notebook 01 — Threshold derivation via weighted classifier
- **Goal**: Load local extract; fit a weighted classifier (logistic regression on continuous features) alongside the simple counting baseline and a small set of hand-tuned compound rules. Pick the operating point that hits the dual target (≥90% recall AND <10K stubborn), or document the tradeoff curve if neither side of the target is feasible. Report learned weights, the recall-vs-pool-size frontier, and the final chosen rule.
- **Expected output**: `data/stubborn_set_chosen.parquet`, `data/threshold_calibration_summary.csv`, `figures/fig01_score_distribution.png`, `figures/fig02_recall_vs_pool_size.png`.

### Notebook 02 — Secondary evidence scoring + annotation categorisation
- **Goal**: For each stubborn-set gene, compute the six secondary-evidence flags (conserved cofit, conserved specific phenotype, informative domain, informative KEGG KO, informative SEED, MetaCyc pathway hit). Also categorise each gene's **existing** `gene.desc` into {hypothetical, DUF, vague, named_enzyme, named_other}. **Annotation category is descriptive, not a filter.**
- **Expected output**: `data/stubborn_set_scored.parquet` (per-flag booleans + annotation category), `figures/fig03_evidence_flag_upset.png`, `figures/fig04_annotation_category_distribution.png`.

### Notebook 03 — Partition + reporting grid
- **Goal**: Apply the improvable / unresolvable / mixed partition (evidence-based, not annotation-based). Produce the `annotation-category × partition` contingency grid. Similar grid for the 1,762 reannotated set to characterise *what kind* of reannotation curators performed (hypothetical → named, named → re-named, etc.). Cross-reference stubborn set with `functional_dark_matter` 17,344 and `truly_dark_genes` 6,427 lakehouse outputs.
- **Expected output**: `data/stubborn_set_partitioned.parquet`, headline figures, contingency tables.

### Notebook 04 — Spot-check and narrative
- **Goal**: ~20 per-gene dossiers covering both types of improvable candidate (hypothetical × improvable, named × improvable) as qualitative sanity check.
- **Expected output**: `data/spot_check_dossiers/*.md`, narrative for REPORT.md.

## Expected Outcomes

- **If H1 supported**: The weighted score recovers ≥95% of the 1,762 reannotated set, the stubborn set is tractable (few thousand or smaller), and the secondary-evidence partition produces a short actionable list of "improvable-now" genes with poor existing annotation — an immediate curator hand-off.
- **If H0 not rejected**: Either the score doesn't separate the reannotated set from the rest, OR the stubborn set is intractably large under any threshold choice, OR the secondary evidence doesn't partition. That would indicate curator decisions are driven by something beyond the signals we've captured (e.g., organism priority, experimental interest, wet-lab follow-up). Still informative.
- **Confounders**:
  - The `reannotation` table covers only 36 of 48 organisms; recent organisms may not have been curated yet, and a strong phenotype in an uncurated organism is not comparable to the same in a curated one. We'll check organism-level coverage in NB01 and possibly restrict to the 36 curated organisms.
  - The 33 reannotated genes with no `genefitness` records won't score on C2 but are still in the positive set — they presumably drove curator interest via cofitness or conserved ortholog evidence alone.
  - Our "informative" tests (KEGG KO description, SEED description) are text-based heuristics. A KO named "conserved membrane protein" may or may not be informative depending on stance.

## Revision History

- **v1** (2026-04-24): Initial plan. Used a Price-faithful specific-phenotype recomputation as the candidate pool and positioned the paper's 456-gene TableS12 as a reference set.
- **v2** (2026-04-24): Scope narrowed to the current BERDL `reannotation` table (1,762) as the sole reference. Replaced the manual specific-phenotype recomputation with the precomputed `specificphenotype` table plus a three-signal weighted classifier (C1 specific, C2 strong, C3 cofitness) calibrated to capture ≥95% of the reannotated set. Addressed Codex plan-review critical items: (i) use `specificphenotype` directly rather than recomputing `|fit|₉₅`; (ii) MetaCyc path includes the `metacycpathwayreaction` middle table; (iii) KEGG EC uses `kgroupec.ecnum`. Also pinned execution environment (JupyterHub Spark primary, local via `.venv-berdl` for interactive work) and explicitly scoped out the SEED subsystem hierarchy.
- **v3** (2026-04-24): Empirical finding from NB01 preliminary run — the 3-signal binary counting rule cannot hit both targets: score ≥ 1 gives 96% recall but 41K stubborn; score ≥ 2 gives 85% recall with 18K stubborn; no integer threshold hits ≥90% recall with <10K stubborn. Changed approach: fit a **weighted classifier** (logistic regression on the 6 continuous evidence features) in NB01, explicitly targeting **≥90% recall AND <10K stubborn**. Added hand-tuned compound rules as comparison points and a recall-vs-pool-size frontier figure. Refactored execution: heavy Spark work moved to a plain `.py` extract script (`notebooks/00_extract_gene_features.py`) producing a local pandas parquet; the analysis notebook is pandas-only to avoid Spark-Connect + nbconvert serialization failures (PlanMetrics is not JSON-serializable and breaks both `jupyter nbconvert` and `pandas.to_parquet` when attached via `df.attrs`). Also changed existing-annotation handling: categorise (`hypothetical`, `DUF`, `vague`, `named_enzyme`, `named_other`) as a **descriptive dimension**, not a filter. Added the `annotation-category × evidence-partition` contingency grid as the primary reporting output.

## Authors
- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
