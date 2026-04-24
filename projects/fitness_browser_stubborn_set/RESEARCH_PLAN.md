# Research Plan: The Fitness Browser Stubborn Set — Curator-Like Genes Left Unannotated

## Research Question

Using the current BERDL `kescience_fitnessbrowser.reannotation` table (1,762 curator re-annotations across 36 organisms) as a labeled "positive" set, can we identify the genes that *look like* curator targets — by the same evidence signals — but were NOT re-annotated, and can BERDL-native evidence tell us which of those left-alone genes are actually **improvable now** vs. **unresolvable from existing evidence**?

We ignore the 2018 paper's 456-gene TableS12 set. It is historical; the live curator-accumulated `reannotation` table is the only reference set that matters.

## Hypothesis

- **H0**: The 1,762 reannotated genes do not separate from the rest of the Fitness Browser on primary fitness/cofitness evidence; ranking non-reannotated genes by curator-likeness produces a flat distribution where reannotation density does not decrease meaningfully with rank. NB02's secondary evidence applied chunk-by-chunk does not yield more improvable candidates near the top of the queue than at the bottom — implying curator decisions cannot be reconstructed from BERDL-native data alone.

- **H1**: A logistic regression on six primary evidence features produces a useful **curator-likeness score**. When non-reannotated genes are ranked by this score, the strongest primary evidence sits at the top of the queue. Walking the queue top-down and reasoning over BERDL-native secondary evidence (conserved cofit, ortholog phenotype, informative domain, KEGG/SEED/MetaCyc) for each gene partitions visited genes into two outcomes:
  - **improvable-now** — secondary evidence supports a concrete annotation proposal
  - **recalcitrant** — strong primary evidence (high score) but secondary evidence does NOT support any meaningful annotation
- We stop walking after the **recalcitrant set reaches 2,000 genes**. Because we walk highest-score first, those 2,000 are the genes with the strongest primary phenotype evidence that nonetheless resist reannotation — the most-difficult-to-improve genes in the Fitness Browser. Everything walked through with a successful proposal is the **improvable** list (its size emerges from the data; not predetermined).

### Why a queue, not a threshold

Earlier exploration (preserved in v3 of this plan and in NB01's calibration table) showed that primary fitness+cofitness features cannot simultaneously achieve ≥90% recall on the 1,762 reannotated set AND a non-reannotated candidate pool under 10K genes. Best operating points:

- Logistic regression @ 90% recall: **~18K** non-reannotated above threshold
- Counting score ≥ 2: 85% recall, ~16K non-reannotated above threshold
- Strict `count ≥ 2 AND specificphenotype`: 7,724 non-reannotated, but only 68.5% recall

There is no clean cutpoint. Rather than choose one and hide the rest of the data behind it, NB01 outputs **the full ranked queue** of non-reannotated genes plus per-chunk diagnostics. NB02 walks the queue top-down, applying secondary evidence (conserved cofit, ortholog phenotype, informative domain, KEGG/SEED/MetaCyc) per chunk, and stops when the yield of "improvable-now" candidates plateaus.

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

**Restriction**: NB01 keeps only genes from the **36 organisms with at least one reannotation**. The other 12 FB organisms may be uncurated rather than reviewed-and-skipped — including their genes inflates the baseline non-reannotated pool with material the curators may never have considered.

**Scoring model**: Logistic regression on the 6 features with `class_weight='balanced'`. The predicted probability is the curator-likeness score. We use logistic regression because it dominated counting and hand-tuned compound rules in the recall-vs-pool tradeoff (preserved as supplementary tables in NB01).

**Output**: a ranked queue of all non-reannotated genes (sorted by score descending), with rank, chunk index, all evidence features, annotation category, and `gene_desc`. Per-chunk diagnostics (1,000-gene chunks) include score range, evidence-flag prevalence, annotation-category mix, and the **reannotation density in the same score band** — i.e., what fraction of genes at this score level have been reannotated. This density is the empirical signal of "is this score band still in curator-interest territory?"

Empirical observations from preliminary runs that motivate this approach:
- 73% of reannotated genes are in `specificphenotype` (1,291/1,729 with fitness data)
- 85% have any strong phenotype; 92% have specific OR strong
- 62/1,729 reannotated genes (3.6%) have none of the three binary signals
- 90% of reannotated are captured by rank ~19,700 in the full ranking
- Top-1000 chunk (highest scores): 29% reann density; chunk 7: 6% density; bottom chunks: 0% density

### Stage 2 — Walk the priority queue with secondary evidence (NB02)

NB02 walks the priority queue from rank 1 (highest score) down. For each gene, it computes the secondary evidence flags listed below and reasons over them to decide one of two outcomes:

- **improvable-now**: ≥1 conservation signal AND ≥1 informative functional signal — record the gene plus the proposed annotation rationale.
- **recalcitrant**: no conservation OR no informative functional signal — record the gene plus what evidence was considered.

**Stop condition**: when the recalcitrant tally reaches **2,000 genes**. Because the queue is sorted by curator-likeness descending, these 2,000 are the **strongest-evidence genes that nevertheless cannot be reannotated** — the answer to "which genes have strong phenotype but no resolvable function from existing evidence?" Everything walked through with a successful improvable verdict is the improvable list; its size emerges from the data.

The stopping rank (the queue position where the 2,000th recalcitrant gene lands) is the operational stubborn-set boundary. Genes below that rank in the queue have lower primary evidence and were not considered — we make no claim about them.

For each stubborn-set gene, compute a **second layer** of BERDL-native evidence flags that Price's curators could have consulted:

| Flag | Signal | Source |
|---|---|---|
| `conserved_cofit` | Any `(locusId, hitId)` cofit > 0.6 whose orthologs also cofit > 0.6 | `cofit` + `ortholog` (self-join) |
| `conserved_specific_phenotype` | Gene appears in `specog` with multiple orgs sharing the same `expGroup`/`condition` | `specog` |
| `informative_domain` | Any `genedomain` hit with `ec IS NOT NULL` OR `definition` that is not "domain of unknown function" | `genedomain` |
| `informative_kegg_ko` | KO with non-"uncharacterized" `kgroupdesc.desc` — **two-hop join** via `besthitkegg → keggmember → kgroupdesc`. Note: `kgroupdesc.desc` (not `description`); `kgroupec.ecnum` (not `ec`). | `besthitkegg`, `keggmember`, `kgroupdesc`, `kgroupec` |
| `informative_seed` | `seedannotation.seed_desc` that is not "hypothetical" — description-level only; we explicitly do NOT attempt the subsystem hierarchy (`seedannotationtoroles → seedroles`) in this project | `seedannotation` |
| `metacyc_pathway_hit` | EC from `genedomain` or `kgroupec.ecnum` links through `metacycreaction.ecnumber` → `metacycpathwayreaction.reaction_id` → `metacycpathway` | `genedomain`/`kgroupec` → `metacycreaction` → `metacycpathwayreaction` → `metacycpathway` |

### Stage 3 — Characterise improvable + recalcitrant sets (NB03)

**Existing annotation is a descriptive dimension, NOT a filter.** We characterise the existing `gene.desc` of every walked gene (improvable + recalcitrant) and contrast it with the 1,729 reannotated set:

| Category | Definition (regex-style on `gene.desc`, lower-cased) |
|---|---|
| `hypothetical` | contains "hypothetical", "uncharacterized", or is empty / bare locus tag |
| `DUF` | matches "DUF\d+" or "domain of unknown function" or "UPF\d+" |
| `vague` | contains "putative", "predicted", or "probable" without a specific function |
| `named_enzyme` | has an enzyme class / EC-style name (e.g., "...-ase", ligase, reductase, transporter, kinase) |
| `named_other` | any other concrete functional name |

**Reporting grid** — contingency table of `existing-annotation-category × outcome`:

|  | Improvable | Recalcitrant | Reannotated (1,729 reference) |
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

### Notebook 01 — Curator-like priority queue
- **Goal**: Restrict to the 36 curated organisms; fit logistic regression on the 6 primary evidence features; rank all non-reannotated genes by predicted score; emit per-chunk diagnostics (1,000-gene chunks) including reannotation density in the same score band. No threshold is chosen.
- **Expected output**: `data/priority_queue.parquet`, `data/chunk_summary.csv`, `data/reannotation_milestones.csv`, `figures/fig01_priority_queue.png`, `figures/fig02_rank_distribution.png`.

### Notebook 02 — Walk priority queue with secondary evidence (stop at 2,000 recalcitrant)
- **Goal**: Walk the priority queue rank 1 → N. For each gene, compute the six secondary-evidence flags and decide improvable vs recalcitrant per the rule above. Stop when the recalcitrant tally hits 2,000.
- **Expected output**: `data/improvable.parquet` (variable size; all genes with a proposed annotation rationale), `data/recalcitrant.parquet` (exactly 2,000 rows by construction; the strongest-evidence un-reannotatable genes), `data/walk_log.csv` (per-chunk improvable/recalcitrant yields, running tallies), `figures/fig03_walk_progress.png`.

### Notebook 03 — Characterise improvable + recalcitrant + reannotated
- **Goal**: Produce the `annotation-category × outcome` contingency grid for {improvable, recalcitrant, reannotated}. For the 1,729 reannotated reference: characterise *what kind* of reannotation curators performed (hypothetical → named, named → re-named, etc.) by comparing pre-reannotation `gene.desc` to the curator's `new_annotation`. Cross-reference improvable + recalcitrant with `functional_dark_matter` (17,344) and `truly_dark_genes` (6,427) lakehouse outputs.
- **Expected output**: `data/outcome_summary.parquet`, headline figures, contingency tables.

### Notebook 04 — Spot-check and narrative
- **Goal**: ~20 per-gene dossiers covering both improvable categories (hypothetical × improvable, named × improvable) AND ~10 dossiers from the recalcitrant set (the hardest unimprovable cases) as qualitative sanity check.
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
- **v4** (2026-04-24): Confirmed empirically that the dual target (≥90% recall AND <10K stubborn) is not reachable from primary fitness+cofitness features alone. Best logistic operating point at 90% recall is ~18K stubborn (after restricting to the 36 curated organisms). Two-stage AND/OR stacking with the counting rule does not break the frontier. **Reframed NB01's deliverable from a thresholded stubborn-set to a ranked priority queue**: every non-reannotated gene gets a curator-likeness score, the queue is sorted, and per-chunk diagnostics expose where reannotation density falls off.
- **v5** (2026-04-24): Concrete stopping rule for NB02. Walk the priority queue rank 1 → N (highest curator-likeness first). For each gene, reason over secondary BERDL-native evidence to decide improvable vs recalcitrant. **Stop when the recalcitrant tally reaches exactly 2,000 genes.** Because we walk highest-score first, those 2,000 are the strongest-primary-evidence genes that nevertheless resist reannotation — the bounded, well-defined "recalcitrant set" answering the original research question. The improvable set is whatever is walked-and-improved before hitting 2,000 recalcitrant; its size emerges from the data. The stopping rank is the operational stubborn-set boundary; genes below it in the queue are not considered.

## Authors
- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
