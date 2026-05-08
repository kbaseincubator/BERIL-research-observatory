---
name: gene-annotate
description: Annotate protein sequences with evidence-tiered functional descriptions using homology, fitness data, InterProScan domains, and LLM reasoning. Use when the user has protein sequences (in any format) and wants to determine their function.
allowed-tools: Bash, Read, Write, Edit, AskUserQuestion, Agent
user-invocable: true
---

# Gene Annotation Skill

Run the `gene-annotate` CLI to produce GeneRIF-style functional annotations for protein sequences. The tool integrates four BERDL evidence layers — PaperBLAST homology (literature-curated), pangenome cluster annotations, Fitness Browser phenotypic data, and gene neighborhoods — plus InterProScan domain analysis and LLM reasoning to generate evidence-tiered annotations. Additional BERDL datasets can be layered on top via `--berdl-source-config`.

## When to Use

- The user has protein sequences in any format — FASTA files, raw sequences, TSV/CSV tables, GenBank records, BERDL query results, or pasted text
- The user wants to determine or predict protein function
- The user wants evidence-backed functional annotations with confidence tiers

## What It Produces

A TSV file with one row per input sequence containing:

| Column | Description |
|--------|-------------|
| `sequence_id` | Sequence identifier from the FASTA header |
| `organism` | Organism name (if `--description-is-organism` was used) |
| `model` | LLM model used |
| `annotation` | GeneRIF-style functional annotation |
| `evidence` | Prose summary of evidence used |
| `tier` | Confidence tier: **A** (strong, specific), **B** (family-level), **C** (fold-only) |
| `reasoning` | Extended LLM reasoning trace |
| `input_tokens` / `output_tokens` / `total_tokens` / `reasoning_tokens` | Token usage |

## Prerequisites

### Package Location

The tool is installed at:
```
/global_share/gene-annotation-predictor/
```

It uses a Poetry-managed virtual environment (`.venv/` in the package directory). No conda activation is needed — use `poetry run` from the package directory.

### API Key (auto-detected)

The CLI resolves the API key automatically from environment variables — no explicit flag is needed. Priority order:

1. `CBORG_API_KEY` in `.env` or environment — routes through the CBORG gateway (`https://api.cborg.lbl.gov`) automatically
2. `ANTHROPIC_API_KEY` in `.env` or environment — used directly

Pass `--api-key KEY` only to override with a literal key value.

### Local Resources

| Resource | Path |
|----------|------|
| InterProScan | `/global_share/gene-annotation-predictor/bin/my_interproscan/interproscan-5.76-107.0/interproscan.sh` |
| BERDL DIAMOND databases | `/global_share/gene-annotation-predictor/data_sources/sequences/` |
| Summaries parquet | `/global_share/gene-annotation-predictor/data_sources/sequences/manuscript-summaries.filtered.parquet` |

### BERDL Evidence Layer

When `--berdl-data-dir` is provided, five evidence sources are always included automatically:

| Source | DIAMOND DB | Toolkit | Output column |
|--------|-----------|---------|---------------|
| PaperBLAST (literature-curated homologs) | `paperblast_uniq.dmnd` | `BatchBERDLPaperBLASTToolkit` | `berdl_paperblast_evidence` |
| Pangenome cluster annotations | `pangenome_gene_cluster.dmnd` | `BatchBERDLPangenomeToolkit` | `berdl_pangenome_evidence` |
| Fitness Browser co-fitness profiles | `fitnessbrowser_aaseqs.dmnd` | `BatchBERDLFitnessBrowserToolkit` | `berdl_fitness_evidence` |
| Gene neighborhoods | *(same as Fitness Browser)* | `fetch_gene_neighborhood_batch` | `gene_neighborhoods` |
| Fitness Browser gene annotations | `fitnessbrowser_aaseqs.dmnd` | `BatchBERDLGenericToolkit` (builtin) | `evidence_fitnessbrowser_aaseqs` |

The fifth source (`evidence_fitnessbrowser_aaseqs`) is loaded automatically from `data_sources/configs/builtin_fitness_browser.yaml` — no flag required. It complements the co-fitness source by providing direct gene-level descriptions from the fitness browser annotation table, which enables convergent direct-naming evidence that the co-fitness profiles alone cannot provide.

Config-driven sources from `--berdl-source-config` are **additive** — they run alongside the five defaults, not instead of them.

Requires:
- `KBASE_AUTH_TOKEN` set in `.env`
- BERDL data directory (path above)
- `--berdl-use-spark` for Spark-based annotation queries

## Workflow

### Step 1: Understand and Prepare Input

The user may provide protein sequences in many formats. The `gene-annotate` tool requires FASTA input, so this step handles conversion.

**Accepted input formats and how to handle each:**

| Input format | How to detect | Preparation |
|---|---|---|
| **FASTA file(s)** | `.faa`, `.fasta`, `.fa` extension; lines starting with `>` | Use directly — no conversion needed |
| **Raw sequence(s) pasted in chat** | Amino acid letters (M, A, G, L, ...) without headers | Assign sequence IDs (`seq_1`, `seq_2`, ...) and write a FASTA file |
| **TSV/CSV table** | Columns for sequence ID, sequence, and optionally organism | Extract ID + sequence + organism columns, write FASTA |
| **GenBank / EMBL records** | `LOCUS`, `ORIGIN`, `//` markers | Parse with BioPython or extract protein translations, write FASTA |
| **BERDL query results** | Protein sequences from a `/berdl` query or direct Spark query against any BERDL database | Extract sequence + ID + organism (use GTDB clade name split at `--` when available), write FASTA. If the source table contains functional annotations (e.g., eggNOG, UniProt descriptions, product names), write a companion `<input>.annotations.json` side file keyed by sequence ID containing those annotations for use in Step 5 comparison |
| **Uniprot / NCBI accessions** | Accession IDs like `P12345`, `WP_*`, `NP_*` | Fetch sequences via NCBI efetch or UniProt API, write FASTA |

**FASTA format for `gene-annotate`:**

```
>sequence_id organism_name
MKTIIALSYIFCLVFADYKNTXXXXXXX...
```

When organism information is available, include it in the FASTA description line (text after the sequence ID on the `>` header line). This enables the `--description-is-organism` flag, which significantly improves annotation quality by providing taxonomic context to the LLM.

**Organism lookup for non-pangenome proteins.** When proteins do not come from `kbase_ke_pangenome` (which provides GTDB clade names), attempt to resolve organism names before writing the FASTA:

1. **Query `kescience_paperblast.gene` via Spark** — this table covers ~1.1M sequences including all VIMSS, WP_, NP_, XP_, YP_, and UniProt (Q/P/A/B/O/...) accessions. The `geneId` column matches the sequence ID directly and the `organism` column contains a full organism name (e.g., `"Agrobacterium tumefaciens str. C58 (Cereon)"`).

   ```python
   ids_sql = ", ".join(f"'{sid}'" for sid in sequence_ids)
   df = spark.sql(f"""
       SELECT geneId, organism
       FROM kescience_paperblast.gene
       WHERE geneId IN ({ids_sql})
   """)
   organism_map = {r["geneId"]: r["organism"] for r in df.collect()}
   ```

2. **Fall back to the FASTA description line** — if the input FASTA already contains descriptive text after the sequence ID (e.g., from a UniProt download), use that as the organism/description.

3. **Leave blank if not resolvable** — for accession types not in PaperBLAST (e.g., `CAZy::*` IDs) and with no FASTA description, omit the organism field and do not use `--description-is-organism`.

Use the organism name as-is from `kescience_paperblast.gene` — it already includes genus, species, and strain where available. Write it into the FASTA description line and set `--description-is-organism` when at least one sequence has a resolved organism.

**Strip asterisks from all sequences before writing.** Pangenome sequences from BERDL (and any ORF-prediction tool output) may contain `*` stop-codon markers. InterProScan rejects any sequence containing `*` and aborts the entire run — not just the offending sequence. Always strip `*` from every sequence with `seq.replace("*", "")` before writing the FASTA file.

**Write the prepared FASTA file** to the project directory or a temp location. Use a descriptive filename (e.g., `input_proteins.faa`).

### Step 1.5: Discover and Select Additional BERDL Evidence Sources

The user's BERDL tenant may contain protein-bearing tables beyond the three built-in sources (PaperBLAST, pangenome, Fitness Browser). Any table with both protein sequences AND per-protein annotation can be added as an extra evidence source. The CLI consumes these via `--berdl-source-config <YAML>` and emits one `evidence_<name>` column per active source plus a manifest preamble in the LLM prompt.

**Skip this step if** the user has already provided a source-config YAML, has explicitly opted out, or this is a quick re-run. Otherwise:

1. **Auto-discover candidates via Spark.** Iterate every database/table the user has access to and look for both a sequence column and an annotation column:

   ```python
   SEQ_COLS = {"sequence", "faa_sequence", "protein_sequence", "aa_sequence"}
   ANN_COLS = {"description", "function", "ec", "ec_number", "product",
               "preferred_name", "annotation", "kegg_ko", "cog_category",
               "go", "gos"}
   EXCLUDE = {("kescience_paperblast", "uniq"),
              ("kbase_ke_pangenome", "gene_cluster"),
              ("kescience_fitnessbrowser", "aaseqs")}  # covered by built-in sources

   candidates = []
   for db in [r["namespace"] for r in spark.sql("SHOW DATABASES").collect()]:
       for t in spark.sql(f"SHOW TABLES IN {db}").collect():
           tn = t.tableName
           if (db, tn) in EXCLUDE:
               continue
           cols = spark.sql(f"DESCRIBE TABLE {db}.{tn}").collect()
           col_names = {c.col_name.lower(): c.col_name for c in cols}
           seq = col_names.keys() & SEQ_COLS
           ann = col_names.keys() & ANN_COLS
           if seq and ann:
               candidates.append({"db": db, "table": tn,
                                  "seq_col": col_names[next(iter(seq))],
                                  "ann_cols": [col_names[a] for a in ann]})
   ```

2. **Present candidates** with `AskUserQuestion` (multi-select) when ≥1 candidate is found. Label each option as `{db}.{table} ({n} ann cols)` so the user can recognize them. If the list is long, group by source type heuristic (UniProt → curated, eggNOG/KEGG → computational, fitness/growth → experimental).

3. **Generate `<output_dir>/berdl_sources.yaml`** for the selected datasets. One YAML doc per source. Field guide:

   | YAML field | Value |
   |---|---|
   | `name` | `<db>_<table>` slugified (replace `.` and `-` with `_`) |
   | `description` | Best one-liner describing the source — derive from db/table name; if unsure, ask the user |
   | `evidence_type` | Heuristic: `curated` for UniProt/SwissProt, `experimental` for fitness/phenotype/biochem assay tables, `computational` for eggNOG/KEGG/InterPro/COG annotations, `literature` for PubMed/PMC-backed text |
   | `diamond_db` | `/global_share/gene-annotation-predictor/data_sources/sequences/<name>.dmnd` |
   | `organism_column` | Set when an organism / strain / GTDB column is present |
   | `annotation_columns` | One `{column, label}` entry per `ANN_COLS` match; pick human-readable labels |
   | `annotation_query` | `SELECT <id_col> AS id, <ann_col1>, <ann_col2>, ... FROM <db>.<table> WHERE <id_col> IN ({ids_placeholder})` |
   | `annotation_query_temp_view` | Spark variant: same SELECT but `JOIN _berdl_ids ON <id_col> = _berdl_ids.id` instead of the IN clause |
   | `build_from.sequence_query` | `SELECT <id_col> AS id, <seq_col> AS sequence FROM <db>.<table> WHERE <seq_col> IS NOT NULL` |

   See `/global_share/gene-annotation-predictor/data_sources/configs/builtin_*.yaml` for working templates.

### Step 2: Check Environment

Run these checks before building the command:

```bash
# Check .venv exists in package directory
[ -d /global_share/gene-annotation-predictor/.venv ] && echo "Poetry venv: OK"

# Check API key availability (priority order)
set -a && source .env 2>/dev/null; set +a
if [ -n "${CBORG_API_KEY:-}" ]; then
    echo "API: CBORG"
elif [ -n "${OPENAI_API_KEY:-}" ]; then
    echo "API: OpenAI"
elif [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    echo "API: Anthropic"
else
    echo "ERROR: No API key found"
fi

# Check InterProScan exists
[ -x /global_share/gene-annotation-predictor/bin/my_interproscan/interproscan-5.76-107.0/interproscan.sh ] && echo "InterProScan: OK"

# Check BERDL data dir
[ -d /global_share/gene-annotation-predictor/data_sources/sequences/ ] && echo "BERDL data: OK"

# Check summaries parquet
[ -f /global_share/gene-annotation-predictor/data_sources/sequences/manuscript-summaries.filtered.parquet ] && echo "Summaries parquet: OK"

# Check KBASE_AUTH_TOKEN for BERDL layer
[ -n "${KBASE_AUTH_TOKEN:-}" ] && echo "KBASE_AUTH_TOKEN: set"
```

If any critical check fails, inform the user and suggest remediation before proceeding.

### Step 2.5: Confirm DIAMOND DB Builds for New Sources

Skip this step when no `--berdl-source-config` was generated in Step 1.5.

For each source in `berdl_sources.yaml`, check whether its `diamond_db` file exists. If not, the CLI can build it under `--berdl-build-missing-dbs`, but builds can take 10–30 minutes for large tables — confirm before proceeding.

**Spark session for standalone build scripts.** Any Python script that calls `get_spark_session()` outside a running notebook kernel must call `refresh_spark_environment()` first to start the local Spark Connect server. Without it, `get_spark_session()` will hang indefinitely. In JupyterHub the server is pre-started automatically; in CLI scripts it is not.

```python
from berdl_notebook_utils.refresh import refresh_spark_environment
refresh_spark_environment()           # starts Spark Connect server + rotates MinIO creds

from berdl_notebook_utils import get_spark_session
spark = get_spark_session()           # now returns immediately

from gene_annotation_predictor.tools.diamond_db_builder import estimate_db_build_cost
n, est_min = estimate_db_build_cost(spark, source["build_from"]["sequence_query"])
```

**Large source tables (100M+ rows) take significant time to export.** A cross-table JOIN (e.g., filtering `entity` then joining `protein`) or an IN-clause scan on an unindexed 200M-row table both require full-table scans. For databases like `refdata_uniprot` or `kbase_uniprot_kb` where sequences and annotations are in separate tables:

- Use a single query with a broadcast hint so Spark does an efficient hash join:
  ```sql
  SELECT /*+ BROADCAST(e) */ p.protein_id AS id, p.sequence
  FROM refdata_uniprot.protein p
  JOIN refdata_uniprot.entity e ON p.protein_id = e.entity_id
  WHERE e.data_source = 'UniProt/Swiss-Prot'
    AND p.sequence IS NOT NULL AND p.sequence != ''
  ```
- Expect 15–30 min for the initial scan of a 200M-row table (data volume, not a bug).
- For very large exports that should survive session restarts, use the `/remote-compute` skill to submit the build as a CTS job instead of running it inline.

Then ask via `AskUserQuestion`:
> "Build DIAMOND DB for `<source_name>`? (~`<n>` sequences, est. `<est_min>` min)"
> Options: **Build now** / **Skip this source**

For each "Skip" answer, remove that source from `berdl_sources.yaml` before running Step 3. Pass `--berdl-build-missing-dbs` in Step 3 only when at least one source was approved for build.

### Step 3: Build and Run the Command

Construct the command from the package directory using `poetry run`:

```bash
cd /global_share/gene-annotation-predictor

set -a && source /home/cjneely/repos/BERIL-research-observatory/.env 2>/dev/null; set +a

PATH=./bin:$PATH poetry run gene-annotate \
  --input <FASTA_FILE(S)> \
  --model gpt-5.4 \
  <API_KEY_FLAGS> \
  --berdl-data-dir /global_share/gene-annotation-predictor/data_sources/sequences/ \
  --summaries-parquet /global_share/gene-annotation-predictor/data_sources/sequences/manuscript-summaries.filtered.parquet \
  --interproscan ./bin/my_interproscan/interproscan-5.76-107.0/interproscan.sh \
  --output-dir <OUTPUT_DIR> \
  --threads 64 \
  --berdl-use-spark \
  <OPTIONAL_FLAGS>
```

**API key**: No flag needed — the CLI auto-detects `CBORG_API_KEY` (CBORG gateway) or `ANTHROPIC_API_KEY` from the environment. Pass `--api-key KEY` only to override with an explicit value.

**`--description-is-organism`**: Include this flag when organism names were placed in the FASTA description lines during input preparation (Step 1) — i.e., when the FASTA was prepared with organism context in the header descriptions. Omit when no organism information is available for any sequence.

**Optional flags** (include only if user requested):
- `--model <model>` — override default `gpt-5.2`
- `--description-is-organism` — include when FASTA descriptions contain organism names
- `--evalue`, `--min-identity`, `--query-coverage`, `--subject-coverage` — DIAMOND thresholds
- `--threads <N>` — override default 64
- `--prompt-file <path>` — custom LLM prompt
- `--berdl-source-config <output_dir>/berdl_sources.yaml` — include when Step 1.5 produced a YAML
- `--berdl-build-missing-dbs` — include when at least one source from Step 2.5 was approved for build

### Step 4: Monitor Execution

The tool runs synchronously — it processes each sequence through the full evidence pipeline (DIAMOND search, InterProScan, fitness lookup, LLM annotation). For large FASTA files this can take significant time.

- Display any stdout/stderr output to the user
- If the run is expected to be long (many sequences), warn the user and consider running in the background

### Step 5: Present Results

After completion, read the output TSV from `<output-dir>/<output-dir-name>_annotations.tsv`.

**Output file:** Always write the full Step 5 output to `<output-dir>/<output-dir-name>_summary.txt`. This file is the persistent record of the run — write it regardless of how many sequences were annotated or whether the analysis is shown in chat.

**Large-run gate (> 10 sequences):** Before generating the per-protein Analysis fields, ask the user:
> "The run produced N annotations. Generating the comparative analysis for each protein is LLM-intensive. Proceed with full analysis? Results will be written to `<summary-path>`."
> Options: **Yes, run full analysis** / **No, write tier summary and annotations only**

If the user declines or there are > 10 sequences and no confirmation: write the summary file with the tier summary (5a) and per-protein blocks without the Analysis field, and tell the user they can request the analysis later. Do not display the full per-protein blocks in chat for runs > 10 sequences — only report the tier summary and the path to the summary file.

For ≤ 10 sequences: run the full analysis automatically, display in chat, and write to file.

#### 5a. Tier summary

Always show the distribution and tier legend first (in chat and in the summary file):

```
Annotated: 9/10   |  Tier A: 2  |  Tier B: 6  |  Tier C: 1  |  Failed: 1

Tier legend (from gene_annotation_predictor/tools/prompts.py):
  [A] Strong, actionable — ≥40% identity to a biochemically characterized homolog, OR specific fitness
      signal, OR convergent evidence from ≥2 independent sources. Specific EC/substrate claims allowed.
  [B] Family/class-level — homologs <40% identity or only pathway-level phenotypes; OR IPR names an
      enzyme/EC but no corroborating experimental data. Substrate class only; no specific EC or substrate.
  [C] Fold-only — broad structural family from IPR alone; no fitness data, no characterized homologs.
      Output is a superfamily stub (e.g., "P450 superfamily protein, substrate undetermined").
```

Include the count of failures (rows where `annotation` starts with `ERROR:` or `tier` is empty).

#### 5b. Per-protein blocks

For each row in the TSV, produce a block of this form:

```
[A] sequence_id (organism)
    Predicted:            <full annotation text>
    Evidence:             <condensed evidence line>
    Experimental support: yes / no (computational only)
    Known:                <known function or "(not available)">
    Analysis:             <2–4 sentence narrative — see below>
```

**Condensed evidence line** — check which evidence columns are non-empty and build a comma-separated summary. Mark experimentally-derived sources with `*`:

| Column | Label to use | Experimental? |
|--------|-------------|---------------|
| `berdl_paperblast_evidence` | `PaperBLAST (BERDL)*` | Yes — literature-curated experimental characterizations |
| `paperblast_evidence` | `PaperBLAST*` | Yes — literature-curated experimental characterizations |
| `berdl_fitness_evidence` or `fitness_evidence` | `Fitness browser (co-fitness)*` | Yes — experimental transposon fitness co-fitness profiles |
| `cofitness_evidence` | `Co-fitness*` | Yes — experimental co-fitness correlations |
| `evidence_fitnessbrowser_aaseqs` | `Fitness browser (gene annotations)*` | Yes — direct gene descriptions from TnSeq-characterized loci |
| `gene_neighborhoods` | `Gene neighborhoods` | No — genomic context from conserved gene order |
| `berdl_pangenome_evidence` | `Pangenome` | No — comparative/computational clustering |
| `ipr_annotations` | `InterProScan` | No — computational domain/family prediction |

**Dynamic source columns.** When `--berdl-source-config` was used, the TSV contains additional `evidence_<source_name>` columns (one per active source). Discover them at read-time and look up each source's `description` and `evidence_type` from the YAML:

```python
import yaml, polars as pl
sources_by_name = {c["name"]: c for c in yaml.safe_load(open("berdl_sources.yaml"))} \
                  if Path("berdl_sources.yaml").exists() else {}
df = pl.read_csv(output_tsv, separator="\t", infer_schema_length=0)
dynamic_cols = [c for c in df.columns if c.startswith("evidence_")
                and c not in {"evidence", "evidence_strategy"}]
```

For each dynamic column with non-empty content, label it as `<source_name> (<source_description>)` and mark with `*` when its `evidence_type` is `experimental` or `curated`. Add these to the condensed evidence line alongside the built-in sources.

Any other BERDL dataset included in the evidence whose description mentions experimental derivation (e.g., phenotype assays, growth measurements, biochemical characterization) should also be marked with `*`.

Format the evidence line as: `Evidence: PaperBLAST (BERDL)*, Pangenome, InterProScan`

After the evidence line, add an experimental support note:
- If any `*`-marked source is present: `Experimental support: yes`
- If only computational sources are present: `Experimental support: no (computational only)`

If all evidence columns are empty, write: `Evidence: (none — structural/fold only)` and `Experimental support: no`

**Failed rows** — when `tier` is empty or `annotation` starts with `ERROR:`:

```
[FAILED] sequence_id (organism)
    Known (eggNOG/BERDL): <known function if available>
    Evidence:             <condensed evidence line>
    Experimental support: <yes/no>
    Analysis:             <narrative>
```

**Known function** — check two sources in priority order:

1. **BERDL annotation side file** (highest priority): if a `.annotations.json` file was written alongside the input FASTA during input preparation (proteins may have been sourced from any BERDL database — e.g., `kbase_ke_pangenome.eggnog_mapper_annotations`, `kbase_uniprot`, `kescience_paperblast`, etc.), load it. It is keyed by sequence ID and contains at minimum `preferred_name` and `description`; optionally `ec`, `cog_category`, `kegg_ko`, `gos`. Use `preferred_name — description [EC:x.x.x.x]` as the known function string, including any additional fields that are non-empty and non-`-`.

2. **FASTA header description** (fallback): re-read the original input FASTA and extract the description text from each `>` header line (all text after the sequence ID). Use this as the known function **only when `--description-is-organism` was NOT used** — when that flag is set the description is organism context, not a functional annotation, so write `Known: (organism context only)` and skip comparison.

When a known function is available from either source and the prediction substantively differs, open the Analysis field with `⚠ Differs from known annotation:` before the narrative.

**Analysis field** — write 2–4 sentences covering three things:

1. **What drove the prediction.** Name the evidence sources that had the most weight: which PaperBLAST homologs were found (identity %, organism, reaction), what InterProScan domains were matched, whether fitness data implicated a specific condition/substrate, or what pangenome cluster context was available. If the run failed, describe what evidence was present and what may have caused the LLM to fail.

2. **Agreement or divergence with the known annotation.** State whether the prediction agrees, partially agrees, or conflicts. Note where the prediction adds specificity beyond the known annotation (e.g., substrate name, reaction mechanism, pathway role), or where the known annotation may itself be incorrect or misleading (e.g., a gene name that does not match the EC number or domain evidence). Flag potential reference annotation errors explicitly.

3. **What would improve confidence or resolve uncertainty.** Specify the missing evidence type concretely: e.g., "A PaperBLAST homolog above 40% identity with biochemical characterization would upgrade this to Tier A", "Fitness data in a cobalamin-biosynthesis context would confirm the B12 pathway role", or "The LLM failure suggests the evidence may be conflicting — reviewing the raw `evidence` column and rerunning may help."

For failed rows, focus the analysis on (1) what evidence was collected before the failure and (2) likely cause and remediation.

#### 5c. Truncation for large runs (> 10 sequences, analysis approved)

When the user has approved full analysis for a run > 10 sequences, write everything to the summary file but display only the tier summary in chat, then report the summary file path.

#### 5d. Offer next steps

After the per-protein output (or after reporting the summary file path for large runs):
- Filter or sort results by tier
- Cross-reference with BERDL data (`/berdl`)
- Literature review on annotated functions (`/literature-review`)
- Include in project synthesis (`/synthesize`)

## Configurable Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--model` | `gpt-5.4` | LLM model: `gpt-5.1`, `gpt-5.2`, `gpt-5.3`, `gpt-5.4`, `claude-sonnet-4.5`, `claude-sonnet-4.6`, `claude-opus-4.5` |
| `--threads` | `64` | CPU threads for DIAMOND and InterProScan |
| `--output-dir` | `./output` | Where to write results |
| `--evalue` | `1e-3` | E-value cutoff for DIAMOND hits |
| `--min-identity` | `0.3` | Minimum sequence identity (0-1) |
| `--query-coverage` | `80.0` | Query coverage % for DIAMOND |
| `--subject-coverage` | `80.0` | Subject coverage % for DIAMOND |
| `--fitness-threshold` | `0.4` | Minimum absolute fitness score |
| `--t-threshold` | `2.0` | Minimum T-statistic for fitness data |
| `--prompt-file` | built-in | Custom system prompt for the LLM |

## Evidence Tiers

Tier definitions are authoritative in `/global_share/gene-annotation-predictor/gene_annotation_predictor/tools/prompts.py` (lines 62–75). Summaries:

**Tier A — Strong, actionable evidence** (specific functional claims allowed)
- At least one homolog with ≥40% identity that is biochemically characterized with an explicit EC number, substrate name, or reaction mechanism in its manuscript/summary; OR
- Fitness data implicating a specific substrate, stressor, or condition (not just generic growth effects); OR
- Convergent signal from ≥2 independent sources (e.g., IPR EC number + fitness + gene neighborhood with annotated pathway enzymes).

**Tier B — Moderate evidence** (family/class-level claims only)
- Homologs present but all <40% identity, OR manuscript text describes only organism/pathway-level phenotypes with no direct biochemical characterization; AND/OR
- InterProScan hits name an enzyme or EC number but no corroborating experimental data from fitness or characterized homologs.
- Allowed: enzyme class, transporter family, substrate *class*. NOT allowed: specific substrate, EC number, or pathway unless ≥2 independent sources agree.

**Tier C — Weak evidence** (decline to make specific claims)
- Only InterProScan annotations available AND hits describe broad structural/fold families (e.g., Rossmann fold, TIM barrel, P450 superfamily) with no EC number and no named enzyme function; AND
- No fitness data, no gene neighborhood with annotated neighbors, no characterized homologs.
- Required output: fold name as a family-level stub only (e.g., `P450 superfamily protein, substrate undetermined`). No substrate, pathway, or reaction mechanism guesses.

## Caching

DIAMOND results, InterProScan output, and batch evidence files are cached under `<output-dir>/.cache/`. Subsequent runs with the same `--output-dir` resume from where they left off. To force a fresh run, delete `<output-dir>/.cache/` or use a new `--output-dir`.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `poetry: command not found` | Poetry not installed or not on PATH | Install Poetry or ensure it's on PATH |
| `.venv` missing | Virtual environment not created | Run `poetry install` from `/global_share/gene-annotation-predictor` |
| No API key found | Neither `CBORG_API_KEY` nor `ANTHROPIC_API_KEY` in environment | Set `CBORG_API_KEY` (preferred) or `ANTHROPIC_API_KEY` in `.env` |
| InterProScan not found | Binary missing or not executable | Verify `/global_share/gene-annotation-predictor/bin/my_interproscan/interproscan-5.76-107.0/interproscan.sh` exists and is executable |
| `InterProScan failed (exit 231)` — tool continues without IPR | A sequence contains `*` (stop-codon marker from ORF predictors like Prodigal). InterProScan rejects the entire batch, not just the offending sequence. | Strip `*` from all sequences during FASTA preparation (Step 1) |
| Summaries parquet not found | File missing from data_sources | Verify `/global_share/gene-annotation-predictor/data_sources/sequences/manuscript-summaries.filtered.parquet` exists |
| BERDL auth error | `KBASE_AUTH_TOKEN` missing or expired | Set or refresh token in `.env` |
| DIAMOND not found | `./bin/` not on PATH | Ensure the `PATH=./bin:$PATH` prefix is included and command is run after `cd /global_share/gene-annotation-predictor` |
| Spark session error | Spark not available in environment | Check that Spark dependencies are installed in the Poetry venv |

## Integration with Other Skills

### After annotation
- **`/literature-review`** — Search literature for annotated gene functions, especially Tier B/C annotations that need more context
- **`/berdl`** — Cross-reference annotations with pangenome data, pathway databases, or fitness browser data in BERDL
- **`/synthesize`** — Include annotation results in a project synthesis report

### Before annotation
- **`/berdl`** — Query BERDL for protein sequences to annotate (e.g., hypothetical proteins from a pangenome analysis)

## Instructions for Claude

1. **Accept any protein input format** — the user should not need to prepare FASTA themselves. Detect the input format, extract sequences + IDs + organism names, and write a well-formed FASTA file. Always include organism names in record descriptions when available.
2. **Use `--description-is-organism`** only when organism information was available and included in the FASTA descriptions during input preparation. Do not include it when the FASTA headers contain only sequence IDs.
3. **Do not pass any API key flag** — the CLI auto-detects `CBORG_API_KEY` then `ANTHROPIC_API_KEY` from the environment. Only use `--api-key` if the user provides a literal key to override. Do not ask the user unless no key is found in the environment.
4. **Run from the package directory** (`cd /global_share/gene-annotation-predictor`) so that `./bin` relative paths and `poetry run` resolve correctly.
5. **Always include `--summaries-parquet`** pointing to `/global_share/gene-annotation-predictor/data_sources/sequences/manuscript-summaries.filtered.parquet`.
6. **After completion**, always read and summarize the output TSV — don't just report success.
7. **For large inputs** (>50 sequences), warn the user about runtime and consider suggesting background execution.

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.
