# Performance Notes — enigma_carbon_census_1

<!-- [enigma_carbon_census_1] 2026-06-09T15:55:14Z  approved-report extraction (REVIEW: REVIEW_2.md) -->

- Both NMDC covstats and Planet Microbe `taxonomy.name` are **species-level**; any genus-level abundance claim requires species→genus aggregation first. Filtering on bare genus names silently matches only near-zero genus-rank reference rows (the bug that first showed 0/68 marine genera). Any project doing genus-level abundance over `covstats_taxonomy_rollup` or Planet Microbe `run_to_taxonomy` needs this rollup.
- The NMDC abundance denominator is the set of covstats files that actually carry taxonomy (**3825**), not the larger `sample_file_lookup` row count (~6700) — using the lookup count deflates relative abundances by ~1.75×.
- Sample-level environment labels come from `nmdc_metadata.biosample_set` (joined to covstats `sample_id` via `kbase.nmdc_arkin.sample_file_lookup`), which gives 99% coverage across two ontologies — far better than `study_table` GOLD alone (~13%).
