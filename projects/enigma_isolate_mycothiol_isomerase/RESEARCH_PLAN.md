# Research Plan: ENIGMA Isolate Survey for Mycothiol-Dependent Malonylpyruvate Isomerase

## Research Question

Which ENIGMA lab isolates carry the mycothiol-dependent malonylpyruvate isomerase,
and are any of those isolates tractable for experimental testing of adaptive metal
function?

## Hypothesis

- **H0**: No ENIGMA isolates carry the malonylpyruvate isomerase, consistent with the
  enzyme being restricted to environmental Actinomycetota not represented in culture.
- **H1**: One or more ENIGMA isolates carry the enzyme, providing a tractable system
  for experimental validation of its role in metal adaptation.

## Scientific Context

The `mycothiol_detox_module` project established that malonylpyruvate isomerase and
S-(hydroxymethyl)mycothiol dehydrogenase are present in ~71% of Actinomycetota but
<1% of Pseudomonadota and Bacillota. Subsequent phylogenetically corrected enrichment
analysis confirmed the isomerase as the most robust Actinobacteria-specific signal
after subsampling to one genome per genus.

The ENIGMA program cultivates and genomes bacterial isolates from metal-contaminated
Oak Ridge Field Research Center sites. These isolates represent organisms that have
adapted to chronic metal exposure over decades, making them compelling candidates for
experimental validation of the isomerase's adaptive function.

## Approach

### NB01: Enigma Genome Depot Query (`01_enigma_depot_query.ipynb`)

**Goal**: Identify all ENIGMA isolate genomes carrying malonylpyruvate isomerase annotations.

**Steps**:
1. Connect to `enigma.genome_depot_enigma` via BERDL Spark.
2. Pull all gene annotation records; filter on:
   - Product name containing "malonylpyruvate isomerase" or "malylpyruvate isomerase"
   - InterPro domain: IPR013785 (aldolase-type TIM barrel, used by maleylpyruvate isomerase family)
   - KEGG orthology: K01800 (maleylpyruvate isomerase) or related
3. Cross-reference hits against `kbase.ke_pangenome` annotation vocabulary to ensure
   consistent search terms.
4. Pull genome metadata for each hit: NCBI taxonomy, genome completeness, isolation
   site/condition.
5. Export: `data/enigma_isomerase_hits.tsv`

**Expected output columns**: `genome_id`, `gene_id`, `product`, `taxon`, `phylum`,
`isolation_site`, `checkm_completeness`, `checkm_contamination`

### NB02: Candidate Ranking (`02_candidate_ranking.ipynb`)

**Goal**: Merge gene hits with Jen's canonical ENIGMA isolate list and rank by
experimental tractability.

**Steps**:
1. Load `data/enigma_isomerase_hits.tsv`.
2. Merge with Jen's isolate list (genome ID or strain name match).
3. Prioritize candidates by:
   - Gene present (binary, required)
   - Genome completeness ≥ 90%
   - Isolate available as frozen stock (from Jen's list)
   - Metal tolerance phenotype documented (if any)
   - Actinobacteria lineage confirmed
4. Output ranked table: `data/candidate_isolates_ranked.tsv`
5. Generate summary figure: `figures/candidate_summary.png`

## Data Sources

| Source | Table/File | Purpose |
|---|---|---|
| Enigma Genome Depot | `enigma.genome_depot_enigma` | Isolate genomes and gene annotations |
| KBase pangenome | `kbase.ke_pangenome.eggnog_mapper_annotations` | Annotation vocabulary cross-reference |
| Jen's isolate list | Provided externally | Canonical list of cultured ENIGMA strains |

## Expected Outputs

- `data/enigma_isomerase_hits.tsv` — all gene hits in ENIGMA genomes
- `data/candidate_isolates_ranked.tsv` — ranked experimental candidates
- `figures/candidate_summary.png` — visualization of candidates by taxon and site

## Decision Criteria for Experimental Follow-up

A candidate isolate is prioritized for experimental testing if it meets all three:
1. Carries malonylpyruvate isomerase with ≥2 annotation lines of evidence
2. Genome completeness ≥ 85%
3. Available as a cultured stock (confirmed via Jen's list)

## Known Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Annotation vocabulary mismatch (isomerase named differently in Genome Depot) | Search by InterPro domain in addition to product name |
| No hits (enzyme absent from all ENIGMA isolates) | Report negative result; cross-reference with NCBI GenBank Actinobacteria isolates as fallback |
| Jen's list not available in machine-readable form | Request TSV or spreadsheet export; manually merge if needed |
| Gene present but non-functional (truncated/pseudogene) | Flag genes < 80% median length as suspect |

## Timeline

- Query design and NB01 execution: before June 30, 2026
- Isolate list merge and NB02: after receiving Jen's list
- Final candidate shortlist to Adam: July 2026

## Authors

- Heather MacGregor, Lawrence Berkeley National Laboratory
