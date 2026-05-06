# BERDL Database: Common Pitfalls & Gotchas

**Purpose**: Quick reference for avoiding common issues when querying BERDL databases.

Use BERDL notebook helpers for live access-aware database and table discovery.
See [schemas/](schemas/) for per-collection documentation.

---

## General BERDL Pitfalls

### [genotype_to_phenotype_enigma] Short Strain Names Collide Across Databases

**Problem**: ENIGMA field isolates often have short strain names (MT20, MT42, GW460-LB6, FW507-14TSA) that are **not globally unique**. When matching to `kbase_ke_pangenome.gtdb_metadata.ncbi_strain_identifiers`, these short names can match **completely unrelated organisms** in NCBI. Example: ENIGMA MT20 is *Rhodanobacter glycinis* (Xanthomonadales, groundwater), but GTDB's MT20 is *Streptococcus pneumoniae* (Lactobacillales, clinical) — 8,434 genomes, 1,751 clinical. This contaminated genus-environment profiles with spurious clinical data.

**Scale**: 12 of 32 pangenome linkages via `ncbi_strain_identifiers` were incorrect genus matches.

**Fix**: Always cross-check the genus from the source database (e.g., `enigma_genome_depot_enigma.browser_taxon`) against the genus from the GTDB match. Reject linkages where genera disagree:

```python
# After matching via ncbi_strain_identifiers, verify genus consistency
depot_genus = depot_taxon.split()[0]  # e.g., "Rhodanobacter" from "Rhodanobacter glycinis"
gtdb_genus = gtdb_taxonomy.split(';g__')[1].split(';')[0]  # from GTDB taxonomy string
if depot_genus.lower() not in gtdb_genus.lower():
    # REJECT this linkage — strain name collision
    pass
```

**Applies to**: Any project linking ENIGMA CORAL strains or genome depot strains to `kbase_ke_pangenome` via strain name matching. Use assembly accession (GCF_*) matching instead when possible — it's unambiguous.

### [genotype_to_phenotype_enigma] Commit Notebooks Alongside Their Artifacts, Not Just the TSVs

**Problem**: Analyses run interactively in a Claude Code session (pure Python REPL, not a committed `.ipynb`) can produce figures and data files that get staged and committed — while the code that produced them lives only in the session transcript. The project then *looks* reproducible (the README references NB08/NB09/NB10, runtime tables list them, the REPORT cites their findings) but `git log` finds no notebook history for those names. Downstream reviewers read the plan and REPORT at face value and miss the gap.

**Scale**: In this project, three "notebooks" (NB08, NB09, NB10 — the entire Act II/III closing) existed only as outputs. The reconstruction took a few hours once the gap was identified; it would have been far cheaper to have written `.ipynb` cells in the first place.

**Fix**:

- When an analysis is worth committing artifacts for, it is worth committing as a notebook. If you find yourself building figures in a REPL, pause and move the logic into a numbered notebook before saving results.
- Before running `/submit` (or any milestone commit), run `git log --all --oneline -- projects/{project_id}/notebooks/NB*.ipynb` to verify every NBxx referenced in the README/plan is backed by actual notebook history.
- If you inherit a project with this gap, reconstruct the notebooks from the committed artifacts; note the reconstruction in `RESEARCH_PLAN.md`'s revision history so reviewers know which numeric counts are the "interactive original" vs. the "reproducible re-run".

**Applies to**: Any Claude Code-assisted project. This is especially easy to trip over late in a project when the user is synthesizing and no longer creating fresh notebooks for each analytical step.

### [genotype_to_phenotype_enigma] Web of Microbes Binary "Produced" Requires Action Code Interpretation

**Problem**: `kescience_webofmicrobes.observation.action` is a single-letter code (`I` increased, `E` emerged, `N` no change, and occasionally `D` decreased). A naive `SELECT action` gives you the raw code; it does NOT give you a binary produced/consumed label. The binary definition used in NB02 and NB08 is `produced = action IN ('I', 'E')` — a compound is counted as produced when it either increased in supernatant (was there and more accumulated) or emerged (was below the detection limit and reached it).

```python
# correct binary encoding for "did this strain produce this metabolite?"
obs["produced"] = obs["action"].isin(["I", "E"]).astype(int)
```

**Why it matters**: Including `N` (no change) in the produced set makes every strain look like a production generalist and collapses the signal. Excluding `E` (emerged, sub-detection-limit → detectable) misses genuinely novel production.

**Applies to**: Any project touching `kescience_webofmicrobes.observation`.

### [ibd_phage_targeting] Agent Sessions Sharing a Checkout — Verify `git branch --show-current` Before Every Commit

**Problem**: Two Claude agent sessions (or any two processes) operating in the same repository clone share one `.git` directory and one working tree. A `git checkout` issued by one session silently reshapes the working tree for the other — files that exist on one branch but not the other simply *disappear* from the working tree, and subsequent `git commit` calls land on whichever branch HEAD is currently pointing at.

**Example** (observed 2026-04-24, during `ibd_phage_targeting` NB00 work): a session working on `projects/ibd_phage_targeting` was operating concurrently with a second `claude` process (PID 22230) working on `projects/plant_microbiome_ecotypes`. During the first session's long `jupyter nbconvert --execute` run, the second session ran `git checkout projects/plant_microbiome_ecotypes`. The first session's subsequent `git commit` landed on the plant-microbiome branch (not ibd), and the user observed `README.md` and `RESEARCH_PLAN.md` "missing" from `projects/ibd_phage_targeting/` when they inspected the directory — both files were still safely in git on the ibd branch, but the checkout had swept them out of the working tree.

**Fix — two layers**:

1. **Defensive hygiene (any session)**:
   - Call `git branch --show-current` immediately before every `git commit`. If the branch is not the one the session started on, investigate before committing.
   - Capture the intended branch name at session start; verify `HEAD` before each commit.
   - If the wrong branch was committed to: `git cherry-pick` onto the correct branch, then `git branch -f <stray> origin/<stray>` to reset the stray. No data loss as long as the stranded commit is recoverable via `git reflog`. Push the corrected branch immediately.

2. **Structural isolation (for parallel sessions)** — use `git worktree add` to give each concurrent session its own working directory on a dedicated branch:

```bash
git worktree add ../repo-copy-for-branch-X projects/X
# each session then works inside its own worktree directory
```

Each worktree has its own `HEAD` and working-tree state while sharing a single object store (cheap). A `git checkout` in one worktree does not affect the other. This is the clean fix for the drift scenario above and is the recommended practice whenever two agents work on the repo simultaneously.

**User-visible symptom to watch for**: "file X is missing from the project directory" when the agent believed it had just committed file X — this is almost always a wrong-branch commit (or, equivalently, a background checkout swept it out of the tree) rather than a genuine deletion. Recovery is cheap if caught early; easier to prevent with worktree isolation.

**Applies to**: Any agent session in this repository longer than a few minutes. Especially: scheduled remote agents, parallel user-started sessions, and auto-import hooks.

### [ibd_phage_targeting] MetaPhlAn3 Cross-Cohort Taxon Names Need a Synonymy Layer, Not Just Format Normalization

**Problem**: Cross-cohort microbiome analysis that pivots on `taxon_name_original` (or any string key) can silently segregate the same species into two non-overlapping rows when cohorts use different MetaPhlAn3 DB vintages / cMD-processing stages. Three divergences observed in the `~/data/CrohnsPhage` integrated mart:

1. **Format** — short name (`Faecalibacterium prausnitzii`) vs. full lineage string (`k__Bacteria|p__Firmicutes|...|s__Faecalibacterium_prausnitzii`). Same database, different export format.
2. **GTDB r214+ genus renames** — `Bacteroides vulgatus` (CMD_HEALTHY lineage) ↔ `Phocaeicola vulgatus` (CMD_IBD short name) are the same NCBI taxid, treated as separate species. Also affects *B. dorei / coprocola / plebeius / salanitronis / sartorii / massiliensis / coprophilus*, all now *Phocaeicola*.
3. **Other reclassification splits** — `Eubacterium rectale` → `Agathobacter rectalis`, `E. eligens` → `Lachnospira eligens`, `E. hallii` → `Anaerobutyricum hallii`; `Ruminococcus gnavus` → `Mediterraneibacter gnavus`; `Clostridium bolteae / clostridioforme / symbiosum / innocuum / asparagiforme / hathewayi / citroniae / aldenense` → *Enterocloster* / *Hungatella* / *Erysipelatoclostridium*; `Lactobacillus mucosae / ruminis` → *Limosilactobacillus / Ligilactobacillus*.

**Scale**: In the CrohnsPhage mart, CMD_IBD uses the modern names, CMD_HEALTHY uses legacy names — so a naive pivot gives log₂FC ≈ 28 (≈ 2.68 × 10⁸ fold) for every renamed species because one cohort's mean abundance collapses to pseudocount.

**The committed `ref_taxonomy_crosswalk` does not fully resolve this**: legacy `Bacteroides_X` rows have `ncbi_taxid = NaN`, so joining through taxid leaves them orphaned. The crosswalk lists *B. vulgatus* and *P. vulgatus* as two separate rows with different `canonical_name` values.

**Fix at three levels**:

1. **Format normalization** — parse the `s__Genus_species` component from full lineage strings and strip brackets from short names to get a canonical `"Genus species"`.
2. **Hand-curated synonym map** — enough for a targeted species battery. NB00 in `projects/ibd_phage_targeting/` ships a 23-entry `SYNONYM_MAP` covering the major renames above.
3. **Systematic reconciliation** — an NCBI-taxid-backboned synonymy layer with GTDB-version-aware rename tables. Mandatory before any cross-cohort aggregation over the full taxonomy (not just a curated battery). This is an NB01 dependency in `ibd_phage_targeting`.

**Applies to**: Any project using `fact_taxon_abundance` or any other MetaPhlAn3-derived table across multiple cohorts that may have been processed at different times (different mpa DB versions, different cMD releases). Also applies generally to merging MetaPhlAn outputs with GTDB-r214+ downstream analyses.

### [ibd_phage_targeting] curatedMetagenomicData Sub-Studies Are Disjoint Between HC and Disease Cohorts — Pooled LME is Unidentifiable

**Problem**: curatedMetagenomicData bundles samples from ~50+ published studies into `CMD_HEALTHY` and `CMD_IBD` buckets. The healthy and disease sub-studies **do not overlap** — every CMD_HEALTHY sample comes from a healthy-cohort study (LifeLinesDeep_2016, AsnicarF_2021, YachidaS_2019, HansenLBS_2018, …), every CMD_IBD CD sample comes from an IBD-cohort study (HallAB_2017, VilaAV_2018, LiJ_2014, IjazUZ_2017, NielsenHB_2014). **There is no sub-study that contains both CD and HC samples.**

A pooled `log_abundance ~ diagnosis + (1 | substudy)` linear mixed-effects model on the CD-vs-HC contrast is therefore structurally unidentifiable: the substudy random effect perfectly predicts diagnosis, so the model either silently fails to converge or absorbs all of the CD effect into the random intercept. `statsmodels.mixedlm` with `lbfgs` fails silently (returns without error but with no usable fixed-effect estimate) on this design.

**Scale**: In the `~/data/CrohnsPhage` integrated mart scoped to ecotype-assigned samples (8,489 total), 45 sub-studies have ≥ 10 HC samples, 5 sub-studies have ≥ 10 CD samples, and **0** sub-studies have both ≥ 10 of HC and ≥ 10 of CD. Vujkovic-Cvijin 2020 cites this kind of structural confounding as the reason to adjust; it cannot be adjusted via a standard random-effects model on the cMD pooled-cohort contrast.

**Detect**:

```python
# After parsing substudy from dim_samples.external_ids.study + participant_id 2nd token:
tbl = sample_meta.groupby('substudy').diagnosis.value_counts().unstack(fill_value=0)
hc_studies = set(tbl[tbl.get('HC', 0) >= 10].index)
cd_studies = set(tbl[tbl.get('CD', 0) >= 10].index)
assert len(hc_studies & cd_studies) > 0, "cMD pooled CD-vs-HC is substudy-confounded"
```

**Fix** — two-track pattern:

1. **Confound-free contrast: CD-vs-nonIBD within IBD sub-studies.** Four IBD sub-studies in cMD have both CD and nonIBD samples with ≥ 10 each (HallAB_2017, LiJ_2014, IjazUZ_2017, NielsenHB_2014; aggregate 242 CD / 369 nonIBD). Within each sub-study, run a within-study CLR-Δ or regression with no study-level confound. Combine across sub-studies via inverse-variance weighted meta-analysis. This is the clean CD-effect estimate.

2. **Pooled contrast: explicitly flag as substudy-confounded.** If a pooled CD-vs-HC effect must be reported, do not rely on substudy random effects to "adjust" for it. Quote the effect as-is with an explicit caveat that study, cohort, sequencing center, and sample prep are all collinear with diagnosis in this design. The within-substudy meta-analysis in (1) is the benchmark the pooled effect should be sanity-checked against.

3. **Proper substudy resolution**: participant_id format `CMD:HallAB_2017:SKST006` encodes substudy in the middle colon-separated token for IBD samples. For HC samples, the substudy lives in `dim_samples.external_ids` as a JSON blob with key `"study"` (e.g., `"AsnicarF_2021"`). Together these cover ≈ 80 % of cMD samples; short-prefix regex on sample IDs covers < 20 % and produces mostly noise categories.

```python
import json
def resolve_substudy(row):
    ext = row['external_ids']
    if isinstance(ext, str):
        try:
            d = json.loads(ext)
            if isinstance(d.get('study'), str): return d['study']
        except Exception: pass
    pid = row['participant_id']
    if isinstance(pid, str):
        parts = pid.split(':')
        if len(parts) >= 3 and parts[0] in ('CMD', 'HMP2'): return parts[1]
    return None
```

**Applies to**: any BERDL project that uses `fact_taxon_abundance` / cMD data for case-vs-control microbiome DA. Also generalizes to any pooled public-dataset analysis (SRA study inventories, Qiita studies, etc.) where the case and control cohorts were collected by different groups. The within-cohort CD-vs-nonIBD contrast is the design-consistent alternative.

### [ibd_phage_targeting] Feature Leakage in Cluster-Stratified DA: Clustering on Taxa Then Testing the Same Taxa Within Cluster

**Problem**: A common pattern in microbiome analysis is (i) define ecotypes / clusters by unsupervised partitioning of the taxon abundance matrix, then (ii) run differential abundance within each cluster. Step (i) selects samples on outcome — cluster membership is a function of the same taxon abundances step (ii) then tests. The result is **selection-on-outcome confounding**: within-cluster effect sizes are mechanically inflated for cluster-defining taxa, and the within-cluster top-N list is substantially the cluster definition itself.

**Scale — observed in `ibd_phage_targeting` NB04**: K=4 LDA ecotypes trained on MetaPhlAn3 species abundances, then within-ecotype CD-vs-HC CLR-Mann-Whitney on the same species matrix. NB04 reported a 33-species within-ecotype Tier-A list with effect sizes +0.5 to +3.0 CLR-Δ. Two leakage checks post-hoc:

- **Held-out-species sensitivity (NB04b §2)**: 5 random 50/50 species splits; refit LDA ecotypes on half A, re-test half B within refit-ecotypes; Jaccard between refit top-30 and original top-30 ∩ half-B. Bound: > 0.5 = leakage bounded, < 0.3 = leakage dominates. Observed: E1 = 0.230, E3 = 0.064.
- **Leave-one-species-out refit (NB04b §3)**: per battery species, refit ecotypes on all-OTHER species, re-derive cluster labels, re-test held-out species. *C. scindens* went from NB04 "n.s. within both ecotypes" (the basis for the "paradox RESOLVED" claim) to CD↑ in both E1 (CI +0.68, +0.87) and E3 (CI +1.13, +1.71) under LOO — the within-ecotype n.s. call was a self-selection effect.

Cross-check via an independent-design analysis (confound-free within-IBD-substudy CD-vs-nonIBD, see pitfall above) confirmed that most of the NB04 Tier-A E1 candidates had *negative* within-study effects — they are ecotype-markers, not CD-drivers.

**Detect**: any analysis that first clusters on feature matrix `X` and then runs per-cluster DA on subsets of `X` should run at least one of:

1. **Held-out-species sensitivity**: split features 50/50, cluster on one half, DA on the other, compare top-N against clusters-on-full-matrix top-N. Jaccard > 0.5 ⇒ leakage bounded.
2. **Leave-one-feature-out**: for any feature whose DA call would lead to a decision, refit clusters without that feature and re-test.
3. **Pathway-level clustering**: define clusters on a *functional* matrix (KEGG pathways, MetaCyc, EC numbers) then test *taxonomic* DA — the two matrices are genuinely different, so leakage is structural-impossible rather than empirical-bounded.

**Fix**: in this project, the NB04c resolution was to gate the within-ecotype Tier-A with a confound-free independent-evidence stream (within-substudy CD-vs-nonIBD). Species that pass *both* within-ecotype DA (possibly leakage-contaminated) AND an independent CD-vs-control contrast are the trustworthy Tier-A. In NB04c this shrank the Tier-A from 33 to 3 rock-solid candidates. The alternative (rebuild Pillar 1 on a functional feature matrix) was flagged as future work.

**Applies to**: any project using ecotype / enterotype / cluster stratification followed by within-stratum DA on the same features. Includes microbiome enterotypes, single-cell type-stratified DE (clustering on gene expression then testing gene DE within cluster is the single-cell analog of this bug), and any analysis where cluster labels are a function of the same features being tested.

### [genotype_to_phenotype_enigma] Fitness Browser KO Mapping Is a Two-Hop Join

**Problem**: There is no single `(orgId, locusId) → KO` table in `kescience_fitnessbrowser`. Mapping a fitness-browser locus to its KEGG ortholog requires two joins:

```sql
SELECT gf.orgId, gf.locusId, km.kgroup AS KO
FROM kescience_fitnessbrowser.genefitness gf
JOIN kescience_fitnessbrowser.besthitkegg bhk
     ON gf.orgId = bhk.orgId AND gf.locusId = bhk.locusId
JOIN kescience_fitnessbrowser.keggmember km
     ON bhk.keggOrg = km.keggOrg AND bhk.keggId = km.keggId
```

`besthitkegg` maps each FB locus to a KEGG organism and gene (`keggOrg`, `keggId`) via best hit; `keggmember` maps each `(keggOrg, keggId)` pair to its KEGG ortholog group (`kgroup`, which is the KO). Both joins are required — neither table alone is sufficient.

**Additional gotchas in the same schema**:

- `kescience_fitnessbrowser.kgroupdesc` has column `desc` (not `description`). Use `SELECT kgroup, desc AS description FROM ...` if you want a tidier alias.
- `kescience_fitnessbrowser.genefitness.fit` and `.t` are stored as **strings**; you must `CAST(t AS DOUBLE)` before any `ABS(...)` or comparison.
- `kescience_fitnessbrowser.experiment.expGroup` (not `Group`) is the experiment class; `SELECT Group` will fail with an `UNRESOLVED_COLUMN` error.

**Applies to**: Any project pulling fitness-browser loci and trying to aggregate at the KO level — concordance analyses, cross-organism conservation, rich-media fitness filtering.

### `data_lakehouse_ingest` Tenant Name ≠ Database Prefix

**[bakta_reannotation]** The `tenant` field in a `data_lakehouse_ingest` config is the MinIO governance group name, not the database name prefix. The library auto-prepends the tenant name to the `dataset` field to form the namespace.

The `kbase_ke_pangenome` database lives under the `kbase` tenant (not `kbase_ke`):

```python
# WRONG: tenant="kbase_ke" → user has no access, falls back to personal warehouse
# Also wrong: dataset="kbase_ke_pangenome" with tenant="kbase" → creates "kbase_kbase_ke_pangenome"

# CORRECT:
config = {
    "tenant": "kbase",           # MinIO group name (check with get_group_sql_warehouse)
    "dataset": "ke_pangenome",   # tenant + "_" + dataset = "kbase_ke_pangenome"
}
```

**How to check**: Use `get_group_sql_warehouse(tenant_name)` to verify access. An `ErrorResponse` with error 20040 means you're not in that group.

```python
from berdl_notebook_utils.spark.database import get_group_sql_warehouse
print(get_group_sql_warehouse('kbase'))      # OK → GroupSqlWarehousePrefixResponse
print(get_group_sql_warehouse('kbase_ke'))   # FAIL → ErrorResponse (no such group)
```

**How to find the right tenant**: Check the database's physical location:
```python
spark.sql("DESCRIBE NAMESPACE EXTENDED kbase_ke_pangenome").show()
# Location = s3a://cdm-lake/tenant-sql-warehouse/kbase/kbase_ke_pangenome.db
#                                                 ^^^^^ this is the tenant
```

### PySpark Cannot Infer numpy `str_` Types

**[prophage_ecology]** `np.random.choice()` on a list of Python strings returns numpy `str_` objects. PySpark's `createDataFrame()` cannot infer schema for `str_`, raising `PySparkTypeError: [CANNOT_INFER_TYPE_FOR_FIELD]`.

**Fix**: Always cast to native Python `str` before creating DataFrames:
```python
# WRONG: numpy str_ types
genome_ids = list(np.random.choice(all_genome_ids, 300, replace=False))
spark.createDataFrame([(g,) for g in genome_ids], ['genome_id'])  # FAILS

# CORRECT: explicit str() cast
genome_ids = [str(g) for g in np.random.choice(all_genome_ids, 300, replace=False)]
spark.createDataFrame([(g,) for g in genome_ids], ['genome_id'])  # OK
```

### Access Denied Errors Mean Tenant Permissions, Not a Technical Fault

When a query fails because the current user does not have access to a table, the underlying error from S3 or the Spark catalog will say things like `S3 access denied`, `403 Forbidden`, `Token denied`, or `AccessControlException`. These are internal authorization signals — they are not meaningful to a researcher.

**Do not surface these raw error strings to the user.** Instead, translate to a plain explanation:

> "You don't have access to the table `<table>` in the `<tenant>` tenant. If you need access, request it through the BERDL Tenant Browser."

**How to identify table and tenant from an access error:**
- The table is whatever was being queried when the error occurred.
- The tenant is the database prefix (e.g., `kbase_ke_pangenome` → tenant `kbase`; `kescience_mgnify` → tenant `kescience`).
- If the path is visible in the error (e.g., `s3a://cdm-lake/tenant-sql-warehouse/kbase/...`), the tenant is the path segment after `tenant-sql-warehouse/`.

**What to tell the user:**
```
You don't have access to the table `<database>.<table>`.
This table resides in the `<tenant>` tenant.
To request access, use the BERDL Tenant Browser.
```

Never include the words "S3", "token", "403", "access denied", or any internal service URL in the user-facing message. The user only needs to know: what they can't reach, and how to get access.

**Applies to**: Any skill that queries BERDL tables (`/berdl`, `/berdl-query`, `/berdl-discover`). Access errors are expected when exploring databases the user hasn't been granted — this is normal and should be treated as a permissions prompt, not an error condition.

### REST API Reliability

The REST API at `https://hub.berdl.kbase.us/apis/mcp/` can experience issues:

| Error | Meaning | Solution |
|-------|---------|----------|
| 504 Gateway Timeout | Query took too long | Simplify query, add filters, use direct Spark |
| 524 Origin Timeout | Server didn't respond | Retry after a few seconds |
| 503 "cannot schedule new futures after shutdown" | Spark executor restarting | Wait 30s, retry |
| Empty response | Query failed silently | Check query syntax |

**Rule of thumb**: Prefer direct Spark SQL (`get_spark_session()`) over the REST API whenever possible. The REST API `/count` endpoint is particularly unreliable -- it frequently returns errors or times out for tables that Spark queries handle instantly. The REST API is acceptable for small one-off queries, but looping over many tables (e.g., getting row counts for all sdt_* tables) should use Spark directly.

### Schema Introspection Timeouts

The `/schema` API endpoint frequently times out for large tables. Use `DESCRIBE database.table` via the `/query` endpoint instead for more reliable schema introspection.

### Auth Token Variable Name

The `.env` file uses `KBASE_AUTH_TOKEN` (not `KB_AUTH_TOKEN`):
```bash
# CORRECT
AUTH_TOKEN=$(grep "KBASE_AUTH_TOKEN" .env | cut -d'"' -f2)

# WRONG (legacy docs may reference this)
AUTH_TOKEN=$(grep "KB_AUTH_TOKEN" .env | cut -d'"' -f2)
```

### Token Expiration During Long Sessions

**[snipe_defense_system]** The token stored in `.env` (`KBASE_AUTH_TOKEN`) can expire during long analysis sessions. When this happens, all BERDL API calls return 401/403 errors.

**Symptom**: Previously-working queries suddenly return authentication errors mid-session.

**Solution**: On JupyterHub, a fresh token is always available at `~/.berdl_kbase_session`, synced every 30 seconds by the IPython startup script (`~/.ipython/profile_default/startup/05-token-sync.py`). Read the token from there:
```python
from pathlib import Path
token = (Path.home() / ".berdl_kbase_session").read_text().strip()
```

**Note**: The `.env` file is not automatically updated. For long-running CLI sessions outside JupyterHub, re-export the token manually.

### MinIO Upload Requires Proxy (Off-Cluster)

**[essential_metabolome]** When uploading projects to the lakehouse via `python tools/lakehouse_upload.py`, the `mc` (MinIO client) commands will timeout if proxy environment variables are not set.

**Symptom**: Upload fails with:
```
Get 'https://minio.berdl.kbase.us/cdm-lake/?location=': dial tcp 140.221.43.167:443: i/o timeout
```

**Root cause**: MinIO server (minio.berdl.kbase.us:443) is only reachable from within the BERDL cluster or through the proxy chain.

**Solution**: Set proxy environment variables before running the upload script:
```bash
export https_proxy=http://127.0.0.1:8123
export no_proxy=localhost,127.0.0.1
python3 tools/lakehouse_upload.py <project_id>
```

**Prerequisites**: SSH tunnels (ports 1337, 1338) and pproxy (port 8123) must be running. See `.claude/skills/berdl-minio/SKILL.md` for setup details.

**Note**: This applies to ALL `mc` commands when off-cluster, not just uploads. The `lakehouse_upload.py` script should be updated to set these variables automatically, but for now they must be set manually.

### String-Typed Numeric Columns

Many databases store numeric values as strings. Always cast before comparisons:
```sql
-- WRONG: String comparison
WHERE fit < -2

-- CORRECT: Cast to numeric
WHERE CAST(fit AS FLOAT) < -2
```

This affects: `kescience_fitnessbrowser` (all columns), `kbase_genomes` (coordinates, lengths), and others.

### Non-UTF-8 Bytes in SQLite TEXT Columns

**[kescience_paperblast]** When exporting a SQLite database to TSV using `sqlite3.connect()` and iterating the cursor, Python's `sqlite3` module defaults to strict UTF-8 decoding for TEXT columns. If the database contains non-UTF-8 byte sequences, this raises `OperationalError: Could not decode to UTF-8 column 'comment' with text '...'` during cursor iteration, before any data cleaning (e.g., `_clean()`) is invoked.

```python
# WRONG: Strict UTF-8 decoding will fail on non-UTF-8 bytes
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT * FROM table_with_bad_bytes")
for row in cur:  # OperationalError raised here
    process(row)

# CORRECT: Permissive UTF-8 with replacement characters
conn = sqlite3.connect(db_path)
conn.text_factory = lambda b: b.decode('utf-8', errors='replace')  # Set this first
cur = conn.cursor()
cur.execute("SELECT * FROM table_with_bad_bytes")
for row in cur:  # Succeeds; invalid bytes become U+FFFD
    process(row)
```

**Solution**: Set `text_factory` immediately after connecting, before executing any queries.

### SQL `/* ... */` Comments in CREATE TABLE Body Parsed as Column Definitions

**[kescience_paperblast]** The `parse_sql_schema()` function in the ingest pipeline uses regex to extract column definitions from `CREATE TABLE` statements. If the table body begins with an inline comment (e.g., `/* geneId is actually a fully specified protein id like YP_006960813.1 */`), the parser treats `/*` as a column name instead of skipping it. This produces an invalid schema string like `/* STRING, geneId STRING, ...`, and the ingest pipeline silently skips the entire table with no error message or quarantine entry.

```python
# WRONG: Parser treats /* as a column name
def parse_sql_schema(sql_path):
    for line in m.group(2).splitlines():
        line = line.strip().rstrip(",")
        if not line:
            continue
        tokens = re.split(r'\s+', line, maxsplit=2)
        col_name = tokens[0]  # BUG: May be "/*" if line starts with comment
        # ...

# CORRECT: Strip comments before tokenizing
def parse_sql_schema(sql_path):
    for line in m.group(2).splitlines():
        line = re.sub(r'/\*.*?\*/', '', line).strip()  # strip /* ... */ comments
        line = re.sub(r'--.*$', '', line).strip()       # strip -- comments
        if not line:
            continue
        tokens = re.split(r'\s+', line, maxsplit=2)
        col_name = re.sub(r'[`"\[\]]', '', tokens[0])
        # ...
```

**Solution**: Add comment-stripping regex at the top of the per-line loop in `parse_sql_schema` to remove both `/* ... */` and `--` style comments before splitting tokens.
### [nmdc_community_metabolic_ecology] Spark DECIMAL Columns Return `decimal.Decimal` in Pandas, Not `float`

**Problem**: Spark SQL `DECIMAL` columns (e.g., `abundance` in `nmdc_arkin.centrifuge_gold`) are returned as Python `decimal.Decimal` objects when collected via `.toPandas()`. Arithmetic with `float` values (e.g., from `AVG()` aggregates) raises `TypeError: unsupported operand type(s) for *: 'float' and 'decimal.Decimal'`.

**Solution**: `CAST(col AS DOUBLE)` in the SQL query, or `.astype(float)` on the pandas column after collection:

```python
# Option 1: Cast in SQL (preferred — avoids the type in the DataFrame entirely)
spark.sql("SELECT CAST(abundance AS DOUBLE) AS abundance FROM ...")

# Option 2: Cast after .toPandas()
df['abundance'] = df['abundance'].astype(float)
```

**Second manifestation**: `AVG(CASE WHEN condition THEN 1.0 ELSE 0.0 END)` also returns `DECIMAL` because Spark treats the literal `1.0` as `DECIMAL(2,1)`, not `DOUBLE`. Use `CAST(AVG(...) AS DOUBLE)` on aggregated columns too:

```sql
-- WRONG — frac_complete arrives as decimal.Decimal
AVG(CASE WHEN best_score >= 5 THEN 1.0 ELSE 0.0 END) AS frac_complete

-- CORRECT
CAST(AVG(CASE WHEN best_score >= 5 THEN 1.0 ELSE 0.0 END) AS DOUBLE) AS frac_complete
```

**Rule of thumb**: Any `AVG()` over integers or decimal literals in Spark SQL should be wrapped in `CAST(... AS DOUBLE)`. Add `.astype(float)` after `.toPandas()` as a defensive safety net.

Observed in `[nmdc_community_metabolic_ecology]` NB03: `centrifuge_gold.abundance` (cell-15) and `gapmind_pathways` AVG aggregates (cell-11/18).

### `SELECT DISTINCT col, COUNT(*) ...` Without GROUP BY Fails in Spark Strict Mode

Spark Connect's SQL analyzer rejects `SELECT DISTINCT` combined with an aggregate function when no `GROUP BY` is present (`MISSING_GROUP_BY`, SQLSTATE 42803). This is a strict standard-SQL interpretation that differs from some other databases (e.g., DuckDB, SQLite) which accept this syntax.

```sql
-- WRONG — AnalysisException: MISSING_GROUP_BY
SELECT DISTINCT score_category, COUNT(*) as n
FROM kbase_ke_pangenome.gapmind_pathways
LIMIT 20

-- CORRECT — GROUP BY only; DISTINCT is redundant when GROUP BY is present
SELECT score_category, COUNT(*) as n
FROM kbase_ke_pangenome.gapmind_pathways
GROUP BY score_category
ORDER BY n DESC
```

**Rule**: Never combine `DISTINCT` with aggregate functions. Use `GROUP BY` exclusively for grouped aggregations. `SELECT DISTINCT col, COUNT(*)` is always wrong — replace with `GROUP BY col`.

Observed in `[nmdc_community_metabolic_ecology]` NB03 cell-9 when checking `score_category` value distribution in `gapmind_pathways`.

---

## Pangenome (`kbase_ke_pangenome`) Pitfalls

### Taxonomy Join: Use `genome_id`, NOT `gtdb_taxonomy_id`

**[prophage_ecology]** The `genome` and `gtdb_taxonomy_r214v1` tables both have a `gtdb_taxonomy_id` column, but they store **different levels of the taxonomy string**:

- `genome.gtdb_taxonomy_id`: truncated at genus level (e.g., `d__Bacteria;p__Bacillota;...;g__Staphylococcus`)
- `gtdb_taxonomy_r214v1.gtdb_taxonomy_id`: includes species (e.g., `d__Bacteria;p__Bacillota;...;s__Staphylococcus aureus`)

Joining on `gtdb_taxonomy_id` returns **zero rows**. Always join on `genome_id`:

```sql
-- CORRECT: join on genome_id
SELECT g.gtdb_species_clade_id, t.phylum, t.family
FROM kbase_ke_pangenome.genome g
JOIN kbase_ke_pangenome.gtdb_taxonomy_r214v1 t ON g.genome_id = t.genome_id

-- WRONG: returns 0 rows because taxonomy depth differs
SELECT g.gtdb_species_clade_id, t.phylum, t.family
FROM kbase_ke_pangenome.genome g
JOIN kbase_ke_pangenome.gtdb_taxonomy_r214v1 t ON g.gtdb_taxonomy_id = t.gtdb_taxonomy_id
```

### SQL Syntax Issues

### [pgp_pangenome_ecology] `order` is a Spark SQL reserved word — must be backtick-quoted

The `gtdb_taxonomy_r214v1` table has a column named `order` (taxonomic rank). In Spark SQL, `order` is a reserved keyword and will cause a parse error if used unquoted in a SELECT or JOIN. Always backtick-quote it:

```sql
-- WRONG: AnalysisException: Reserved keyword 'order' used as identifier
SELECT t.phylum, t.class, t.order, t.family FROM kbase_ke_pangenome.gtdb_taxonomy_r214v1 t

-- CORRECT: backtick-quote the reserved word
SELECT t.phylum, t.class, t.`order`, t.family FROM kbase_ke_pangenome.gtdb_taxonomy_r214v1 t
```

The same applies to other SQL reserved words that appear as column names (e.g., `class`, `select`, `from`). When in doubt, backtick-quote any column name that looks like a keyword.

### [pgp_pangenome_ecology] GapMind `score_simplified` is binary (0.0 / 1.0), not continuous

When querying `kbase_ke_pangenome.gapmind_pathways` with `sequence_scope = 'core'`, the `score_simplified` column contains only `0.0` (pathway incomplete) or `1.0` (pathway complete) — it is not a continuous confidence score. The table is genome-level (one row per genome-pathway pair); aggregate to species level with `MAX(score_simplified) GROUP BY clade_name, pathway` before joining to species data.

```sql
-- CORRECT: aggregate to species level, binary threshold still applies
SELECT clade_name AS gtdb_species_clade_id, pathway,
       MAX(score_simplified) AS score_simplified  -- still 0.0 or 1.0 after MAX
FROM kbase_ke_pangenome.gapmind_pathways
WHERE pathway IN ('trp', 'tyr') AND metabolic_category = 'aa' AND sequence_scope = 'core'
GROUP BY clade_name, pathway
```

### The `--` in Species IDs: Non-Issue in Spark, Real Issue in REST API

Species clade IDs contain `--` (e.g., `s__Escherichia_coli--RS_GCF_000005845.2`). Behavior depends on the query method:

**Direct Spark SQL**: NOT a problem when the ID is inside a quoted string literal:
```sql
-- CORRECT via Spark: The '--' inside quotes is NOT interpreted as a comment
SELECT * FROM kbase_ke_pangenome.genome
WHERE gtdb_species_clade_id = 's__Escherichia_coli--RS_GCF_000005845.2'
```

**REST API**: IS a problem — the REST API rejects any query containing `--` regardless of quoting, treating it as a SQL comment metacharacter (returns 400 error).

**[snipe_defense_system]** Workaround for REST API: query all rows unfiltered and filter locally with pandas:
```python
# WRONG via REST API: '--' in the string causes 400 error
query = "SELECT * FROM ... WHERE species_id = 's__E_coli--RS_GCF_000005845.2'"

# CORRECT via REST API: query unfiltered, filter locally
df_all = query_berdl("SELECT * FROM kbase_ke_pangenome.gtdb_taxonomy_r214v1")
df_filtered = df_all[df_all['species_id'] == target_species]
```

### ID Format Reference

| ID Type | Format | Example |
|---------|--------|---------|
| `genome_id` | `RS_GCF_XXXXXXXXX.X` or `GB_GCA_XXXXXXXXX.X` | `RS_GCF_000005845.2` |
| `gtdb_species_clade_id` | `s__Genus_species--{representative_genome_id}` | `s__Escherichia_coli--RS_GCF_000005845.2` |
| `gene_cluster_id` | `{contig}_{number}` or `{prefix}_mmseqsCluster_{number}` | `NZ_CP095497.1_1766` |

### [metabolic_capability_dependency] `gtdb_metadata` NCBI Taxid Column Returns Boolean Strings, Not Numeric IDs

**Problem**: Attempting to join `kescience_fitnessbrowser.organism` to `kbase_ke_pangenome.gtdb_metadata` via NCBI taxonomy IDs returns zero matches. The `ncbi_taxid` (or equivalent) column in `gtdb_metadata` contains the string values `"t"` / `"f"` (boolean tokens) rather than numeric taxonomy IDs.

**Symptom**: A query like:
```python
gtdb_metadata_spark.filter(col("ncbi_taxid").isin(fb_taxids))
```
returns 0 rows even when the taxids should match, because the stored values are `"t"`/`"f"`, not integers.

**Solution**: Inspect the column values before joining:
```python
spark.sql("SELECT ncbi_taxid, COUNT(*) FROM kbase_ke_pangenome.gtdb_metadata GROUP BY ncbi_taxid LIMIT 10").show()
```
Use an alternative join key (e.g., organism name string matching or `orgId`-based lookup) or look for a different taxonomy column. In `metabolic_capability_dependency`, the fallback was to match organisms directly by `orgId` without a clade-level link.

### [nmdc_community_metabolic_ecology] `gapmind_pathways.clade_name` = `gtdb_species_clade_id` Format, NOT `GTDB_species`

**Problem**: `gapmind_pathways.clade_name` stores the full `gtdb_species_clade_id` including the representative genome accession suffix (e.g., `s__Rhizobium_phaseoli--RS_GCF_001234567.1`). It does **not** store the short `GTDB_species` name (e.g., `s__Rhizobium_phaseoli`).

**Symptom**: Joining `gapmind_pathways` on a temp view populated from `gtdb_species_clade.GTDB_species` returns 0 rows because the two formats don't match.

**Solution**: When filtering `gapmind_pathways` by species, use `gtdb_species_clade_id` values directly. The `taxon_bridge.tsv` produced by NB02 already stores `gtdb_species_clade_id` — use those directly as the clade filter without a round-trip through `gtdb_species_clade.GTDB_species`.

```python
# WRONG — uses GTDB_species format (s__Genus_species) which doesn't match clade_name
gtdb_meta = spark.sql("SELECT GTDB_species FROM kbase_ke_pangenome.gtdb_species_clade").toPandas()
clade_names_df = pd.DataFrame({'clade_name': gtdb_meta['GTDB_species'].tolist()})

# CORRECT — use gtdb_species_clade_id directly (matches clade_name in gapmind_pathways)
clade_names_df = pd.DataFrame({'clade_name': mapped_clade_ids})  # from taxon_bridge
```

### [nmdc_community_metabolic_ecology] `gapmind_pathways.metabolic_category` Values Are `'aa'` and `'carbon'`, Not `'amino_acid'`

**Problem**: Filter code using `metabolic_category == 'amino_acid'` returns 0 rows. The actual stored values are `'aa'` (amino acid pathways) and `'carbon'` (carbon source pathways).

```python
# WRONG
aa_mask = df['metabolic_category'] == 'amino_acid'  # always False

# CORRECT
aa_mask = df['metabolic_category'] == 'aa'
```

### [nmdc_community_metabolic_ecology] Spark Connect Temp Views Lost After Long-Running Cell

**Problem**: A Spark temp view registered in cell N may be silently destroyed if the Spark Connect server reconnects during cell N (e.g., triggered by an expensive 305M-row full-table scan). Subsequent cells that JOIN against the temp view return 0 rows with no error.

**Symptom**: Row count queries like `SELECT COUNT(*) FROM table JOIN temp_view ON ...` return 0 unexpectedly.

**Solution**: Re-register the temp view immediately before any cell that uses it in a JOIN. The Python variable holding the data persists in the kernel even when the Spark server reconnects.

```python
# At the top of any cell that JOINs against a temp view:
spark.createDataFrame(
    pd.DataFrame({'clade_name': mapped_clade_names})
).createOrReplaceTempView('mapped_clade_names_tmp')
```

**Prevention**: Avoid expensive full-table scans in cells between temp view registration and temp view use. Use `LIMIT` or `TABLESAMPLE` for schema verification queries rather than full `GROUP BY` counts on large tables.

### `ncbi_env` Table is EAV (Key-Value), Not Flat

**[amr_strain_variation]** The `ncbi_env` table is **not** a flat table with columns like `genome_id, isolation_source, collection_date`. It's an Entity-Attribute-Value table with columns: `accession` (BioSample ID), `attribute_name`, `content`, `display_name`, `harmonized_name`, `id`, `package_content`.

To get genome metadata you must:
1. Join `genome.ncbi_biosample_id` → `ncbi_env.accession`
2. Filter `attribute_name IN ('isolation_source', 'collection_date', 'geo_loc_name', 'host')`
3. Pivot from long to wide format

```sql
-- WRONG: these columns don't exist
SELECT genome_id, isolation_source, collection_date FROM ncbi_env

-- CORRECT: EAV query
SELECT accession, attribute_name, content
FROM kbase_ke_pangenome.ncbi_env
WHERE accession IN (...) AND attribute_name IN ('isolation_source', 'collection_date', 'host')
```

### `genome_ani` Column Names Are Not What You Expect

**[amr_strain_variation]** The `genome_ani` table uses `genome1_id`, `genome2_id`, `ANI` — **not** `genome_id_1`, `genome_id_2`, `ani`. The capitalization matters too (`ANI` not `ani`).

```sql
-- WRONG
SELECT genome_id_1, genome_id_2, ani FROM genome_ani

-- CORRECT
SELECT genome1_id, genome2_id, ANI FROM genome_ani
```

### Large Species Blow Up ANI Queries (O(n²) Problem)

**[amr_strain_variation]** ANI queries for species with >500 genomes can take 30+ minutes per species and may timeout Spark connections. *K. pneumoniae* (14,240 genomes) and *S. aureus* (14,526 genomes) generate IN clauses with 14K+ IDs that overwhelm the query planner. Cap at <=500 genomes for Mantel tests, or use subsampling.

### Per-Genome Environment Classification Gives 53% "Unknown"

**[amr_strain_variation]** Parsing `isolation_source` and `host` from `ncbi_env` at the per-genome level produces 52.7% "Unknown" labels (94,957/180,025 genomes), because most BioSample records lack structured isolation metadata. For cross-species analyses, use species-level majority-vote environment labels instead (91% coverage via keyword classification of NCBI metadata).

---

## Data Sparsity Issues

### AlphaEarth Embeddings (28.4% coverage)

Only 83,227 of 293,059 genomes have environmental embeddings.

```sql
-- Check if a species has embeddings before relying on them
SELECT COUNT(DISTINCT ae.genome_id) as n_with_embeddings,
       COUNT(DISTINCT g.genome_id) as n_total
FROM kbase_ke_pangenome.genome g
LEFT JOIN kbase_ke_pangenome.alphaearth_embeddings_all_years ae
    ON g.genome_id = ae.genome_id
WHERE g.gtdb_species_clade_id LIKE 's__Klebsiella_pneumoniae%'
```

**Why sparse?**: Embeddings require valid lat/lon coordinates, which are often missing in NCBI metadata, especially for clinical isolates.

### NCBI Environment Metadata (EAV format)

The `ncbi_env` table uses Entity-Attribute-Value format - multiple rows per sample.

```sql
-- Get isolation source for a genome
SELECT content
FROM kbase_ke_pangenome.ncbi_env
WHERE accession = 'SAMN12345678'
  AND harmonized_name = 'isolation_source'

-- Pivot to get multiple attributes
SELECT accession,
       MAX(CASE WHEN harmonized_name = 'isolation_source' THEN content END) as isolation_source,
       MAX(CASE WHEN harmonized_name = 'geo_loc_name' THEN content END) as location
FROM kbase_ke_pangenome.ncbi_env
WHERE accession IN ('SAMN12345678', 'SAMN87654321')
GROUP BY accession
```

### Geographic Coordinates

`ncbi_lat_lon` in `gtdb_metadata` is often:
- NULL (most common)
- Malformed strings ("missing", "not collected")
- Low precision ("37.0 N 122.0 W")

---

## Foreign Key Gotchas

### Orphan Pangenomes (12 species)

12 pangenome records reference species clades not in `gtdb_species_clade`:

```
s__Portiera_aleyrodidarum--RS_GCF_000300075.1
s__Profftella_armatura--RS_GCF_000441555.1
s__Nanosynbacter_sp022828325--RS_GCF_022828325.1
... (mostly symbionts and single-genome species)
```

These are valid pangenomes but filtered from species metadata. Handle with LEFT JOIN.

### Annotation Table Join Key

`eggnog_mapper_annotations.query_name` joins to `gene_cluster.gene_cluster_id`, NOT to `gene.gene_id`:

```sql
-- CORRECT: Join on gene_cluster_id
SELECT gc.gene_cluster_id, e.COG_category, e.Description
FROM kbase_ke_pangenome.gene_cluster gc
LEFT JOIN kbase_ke_pangenome.eggnog_mapper_annotations e
    ON gc.gene_cluster_id = e.query_name
WHERE gc.gtdb_species_clade_id LIKE 's__Mycobacterium%'

-- WRONG: gene_id won't match
SELECT * FROM kbase_ke_pangenome.eggnog_mapper_annotations
WHERE query_name = 'some_gene_id'  -- This won't find anything
```

### Gene Clusters are Species-Specific

Gene cluster IDs are only meaningful within a species. You cannot compare cluster IDs across species:

```sql
-- This comparison is MEANINGLESS:
-- Cluster "X_123" in E. coli is unrelated to "X_123" in Salmonella

-- To compare gene content across species, use:
-- 1. COG categories from eggnog_mapper_annotations
-- 2. KEGG orthologs (KEGG_ko column)
-- 3. PFAM domains
```

### [snipe_defense_system] eggNOG `PFAMs` Column Stores Domain Names, Not Accessions

**Problem**: The `eggnog_mapper_annotations.PFAMs` column stores Pfam domain **names** (e.g., `DUF4041`, `GIY-YIG`), not Pfam **accession IDs** (e.g., `PF13250`, `PF01541`). Searching by accession returns 0 results.

**Symptom**: `WHERE PFAMs LIKE '%PF13250%'` returns 0 rows; `WHERE PFAMs LIKE '%DUF4041%'` returns 2,962.

```sql
-- WRONG: accession IDs are not stored in this column
WHERE PFAMs LIKE '%PF13250%'   -- returns 0

-- CORRECT: search by domain family name
WHERE PFAMs LIKE '%DUF4041%'   -- returns 2,962
```

**Note**: The column contains comma-separated lists of domain names, so always use `LIKE` with `%` wildcards, not exact equality.

### [snipe_defense_system] eggNOG Query Returns Fewer Rows Than gene_cluster JOIN

**Problem**: Querying `eggnog_mapper_annotations` for a domain returns N rows (e.g., 2,962 DUF4041 annotations), but joining to `gene_cluster` produces more rows (e.g., 4,572). This is because gene clusters are species-specific — the same eggNOG annotation (`query_name`) can map to gene_cluster entries in multiple species pangenomes.

**Rule**: The final row count after JOIN is the correct number of *species-level gene clusters*. The eggNOG count is the number of *unique annotation records*. Both are valid counts for different purposes — document which one you're reporting.

### [snipe_defense_system] Pfam Accession Lookup Errors: Always Verify Against InterPro/UniProt

**Problem**: Pfam domain names (e.g., "DUF4041", "GIY-YIG") can map to wrong accessions if looked up by name alone. PF13250 and PF13291 are numerically close but completely unrelated families. PF01541 (canonical GIY-YIG) and PF13455 (Mug113) are in the same clan but are distinct families.

**Symptom**: Zero co-occurrence hits for domains that should co-occur (e.g., DUF4041 + GIY-YIG in SNIPE proteins), or unexpected functional annotations for your domain hits.

**Fix**: Always verify Pfam accessions against a known protein in InterPro or UniProt. For SNIPE:
- DUF4041 = **PF13250** (IPR025280), NOT PF13291 (ACT_4)
- SNIPE nuclease = **PF13455** (Mug113, GIY-YIG clan CL0418), NOT PF01541 (canonical GIY-YIG)

```python
# Verify via InterPro API
import requests
r = requests.get("https://www.ebi.ac.uk/interpro/api/entry/pfam/PF13250/")
# Check the name matches your expected domain
```

---

## PhageFoundry (`phagefoundry_*`) Pitfalls

### [snipe_defense_system] PhageFoundry Has Two Types of Databases

PhageFoundry data is split across two different database types in BERDL:

| Type | Database pattern | Contents | Tables |
|------|-----------------|----------|--------|
| GenomeDepot browsers | `phagefoundry_{species}_genome_browser_genomedepot` | Genome annotations only (eggNOG, COG, Pfam) | `browser_*` (10+ tables each) |
| Strain modelling | `phagefoundry_strain_modelling` | Experimental phage-host interaction data + ML model | 18 tables (organism, interaction, feature, etc.) |

**Pitfall**: It's easy to explore only the GenomeDepot databases and conclude PhageFoundry has "no experimental data." The strain modelling database is separate and contains the actual experimental results (Gaborieau et al. 2024, *Nature Microbiology*).

### [snipe_defense_system] Strain Modelling Gene Table Has No Functional Annotations

The `strainmodelling_gene` table has 933K genes but only `locus_tag` and `protein_seq` columns — no `gene_name`, `product`, or functional annotation fields. You cannot search for genes by name.

**Workaround**: Use the `strainmodelling_feature` and `strainmodelling_protein_family` tables instead, which link gene clusters to ML model features with SHAP importance scores.

### [snipe_defense_system] Spark Cold-Start: Count Works But Query Returns Empty

For rarely-accessed BERDL databases (including `phagefoundry_strain_modelling`), the Spark cluster needs warm-up time. The `/count` endpoint often returns correct results while `/query` and `/sample` endpoints return 0 rows or empty results.

**Workaround**: Use `/count` to verify data exists, then retry `/query` with exponential backoff. May take several minutes for the Spark cluster to warm up for cold databases.

### [snipe_defense_system] GenomeDepot COG Column Name Mismatch

The `browser_protein_cog_classes` table uses `cog_class_id` (not `cogclass_id`). Always check the schema with `DESCRIBE` before filtering:
```sql
-- WRONG
WHERE cogclass_id = 'V'

-- CORRECT
WHERE cog_class_id = 'V'
```

---

## Data Interpretation Issues

### Core/Auxiliary/Singleton Definitions

In `gene_cluster` table:
- `is_core` = 1: Present in ≥95% of genomes
- `is_auxiliary` = 1: Present in <95% and >1 genome
- `is_singleton` = 1: Present in exactly 1 genome

**These are mutually exclusive** (only one flag is 1 per row).

**Important**: These are stored as integers (0/1), not booleans:
```sql
-- CORRECT
WHERE is_core = 1

-- May fail depending on SQL dialect
WHERE is_core = true
```

### Pangenome Table Count Interpretation

In `pangenome` table:
- `no_core` + `no_aux_genome` = `no_gene_clusters` (total clusters)
- `no_singleton_gene_clusters` ⊂ `no_aux_genome` (singletons are a subset of auxiliary)

```sql
-- Verify: core + aux = total
SELECT
    no_core + no_aux_genome as computed_total,
    no_gene_clusters as reported_total,
    no_singleton_gene_clusters as singletons,
    no_aux_genome as auxiliary
FROM kbase_ke_pangenome.pangenome
LIMIT 5
```

---

## JupyterHub Environment Issues

### `get_spark_session()` — Use the Right Import for Your Environment

There are three environments with different import patterns. Using the wrong one causes `ImportError`:

| Environment | Import | Why |
|---|---|---|
| **BERDL JupyterHub notebooks** | `spark = get_spark_session()` (no import) | Injected by `/configs/ipython_startup/00-notebookutils.py` |
| **BERDL JupyterHub CLI/scripts** | `from berdl_notebook_utils.setup_spark_session import get_spark_session` | Same module, explicit import. **[fitness_modules]** discovered this works from regular Python scripts, not just notebooks. |
| **Local machine** | `from get_spark_session import get_spark_session` | Uses `scripts/get_spark_session.py`, requires `.venv-berdl` + proxy chain |

**Common mistakes**:
- Using `from get_spark_session import get_spark_session` on the BERDL cluster → `ImportError` (that module is `scripts/get_spark_session.py`, only on local machines)
- Using `from berdl_notebook_utils.setup_spark_session import get_spark_session` locally → `ImportError` (that package is only on the BERDL cluster)
- Using the bare `get_spark_session()` (no import) in a CLI script on JupyterHub → `NameError` (auto-import only applies to notebook kernels)

### Don't Kill Java Processes

**[conservation_vs_fitness]** The Spark Connect service runs as a Java process on port 15002. Killing Java processes (e.g., when cleaning up stale notebook processes) will take down Spark Connect, and `get_spark_session()` will fail with `RETRIES_EXCEEDED` / `Connection refused`.

**Recovery**: Log out of JupyterHub and start a new session. Then run `get_spark_session()` from a notebook to restart the Spark Connect daemon. You cannot restart it from the CLI.

### Spark Connect Sidecar Startup Race (Off-Cluster Access)

**Context**: Off-cluster access via `scripts/get_spark_session.py` + proxy chain.

**Problem**: After restarting the JupyterHub kernel, the Python kernel becomes ready almost immediately, but the Spark Connect gRPC sidecar (the Java process on port 15002) takes an additional 20–60 seconds to start and register with the BERDL gateway. During this window, any connection attempt from outside the cluster fails with:

```
SparkConnectGrpcException: FAILED_PRECONDITION
  "Spark Connect server at jupyter-<username>.jupyterhub-prod.svc.cluster.local:15002
   is not reachable. Please ensure you have logged in to BERDL JupyterHub and your
   notebook's Spark Connect service is running."
```

This is misleading — the session *is* running, the sidecar just hasn't finished starting. The error looks identical to a "not logged in" error, so it's easy to mistake for an authentication problem and keep resetting the kernel unnecessarily.

**Solution**: After restarting the kernel, wait ~30–60 seconds before attempting off-cluster connections, or poll with retries:

```bash
source .venv-berdl/bin/activate
for i in $(seq 1 10); do
    echo "Attempt $i at $(date +%H:%M:%S)..."
    result=$(python scripts/run_sql.py --berdl-proxy --query "SELECT 1 AS ok" 2>&1)
    if echo "$result" | grep -q '"ok"'; then
        echo "Connected!"
        break
    fi
    echo "  Not ready — retrying in 20s"
    sleep 20
done
```

**Do not** reset the kernel repeatedly — this just restarts the race. One reset is enough; then wait and retry from the local side.

### Running Notebooks from CLI

Notebooks can be executed headlessly via `jupyter nbconvert`:

```bash
jupyter nbconvert --to notebook --execute notebook.ipynb \
  --output notebook_executed.ipynb \
  --ExecutePreprocessor.timeout=7200
```

The kernel spawned by nbconvert has `get_spark_session()` available. However, long-running notebooks may time out — set `--ExecutePreprocessor.timeout` appropriately.

**Tip**: For long pipelines, design notebooks with checkpointing (save intermediate files, skip steps that already have output). This allows re-running after interruptions without repeating completed work.

### `jupyter nbconvert --inplace` Silently Drops Cell Outputs

**[genome_depot_enigma]** On this JupyterHub, `jupyter nbconvert --to notebook --execute --inplace ...` can exit with code 0 but leave the notebook file on disk with **zero cell outputs** — the kernel executes cells successfully, but the outputs are never written back. This is particularly problematic when the pre-flight cell raises an intentional `RuntimeError` (the `CONFIRMED = False` pattern used by `/berdl-ingest`), because the plan output that was supposed to be inspected is lost.

```bash
# Looks correct but silently strips outputs:
jupyter nbconvert --to notebook --execute --inplace notebook.ipynb
# Even with --allow-errors, outputs may still not be persisted.

# Workarounds (any of these):
# 1. Write to a new file instead of --inplace:
jupyter nbconvert --to notebook --execute notebook.ipynb --output notebook_executed.ipynb

# 2. Run the equivalent code as a plain Python script and log stdout:
python3 -u run_ingest.py > ingest.log 2>&1
```

**Solution**: Don't rely on `--inplace` to capture outputs. Either write to a separate file via `--output`, or for long-running production ingests, run the equivalent logic as a standalone Python script so you get streaming stdout/stderr to a log file.

### `/berdl-ingest` Skill Assumes Off-Cluster — Adapt for On-Cluster Use

**[genome_depot_enigma]** The `/berdl-ingest` skill's `initialize()` (in `scripts/ingest_lib.py`) requires SSH tunnels on ports 1337/1338, pproxy on 8123, and `berdl-remote login`/`spawn` — all specific to running from a laptop. Running it from inside BERDL JupyterHub fails at Step 0 (`berdl-remote status` → "Configuration file not found"), even though Spark Connect is directly reachable at `sc://jupyter-<user>.jupyterhub-prod:15002`.

**On-cluster pattern**: Build your own Spark + MinIO clients and reuse the rest of `ingest_lib` unchanged. The library's helpers (`detect_source_files`, `parse_sql_schema`, `build_table_stats`, `upload_files`, `run_ingest`, `verify_ingest`) are infrastructure-agnostic — only `initialize()` is off-cluster-only.

```python
import os, sys
sys.path.insert(0, "/home/aparkin/BERIL-research-observatory/scripts")
import ingest_lib
from ingest_lib import (detect_source_files, parse_sql_schema, build_table_stats,
                       upload_files, run_ingest, verify_ingest)
from pyspark.sql import SparkSession
from minio import Minio

# Direct Spark Connect (on-cluster URL, no tunnels/pproxy)
token = os.environ["KBASE_AUTH_TOKEN"]
spark_url = f"sc://jupyter-{os.environ['USER']}.jupyterhub-prod:15002/;use_ssl=false;x-kbase-token={token}"
spark = SparkSession.builder.remote(spark_url).getOrCreate()

# Direct MinIO (env vars are pre-set on-cluster)
endpoint = os.environ["MINIO_ENDPOINT_URL"].replace("https://","").replace("http://","")
minio_client = Minio(endpoint,
    access_key=os.environ["MINIO_ACCESS_KEY"],
    secret_key=os.environ["MINIO_SECRET_KEY"],
    secure=os.environ.get("MINIO_SECURE","true").lower()=="true")

# Register with the berdl_notebook_utils stubs that ingest_lib sets up on import
sys.modules["berdl_notebook_utils.setup_spark_session"].get_spark_session = lambda **kw: spark
sys.modules["berdl_notebook_utils.clients"].get_minio_client = lambda **kw: minio_client

# Then use the rest of ingest_lib helpers exactly as off-cluster.
```

**Solution**: Skip the skill's Step 0/0b entirely when on-cluster. Use the pattern above in place of `ingest_lib.initialize()`. The rest of the workflow — schema parsing, plan, upload, ingest, verify — works unchanged.

### MySQL `mysqldump` Exports Aren't Standard TSV/CSV

**[genome_depot_enigma]** A MySQL dump produced by `mysqldump` (especially one packaged with per-table `.sql` + `.txt` file pairs) looks like CSV but has three traps that break `ingest_lib.parse_sql_schema` + standard CSV readers:

1. **No header row** on data files — column names come from the `CREATE TABLE`, not the first line.
2. **`\N` literal** for NULL — not empty string, not `NULL`.
3. **MySQL-specific DDL trailer** — `) ENGINE=InnoDB AUTO_INCREMENT=... DEFAULT CHARSET=utf8mb3;` after the column list. `ingest_lib.parse_sql_schema`'s regex `\)\s*;` requires the closing paren be followed only by whitespace and a semicolon — it won't match.

**Solution**: Preprocess before calling the ingest pipeline:
- **Schema**: strip the `ENGINE=...;` trailer, keep just `CREATE TABLE name (cols);`. Concatenate all per-table `.sql` into one `schema.sql`.
- **Data**: stream each `.txt` through `csv.reader` (comma-delimited, `doublequote=True`), replace `\N` → empty string, write as TSV with prepended header derived from the `CREATE TABLE`.

See `~/data/genome_depot_enigma/preprocess.py` for a reference implementation (handles 13 GB / 32 tables in ~5 minutes).

---

## Pandas-Specific Issues

### [gene_function_ecological_agora] Spark-Connect driver result-size cap (1 GB serialized) — use MinIO staging for >200K-element joins

**Problem**: When joining 1B-row tables (e.g., `kbase_genomes.feature` × `contig_x_feature` × `pangenome.gene_genecluster_junction`) filtered to >200K elements via broadcast, calling `.toPandas()` on the Spark Connect result hits `spark.driver.maxResultSize = 1024 MB` and throws `Total size of serialized results bigger than spark.driver.maxResultSize`. The cap can NOT be raised via `SET spark.driver.maxResultSize` at runtime — that property is read-only after session start.

**Workaround**: write the Spark result to MinIO via `df.coalesce(N).write.mode("overwrite").parquet("s3a://cdm-lake/...")`, then read it back with `spark.read.parquet(path).toPandas()`. The read-back goes through Spark Connect's parquet streaming path which doesn't hit the result-size cap. Alternative: `pyarrow.parquet.read_table(path)` directly via s3fs if pyarrow is configured.

**Scale where this matters**: filtered cxf table at 218K Bacteroidota contigs × ~140 features/contig = 30M+ rows × ~50 bytes serialized ≈ 1.5 GB. Standard pattern in any project doing genome-context cross-walks at >200 species.

**Encountered in**: P4-D2 NB26b/c (per-cluster MGE-machinery atlas-wide), NB26h/k (PUL/mycolic gene-neighborhood at sampled scale).

### [gene_function_ecological_agora] Pandas spatial-merge OOM at ~10M+ rows — batch processing or full-Spark required

**Problem**: After Spark filters down to focal features, the in-pandas spatial-range merge (e.g., focal_features × contig_features on contig_id, then filter by `±NEIGHBOR_BP`) creates a Cartesian-product-then-filter pattern. For 80K focal × 21K contigs × ~105 features/contig avg, the merged DataFrame is ~24M rows × 9 columns ≈ 9 GB working set, OOMing on a 16 GB driver.

**Workarounds** (in order of effort):
1. Process focal features in batches of ~10K, merge per-batch, accumulate aggregate result
2. Do the spatial-range filter in Spark (push the BETWEEN clause through), only collect the per-feature aggregate to driver
3. Reduce scope (sample down focal-species set; restrict to canonical-marker KOs only)

**Encountered in**: P4-D2 NB26h Bacteroidota PUL gene-neighborhood (723K focal × 210K contigs blew it; sampled to 309 species still OOM'd at 80K × 21K). PSII at 27K focal × 16K contigs × 16M-row merge fit; PUL/mycolic at full scale did not.

### [gene_function_ecological_agora] `spark.sql.autoBroadcastJoinThreshold = -1` is HARMFUL, not protective — trust the optimizer

**Problem**: A defensive setting carried over from prior projects (`spark.sql.autoBroadcastJoinThreshold = -1` to "force shuffle joins") caused an NB10 KO atlas job to hang for 17+ minutes on a 13.7M × 18K join. The job was waiting for shuffle that never materialized; the small-side table (18,989 species_tax) is well below the default 10MB broadcast threshold and would have been auto-broadcast had the setting been left at default.

**Workaround**: REMOVE the autoBroadcast disable. Trust the optimizer for small-table joins. Use explicit `F.broadcast(small_df)` hints when the optimizer doesn't auto-detect.

**Generalizable rule**: copy-pasted Spark configuration "defensive defaults" from prior projects can be actively counterproductive. Audit configuration before assuming a working setting.

### [gene_function_ecological_agora] JupyterHub kernel idle-timeout (~17–25 min) silently kills long-running notebooks — convert to .py + nohup + checkpoints

**Problem**: BERDL JupyterHub idle-times out kernels that haven't received user activity for ~17–25 minutes. Long-running notebook cells (Spark jobs that take 30+ min, like NB10 KO atlas construction or NB10b M22 attribution at 17M events) get silently killed mid-execution. The kernel disappears with no error message.

**Workaround pattern**:
1. Convert long-running notebook to standalone .py script (`jupytext --to py 10_p2_ko_atlas.ipynb`)
2. Run via `nohup python3 -u <script>.py > /tmp/<name>.log 2>&1 &` from a terminal (not JupyterHub kernel)
3. Write intermediate parquets at each stage so partial results are recoverable from disk
4. Provide `_finalize.py` recovery scripts that load intermediates and complete from where the killed run stopped

**Encountered in**: NB10 (atlas construction; required `10_finalize.py` + `10_finalize2.py` recovery), NB10b (M22 attribution; required `10b_finalize.py`), NB26b/c (P4-D2 atlas-wide MGE), NB28e (leaf_consistency build).

### [gene_function_ecological_agora] Pandas `iterrows()` over 6M+ rows is dramatically slower than vectorized merge

**Problem**: Stage 6 of the gene-neighborhood pipeline (NB26e) used `for _, row in focal_features.iterrows()` with per-row groupby lookup over 27K focal features × 218K contigs. The loop ran 30+ minutes without completing.

**Workaround**: vectorized merge via `pd.merge(focal_features, contig_features, on="contig_id")` followed by boolean filter on the merged frame. Same operation completed in ~10 seconds.

**Generalizable rule**: never use iterrows() for >10K rows; vectorize via merge + boolean filter or numpy array operations. The 1000× speedup is consistent across pandas use cases.

### [gene_function_ecological_agora] Algebraic identity replaces explode() when explode would be O(N²) — `R_FK − self_recipient`

**Problem**: NB28b tree-based donor inference (M26) computes per-(donor genus × KO) "donor candidate event" count by exploding 6.3M gain events × ~20 candidate-donor genera per event = 126M-row exploded DataFrame, ~19 GB. OOM.

**Workaround** (algebraic identity): for each (family F × KO K) with R_FK total recipient events, every genus G in F that has K present is a candidate donor for (R_FK − recipient_events_for_G). Computable as a single join + subtraction, no explode. Stage 2b ran in 142s instead of OOMing.

**Generalizable rule**: when an explode produces O(N×M) rows where M is bounded but large (e.g., genera-with-KO per family-KO), look for an algebraic identity that produces the same aggregate without enumerating all combinations. Sum-over-bins reformulations are typically what's needed.

### Unnecessary `.toPandas()` Calls

**`.toPandas()` pulls all data from the Spark cluster to the driver node.** This is slow for large results and can cause out-of-memory errors. Do filtering, joins, and aggregations in Spark first.

```python
# BAD: Pull 132M rows to driver, then filter locally
df = spark.sql("SELECT * FROM kbase_ke_pangenome.gene_cluster").toPandas()
core = df[df['is_core'] == 1]

# GOOD: Keep as Spark DataFrame, filter in Spark
df = spark.sql("""
    SELECT * FROM kbase_ke_pangenome.gene_cluster
    WHERE is_core = 1
    AND gtdb_species_clade_id = 's__Escherichia_coli--RS_GCF_000005845.2'
""")

# Only convert to pandas for small, final results (plotting, export)
summary = df.groupBy("gtdb_species_clade_id").count().toPandas()
```

**Rule of thumb**: Use PySpark DataFrame operations for all intermediate steps. Only call `.toPandas()` when you need the data locally (matplotlib plots, CSV export, or results that are a few thousand rows).

See [performance.md](performance.md) for detailed PySpark-first patterns.

### NaN Handling When Mapping to Dictionaries

**[cog_analysis]** When mapping COG categories to descriptions using a dictionary, composite categories (e.g., "LV", "EGP") will return NaN if not in the dictionary. String operations on NaN values will fail:

```python
# Dictionary only has single-letter COGs
COG_DESCRIPTIONS = {
    'J': 'Translation, ribosomal structure',
    'L': 'Replication, recombination, repair',
    # ... but no "LV", "EGP", etc.
}

# This will introduce NaN values for composite COGs
df['description'] = df['COG_category'].map(COG_DESCRIPTIONS)

# BAD: This will fail with TypeError on NaN values
labels = [f"{row['COG_category']}: {row['description'][:40]}" for _, row in df.iterrows()]

# GOOD: Check for NaN before string operations
labels = []
for _, row in df.iterrows():
    desc = row['description'][:40] if pd.notna(row['description']) else 'Unknown'
    labels.append(f"{row['COG_category']}: {desc}")
```

**Solution**: Always use `pd.notna()` or `pd.isna()` before string slicing or other operations on potentially-NaN columns.

### Type Conversion from Spark .toPandas()

Numeric columns from Spark can come through as strings when using `.toPandas()`:

```python
df = spark.sql("SELECT no_genomes, no_core FROM pangenome").toPandas()

# BAD: Might fail with type error if columns are strings
filtered = df[df['no_genomes'] <= 500]  # TypeError: '<=' not supported for str

# GOOD: Explicitly convert to numeric
numeric_cols = ['no_genomes', 'no_core', 'no_aux_genome']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')
```

---

## Pangenome: Missing Tables

These tables were previously missing but some have been added:

| Table | Mentioned Purpose | Status (2026-02-11) |
|-------|-------------------|--------|
| `phylogenetic_tree` | Species trees from core genes | **NOW AVAILABLE** |
| `phylogenetic_tree_distance_pairs` | Pairwise phylo distances | **NOW AVAILABLE** |
| `pangenome_build_protocol` | Build parameters | NOT FOUND (but `protocol_id` column exists) |
| `genomad_mobile_elements` | Plasmid/virus annotations | NOT FOUND |
| `IMG_env` | IMG environment metadata | NOT FOUND |

---

## Pangenome: API vs Direct Spark

Use direct `spark.sql()` on the cluster when:
- Query involves >1M rows
- JOINs across large tables
- Aggregations on billion-row tables
- REST API keeps timing out

### [cog_analysis] Multi-table joins can be slow for large species

**Problem**: Joining gene → gene_genecluster_junction → gene_cluster → eggnog_mapper_annotations can be slow for species with >500 genomes.

**Solutions**:
1. **Use direct Spark**: Run on JupyterHub with `spark.sql()` instead of REST API
2. **Separate queries per gene class**: Break into smaller queries
3. **Select smaller species**: Use species with 100-300 genomes for faster queries

**Performance tip**: Always use exact equality (`WHERE id = 'value'`) rather than `LIKE` patterns for best performance.

### [cofitness_coinheritance] Phylo distance genome IDs lack GTDB prefix

**Problem**: The `phylogenetic_tree_distance_pairs` table uses bare NCBI accessions (`GCA_001038305.1`, `GCF_000005845.2`) while all other pangenome tables (`genome`, `gene`, `gene_genecluster_junction`) use GTDB-prefixed IDs (`GB_GCA_001038305.1`, `RS_GCF_000005845.2`). Joining phylo distances with presence matrices produces zero matches because no IDs overlap.

**Solution**: Strip the `GB_` or `RS_` prefix (first 3 characters) from GTDB genome IDs before joining with phylo distance data:
```python
def strip_gtdb_prefix(genome_id):
    if genome_id.startswith(('GB_', 'RS_')):
        return genome_id[3:]
    return genome_id
```

After stripping, overlap is 100% for all tested species (399/399 for Koxy, 287/287 for Btheta, etc.).

---

### [cofitness_coinheritance] Billion-row table joins require BROADCAST hints

**Problem**: Joining `gene_genecluster_junction` (~1B rows) with `gene` (~1B rows) to build genome × cluster presence matrices takes 3-5 minutes per species, even on Spark. Neither table is partitioned by `gene_cluster_id` or `genome_id`, so every query requires a full table scan.

**Profiling results** (Smeli, 241 genomes, 6K target clusters):
- Without BROADCAST: ~300s per organism
- With `/*+ BROADCAST(tc), BROADCAST(tg) */` on filter tables: ~274s (8% improvement)
- Two-stage approach (filter junction first, then lookup genome_ids): ~310s (no improvement)
- `.toPandas()` on 1-2M result rows: <2s (not the bottleneck)

**Solutions**:
1. **Use BROADCAST hints**: Register target cluster IDs and genome IDs as temp views, then use `/*+ BROADCAST(tc), BROADCAST(tg) */` in the query
2. **Cache aggressively**: Once extracted, save matrices as TSV and skip on re-run
3. **Set long timeouts**: `ExecutePreprocessor.timeout=3600` for `nbconvert --execute`
4. **Budget ~5 min per organism**: 11 organisms ≈ 55 min total for matrix extraction

**Root cause**: The `gene` and `gene_genecluster_junction` tables are stored as unpartitioned parquet. Adding partitioning by `genome_id` (for `gene`) or `gene_cluster_id` (for junction) would dramatically reduce scan time, but this requires rebuilding the lakehouse tables.

---

## Fitness Browser (`kescience_fitnessbrowser`) Pitfalls

### All Columns Are Strings

Every column in the fitness browser is stored as a string. Always cast before numeric comparisons:

```sql
-- WRONG
WHERE fit < -2

-- CORRECT
WHERE CAST(fit AS FLOAT) < -2
```

### orgId is Case-Sensitive

Use exact case: `WHERE orgId = 'Keio'` (not `'keio'`).

### genefitness Table is Large (27M rows)

Always filter by `orgId` at minimum.

### Per-Organism Convenience Tables

**[fitness_modules]** The `fitbyexp_*` tables are **long format** (columns: `expName, locusId, fit, t`), NOT pre-pivoted wide tables as the schema docs suggest. They're equivalent to a per-organism slice of `genefitness`. Use `genefitness` directly with an `orgId` filter instead.

### KEGG Annotation Join Path

**[fitness_modules]** `keggmember` does NOT have `orgId` or `locusId` columns. It has `keggOrg, keggId, kgroup`. To link genes to KEGG groups:

```sql
-- CORRECT: Join through besthitkegg
SELECT bk.locusId, km.kgroup, kd.desc
FROM kescience_fitnessbrowser.besthitkegg bk
JOIN kescience_fitnessbrowser.keggmember km
    ON bk.keggOrg = km.keggOrg AND bk.keggId = km.keggId
LEFT JOIN kescience_fitnessbrowser.kgroupdesc kd ON km.kgroup = kd.kgroup
WHERE bk.orgId = 'DvH'

-- WRONG: keggmember has no orgId column
SELECT * FROM kescience_fitnessbrowser.keggmember WHERE orgId = 'DvH'
```

Also: `kgroupec` uses column `ecnum` (not `ec`).

### Experiment Table Is Named `experiment`, Not `exps`

**[pathway_capability_dependency]** The experiments table in `kescience_fitnessbrowser` is called `experiment` (not `exps`). Column names: `expName` (not `name`), `expGroup` (not `Group`), `condition_1` (not `Condition_1`). The `expGroup` column provides clean condition categories ("carbon source", "nitrogen source", "stress", "pH", "temperature", etc.) — use this for condition-type classification instead of pattern matching on `condition_1`.

### seedannotationtoroles Joins on `seed_desc`, Not `orgId`/`locusId`

**[pathway_capability_dependency]** The `seedannotationtoroles` table has columns `seed_desc` and `seedrole` only — no `orgId` or `locusId`. Join chain: `seedannotation` (orgId, locusId, seed_desc) → `seedannotationtoroles` (seed_desc → seedrole) → `seedroles` (seedrole → toplevel, category, subsystem). The `seedroles` table columns are `toplevel`, `category`, `subsystem`, `seedrole` — not `seed_role`, `seed_subsystem`, or `seedroleId`.

### seedclass Has No Subsystem Hierarchy

**[fitness_modules]** `seedclass` has columns `orgId, locusId, type, num` — it stores EC numbers, NOT SEED subsystem categories. Use `seedannotation` (columns: `orgId, locusId, seed_desc`) for functional descriptions.

### ICA Component Ratio Affects Performance

**[fitness_modules]** When running FastICA on fitness matrices, keep `n_components` ≤ 40% of `n_experiments`. Higher ratios cause frequent convergence failures, and each failed run hits `max_iter` (very slow). For an organism with 150 experiments, use at most 60 components.

### Cosine Distance Floating-Point Issue

**[fitness_modules]** When computing pairwise cosine distance (`1 - |cosine_similarity|`) for DBSCAN clustering, tiny negative values can appear due to floating-point precision. DBSCAN with `metric="precomputed"` rejects negative distances. Fix: `np.clip(cos_dist, 0, 1, out=cos_dist)` before clustering.

### Ortholog Scope Must Match Analysis Scope

**[fitness_modules]** When building cross-organism ortholog groups, always extract BBH pairs for ALL organisms in the analysis — not just a pilot subset. Using 5-organism orthologs for a 32-organism analysis produced 6x fewer module families and missed all families spanning 5+ organisms. The ortholog graph gains transitive connections from each new organism, so partial extraction severely underestimates cross-organism conservation.

### D'Agostino K² is Wrong for ICA Membership Thresholding

**[fitness_modules]** ICA weight distributions are intentionally non-Gaussian (heavy-tailed), so the D'Agostino K² normality test always rejects normality, causing it to use a permissive z-threshold (2.5) that lets 100-280 genes into each module. Use absolute weight thresholds instead (|Pearson r| ≥ 0.3 with module profile, max 50 genes). This is the single most impactful parameter in the pipeline.

### Enrichment min_annotated Must Match Annotation Granularity

**[fitness_modules]** Using `min_annotated=3` with KEGG KOs (~1.2 genes per KO) results in only 8% of modules getting any enrichment — almost no KEGG term has 3+ genes in a single 5-50 gene module. Lower to `min_annotated=2` (still valid with FDR correction) and include PFam domains (814 terms with 2+ genes) alongside TIGRFam (88 terms). This increases module annotation from 8% to 80%.

### FB Locus Tag Mismatch Between Gene Table and Aaseqs Download

**[conservation_vs_fitness]** The FB protein sequences at `fit.genomics.lbl.gov/cgi_data/aaseqs` use RefSeq-style locus tags for some organisms (e.g., `ABZR86_RS00005` for Dyella79), while the FB `gene` table uses the original annotation locus tags (`N515DRAFT_0001`). If you build DIAMOND databases from aaseqs and then try to join the hit locusIds back to the gene table, the join will silently produce zero matches. Check locusId overlap between datasets before analysis. Affected: Dyella79 (0% overlap). Other organisms had >94% overlap.

### FB Gene Table Has No Essentiality Flag

**[conservation_vs_fitness]** After checking all 45 tables in `kescience_fitnessbrowser`, there is no explicit essentiality column, insertion count, or "has fitness data" flag. The `gene.type` column encodes feature type (1=CDS, 5=pseudo, 7=rRNA, 2=tRNA), not essentiality. To identify putative essential genes, compare the `gene` table (type='1') against `genefitness` — genes absent from genefitness had no viable transposon mutants. This is an upper bound on true essentiality.

### Spark LIMIT/OFFSET Pagination Is Slow

**[conservation_vs_fitness]** Using `LIMIT N OFFSET M` for pagination in Spark queries causes Spark to re-scan all rows up to the offset on each query. For extracting cluster rep FASTAs across 154 clades, paginated queries (5000 rows per batch) were orders of magnitude slower than single queries per clade. Since `gene_cluster` is partitioned by `gtdb_species_clade_id`, a single `WHERE gtdb_species_clade_id = 'X'` query per clade is fast. Only paginate when the result set would exceed memory.

### % Core Denominator Inconsistency Across Projects

**[conservation_fitness_synthesis]** When computing "% core," the denominator matters: using all genes (including unmapped) gives lower percentages (e.g., essential = 82% core) than using mapped genes only (86% core). Different projects may use different denominators. This caused a critical review issue where figures showed 86%/78% but prose said 82%/66%. Always document which denominator is used, and be consistent within a synthesis or comparison.

### Row-Wise Apply on Large DataFrames Is Orders of Magnitude Slower Than Merge

**[core_gene_tradeoffs]** Filtering a 961K-row DataFrame with `df.apply(lambda r: (r['orgId'], r['locusId']) in some_set, axis=1)` is extremely slow because it iterates row-by-row in Python. Replace with `df.merge(keys_df, on=['orgId','locusId'], how='inner')` for the same result in seconds instead of minutes. This applies whenever you need to filter a large DataFrame to rows matching a set of key pairs.

### Column Name Collisions When Merging Family Annotations

**[module_conservation]** Merging `module_families.csv` with `family_annotations.csv` on `familyId` can create duplicate column names (`n_modules_x`, `n_modules_y`) when both DataFrames have columns with the same name. Use explicit `suffixes=('_obs', '_annot')` in the merge call to avoid ambiguous column names in downstream analysis and saved TSV files.

### Essential Genes Are Invisible in genefitness-Only Analyses

**[fitness_effects_conservation]** If you query only the `genefitness` table for fitness data, you miss ~14.3% of protein-coding genes — the essential genes that have no transposon insertions and therefore no entries in `genefitness`. These are the most functionally important genes (82% core). Any analysis of fitness vs conservation must explicitly include essential genes from the `gene` table (type='1' genes absent from `genefitness`), or acknowledge that the most extreme fitness category is missing.

### Reviewer Subprocess May Write to Nested Path

**[fitness_effects_conservation]** When invoking the `/submit` reviewer subprocess, if the subprocess resolves `projects/{id}/` relative to its own working directory rather than the repo root, the `REVIEW.md` file can end up at `projects/{id}/projects/{id}/REVIEW.md` instead of `projects/{id}/REVIEW.md`. Check the output path after the reviewer completes and move the file if needed.

---

## Genomes (`kbase_genomes`) Pitfalls

### UUID-Based Identifiers

All primary keys are CDM UUIDs. Use the `name` table to map between external gene IDs and CDM UUIDs.

### Billion-Row Junction Tables

Most junction tables have ~1 billion rows. Never query without filters.

---

## Python / Pandas Pitfalls

### [essential_genome] fillna(False) Produces Object Dtype, Breaking Boolean Operations

When using `merge(..., how='left')` to create a boolean flag column, the unmatched rows get `NaN`. Calling `.fillna(False)` converts the column to `object` dtype (mixed `True`/`False`/`NaN` → mixed `True`/`False`), NOT boolean. The `~` (bitwise NOT) operator on an `object` column produces silently wrong results instead of boolean negation.

```python
# BAD: creates object dtype, ~ gives garbage
df = left.merge(right_with_flag, how='left')
df['flag'] = df['flag'].fillna(False)
not_flagged = df[~df['flag']]  # WRONG — may include all rows

# GOOD: cast to bool after fillna
df['flag'] = df['flag'].fillna(False).astype(bool)
not_flagged = df[~df['flag']]  # Correct boolean negation
```

This caused an orphan essential gene count of 41,059 (total essentials) instead of 7,084 (actual orphans) — a silently incorrect result with no error message.

---

## Skill / Workflow Pitfalls

### [cofitness_coinheritance] Don't create data/results/ subdirectory

**Problem**: Computed results (phi coefficients, summary tables) were placed in `data/results/` instead of flat in `data/`. The BERIL pattern (per `PROJECT.md`) stores all data files flat in `data/`, with subdirectories only for extracted data categories (e.g., `data/cofit/`, `data/genome_cluster_matrices/`). A `data/results/` subdirectory is non-standard.

**Correct pattern**: Put computed outputs directly in `data/` alongside extracted data. Examples from other projects: `data/module_conservation.tsv`, `data/fitness_stats.tsv`, `data/essential_families.tsv`.

---

### [cofitness_coinheritance] Synthesize skill writes findings to README instead of REPORT.md

**Problem**: The `/synthesize` skill instructions say to update `README.md` with Key Findings, Interpretation, Literature Context, etc. But the observatory uses a **three-file structure**: README (concise overview with links), RESEARCH_PLAN (hypothesis/approach), REPORT (full findings/interpretation). The `essential_genome` project is the canonical example. Writing detailed findings into the README makes it too long and inconsistent with other projects.

**Correct workflow**:
1. `/synthesize` should produce **`REPORT.md`** with: Key Findings, Results, Interpretation, Literature Context, Limitations, Future Directions, Visualizations, Data Files
2. **`README.md`** should be a concise overview with a Status line, Overview paragraph, Quick Links section (linking to RESEARCH_PLAN, REPORT, references), and project metadata (Data Sources, Structure, Reproduction, Dependencies, Authors)
3. The README should link to REPORT.md: `See [REPORT.md](REPORT.md) for full findings and interpretation.`

**Action**: Update the synthesize skill's Step 7 to target REPORT.md instead of README.md, and add a step to update the README with a Status line and Quick Links.

---

### [submit] Codex CLI reviewer fails in sandbox with network disabled

**Problem**: Running `codex exec` from a restricted sandbox can fail with DNS/connection errors to the Codex backend (for example `chatgpt.com` resolution failures) because network egress is disabled in that environment.

**Solution**: Run the reviewer invocation with network-enabled permissions (outside the restricted sandbox) and confirm quickly with a minimal smoke test first, e.g. `codex exec "Reply with exactly: ok"`. If the smoke test works, rerun the full reviewer command.

---

### [submit] Inlining very large reviewer prompts reduces Codex CLI reliability

**Problem**: Passing a long system prompt inline (for example via large shell substitutions) can make `codex exec` runs unstable or fail intermittently.

**Solution**: Keep the CLI prompt compact and reference the on-disk prompt file in instructions (for example: "Read and follow `.claude/reviewer/SYSTEM_PROMPT.md`"), then write output to `projects/{id}/REVIEW.md`. This has been more reliable in BERIL submit workflows.

---

### [enigma_contamination_functional_potential] Copying strict features into relaxed mode invalidates sensitivity analysis

**Problem**: In NB02, setting `feats_relaxed = feats_strict.copy()` produces numerically identical strict/relaxed downstream outputs. This makes mapping-mode sensitivity conclusions invalid because the two modes are no longer independently constructed.

**Solution**: Compute strict and relaxed features independently. A scalable pattern is to precompute clade-level annotation counts once on the union of clades, then aggregate those counts separately per mode.

---

### [enigma_contamination_functional_potential] Aggregating annotations directly at genus level in both modes can be slow

**Problem**: Running separate heavy Spark joins/aggregations over `eggnog_mapper_annotations` for each mapping mode can stall notebook execution on large tables.

**Solution**: Precompute per-clade annotation totals once (`total_ann`, defense, mobilome, metabolism), then derive strict/relaxed genus-level feature fractions via pandas aggregation on the precomputed clade table. This preserves mode independence while reducing duplicate Spark work.

---

### [enigma_contamination_functional_potential] Species/strain bridge cannot be forced from genus-only ENIGMA taxonomy

**Problem**: ENIGMA taxonomy in `ddt_brick0000454` currently includes `Domain` through `Genus` levels only. Attempting species-level bridge logic directly will either fail or silently reuse genus-level mappings while appearing higher resolution.

**Solution**: Verify available taxonomy levels first. If species/strain labels are absent, either:
- use an explicit species-proxy mode (unique genus->single GTDB clade) and report mapped-coverage loss, or
- switch to data sources that support species/strain resolution (metagenomes, ASV reclassification pipeline).

---

### [enigma_contamination_functional_potential] FDR pass can silently miss p-value columns with non-standard names

**Problem**: If multiple-testing correction only targets columns ending in `_p`, it will miss p-value columns named like `adj_cov_p_contamination` or `adj_frac_p_contamination`.

**Solution**: Detect p-value columns by substring pattern (for example columns containing `_p` and excluding derived q-value columns) or by an explicit p-column allowlist before applying BH-FDR.

---

### [enigma_contamination_functional_potential] Bootstrap CI loops can become the runtime bottleneck in notebook models

**Problem**: Adding bootstrap confidence intervals for multiple outcomes and model families can make NB03 noticeably slower if bootstrap counts are set too high.

**Solution**: Use moderate bootstrap sizes (for example 250-400) with fixed seeds for reproducibility, and restrict CI estimation to key coefficients/endpoints. This keeps runtime practical while still giving uncertainty intervals for interpretation.

---

### [ecotype_env_reanalysis] Large species exceed Spark maxResultSize during gene cluster extraction

**Problem**: Extracting gene-cluster memberships for *K. pneumoniae* (250 genomes × ~5,500 genes per genome) via `gene` JOIN `gene_genecluster_junction` WHERE `genome_id IN (...)` exceeds Spark's `spark.driver.maxResultSize` (1GB default). The query succeeds in Spark but fails when collecting results to the driver node.

**Solution**: For species with >200 genomes, chunk the genome list into batches of 50-100 and concatenate results. Alternatively, increase `spark.driver.maxResultSize` in the Spark session config. The per-species extraction script should catch this error and continue to the next species (which it does via try/except).

### [ecotype_env_reanalysis] Broken symlinks to Mac paths cause silent failures on JupyterHub

**Problem**: The `ecotype_analysis/data` directory was a symlink pointing to `/Users/paramvirdehal/...` (a Mac path from local development). On JupyterHub, this path doesn't exist, so `os.makedirs(path, exist_ok=True)` throws `FileExistsError` (the symlink exists but its target doesn't). This is confusing because `exist_ok=True` is supposed to suppress the error.

**Solution**: Check for broken symlinks before creating directories. If the path exists as a symlink but the target is missing, remove the symlink first: `if os.path.islink(path): os.remove(path)`. Or avoid committing symlinks to git — use relative paths in code and `.gitignore` data directories.

---

### [env_embedding_explorer] Notebooks committed without outputs are useless for review

**Problem**: When analysis is prototyped as Python scripts (for debugging speed or iterative development), the notebooks get committed with empty output cells. This defeats their purpose — notebooks are the primary audit trail and methods documentation. The `/synthesize` skill reads notebook outputs to extract results, the `/submit` reviewer checks outputs to verify claims, and human readers rely on outputs to follow the analysis without re-running it. Empty notebooks fail all three use cases.

**Solution**: Always execute notebooks before committing, even if the analysis was originally run as a script. Use `jupyter nbconvert --to notebook --execute --inplace notebook.ipynb` or run Kernel → Restart & Run All in JupyterHub. If UMAP or other expensive steps were pre-computed, design the notebook to load cached results (check for file existence before recomputing). This way the notebook runs quickly and still captures all outputs.

---

### [env_embedding_explorer] AlphaEarth geographic signal is diluted by human-associated samples

**Problem**: The pooled geographic distance–embedding distance curve shows a 2.0x ratio (near vs far), but this blends two distinct populations. Environmental samples show 3.4x (strong signal) while human-associated samples show only 2.0x (weak signal). Using the pooled curve underestimates the true geographic signal in the embeddings.

**Solution**: Always stratify AlphaEarth analyses by environment category. At minimum, compute results separately for environmental vs human-associated samples. If using embeddings as environment proxies (e.g., ecotype analysis), consider excluding human-associated samples entirely.

### [env_embedding_explorer] AlphaEarth NaN embeddings — filter before analysis

**Problem**: 3,838 of 83,287 genomes (4.6%) have NaN in at least one of the 64 embedding dimensions. UMAP, cosine distance, and other operations will fail or produce NaN results silently.

**Solution**: Filter to `~df[EMB_COLS].isna().any(axis=1)` before any embedding-based computation. This reduces the dataset from 83,287 to 79,449 genomes.

### [env_embedding_explorer] UMAP with cosine metric is extremely slow for >50K points

**Problem**: Running `umap.UMAP(metric='cosine')` on 83K genomes with 64 dimensions took >60 minutes and did not complete on a single-CPU JupyterHub pod. The cosine metric requires pairwise precomputation which is O(n^2).

**Solution**: L2-normalize the embeddings first, then use `metric='euclidean'`. For L2-normalized vectors, Euclidean distance is monotonically related to cosine distance (`||a-b||^2 = 2(1-cos(a,b))`), so the UMAP topology is equivalent. Additionally, fit UMAP on a 20K subsample (`reducer.fit(subsample)`) then transform the full dataset (`reducer.transform(all_data)`) — this reduced runtime from >60 min to ~7 min.

### [env_embedding_explorer] kaleido v1 requires Chrome — use v0.2.1 on headless pods

**Problem**: kaleido 1.x (the plotly static image export library) requires Google Chrome installed, which isn't available on headless JupyterHub pods. `fig.write_image()` fails with `ChromeNotFoundError`.

**Solution**: Install kaleido 0.2.1 instead: `pip install kaleido==0.2.1`. This older version uses its own bundled Chromium and works on headless systems. The deprecation warning can be ignored.

---

### [pangenome_pathway_geography] GapMind pathways have multiple rows per genome-pathway pair

**Problem**: The initial analysis counted exactly 80 pathways for every species with 0% present because it looked for `score_category = 'present'` which doesn't exist. The root cause: GapMind has exactly 80 pathways total, and each genome-pathway pair has MULTIPLE rows (one per step/component in the pathway).

**Correct approach**: Take the BEST score for each genome-pathway pair before aggregating to species level:

```sql
WITH pathway_scores AS (
    SELECT
        clade_name,
        genome_id,
        pathway,
        CASE score_category
            WHEN 'complete' THEN 5
            WHEN 'likely_complete' THEN 4
            WHEN 'steps_missing_low' THEN 3
            WHEN 'steps_missing_medium' THEN 2
            WHEN 'not_present' THEN 1
            ELSE 0
        END as score_value
    FROM kbase_ke_pangenome.gapmind_pathways
),
best_scores AS (
    SELECT
        clade_name,
        genome_id,
        pathway,
        MAX(score_value) as best_score
    FROM pathway_scores
    GROUP BY clade_name, genome_id, pathway
)
-- Then aggregate to species level
SELECT
    clade_name,
    AVG(complete_pathways) as mean_complete_pathways,
    STDDEV(complete_pathways) as std_complete_pathways
FROM (
    SELECT clade_name, genome_id,
           SUM(CASE WHEN best_score >= 5 THEN 1 ELSE 0 END) as complete_pathways
    FROM best_scores
    GROUP BY clade_name, genome_id
)
GROUP BY clade_name
```

**Key insight**: GapMind score categories are: `complete`, `likely_complete`, `steps_missing_low`, `steps_missing_medium`, `not_present` (NOT a simple binary 'present' flag).

---

### [aromatic_catabolism_network] Keyword-based gene categorization is fragile — use co-fitness to validate

**Problem**: Categorizing genes by keyword matching on RAST function descriptions (e.g., `if 'protocatechuate' in func.lower()`) misclassifies enzymes with non-obvious names. ACIAD1710 (4-carboxymuconolactone decarboxylase, EC 4.1.1.44) is a core pca pathway enzyme but was classified as "Other" because the keyword list checked for "muconate" but not "muconolactone."

**Solution**: Use keyword-based categorization as an initial pass, then validate with co-fitness correlations. In this case, co-fitness analysis correctly recovered pcaC (r=0.978 with the Aromatic pathway). When writing keyword classifiers for gene functions, test them against known members of each category and add missing synonyms.

### [aromatic_catabolism_network] NotebookEdit can create invalid cells missing 'outputs' field

**Problem**: Using the `NotebookEdit` tool to replace a code cell's content can produce a cell without the required `outputs` and `execution_count` fields. `jupyter nbconvert --execute` then fails with `NotebookValidationError: 'outputs' is a required property`.

**Solution**: After using `NotebookEdit` on code cells, verify the notebook JSON is valid. Fix missing fields with:
```python
import json
with open('notebook.ipynb') as f:
    nb = json.load(f)
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        cell.setdefault('outputs', [])
        cell.setdefault('execution_count', None)
with open('notebook.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)
```

### [aromatic_catabolism_network] Claude Code 2.1.47 Bash tool swallows output when waiting on `claude` subprocess

**Problem**: In Claude Code version 2.1.47, running `claude -p` as a foreground command (or backgrounded with `wait`) in the Bash tool causes ALL output to be suppressed — including `echo` statements that precede the `claude` invocation. The `claude -p` process runs and produces correct output, but the Bash tool discards it. This worked correctly in 2.1.45.

**Workaround**: Launch `claude -p` in the background with file redirection, return immediately, then read the output file in a separate Bash call:
```bash
env -u CLAUDECODE claude -p --no-session-persistence ... > /tmp/output.txt 2>&1 &
echo "PID=$!"
# In a separate Bash call:
cat /tmp/output.txt
```

Do NOT use `wait` on the PID — this triggers the same output suppression.

### [counter_ion_effects] NaCl-importance thresholds are sensitive to experiment count

**Problem**: Using `n_sick >= 1` (at least one NaCl experiment with fit < -1) as an NaCl-importance threshold is biased by the number of NaCl experiments per organism. *Synechococcus elongatus* (SynE) has 12 NaCl dose-response experiments (0.5–250 mM) and flags 32.6% of genes as NaCl-important — 3× higher than the next organism. This inflates cross-condition overlap statistics (SynE shows 88.6% metal–NaCl shared-stress).

**Solution**: When comparing gene-level importance across conditions with unequal experiment counts, either (a) require `n_sick >= 2` or use `mean_fit < threshold` instead of `n_sick >= 1`, or (b) report results with and without outlier organisms as a sensitivity check. Excluding SynE, overall metal–NaCl overlap drops from 39.8% to 36.7% — modest but worth documenting.

### [fw300_metabolic_consistency] BacDive utilization has four values, not two

**Problem**: BacDive `metabolite_utilization.utilization` stores four distinct values: `+` (can utilize), `-` (cannot utilize), `produced` (organism produces it), and `+/-` (variable/ambiguous). Treating this as a binary +/- field inflates counts: for *P. fluorescens*, indole has 60 "produced" entries and only 1 actual utilization test. Computing `pct_positive` from raw +/- counts without excluding `produced` and `+/-` entries gives incorrect species-level utilization rates.

**Solution**: Filter to explicit +/- tests before computing utilization percentages:
```python
n_tested = (utilization == '+').sum() + (utilization == '-').sum()
pct_positive = (utilization == '+').sum() / n_tested  # exclude 'produced' and '+/-'
```
Track all four categories separately (`n_positive`, `n_negative`, `n_produced`, `n_ambiguous`) for full transparency.

### [fw300_metabolic_consistency] GapMind genome IDs lack the RS_/GB_ prefix used in pangenome tables

**Problem**: The `kbase_ke_pangenome.gapmind_pathways` table stores genome IDs without the GTDB `RS_` or `GB_` prefix (e.g., `GCF_001307155.1`), while the pangenome `genome` table uses the prefixed form (`RS_GCF_001307155.1`). A direct equality match between a pangenome genome_id and GapMind genome_id returns zero rows.

**Solution**: Strip the `RS_` or `GB_` prefix before matching, or use a fallback chain:
```python
# Try original ID first, then stripped, then partial match
gapmind_match = df[df['genome_id'] == pangenome_id]
if len(gapmind_match) == 0:
    alt_id = pangenome_id.replace('RS_', '').replace('GB_', '')
    gapmind_match = df[df['genome_id'] == alt_id]
if len(gapmind_match) == 0:
    accession = pangenome_id.split('_', 1)[-1]  # e.g., GCF_001307155.1
    gapmind_match = df[df['genome_id'].str.contains(accession)]
```

---

## NMDC (`nmdc_arkin`) Pitfalls

### [nmdc_community_metabolic_ecology] Classifier and metabolomics tables use `file_id`, not `sample_id`

**Problem**: `nmdc_arkin.metabolomics_gold`, `kraken_gold`, `centrifuge_gold`, and
`gottcha_gold` all use `file_id` and `file_name` as their primary identifier — not
`sample_id`. Queries with `WHERE sample_id = ...` or `COUNT(DISTINCT sample_id)` will throw
`AnalysisException: UNRESOLVED_COLUMN` and stop notebook execution.

**Solution**: Use `file_id` as the join key for all classifier and metabolomics tables.
```sql
-- WRONG
SELECT COUNT(DISTINCT sample_id) FROM nmdc_arkin.metabolomics_gold

-- CORRECT
SELECT COUNT(DISTINCT file_id) FROM nmdc_arkin.metabolomics_gold
```

### [nmdc_community_metabolic_ecology] `taxonomy_features` is a wide-format matrix with numeric column names

**Problem**: `nmdc_arkin.taxonomy_features` does not have a `sample_id` or `file_id` column.
Its columns are numeric NCBI taxon IDs (e.g., `7`, `11`, `33`, `34`, ...). Attempting to
`SELECT sample_id FROM taxonomy_features` fails immediately. The table is a pivoted matrix
where rows are likely samples and columns are taxon abundances.

**Solution**: Do not use `taxonomy_features` for tidy-format joins. Use the classifier tables
(`kraken_gold`, `centrifuge_gold`, `gottcha_gold`) instead — they are tidy format with
`file_id`, `rank`, `name`/`label`, and `abundance` columns. Count rows with
`SELECT COUNT(*) FROM nmdc_arkin.taxonomy_features` to verify the row count matches the
expected number of samples.

### [nmdc_community_metabolic_ecology] Confirmed `metabolomics_gold` compound annotation columns

The `metabolomics_gold` table has: `kegg` (string — KEGG compound ID), `chebi` (double —
ChEBI ID), `name` (string — compound name), `inchi`, `inchikey`, `smiles`. Use backtick
quoting for column names with spaces (e.g., `` `Molecular Formula` ``, `` `Area` ``).
The `annotation_terms_unified` table is a gene-annotation lookup (COG/EC/GO/KEGG terms) and
**cannot** be used as a metabolite compound lookup.

### [nmdc_community_metabolic_ecology] Classifier and metabolomics `file_id` namespaces do not overlap — must bridge through `sample_id`

**Problem**: Joining `nmdc_arkin.centrifuge_gold` (or `kraken_gold`, `gottcha_gold`) directly
to `nmdc_arkin.metabolomics_gold` on `file_id` always returns **zero rows**. The two table
sets use non-overlapping `file_id` prefixes:
- Classifier files: `nmdc:dobj-11-*` (metagenomics workflow outputs)
- Metabolomics files: `nmdc:dobj-12-*` (metabolomics workflow outputs)

They are different workflow output types for the same biosample and are only linkable through
the **biosample `sample_id`** (e.g., `nmdc:bsm-11-*`).

**Solution**: Find a `file_id → sample_id` bridge table in `nmdc_arkin` before attempting
to link classifier and metabolomics data. The `abiotic_features` table uses `sample_id` as
its primary key; use `get_tables("nmdc_arkin")` and
`get_table_schema("nmdc_arkin", table_name)` to find any table that has
**both** `file_id` and `sample_id` columns. NB02 of
`nmdc_community_metabolic_ecology` does this scan systematically.

```python
from berdl_notebook_utils import get_tables, get_table_schema

# Scan all nmdc_arkin tables for file_id + sample_id
all_tables = get_tables("nmdc_arkin")
for tbl in all_tables:
    schema = get_table_schema("nmdc_arkin", tbl)
    cols = {col["name"] for col in schema}
    if 'file_id' in cols and 'sample_id' in cols:
        print(f'Bridge candidate: {tbl}')
```

The bridge table is `nmdc_arkin.omics_files_table` (385,562 rows, confirmed). It has
`file_id`, `sample_id`, `study_id`, `workflow_type`, and `file_type` columns.

### [nmdc_community_metabolic_ecology] `spark.createDataFrame(pandas_df)` fails with `ChunkedArray` error after `.toPandas()` on Spark Connect

**Problem**: When a pandas DataFrame is produced by calling `.toPandas()` on a Spark Connect
DataFrame, its columns are backed by PyArrow `ChunkedArray` objects. Passing this DataFrame
back to `spark.createDataFrame()` raises:

```
TypeError: Cannot convert pyarrow.lib.ChunkedArray to pyarrow.lib.Array
```

This prevents the common pattern of "pull data to pandas, filter it, register as a Spark temp view."

**Solution**: Avoid the pandas→Spark roundtrip entirely. Instead, keep all filtering and joining
in Spark SQL using subqueries and the original table name. For bridge joins, use the full table
name directly in SQL rather than materializing the bridge to a temp view:

```python
# WRONG — fails with ChunkedArray error
bridge_df = spark.sql("SELECT file_id, sample_id FROM nmdc_arkin.omics_files_table").toPandas()
bridge_spark = spark.createDataFrame(bridge_df)  # TypeError

# CORRECT — join using the table name directly in SQL
clf_samples = spark.sql("""
    SELECT DISTINCT b.sample_id
    FROM (SELECT DISTINCT file_id FROM nmdc_arkin.centrifuge_gold) c
    JOIN nmdc_arkin.omics_files_table b ON c.file_id = b.file_id
""").toPandas()
```

If you must convert pandas back to Spark (small DataFrames only), convert columns to native
Python lists first: `df[col] = df[col].tolist()` for each column before calling
`spark.createDataFrame(df)`.

### [nmdc_community_metabolic_ecology] `abiotic_features` Column Names Use `_has_numeric_value` Suffix; No `water_content` Column

**Problem**: Most numeric columns in `nmdc_arkin.abiotic_features` use a `_has_numeric_value` suffix (e.g., `annotations_tot_org_carb_has_numeric_value`), but two columns do not: `annotations_ph` (no suffix) and depth/temp which do have the suffix. Using the bare name without the suffix raises `UNRESOLVED_COLUMN`.

Additionally, `annotations_water_content` does not exist. Use `annotations_diss_org_carb_has_numeric_value` and `annotations_conduc_has_numeric_value` instead.

**Columns are already `double` type** — no `CAST` needed, but harmless if included.

**All-zero values mean missing**: the table stores `0.0` for unmeasured variables rather than `NULL`. Replace zeros with `NaN` before analysis:
```python
for col in abiotic_num_cols:
    abiotic[col] = abiotic[col].replace(0.0, np.nan)
```

**Correct column reference**:
```sql
-- WRONG
a.annotations_tot_org_carb, a.annotations_tot_nitro_content, a.annotations_water_content

-- CORRECT
a.annotations_tot_org_carb_has_numeric_value,
a.annotations_tot_nitro_content_has_numeric_value,
a.annotations_diss_org_carb_has_numeric_value,   -- dissolved organic carbon proxy
a.annotations_conduc_has_numeric_value            -- conductance (replaces water_content)
```

Full column list: `sample_id`, `annotations_ph`, `annotations_temp_has_numeric_value`, `annotations_depth_has_numeric_value`, `annotations_depth_has_maximum_numeric_value`, `annotations_depth_has_minimum_numeric_value`, `annotations_tot_org_carb_has_numeric_value`, `annotations_tot_nitro_content_has_numeric_value`, `annotations_diss_org_carb_has_numeric_value`, `annotations_conduc_has_numeric_value`, `annotations_diss_oxygen_has_numeric_value`, `annotations_ammonium_has_numeric_value`, `annotations_tot_phosp_has_numeric_value`, `annotations_soluble_react_phosp_has_numeric_value`, `annotations_carb_nitro_ratio_has_numeric_value`, `annotations_chlorophyll_has_numeric_value`, `annotations_calcium_has_numeric_value`, `annotations_magnesium_has_numeric_value`, `annotations_potassium_has_numeric_value`, `annotations_manganese_has_numeric_value`, `annotations_samp_size_has_numeric_value`.

---

### Fitness Matrix locusId Type Mismatch (Integer vs String)

**[metal_specificity]** Fitness matrices from `fitness_modules/data/matrices/` use integer-typed locusId indices (e.g., `206065`) while the Metal Atlas `metal_important_genes.csv` stores locusIds as strings (e.g., `'206065'`). Pandas index lookup (`locus not in fit_mat.index`) silently fails when types don't match — the gene appears absent rather than raising an error.

This caused DvH (495 metal-important genes) and Btheta (276 genes) to be completely dropped from the analysis without any warning. The organism processing loop reported "SKIPPED (no fitness matrix or no non-metal experiments)" even though the matrix existed.

**Fix**: Always convert both sides to strings before matching:
```python
fit_mat.index = fit_mat.index.astype(str)
metal_loci = {str(l) for l in metal_loci}
```

**Detection**: Check organism counts in your output data against the expected input. If organisms with known data are missing, suspect a type mismatch.

### ICA Module z-Normalization Fails When Target Experiments Are Rare

**[metal_specificity]** When computing per-module z-scores across all experiments to identify metal-responsive modules, the z-normalization produces max |z| < 2.0 for metal experiments if metals are a small fraction of total experiments (e.g., 12/176 for MR1). This is because the z-score denominator (std across all experiments) is dominated by the non-metal majority.

The Metal Atlas NB05 avoided this by using pre-computed z-scores from `metal_modules.csv` that were standardized per-module across all experiments (not per-experiment-type). Re-computing z-scores from raw `module_conditions.csv` activity values does not reproduce the same responsiveness threshold.

**Fix**: Use the pre-computed z-scores from upstream analysis rather than re-normalizing from raw activity scores.

### BacDive Species Names Don't Always Match GTDB Species Names

**[bacdive_metal_validation]** GTDB (used by the pangenome) renames many species with suffixes like `_A`, `_B` (e.g., `Pseudomonas fluorescens A`), adds genus-level splits (e.g., `Pantoea A`), and redefines species boundaries differently from LPSN/DSMZ (used by BacDive). Direct species name matching captures only 34.5% of strains; adding base-name matching (stripping GTDB suffixes) adds another 8.9% for 43.4% total. The remaining 56.6% are genuinely different species concepts or genera not yet in GTDB r214.

**Fix**: Use two-pass matching: (1) exact species name, (2) base name with GTDB suffix stripped. For higher coverage, match via GCA genome accession → pangenome `genome_id` (requires `GB_` prefix + version suffix handling).

### BacDive Heavy Metal Category Is Small After Matching

**[bacdive_metal_validation]** BacDive has 31 strains tagged with cat3=#Heavy metal contamination, but only 10 match to pangenome species with metal tolerance scores. Research plans should not assume the full BacDive category size will survive matching — always compute post-matching sample sizes and power before interpreting results.

### Variable Overwriting in Multi-Test Notebook Cells

**[metal_specificity]** When running multiple statistical tests in sequence (e.g., Fisher exact for H1c then Fisher exact for H1d), reusing generic variable names like `odds, p = stats.fisher_exact(table)` causes the second test to overwrite the first. A downstream summary cell then prints the wrong values under the wrong labels.

**Fix**: Use descriptive variable names for each test:
```python
h1c_or, h1c_p = stats.fisher_exact(table_h1c)
h1d_or, h1d_p = stats.fisher_exact(table_h1d)
```

---

## BacDive (`kescience_bacdive`) Pitfalls

### [plant_microbiome_ecotypes] BacDive JOIN type mismatch between sequence_info and isolation tables

**Problem**: `kescience_bacdive.sequence_info.bacdive_id` is INT but `kescience_bacdive.isolation.bacdive_id` is STRING. A direct join returns zero rows because Spark does not implicitly cast across INT/STRING types.

**Solution**: Use `CAST(si.bacdive_id AS STRING) = iso.bacdive_id` for cross-table joins:

```sql
-- WRONG: type mismatch, returns 0 rows
SELECT * FROM kescience_bacdive.sequence_info si
JOIN kescience_bacdive.isolation iso ON si.bacdive_id = iso.bacdive_id

-- CORRECT: explicit cast
SELECT * FROM kescience_bacdive.sequence_info si
JOIN kescience_bacdive.isolation iso ON CAST(si.bacdive_id AS STRING) = iso.bacdive_id
```

---

## Additional Spark / Python Pitfalls

### [plant_microbiome_ecotypes] Spark driver memory overflow with large aggregations on eggnog_mapper_annotations

**Problem**: The 93M row `eggnog_mapper_annotations` table can produce aggregated results exceeding `spark.driver.maxResultSize` (1024 MiB) when collecting species×OG matrices or similar large cross-tabulations to the driver.

**Solution**: Compute Fisher test contingency inputs (counts per group) server-side rather than collecting species×OG matrices. Push aggregation into Spark SQL and collect only the summary counts needed for statistical tests:

```python
# WRONG: collect full species×OG matrix
matrix = spark.sql("SELECT species, OG, COUNT(*) FROM ... GROUP BY species, OG").toPandas()

# CORRECT: compute contingency counts server-side
counts = spark.sql("""
    SELECT OG,
           SUM(CASE WHEN is_plant = 1 THEN 1 ELSE 0 END) AS plant_count,
           SUM(CASE WHEN is_plant = 0 THEN 1 ELSE 0 END) AS non_plant_count
    FROM ... GROUP BY OG
""").toPandas()
```

### [plant_microbiome_ecotypes] statsmodels Python 3.13 compatibility — use formula API

**Problem**: `import statsmodels.api as sm` fails on Python 3.13 due to a graphics import chain that triggers an ImportError.

**Solution**: Use `import statsmodels.formula.api as smf` instead, which avoids the problematic graphics import path:

```python
# WRONG on Python 3.13
import statsmodels.api as sm

# CORRECT
import statsmodels.formula.api as smf
```

### [plant_microbiome_ecotypes] bakta_pfam_domains query format — Pfam IDs may not match

**Problem**: Querying `bakta_pfam_domains` with Pfam IDs like `'PF00771'` returned 0 hits across all 11 domains tested. The table may use a different ID format (e.g., domain names instead of accessions, or versioned accessions like `PF00771.1`) or require a different join logic.

**Solution**: Investigate the actual values stored in the table before writing queries:

```python
# Check what format the table actually uses
spark.sql("SELECT DISTINCT pfam_id FROM kbase_ke_pangenome.bakta_pfam_domains LIMIT 20").show()
```

This pitfall needs further investigation to determine the correct query format.

### [plant_microbiome_ecotypes] GapMind core-level completeness scoring yields 0% across all compartments

**Problem**: Using `gapmind_pathways` with `sequence_scope = 'core'` for broad taxonomic comparisons yields 0% completeness across all compartments. The core-level scoring threshold is too stringent for genus-level or cross-species comparisons where pathway genes may not be universally present.

**Solution**: Use max-aggregation at the genus level instead of core-level scoring:

```sql
-- WRONG: core-level scoring too stringent for cross-species comparison
SELECT pathway, AVG(score_simplified) FROM gapmind_pathways
WHERE sequence_scope = 'core' GROUP BY pathway

-- CORRECT: aggregate at genus level with max score per genome-pathway pair
SELECT genus, pathway, AVG(max_score) FROM (
    SELECT clade_name, pathway, MAX(score_simplified) AS max_score
    FROM gapmind_pathways
    GROUP BY clade_name, pathway
) grouped
JOIN taxonomy ON ...
GROUP BY genus, pathway
```

---

## Quick Checklist

Before running a query, verify:

- [ ] Using exact equality instead of LIKE patterns for performance
- [ ] Large tables have appropriate filters (genome_id, species_id, orgId)
- [ ] JOIN keys are correct (gene_cluster_id for pangenome annotations, locusId for fitness)
- [ ] Numeric comparisons use CAST for string-typed databases
- [ ] You're not comparing gene clusters across species (pangenome)
- [ ] Expected tables actually exist (check [schemas/](schemas/))
- [ ] Data coverage is sufficient for your analysis
- [ ] Using REST API only for simple queries; Spark SQL for complex ones

---

## Project-Specific Pitfalls

### `fact_pairwise_interaction` Is Identical to `fact_carbon_utilization`

**[cf_formulation_design]** In the PROTECT Gold tables, `fact_pairwise_interaction` and `fact_carbon_utilization` contain identical values (correlation = 1.0, mean difference = 0.0). The endpoint OD data does not capture co-culture metabolic interactions — only the RFU-based competition assay provides pairwise interaction effects.

**Impact**: Per-substrate co-culture analysis is impossible from endpoint OD data. NB08 discovered this and pivoted to using only the RFU-based competition assay.

### Codon Usage Bias (CUB) Is Confounded by GC Content Across Species

**[cf_formulation_design]** Cross-species CUB comparisons (e.g., PA vs commensals) are confounded by GC content variation (31–73%). Organisms with extreme GC composition have inflated CUB scores regardless of growth optimization. CUB is only meaningful within species or across species with similar GC content.

**Fix**: Use lab growth data as ground truth for cross-species growth rate comparisons. CUB is valid within-species (e.g., comparing PA strain groups).

### PA14 Is Not Representative of CF Lung PA

**[cf_formulation_design]** PA14 (ExoU+, Pel-only, ladS mutant) represents <5% of CF PA isolates by virulence genotype. CF PA is 94% ExoS+ and 92% Pel+Psl+ (PAO1-like). Results from PA14-based assays should be validated against ExoS+ strains before generalizing to CF.

**Impact**: Inhibition assays using PA14 test the formulation against a minority variant. Amino acid catabolism is identical across ExoU+ and ExoS+ strains (no FDR-significant differences), so competitive exclusion mechanism should transfer, but direct validation is needed.

### Pangenome `gene_cluster` Uses `gtdb_species_clade_id`, Not `clade_name`

**[cf_formulation_design]** The `kbase_ke_pangenome.gene_cluster` table has `gtdb_species_clade_id` (not `clade_name`). The `gapmind_pathways` table has `clade_name`. The `gene` table has only `gene_id` and `genome_id` — no species/clade column. The `eggnog_mapper_annotations` table uses `query_name` (not `gene_cluster_id`) as its identifier, which maps to `gene_cluster_id` in the gene_cluster table.

**Fix**: Always check column names with `DESCRIBE table` before writing joins. Common join patterns:
```sql
-- bakta: gene_cluster_id matches directly
bakta_annotations ba JOIN gene_cluster gc ON ba.gene_cluster_id = gc.gene_cluster_id

-- eggnog: query_name = gene_cluster_id
eggnog_mapper_annotations ea JOIN gene_cluster gc ON ea.query_name = gc.gene_cluster_id

-- gene-to-genome: via junction table
gene_genecluster_junction ggj JOIN gene g ON ggj.gene_id = g.gene_id
```

### protect_genomedepot Species Filter Requires Taxon Join

**[cf_formulation_design]** `browser_genome` has no `species` column. Filtering by species requires joining through `browser_taxon`:
```sql
FROM protect_genomedepot.browser_gene bg
JOIN protect_genomedepot.browser_genome bge ON bg.genome_id = bge.id
JOIN protect_genomedepot.browser_taxon bt ON bge.taxon_id = bt.id
WHERE bt.name LIKE '%aeruginosa%'
```

### Psl Operon Genes Are Under-Annotated by Name

**[cf_formulation_design]** In GenomeDepot-based databases (`protect_genomedepot`, `phagefoundry_paeruginosa_genome_browser`), pslA-pslO genes are rarely annotated with canonical gene names — only PAO1's reference genome has them. The pangenome `bakta_annotations` has better coverage but pslA/pslG/pslK are still sparse. Use KEGG orthologs (K20997–K21005) via `eggnog_mapper_annotations` for reliable psl detection (~95% prevalence vs <1% by gene name alone).
- [ ] Pfam accessions verified against InterPro/UniProt (not assumed from name)
- [ ] eggNOG PFAMs column searched by domain NAME, not accession
- [ ] Auth token is fresh (check `~/.berdl_kbase_session` if `.env` token fails)
- [ ] Checked ALL databases for a project prefix (e.g., both GenomeDepot and strain_modelling for PhageFoundry)
