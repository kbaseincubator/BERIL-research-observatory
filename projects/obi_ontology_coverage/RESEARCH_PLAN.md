# Research Plan: OBI Ontology Coverage and Utilization in BERDL

## Research Question

How completely is OBI represented in the BERDL ontology store, and to what extent do NMDC and other DOE/LBL datasets actually use OBI terms for annotation — versus using free text, ad hoc identifiers, or terms from other ontologies where OBI terms would be more appropriate?

## Hypothesis

- **H0**: OBI terms are fully loaded and consistently used wherever applicable across BERDL datasets (i.e., there is no gap between availability and adoption).
- **H1**: OBI is loaded but underutilized — datasets use free text or inconsistent identifiers for concepts that OBI already defines (instruments, assay types, sample collection methods), representing missed annotation opportunities.

## Literature Context

OBI (Ontology for Biomedical Investigations) is an OBO Foundry ontology covering: experimental roles, instruments, assay types, sample collection devices, data transformations, and study designs. It is widely referenced in biomedical metadata standards (e.g., MIxS, NMDC schema) but actual adoption varies. The NMDC schema references OBI for fields like `samp_collect_device` and `seq_meth`, but submitter compliance is inconsistent.

Key references to review:
- OBI paper (Bandrowski et al., 2016) — ontology design and scope
- NMDC schema documentation — which fields recommend OBI terms
- MIxS checklists — OBI term recommendations for environmental genomics

## Preliminary Findings

Initial exploration (2026-04-03) revealed:

1. **OBI is fully loaded**: 4,422 labeled OBI terms in `kbase_ontology_source.statements`, defined by `obi-base.owl`, with 6,029 subClassOf triples and 2.8M entailed edges.
2. **OBI is used but sporadically in NMDC biosamples**:
   - `sample collection device` → `OBI:0003004` (3,018 samples)
   - `sequencing method` → `OBI_0002003` (2,901 samples, note: underscore instead of colon)
   - `collection_device` → `Virus Transport Medium [OBI:0002866]` (2,732)
   - `samp_source_mat_cat` → `environmental swab specimen [OBI:0002613]` (1,148)
3. **OBI is absent from env_triads** — the environment annotation table uses ENVO, UBERON, NCBITaxon, FOODON, and PO exclusively.
4. **Inconsistent formatting**: OBI terms appear as `OBI:0002003`, `OBI_0002003`, `OBI: 0002003`, and embedded in bracketed labels like `[OBI:0002866]`.

## Query Strategy

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `kbase_ontology_source.statements` | OBI term definitions, labels, hierarchy | ~millions | Filter by `subject LIKE 'OBI:%'` |
| `kbase_ontology_source.entailed_edge` | OBI class hierarchy (transitive closure) | 2.8M OBI-related | Filter by subject or object LIKE 'OBI:%' |
| `nmdc_ncbi_biosamples.biosamples_attributes` | Free-text sample metadata | large | Search content for OBI patterns |
| `nmdc_ncbi_biosamples.env_triads_flattened` | Structured environment annotations | ~20M | Check prefix column |
| `nmdc_ncbi_biosamples.biosamples_flattened` | Sample metadata with ontology fields | varies | Check env/method columns |
| `nmdc_arkin.annotation_terms_unified` | NMDC annotation ontology terms | varies | Check for OBI references |
| `kbase_phenotype.*` | Phenotype experiments | small | Check for OBI instrument/assay terms |
| `globalusers_phenotype_ontology_1.*` | Staging phenotype ontology | small | Check for OBI references |

### Key Queries

1. **OBI term census** — classify all 4,422 OBI terms by OBI branch (investigation, instrument, assay, etc.):
```sql
SELECT s1.subject, s1.value as label,
       s2.object as parent_class
FROM kbase_ontology_source.statements s1
JOIN kbase_ontology_source.statements s2
  ON s1.subject = s2.subject
WHERE s1.subject LIKE 'OBI:%'
  AND s1.predicate = 'rdfs:label'
  AND s2.predicate = 'rdfs:subClassOf'
  AND s2.object LIKE 'OBI:%'
```

2. **OBI usage across all NMDC biosample attributes** — comprehensive search:
```sql
SELECT attribute_name, 
       COUNT(*) as total_uses,
       COUNT(DISTINCT biosample_id) as distinct_samples
FROM nmdc_ncbi_biosamples.biosamples_attributes
WHERE content RLIKE 'OBI[:\\-_]\\d{7}'
GROUP BY attribute_name
ORDER BY total_uses DESC
```

3. **Free-text fields that COULD use OBI** — find instrument/method mentions without OBI IDs:
```sql
SELECT attribute_name, content, COUNT(*) as cnt
FROM nmdc_ncbi_biosamples.biosamples_attributes
WHERE attribute_name IN ('seq_meth', 'samp_collect_device', 'nucl_acid_ext', 'lib_const_meth')
  AND content NOT LIKE '%OBI%'
GROUP BY attribute_name, content
ORDER BY cnt DESC
```

4. **Cross-database OBI join** — resolve OBI IDs found in NMDC back to the ontology store:
```sql
SELECT ba.attribute_name, ba.content as nmdc_value,
       st.value as obi_label, st2.value as obi_definition
FROM nmdc_ncbi_biosamples.biosamples_attributes ba
JOIN kbase_ontology_source.statements st
  ON st.subject = REGEXP_EXTRACT(ba.content, '(OBI[:\\-_]\\d{7})', 1)
  AND st.predicate = 'rdfs:label'
JOIN kbase_ontology_source.statements st2
  ON st2.subject = st.subject
  AND st2.predicate = 'IAO:0000115'
WHERE ba.content RLIKE 'OBI[:\\-_]\\d{7}'
```

### Performance Plan

- **Tier**: JupyterHub (direct Spark)
- **Estimated complexity**: moderate — ontology tables are small, but biosamples_attributes is large
- **Known pitfalls**: String matching with regex on large tables; inconsistent OBI ID formatting

## Analysis Plan

### Notebook 1: OBI Census in the Ontology Store
- **Goal**: Characterize the 4,422 OBI terms by branch, depth, and annotation completeness
- **Expected output**: CSV of OBI terms with labels/branches, summary statistics, hierarchy visualization

### Notebook 2: OBI Usage Across BERDL Datasets
- **Goal**: Comprehensive survey of OBI term references across all BERDL databases
- **Expected output**: Usage matrix (which OBI terms x which databases/tables), consistency analysis

### Notebook 3: Gap Analysis and Cross-Database Joins
- **Goal**: Identify fields that should use OBI but don't; resolve OBI IDs to definitions via joins; compare OBI coverage to ENVO/UBERON adoption
- **Expected output**: Gap report, enrichment opportunities, cross-ontology comparison figures

## Expected Outcomes

- **If H1 supported**: Document specific gaps and inconsistencies; produce a concrete list of fields/datasets where OBI adoption could improve; compare BERDL's OBI utilization to the ontology's intended scope
- **If H0 not rejected**: OBI is well-adopted — document this as a positive finding and characterize the coverage pattern
- **Potential confounders**: Some OBI terms may be embedded in composite strings that regex misses; some datasets may use OBI indirectly through higher-level standards

## Revision History

- **v1** (2026-04-03): Initial plan based on exploratory queries

## Authors

- Mark Andrew Miller (ORCID: [0000-0001-9076-6066](https://orcid.org/0000-0001-9076-6066)), Lawrence Berkeley National Laboratory
