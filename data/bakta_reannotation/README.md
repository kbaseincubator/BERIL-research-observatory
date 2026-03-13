# Bakta Reannotation of Pangenome Cluster Representatives

## Status

**Complete.** All 4 tables ingested into `kbase_ke_pangenome` on 2026-03-12.

### What was done

1. Annotated all **132,538,155** protein cluster representatives (from 27,690 species) using `bakta_proteins` v1.12.0 on NERSC Perlmutter
2. Extracted per-chunk tables (176 chunks) and combined into 4 final TSVs
3. Uploaded TSVs to MinIO user staging area
4. Ingested into Delta Lake via `data_lakehouse_ingest` on JupyterHub

### Delta Lake tables in `kbase_ke_pangenome`

| Table | Rows | Description |
|-------|------|-------------|
| `bakta_annotations` | 132,538,155 | Main annotations: gene, product, EC, GO, COG, KEGG, UniRef, MW, pI |
| `bakta_db_xrefs` | 572,376,477 | Database cross-references (db, accession) |
| `bakta_pfam_domains` | 18,807,208 | Pfam domain hits with scores, e-values, coverage |
| `bakta_amr` | 83,008 | AMR gene annotations from AMRFinderPlus |

### Example queries

```sql
-- Get bakta annotation for a gene cluster
SELECT * FROM kbase_ke_pangenome.bakta_annotations
WHERE gene_cluster_id = 'JABHIP010000076.1_14';

-- Find all AMR genes
SELECT gene_cluster_id, amr_gene, amr_product, identity
FROM kbase_ke_pangenome.bakta_amr
ORDER BY identity DESC;

-- Count Pfam domain assignments
SELECT pfam_id, pfam_name, COUNT(*) as n_clusters
FROM kbase_ke_pangenome.bakta_pfam_domains
GROUP BY pfam_id, pfam_name
ORDER BY n_clusters DESC
LIMIT 20;

-- Cross-reference: find all KEGG links for a cluster
SELECT gene_cluster_id, db, accession
FROM kbase_ke_pangenome.bakta_db_xrefs
WHERE gene_cluster_id = 'JABHIP010000076.1_14'
  AND db = 'KEGG';
```

## Bakta vs EggNOG Comparison

Comparison script: `scripts/compare_bakta_eggnog.py` (Spark-optimized, all joins stay in Spark).

### Per-field coverage (132.5M clusters)

| Annotation | Bakta | % | EggNOG | % | Winner |
|---|---|---|---|---|---|
| Gene name | 29.0M | 21.9% | 93.4M | 70.4% | EggNOG |
| Product/Description | 94.4M | 71.2% | 93.4M | 70.4% | Bakta |
| EC number | 19.0M | 14.4% | 25.9M | 19.6% | EggNOG |
| COG (informative) | 10.8M | 8.2% | 67.6M | 51.0% | EggNOG |
| KEGG KO | 22.9M | 17.3% | 51.0M | 38.5% | EggNOG |
| GO terms | 19.9M | 15.0% | 9.8M | 7.4% | Bakta |
| UniRef50 | 105.0M | 79.2% | — | — | Bakta |
| Pfam | 10.2M | 7.7% | 83.7M | 63.1% | EggNOG |

### Why bakta's COG/KEGG/Pfam coverage is lower

Bakta uses a **hierarchical annotation strategy**: PSC (UniProt protein similarity clusters) first, then Pfam HMMER only for hypotheticals. If PSC matches, bakta assigns the gene name/product/EC/KEGG from that UniProt entry and **skips Pfam HMMER**. This is why Pfam domains are only on hypothetical proteins (10.2M/132.5M).

EggNOG uses **orthology transfer** — maps every protein to an orthologous group and transfers ALL group annotations (COG, KEGG, Pfam, etc.), which yields higher coverage but potentially lower specificity.

### Combined coverage (union of both tools)

| Annotation | EggNOG alone | Bakta alone | Union | Gain |
|---|---|---|---|---|
| KEGG | 38.5% | 17.3% | **41.4%** | +2.9pp |
| EC | 19.6% | 14.4% | **22.8%** | +3.2pp |
| GO | 7.4% | 15.0% | **18.2%** | +10.8pp |
| Any function | 70.4% | 71.2% | **77.3%** | +6.1pp |

### Rescue analysis

- **39.2M clusters** have NO eggNOG annotation at all (29.4%)
  - Of these, bakta provides a product description for 11.2M (28.6%)
  - Bakta provides a UniRef50 link for 17.7M (45.1%)
- **7.5M clusters** have eggNOG but no description
  - Bakta rescues 5.3M of these (70.4%) with a functional annotation

### UniRef50 bridge to UniProt

Bakta provides UniRef50 IDs for 79.2% of clusters (105M). These can bridge to external databases via `kbase_uniprot.uniprot_identifier`:

- Only **33.3%** of bakta's 17.6M distinct UniRef50 IDs exist in the BERDL UniProt subset
- Of the matched IDs, the bridge reaches: RefSeq (71%), OrthoDB (46%), STRING (40%), KEGG (36%)
- The bridge table lacks GO, EC, InterPro, and Pfam — **importing full UniProt would unlock these**

### Key takeaways

1. **Bakta and eggNOG are complementary**, not competing — union raises "any function" from ~70% to 77.3%
2. **GO terms are bakta's clear win** — 2× eggNOG's coverage (15% vs 7.4%)
3. **EggNOG dominates for enrichment annotations** (COG, KEGG, Pfam) due to orthology transfer
4. **Bakta's UniRef50 links are the biggest new asset** — 79.2% coverage, enabling future UniProt bridging
5. **AMR annotations are unique to bakta** — 83K clusters with AMRFinderPlus hits

## Background

The `kbase_ke_pangenome` database has 1B gene cluster representatives but only eggNOG-based functional annotations. This reannotation adds Bakta's broader annotation pipeline:

- **UniProt lookups**: UPS (UniParc), IPS (InterPro), PSC/PSCC (UniRef clusters)
- **Pfam domain annotation**: HMM-based domain hits with coverage metrics
- **AMR detection**: AMRFinderPlus with identity/coverage scores
- **Cross-references**: Links to external databases (SO, UniRef, KEGG, COG, GO, EC, Pfam)
- **Physical properties**: Molecular weight and isoelectric point

### Software versions

- bakta: 1.12.0
- bakta DB: v6.0
- AMRFinderPlus: 4.2.7 (DB: 2026-01-21.1)
- HMMER: 3.4

### Key files on NERSC pscratch (ephemeral — may be purged)

- Chunks: `/pscratch/sd/p/psdehal/bakta_reannotation/chunks_2M/chunk_000.fasta` through `chunk_043.fasta`
- Raw results: `/pscratch/sd/p/psdehal/bakta_reannotation/results_2M/chunk_*/`
- Per-chunk tables: `/pscratch/sd/p/psdehal/bakta_reannotation/tables/chunk_*/`
- Final combined tables: `/pscratch/sd/p/psdehal/bakta_reannotation/tables/final/`

### Scripts

| Script | Purpose |
|--------|---------|
| `extract_bakta_tables.py` | Parse bakta TSV output into normalized tables per chunk |
| `combine_tables.py` | Concatenate per-chunk tables into final combined files |
| `ingest_bakta.py` | Original upload + ingest script (paths point to NERSC) |
| `run_ingest.py` | Final ingest script used for Delta Lake import (reads from MinIO user staging) |
| `compare_bakta_eggnog.py` | Spark-optimized comparison of bakta vs eggNOG coverage |
| `bakta_reannotation.json` | Ingestion config with table schemas |

### Ingestion notes

- Tenant is `kbase` (not `kbase_ke`) — see pitfalls doc
- `data_lakehouse_ingest` auto-prepends tenant name to the dataset as a namespace prefix, so `dataset="ke_pangenome"` with `tenant="kbase"` produces `kbase_ke_pangenome`
- Ingestion of all 4 tables took ~20 minutes on JupyterHub Spark
- Staging TSVs on MinIO were deleted after successful ingestion
