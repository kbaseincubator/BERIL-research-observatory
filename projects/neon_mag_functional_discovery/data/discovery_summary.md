# Discovery Probe Results (2026-05-21)

These are the BERDL probe results that bounded the project scope. All counts are live from the NMDC and KBase tenants on the date above.

## Confirmed studies

```sql
SELECT id, title FROM nmdc_metadata.study_set
WHERE lower(title) LIKE '%national ecological observatory%' OR lower(title) LIKE '%neon%';
```

Five hits; three are the analysis targets:

| Study ID | Title |
|---|---|
| `nmdc:sty-11-34xj1150` | NEON: soil metagenomes (DP1.10107.001) |
| `nmdc:sty-11-hht5sb92` | NEON: surface water metagenomes (DP1.20281.001) |
| `nmdc:sty-11-pzmd0x14` | NEON: benthic metagenomes (DP1.20279.001) |

Plus two umbrella records (`nmdc:sty-11-nxrz9m96` "NEON" parent, `nmdc:sty-11-wyvany77` "NEON Contract FY24"), not used directly.

## Biosamples per study

| Study | Biosamples | With omics processing |
|---|---|---|
| Soil | 6,489 | 4,436 |
| Water | 234 | 192 |
| Benthic | 736 | 560 |

## Omics types — metagenomics only

`data_generation_set.type` for all three studies = `nmdc:NucleotideSequencing` only. No `nmdc:MassSpectrometry` / `nmdc:Metatranscriptomics` / etc. Confirmed against `nmdc_arkin.omics_files_table` — only metagenome workflow types appear (MagsAnalysis, MetagenomeAnnotation, MetagenomeAssembly, ReadBasedTaxonomyAnalysis, ReadQcAnalysis). All `nmdc_arkin` _gold tables (metaT/metaP/metabolomics/lipidomics/NOM) return zero NEON rows.

## Biosample field coverage (≥ 5% in any habitat)

Fields with non-null values, percentage of biosamples populated:

| Field | Soil | Water | Benthic |
|---|---|---|---|
| `lat_lon_latitude`, `lat_lon_longitude`, `elev`, `depth`, `collection_date`, `geo_loc_name`, `env_broad/local/medium_term_id+name`, `env_package`, `analysis_type`, `name` | 100% | 100% | 100% |
| `temp` | 97% | 95% | 0% |
| `ph` | 97% | 0% | 0% |
| `samp_collec_device` | 95% | 81% | 0% |
| `water_content` | 84% | 0% | 0% |
| `soil_horizon` | 100% | 0% | 0% |
| `ecosystem` / `ecosystem_type` / `specific_ecosystem` | 80% | 18% | 24% |
| `biosample_categories` | 68% | 82% | 76% |
| `img_identifiers` | 58% | 18% | 24% |
| `org_carb` | 32% | 0% | 0% |
| `tot_nitro_content` | 29% | 0% | 0% |
| `ammonium_nitrogen` | 29% | 0% | 0% |
| `carb_nitro_ratio`, `nitro` | 21% | 0% | 0% |
| `conduc` | 0% | 77% | 0% |
| `diss_oxygen` | 0% | 75% | 0% |
| `samp_size` | 0% | 82% | 60% |
| `dna_isolate_meth`, `experimental_factor*` | 0% | 18% | 24% |

Full per-field counts in `biosample_field_coverage.json` (gitignored; regenerable from NB01).

## MAG counts by quality and domain

From `workflow_execution_set_mags_list` joined via study → data_generation → workflow chain:

| Habitat | LQ | MQ | HQ | Bacteria (MQ+HQ) | Archaea (MQ+HQ) | Eukaryotic-credible (eval ≥ 50%) |
|---|---|---|---|---|---|---|
| Soil | 4,032 | 1,067 | 110 | 1,137 | 40 | 10 |
| Water | 448 | 95 | 15 | 110 | 0 | 0 |
| Benthic | 1,209 | 244 | 78 | 322 | 0 | 4 |

GTDB species-level calls (any quality): soil 19, water 12, benthic 4 distinct species. Most MAGs are classified only at genus or higher rank; ~75% of soil MAGs have no genus assignment.

## Functional annotation coverage

`nmdc_metadata.functional_annotation_agg` (workflow-level KO/COG/Pfam counts):

| Habitat | Workflows | Annotation rows | Distinct functions |
|---|---|---|---|
| Soil | 1,895 | 18,284,280 | 35,013 |
| Water | 102 | 773,864 | 27,958 |
| Benthic | 645 | 8,045,141 | 34,786 |

ID prefix distribution (soil): PFAM 6.6M rows / 14,824 terms; KEGG.ORTHOLOGY 6.4M / 15,558; COG 5.3M / 4,631.

Per-gene tables exist (`nmdc_results.annotation_kegg_orthology` 1.83 billion rows; `pfam_annotation_gff` 2.68 billion rows) but are too large for casual joins. Use only for targeted gene hunts after Hypothesis 2/4 narrows candidates.

## Pangenome linkability

`kbase_ke_pangenome.gtdb_species_clade` has 27,690 species. Genus-level overlap (after `split(replace(GTDB_species,'s__',''), '_')[0]` to extract genus):

- 412 distinct genera in NEON MQ+HQ MAGs (excluding null)
- **249 (60%)** have at least one KE pangenome species representative
- Overlapping genera include both clinical-cultured (Mycobacterium 186 pangenome species, Bradyrhizobium, Rhizobium, Sphingomonas) and environmental groups (Palsa-295, Bog-1198, Sulfotelmatobacter, JAAFIP01, UBA8403)

Direct species-level match (`gtdbtk_species` = `replace(GTDB_species,'s__','')`): only ~33 NEON MAGs have species-level GTDB calls, so species-level pangenome anchor is too thin. **Genus-level is the productive layer.**

## Inputs to the project

All discovery results above are reproducible from `notebooks/01_discovery_and_sample_design.ipynb` (planned). No external data is required.
