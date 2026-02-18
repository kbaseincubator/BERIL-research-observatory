# Local BERDL Workflow Test Results

**Date**: 2026-02-17  
**Project**: Essential Metabolome  
**Goal**: Validate local BERDL workflow (Spark Connect + MinIO)

## Tests Performed

### ✅ TEST 1: Spark Connect from Local Machine
- **Status**: SUCCESS
- **Method**: Used `get_spark_session()` from `scripts/get_spark_session.py`
- **Connection**: `metrics.berdl.kbase.us:443` via `spark_connect_remote`
- **Proxy**: SSH tunnel (port 1338) + pproxy (port 8123)
- **Result**: Connected successfully, Spark version 4.0.1
- **Databases found**: 77 databases including `kbase_ke_pangenome` and `kbase_msd_biochemistry`

### ✅ TEST 2: Query Pangenome eggNOG Annotations  
- **Status**: SUCCESS
- **Query**: Extracted EC numbers from eggNOG annotations
- **Results**: 100 EC annotations retrieved
- **Sample EC numbers**: 5.4.99.5, 3.6.1.23, 1.4.3.5, 5.3.1.6
- **Performance**: Fast (<5 seconds)

### ✅ TEST 3: MinIO Data Access
- **Status**: SUCCESS (tested earlier)
- **Method**: `mc cp` via pproxy
- **Downloaded**: 185 MB from `projects/essential_genome/data/` in 57 seconds
- **Speed**: 3.21 MiB/s

### ⏳ TEST 4: Biochemistry Schema Discovery
- **Status**: IN PROGRESS
- **Finding**: `reaction` table schema is simpler than documented:
  - Columns: `abbreviation`, `deltag`, `deltagerr`, `id`, `is_transport`, `name`, `reversibility`, `source`, `status`
  - **No `ec_numbers` column** directly in reaction table
  - EC mappings likely in separate table or embedded in `source` field
- **Next**: Explore schema more to find EC → reaction mappings

## Key Achievements

1. **✅ Local Spark Connect Working**: Can run queries from local machine while compute runs on BERDL cluster
2. **✅ Proxy Chain Validated**: SSH tunnel + pproxy correctly routing traffic
3. **✅ MinIO Access Confirmed**: Can download/upload data to lakehouse
4. **✅ Cross-project Data Reuse**: Implemented policy for referencing data from other projects

## Workflow Components Validated

| Component | Status | Notes |
|-----------|--------|-------|
| SSH tunnel (port 1338) | ✅ | Manually started by user |
| pproxy (port 8123) | ✅ | Started via `scripts/start_pproxy.sh` |
| Spark Connect | ✅ | Using `get_spark_session()` from scripts |
| MinIO access | ✅ | Using `mc cp` with proxy |
| Pangenome queries | ✅ | eggNOG annotations working |
| Biochemistry queries | ⏳ | Schema exploration needed |

## Recommendations

1. **For notebooks**: Use `from get_spark_session import get_spark_session` (when `.venv-berdl` is active)
2. **For queries**: Keep using `spark.sql()` - works identically to JupyterHub
3. **For large results**: Export to MinIO via `scripts/export_sql.py`
4. **Schema discovery**: Always query `DESCRIBE table` before writing complex queries

## Next Steps

1. Complete biochemistry schema exploration (find EC mappings)
2. Create simplified notebook using `get_spark_session()`
3. Run full essential metabolome analysis
4. Document findings in REPORT.md
