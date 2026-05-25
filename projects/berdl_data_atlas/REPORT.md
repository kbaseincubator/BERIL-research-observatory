# BERDL Data Atlas — Inventory, Topic Map, and Cross-Reference Synergies

**Status:** complete (analysis + one use case sample-validated).

## Executive summary

BERDL hosts **1,740 deduplicated tables across 119 databases, 17 tenants, and 10 funding agencies / programs**, covering 17 biological topics. The atlas finds:

1. **Depth is at the billion-row scale.** BERDL holds ~1.01 billion KBase pangenome genes (across 293K genomes / 27.7K species pangenomes), 241M AlphaFold predicted structures, 475M UniRef100 clusters, 261M MicrobeAtlas 16S OTU-count rows, 132.5M KBase gene clusters, 75M metatranscriptomic abundance rows, 27.4M FitnessBrowser measurements, 24.4M+15.7M viral sequence records, 40M PubMed records, plus reference layers for biochemistry, mass spec, growth phenotype, and environmental embeddings. See §Depth (NB05) for the full per-class breakdown.
2. **DOE dominates BERDL** at ~78% of tables (DOE-BER 63%, DOE BRaVE 14%, DOE/NSF 0.6%, DOE-FE 0.4%); ARPA-H (PROTECT) contributes 4%; NSF (Planet Microbe) 3.5%; DOI (USGS) and the academic / multi / user namespaces fill the rest. DOE-BER is the only agency covering all 15 biological topics.
3. **536 cross-tenant bridges** exist at the schema level, defined by 29 canonical join keys (`sample_id`, `genome_id`, `ncbi_taxon_id`, `feature_id`, `ec_number`, `kegg_pathway`, …).
4. **77% (51/66) of audited BERIL projects already span multiple tenants** — the lakehouse architecture is delivering on cross-program synergy. Realized use is concentrated on the `kbase × kescience` axis (36 projects).
5. **The five highest-leverage bridges had zero realized use at audit time**: `kescience ↔ refdata` (12 keys, including AlphaFold IDs), `enigma ↔ phagefoundry` (11), `kbase ↔ refdata` (11, including `gtdb_taxonomy`), `nmdc ↔ protect` (10), `nmdc ↔ refdata` (9). Five concrete use cases derived from these bridges are documented in NB04.
6. **UC1 (structural fitness atlas) has been sample-validated.** A first SQL probe against the live Spark Connect cluster confirmed the join path is executable and yields a working dataset of **55,454 FitnessBrowser genes across 48 organisms** with both fitness measurements AND an AlphaFold model. SwissProt-best-hit coverage is 99.5%. The use case is ready to scope as a standalone project.

The depiction was built for two audiences: KBase users who want to know "where to look for what" and funders / PIs evaluating cross-agency synergies. Both views are summarized in NB04 §3.

## Approach

The atlas was built in three layers, each delivered as a Jupyter notebook with saved outputs (audit-trail artifacts):

| Layer | Notebook | Output |
|---|---|---|
| Catalog + topic tagging | NB00 | `data/table_topic_map.csv` (1,740 rows) + `data/tenant_to_agency.csv` |
| Topic map (agency + concentration + synergy) | NB01 | 3 figures + topic concentration / synergy capacity tables |
| Linkage atlas (29 join keys, 536 bridges) | NB02 | `data/join_keys.json`, `data/cross_tenant_bridges.csv`, `data/join_key_coverage.csv` |
| Realized-use audit (66 projects) | NB03 | `data/realized_use.csv`, `data/theoretical_vs_realized.csv`, `data/untapped_bridges.csv` |
| Synthesis + 5 synergy use cases | NB04 | Composite atlas figure + use-case spec |
| Per-entity depth inventory (65 headline tables) | NB05 | `data/data_volume.csv`, two figures (per-class rollup + per-table) |

Supporting code lives in `src/`:
- `build_inventory.py` — parallel schema walker (16 workers, ~95 s for 1,740 tables). Filters out dotted-namespace duplicates the Spark Connect catalog exposes alongside legacy underscored names.
- `topic_tags.py` — ordered regex rules over `(db, table, columns)`, plus the tenant → agency / program / funder map.
- `data_volume.py` — curated `ENTITIES` list (~65 headline `(entity_class, table)` pairs) and a runner that issues `COUNT(*)` / `COUNT(DISTINCT)` per entry against the live Spark cluster.

## Key findings

### Inventory (NB00)

- **1,740 tables / 119 dbs / 17 tenants** is the canonical scale.
- A first walk reported 3,587 tables; the Spark Connect catalog exposes every Delta table under two names (`enigma.coral` AND `enigma_coral`). `walk_inventory()` now drops dotted duplicates by default.
- Topic-distribution highlights: `field_observational` 40%, `mobile_phage` 14%, `fitness_phenotype` 11%, `genome` 6.4%, then everything else <4%. Unclassified residual is 0.9% (16 rows), all personal-namespace / one-off survey data.

### Depth — what BERDL actually contains, in the units biologists think in (NB05)

The breadth-first views (tables, tenants, topics, bridges) understate how much *biological mass* lives in the lakehouse. NB05 hits 65 curated headline tables on the live cluster with `COUNT(*)` (or `COUNT(DISTINCT key)` where rows are repeated). Selected headlines:

**Genomes and pangenomes**
- 293,059 KBase pangenome genomes, organized into 27,690 species-level GTDB pangenomes
- 132,531,501 KBase pangenome gene clusters
- 1,011,650,903 KBase pangenome gene records (≈3.4K genes × 293K genomes on average)
- 1,158,553 SPIRE MAGs + 52,515 JGI GEM-MAGs in refdata
- 3,110 ENIGMA genomes (depot) + 6,705 ENIGMA SDT genomes
- 4,923 PROTECT MIND pathogen genomes
- ~1,950 PhageFoundry host genomes across 5 host species

**Proteins and structures**
- 215,130,942 UniProt proteins
- 475,217,233 UniRef100 / 188,848,220 UniRef90 / 60,315,044 UniRef50 clusters (2026-01)
- 241,070,489 AlphaFold predicted structures
- ~253K PDB experimental structures (refdata + kescience copies)

**Phenotype, fitness, growth**
- 27,410,721 FitnessBrowser per-gene fitness measurements across 7,552 experiments and 228,709 genes
- 97,334 BacDive strain phenotype profiles
- 57,302 globalusers carbon-source phenotype measurements
- 10,744 Web of Microbes growth observations across 37 organisms

**Field samples and environmental data**
- 463,972 MicrobeAtlas 16S samples (98,919 OTUs, 260,831,135 OTU-count rows)
- 114,943 USGS produced-water samples (curated + national)
- 16,640 NMDC biosamples
- 5,438 NETL produced-water DNA samples
- 4,346 ENIGMA SDT samples (plus 579 multidimensional DDT measurement 'bricks')
- 2,371 Planet Microbe samples
- 218,510 ENIGMA SDT ASVs
- 83,287 AlphaEarth environment embeddings indexed to KBase genomes

**Community-level multi-omics**
- 75,119,498 metatranscriptomic abundance rows (NMDC GOLD)
- 29,023,980 kraken + 482,669 gottcha taxonomic profile rows (NMDC GOLD)
- 9,928,244 NOM mass spec assignments (NMDC GOLD)

**Phage / virus / mobile**
- 24,435,662 MetaVR + 15,677,623 IMG/VR viral sequence records (refdata)
- 933,103 PhageFoundry strain-modelling gene records

**Biochemistry, ontology, literature**
- 56,012 ModelSEED reactions + 45,708 compounds + 17,783 Rhea reactions
- 48,196 GO terms + 8,813 EC terms (NMDC integrated)
- 255,096 PaperBLAST curated genes
- 39,994,988 PubMed article records

**Why this matters for the audience.** BERDL is not one deep dataset; it is **simultaneously deep across 10+ biological dimensions** — genome reference, computed pangenome, protein/structure reference, lab-derived phenotype, field-derived community profiles, geospatial environment, mass spec, viral genomes, biochemical reference, literature, ontology. Few biological data systems combine even three of those at this scale. The per-class rollup figure (`figures/nb05_volume_by_entity_class.png`) and per-table breakdown (`figures/nb05_volume_per_table.png`) make the diversity story visible at a glance.

### Topic map (NB01)

- **DOE-BER covers every topic.** ENIGMA contributes 601 `field_observational` tables; the rest is spread across KBase reference, KE Science phenotype, NMDC multi-omics, refdata reference.
- **Defense/HHS is mono-topic** (PhageFoundry, all `mobile_phage`) — high inbound-cross-reference potential.
- **Topic concentration**: highly concentrated topics are reference resources (`mobile_phage` 96% PhageFoundry, `pangenome` 79% kbase, `reference_protein` 78% refdata); cross-tenant topics are natural join surfaces (`taxonomy` 12 tenants, `genome` 8, `annotation` 8, `multiomics` 7).
- **Synergy capacity** (distinct topics × entropy): `kbase` (10 topics, 2.87 bits), `nmdc` (11, 2.61), `protect` (6, 2.37), `kescience` (11, 1.83) are the broadest anchors. `enigma` is deep-but-narrow (5 topics, 0.43 bits). `phagefoundry` and `usgs` are mono-topic.

### Linkage atlas (NB02)

- **29 canonical join keys** scanned across the catalog. Workhorses by tenant span: `sample_id` (10), `genome_id` (9), `ncbi_taxon_id` (9), `feature_id` (9), `ec_number` (8).
- **536 cross-tenant bridges** identified. Top bridges share up to 7 keys: `kbase.pathway ↔ kescience.pathway`, `kescience.pathway ↔ phagefoundry.mobile_phage`, `refdata.structural ↔ kescience.structural` (via `alphafold_pdb` + `protein_id` + `ncbi_taxon_id`).
- **Surprises:** `gtdb_taxonomy` appears in only 5 tables despite being the modern standard. `assembly_accession` / `gcf_gca` are refdata-only. `envo` ontology IDs are limited to NMDC + refdata; other field tenants use ad-hoc `isolation_source` strings.

### Realized-use audit (NB03)

- **66 BERIL projects audited** via README "Data Sources" mining; 4 excluded (`berdl_data_atlas`, `misc_exploratory`, plus 2 incomplete).
- **51 / 66 (77%) are already cross-tenant.** `kbase` is in 53/66, `kescience` in 35/66. `kbase ↔ kescience` is the dominant realized bridge (36 projects).
- **Heavy in BERDL ≠ heavy in reuse.** ENIGMA holds 36% of tables but is in 6 projects (9%). PhageFoundry holds 14% / 5 projects. PROTECT holds 4% / 2 projects.
- **Untapped high-key bridges**: see §Findings overview.

### Synthesis (NB04)

The composite atlas figure (`figures/nb04_atlas_composite.png`) shows tenant × topic heat plus per-tenant realized-reuse bars and the theory-vs-practice scatter on a single sheet.

**Five synergy use cases** derived from the top untapped bridges, each with motivating question + join recipe + payoff + audience message:

| UC | Bridge | Keys | Question | Sample-validated? |
|---|---|---|---|---|
| UC1 | kescience ↔ refdata | 12 | Do high-fitness-impact genes have structural signatures detectable in AlphaFold? | **Yes** — see §UC1 validation below |
| UC2 | enigma ↔ phagefoundry | 11 | Do subsurface prophages mobilize metal-resistance along the Oak Ridge contamination gradient? | not yet |
| UC3 | kbase ↔ refdata | 11 | Where do GTDB clades and KBase species pangenomes disagree, and what does that imply for gene flow? | not yet |
| UC4 | nmdc ↔ protect | 10 | Where do clinically relevant pathogens live in the environment, and what biogeochemistry tracks them? | not yet |
| UC5 | nmdc ↔ refdata | 9 | What fraction of NMDC biosamples carry well-formed ENVO ontology terms, and where does coverage break? | not yet |

### UC1 validation — sample-execution against the live Spark cluster (2026-05-24)

**Real join path discovered.** The proposed UC1 recipe pointed to `protein_id` as the bridge column, but FitnessBrowser does not expose `protein_id` — it uses a composite `(orgId, locusId)` key. The working bridge is:

```sql
genefitness  ──(orgId, locusId)── besthitswissprot  ──sprotAccession = uniprot_accession── alphafold_entries
```

i.e., FitnessBrowser's pre-computed SwissProt best-hit table mediates the join into AlphaFold via UniProt accession. AlphaFold model data lives in `kescience_alphafold` (not in `refdata`); the originally-claimed `refdata` participation comes via `refdata_uniprot.protein` and `refdata_pdb.pdb_uniprot_mapping`, both reachable from the same `uniprot_accession` pivot.

**Coverage measured against the live cluster:**

| Quantity | Value |
|---|---|
| FitnessBrowser gene-fitness measurements | 27,410,721 |
| Genes with SwissProt best-hit (`besthitswissprot`) | 79,180 |
| AlphaFold entries in `kescience_alphafold` | 241,070,489 |
| **SwissProt-best-hit coverage in AlphaFold** | **99.5% (78,753 of 79,180)** |
| Distinct AlphaFold models reachable | 32,858 |
| **Genes with BOTH fitness data AND an AlphaFold model** | **55,454** (across 48 organisms, 22,303 distinct AF models) |

**Semantic validity check.** A 10-row sample of E. coli Keio genes returned biologically coherent matches — `thrA` → `AF-P00561-F1` (aspartokinase I / homoserine dehydrogenase I), `thrB` → `AF-P00547-F1` (homoserine kinase), `thrC` → `AF-P00934-F1` (threonine synthase), `talB` → `AF-Q3Z606-F1` (transaldolase B). UniProt accessions are correct and the AlphaFold IDs follow the standard `AF-{uniprot}-F1` convention.

**Fitness distribution within the joined cohort** (min fitness across all conditions per gene; large negative = essentiality signal):

| Class | Genes | Avg. conditions tested |
|---|---|---|
| Essential (min_fit ≤ −4) | 6,635 | 187 |
| Strong defect (−4 < min_fit ≤ −2) | 8,271 | 170 |
| Moderate defect (−2 < min_fit ≤ −1) | 10,950 | 161 |
| Mild defect (−1 < min_fit < 0) | 29,467 | 121 |
| No defect (min_fit ≥ 0) | 131 | 15 |

The cohort is **strongly enriched for essentiality signal** — ~6.6K essential and ~8.3K strong-defect genes, each tested across an average of 170–190 conditions, with AlphaFold structures available. This is the dataset on which the proposed structural × phenotype analysis would be performed.

**What this validation establishes:**
- The cross-tenant join surface predicted by the linkage atlas is real and executable.
- Coverage is large enough for population-scale structure-function inference (not just anecdotal pairs).
- The join recipe needed correction (mediating table + composite key + actual UniProt pivot) that the schema-only atlas could not surface — this is exactly the "first sample-execution" pattern documented in NB04.

**What it does not establish:**
- AlphaFold structural-quality features (per-residue pLDDT, predicted TM-score, disorder fraction) are NOT in the `alphafold_entries` table — they would need to be derived from the actual PDB files or pulled from a structural-features table not yet present in BERDL. Adding that would either require ingest or a derived feature computation step.
- Whether structural features actually discriminate essential from non-essential genes (the UC1 question) — that is the downstream analysis, not validated here.

## What this atlas does not establish

- **Value-space validity of joins.** The bridge atlas proves the schema admits a join; it does not prove the value space overlaps. `genome_id` means different things in KBase (UPA), NCBI (accession), and MAG pipelines (hash). Each use case (UC1–UC5) requires a first sample-execution to confirm value-space overlap before publication. **UC1 has now been validated; UC2–UC5 remain pending.**
- **Agency provenance for remaining tenants.** `phagefoundry` and `msyscolo` have been corrected post-audit (DOE BRaVE and DOE/NSF respectively). `evaluation` and `lambda` are still not mapped (4 tables total). Verify with program documentation before external publication.
- **Audit completeness.** The realized-use audit was README-based; data-source mentions buried in research plans or referenced only in notebook source may have been missed. True per-project tenant breadth is a **lower bound**.

## Reproduction

**Prerequisites:** BERDL JupyterHub access with valid `KBASE_AUTH_TOKEN`. Python 3.11+ with `pandas`, `numpy`, `matplotlib`, `seaborn`, `networkx`, `berdl_notebook_utils` (already on JupyterHub).

```bash
# 1. Rebuild the catalog (~95 s; parallel Spark Connect schema walk)
python -m projects.berdl_data_atlas.src.build_inventory

# 2. Refresh the per-entity volume counts (~60 s, 65 COUNT queries against Spark)
python -c "
import csv, sys
sys.path.insert(0, 'projects/berdl_data_atlas/src')
from data_volume import collect_volumes
from berdl_notebook_utils import get_spark_session
rows = collect_volumes(get_spark_session())
with open('projects/berdl_data_atlas/data/data_volume.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=['entity_class','table','count_col','rows','label','error'])
    w.writeheader(); w.writerows(rows)
"

# 3. Re-execute the six notebooks in order
cd projects/berdl_data_atlas/notebooks
for nb in 00_inventory_audit 01_topic_map 02_linkage_atlas 03_realized_use_audit 04_synthesis_and_use_cases 05_data_volume; do
    jupyter nbconvert --to notebook --execute --inplace ${nb}.ipynb
done
```

Re-runs are idempotent against `data/realized_use.csv` (the project audit). To refresh the project audit, re-run the Explore-agent prompt in NB03's intro against `projects/`.

## Artifacts

**Data:**
- `data/table_topic_map.csv` — canonical inventory (1,740 rows; 11 columns including tenant, agency, program, primary_topic, secondary_topics, n_columns, column_names).
- `data/tenant_to_agency.csv` — manual tenant → agency / program / funder map.
- `data/join_keys.json` — `{key: [{tenant, topic, db, table}, …]}` for 29 canonical keys.
- `data/cross_tenant_bridges.csv` — 536 ranked (tenant×topic) bridge pairs with key inventory.
- `data/join_key_coverage.csv` — per-key coverage stats.
- `data/realized_use.csv` — 66 BERIL projects × tenants × databases × topic_focus.
- `data/theoretical_vs_realized.csv` — bridge overlay (72 tenant pairs).
- `data/untapped_bridges.csv` — 20 prioritized unrealized bridges.
- `data/tenant_reuse_frequency.csv` — per-tenant project count.
- `data/data_volume.csv` — 65 headline tables × `(entity_class, table, count_col, rows, label)` from NB05.

**Figures (12):** `figures/nb0[0-5]_*.png` — topic distribution, tenant×topic heatmap, agency×topic heatmap, topic concentration, synergy capacity, key×tenant heatmap, linkage graph, tenant frequency, theory vs realized scatter, composite atlas, per-entity-class volume rollup, per-headline-table volume.

**Notebooks (6):** `notebooks/0[0-5]_*.ipynb` — each with executed outputs as audit-trail artifacts.

## Data sources

The atlas is *about* BERDL itself; the canonical references for the tenants that contributed the data being catalogued — and the data sources sample-validated in UC1 — are:

| Collection | Reference |
|---|---|
| `kescience_fitnessbrowser` | Price M.N. et al. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature* 557, 503–509. PMID 29769710 |
| `kescience_alphafold` | Jumper J. et al. (2021). "Highly accurate protein structure prediction with AlphaFold." *Nature* 596, 583–589. PMID 34265844 |
| `refdata_uniprot` | The UniProt Consortium (2023). "UniProt: the Universal Protein Knowledgebase in 2023." *Nucleic Acids Research* 51, D523–D531. PMID 36408920 |
| `refdata_pdb` | Berman H.M. et al. (2000). "The Protein Data Bank." *Nucleic Acids Research* 28, 235–242. PMID 10592235 |
| `kbase_ke_pangenome` | Arkin A.P. et al. (2018). "KBase: The United States Department of Energy Systems Biology Knowledgebase." *Nature Biotechnology* 36, 566–569. PMID 29979655 |
| `nmdc_arkin` | Eloe-Fadrosh E.A. et al. (2022). "The National Microbiome Data Collaborative Data Portal: an integrated multi-omics microbiome data resource." *Nucleic Acids Research* 50, D828–D836. PMID 34850110 |
| `enigma_*` | Smith H.J. et al. (2024). "ENIGMA SFA — Subsurface Microbial Ecology in Contaminated Aquifers." (DOE-BER SFA program documentation) |
| `phagefoundry_*` | DOE BRaVE Phage Foundry program documentation (Defense and bioenergy applications) |
| `protect_*` | ARPA-H PROTECT program — pathogen genome catalog and MIND taxonomy classification |
| `planetmicrobe_*` | Hurwitz B.L. et al. (2020). "Planet Microbe — a marine and aquatic microbiome data discovery platform." NSF-funded; Planet Microbe consortium |

## Authors
- Adam Arkin (University of California, Berkeley, ORCID: 0000-0002-4999-2931)
