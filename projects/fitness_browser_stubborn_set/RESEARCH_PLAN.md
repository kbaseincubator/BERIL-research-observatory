# Research Plan: The Fitness Browser Stubborn Set — Curator-Like Genes Left Unannotated

## Research Question

Using the current BERDL `kescience_fitnessbrowser.reannotation` table (1,762 curator re-annotations across 36 organisms) as a labeled "positive" set, can we identify the genes that *look like* curator targets — by the same evidence signals — but were NOT re-annotated, and can BERDL-native evidence tell us which of those left-alone genes are actually **improvable now** vs. **unresolvable from existing evidence**?

We ignore the 2018 paper's 456-gene TableS12 set. It is historical; the live curator-accumulated `reannotation` table is the only reference set that matters.

## Hypothesis

- **H0**: The 1,762 reannotated genes do not separate from the rest of the Fitness Browser by any simple combination of BERDL-native evidence signals (specific phenotype, strong fitness, significant cofitness). Any threshold that captures the reannotated set also captures a "stubborn set" that is either intractably large or indistinguishable from the reannotated genes on secondary evidence — implying there is no principled answer to "which of these can be reannotated now?"

- **H1**: A simple weighted score over three curator-relevant signals (specific phenotype flag, any strong phenotype, max cofitness ≥ 0.75) captures ≥95% of the reannotated set, and the resulting candidate pool minus reannotation yields a tractable "stubborn set" (target: low thousands or smaller). Within that stubborn set, secondary BERDL-native evidence (ortholog phenotype conservation, informative domain, KEGG KO description, SEED annotation, MetaCyc pathway) separates genes where a new annotation is plausibly proposable from genes where the evidence is genuinely insufficient.

## Approach Overview

### Stage 1 — Threshold derivation (NB01, formalized here)

We treat the 1,762 reannotated genes as **positive examples** and back out the evidence thresholds that characterise them.

**Three evidence signals** (each binary, weight 1):

| Signal | Definition | Source tables |
|---|---|---|
| **C1 — specific phenotype** | Gene appears in `specificphenotype` (Price's precomputed 4-condition test: `|fit|>1 AND |t|>5 AND |fit|₉₅<1 AND |fit|>|fit|₉₅+0.5`) | `specificphenotype` |
| **C2 — strong phenotype** | Any experiment with `|fit|≥2 AND |t|≥5` | `genefitness` (CAST to DOUBLE first — see pitfall) |
| **C3 — significant cofitness** | `max_cofit ≥ 0.75` with any partner in the same organism | `cofit` |

**Score = C1 + C2 + C3**, integer 0–3.

**Calibration rule**: choose the **largest** score threshold such that ≥95% of the 1,762 reannotated set scores at-or-above it. This is the narrowest evidence envelope that still recovers the curator's positive set.

Empirical observations from preliminary queries that motivate this design:
- **73% of reannotated are in `specificphenotype`** (1,291/1,762)
- **84% have a strong phenotype** in at least one experiment (1,472/1,762)
- **92% have either specific or strong phenotype** (1,618/1,762)
- Of the 471 reannotated genes NOT in `specificphenotype`, **73% have max cofit ≥ 0.75** (mean max cofit = 0.85) — cofitness is an independent curator signal.

The union of the three signals therefore captures very nearly all reannotated genes. The threshold calibration decides how narrowly to hold the candidate pool.

**Candidate pool** = `{ genes with score ≥ chosen_threshold }`.
**Stubborn set** = `candidate_pool ∖ reannotation`.

We commit to the chosen threshold in NB01 once the distributions are visible. A tractable target is a stubborn set of a few thousand or smaller.

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

### Stage 3 — Partition + filter (NB03)

1. Filter the stubborn set to genes with **poor existing annotation** — `gene.desc` matching "hypothetical", "DUF", "uncharacterized", "predicted", or a bare locus tag. No point proposing improvements for genes that already have a meaningful name.
2. Partition:
   - **Improvable-now**: ≥1 conservation signal (`conserved_cofit` OR `conserved_specific_phenotype`) AND ≥1 informative functional signal (`informative_domain` OR `informative_kegg_ko` OR `informative_seed` OR `metacyc_pathway_hit`).
   - **Unresolvable-from-evidence**: no conservation AND no informative signal.
   - **Mixed**: everything else (transparency bucket).

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

### Notebook 01 — Threshold Derivation (this stage)
- **Goal**: Build per-gene evidence features, score every FB gene on C1+C2+C3, calibrate the score threshold to capture ≥95% of the 1,762 reannotated set, report the resulting stubborn-set size.
- **Expected output**: `data/gene_evidence_features.parquet`, `data/stubborn_set_score_ge_{threshold}.parquet`, `data/threshold_calibration_summary.csv`, `figures/fig01_score_distribution.png`.

### Notebook 02 — Secondary evidence scoring
- **Goal**: For each stubborn-set gene, compute the six secondary-evidence flags.
- **Expected output**: `data/stubborn_set_scored.parquet` (per-flag booleans preserved for audit), `figures/fig02_evidence_flag_upset.png`.

### Notebook 03 — Partition + existing-annotation filter + characterization
- **Goal**: Filter the stubborn set to genes with poor existing annotation (`gene.desc`), apply the improvable / unresolvable / mixed partition, cross-reference with `functional_dark_matter` and `truly_dark_genes` lakehouse outputs.
- **Expected output**: `data/stubborn_set_partitioned.parquet`, headline figures, numeric summaries.

### Notebook 04 — Spot-check and narrative
- **Goal**: ~20 per-gene dossiers for Improvable candidates as qualitative sanity check.
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

## Authors
- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
