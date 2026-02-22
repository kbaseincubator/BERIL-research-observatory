# PaperBLAST Module

## Overview
PaperBLAST links protein sequences to scientific literature by identifying mentions of genes/proteins in published papers. It maps genes to papers through text mining of PubMed Central (PMC) full-text articles, curated databases (SwissProt, BRENDA, etc.), and GeneRIF annotations. Also includes PDB binding site and ligand data for structural context.

**Database**: `kescience_paperblast`
**Generated**: 2026-02-22
**Source**: [PaperBLAST](https://papers.genomics.lbl.gov/) (Price & Arkin, mSystems 2017)

## Tables

| Table | Rows | Description |
|-------|------|-------------|
| `genepaper` | 3,195,890 | Gene-to-paper associations (text-mined from PMC) |
| `gene` | 1,135,366 | Gene/protein entries with organism and description |
| `snippet` | 1,951,949 | Text snippets from papers mentioning each gene |
| `paperaccess` | 274,899 | Paper access status (full-text availability in PMC) |
| `curatedgene` | 255,096 | Curated gene entries from SwissProt, BRENDA, etc. |
| `curatedpaper` | 599,587 | Curated gene-to-paper associations |
| `seqtoduplicate` | 284,104 | Sequence ID cross-references (maps between databases) |
| `site` | 2,089,192 | Protein binding/active/modified sites from PDB |
| `hassites` | 146,190 | PDB chains with site annotations |
| `seqhassite` | 146,195 | Sequence-to-PDB chain mappings (via hash) |
| `pdbligand` | 48,991 | PDB ligand identifiers and names |
| `pdbclustinfo` | 67,528 | PDB cluster descriptions |
| `generif` | 1,358,798 | Gene Reference Into Function (GeneRIF) annotations |
| `uniq` | 815,571 | Unique protein sequences with full amino acid sequence |

## Key Table Schemas

### genepaper
Links genes to papers via text mining of PMC full-text.
| Column | Type | Description |
|--------|------|-------------|
| `geneId` | string | Gene/protein accession (e.g., NP_010242.1, WP_002987892.1) |
| `queryTerm` | string | Search term used to find the gene in literature |
| `pmcId` | string | PubMed Central ID (e.g., PMC3553284) |
| `pmId` | string | PubMed ID |
| `doi` | string | Digital Object Identifier |
| `title` | string | Paper title |
| `authors` | string | Author list |
| `journal` | string | Journal name |
| `year` | string | Publication year (string — CAST to INT for comparisons) |
| `isOpen` | int | Whether paper is open access (mostly NULL) |

### gene
Gene/protein metadata.
| Column | Type | Description |
|--------|------|-------------|
| `geneId` | string | Gene/protein accession |
| `organism` | string | Source organism name |
| `protein_length` | int | Protein length in amino acids |
| `desc` | string | Protein description/function |

### snippet
Text excerpts from papers mentioning genes.
| Column | Type | Description |
|--------|------|-------------|
| `geneId` | string | Gene/protein accession |
| `queryTerm` | string | Search term used |
| `pmcId` | string | PMC ID |
| `pmId` | string | PubMed ID |
| `snippet` | string | Text snippet from paper mentioning the gene |

### curatedgene
Genes with curated functional annotations from reference databases.
| Column | Type | Description |
|--------|------|-------------|
| `db` | string | Source database (SwissProt, CharProtDB, BRENDA, etc.) |
| `protId` | string | Protein accession in source database |
| `id2` | string | Secondary identifier |
| `name` | string | Gene name |
| `desc` | string | Functional description |
| `organism` | string | Source organism |
| `protein_length` | string | Protein length (string — CAST for numeric ops) |
| `comment` | string | Detailed functional annotation/comments |

### curatedpaper
Links curated gene entries to their supporting PubMed references.
| Column | Type | Description |
|--------|------|-------------|
| `db` | string | Source database |
| `protId` | string | Protein accession |
| `pmId` | string | PubMed ID of supporting paper |

### generif
Gene Reference Into Function — curated one-line functional summaries from NCBI.
| Column | Type | Description |
|--------|------|-------------|
| `geneId` | string | Gene/protein accession |
| `pmcId` | string | PMC ID |
| `pmId` | string | PubMed ID |
| `comment` | string | Functional summary text |

### uniq
Unique protein sequences.
| Column | Type | Description |
|--------|------|-------------|
| `sequence_id` | string | Sequence identifier |
| `sequence` | string | Full amino acid sequence |
| `protein_length` | string | Protein length (string) |

### site
Protein functional sites from PDB structures.
| Column | Type | Description |
|--------|------|-------------|
| `db` | string | Source (PDB) |
| `id` | string | PDB ID |
| `chain` | string | PDB chain |
| `ligandId` | string | Ligand identifier |
| `ligandChain` | string | Ligand chain |
| `type` | string | Site type (binding, active, modified) |
| `posFrom` | string | Start position |
| `posTo` | string | End position |
| `pdbFrom` | string | PDB start position |
| `pdbTo` | string | PDB end position |
| `comment` | string | Site description |
| `pmIds` | string | Supporting PubMed IDs |

## Table Relationships

- `genepaper.geneId` → `gene.geneId` (gene metadata)
- `genepaper.geneId` → `snippet.geneId` (text snippets for gene-paper pairs)
- `genepaper.pmId` → `paperaccess.pmId` (access status)
- `curatedgene.protId` → `curatedpaper.protId` (curated references)
- `seqtoduplicate.sequence_id` links text-mined IDs to curated IDs (cross-database mapping)
- `generif.geneId` → `gene.geneId` (GeneRIF annotations)
- `hassites.id` + `hassites.chain` → `site.id` + `site.chain` (PDB sites)
- `seqhassite.seqHash` links sequences to PDB chains
- `site.ligandId` → `pdbligand.ligandId` (ligand names)

## Cross-Collection Relationships

PaperBLAST gene IDs can link to other BERDL collections:
- **Fitness Browser** (`kescience_fitnessbrowser`): Gene locus IDs (e.g., VIMSS IDs) appear in `seqtoduplicate` and can be mapped to FB `locusId` values
- **Pangenome** (`kbase_ke_pangenome`): Protein sequences in `uniq` can be matched to pangenome gene sequences via BLAST or exact match
- **ModelSEED** (`kbase_msd_biochemistry`): Curated enzyme annotations in `curatedgene` include EC numbers that map to ModelSEED reactions

## Common Query Patterns

### Count papers per gene
```sql
SELECT geneId, COUNT(DISTINCT pmId) as n_papers
FROM kescience_paperblast.genepaper
GROUP BY geneId
ORDER BY n_papers DESC
LIMIT 20
```

### Find papers for a specific protein
```sql
SELECT gp.title, gp.journal, gp.year, gp.pmId
FROM kescience_paperblast.genepaper gp
WHERE gp.geneId = 'NP_010242.1'
ORDER BY CAST(gp.year AS INT) DESC
```

### Get curated annotations with references
```sql
SELECT cg.protId, cg.name, cg.desc, cg.organism, cp.pmId
FROM kescience_paperblast.curatedgene cg
JOIN kescience_paperblast.curatedpaper cp
  ON cg.db = cp.db AND cg.protId = cp.protId
WHERE cg.organism LIKE '%Escherichia%'
LIMIT 20
```

### Find text snippets mentioning a gene
```sql
SELECT s.snippet, s.pmId
FROM kescience_paperblast.snippet s
WHERE s.geneId = 'NP_010242.1'
LIMIT 10
```

### Count genes by organism
```sql
SELECT organism, COUNT(*) as n_genes
FROM kescience_paperblast.gene
GROUP BY organism
ORDER BY n_genes DESC
LIMIT 20
```

### Find binding sites for a PDB structure
```sql
SELECT s.chain, s.type, s.ligandId, pl.ligandName, s.posFrom, s.posTo
FROM kescience_paperblast.site s
LEFT JOIN kescience_paperblast.pdbligand pl ON s.ligandId = pl.ligandId
WHERE s.id = '7bgt'
```

## Pitfalls

- **`year` is a string**: Always `CAST(year AS INT)` for comparisons or ordering.
- **`protein_length` in curatedgene and uniq is a string**: Cast to INT for numeric operations.
- **`isOpen` is mostly NULL**: Do not rely on this field for filtering open-access papers.
- **genepaper is large (3.2M rows)**: Filter by geneId or pmId rather than scanning the full table.
- **Gene IDs span multiple namespaces**: geneId values include RefSeq (NP_*), UniProt (WP_*), VIMSS, and others. Cross-referencing requires the `seqtoduplicate` table.
- **Snippet text is raw PMC text**: May contain formatting artifacts, partial sentences, or references. Not suitable for direct display without cleaning.
