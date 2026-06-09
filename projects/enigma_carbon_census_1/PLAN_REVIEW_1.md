# Plan Review — ENIGMA Carbon Census 1

**Reviewed**: 2026-06-09  
**Plan version**: v2 (2026-06-09)  
**Status at review**: `proposed`

---

**Overall**: A well-structured and methodologically mature plan — tiered evidence framework, compound-first execution order, and the Phase-1 stop-gate are all sound design choices; a few database naming discrepancies and schema implementation details need attention before notebooks run.

---

## Critical (likely to cause failures or wasted effort)

1. **SPIRE database name is wrong.** The plan lists `refdata_spire`, but live discovery shows the actual database name is `refdata.spire` (dot notation, not underscore). `get_tables('refdata_spire')` fails with `SCHEMA_NOT_FOUND`; `get_tables('refdata.spire')` returns an empty table list (database is listed but tables may need dot-notation SQL access: `FROM refdata.spire.tablename`). Verify the correct query syntax and table names for SPIRE before NB07.

2. **GenomeDepot annotation junction tables store FK IDs, not strings.** Live schema check confirms `browser_protein_kegg_reactions.kegg_reaction_id`, `browser_protein_kegg_orthologs.kegg_ortholog_id`, `browser_protein_kegg_pathways.kegg_pathway_id`, `browser_protein_ec_numbers.ec_number_id`, and `browser_protein_cazy_families.cazy_family_id` are all foreign keys to lookup tables (`browser_kegg_reaction`, `browser_kegg_ortholog`, etc.) — not the actual KO/EC/reaction strings. To get `K01234`-style KO names or EC numbers, a 3-hop join is required (e.g., `browser_protein_kegg_orthologs → browser_kegg_ortholog` to retrieve the actual identifier). Plan NB03/NB04 accordingly; all lookup tables exist in `enigma_genome_depot_enigma`.

3. **`kbase_nmdc_arkin` will fail; use `kbase.nmdc_arkin`.** The plan's context memory correctly notes `kbase.nmdc_arkin`, but if notebooks use the underscore form `kbase_nmdc_arkin`, they will get `SCHEMA_NOT_FOUND`. This is the NMDC multi-omics table referenced for environmental context in NB07. Use dot notation in SQL: `FROM kbase.nmdc_arkin.tablename`.

---

## Recommended (would improve the plan)

1. **GapMind Tier 2 coverage for this compound set will be near-zero — pre-verify in NB00.** GapMind catalogs ~50–60 curated carbon-source pathways (common sugars, amino acids, organic acids) against 293K genomes. The 83 target compounds are natural-product secondary metabolites (alkaloids, terpenoids, shikimates); essentially none will be in the GapMind catalog. The plan correctly flags this as a confounder but frames it as conditional ("if GapMind catalog not overlapping..."). Better framing: **Tier 2 via GapMind should be expected to contribute near-zero coverage** for this compound set; ModelSEED will carry all the Tier 2 weight. Add a GapMind catalog overlap check as the first step of NB02 so the stop-gate report can quantify this explicitly.

2. **Environmental arm of H3 (NB07) is limited by ENIGMA CORAL taxonomy resolution.** When linking genome_depot ENIGMA isolate predictions to ENIGMA field observations, the ENIGMA CORAL community data (`enigma_coral`) is currently available at genus level only — per the `enigma_contamination_functional_potential` project experience. H3 tests whether predicted-utilizer environmental abundance tracks compound source; this requires linking genome_depot strains to field ASV community data, which will resolve at genus level at best. Flag this precision limitation explicitly in the NB07 design and Expected Outcomes.

3. **`gapmind_pathways.metabolic_category` uses `'carbon'` and `'aa'`, not display names.** Confirmed pitfall: `WHERE metabolic_category = 'carbon_source'` or `'amino_acid'` returns 0 rows. Use `'carbon'` and `'aa'`. Also: `score_simplified` is binary (0.0/1.0), not a confidence score. Flag these in NB03 notebook comments.

4. **Short strain name collision risk for ENIGMA–pangenome bridge.** The plan correctly avoids the coarse genus-level bridge for deliverable (a) by mapping directly on genome_depot. However, if NB06 (phylo maps) places genome_depot strains on the GTDB tree via `browser_taxon.taxonomy_id` → pangenome join, the `[genotype_to_phenotype_enigma]` short-strain-name collision pitfall applies: ENIGMA short names can match unrelated NCBI genomes. Use assembly accession from `browser_genome.external_id` as the join key to `kbase_ke_pangenome.genome.genome_id` where possible; always cross-check genus after any NCBI-taxid-based join.

5. **JupyterHub kernel idle-timeout for NB07 (environmental atlas).** NB07 queries MGnify, SPIRE, NMDC, and Planet Microbe for implicated taxa — likely >30 minutes of Spark execution. The JupyterHub kernel silently dies after ~17–25 minutes of idle time (`[gene_function_ecological_agora]` pitfall). Consider converting long-running NB07 cells to a standalone `.py` script with `nohup` + checkpoint parquet writes.

---

## Optional (nice-to-have)

1. **README Quick Links still shows "(TBD)" next to Research Plan.** The plan exists now — remove the `*(TBD)*` annotation from that link.

2. **`browser_strain.taxon_id` is FK to `browser_taxon.id`, not `taxonomy_id`.** Confirmed via schema: `browser_strain.taxon_id → browser_taxon.id`; the NCBI taxid lives in `browser_taxon.taxonomy_id` and eggNOG taxid in `browser_taxon.eggnog_taxid`. The join chain is correctly described in the plan, but note this Django FK naming convention in notebook comments to avoid confusion.

3. **Spark DECIMAL → `decimal.Decimal` in pandas.** If GapMind or ModelSEED score columns are DECIMAL-typed, `.toPandas()` returns `decimal.Decimal` objects; arithmetic with floats raises `TypeError`. Use `CAST(col AS DOUBLE)` in SQL or `.astype(float)` after collection.

4. **Spark Connect temp views can be silently lost after heavy scans.** `[nmdc_community_metabolic_ecology]` documented this: Spark Connect drops registered temp views if the server reconnects during a long cell. In NB03 (organism mapping, 305M-row GapMind scan), re-register any temp views at the top of cells that JOIN against them.

---

## Relevant Pitfalls

- **Short Strain Names Collide Across Databases** [`docs/pitfalls.md`]: Applies to NB06 if bridging genome_depot ENIGMA strains to `kbase_ke_pangenome` via NCBI taxid. Use assembly accession matching; cross-check genus.
- **`gtdb_metadata` NCBI Taxid Column Returns Boolean Strings** [`docs/pitfalls.md`]: `gtdb_metadata.ncbi_taxid` stores `"t"`/`"f"`, not taxids — cannot use for pangenome joins. Use name-based or orgId-based matching.
- **Fitness Browser KO Mapping Is a Two-Hop Join** [`docs/pitfalls.md`]: Locus→KO path requires `genefitness → besthitkegg → keggmember`. Also: `genefitness.fit` is string-typed; cast to FLOAT before numeric comparisons.
- **`gapmind_pathways.metabolic_category` values** [`docs/pitfalls.md`]: Use `'carbon'` and `'aa'`, not display names.
- **`gapmind_pathways.clade_name` = `gtdb_species_clade_id` format** [`docs/pitfalls.md`]: Must use full `s__Genus_species--RS_GCF_...` format; short `GTDB_species` returns 0 rows.
- **`ncbi_env` Table is EAV format** [`docs/pitfalls.md`]: Must pivot from long to wide; 52% "Unknown" at genome level — use species-level majority-vote labels.
- **Spark DECIMAL Columns Return `decimal.Decimal`** [`docs/pitfalls.md`]: Wrap `AVG()` and DECIMAL columns in `CAST(... AS DOUBLE)`.
- **Spark Connect Temp Views Lost After Long-Running Cell** [`docs/pitfalls.md`]: Re-register temp views before cells that JOIN against them after heavy scans.
- **JupyterHub kernel idle-timeout silently kills long cells** [`docs/pitfalls.md`, `[gene_function_ecological_agora]`]: Plan nohup/.py fallbacks for any cell expected to run >20 min.
- **Species/strain bridge cannot be forced from genus-only ENIGMA CORAL taxonomy** [`docs/pitfalls.md`, `enigma_contamination_functional_potential` project]: CORAL field community data is genus-level; H3 environmental validation will be limited to genus-level association.
- **`eggnog_mapper_annotations.PFAMs` stores domain names, not accessions** [`docs/pitfalls.md`]: If Pfam domains are used in pangenome Tier-3 lookups, search by name (e.g., `'DUF4041'`), not accession (e.g., `'PF13250'`).

---

## Live Discovery Summary

All primary databases verified accessible:

| Database | Plan name | Actual name | Status |
|---|---|---|---|
| enigma_genome_depot_enigma | `enigma_genome_depot_enigma` | `enigma_genome_depot_enigma` | ✓ Accessible |
| KBase pangenome | `kbase_ke_pangenome` | `kbase_ke_pangenome` | ✓ Accessible |
| Fitness Browser | `kescience_fitnessbrowser` | `kescience_fitnessbrowser` | ✓ Accessible |
| MGnify | `kescience_mgnify` | `kescience_mgnify` | ✓ Accessible |
| SPIRE | `refdata_spire` | `refdata.spire` | ⚠ Name mismatch — verify |
| NMDC metadata | `nmdc_metadata` | `nmdc_metadata` | ✓ Accessible |
| NMDC results | `nmdc_results` | `nmdc_results` | ✓ Accessible |
| NMDC BioSamples | `nmdc_ncbi_biosamples` | `nmdc_ncbi_biosamples` | ✓ Accessible |
| NMDC Arkin | `kbase.nmdc_arkin` | `kbase.nmdc_arkin` | ✓ Accessible (dot notation required) |
| Planet Microbe | `planetmicrobe` | `planetmicrobe.planetmicrobe` | ✓ Accessible |

**GenomeDepot schema confirmed**: `browser_taxon.taxonomy_id`, `browser_taxon.eggnog_taxid`, `browser_taxon.name` all exist exactly as named in the plan ✓. All annotation junction tables (`browser_protein_kegg_reactions`, `_kegg_pathways`, `_kegg_orthologs`, `_ec_numbers`, `_cazy_families`) exist ✓. Lookup tables for string identifiers (`browser_kegg_ortholog`, `browser_kegg_reaction`, `browser_kegg_pathway`, `browser_ec_number`, `browser_cazy_family`) also confirmed present ✓.

---

## Overlap Check

No significant duplication with existing projects:
- `genotype_to_phenotype_enigma` uses overlapping data sources (genome_depot, FB, CORAL) but answers a different question (phenotype prediction). Its ENIGMA strain list and FB anchor join recipe are useful references for Tier 1.
- `aromatic_catabolism_network`, `pseudomonas_carbon_ecology` — topically adjacent but different organisms/questions; complementary.
- `metabolic_capability_dependency`, `pangenome_pathway_geography` — both use GapMind at scale; their cached extraction outputs could reduce re-query time in NB03 if reusable.

---

Plan reviewed by Claude (claude-sonnet-4-6).
