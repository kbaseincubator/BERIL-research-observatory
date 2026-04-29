# Gene-Function Agent Training Set (v2)

A self-contained training corpus for a gene-function annotation agent, built from the Fitness Browser microbial fitness data and benchmarked against expert human curators. Each labeled gene carries the full 8-layer evidence dossier the agent should reason over, plus the labels and rationales from one or more reasoning sources (LLMs, human curators, or both).

## What's in this directory

| File | Rows | Source of labels | Best use |
|---|---:|---|---|
| `human_validated.jsonl` | **1,762** | **Price-lab expert curators** (BERDL `kescience_fitnessbrowser.reannotation`) | **Strongest positive training signal** — every row is a human-validated function name with a written rationale |
| `llm_vs_human_disagreements.jsonl` | 868 | Subset of `human_validated` where the LLM (Claude Sonnet 4.6) endorsed the original FB description or said `recalcitrant`, but the human curator went deeper | **Hard examples** — teaches the agent to refine when an LLM would have stopped |
| `negatives.jsonl` | 755 | Two-LLM agreement that the gene cannot be annotated from current evidence | True negatives — examples of "no annotation is justified" |
| `positives.jsonl` | 445 | Two-LLM agreement that the existing FB annotation is defensible | "Floor of LLM-defensible existing names" — see calibration notes for the right framing |
| `target_gene_homologs.tsv` | 8,657 | Per (target gene × PaperBLAST homolog) deduplicated mapping | Lookup: "what homologs does my FB gene have?" + alignment statistics for ranking |
| `target_gene_paperblast_summaries.tsv` | 16,618 | Per (target gene × PaperBLAST homolog × paper) flattened TSV with summaries | Companion file: lets the agent join target → homolog → paper → summary at runtime without rebuilding |
| `target_gene_interpro_union.tsv` | 15,698 | Per (target gene × InterPro entry) consolidated across the three sources below; carries pangenome cluster metadata for every gene (`unknown` when the gene has no FB↔pangenome link) | **Default InterPro layer.** 82.6% gene coverage (2,447 / 2,962); 67% of rows have ≥ 2 corroborating sources |
| `target_gene_ortholog_fitness.tsv` | 39,950 | Per (target gene × FB BBH ortholog) — for every cross-organism BBH partner of a target gene, the ortholog's own fitness profile + a gene-level (BBH ratio) and organism-level (shared GTDB ranks) distance signal | **Cross-organism fitness evidence.** Lets the agent reason "this target's ortholog in X shows phenotype on Y" — covers 80.9% of training genes |
| `fb_organism_gtdb_lineage.tsv` | 36 | Per FB orgId — full GTDB lineage (domain through species), majority-vote of pangenome cluster placements from `fb_pangenome_link.tsv` joined to `kbase_ke_pangenome.gtdb_taxonomy_r214v1`; FB-fallback genus/species for orgs not in the pangenome | Lookup: full taxonomic context for each FB organism |
| `target_gene_interpro.tsv` | 13,238 | UniProt-route audit trail — per (gene × InterPro entry) via `locusxref` → `kescience_interpro` | Audit / source-specific reuse |
| `target_gene_interproscan.tsv` | 15,552 | MD5-route audit trail — bridged by MD5 sequence match against `kbase_ke_pangenome.interproscan_*` tables | Audit / source-specific reuse |
| `target_gene_interpro_cluster.tsv` | 19,533 | Cluster-route audit trail — bridged via DIAMOND best-hit to pangenome cluster representative | Audit / source-specific reuse (raw alignment quality + per-hit conservation flags) |

The four `.jsonl` files share a common base schema (`orgId`, `locusId`, `dossier_md`) plus per-file extensions documented below. The `.tsv` companion has a different shape — see the dedicated section below.

## Source data

### The Fitness Browser (`kescience_fitnessbrowser`)

Price et al. (LBNL) ran transposon-mutant fitness assays across **36 bacterial / archaeal organisms**, 137,798 genes, hundreds of growth conditions per organism. Strong negative fitness in a specific condition is the primary phenotypic signal — "this gene matters for growing in X."

Key tables consumed (all `kescience_fitnessbrowser`):

| Table | Role |
|---|---|
| `gene` | Existing per-gene description (`gene.desc`) and symbol |
| `genefitness` | Per-condition fitness + t-statistic, 27M rows |
| `specificphenotype` | Precomputed Price-thresholded specific-phenotype flag |
| `cofit` | Per-pair cofitness within an organism |
| `specog` | Conserved specific phenotype across orthologs |
| `ortholog` | BBH orthologs across organisms |
| `genedomain` | TIGRFam / Pfam / CDD domain hits |
| `besthitkegg`, `keggmember`, `kgroupdesc`, `kgroupec` | KEGG KO and EC mapping (two-hop) |
| `seedannotation` | SEED description |
| `reannotation` | **1,762 expert curator re-annotations across 36 organisms** — the gold-standard reference for `human_validated.jsonl` |

### PaperBLAST literature corpus

For each FB gene, DIAMOND blastp (evalue ≤ 1e-5, identity ≥ 30%, qcov ≥ 50%) against the PaperBLAST `uniq` database (815K characterized homologs) returns up to ~25 cited papers per gene. We summarized **9,633 unique papers** with Codex (gpt-5.5) reading the PMC full-text XML — one per-(paper, gene_identifier) summary in the canonical 4-column format used downstream.

### The 8-layer evidence dossier

Every labeled gene in this set has its full evidence dossier inlined as `dossier_md`. The dossier is what the agent reads to reason about a gene:

1. **Existing annotation** — `gene.desc`, `gene_symbol`, annotation category (hypothetical / DUF / vague / named_enzyme / named_other)
2. **Primary fitness** — max |fit|, max |t|, strong-experiment count, max cofit
3. **Phenotype with conditions** — top experiments by |fit|, with the condition (carbon source, nitrogen source, stress, etc.)
4. **Cofitness partners** — top cofit partners with their `gene.desc`, including conserved-cofit flag
5. **Genomic neighborhood** — ±5 positions on the same scaffold, each neighbor's `gene.desc` and strand
6. **Sequence-based hits** — SwissProt (best RAPSearch2 hit + identity + curated description), Pfam/TIGRFam domains (top 5 by score), KEGG KO + EC (two-hop), SEED description
7. **Conservation flags** — conserved cofit, conserved specific phenotype
8. **PaperBLAST literature** — top homolog hits + cited papers; per-paper Codex summaries where available

The dossier is built by [`notebooks/dossier.py`](../../notebooks/dossier.py) and reproducible for any (orgId, locusId).

## LLM models and settings

All LLM-derived artifacts in this directory (Codex paper summaries, Claude classification verdicts, Codex cross-check verdicts, all rationales) were produced by the exact CLI invocations below. Model versions and CLI versions are pinned here for reproducibility — the `sonnet` alias in particular resolves to whichever Sonnet revision is current at runtime, so the value here is what it resolved to during this run, not a forward-stable identifier.

| Pipeline step | Tool | Model | CLI invocation (key flags) |
|---|---|---|---|
| Per-paper PaperBLAST summaries | Codex CLI | `gpt-5.5` | `codex exec --model gpt-5.5 --sandbox workspace-write --ephemeral --output-last-message <out>` |
| Abstract-only fallback summaries | Codex CLI | `gpt-5.5` | same as above |
| Alt-source / title-search fallback | Codex CLI | `gpt-5.5` | same as above |
| 4-class classification (Claude) | Claude Code CLI | `sonnet` (resolved to **Claude Sonnet 4.6** during this run) | `claude -p --model sonnet --no-session-persistence` |
| Augmented-dossier cross-check (Codex) | Codex CLI | `gpt-5.5` | `codex exec --model gpt-5.5 --sandbox workspace-write --ephemeral --output-last-message <out>` |

**CLI versions** at generation time:

- Claude Code: **2.1.96**
- Codex CLI: **0.125.0**

**Settings notes**:

- `--ephemeral` (Codex) ensures each gene's classification runs in a fresh, isolated workspace — no cross-gene state leakage between batches.
- `--no-session-persistence` (Claude) gives the same isolation guarantee for the Claude side.
- `--sandbox workspace-write` (Codex) restricts filesystem access to the working directory; no network or system-level side effects.
- Default sampling parameters are used (no temperature override). For 4-class verdicts the LLMs run essentially deterministically because the prompt strongly constrains output to a JSONL line of fixed shape.
- The same prompt template is used for every gene within a step; see the `prompt.txt` artifacts inside each batch directory for the exact text the model received.

The exact prompt contents (which evolved as the dossier was augmented across the pipeline — paper summaries, then InterPro union, then ortholog fitness) are captured per-batch in `batches_*/batch_*/prompt.txt` for the labels in `negatives.jsonl`, `positives.jsonl`, `human_validated.jsonl`, and `llm_vs_human_disagreements.jsonl`. The `notebooks/dossier.py` source is the canonical definition of the eight-layer evidence input.

## Common schema

All four files are JSONL (one JSON object per line). Common fields:

| Field | Type | Description |
|---|---|---|
| `orgId` | str | Fitness Browser organism ID (e.g. `MR1`, `Caulo`, `acidovorax_3H11`) |
| `locusId` | str | Fitness Browser locus ID |
| `dossier_md` | str | Full 8-layer evidence dossier in markdown |
| `signal_class` | str | `"stubborn"` if the gene meets the Price-2018 strong-fitness threshold (`n_strong_experiments ≥ 1` OR `in_specificphenotype == 1`); `"no_signal"` otherwise. See "Stubborn vs no-signal" below. |

## Stubborn vs no-signal — what `signal_class` means

The project name (`fitness_browser_stubborn_set`) reflects the original goal: identify genes with **strong fitness phenotype** that nonetheless **stubbornly resist annotation**. The Price-2018 RB-TnSeq paper threshold for "strong" is `|fit| ≥ 2 AND |t| ≥ 5` in at least one condition; any gene also flagged in `kescience_fitnessbrowser.specificphenotype` is by definition stubborn-grade. Combining: a gene is `stubborn` if `n_strong_experiments ≥ 1` OR `in_specificphenotype == 1`.

The v1 LLM-derived files (`negatives.jsonl`, `positives.jsonl`) drew their candidate pool by **uniform random sampling over all 137,798 fitness-measured FB genes** rather than the stubborn-grade subset. As a result they are dominated by `no_signal` genes — the agent labeled them "I don't know" because there's nothing to be stubborn about, not because the evidence was uninterpretable. The `signal_class` field lets consumers filter to the genuinely stubborn cohort:

| File | Stubborn | No-signal |
|---|---:|---:|
| `human_validated.jsonl` | **1,618 (92%)** | 144 (8%) |
| `llm_vs_human_disagreements.jsonl` | **789 (91%)** | 79 (9%) |
| `positives.jsonl` | 129 (29%) | 316 (71%) |
| `negatives.jsonl` | **65 (9%)** | 690 (91%) |

The human-curated files are unambiguously stubborn-grade (92%) — exactly because Price-lab curators paid attention to genes with real phenotype. The LLM-derived files are not. Two recommended uses:

1. **Strict stubborn-set training** — filter every file to `signal_class == "stubborn"`. The training corpus is then 2,601 stubborn-grade rows (1,618 human + 789 disagreements + 129 LLM-positive + 65 LLM-negative), all with strong measured phenotype, all weakly-supervised or expert-validated as a function call.
2. **Permissive corpus** — use everything. Adds 1,229 no-signal rows that teach the agent what "no fitness data → no annotation" looks like (legitimate absence-of-evidence reasoning), at the cost of 91% of the negatives bucket having a less interesting failure mode.

A future v3 expansion will explicitly sample only from the 26,437 stubborn-grade non-curated FB genes to refill the LLM-derived bucket. Until that lands, filter by `signal_class` for the cleanest training cut.

## Per-file schema and provenance

### `human_validated.jsonl` (n = 1,762)

**Source**: BERDL `kescience_fitnessbrowser.reannotation` — Price-lab curators looked at the same evidence we hand the agent and committed to a function name with a rationale (`comment`) for each gene.

**Build pipeline**:
1. Pull `(orgId, locusId, new_annotation, comment)` from `reannotation` → `notebooks/21_pull_reannotation.py` → `data/reannotation_set.parquet`.
2. Resolve **pre-curation** description: BERDL `gene.desc` for the 1,662 rows where it differs from `new_annotation` (validated to match the FEBA `original_description` 99.8% of the time on 439 overlap rows); `"uncharacterized protein"` placeholder for the 100 rows where BERDL had been updated to the curator's name. Other evidence layers (KEGG, SwissProt, SEED, Pfam, PaperBLAST) are sequence-derived and unaffected.
3. Build dossiers with `desc_override` = pre-curation description → `notebooks/22_prepare_reann_batches.py`.
4. Run Claude (Sonnet 4.6, `claude -p`) and Codex (gpt-5.5 augmented-dossier cross-check) for each gene → `notebooks/28_run_claude_classify.sh`, `13_run_codex_xcheck.sh`.
5. Score against the human ground truth → `notebooks/26_score_reann_calibration.py`.
6. Assembled into the distributable file via `notebooks/31_assemble_training_set_v2.py`.

**Schema** (in addition to common fields):

| Field | Type | Description |
|---|---|---|
| `original_description` | str | Pre-curation gene description shown in the dossier (BERDL `gene.desc` or placeholder) |
| `desc_source` | str | `berdl_clean` (1,662 rows) or `placeholder` (100 rows) |
| `human_annotation` | str | The curator's proposed name |
| `human_comment` | str | The curator's free-text rationale (single-line, newlines stripped) |
| `human_category` | str | Derived: `improvable_new` if original was hypothetical/DUF/vague/blank; `improvable_correction` if original was already a specific name |
| `claude_verdict` | str | Claude's independent verdict (`improvable_new` / `improvable_correction` / `already_correctly_named` / `recalcitrant`) |
| `claude_proposal` | str | Claude's proposed name |
| `claude_confidence` | str | `high` / `medium` / `low` |
| `claude_class` | str | One of: `recovered`, `right_type_wrong_name`, `false_negative`, `false_positive_named` (see "Calibration" below) |
| `codex_*` | (same shape) | Codex's independent verdict + class (after augmented-dossier cross-check) |

**Best use**: positive training signal. The label (`human_annotation`) and rationale (`human_comment`) are expert-validated; the dossier is the input the agent should learn to map to that name. Includes both LLMs' verdicts so consumers can compute their own filters (e.g. "only train on rows where the human went deeper than both LLMs").

### `llm_vs_human_disagreements.jsonl` (n = 868)

**Source**: subset of `human_validated.jsonl` where Claude either:
- Said `already_correctly_named` (`disagreement_type == "false_positive_named"`, n = 783) — Claude thought the original FB description was fine, but the human refined it to a more specific name; OR
- Said `recalcitrant` (`disagreement_type == "false_negative"`, n = 85) — Claude gave up, but the human still produced an annotation.

**Build pipeline**: derived from `human_validated.jsonl` during the same assembly step. No separate run.

**Schema**: same as `human_validated.jsonl` plus:

| Field | Type | Description |
|---|---|---|
| `disagreement_type` | str | `false_positive_named` (783) or `false_negative` (85) |
| `both_llms_disagreed` | int | 1 if Codex *also* disagreed (i.e. both LLMs missed); 0 if only Claude disagreed |

**Best use**: hard examples. These rows are exactly the gap between LLM-baseline reasoning and curator-level reasoning. Useful as:
- **Refinement training** — the agent learns: "when you see evidence pattern X with name pattern Y, the right move is to refine to a more specific name, not endorse the existing one."
- **Curriculum** — start training on the easy `human_validated` rows where LLMs already agree, then escalate to these for fine-tuning the harder cases.
- Filter `both_llms_disagreed == 1` for the strongest signal — both LLMs missed, so the human-LLM gap is robust.

### `negatives.jsonl` (n = 755)

**Source**: random walk over 4,600 of the ~5,000 sampled non-reannotated FB genes. Each was classified by Claude with the same 4-class verdict schema; the 1,220 Claude said were `recalcitrant` were re-classified by Codex (with augmented dossier including PaperBLAST per-paper summaries). The **755** where both LLMs agreed `recalcitrant` are this file.

**Build pipeline**: see project's `REPORT.md` "Codex cross-check" section. Notebooks 01–18.

**Schema** (in addition to common fields):

| Field | Type | Description |
|---|---|---|
| `verdict` | str | `recalcitrant` (constant, by construction) |
| `confidence` | str | Claude's intake confidence — `high` / `medium` / `low` |
| `proposed_annotation` | str / null | Usually null for recalcitrant |
| `rationale` | str | Claude's reasoning |
| `papers_consulted` | list[str] | PMIDs Claude cited |
| `codex_verdict`, `codex_confidence`, `codex_rationale`, `codex_proposed_annotation` | | Codex's independent re-classification |
| `evidence_tier` | str | `orphan` (no PaperBLAST hits, n=582) / `hits_no_summaries` (homologs but no useful papers, n=89) / `hits_with_summaries` (literature read, both LLMs still couldn't resolve, n=84) |
| `n_paperblast_hits` | int | Number of PaperBLAST DIAMOND homologs |
| `n_papers_with_summaries` | int | Number of homolog papers with non-null Codex summary |
| `strong_phenotype` | int | 1 if `\|fit\|≥2 AND \|t\|≥5` — marks the 42 wet-lab targets |
| `max_abs_fit`, `max_abs_t` | float | Strongest fitness signal across conditions |

**Best use**: true negatives. False-negative rate against humans (measured on the calibration set) is ~4%, meaning ≤ ~30 of the 755 might be annotatable by an expert. Filter `strong_phenotype == 1` to surface the 42 wet-lab targets.

### `positives.jsonl` (n = 445)

**Source**: 500 high-confidence Claude `already_correctly_named` calls were re-classified by Codex with augmented dossier. The **445** where both LLMs agreed are this file.

**Schema**:

| Field | Type | Description |
|---|---|---|
| `verdict` | str | `already_correctly_named` (constant) |
| `confidence` | str | Claude's intake confidence (all `high` for this set) |
| `proposed_annotation` | str | The existing FB annotation Claude is confirming |
| `ec_number` | str / null | EC number where applicable |
| `rationale` | str | Claude's reasoning |
| `papers_consulted` | list[str] | PMIDs cited |
| `codex_verdict`, `codex_proposal`, `codex_confidence`, `codex_rationale` | | Codex's independent re-classification |

**Best use** — read carefully:

The calibration showed that LLMs say `already_correctly_named` 44–46% of the time when humans actually re-annotated. So **these 445 rows are best framed as "name is plausibly defensible from the 8-layer dossier alone — the LLM cannot justify improving it without going beyond what the dossier shows"**, not as "no curator would change this." If you train an agent to mimic this label without further refinement, you train it to be **as conservative as the LLM** — which calibration tells us is more conservative than a human curator.

**Recommended uses**:
- "Floor" examples — the agent should at least confirm the existing name when LLMs converge.
- Negative training data for the agent's "decide whether to refine" head — these are exactly the cases where humans went deeper.
- Pair with `llm_vs_human_disagreements.jsonl` to teach the contrast: same kind of input, but the right move is to refine.

### `target_gene_homologs.tsv` (8,657 rows)

**Why it exists**: deduplicated (FB target gene → PaperBLAST homolog) mapping, without paper-level repetition. The same information lives inside `target_gene_paperblast_summaries.tsv` denormalized across paper rows; this file is the clean per-pair view.

**Build**: produced by `notebooks/36_build_target_gene_homologs.py`, aggregating the PaperBLAST DIAMOND hits in `data/fb_paperblast_hit_papers.parquet` to one row per `(orgId, locusId, geneId)` tuple, joined with the orgId → organism lookup.

**Schema** (12 columns, TSV with header):

| Column | Description |
|---|---|
| `orgId`, `locusId` | FB target gene |
| `organism` | Target's full organism name |
| `source_file` | Which `.jsonl` file(s) the target appears in (`;`-separated) |
| `paperblast_homolog_id` | PaperBLAST homolog accession (`geneId` in upstream parquets) |
| `paperblast_homolog_organism` | Homolog's organism |
| `paperblast_homolog_desc` | PaperBLAST description of the homolog |
| `pident` | Best-HSP % identity (target ↔ homolog) |
| `evalue` | Best e-value |
| `qcovhsp` | Query coverage of best HSP |
| `scovhsp` | Subject coverage of best HSP |
| `n_papers_cited` | Number of distinct papers PaperBLAST has for this homolog |

Sorted by `(orgId, locusId, pident desc)` so the best homolog for each target comes first.

**Quick stats**:
- 2,215 of 2,962 target genes have at least one PaperBLAST homolog
- 747 targets are **orphans** — no PaperBLAST hits at all (mostly the orphan tier of `negatives.jsonl`)
- Median 4 homologs per target; max 17

**Best use**: agent-side lookup of "what's the closest characterized relative for this gene, and how good is the alignment?" Filter `pident ≥ 50` for high-confidence homology; use `n_papers_cited` to estimate available literature volume; use as the index for joining to `target_gene_paperblast_summaries.tsv` for per-paper summaries.

### `target_gene_interpro_union.tsv` (15,698 rows) — default InterPro layer

**Why it exists**: consolidates the three InterPro evidence routes below into a single per-gene-per-domain table so downstream consumers do not have to merge three differently-shaped files. Built by `notebooks/58_union_interpro.py` from the three audit-trail TSVs plus `data/fb_pangenome_link.tsv`.

**Grain**: one row per `(orgId, locusId, ipr_acc)`. When a signature has no IPR mapping in the InterProScan run (e.g. some Gene3D / MobiDBLite hits), `signature_acc` is used as the fallback grain so those hits are not silently dropped.

**Aggregation rules**:

- `sources` — comma-joined subset of `{uniprot, md5, cluster}` indicating which routes corroborate this hit
- `n_sources` — 1, 2, or 3
- `start`, `stop`, `score`, `signature_*`, `analysis` — taken from the highest-priority source carrying the value (cluster > md5 > uniprot, since cluster and md5 share the same InterProScan run and the cluster route adds conservation context)
- `go_ids`, `pathways` — set-union across sources, semicolon-delimited
- `gene_cluster_id`, `gtdb_species_clade_id`, `is_core`, `is_auxiliary`, `is_singleton` — **always populated**, taken from `fb_pangenome_link.tsv` (per-gene, regardless of which route surfaced the InterPro hit). Genes with no FB↔pangenome link get the literal string `unknown` for the conservation flags so downstream code can treat that as a distinct tier rather than confusing it with `False`
- `uniprot_acc`, `md5` — populated when the corresponding route contributed

**Coverage**:

- **2,447 of 2,962 training genes (82.6%)** — union of all three InterPro sources
- 5,142 rows from a single source (33%); 6,700 rows with 2 sources; 3,856 rows with all 3 (so 67% of rows have ≥ 2 corroborating routes)
- Conservation flags: 12,509 rows in core clusters, 1,578 in non-core, 1,611 marked `unknown`

**Best use**: the one InterPro file an agent should read by default. Three-source corroboration acts as a confidence signal; the `sources` column lets the agent see whether a hit is supported by an UniProt-curated InterPro index, the raw InterProScan run on FB sequences (MD5 identity), the InterProScan run on the pangenome cluster representative (DIAMOND homology), or any combination. The audit-trail files below remain available for source-specific re-analysis.

### `target_gene_interpro.tsv` (13,238 rows) — UniProt-route audit trail

**Why it exists**: extends the existing Pfam + TIGRFam domain layer (in `dossier_md`) with **broader InterPro coverage** plus site annotations and GO term mappings. InterPro is the meta-database that integrates Pfam, TIGRFams, PANTHER, SMART, PROSITE, CDD, ProDom, HAMAP, SUPERFAMILY etc.

**Build pipeline** (`notebooks/55_extract_interpro.py`):

```
FB (orgId, locusId)
  → kescience_fitnessbrowser.locusxref (xrefDb='uniprot')
  → UniProt accession
  → kescience_interpro.protein2ipr      [InterPro entries with start/stop]
  → kescience_interpro.entry            [entry type + name]
  → kescience_interpro.go_mapping       [GO term aggregation per IPR entry]
```

**Schema** (11 columns, TSV with header):

| Column | Description |
|---|---|
| `orgId`, `locusId` | FB target gene |
| `uniprot_acc` | The UniProt accession via `locusxref` (the join key) |
| `ipr_id` | InterPro accession (e.g. `IPR000019`) |
| `ipr_desc` | InterPro description (short form from `protein2ipr`) |
| `entry_type` | `Family` / `Domain` / `Site` / `Active site` / `Binding site` / `Conserved site` etc. |
| `entry_name` | InterPro entry name (long form) |
| `source_acc` | DB-specific ID (e.g. `PF07869` for Pfam, `TIGR00001` for TIGRFams) |
| `start`, `stop` | Match position in the protein |
| `go_terms` | Semicolon-separated `go_id:go_name` pairs (from `go_mapping`) |

**Coverage**:

- **1,963 of 2,962 training genes (66.3%)** have at least one InterPro entry
- 13,238 (gene × IPR) rows total
- 2,424 distinct InterPro entries
- Median 6 IPR entries per gene; max 17

**Missing orgs**: 4 of the 36 training-set organisms have no InterPro coverage (Burk376, Pedo557, Phaeo, Kang). Three of them have UniProt xrefs in `locusxref` but their accessions aren't indexed in `kescience_interpro.protein2ipr` (likely TrEMBL-only entries that haven't been processed). For these, the agent falls back to Pfam/TIGRFam evidence already in `dossier_md`.

**Best use**: load alongside `dossier_md` as an additional domain-evidence layer. Filter by `entry_type` to focus on `Family`/`Domain` (broad classifications) vs `Active site`/`Binding site` (residue-level). Use `go_terms` to extract functional ontology annotations the original Pfam/TIGRFam layer doesn't carry.

### `target_gene_interproscan.tsv` (15,552 rows) — MD5-route audit trail

**Why it exists**: complementary InterPro source from `kbase_ke_pangenome.interproscan_*` (a fresh InterProScan run on the Kbase pangenome's gene-cluster representative sequences). Distinct from `target_gene_interpro.tsv` in two ways:
1. Bridged via **MD5 of the protein sequence** rather than UniProt accession — works for any FB gene whose protein sequence appears identically in the pangenome (no UniProt-indexing requirement)
2. Carries **per-domain scores** and **pathway annotations** (KEGG / Reactome / MetaCyc) that the curated InterPro index does not

**Build pipeline** (`notebooks/56_extract_interproscan_pangenome.py`):

```
FB protein sequence (from fb_aaseqs_all.fasta)
  → MD5 hex digest
  → kbase_ke_pangenome.interproscan_domains       [exact-sequence match → IPS hits]
  → kbase_ke_pangenome.interproscan_go            [GO term aggregation per gene_cluster_id]
  → kbase_ke_pangenome.interproscan_pathways      [pathway aggregation per gene_cluster_id]
```

**Schema** (14 columns, TSV with header):

| Column | Description |
|---|---|
| `orgId`, `locusId` | FB target gene |
| `md5` | MD5 of the protein sequence (the join key) |
| `gene_cluster_id` | Pangenome gene cluster the FB gene maps to |
| `analysis` | InterProScan analysis (Pfam, TIGRFAM, PIRSF, SMART, SUPERFAMILY, CDD, MobiDBLite, ...) |
| `signature_acc`, `signature_desc` | DB-specific signature (e.g. PF07869) |
| `ipr_acc`, `ipr_desc` | InterPro entry mapped from the signature |
| `start`, `stop`, `score` | Match position + raw score |
| `go_ids` | Semicolon-joined GO IDs (from `interproscan_go`) |
| `pathways` | Semicolon-joined `db:id` pairs (KEGG/Reactome/MetaCyc/UniPathway) |

**Coverage**:

- 1,159 of 2,962 training genes (39.1%) have InterProScan coverage via exact-sequence match
- 1,721 distinct InterPro entries; 1,855 distinct gene_cluster_ids
- Lower coverage than `target_gene_interpro.tsv` (66.3%) because MD5 requires *identical* sequences, not just shared homology
- The two files **overlap on most genes both cover** (the pangenome IPS row is just a different InterProScan version) but each contributes some genes the other doesn't index

**Best use**: feed alongside `target_gene_interpro.tsv` as a second domain-evidence layer. The pathway annotations are unique to this source — useful for placing genes in metabolic context. For autoresearch, sweeping `[neither / interpro / interproscan / both]` measures the marginal value of each.

### `target_gene_interpro_cluster.tsv` (19,533 rows) — cluster-route audit trail

**Why it exists**: highest-coverage InterPro source (70.8% of training genes), bridged via the FB→pangenome cluster mapping from the sibling `conservation_vs_fitness/` project. For each FB gene, DIAMOND found its best-hit pangenome cluster representative; the cluster's InterProScan results then transfer back to the FB gene. This works for any gene whose protein is *homologous* to a cluster representative (vs. MD5 which requires identity).

**Build pipeline** (`notebooks/57_extract_interproscan_via_cluster.py`):

```
FB (orgId, locusId)
  → fb_pangenome_link.tsv  [DIAMOND best-hit to cluster representative]
  → gene_cluster_id
  → kbase_ke_pangenome.interproscan_domains   [IPS hits at cluster rep]
  → kbase_ke_pangenome.interproscan_go        [GO term aggregation]
  → kbase_ke_pangenome.interproscan_pathways  [KEGG/Reactome/MetaCyc]
```

The link table (`fb_pangenome_link.tsv`, 178K rows, 44 orgs) is built by the upstream `conservation_vs_fitness/` project (DIAMOND alignment of FB protein sequences against per-clade pangenome cluster reps). Pulled from the lakehouse archive (`s3a://cdm-lake/tenant-general-warehouse/microbialdiscoveryforge/projects/conservation_vs_fitness/data/fb_pangenome_link.tsv`) — the file produced by the `/submit` lakehouse upload of the upstream project.

**Schema** (20 columns, TSV with header):

| Column | Description |
|---|---|
| `orgId`, `locusId` | FB target gene |
| `gene_cluster_id` | Pangenome cluster the FB gene maps to (DIAMOND best hit) |
| `gtdb_species_clade_id` | GTDB species clade containing this cluster |
| `is_core` / `is_auxiliary` / `is_singleton` | Pangenome conservation flags — is this gene present in all / some / one strain of the species clade |
| `pident`, `evalue`, `bitscore` | DIAMOND alignment quality of FB → cluster rep |
| `analysis` | InterProScan analysis (Pfam, TIGRFAM, PIRSF, SMART, SUPERFAMILY, etc.) |
| `signature_acc`, `signature_desc` | DB-specific signature |
| `ipr_acc`, `ipr_desc` | InterPro entry mapped from the signature |
| `start`, `stop`, `score` | Match position + raw score (in cluster representative coords) |
| `go_ids` | Semicolon-joined GO IDs |
| `pathways` | Semicolon-joined `db:id` pathway annotations |

**Coverage**:

- **2,096 of 2,962 training genes (70.8%)** have InterProScan via cluster bridge
- 19,533 (gene × IPS hit) rows
- Distinct cluster_ids covered: 2,096
- Best of the three InterPro routes; covers 351 genes the UniProt route misses

**Combined coverage** (union of all three InterPro files): **82.6%** (2,447 / 2,962). The 17.4% with no InterPro coverage from any source fall back to the Pfam/TIGRFam evidence already in `dossier_md` (which has 81.8% coverage on its own).

**Best use**: primary InterPro layer when high coverage matters. Because alignment quality is exposed (`pident`, `evalue`, `bitscore`), an agent can choose to discount IPR entries where the FB→cluster alignment is weak (e.g., `pident < 50` would mean the cluster rep is a distant homolog and its InterPro annotations should be taken cautiously). The cluster-context flags (`is_core`/`is_auxiliary`/`is_singleton`) are unique to this source and useful for evolutionary reasoning ("this gene is in 95% of species in this clade — likely essential").

### `target_gene_ortholog_fitness.tsv` (39,950 rows)

**Why it exists**: the dossier carries `conserved_cofit` and `conserved_specific_phenotype` only as **binary flags** derived from the FB ortholog graph; the actual fitness profile of an ortholog never reaches the agent. For a target gene with weak signal, the strongest reasoning move is "but its ortholog in *Pseudomonas WCS417* shows phenotype on xylose" — exactly what this file surfaces.

**Build pipeline** (`notebooks/59_extract_ortholog_fitness.py`): for each training-set target gene, pull all BBH ortholog pairs from `kescience_fitnessbrowser.ortholog`, then for each ortholog attach its own fitness summary, top conditions, specific-phenotype count, and gene description. Two distance signals are exposed so the agent can weight orthologs:

- **`bbh_ratio`** (0–1, gene-level) — BBH score ratio from `ortholog.ratio`
- **`shared_taxonomic_ranks`** (0–7, organism-level) — count of GTDB ranks (domain → species) that match between the target's organism and the ortholog's organism, derived from `fb_organism_gtdb_lineage.tsv`

**Schema** (15 columns, TSV with header):

| Column | Description |
|---|---|
| `target_orgId`, `target_locusId` | The training-set gene |
| `ortholog_orgId`, `ortholog_locusId` | The BBH ortholog |
| `bbh_ratio` | BBH score ratio (per-pair similarity, 0–1) |
| `shared_taxonomic_ranks` | 0–7, count of matching GTDB ranks between target and ortholog organisms |
| `ortholog_symbol`, `ortholog_gene_desc` | The ortholog's own annotation |
| `ortholog_max_abs_fit`, `ortholog_max_abs_t` | Strongest fitness signal at the ortholog |
| `ortholog_n_strong` | Count of experiments where ortholog has &#124;fit&#124; ≥ 1 and &#124;t&#124; ≥ 4 |
| `ortholog_n_specific_phenotype` | Count of `specificphenotype` rows for the ortholog (Price-thresholded specific phenotype calls) |
| `ortholog_top_conditions` | Top-3 strongest conditions for the ortholog, formatted `fit=… t=… cond=…` joined with ` \| ` |
| `target_gtdb_lineage`, `ortholog_gtdb_lineage` | Full `domain;phylum;class;order;family;genus;species` strings (semicolon-joined) |

**Coverage**:

- 39,950 ortholog pairs across **2,397 of 2,962 training genes (80.9%)**
- 35,346 (88.5%) ortholog pairs have measured fitness data on the ortholog side
- BBH ratio quartiles: 0.31 / 0.48 / 0.67
- Shared-ranks distribution: 50 same-species, 5,465 same-genus, 1,816 same-family, 1,154 same-order, 11,985 same-class, 6,568 same-phylum, 12,559 same-domain only, 353 with no shared ranks

**Best use**: cross-organism fitness corroboration. An agent looking at a target gene with weak primary fitness can filter to high-confidence orthologs (`bbh_ratio ≥ 0.5`) and check whether *any* of them show a strong, specific phenotype — a strong signal that the target's function is conserved and consequential. Discounting by `shared_taxonomic_ranks` lets the agent down-weight distantly-related orthologs whose phenotype may not transfer. Because `ortholog_top_conditions` carries the actual condition strings (e.g. "Tween 20 carbon source"), this evidence is directly interpretable: a fatty-acid-related condition firing in an ortholog suggests the target is a fatty-acid metabolism gene.

### `fb_organism_gtdb_lineage.tsv` (36 rows)

**Why it exists**: lookup file for the FB organism → full GTDB lineage mapping used by `target_gene_ortholog_fitness.tsv` (and useful as standalone reference for any per-organism reasoning).

**Build pipeline** (also in `notebooks/59_extract_ortholog_fitness.py`):

1. From `data/fb_pangenome_link.tsv`, take the majority `gtdb_species_clade_id` per FB orgId
2. Parse out the GTDB genome accession (the suffix after `--`)
3. Look up the full lineage in `kbase_ke_pangenome.gtdb_taxonomy_r214v1`
4. For 5 orgs missing or partial in GTDB (Cola, Kang, SB2B, plus 2 with incomplete higher-rank coverage), fall back to `kescience_fitnessbrowser.organism` (genus + species always populated, with prefixes added so cross-source rank matching works)

**Schema** (9 columns, TSV with header): `orgId`, `genome_id`, `domain`, `phylum`, `class`, `order`, `family`, `genus`, `species`. 31 of 36 orgs have full GTDB lineage; the remaining 5 carry FB-fallback genus/species (other ranks empty).

**Best use**: organism-level taxonomy lookup; consumed by `target_gene_ortholog_fitness.tsv` for shared-rank distance computation but also exposable directly so an agent can reason about whether a particular evidence source comes from an evolutionarily close or distant relative.

### `target_gene_paperblast_summaries.tsv` (16,618 rows)

**Why it's separate**: each row in the four `.jsonl` files is one *target gene*; that gene typically has many PaperBLAST homologs, each with multiple cited papers. Flattening into "one row per (target gene × homolog × paper)" gives the agent a tabular file it can filter / join without parsing nested fields out of the dossier markdown.

**Build pipeline**: produced by `notebooks/32_build_target_gene_summaries.py` from these inputs:
- `data/fb_paperblast_hit_papers.parquet` — target → homolog → paper hits
- `data/manuscript-summaries-merged.tsv` — homolog × paper → summary
- `data/reannotation_set.parquet` — target → curator annotation (where applicable)
- `data/gene_evidence_features.parquet` — target → original gene description
- `data/fb_organism_names.tsv` — orgId → full organism name lookup
- `data/fitness_browser/fb_aaseqs_all.fasta` — target → protein sequence

**Schema** (22 columns, TSV with header):

| Column | Description |
|---|---|
| `benchmark_index` | Ordinal across the file |
| `orgId`, `locusId` | FB target gene identifiers |
| `organism` | Target gene's full organism name (e.g. "Acidovorax sp. GW101-3H11") |
| `source_file` | Which `.jsonl` file(s) the target gene appears in (`;`-separated) |
| `reannotation` | Curator's annotation (populated for `human_validated` genes; blank otherwise) |
| `original_desc` | Pre-curation gene description (matches what the dossier shows) |
| `aaseq` | Target gene's protein sequence |
| `paperblast_target_id` | PaperBLAST homolog identifier |
| `paperblast_query_term` | The query (target `orgId::locusId`) |
| `paperblast_manuscript_id` | PMID of the cited paper |
| `source_type` | `pubmed` |
| `paperblast_organism` | Organism of the homolog |
| `paperblast_homolog_desc` | PaperBLAST description of the homolog |
| `pident`, `evalue`, `qcovhsp`, `scovhsp` | DIAMOND alignment statistics |
| `paper_title`, `paper_year`, `paper_journal` | Paper bibliographic data |
| `summary` | Homolog-specific summary text. Empty when no homolog-specific summary exists — see `summary_status`. |
| `summary_status` | `homolog_match` / `null_for_homolog` / `missing` (see "Summary coverage" below) |

**Summary coverage** (per row):

| Status | n | % | What it means |
|---|---:|---:|---|
| `homolog_match` | 12,425 | **74.8%** | Codex generated a non-null summary specifically about this homolog × this paper. Best signal. |
| `null_for_homolog` | 3,557 | 21.4% | Codex was asked about this homolog in this paper and returned `null` (paper doesn't characterize this homolog). Summary column is empty. **This is informative non-coverage**, not a data gap. |
| `missing` | 636 | 3.8% | Paper has no usable text source. Summary is empty; only the title is available. See breakdown below. |

**Important**: the summary text is **always homolog-specific**. We do NOT use a fallback that re-uses a summary written about a different homolog of the same paper — that would mislead the agent into thinking a paragraph about gene Y describes gene X. If we don't have a homolog-specific summary, the row's summary column is empty and `summary_status` indicates why.

**96.2% of rows have codex evaluated** (homolog_match + null_for_homolog). The 4.2% missing breaks down:

| Subcategory | n | Recoverable? |
|---|---:|---|
| Conference proceedings (UEG Week posters, EHA Congress, etc.) — no PMID exists by design | 484 | No |
| PaperBLAST citations with no PMID and no title in metadata that we couldn't resolve via Europe PMC search | ~215 | Some, with relaxed-match search |
| Truly unrecoverable (no PMC, no abstract, not in Europe PMC / OpenAlex / CrossRef) | 1 | No |

The chase pipeline tries each paper through five sources in order: PMC full text → PubMed abstract → Europe PMC full text → OpenAlex inverted index → CrossRef DOI metadata. Papers with completely empty bibliographic metadata (geneId/title/journal all blank in PaperBLAST) are filtered out as orphan placeholders before reaching this stage.

**Best use**: feed this directly to the agent as the literature-evidence layer. Filter to rows where `(orgId, locusId)` matches the target gene of interest, optionally rank-cut by `pident`, and the resulting subset is the agent's literature context for that gene.

## Label stability under richer evidence

We ran a 40-gene sample re-classification (20 random from `negatives.jsonl` + 20 from `positives.jsonl`) using the same Claude+Codex pipeline that produced the original labels, but feeding both LLMs the now-much-richer literature corpus from the gap-fill / abstract / alt-source / titlesearch chases.

| Source | n | Claude flipped | Codex flipped | **Both agree on flip** |
|---|---:|---:|---:|---:|
| Negatives | 20 | 25% | 10% | **5%** |
| Positives | 20 | 5% | 10% | **0%** |

**Observations**:
- Individual LLMs flip more often (5–25%) when shown richer evidence, but they don't agree on the flips. The two-LLM agreement filter that produced the original labels successfully filters out single-LLM noise.
- All flips are in the same direction: `recalcitrant` / `already_correctly_named` → `improvable_*`. More literature lets the LLM see more evidence; it never becomes *less* confident.
- Negatives are more flip-prone than positives — a `recalcitrant` verdict depends on absence-of-evidence reasoning, which the new corpus directly addresses. `already_correctly_named` is more stable because it depends on existing-evidence agreement.

**Implication**: extrapolating the both-LLM-agreement flip rate (5% on negatives, 0% on positives), the 755 negatives may contain ~38 cases where the original `recalcitrant` verdict would now be reversed; the 445 positives are essentially stable. **The decision threshold for relabeling was 5% overall; we observed 2.5%, so the labels were not regenerated.** The sample-reclassification artifacts are in `../sample_reclass/` for transparency.

If a downstream user is concerned about the ~38 potentially-mislabeled negatives, the easiest course is to filter `negatives.jsonl` to rows where both `confidence == "high"` and `codex_confidence == "high"` (gives 204 most-confident calls) — those are demonstrably the most robust subset.

## Calibration: how the labels stack up against humans

The same Claude+Codex pipeline was run against the 1,762-gene human-curated reannotation set as a held-out benchmark.

### Headline metrics (Claude alone vs human curators)

| Metric | Value |
|---|---:|
| Recall@type (LLM said improvable_*) | 50.7% |
| Recall@name (token-set Jaccard ≥0.5 OR EC equality) | 15.5% |
| False-negative (LLM said `recalcitrant` when human annotated) | 4.8% |
| False-positive-named (LLM said `already_correctly_named` when human re-annotated) | 44.4% |

### The structural finding

LLMs distinguish two cases sharply:

| Original was… | n | Recall@type | Recall@name |
|---|---:|---:|---:|
| **hypothetical / DUF / vague / blank** | 318 (18%) | **85.5%** | 34.0% |
| **already a specific name** (curator's act was a *correction*) | 1,444 (82%) | 43.1% | 11.4% |

LLMs are excellent at upgrading vague existing names; they rarely override an existing specific name even when humans did. The dominant gap is in **specific → better-specific** corrections, which is also the dominant flavor of the human reannotation set.

### What this means for each file

| File | Calibration implication |
|---|---|
| `human_validated.jsonl` | Ground truth — these labels carry the lowest uncertainty. |
| `llm_vs_human_disagreements.jsonl` | The richest training signal — exactly the LLM-vs-curator gap, with the human's name + rationale as target. |
| `negatives.jsonl` | False-negative rate against humans is ~4%, but our 755 came from genes humans **did not** curate — so the conditional rate is lower than 4%. Treat as reliable. |
| `positives.jsonl` | Read the "Best use" note. The label means "LLM-defensible original name," not "no curator would refine it." |

## Caveats

- **Domain scope**: 36 organisms in the Fitness Browser. Generalization beyond bacteria/archaea with measured fitness phenotypes is not validated.
- **"Unannotatable" is point-in-time**: based on PaperBLAST literature available at run time. New papers may resolve some negatives later.
- **Two-LLM agreement is not ground truth**: it's high-quality weak supervision. The calibration section quantifies the gap to actual experts.
- **Token-set name match is conservative**: many `right_type_wrong_name` rows in the calibration are semantically identical (e.g. "Histidinol-phosphatase (EC:3.1.3.15)" vs "histidinol-phosphate phosphatase"). Semantic recall@name is meaningfully higher than 15.5%.
- **Contamination control** in the human-curated files applies **only to the focal gene's `gene.desc`**. The dossier includes top-10 cofit partner descriptions and ±5 neighborhood gene descriptions so the agent can reason about operon context (curators use the same signal); those partner/neighbor descriptions show their *current* BERDL `gene.desc`, which may include curator updates if the partner/neighbor was also reannotated. Population effect is small (only 1.3% of FB genes were reannotated, so the per-row probability of a useful leak through partners/neighbors is small) and the leak is intentional — an agent in production will see whatever current annotations exist. For stricter calibration we could extend the swap to every reannotated gene appearing anywhere in the dossier; not done here because the footprint is small and the headline numbers are robust to it.
- The other two files (`negatives.jsonl`, `positives.jsonl`) use unmodified BERDL `gene.desc` because they came from non-reannotated genes — no contamination concern for the focal gene either.
- **Human comments can be terse**: the curator's `human_comment` field is sometimes a single sentence pointing at the strongest evidence. It's the curator's working note, not a manuscript-quality justification.
- **Negatives candidate-pool methodology**: v1's `negatives.jsonl` was sampled before `signal_class` filtering existed, so 91% of those rows are `no_signal` rather than the stubborn-grade negatives the project name targets. The human-curated files (`human_validated.jsonl`, `llm_vs_human_disagreements.jsonl`) are 91-92% stubborn because curators paid attention to genes with real phenotype. Filter by `signal_class == "stubborn"` for the strict cohort. A v3 expansion track is planned to refill the LLM-derived stubborn bucket.

## Provenance

All artifacts are reproducible from this project. Notebook chain (in execution order):

| Step | Notebook | Output |
|---|---|---|
| BERDL pull | `21_pull_reannotation.py` | `data/reannotation_set.parquet` |
| Build reann batches | `22_prepare_reann_batches.py` | `data/batches_reann/batch_RA*/input.md` |
| Merge summary corpora | `23_merge_summary_corpora.py` | `data/manuscript-summaries-merged.tsv` |
| Build new paper tasks | `27_build_reann_paper_tasks.py` | `data/codex_summaries_reann/tasks.jsonl` |
| Fetch PMC | `07_fetch_pmc.py` (env-driven) | `data/codex_summaries/pmc/*.xml` |
| Codex summarize | `09_run_all_codex.sh` (env-driven) | `data/codex_summaries_reann/per_paper/*.tsv` |
| Concat reann summaries | `30_concat_summaries_reann.py` | `data/manuscript-summaries-reann.tsv` |
| Build codex xcheck batches | `25_build_codex_xcheck_reann.py` | `data/codex_xcheck_reann/batch_RA*/input.md` |
| Claude classification | `28_run_claude_classify.sh` + `29_run_all_claude.sh` | `data/batches_reann/batch_RA*/output.jsonl` |
| Codex cross-check | `13_run_codex_xcheck.sh` + `14_run_all_xcheck.sh` (env-driven) | `data/codex_xcheck_reann/batch_RA*/output.jsonl` |
| Score | `26_score_reann_calibration.py` | `data/reann_calibration.tsv` |
| Assemble v2 | `31_assemble_training_set_v2.py` | this directory |

The recalcitrant + positive sides (negatives.jsonl, positives.jsonl) were produced earlier — see notebooks 01–20 and the project's `REPORT.md`.
