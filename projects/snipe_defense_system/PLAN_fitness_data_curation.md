# Plan: Curating K. pneumoniae Fitness Data for SNIPE / ManYZ

## Motivation

Our SNIPE report identifies the ManYZ trade-off as the central evolutionary rationale
for SNIPE, but all fitness evidence comes from published E. coli literature. Meanwhile,
at least 5 genome-wide K. pneumoniae Tn-Seq datasets exist with downloadable fitness
scores. Curating these would let us answer:

1. **Does any K. pneumoniae Tn-Seq strain carry SNIPE?** (If yes, we have direct fitness data.)
2. **What are the ManYZ fitness phenotypes in K. pneumoniae?** (Essentiality, infection fitness.)
3. **Are ManYZ and SNIPE in the same defense island neighborhood?** (Genomic context.)
4. **How do ManYZ fitness effects compare across Enterobacterales?** (Pan-genome perspective.)

## Datasets to Curate

### Priority 0 — BERDL Fitness Browser (already loaded!)

The Deutschbauer/Price RB-TnSeq Fitness Browser is **already in BERDL** as
`kescience_fitnessbrowser`. This should be queried FIRST before downloading
external supplements.

| Table | Rows | Key columns |
|-------|------|-------------|
| `organism` | 48 | `orgId`, `genus`, `species`, `strain` |
| `gene` | 228,709 | `orgId`, `locusId`, `gene` (symbol), `desc` |
| `genefitness` | 27,410,721 | `orgId`, `locusId`, `expName`, `fit` (log2), `t` |
| `genedomain` | millions | `orgId`, `locusId`, `domainId` (Pfam accession) |
| `experiment` | 7,552 | `orgId`, `expName`, `expDesc`, `condition_1` |
| `ortholog` | millions | cross-organism BBH pairs |
| `cofit` | 13,656,145 | gene co-fitness correlations |

See full schema: `docs/schemas/fitnessbrowser.md`

**Queries to run** (all via BERDL REST API or Spark Connect):

```sql
-- Q1: Which organisms have manX/manY/manZ?
SELECT g.orgId, o.genus, o.species, g.locusId, g.gene, g.desc
FROM kescience_fitnessbrowser.gene g
JOIN kescience_fitnessbrowser.organism o ON g.orgId = o.orgId
WHERE g.gene IN ('manX', 'manY', 'manZ')

-- Q2: Any DUF4041/PF13250/PF13455 domains in any organism?
SELECT gd.orgId, gd.locusId, gd.domainId, gd.domainName, g.gene, g.desc
FROM kescience_fitnessbrowser.genedomain gd
JOIN kescience_fitnessbrowser.gene g ON gd.orgId = g.orgId AND gd.locusId = g.locusId
WHERE gd.domainId IN ('PF13250', 'PF13455', 'DUF4041')
   OR gd.domainName LIKE '%DUF4041%'

-- Q3: ManYZ fitness across ALL conditions (E. coli Keio + K. michiganensis)
SELECT g.orgId, g.gene, g.desc, gf.expName, e.expDesc, e.condition_1,
       CAST(gf.fit AS FLOAT) AS fitness, CAST(gf.t AS FLOAT) AS t_stat
FROM kescience_fitnessbrowser.genefitness gf
JOIN kescience_fitnessbrowser.gene g ON gf.orgId = g.orgId AND gf.locusId = g.locusId
JOIN kescience_fitnessbrowser.experiment e ON gf.orgId = e.orgId AND gf.expName = e.expName
WHERE g.gene IN ('manX', 'manY', 'manZ')
  AND CAST(gf.fit AS FLOAT) < -1
ORDER BY CAST(gf.fit AS FLOAT) ASC

-- Q4: ManYZ co-fitness partners (what genes track with ManYZ?)
SELECT g.orgId, g.gene AS query_gene, g2.gene AS cofit_gene, g2.desc,
       CAST(c.cofit AS FLOAT) AS cofit_score, c.rank
FROM kescience_fitnessbrowser.cofit c
JOIN kescience_fitnessbrowser.gene g ON c.orgId = g.orgId AND c.locusId = g.locusId
JOIN kescience_fitnessbrowser.gene g2 ON c.orgId = g2.orgId AND c.hitId = g2.locusId
WHERE g.gene IN ('manX', 'manY', 'manZ')
  AND CAST(c.rank AS INT) <= 20
ORDER BY g.gene, CAST(c.rank AS INT)

-- Q5: ManYZ orthologs across all 48 organisms
SELECT o.orgId1, g1.gene AS gene1, o.orgId2, g2.gene AS gene2, g2.desc, o.ratio
FROM kescience_fitnessbrowser.ortholog o
JOIN kescience_fitnessbrowser.gene g1 ON o.orgId1 = g1.orgId AND o.locusId1 = g1.locusId
JOIN kescience_fitnessbrowser.gene g2 ON o.orgId2 = g2.orgId AND o.locusId2 = g2.locusId
WHERE g1.gene IN ('manX', 'manY', 'manZ') AND g1.orgId = 'Keio'
```

**Expected value**: ManYZ fitness scores across hundreds of conditions in E. coli
and K. michiganensis, co-fitness partners, and orthologs across 48 organisms — all
without downloading anything. This is the Deutschbauer/Price dataset.

### Priority 1 — External K. pneumoniae Tn-Seq datasets (download required)

| ID | Study | Strain | Type | Data location | Format |
|----|-------|--------|------|---------------|--------|
| D1 | Ramage et al. 2017, J Bacteriol | KPNIH1 / MKP103 (ST258) | Tn5 arrayed library | [UW browser](https://tools.uwgenomics.org/tn_mutants/index.php) + [PMC supplements](https://pmc.ncbi.nlm.nih.gov/articles/PMC5637181/) | Excel (library catalog) |
| D2 | Bachman et al. 2015, mBio | KPPR1 / ATCC 43816 (hypervirulent K2) | Pooled Tn-Seq, mouse lung | [PMC Data Set S2](https://pmc.ncbi.nlm.nih.gov/articles/PMC4462621/) | XLSX (fitness ratios) |
| D3 | Short et al. 2024, eLife | ECL8 (K2-ST375) | TraDIS, >1M mutants | [eLife source data](https://elifesciences.org/articles/88971) | Excel (essential genes) |
| D4 | Bachman et al. 2025, mBio | KPPR1 + E. coli CFT073 + 3 others | Pan-genome Tn-Seq | [Zenodo](https://doi.org/10.5281/zenodo.15793688) | Mixed (Zenodo archive) |
| D5 | ATCC 43816 Galleria, 2025, Frontiers | ATCC 43816 | Tn-seq, insect model | Frontiers supplements | Excel |

### Priority 2 — E. coli phage-specific screens (for comparison)

| ID | Study | Strain | Type | Data location |
|----|-------|--------|------|---------------|
| D6 | Mutalik et al. 2020, PLoS Biol | E. coli K-12 BW25113/MG1655/BL21 | RB-TnSeq, 14 phages | [Figshare](https://figshare.com/articles/dataset/11413128) |
| D7 | Burmeister et al. 2021 | E. coli K-12 BW25113 | Keio knockouts + phage lambda coevolution | Published tables (PMID 34032565) |

### Priority 3 — Curated essentiality databases

| ID | Resource | URL | Notes |
|----|----------|-----|-------|
| D8 | OGEE v3 | https://v3.ogee.info | 91 species, may include K. pneumoniae |
| D9 | DEG 15 | http://essentialgene.org | 78 bacterial datasets, likely includes Klebsiella |

## Agentic Workflow

### Phase 0: Query BERDL Fitness Browser (no download needed)

Run queries Q1–Q5 above against `kescience_fitnessbrowser`. This gives us:

1. **ManXYZ across 48 organisms**: Which Fitness Browser organisms have manX/manY/manZ?
   How many conditions show fitness defects? What are the strongest phenotypes?
2. **SNIPE domain check**: Confirm whether any of the 48 organisms carry PF13250/PF13455
   (likely none, but must verify — `genedomain` table has Pfam annotations)
3. **Co-fitness partners**: What genes co-fitness with ManYZ? Are any defense-related?
4. **Cross-organism ManYZ orthologs**: How conserved is ManYZ across the 48 organisms?
5. **Condition-specific effects**: Does ManYZ show fitness defects specifically on
   mannose, glucosamine, or other PTS substrates? (Use `experiment.condition_1`)

Save results to `data/fitness/fitnessbrowser_manyz.csv`.

**Key advantage**: This is the same Price et al. dataset we cited in the report,
but we can now pull actual fitness scores rather than relying on literature summaries.
If ManYZ shows strong condition-specific defects (e.g., fit < -2 on mannose), that
directly quantifies the metabolic cost of losing the transporter.

### Phase 1: Download and inventory external datasets (automated)

For each Priority 1 dataset:

1. **Download** supplementary files (Excel/CSV) from PMC / eLife / Zenodo / Frontiers
2. **Parse** into a standardized schema:
   - `strain`, `locus_tag`, `gene_name`, `product`, `fitness_score`, `essentiality_call`, `condition`, `source_study`
3. **Check for SNIPE**: search each genome's annotation for DUF4041, PF13250, T5orf172
4. **Check for ManYZ**: search for manX, manY, manZ, ptsI, PTS_EIIC, PF02378, PF00358
5. **Save** standardized tables to `data/fitness/`

Expected outputs:
- `data/fitness/kpnih1_fitness.csv`
- `data/fitness/kppr1_lung_fitness.csv`
- `data/fitness/ecl8_tradis_essentials.csv`
- `data/fitness/pan_enterobacterales_fitness.csv`
- `data/fitness/atcc43816_galleria_fitness.csv`

### Phase 2: SNIPE presence check (critical gate)

For each K. pneumoniae strain (KPNIH1, KPPR1, ECL8, ATCC 43816):

1. **Get genome accession** from NCBI (RefSeq / GenBank)
2. **Search for PF13250 / IPR025280** using InterPro REST API or NCBI protein search
3. **Record result**: does this strain carry SNIPE? Y/N

This determines whether we have **direct SNIPE fitness data** (game-changer) or only
**ManYZ fitness data** (still valuable for the trade-off narrative).

### Phase 3: Extract and compare ManYZ fitness (core analysis)

1. **Pull ManYZ rows** from each standardized fitness table
2. **Compare across strains and conditions**:
   - Essential in LB? (baseline growth)
   - Fitness defect in mouse lung? (KPPR1)
   - Fitness defect in urine/serum? (ECL8)
   - Fitness defect in Galleria? (ATCC 43816)
3. **Cross-reference with E. coli phage data** (D6, D7)
4. **Build summary table** for the report:

   | Gene | E. coli K-12 (phage λ) | KPNIH1 (LB) | KPPR1 (lung) | ECL8 (serum) | ATCC 43816 (Galleria) |
   |------|----------------------|-------------|-------------|-------------|----------------------|
   | manX | Fitness defect on mannose | ? | ? | ? | ? |
   | manY | Zero phage growth | ? | ? | ? | ? |
   | manZ | 5 OOM reduction | ? | ? | ? | ? |
   | DUF4041 | N/A (not in K-12) | ? | ? | ? | ? |

### Phase 4: Genomic context (if SNIPE present)

If any K. pneumoniae strain carries SNIPE:

1. **Extract ±10 gene neighborhood** around the SNIPE locus
2. **Annotate neighbors**: defense genes? ManYZ? Other PTS?
3. **Pull fitness scores** for all neighbors
4. **Look for defense island signature**: co-localized defense genes with accessory/low-fitness profile

### Phase 5: Report integration

1. **Update REPORT.md** Finding 1 with K. pneumoniae-specific ManYZ fitness data
2. **Add new finding** if SNIPE is found in a Tn-Seq strain
3. **Create notebook** `05_fitness_data_curation.ipynb` documenting the full analysis
4. **Save comparison figures** to `figures/`

## Practical Considerations

### Data access
- PMC and eLife supplements: direct HTTP download (no auth)
- Zenodo: direct download (no auth)
- KPNIH1 browser: web scraping or direct query (public)
- OGEE/DEG: may require manual download if APIs are down

### Genome accessions (for SNIPE search)
- KPNIH1: GCF_000714575.1 (RefSeq)
- KPPR1 / ATCC 43816: GCF_000220485.1 (RefSeq)
- ECL8: search NCBI
- K. pneumoniae strains with known SNIPE (from UniProt): NCTC9140, HS11286

### Risks
- **SNIPE absent from all Tn-Seq strains**: Very likely given 86.7% accessory rate and
  bias toward laboratory/reference strains. Still valuable for ManYZ data.
- **ManYZ annotated under different names**: PTS nomenclature varies; search by Pfam
  (PF02378, PF00358) and COG in addition to gene name.
- **Fitness scores not comparable across studies**: Different methods (Tn5 vs TraDIS),
  conditions (LB vs lung vs serum), and metrics (fitness ratio vs essentiality call).
  Report each study's metric separately rather than merging into a single score.
- **Large Zenodo archive**: The 2025 pan-genome dataset may be large; download only
  the relevant fitness tables.

## Estimated Scope

| Phase | Effort | Parallelizable? | Depends on |
|-------|--------|-----------------|------------|
| Phase 0: BERDL Fitness Browser | Small (5 SQL queries) | — | API availability |
| Phase 1: Download + parse | Medium (5 datasets, varied formats) | Yes — each dataset independent | — |
| Phase 2: SNIPE presence | Small (4 InterPro API calls) | Yes | — |
| Phase 3: ManYZ extraction | Small (filter + compare) | After Phase 0+1 | Phase 0, 1 |
| Phase 4: Genomic context | Small-Medium (conditional) | After Phase 2 | Phase 2 |
| Phase 5: Report update | Small | After Phase 3-4 | Phase 3, 4 |

Phase 0 is the highest-value, lowest-effort step — it uses data already in BERDL
and can answer most of our questions about ManYZ fitness without any external downloads.

## Success Criteria

- [ ] All 5 Priority 1 datasets downloaded and parsed into standardized format
- [ ] SNIPE presence determined for all 4 K. pneumoniae strains
- [ ] ManYZ fitness scores extracted and compared across strains/conditions
- [ ] Summary table added to REPORT.md with K. pneumoniae-specific fitness data
- [ ] Provenance clear: each data point traceable to study, strain, and condition
