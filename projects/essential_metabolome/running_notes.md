# Essential Metabolome - Running Notes

**Project**: essential_metabolome
**Started**: 2026-02-17
**Author**: Paramvir Dehal (ORCID: 0000-0001-5810-2497)

---

## Key Learnings & Pitfalls Discovered

### ✅ Spark Connect from Local Machine
**Finding**: Must use `scripts/get_spark_session.py`, NOT standard PySpark

**What DOESN'T work**:
```python
# This fails with gRPC errors
from pyspark.sql import SparkSession
spark = SparkSession.builder.remote("sc://hub.berdl.kbase.us:443").getOrCreate()
```

**What WORKS**:
```python
# This works perfectly
from get_spark_session import get_spark_session
spark = get_spark_session()
```

**Why**: The `get_spark_session()` uses `spark_connect_remote` library and connects to `metrics.berdl.kbase.us` (not `hub.berdl.kbase.us`). It also properly handles proxy configuration.

**Performance**: Connection takes ~2-3 seconds, queries are fast

**For docs/pitfalls.md**:
- Document that standard PySpark SparkSession.builder.remote() doesn't work
- Must use scripts/get_spark_session.py
- Connection endpoint is metrics.berdl.kbase.us, not hub.berdl.kbase.us

---

### ✅ pproxy Handles gRPC Despite HTTP/1 Limitation
**Finding**: pproxy works for Spark Connect even though it's an HTTP/1 proxy

Initially thought pproxy wouldn't work for gRPC (HTTP/2), but it does when configured as:
- `grpc_proxy=http://127.0.0.1:8123`
- Routes through SOCKS5 tunnel on port 1338

The `spark_connect_remote` library somehow bridges this. Standard PySpark doesn't.

---

### ⚠️ ModelSEED Biochemistry Schema Different Than Expected
**Finding**: `kbase_msd_biochemistry.reaction` table has NO `ec_numbers` column

**Expected schema** (from docs): columns include `ec_numbers`
**Actual schema**:
- abbreviation, deltag, deltagerr, id, is_transport, name, reversibility, source, status
- NO ec_numbers column

**Next**: Need to find where EC → reaction mappings are stored:
- Possibly in `source` field (string, may contain EC references)
- Possibly in a separate junction/mapping table
- May need to use `/berdl-discover` on biochemistry database

**For docs/pitfalls.md**:
- Add note about biochemistry schema discrepancy
- Always DESCRIBE tables before querying

---

### ✅ Cross-Project Data Reuse Policy
**Decision**: Don't copy data from other projects, reference from lakehouse

**Rationale**:
- Avoids duplication
- Preserves attribution
- Single source of truth

**Implementation**:
```python
# WRONG: Don't copy files
mc cp berdl-minio/.../essential_genome/data/ ./data/essential_genome/

# RIGHT: Reference from lakehouse
lakehouse_path = "s3a://.../essential_genome/data/essential_families.tsv"
df = spark.read.csv(lakehouse_path, header=True, sep="\t")
```

**Documented in**: PROJECT.md

---

### 📊 MinIO Performance
**Transfer speed**: 3.21 MiB/s (185 MB in 57 seconds)
**Acceptable for**: Files <1 GB
**Proxy overhead**: Minimal (~10-15% vs direct connection estimate)

---

## Workflow Process Notes

### Session Start Checklist
1. ✅ Start SSH tunnel: `ssh -f -N -o ServerAliveInterval=60 -D 1338 ac.psdehal@login1.berkeley.kbase.us`
2. ✅ Start pproxy: `bash scripts/start_pproxy.sh` (runs in background)
3. ✅ Activate JupyterHub session: Open notebook at hub.berdl.kbase.us
4. ✅ Verify ports: `lsof -i :1338 -i :8123 | grep LISTEN`
5. ✅ Activate venv: `source .venv-berdl/bin/activate` (for notebooks)

### Useful Commands
```bash
# Test Spark Connect
python -c "from get_spark_session import get_spark_session; spark = get_spark_session(); print(spark.version)"

# Check proxy status
lsof -i :1338 -i :8123 | grep LISTEN

# MinIO with proxy
export https_proxy=http://127.0.0.1:8123
mc ls berdl-minio/cdm-lake/tenant-general-warehouse/microbialdiscoveryforge/projects/
```

---

## Potential Skill Improvements

### `/berdl-query` skill
**Suggestion**: Add example showing `get_spark_session()` usage in notebooks
**Current docs**: Show CLI usage of run_sql.py but don't emphasize the drop-in notebook replacement

**Example to add**:
```markdown
## Using in Notebooks

When `.venv-berdl` is active, notebooks can use get_spark_session():

\```python
from get_spark_session import get_spark_session
spark = get_spark_session()
df = spark.sql("SELECT * FROM kbase_ke_pangenome.pangenome LIMIT 10")
df.show()
\```

This is a drop-in replacement for the JupyterHub `get_spark_session()`.
```

### `/berdl-discover` skill usage
**Need**: Schema documentation for biochemistry database is incomplete
**Action**: Should run `/berdl-discover` on `kbase_msd_biochemistry` to document actual schema
**Priority**: Medium (blocking EC → reaction mapping)

---

## Project-Specific Notes

### Essential Gene Families
- 859 universally essential families (present in all 48 FB organisms)
- Located at: `berdl-minio/.../microbialdiscoveryforge/projects/essential_genome/data/`
- File: `essential_families.tsv` (2.9 MB, 17,223 rows total)
- Attribution: Dehal (2026), essential_genome project

### eggNOG Annotations
- Table: `kbase_ke_pangenome.eggnog_mapper_annotations`
- Size: 93M annotations
- EC column: `EC` (some have comma-separated lists)
- Join key: `query_name` = gene_cluster_id

### Next Analysis Steps
1. Explore biochemistry schema to find EC mappings
2. Load essential families from lakehouse via Spark
3. Map essential genes → EC numbers → reactions
4. Identify universally essential reactions
5. Pathway enrichment analysis

---

## Session Info
**Session name**: essential_metabolome (requested by user)
**Branch**: projects/essential_metabolome
**Working directory**: /Users/paramvirdehal/KBase/ke-pangenome-science

---

## Quick Reference

### Commits Made
1. Initial plan + structure
2. Cross-project data policy
3. Workflow validation (Spark Connect working)
4. (Next: Clean analysis notebook)

### Files Created
- RESEARCH_PLAN.md
- README.md
- WORKFLOW_TEST_RESULTS.md
- test_workflow.py (validation script)
- load_essential_families.py (helper)
- requirements.txt
- this file (running_notes.md)

---

*Note: This file is for development notes and doesn't need to be committed to git.*

---

## Notebook 01 Results (2026-02-17 21:58)

### ✅ Successful Execution
- Notebook ran successfully via `jupyter nbconvert --execute`
- Spark Connect from local machine working perfectly
- Total execution time: ~30-40 seconds

### Data Extracted
- **EC annotations**: 10,000 sample (from 93M+ total in eggNOG)
- **Unique EC numbers**: 8,914 distinct EC values
- Some ECs are comma-separated (e.g., "1.1.1.1,1.1.1.284") - need to split these

### Biochemistry Schema Findings
**Tables in kbase_msd_biochemistry**:
- molecule
- reaction  
- reagent
- reaction_similarity
- structure

**reaction table columns**:
- abbreviation, deltag, deltagerr, id, is_transport, name, reversibility, source, status
- **NO `ec_numbers` column** (confirmed)

### Next Steps
1. Explore `source` field in reaction table for EC references
2. Check if there's a separate EC → reaction mapping table
3. May need to parse `source` field (could be JSON/delimited string)
4. Consider using reaction_similarity or other tables for mapping
5. Might need `/berdl-discover` on biochemistry to fully document schema

### Files Created
- `data/eggnog_ec_annotations_sample.tsv` (1.2 MB, 10K rows)
- `data/unique_ec_numbers.tsv` (172 KB, 8,914 unique ECs)


---

## Biochemistry Schema Discovery (2026-02-17 22:15)

### ✅ Complete Schema Documented
Created module file: `.claude/skills/berdl/modules/biochemistry.md`

### 🔍 Key Findings

**Tables in kbase_msd_biochemistry**:
1. `reaction` (56K rows) - Biochemical reactions
2. `molecule` (46K rows) - Chemical compounds
3. `reagent` (263K rows) - Stoichiometry (reaction ↔ molecule links)
4. `reaction_similarity` (671M rows) - Pairwise similarities **[HUGE - avoid full scans]**
5. `structure` (97K rows) - Molecular structures (SMILES, InChI)

### ❌ Critical Limitation Discovered

**NO EC NUMBER → REACTION MAPPING IN DATABASE**

The `reaction` table does NOT have an `ec_numbers` column. This is a blocker for the original analysis plan.

**What's available**:
- Reaction names (enzyme systematic names)
- KEGG abbreviations (R numbers) for 80% of reactions
- ModelSEED reaction IDs

**What's missing**:
- Direct EC → reaction mappings
- KEGG has EC mappings, but that's external to BERDL

### 📋 Revised Approach for Essential Metabolome

Since we can't map EC → reactions directly, alternative strategies:

**Option 1: Use KEGG IDs instead of EC**
- eggNOG has `KEGG_ko` column (KEGG Orthology)
- Map essential genes → KEGG KO → KEGG reactions → ModelSEED (via abbreviation field)
- Coverage: 80% of reactions have KEGG abbreviations

**Option 2: Focus on Pathway-Level Analysis**
- eggNOG has `KEGG_Pathway` column
- GapMind has pathway predictions (305M rows in pangenome)
- Map essential genes → pathways (not individual reactions)
- Identify universally essential PATHWAYS instead of reactions

**Option 3: Use GapMind for Metabolic Analysis**
- GapMind predictions are pathway-level (carbon sources, amino acids, etc.)
- Link essential gene families → GapMind pathway completeness
- Identify metabolic capabilities of essential gene set

**Recommendation**: Option 2 or 3 - focus on pathway-level analysis using GapMind, which is already integrated in pangenome database.

### 📊 eggNOG Columns Available
Need to check what's actually in eggNOG annotations:
- EC (confirmed - 8,914 unique)
- KEGG_ko (need to check coverage)
- KEGG_Pathway (need to check coverage)
- Description, Preferred_name, COG_category (confirmed)

### Next Steps
1. Query eggNOG to check KEGG_ko and KEGG_Pathway coverage
2. Decide on pathway-level vs reaction-level analysis
3. Pivot to GapMind if KEGG coverage is low
4. Update RESEARCH_PLAN.md with revised approach


---

## SESSION SUMMARY (2026-02-17 - essential_metabolome)

### ✅ Major Achievements

1. **Local BERDL Workflow Fully Validated**
   - Spark Connect from local machine: ✅ WORKING
   - Key: Use `scripts/get_spark_session.py`, NOT standard PySpark
   - Connection: metrics.berdl.kbase.us:443 via spark_connect_remote
   - Proxy: SSH tunnel (1338) + pproxy (8123) working perfectly
   - MinIO: Downloaded 185 MB in 57 seconds (3.21 MiB/s)

2. **Critical Discovery: NO EC Mappings in BERDL**
   - Biochemistry database has no ec_numbers column
   - kbase_genomes has no EC annotations (structural data only)
   - EC data ONLY in kbase_ke_pangenome.eggnog_mapper_annotations
   - Documented in docs/schemas/biochemistry.md

3. **Research Plan Pivoted to Pathway Analysis**
   - Original: EC → reactions (BLOCKED by missing mappings)
   - Revised: GapMind pathway completeness (better approach)
   - Focus: 48 FB organisms, 80 pathways (18 AA + 62 carbon)
   - More biologically meaningful than individual reactions

4. **GapMind Data Explored**
   - 305M predictions across 293K genomes
   - Amino acid biosynthesis: met, gln, asn, gly, thr most complete
   - Score categories: complete, likely_complete, steps_missing, not_present
   - Pathway-level (not gene-level) predictions

### 📊 Repository Status

**Branch**: projects/essential_metabolome (7 commits)
1. Initial plan + structure
2. Cross-project data policy
3. Workflow validation tests
4. Notebook 01 with outputs (EC extraction)
5. Biochemistry module documentation
6. Updated biochemistry schema (EC limitation)
7. Research plan v2 (GapMind pivot)

**Files Created**:
- RESEARCH_PLAN.md (v2)
- README.md
- WORKFLOW_TEST_RESULTS.md
- notebooks/01_extract_essential_reactions.ipynb (with outputs)
- data/eggnog_ec_annotations_sample.tsv (1.2 MB)
- data/unique_ec_numbers.tsv (8,914 unique ECs)
- docs/schemas/biochemistry.md (updated)
- running_notes.md (this file)

### 🔑 Key SQL Patterns That Work

```python
# Connect to Spark (CORRECT WAY)
from get_spark_session import get_spark_session
spark = get_spark_session()

# Query with limit
df = spark.sql("SELECT * FROM kbase_ke_pangenome.gapmind_pathways LIMIT 100")

# Convert to pandas for local analysis
pd_df = df.toPandas()

# Save locally
pd_df.to_csv('output.tsv', sep='\t', index=False)

# Always close
spark.stop()
```

### 📋 Next Steps for Notebook 02

**Goal**: Identify universally complete metabolic pathways in 48 FB organisms

**Steps**:
1. Load FB organism list from essential_genome project
2. Map FB organism names → pangenome genome_ids
   - FB uses names like "Keio", "DvH", "Burk376"
   - Pangenome uses genome_ids like "GCF_000005845.2"
   - Need mapping table or fuzzy matching
3. Extract GapMind predictions for 48 genomes
4. Identify universally complete pathways (complete in all 48)
5. Characterize:
   - Which amino acids all can synthesize?
   - Which carbon sources all can use?
   - Core vs peripheral metabolism
6. Save results, create visualizations

**Potential Challenge**: Mapping FB names to genome IDs
- May need to use taxonomy or NCBI IDs
- Check if essential_genome data has genome IDs
- Alternative: Use species names from essential_families

### 💡 Important Decisions Made

1. **Data Reuse Policy**: Reference from lakehouse, don't copy (PROJECT.md)
2. **EC Approach Abandoned**: Pathway-level more meaningful + feasible
3. **GapMind Over KEGG**: Data already in BERDL, no external deps
4. **Focus on 48 FB Organisms**: Subset with essential gene data

### ⚠️ Pitfalls to Document (for docs/pitfalls.md)

1. **Spark Connect requires spark_connect_remote**
   - Standard PySpark SparkSession.builder.remote() FAILS
   - Must use scripts/get_spark_session.py
   - Connects to metrics.berdl.kbase.us NOT hub.berdl.kbase.us

2. **pproxy works for gRPC despite being HTTP/1**
   - Initial assumption: gRPC needs HTTP/2
   - Reality: spark_connect_remote bridges this somehow
   - Config: grpc_proxy=http://127.0.0.1:8123

3. **Biochemistry has no EC mappings**
   - Common assumption: ModelSEED has EC → reaction links
   - Reality: Only KEGG abbreviations (80% coverage)
   - Must use external KEGG data or pivot approach

### 🎯 Session Metrics

- **Time**: ~3-4 hours
- **Commits**: 7
- **Notebooks**: 1 (with outputs)
- **Data files**: 2 (8,914 unique ECs extracted)
- **Schemas documented**: 1 (biochemistry)
- **Workflow components validated**: MinIO ✅, Spark Connect ✅
- **Research plan iterations**: 2 (v1 → v2 pivot)

### 🚀 Ready State

**Environment**:
- ✅ .venv-berdl installed and working
- ✅ pproxy running on port 8123
- ✅ SSH tunnel on port 1338
- ✅ JupyterHub session active
- ✅ KBASE_AUTH_TOKEN in .env

**Code**:
- ✅ All notebooks execute successfully
- ✅ get_spark_session() working perfectly
- ✅ Cross-database queries tested

**Next Session**: Create Notebook 02 for GapMind pathway analysis

---

*End of session summary - ready for auto-compaction*


---

## Notebook 02 Progress (2026-02-17 Evening)

### 🔍 Genome Table Schema Discovery
Discovered that `kbase_ke_pangenome.genome` table has limited columns:
- genome_id, gtdb_species_clade_id, gtdb_taxonomy_id
- ncbi_biosample_id, fna_file_path_nersc, faa_file_path_nersc
- **NO** `ncbi_taxid`, `gtdb_organism_name`, or `is_representative` columns

This blocked the original matching strategy (FB taxonomyId → pangenome ncbi_taxid).

### ✅ Solution: Manual Genome Mapping
Created `data/fb_genome_mapping_manual.tsv` with known FB organism → genome_id mappings:
- Started with 8 well-known organisms (Keio, DvH, MR1, Putida, PS, Caulo, Smeli, azobra)
- Verified GapMind has data for all 8 genomes
- Can expand mapping incrementally for remaining 37 organisms

### 📊 Initial Test Results
- 8 mapped organisms
- GapMind query successful
- Sample shows complete/likely_complete pathways for arg, asn, chorismate, cys
- Ready to proceed with pathway analysis on subset

### Next Steps
1. Update Notebook 02 to use manual mapping
2. Run full pathway analysis on 8 organisms
3. Identify universally complete pathways in subset
4. Document approach in RESEARCH_PLAN.md
5. Expand mapping to all 45 organisms (iterative)

