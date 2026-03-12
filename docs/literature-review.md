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
Step 3: Discover and rank papers via subagent (search → dedup → rank → snowball)
Step 4: PaperBLAST cross-reference via subagent (parallel with Step 3)
Step 5: Full-text deep reading via subagents (Standard + Deep)
Step 5.5: On-demand deep reading (after presenting review)
Step 6: Summarize with methods comparison, quantitative results, evidence quality
Step 7: Store references to projects/{id}/references.md
Step 8: Connect findings back to BERDL tables
```

### Tool Architecture

Both MCP servers are configured in `.mcp.json` and available to all collaborators automatically.

**Primary PubMed search** — `pubmed` MCP server (`https://pubmed.mcp.claude.com/mcp`):
- Tools prefixed `mcp__pubmed__*`
- `search_articles`: date filters, MeSH support, pagination, sorting
- `find_related_articles`: citation network exploration
- `get_full_text_article`: full text from PMC (~6M open-access articles)
- `convert_article_ids`: PMID ↔ PMCID ↔ DOI

**Preprint search** — `paper-search` MCP server (runs locally via `uvx`):
- Tools prefixed `mcp__paper-search__*`
- bioRxiv, arXiv, medRxiv keyword search
- Google Scholar broad fallback
- Full-text PDF extraction via `read_arxiv_paper`, `read_biorxiv_paper`, `read_medrxiv_paper`
- Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/)

**Gene/protein literature** — PaperBLAST (BERDL local):
- 3.2M gene-paper associations from PMC text mining
- 1.9M text snippets mentioning specific genes
- Curated annotations from SwissProt, BRENDA, etc.
- GeneRIF functional summaries from NCBI

### Why Both MCP Servers?

The PubMed MCP covers published biomedical literature with rich search, citation networks, and PMC full text. But it doesn't cover preprints or non-biomedical sources. paper-search-mcp fills the gaps:

| Capability | `pubmed` MCP | `paper-search` MCP |
|---|---|---|
| PubMed search (rich, MeSH, pagination) | Yes | Basic only |
| PMC full text | Yes | Not supported |
| Citation snowballing | Yes | No |
| bioRxiv keyword search | No | **Yes** |
| arXiv search | No | **Yes** |
| Google Scholar | No | **Yes** |
| Preprint PDF full-text reading | No | **Yes** |

### Context-Efficient Subagent Architecture

The skill delegates three heavy operations to subagents to keep the main context clean for synthesis:

```
Main context                          Subagents (isolated contexts)
─────────────                         ───────────────────────────

Queries, tier, filters          ──►   DISCOVERY SUBAGENT
                                      Search PubMed, bioRxiv, arXiv, Scholar
                                      Deduplicate by DOI/PMID
                                      Rank by BERDL relevance
                                      Citation snowball (Standard + Deep)
Compact manifest (2-4K tokens)  ◄──   Return ~100-150 tokens/paper

Gene/protein identifiers        ──►   PAPERBLAST SUBAGENT
                                      SQL queries against kescience_paperblast
                                      Gene lookup, gene-paper, snippets, curated, GeneRIF
Gene-lit summary (1-3K tokens)  ◄──   Return compact summary + PMID list

Paper manifest (IDs, titles)    ──►   PAPER-READER SUBAGENTS (1 per paper)
                                      ToolSearch → load MCP tool
                                      Call get_full_text_article / read_*_paper
                                      Read 5K-20K tokens of full text
Structured summary (200-400 tokens) ◄── Extract methods, results, limitations
```

**Discovery + PaperBLAST launch in parallel** (single message, two Agent tool calls). Paper-reader subagents launch after the discovery manifest is received.

**Context savings:**

| Component | Before (main context) | After (subagent) | Saved |
|-----------|----------------------|-------------------|-------|
| Search + abstracts | 8-20K tokens | ~50 (launch) | 8-20K |
| Ranking + snowball | 7-20K tokens | 2-4K (manifest) | 5-16K |
| PaperBLAST | 9.5-40K tokens | 1-3K (summary) | 8-37K |
| Full-text reading (10 papers) | ~100K tokens | 3-5K (summaries) | ~95K |
| **Total pipeline** | **125-180K** | **~6-12K** | **~115-170K** |

**Fallback:** If any subagent fails, the main agent degrades gracefully — running the operation directly in main context or skipping the optional step.

### What Changed from the Previous Version

The previous skill stopped at abstract-level search results. The upgrades add:

1. **Discovery pipeline delegation** — search, dedup, rank, and citation snowball run in a subagent, returning a compact manifest (~100-150 tokens/paper) instead of loading 15-40K+ tokens of raw results into main context
2. **PaperBLAST delegation** — gene-literature SQL queries run in a subagent, returning a compact summary (~1-3K tokens) instead of 9.5-40K+ tokens of raw SQL results
3. **Full-text reading via subagents** — retrieves and analyzes actual paper content (methods, results, limitations) through context-isolated subagents instead of loading raw text into the main context
4. **Citation snowballing** — finds related papers through PubMed's citation network, catching papers that use different terminology
5. **PaperBLAST integration** — queries 3.2M gene-paper associations when the research involves specific genes or proteins
6. **Depth tiers** — scales the review effort to match the need (quick check vs. systematic review)
7. **Project-level PubMed MCP** — `pubmed` HTTP server in `.mcp.json` so all collaborators get it (no plugin install needed)
8. **Cross-source deduplication** — removes duplicate papers found across PubMed, bioRxiv, and Google Scholar
9. **Enhanced summaries** — includes methods comparison tables, quantitative results, and evidence quality indicators
10. **On-demand deep reading** — drill into any paper post-review with an expanded extraction focused on a specific question

---

## Test Prompts

Use these after restarting Claude Code (MCP servers initialize on session start).

### Test 1: Quick Scan (basic search, abstract-only)

```
/literature-review

Do a quick scan on CRISPR-Cas defense systems in Escherichia coli.
Just 5-10 recent papers to get an overview of the current state.
```

**What to verify:**
- Step 3 spawns a discovery subagent (not direct MCP calls in main context)
- Main context receives a compact manifest, not raw search results
- Skips Steps 4, 5, 5.5 (quick scan tier — no PaperBLAST, no full-text, no snowball)
- Discovery subagent skips citation snowball for quick_scan tier
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
- Step 3 spawns a discovery subagent that searches PubMed, bioRxiv, arXiv
- Discovery subagent performs citation snowballing and returns a compact manifest
- Main context does NOT contain raw search results or abstracts (only the manifest)
- Step 5 spawns paper-reader subagents via Agent tool (not direct MCP calls in main context)
- Main context does NOT contain raw full-text paper content (only structured summaries)
- Each subagent returns a structured extraction under 400 words
- Summary includes methods comparison and quantitative results tables
- Each paper tagged [FULL TEXT] or [ABSTRACT ONLY]
- Papers not in PMC are tagged ABSTRACT_ONLY with graceful fallback

### Test 3: Gene-Focused Review (triggers PaperBLAST)

```
/literature-review

Standard review on the fitness effects of the rpoB gene across bacterial
species. I want to understand what's known about rpoB mutations and
adaptation. This involves a specific gene, so please include PaperBLAST
cross-referencing.
```

**What to verify:**
- Recognizes gene involvement → activates Step 4 (PaperBLAST subagent)
- Steps 3 and 4 launch in parallel (single message with two Agent tool calls)
- PaperBLAST subagent queries `kescience_paperblast` tables via SQL
- Main context receives compact gene-lit summary, not raw SQL results
- Step 4c cross-references PaperBLAST PMIDs with discovery manifest
- Summary includes "PaperBLAST Findings" section with confirmed/new paper counts

### Test 4: Fallback Behavior

```
/literature-review

Quick scan on horizontal gene transfer in thermophilic archaea.
```

**What to verify:**
- If `pubmed` MCP is down, discovery subagent falls back to `mcp__paper-search__search_pubmed`
- Notes in output that results may be less comprehensive
- Still searches bioRxiv and arXiv via paper-search-mcp
- If discovery subagent crashes entirely, main agent runs search directly (degraded mode)

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
- Steps 3 and 4 launch in parallel as subagents (single message with two Agent tool calls)
- Discovery subagent searches broadly (all 4 sources) with citation snowballing
- PaperBLAST subagent queries for resistance gene IDs
- Main context receives compact manifest + gene-lit summary, not raw results
- Step 5 spawns paper-reader subagents for top 20 papers (multiple Agent tool calls in parallel batches)
- Main context stays clean — only structured summaries, no raw paper text or SQL results
- Step 4c cross-references PaperBLAST PMIDs with discovery manifest
- Summary includes all extended sections (methods, quant results, evidence quality, PaperBLAST findings)
- Methods comparison table is populated from subagent extractions
- References stored to project file
