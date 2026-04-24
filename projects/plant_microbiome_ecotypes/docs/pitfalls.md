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

**Additional gotcha discovered 2026-04-24** (paired adversarial review, Phase 2b): even with the LIKE fix, `bakta_pfam_domains` **silently omits** some Pfam accessions that are widely detected by InterProScan on the same gene clusters. Verified in this pangenome build:

| Pfam | `bakta_pfam_domains` | `interproscan_domains` |
|---|---|---|
| PF00771 (T3SS inner rod) | 0 | **18,598** |
| PF01313 (T3SS PrgH) | 0 | **13,576** |

Likely cause: bakta uses a reduced Pfam HMM profile set (a "core" release) while InterProScan uses the full set. Do not interpret 0 hits in `bakta_pfam_domains` as domain absence — always cross-check `interproscan_domains` via `signature_acc` before drawing biological conclusions about missing functions.

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
