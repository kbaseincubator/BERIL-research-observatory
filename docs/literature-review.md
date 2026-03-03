# Literature Review Skill

The `/literature-review` skill searches, reads, and synthesizes biological literature relevant to BERDL research. It goes beyond abstract-level summaries by combining multi-source discovery with full-text analysis, citation network exploration, and PaperBLAST cross-referencing.

## How It Works

### Three Depth Tiers

| Tier | Papers | Full text | Citation snowball | PaperBLAST | Use case |
|---|---|---|---|---|---|
| **Quick scan** | 5-10 | No | No | No | Ad-hoc questions, quick checks |
| **Standard review** | 20-30 | Top 10 | Yes | If genes involved | Project workflows, hypothesis validation |
| **Deep review** | 50+ | Top 20 | Yes | Yes | Systematic reviews, grant writing |

Quick scan is the default for ad-hoc questions. Standard review is the default when invoked via `/berdl_start` or during project work.

### Workflow Steps

```
Step 1: Understand question → select depth tier
Step 2: Construct queries (MeSH expansion, organism filters, COG/KEGG keywords)
Step 3: Search across sources → deduplicate by DOI/PMID
Step 4: Filter and rank by BERDL relevance
Step 4.5: Citation snowballing (Standard + Deep)
Step 4.7: Full-text deep reading (Standard + Deep)
Step 4.9: PaperBLAST cross-reference (Deep, or when genes/proteins involved)
Step 5: Summarize with methods comparison, quantitative results, evidence quality
Step 6: Store references to projects/{id}/references.md
Step 7: Connect findings back to BERDL tables
```

### Tool Architecture

**Primary PubMed search** — bio-research plugin (`search_articles`):
- Date filters, MeSH support, pagination, sorting
- Citation network via `find_related_articles`
- Full text from PMC via `get_full_text_article` (~6M open-access articles)
- ID conversion: PMID ↔ PMCID ↔ DOI

**Preprint search** — paper-search-mcp:
- bioRxiv, arXiv, medRxiv keyword search
- Google Scholar broad fallback
- Full-text PDF extraction via `read_arxiv_paper`, `read_biorxiv_paper`, `read_medrxiv_paper`

**Gene/protein literature** — PaperBLAST (BERDL local):
- 3.2M gene-paper associations from PMC text mining
- 1.9M text snippets mentioning specific genes
- Curated annotations from SwissProt, BRENDA, etc.
- GeneRIF functional summaries from NCBI

### What Changed from the Previous Version

The previous skill stopped at abstract-level search results. The upgrade adds:

1. **Full-text reading** — retrieves and analyzes actual paper content (methods, results, limitations) instead of just abstracts
2. **Citation snowballing** — finds related papers through PubMed's citation network, catching papers that use different terminology
3. **PaperBLAST integration** — queries 3.2M gene-paper associations when the research involves specific genes or proteins
4. **Depth tiers** — scales the review effort to match the need (quick check vs. systematic review)
5. **Better PubMed tooling** — uses bio-research plugin with richer search capabilities (date filters, MeSH, pagination)
6. **Cross-source deduplication** — removes duplicate papers found across PubMed, bioRxiv, and Google Scholar
7. **Enhanced summaries** — includes methods comparison tables, quantitative results, and evidence quality indicators

---

## Test Prompts

Use these after restarting Claude Code (the bio-research PubMed MCP plugin needs a fresh session).

### Test 1: Quick Scan (basic search, abstract-only)

```
/literature-review

Do a quick scan on CRISPR-Cas defense systems in Escherichia coli.
Just 5-10 recent papers to get an overview of the current state.
```

**What to verify:**
- Uses `search_articles` (bio-research) for PubMed, not `search_pubmed` (paper-search-mcp)
- Returns 5-10 papers with abstracts
- Skips Steps 4.5, 4.7, 4.9 (quick scan tier)
- Summary uses the basic template (no methods comparison table)

### Test 2: Standard Review (full text + citation snowballing)

```
/literature-review

Standard review: What is known about pangenome openness and environmental
adaptation in bacteria? I'm interested in whether bacteria in variable
environments tend to have larger accessory genomes. This is for a BERDL
project comparing pangenome statistics across habitats.
```

**What to verify:**
- Selects "standard review" tier
- Searches PubMed (bio-research), bioRxiv (paper-search-mcp), arXiv
- Deduplicates results by DOI before ranking
- Step 4.5: Uses `find_related_articles` on top papers
- Step 4.7: Retrieves full text (PMC for PubMed papers, PDF for preprints)
- Summary includes methods comparison and quantitative results tables
- Each paper tagged [FULL TEXT] or [ABSTRACT ONLY]

### Test 3: Gene-Focused Review (triggers PaperBLAST)

```
/literature-review

Standard review on the fitness effects of the rpoB gene across bacterial
species. I want to understand what's known about rpoB mutations and
adaptation. This involves a specific gene, so please include PaperBLAST
cross-referencing.
```

**What to verify:**
- Recognizes gene involvement → activates Step 4.9
- Queries `kescience_paperblast.genepaper` for rpoB-related gene IDs
- Queries `kescience_paperblast.snippet` for text excerpts
- Cross-references PaperBLAST PMIDs with keyword search results
- Summary includes "PaperBLAST Findings" section

### Test 4: Fallback Behavior

```
/literature-review

Quick scan on horizontal gene transfer in thermophilic archaea.
```

**What to verify:**
- If bio-research PubMed plugin is down, falls back to `search_pubmed` (paper-search-mcp)
- Notes in output that results may be less comprehensive
- Still searches bioRxiv and arXiv via paper-search-mcp

### Test 5: Deep Review (comprehensive)

```
/literature-review

Deep review: Comprehensive literature review on the relationship between
bacterial pangenome size, genome fluidity, and antibiotic resistance gene
prevalence. This is for a grant proposal. I need 50+ papers, full text on
the top 20, citation snowballing, and PaperBLAST integration for any
resistance genes found.
```

**What to verify:**
- Selects "deep review" tier
- Searches broadly (all 4 sources)
- Citation snowballing on top 10 papers
- Full-text reading on top 20 papers
- PaperBLAST queries for resistance gene IDs
- Summary includes all extended sections (methods, quant results, evidence quality, PaperBLAST findings)
- References stored to project file
