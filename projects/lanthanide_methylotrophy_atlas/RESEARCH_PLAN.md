# Research Plan: Lanthanide Methylotrophy Atlas

## Research Question
Across BERDL's 293K-genome pangenome, what is the phylogenomic distribution and cassette-completeness of the lanthanide-dependent methanol/ethanol oxidation system (xoxF / xoxJ / PQQ / lanmodulin), and does its presence correspond to environments containing rare earth elements?

## Hypotheses
- **H1 (xoxF dominance)**: xoxF (KEGG K00114, REE-dependent MDH) is genome-frequent at ≥10× the rate of mxaF (K14028, Ca-dependent MDH) across the BERDL pangenome. Pilot probes already show ~30:1 (3,690 vs 189 genomes); H1 tests whether the ratio is robust across phyla after phylogenetic controls.
  - **H0**: xoxF and mxaF occur at indistinguishable rates once phylogeny and genome size are controlled.
- **H2 (environmental enrichment)**: Genomes carrying the *full* lanthanide-MDH cassette (xoxF + xoxJ + ≥1 PQQ-biosynthesis gene) are over-represented in samples whose `ncbi_env` metadata reference REEs, mining drainage, methylotrophic media, volcanic/geothermal sources, or other mineral-rich substrates, vs. matched-phylogeny controls drawn from host-associated and generic environmental sources.
  - **H0**: Full-cassette presence is independent of environmental metadata after phylogenetic control.
- **H3 (lanmodulin clade restriction)**: Bakta-validated `Lanmodulin` product hits are restricted to a small set of α-Proteobacterial methylotroph clades (Beijerinckiaceae, Acetobacteraceae, Hyphomicrobiaceae) and co-occur with xoxF in ≥80% of cases.
  - **H0**: Lanmodulin product hits are taxonomically diffuse and lanmodulin presence is uncorrelated with xoxF presence.

## Literature Context
The lanthanide switch in methylotrophs was discovered when Pol et al. (2014, *Nature*) characterized XoxF in *Methylacidiphilum fumariolicum* SolV from a volcanic mudpot. Subsequent work showed xoxF is widespread (Skovran & Martinez-Gomez, 2015; Chistoserdova, 2016) but pangenome-scale surveys remain limited to a few hundred genomes. Lanmodulin (LanM) was discovered in *Methylobacterium extorquens* AM1 (Cotruvo et al., 2018, *JACS*) as a high-affinity REE-binding protein implicated in periplasmic REE handling. Picone & Op den Camp (2019, *Curr Opin Biotechnol*) reviewed REE-dependent enzymes and the open environmental questions. **Open question**: the field's working hypothesis that XoxF rather than MxaF is the dominant biological methanol-oxidation cofactor across bacteria has never been tested at >1000 genomes; the BERDL pangenome (293K genomes, 27K species) enables this directly.

The `metal_fitness_atlas` project (Dehal, complete) explicitly identifies REEs as the highest-priority untested critical mineral and proposes wet-lab follow-on experiments. This project answers the parallel genomic questions BERDL alone can address.

## Query Strategy

### Tables Required
| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `kbase_ke_pangenome.eggnog_mapper_annotations` | KEGG_ko (K00114, K14028, K06135-K06139, K20385); Preferred_name (xoxF, xoxJ, mxaF, pqq*, lanM) | ~1B annotations | filter by KEGG_ko or Preferred_name first; project columns |
| `kbase_ke_pangenome.bakta_annotations` | gold-standard `product` field (lanthanide-MDH variants, lanmodulin, xoxJ accessory) | ~1B annotations | RLIKE on `product` for lanthan/xoxf/lanmod/rare.earth |
| `kbase_ke_pangenome.gene` | gene_id → genome_id mapping | 1B | always JOIN, never full-scan |
| `kbase_ke_pangenome.gene_genecluster_junction` | bakta annotations are per-cluster; this links to genes | ~1B | join via gene_cluster_id |
| `kbase_ke_pangenome.gene_cluster` | cluster representative protein/nucleotide sequences (faa/fna) | 132M | for sequence audits of xoxF/lanmodulin paralogs |
| `kbase_ke_pangenome.genome` | genome_id → biosample/taxonomy bridge | 293K | small enough to load in full |
| `kbase_ke_pangenome.gtdb_taxonomy_r214v1` | per-genome taxonomy for phylogenomic rollups | 293K | small |
| `kbase_ke_pangenome.ncbi_env` | sample isolation metadata; explicit REE-AMD samples | varies | filter on `content` regex; explicit `accession` join via `genome.ncbi_biosample_id` |
| `kbase_ke_pangenome.alphaearth_embeddings_all_years` | env-niche coordinates (39.5% of xoxF genomes covered) | 83K rows × 64 dims | join after subsetting genomes |
| `kescience_bacdive.culture_condition` | DSMZ methylotroph media as taxonomic anchor | 1M | filter on medium_name |

### Key Queries

1. **Marker calibration — eggNOG vs bakta cross-validation per genome**:
```sql
WITH eggnog_xoxf AS (
  SELECT g.genome_id, COUNT(DISTINCT g.gene_id) AS n
  FROM kbase_ke_pangenome.gene g
  JOIN kbase_ke_pangenome.eggnog_mapper_annotations e ON e.query_name = g.gene_id
  WHERE e.KEGG_ko LIKE '%K00114%'
  GROUP BY g.genome_id
),
bakta_xoxf AS (
  SELECT g.genome_id, COUNT(DISTINCT g.gene_id) AS n
  FROM kbase_ke_pangenome.gene g
  JOIN kbase_ke_pangenome.gene_genecluster_junction j ON j.gene_id = g.gene_id
  JOIN kbase_ke_pangenome.bakta_annotations b ON b.gene_cluster_id = j.gene_cluster_id
  WHERE LOWER(b.product) RLIKE 'xoxf|lanthanide.dependent.*dehydrog'
  GROUP BY g.genome_id
)
SELECT
  COUNT(DISTINCT COALESCE(e.genome_id, b.genome_id)) AS n_either,
  COUNT(DISTINCT CASE WHEN e.n IS NOT NULL AND b.n IS NOT NULL THEN COALESCE(e.genome_id, b.genome_id) END) AS n_both,
  COUNT(DISTINCT CASE WHEN e.n IS NOT NULL AND b.n IS NULL THEN e.genome_id END) AS n_eggnog_only,
  COUNT(DISTINCT CASE WHEN e.n IS NULL AND b.n IS NOT NULL THEN b.genome_id END) AS n_bakta_only
FROM eggnog_xoxf e FULL OUTER JOIN bakta_xoxf b USING (genome_id);
```

2. **Cassette-completeness scoring per genome** (already prototyped in feasibility probe):
```sql
WITH per_genome AS (
  SELECT g.genome_id,
    MAX(CASE WHEN e.KEGG_ko LIKE '%K00114%' THEN 1 ELSE 0 END) AS has_xoxF,
    MAX(CASE WHEN e.KEGG_ko LIKE '%K14028%' THEN 1 ELSE 0 END) AS has_mxaF,
    MAX(CASE WHEN e.Preferred_name = 'xoxJ' THEN 1 ELSE 0 END) AS has_xoxJ,
    MAX(CASE WHEN e.Preferred_name IN ('pqqB','pqqC','pqqD','pqqE') THEN 1 ELSE 0 END) AS has_pqq
  FROM kbase_ke_pangenome.gene g
  JOIN kbase_ke_pangenome.eggnog_mapper_annotations e ON e.query_name = g.gene_id
  GROUP BY g.genome_id
)
SELECT * FROM per_genome;
```

3. **Environmental association — REE-AMD anchor**:
```sql
SELECT g.genome_id
FROM kbase_ke_pangenome.genome g
WHERE g.ncbi_biosample_id IN (
  SELECT DISTINCT accession FROM kbase_ke_pangenome.ncbi_env
  WHERE LOWER(content) LIKE '%rare earth%'
);
-- 37 genomes confirmed in pilot probe
```

### Performance Plan
- **Tier**: BERDL JupyterHub (Spark) for NB01/NB02/NB04/NB05/NB07 (any cell that hits `kbase_ke_pangenome` directly); local pandas for NB03/NB06 once cached parquet/CSV is in `data/`.
- **Spark session import (matched to environment)**:
  - **JupyterHub notebook (`.ipynb` rendered by JupyterLab)**: `spark = get_spark_session()` — no import needed; provided by the kernel.
  - **JupyterHub CLI / scripts (`python script.py` on cluster)**: `from berdl_notebook_utils.setup_spark_session import get_spark_session; spark = get_spark_session()`.
  - **Local machine off-cluster**: `from get_spark_session import get_spark_session` (requires `.venv-berdl` + SSH tunnels + pproxy chain — not used here since we're on-cluster).
  - This project's notebooks will use the JupyterHub-notebook idiom (`spark = get_spark_session()` with no import) and document the alternative in their headers.
- **Estimated complexity**: moderate — joins on `eggnog_mapper_annotations` (~1B rows) need per-marker filters (KEGG_ko or Preferred_name) before joining to `gene`; never full-scan `gene` (1B rows) without genome_id pruning. NB02/NB04 joins benefit from caching marker hits per-genome to a small table first.
- **Known pitfalls**:
  - eggNOG `Preferred_name='lanM'` returns 337 false positives in gut bacteria (Blautia, Lachnospiraceae, Streptococcus) — these are unrelated proteins. **Use bakta `product='Lanmodulin'` as the trustworthy lanmodulin source.**
  - eggNOG `Preferred_name='mxaF'` with `KEGG_ko='ko:K00114'` is actually xoxF (KO is authoritative; Preferred_name is sometimes stale). Always disambiguate by KEGG_ko.
  - `ncbi_env.content` regex needs care: "Lepus europaeus", "Salicornia europaea", "Russia: Samara" all hit naive `samar|europ` patterns. Use full-element-name regex anchored on `\brare earth\b|\blanthan|\bcerium|\bytterb` etc., or restrict to `attribute_name='isolation_source'`.
  - String-typed numerics in `metal_concentration_value`-style columns may need CAST.
- **Auth**: `KBASE_AUTH_TOKEN` already loaded from `.env`; on-cluster direct Spark (verified via `python scripts/detect_berdl_environment.py`).

## Analysis Plan

### NB01 — Marker extraction & calibration (Spark, ~10 min)
- **Goal**: build the per-genome marker matrix for xoxF, mxaF, xoxJ, lanmodulin, pqq[A-E], using both eggNOG (KEGG_ko) and bakta (product) sources; quantify agreement and the lanM-Preferred_name false-positive rate.
- **Expected output**: `data/genome_marker_matrix.parquet` (genome_id × markers × source-of-evidence), `figures/marker_agreement_eggnog_vs_bakta.png`, `figures/lanM_preferred_name_false_positives.png`

### NB02 — Phylogenomic atlas (Spark, ~5 min)
- **Goal**: roll up markers to GTDB family/genus level; quantify the xoxF:mxaF ratio across phyla; compare cassette-completeness distributions.
- **Expected output**: `data/marker_taxonomy_rollup.csv`, `figures/xoxF_vs_mxaF_by_phylum.png`, `figures/cassette_completeness_distribution.png`

### NB03 — H1 testing (local, ~2 min)
- **Goal**: formally test xoxF dominance with binomial / chi-square tests stratified by phylum; control for genome size with logistic regression.
- **Expected output**: `data/h1_results.csv`, `figures/h1_xoxF_dominance.png`

### NB04 — Environmental association (Spark for join, local for stats, ~15 min)
- **Goal**: link genomes → biosamples → ncbi_env → environment classes (REE-impacted / methylotrophic / mining / generic-environmental / host-associated); test H2 with logistic regression controlling for phylum and genome size; AlphaEarth embedding-distance follow-up.
- **Expected output**: `data/genome_environment_classes.csv`, `data/h2_logistic_results.csv`, `figures/cassette_by_environment.png`, `figures/alphaearth_pca_xoxF.png`

### NB05 — Lanmodulin focal study (Spark + local, ~5 min)
- **Goal**: bakta-validated lanmodulin genomes → taxonomy → fraction with co-located xoxF; sequence-level inspection of representative lanmodulin protein clusters; test H3.
- **Expected output**: `data/lanmodulin_genomes.csv`, `data/lanmodulin_xoxf_cooccurrence.csv`, `figures/lanmodulin_clade_restriction.png`

### NB06 — REE-AMD case study (local, ~3 min)
- **Goal**: characterize the 37 REE-AMD MAGs — taxonomy, dominant functional categories, presence/absence of the lanthanide-MDH cassette (only 4/37 have xoxF in pilot); contextualize the uncharacterized `f__REEB76` and acidophilic genera (Acidocella, Acidiphilium, Thiomonas, Metallibacterium).
- **Expected output**: `data/ree_amd_mag_profile.csv`, `figures/ree_amd_taxonomy.png`, `figures/ree_amd_functional_summary.png`

### NB07 — PQQ-supply asymmetry (Spark + local, ~5 min)
- **Goal**: characterize the ~2,300 xoxF-without-PQQ genomes — annotation gap (re-check via bakta `pqqA-E` products + interproscan PFAMs), pseudogenization (open reading frame / length sanity), or community-acquisition (co-occurrence with PQQ-bearing taxa in shared metagenomes via biosample/bioproject).
- **Expected output**: `data/xoxf_without_pqq.csv`, `figures/pqq_supply_asymmetry.png`

## Expected Outcomes
- **If H1 supported**: confirms the field's working hypothesis at unprecedented scale; positions BERDL as the reference resource for REE-utilization phylogenomics.
- **If H1 not supported**: identifies a hidden mxaF-dominant lineage; reframes the methylotrophy-evolution narrative.
- **If H2 supported**: produces a reusable cassette-completeness score for predicting REE-utilization potential from any new genome; useful for biorecovery candidate prioritization.
- **If H2 not supported**: suggests lanthanide-MDH presence is a phylogenetic accident decoupled from contemporary niche — interesting evolutionary question about ancestral cofactor preference.
- **If H3 supported**: tightens lanmodulin's clade boundary; provides a curated reference set for lanmodulin biochemistry/structural follow-up.
- **If H3 not supported**: identifies novel lanmodulin-bearing clades worth characterizing experimentally.
- **Potential confounders & limitations**:
  - **Phylogenetic non-independence** — handled with stratified (within-phylum / within-family) analysis and, where statistical power allows, mixed-effects logistic regression with family as a random effect. Headline H1 statistics will be reported both naive and phylogeny-controlled; both required to claim support.
  - **Annotation method variance** between eggNOG and bakta — handled by NB01 cross-validation and a "concordant-call" subset for the H1/H2 primary analyses; secondary "either-source" subset reported for robustness.
  - **REE-AMD anchor is small (n=37) and from a single bioproject** — used as a *descriptive* environmental anchor rather than a statistical test in NB04. H2 tests are powered by the broad `ncbi_env` regex on isolation-source-like fields plus AlphaEarth-based niche distance, not by the REE-AMD bioproject alone. NB06 treats the 37 MAGs as a case study with its own narrative; statistical claims are restricted to descriptive enrichments (Fisher's exact for cassette presence vs. matched-phylum baselines) with explicit small-N caveats.
  - **AlphaEarth's 39.5% coverage** on xoxF genomes leaves 60.5% without environmental coordinates. Two mitigations: (1) AlphaEarth-based environmental analyses are presented as a coverage-restricted *supplementary* axis to the `ncbi_env` text-mining primary analysis (mirroring the `amr_environmental_resistome` precedent); (2) coverage bias is reported per-clade so any genus-specific gaps are visible. AlphaEarth-restricted subset findings are not generalized to the full xoxF population without explicit caveat.
  - **`ncbi_env` coverage** is heterogeneous — many biosamples lack rich environmental metadata. NB04 reports the fraction of xoxF-genome biosamples with usable `ncbi_env` content alongside any environmental claims.

### Optional cross-validation with `metal_fitness_atlas` species scores
Where the metal_fitness_atlas species-level metal-tolerance scores (Co, Ni, Cu, Zn, etc.) overlap with lanthanide-cassette-bearing species, we will report Spearman correlation as a supplementary check. Hypothesis: lanthanide-cassette presence is largely *orthogonal* to existing transition-metal tolerance scores (different chemistry, different niches), so a near-zero correlation is the expected and supportive outcome. A strong positive correlation would indicate confounding by general metal-rich environments and would prompt re-examination of H2.

## Revision History
- **v1** (2026-04-30): Initial plan after pilot exploration confirmed all key quantitative inputs (3,690 xoxF genomes, 37 REE-AMD MAGs, 39.5% AlphaEarth coverage, eggNOG `lanM` false-positive caveat).
- **v2** (2026-04-30): Addressed `PLAN_REVIEW_1.md` feedback. Clarified Spark-session execution environment per notebook (JupyterHub-notebook idiom). Sharpened limitations on REE-AMD n=37 anchor (now treated as descriptive/case-study, not inferential) and AlphaEarth 39.5% coverage (now framed as coverage-restricted supplementary axis with coverage-bias reporting per-clade). Added optional cross-validation with `metal_fitness_atlas` species scores as a confounding check (orthogonality is the expected outcome).

## Authors
David Lyon (ORCID: [0000-0002-1927-3565](https://orcid.org/0000-0002-1927-3565)) — KBase
