---
name: literature-review
description: Search biological literature using PubMed, Europe PMC, CORE, and OpenAlex. Use when the user wants to find papers, review existing research on a topic, check what's known about an organism or pathway, or support a hypothesis with citations.
allowed-tools: Bash, Read, Write, WebSearch
user-invocable: true
---

# Literature Review Skill

Search and summarize biological literature relevant to BERDL research. Uses the pubmed-search MCP server for access to PubMed, Europe PMC (33M+ papers), CORE (200M+ open access), and OpenAlex.

## Prerequisites

The `pubmed-search` MCP server must be configured in `.claude/settings.json` (already included in this repo). It runs via `uvx pubmed-search-mcp` with zero install — collaborators only need `uv`.

**Optional** (for faster PubMed access): Add to `.env`:
```
NCBI_EMAIL="your@email.com"
NCBI_API_KEY="your_ncbi_api_key"
```
Without these, PubMed rate limit is 3 requests/sec (vs 10/sec with key).

## Workflow

### Step 1: Understand the Research Question

Clarify what the user wants to search for. Ask if needed:
- Specific organism, gene, pathway, or phenotype?
- Time frame (recent papers only, or comprehensive)?
- Scope: quick check (5-10 papers) or thorough review (20-50 papers)?

If invoked from `/hypothesis`, the hypothesis provides the search context.

### Step 2: Construct Search Queries

Build search queries using biology-aware strategies:

#### MeSH Term Expansion

For biological topics, expand to MeSH terms for better PubMed coverage:

| User term | MeSH expansion |
|---|---|
| "pangenome" | "pangenome" OR "pan-genome" OR "core genome" OR "accessory genome" |
| "horizontal gene transfer" | "Gene Transfer, Horizontal"[MeSH] OR "lateral gene transfer" |
| "E. coli" | "Escherichia coli"[MeSH] OR "E. coli" |
| "antibiotic resistance" | "Drug Resistance, Microbial"[MeSH] OR "antimicrobial resistance" |
| "metabolic pathway" | "Metabolic Networks and Pathways"[MeSH] |

#### Organism Filters (aligned with BERDL's GTDB taxonomy)

When searching for a BERDL species, use both the GTDB name and common variants:
```
"Escherichia coli" OR "E. coli"
"Staphylococcus aureus" OR "S. aureus" OR "MRSA"
```

#### Functional Annotation Keyword Expansion

When searching for gene functions found in BERDL data, expand:

| BERDL annotation | Search terms |
|---|---|
| COG category J | "translation" AND "ribosomal" |
| COG category V | "defense mechanisms" OR "restriction modification" OR "CRISPR" |
| COG category X | "mobilome" OR "transposon" OR "prophage" OR "mobile genetic element" |
| EC 2.7.1.* | "kinase" AND "phosphorylation" |
| KEGG pathway map00010 | "glycolysis" OR "gluconeogenesis" |

### Step 3: Execute Search

Use the pubmed-search MCP tools to search. If the MCP server is not available, fall back to WebSearch.

**Search priority order**:
1. **PubMed** — primary for biology/biomedical papers
2. **Europe PMC** — broader coverage, includes preprints
3. **CORE** — open access full text
4. **OpenAlex** — citation analysis and metadata

**For each search**:
- Start with a focused query (specific organism + specific topic)
- If too few results (<5), broaden the query
- If too many results (>100), narrow with date range or additional terms
- Retrieve: title, authors, year, DOI, PMID/PMCID, abstract

### Step 4: Filter and Rank Results

Filter results for relevance to BERDL research:

**High relevance** (prioritize these):
- Papers using the same organisms present in BERDL
- Pangenome analyses, comparative genomics, core/accessory gene studies
- Metabolic pathway analyses that can be cross-referenced with BERDL biochemistry data
- Environmental genomics studies with taxonomic overlap

**Medium relevance**:
- Methodology papers (pangenome tools, clustering methods)
- Review articles on relevant topics
- Related organisms or pathways

**Low relevance** (include only if few high-relevance results):
- Tangentially related topics
- Papers on distant organisms

### Step 5: Summarize Findings

Group results by theme and present as a structured summary:

```markdown
## Literature Review: [Topic]

### Summary
[2-3 sentence overview of what the literature says]

### Key Findings by Theme

#### Theme 1: [e.g., "Pangenome methods"]
- **Author et al. (Year)** — [Key finding]. DOI: [doi]
- **Author et al. (Year)** — [Key finding]. DOI: [doi]

#### Theme 2: [e.g., "Core gene evolution"]
- ...

### Gaps in Current Knowledge
- [What hasn't been studied yet that BERDL could address]

### Relevance to BERDL
- [Specific tables/queries that could extend these findings]
- [Which BERDL species overlap with the studies found]
```

### Step 6: Store References

Save structured references to the project directory:

```markdown
# References

## [Topic or Research Question]

Searched: [date], Sources: PubMed, Europe PMC
Query: "[search terms used]"

### Cited References

1. Author A, Author B. (Year). "Title." *Journal*, Volume(Issue), Pages. DOI: [doi]. PMID: [pmid]
2. ...

### Additional References (not cited but relevant)

1. ...
```

**File location**: `projects/{project_id}/references.md`

If no project context exists, offer to create the file in the current working directory.

### Step 7: Connect to BERDL (optional)

If the literature review reveals organisms, genes, or pathways present in BERDL:

1. Note which BERDL tables contain relevant data
2. Suggest specific queries to test literature findings at scale
3. Identify discrepancies between published results and BERDL data
4. Flag opportunities for novel analysis

## Integration with Other Skills

### From `/hypothesis`
After generating a hypothesis, the user can invoke `/literature-review` to:
- Check if the hypothesis has already been tested
- Find supporting or contradicting evidence
- Identify methods used in similar studies
- Discover additional variables to consider

### To `/berdl`
Literature findings can inform BERDL queries:
- Paper mentions specific EC numbers → query `eggnog_mapper_annotations`
- Paper studies specific species → look up in `gtdb_species_clade`
- Paper reports gene essentiality → cross-reference with fitness browser

### To `/submit`
The `references.md` file created by this skill is checked during project submission as an advisory item.

## Fallback: WebSearch

If the pubmed-search MCP server is not available (e.g., `uvx` not installed):

1. Use `WebSearch` to search PubMed directly: `site:pubmed.ncbi.nlm.nih.gov [query]`
2. Use `WebSearch` for Google Scholar: `site:scholar.google.com [query]`
3. Use `WebFetch` to retrieve paper details from DOIs: `https://doi.org/[doi]`
4. Note in the output that results may be less comprehensive than MCP-based search

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.
