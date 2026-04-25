# Fitness Browser Stubborn Set — Curator-Like Genes Left Unannotated

## Research Question

Among the ~138K Fitness Browser genes that were NOT in Price's curator-accumulated `kescience_fitnessbrowser.reannotation` table, which can be re-annotated using BERDL-native evidence (including PaperBLAST-linked literature), and which are genuinely unresolvable?

## Status

**Pilot complete** — top 210 of 137,798 ranked genes evaluated by LLM-reasoning subagents with PMC paper fetching. Walking continues in batches.

## Headline finding (n = 210)

| Verdict | n | % |
|---|---:|---:|
| already_correctly_named | 72 | 34% |
| improvable_correction | 69 | 33% |
| improvable_new | 52 | 25% |
| recalcitrant | 17 | 8% |

**58% of top-ranked non-reannotated genes are improvable** (correction + new). 8% are genuinely recalcitrant despite a strong phenotype. Literature consultation via PubMed MCP changed verdicts on ~30-40% of genes that consulted papers.

## Approach

Direct primary-fitness ranking (no learned model) → per-gene structured dossier (8 evidence layers including PaperBLAST homologs) → Claude Code subagents reason over each dossier and fetch PMC full text via PubMed MCP for borderline cases → 4-verdict classification with proposed annotation, EC, rationale, confidence, and PMIDs consulted.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — full methodology + revision history (v7)
- [Report](REPORT.md) — pilot findings, cross-gene cluster discoveries, limitations
- [References](references.md) — Price 2018 + Fitness Browser documentation
- [data/improvable_genes.tsv](data/improvable_genes.tsv) — 121 actionable proposals (ranked)
- [data/recalcitrant_genes.tsv](data/recalcitrant_genes.tsv) — the project's "stubborn" answer set
- [data/cited_pmids.tsv](data/cited_pmids.tsv) — 80 unique PMIDs cited
- [data/cross_gene_clusters.md](data/cross_gene_clusters.md) — published functional clusters reconstructed (8 PMIDs, ≥3 genes each)
- [data/verdicts_characterisation.md](data/verdicts_characterisation.md) — contingency tables and notable corrections
- Figures: [figures/](figures/)
- Notebooks: [notebooks/](notebooks/)

## Reproduction

### Prerequisites

- BERDL access (`KBASE_AUTH_TOKEN`)
- `.venv-berdl` virtualenv (`bash scripts/bootstrap_client.sh`)
- BERDL proxy chain (SSH tunnels on 1337/1338 + pproxy on 8123) — see `.claude/skills/berdl-query/references/proxy-setup.md`
- DIAMOND v2 (`brew install diamond`)
- `mc` (MinIO client) configured for `berdl-minio` (uses HTTPS_PROXY=http://127.0.0.1:8123)

### Pipeline (one-time data extraction)

```bash
source .venv-berdl/bin/activate

# Spark extracts (each takes 30-90 seconds)
python projects/fitness_browser_stubborn_set/notebooks/00_extract_gene_features.py
python projects/fitness_browser_stubborn_set/notebooks/02_extract_secondary_evidence.py
python projects/fitness_browser_stubborn_set/notebooks/03_extract_paperblast_via_swissprot.py
python projects/fitness_browser_stubborn_set/notebooks/06_extract_phenotype_conditions.py
python projects/fitness_browser_stubborn_set/notebooks/07_extract_partners_and_neighbors.py
python projects/fitness_browser_stubborn_set/notebooks/08_extract_functional_text.py

# DIAMOND vs PaperBLAST (one-time, ~10 minutes)
# Download FB AA sequences:
curl -sSL -o data/fitness_browser/fb_aaseqs_all.fasta https://fit.genomics.lbl.gov/cgi_data/aaseqs
# Filter to curated orgs (~140K seqs), then build DIAMOND DB and search:
HTTPS_PROXY=http://127.0.0.1:8123 mc cp --recursive \
  berdl-minio/cdm-lake/tenant-sql-warehouse/kescience/kescience_paperblast.db/uniq/ \
  data/paperblast/uniq_parquet/
HTTPS_PROXY=http://127.0.0.1:8123 mc cp --recursive \
  berdl-minio/cdm-lake/tenant-sql-warehouse/kescience/kescience_paperblast.db/Gene/ \
  data/paperblast/Gene/
HTTPS_PROXY=http://127.0.0.1:8123 mc cp --recursive \
  berdl-minio/cdm-lake/tenant-sql-warehouse/kescience/kescience_paperblast.db/SeqToDuplicate/ \
  data/paperblast/SeqToDuplicate/
HTTPS_PROXY=http://127.0.0.1:8123 mc cp --recursive \
  berdl-minio/cdm-lake/tenant-sql-warehouse/kescience/kescience_paperblast.db/GenePaper/ \
  data/paperblast/GenePaper/

python projects/fitness_browser_stubborn_set/notebooks/04_dump_paperblast_sequences.py
diamond makedb --in data/paperblast/paperblast_uniq.fasta --db data/paperblast/paperblast_uniq
diamond blastp --query data/fitness_browser/fb_aaseqs_curated.fasta \
  --db data/paperblast/paperblast_uniq.dmnd \
  --out data/paperblast/fb_vs_paperblast.tsv \
  --outfmt 6 qseqid sseqid pident length qlen slen evalue bitscore qcovhsp scovhsp \
  --evalue 1e-5 --id 30 --query-cover 50 --max-target-seqs 5 --threads 8
python projects/fitness_browser_stubborn_set/notebooks/05_paperblast_via_diamond.py
```

### Pipeline (per-batch reasoning)

```bash
# Rank all non-reannotated genes (one-time)
python projects/fitness_browser_stubborn_set/notebooks/01_rank_genes.py

# For each batch, prepare a dossier file then spawn a Claude Code subagent
# to reason over it and write verdicts. Example:
python projects/fitness_browser_stubborn_set/notebooks/02_prepare_batch.py \
  --batch-id B01 --start-rank 1 --n 25
# Then spawn a subagent (via Agent tool in Claude Code) with the prompt template
# in REPORT.md to reason over batch_B01/input.md and write batch_B01/output.jsonl

# After all batches return, aggregate + characterise + synthesize
python projects/fitness_browser_stubborn_set/notebooks/03_aggregate_verdicts.py
python projects/fitness_browser_stubborn_set/notebooks/04_characterise_verdicts.py
python projects/fitness_browser_stubborn_set/notebooks/05_synthesize.py
```

### Expected runtime

- One-time extracts: ~10 min total (Spark) + ~10 min (DIAMOND) + ~5 min (MinIO downloads)
- Per-batch reasoning: ~5 min per 25-gene batch (5 batches in parallel = ~5 min for 125 genes)

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
