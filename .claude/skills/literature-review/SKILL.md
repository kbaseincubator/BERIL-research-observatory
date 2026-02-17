---
name: literature-review
description: Search biological literature using PubMed via the pubmed-mcp-server. Use when the user wants to find papers, review existing research on a topic, check what's known about an organism or pathway, or support a hypothesis with citations.
allowed-tools: Bash, Read, Write, WebSearch
user-invocable: true
---

# Literature Review Skill

Search and summarize biological literature relevant to BERDL research. Uses the [cyanheads/pubmed-mcp-server](https://github.com/cyanheads/pubmed-mcp-server) for PubMed search, article retrieval, citation network exploration, and research planning.

## Prerequisites

The `pubmed-mcp-server` from [cyanheads/pubmed-mcp-server](https://github.com/cyanheads/pubmed-mcp-server) must be configured in `.mcp.json` (already included in this repo). It runs via `npx -y @cyanheads/pubmed-mcp-server` — collaborators only need Node.js/npm.

### Available MCP Tools

- **`pubmed_search_articles`** — Search PubMed with filters and date ranges
- **`pubmed_fetch_contents`** — Retrieve detailed article metadata
- **`pubmed_article_connections`** — Find related articles and citations
- **`pubmed_research_agent`** — Generate structured research plans
- **`pubmed_generate_chart`** — Create PNG charts from publication data

**Optional** (for higher PubMed rate limits): Set `NCBI_API_KEY` in your environment or `.env`:
```
NCBI_API_KEY="your_ncbi_api_key"
```
Without this, PubMed rate limit is 3 requests/sec (vs 10/sec with key).

## Workflow

### Step 1: Understand the Research Question

Clarify what the user wants to search for. Ask if needed:
- Specific organism, gene, pathway, or phenotype?
- Time frame (recent papers only, or comprehensive)?
- Scope: quick check (5-10 papers) or thorough review (20-50 papers)?

If invoked during the `/berdl_start` research workflow, the hypothesis provides the search context.

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

Use the `pubmed-mcp-server` MCP tools to search. The primary tool is `pubmed_search_articles`. Use `pubmed_fetch_contents` to get full metadata and `pubmed_article_connections` to find related/citing papers. If the MCP server is not available, fall back to WebSearch.

**Search priority order**:
1. **PubMed** (via `pubmed_search_articles`) — primary for biology/biomedical papers
2. **Related articles** (via `pubmed_article_connections`) — citation network exploration
3. **WebSearch fallback** — if MCP server is unavailable

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

### From hypothesis generation (via `/berdl_start`)
After generating a hypothesis, `/literature-review` can be used to:
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

If the `pubmed-mcp-server` is not available (e.g., `npx` not installed or MCP not loading):

1. Check `.mcp.json` is configured with `"command": "npx", "args": ["-y", "@cyanheads/pubmed-mcp-server"]`
2. Test the server: `npx -y @cyanheads/pubmed-mcp-server --help`
3. If still unavailable, use `WebSearch` to search PubMed: `site:pubmed.ncbi.nlm.nih.gov [query]`
4. Use `WebFetch` to retrieve paper details from DOIs: `https://doi.org/[doi]`
5. Note in the output that results may be less comprehensive than MCP-based search

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.
