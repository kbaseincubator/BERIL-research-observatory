# Pitfalls & Gotchas

Documented issues encountered during this project that future analyses should watch for.

## Versioned Pfam IDs in `bakta_pfam_domains`

`kbase_ke_pangenome.bakta_pfam_domains.pfam_id` stores **versioned** Pfam accessions (e.g., `PF00771.22`, `PF13629.12`) rather than bare accessions (`PF00771`, `PF13629`).

**Symptom**: `WHERE pfam_id IN ('PF00771', 'PF01313', ...)` returns 0 rows even though the domains exist in the table. This caused NB02 to miss all Pfam hits.

**Workarounds**:
- Use `LIKE` with the bare ID followed by `%`:
  ```sql
  WHERE pfam_id LIKE 'PF00771%' OR pfam_id LIKE 'PF01313%' ...
  ```
- Or query the InterProScan table instead, which stores bare accessions:
  ```sql
  SELECT signature_acc FROM kbase_ke_pangenome.interproscan_domains
  WHERE signature_acc IN ('PF00771', 'PF01313')
  ```

**Where fixed**: NB13 Cell 3 (`pfam_recovery_hits.csv`). NB02 documented as limitation in REPORT.md §Limitations.

**Additional gotcha discovered 2026-04-24** (paired adversarial review, Phase 2b): even with the LIKE fix, `bakta_pfam_domains` **silently omits** many Pfam accessions that are widely detected by InterProScan on the same gene clusters.

**Full audit, 2026-04-25** (`data/pfam_bakta_ips_audit.csv`): of the 22 marker Pfam accessions queried by this project across NB02 and NB10, **12 are completely absent from `bakta_pfam_domains` despite being abundant in `interproscan_domains`**:

| Pfam | Description (project) | IPS hits | IPS species | Bakta hits |
|---|---|---:|---:|---:|
| PF01312 | (T3SS-related) | 21,954 | 10,225 | **0** |
| PF00771 | T3SS inner rod (PrgJ) | 18,598 | 10,207 | **0** |
| PF03743 | TrbI / VirB10 (T4SS) | 17,488 | 4,733 | **0** |
| PF02579 | (T3SS-related) | 16,847 | 7,549 | **0** |
| PF04610 | T3SS HrpB7 | 15,625 | 4,337 | **0** |
| PF01514 | Secretin (T2SS/T3SS) | 15,039 | 10,094 | **0** |
| PF01313 | T3SS PrgH | 13,576 | 10,088 | **0** |
| PF03135 | VirB8 (T4SS) | 11,016 | 3,927 | **0** |
| PF07916 | (T3SS-related) | 8,379 | 2,315 | **0** |
| PF04183 | (T6SS-related) | 7,530 | 2,718 | **0** |
| PF05936 | Hcp (T6SS tube) | 7,465 | 3,379 | **0** |
| PF09599 | (T3SS-related) | 292 | 156 | **0** |

The pattern: **secretion-system Pfams (T3SS, T4SS, T6SS) are systematically missing from `bakta_pfam_domains`** but present in `interproscan_domains`. The 10 Pfams that are present in bakta (PF00857, PF00150, PF00148, PF00295, PF12708, PF05943, PF00142, PF00544, PF01670, PF07201) are mostly nitrogen fixation, CWDE, and a few miscellaneous; bakta returns ~10–35% of the IPS hit count for these, also undercounting but at least non-zero.

Likely cause: bakta uses a reduced Pfam HMM profile set (e.g., the "core" or "trimmed" release) while InterProScan uses the full Pfam-A set. The omitted Pfams skew systematically toward the larger HMM families used in secretion systems.

**Operational consequence**: do not query `bakta_pfam_domains` for any Pfam accession without cross-checking `interproscan_domains.signature_acc` first. NB10's pipeline correctly uses `interproscan_domains` for T3SS/T4SS/T6SS marker detection and is unaffected; Phase 1 NB02's bakta-only Pfam query returned zero hits and the cohort pipeline fell back to gene-name matching, which is also unaffected. Future BERDL projects should treat `bakta_pfam_domains` as an opt-in supplement, not a primary Pfam source.

## Genome ID prefix mismatch between phylogenetic tree and environment tables

`kbase_ke_pangenome.phylogenetic_tree_distance_pairs.genome1_id`/`genome2_id` returns **bare NCBI accessions** (e.g., `GCA_005059785.1`, `GCF_001274215.1`), while `genome_environment.csv` (derived from `genome` / `ncbi_env`) uses **GTDB-prefixed** IDs: `GB_GCA_005059785.1` and `RS_GCF_001274215.1`.

**Symptom**: Merging subclade assignments onto genome environment produced 0 matches in NB12. Plant-association column came back entirely NaN, yielding a false null result for H7.

**Workaround**: prepend `GB_` for `GCA_` accessions and `RS_` for `GCF_` accessions before merging:

```python
def fix_genome_id(gid):
    if gid.startswith('GCA_'): return 'GB_' + gid
    if gid.startswith('GCF_'): return 'RS_' + gid
    return gid
subclades['genome_id_fixed'] = subclades['genome_id'].apply(fix_genome_id)
```

**Where fixed**: NB13 Cell 4 (`subclade_enrichment_corrected.csv`). With the fix, 1306/1306 (100%) of subclade genomes match environment IDs and H7 is revised from "not supported" to "partially supported" (2/5 species significant).

## Max-aggregation of species → genus GapMind inflates pathway completeness

In NB06, genus-level GapMind completeness was computed as `max(complete)` across constituent species. This marks a pathway as "present" in a genus if **any** species has it, regardless of how prevalent it is. For complementarity analysis this produced an implausibly large Cohen's d of −7.54 for co-occurring vs random genus pairs.

**Workaround**: use the **fraction of species** with the pathway (prevalence) and compute asymmetric gaps as continuous products instead of set differences:

```python
p1 = prev_vector_genus_A   # in [0,1]
p2 = prev_vector_genus_B
a_to_b = (p1 * (1 - p2)).sum()
b_to_a = (p2 * (1 - p1)).sum()
complementarity = a_to_b + b_to_a
```

**Where fixed**: NB14 Cell 5 (`complementarity_v2.csv`). Cohen's d becomes −0.39 — direction unchanged (redundancy still dominant) but magnitude is now credible.

## Genus-level fixed-effects logit does not converge with 25K species

NB10 tried statsmodels `Logit(marker ~ is_plant + genus_dummies)` with ~2000 genus dummies across 25,660 species. All 14 models failed to converge (quasi-separation, singular matrix).

**Workaround**: use L1-regularized (`penalty='l1', solver='saga'`) scikit-learn `LogisticRegression` with top-N genus dummies and bootstrap CI on the `is_plant` coefficient. With N=20 top genera and 100 bootstraps, 9/17 markers produce CIs that exclude zero.

**Where fixed**: NB14 Cell 2 (`regularized_phylo_control.csv`).

## `species_compartment.csv` column name is `dominant_compartment`, not `compartment`

The `species_compartment.csv` summary file uses `dominant_compartment` as the majority-vote column. Downstream scripts that use `sp_comp['compartment']` will fail with KeyError. The per-genome `genome_environment.csv` does have `compartment`.

## `kbase_ke_pangenome.phylogenetic_tree_distance_pairs` is sparse — most species have no tree

Discovered 2026-04-25 during the full 65-species subclade scan (`notebooks/_run_subclade_full_scan.py`). Of 65 plant-associated species with ≥20 genomes in this project, only **18 (28%)** have any pairwise phylogenetic-distance data in `phylogenetic_tree_distance_pairs`. The other 47 species — including major plant-associated taxa such as *Bradyrhizobium japonicum*, *B. diazoefficiens*, *Mesorhizobium ciceri*, *Sinorhizobium medicae*, *Burkholderia glumae*, *Methylobacterium extorquens*, *Streptomyces scabiei*, *Xylella taiwanensis*, *Clavibacter michiganensis*, *Pectobacterium parmentieri*, *Bacillus_A cereus_U*, *Pseudomonas_E brassicacearum* — return zero rows when their `gtdb_species_clade_id` is queried.

**Operational consequence**: any analysis that requires within-species phylogenetic structure (subclade clustering, MDS embeddings, host-specificity-by-clade tests, intra-species ANI patterns) will silently exclude ~70% of plant-associated species. Always pre-check coverage before drawing conclusions about lineage-level patterns:

```python
# Audit phylo coverage for a target species set
spark.sql(f"""
    SELECT pt.gtdb_species_clade_id, COUNT(*) AS n_pairs
    FROM kbase_ke_pangenome.phylogenetic_tree pt
    JOIN kbase_ke_pangenome.phylogenetic_tree_distance_pairs pd
         ON pd.phylogenetic_tree_id = pt.phylogenetic_tree_id
    WHERE pt.gtdb_species_clade_id IN (...)
    GROUP BY pt.gtdb_species_clade_id
""")
```

This is a **database-coverage limitation**, not a methodological bug. It bounds the power of any subclade-level hypothesis (H7 in this project) to the species that happen to have trees built. Worth flagging to the BERDL data team if more thorough phylogenetic coverage is feasible.
