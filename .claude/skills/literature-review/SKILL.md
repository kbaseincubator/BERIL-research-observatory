---
name: literature-review
description: Search and review biological literature using MCP tools (PubMed, arXiv, bioRxiv, Google Scholar) with full-text reading, citation snowballing, and PaperBLAST integration. Use when the user wants to find papers, review existing research on a topic, check what's known about an organism or pathway, or support a hypothesis with citations.
allowed-tools: Bash, Read, Write, WebSearch, Agent, ToolSearch
user-invocable: true
---

# Literature Review Skill

Search, read, and synthesize biological literature relevant to BERDL research. Combines multi-source discovery (PubMed, arXiv, bioRxiv, Google Scholar) with full-text analysis, citation network exploration, and PaperBLAST cross-referencing for literature reviews that go beyond abstract-level summaries.

## Prerequisites

Two MCP servers provide literature access. Both are configured in `.mcp.json` and available to all collaborators.

### Primary: PubMed MCP (project-level, HTTP)

The `pubmed` MCP server (`https://pubmed.mcp.claude.com/mcp`) provides the richest PubMed access with date filters, pagination, MeSH support, citation networks, and full-text retrieval from PMC. Tools are prefixed `mcp__pubmed__`.

**Search & discovery:**
- **`search_articles`** — Rich PubMed search with date filters, sorting, MeSH, pagination
- **`find_related_articles`** — Citation network: similar papers, PMC links, gene/protein links
- **`get_article_metadata`** — Detailed metadata for specific PMIDs

**Full-text & access:**
- **`get_full_text_article`** — Full text from PMC (~6M open-access articles)
- **`get_copyright_status`** — Open access/license info
- **`convert_article_ids`** — PMID ↔ PMCID ↔ DOI conversion

### Secondary: paper-search-mcp (openags)

The `paper-search-mcp` from [openags/paper-search-mcp](https://github.com/openags/paper-search-mcp) provides keyword search across arXiv, bioRxiv, medRxiv, and Google Scholar. It runs via `uvx --from paper-search-mcp python -m paper_search_mcp.server` — collaborators only need Python 3.10+ and [uv](https://docs.astral.sh/uv/).

**Search tools:**
- **`search_pubmed`** — PubMed search (use as fallback; prefer bio-research `search_articles`)
- **`search_arxiv`** — Search arXiv preprints
- **`search_biorxiv`** — Search bioRxiv preprints (keyword search — bio-research bioRxiv plugin only supports category/date browsing)
- **`search_medrxiv`** — Search medRxiv preprints
- **`search_google_scholar`** — Search Google Scholar

**Full-text read tools** (extract text from preprint PDFs):
- **`read_arxiv_paper`** — Read arXiv paper full text
- **`read_biorxiv_paper`** — Read bioRxiv paper full text
- **`read_medrxiv_paper`** — Read medRxiv paper full text

> **Note**: `download_pubmed` and `read_pubmed_paper` from paper-search-mcp are **not supported** and return errors. Use the pubmed MCP's `get_full_text_article` for PubMed/PMC full text instead.

### PaperBLAST (BERDL local resource)

The `kescience_paperblast` database (3.2M gene-paper associations, 1.9M text snippets from PMC full-text mining) links protein sequences to scientific literature. See `.claude/skills/berdl/modules/paperblast.md` for table schemas. Used in deep reviews when the research question involves specific genes, proteins, or pathways.

### Supported Sources

| Source | Best for | Primary tool |
|---|---|---|
| PubMed | Biomedical, microbiology, genomics — primary for BERDL | `mcp__pubmed__search_articles` |
| bioRxiv | Recent preprints in biology, genomics, microbiology | paper-search-mcp `search_biorxiv` |
| arXiv | Computational biology, bioinformatics methods | paper-search-mcp `search_arxiv` |
| Google Scholar | Broad coverage, catching papers not in other databases | paper-search-mcp `search_google_scholar` |
| PaperBLAST | Gene/protein-focused literature from PMC text mining | BERDL SQL queries |

## Workflow

### Step 1: Understand the Research Question

Clarify what the user wants to search for. Ask if needed:
- Specific organism, gene, pathway, or phenotype?
- Time frame (recent papers only, or comprehensive)?
- Does the question involve specific genes or proteins? (triggers PaperBLAST integration)

**Select a review depth tier** based on user needs:

| Tier | Papers | Full text? | Citation snowball? | PaperBLAST? | When to use |
|---|---|---|---|---|---|
| **Quick scan** | 5-10 | No | No | No | Ad-hoc questions, quick checks |
| **Standard review** | 20-30 | Top 10 | Yes | If genes involved | Default for project workflows, `/berdl_start` hypotheses |
| **Deep review** | 50+ | Top 20 | Yes | Yes | Systematic/comprehensive needs, grant writing |

Default to **quick scan** for ad-hoc questions and **standard review** for project-based work or when invoked via `/berdl_start`. Use **deep review** only when explicitly requested or when the question demands comprehensive coverage.

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

Search across multiple sources, then deduplicate before ranking.

**Search priority order** (for biology/BERDL research):
1. **PubMed** via `mcp__pubmed__search_articles` — primary for published biomedical papers. Supports date filters, MeSH terms, field tags, pagination, and sorting. Richer than paper-search-mcp's `search_pubmed`.
2. **bioRxiv** via `mcp__paper-search__search_biorxiv` — keyword search for recent preprints. (The bio-research bioRxiv plugin only supports category/date browsing, not keyword search.)
3. **arXiv** via `mcp__paper-search__search_arxiv` — computational biology and bioinformatics methods papers
4. **Google Scholar** via `mcp__paper-search__search_google_scholar` — broad fallback for papers missed by other sources
5. **WebSearch fallback** — if MCP servers are unavailable, use `site:pubmed.ncbi.nlm.nih.gov [query]`

> **Fallback**: If `search_articles` (bio-research) is unavailable, use `search_pubmed` (paper-search-mcp) as a secondary PubMed search option.

**For each search**:
- Start with a focused query (specific organism + specific topic)
- If too few results (<5), broaden the query
- If too many results (>100), narrow with date range or additional terms
- Retrieve: title, authors, year, DOI, PMID/PMCID, abstract

**Deduplication**: After collecting results from all sources, deduplicate by DOI (preferred) or PMID before proceeding to Step 4. Papers found in multiple sources get a small relevance boost in ranking (multiple indexing suggests broad impact). Use `mcp__pubmed__convert_article_ids` to resolve PMID ↔ PMCID ↔ DOI when needed.

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

### Step 4.5: Expand via Citation Network *(Standard + Deep tiers only)*

For the top 10 most relevant papers found in Steps 3-4:

1. **Find related papers**: Use `mcp__pubmed__find_related_articles` with `link_type=pubmed_pubmed` to find computationally similar papers not caught by keyword search
2. **Score new papers** against the same relevance criteria from Step 4
3. **Add high-relevance papers** to the results set
4. **Deduplicate** by DOI/PMID before proceeding

This catches papers using different terminology but studying the same phenomenon (e.g., a paper about "dispensable genes" when you searched for "accessory genome").

> **Tip**: `find_related_articles` also supports `link_type=pubmed_pmc_refs_citedin` for forward citations (papers that cite this one) — useful for finding recent follow-up studies.

### Step 4.7: Deep Reading of Key Papers via Subagents *(Standard + Deep tiers only)*

Full-text papers are 5K-20K+ tokens each. Reading them directly in the main context would consume 50K-200K tokens, leaving little room for synthesis. Instead, delegate full-text reading to **subagents** that each return a structured summary (~200-400 tokens).

> **Context budget**: ~200-400 tokens per paper summary vs. 5K-20K+ for raw full text. For 10 papers this reduces context consumption from ~100K tokens to ~3K-5K tokens.

#### 4.7a: Build the Paper Manifest

From the ranked papers (Steps 4-4.5), build a manifest of the top papers to read in full:

| Field | Description |
|---|---|
| `title` | Paper title |
| `id` | PMID, PMCID, arXiv ID, or DOI |
| `source` | `pubmed`, `arxiv`, `biorxiv`, or `medrxiv` |
| `has_pmcid` | Whether a PMCID is available (for PubMed papers, use `mcp__pubmed__convert_article_ids`) |

Standard tier: top 10 papers. Deep tier: top 20 papers.

#### 4.7b: Spawn Paper-Reader Subagents

For each paper in the manifest, spawn a subagent using the **Agent tool** with `subagent_type: "general-purpose"`. Launch multiple subagents in parallel — use a **single message with multiple Agent tool calls** (up to 5 at a time) for efficiency.

Each subagent receives this prompt template (fill in the bracketed values):

```
You are a paper-reader agent. Your task is to retrieve and extract structured information from a scientific paper.

RESEARCH QUESTION: [the user's research question]

PAPER: "[title]"
SOURCE: [pubmed|arxiv|biorxiv|medrxiv]
IDENTIFIER: [PMCID, arXiv ID, or DOI]

STEP 1: Load the appropriate MCP tool using ToolSearch:
- For PubMed/PMC papers: ToolSearch query "select:mcp__pubmed__get_full_text_article", then call mcp__pubmed__get_full_text_article with pmcid="[PMCID]"
- For arXiv papers: ToolSearch query "select:mcp__paper-search__read_arxiv_paper", then call mcp__paper-search__read_arxiv_paper with the arXiv ID
- For bioRxiv papers: ToolSearch query "select:mcp__paper-search__read_biorxiv_paper", then call mcp__paper-search__read_biorxiv_paper with the DOI
- For medRxiv papers: ToolSearch query "select:mcp__paper-search__read_medrxiv_paper", then call mcp__paper-search__read_medrxiv_paper with the DOI

STEP 2: Read the full text. Focus on Methods, Results, and Discussion sections.

STEP 3: Return EXACTLY this structured extraction (400 words max):

**[First Author et al. (Year)] — [Title]**
STATUS: FULL_TEXT

### Methods
- [study design, key techniques, sample size, organisms used] (1-3 bullets)

### Key Results
- [findings with specific numbers, effect sizes, p-values] (3-5 bullets, focused on the research question)

### Limitations
- [acknowledged weaknesses] (1-3 bullets)

### BERDL Relevance
- [organisms, genes, pathways, EC numbers, or data types that map to BERDL tables]

### Notable Quotes
- "[verbatim quote]" — [section name]

If the full text is unavailable (tool error, not in PMC, PDF extraction fails), return:
STATUS: ABSTRACT_ONLY
and note the reason. The main agent will use the abstract from Step 3 instead.
```

#### 4.7c: Collect and Tag Results

After all subagents return:
1. Collect each structured extraction
2. Tag each paper as `[FULL TEXT]` or `[ABSTRACT ONLY]` based on the STATUS field
3. For `ABSTRACT_ONLY` papers, use the abstract retrieved in Step 3 for synthesis
4. Use the structured extractions (not raw full text) for the summary in Step 5

**Error handling:**
- **Paper not in PMC**: Subagent returns `STATUS: ABSTRACT_ONLY` — use abstract from Step 3
- **MCP tool unavailable**: Subagent returns `ABSTRACT_ONLY` with reason — fall back per the Fallback section
- **PDF extraction fails**: Same `ABSTRACT_ONLY` fallback
- **Subagent timeout/failure**: Note as `ABSTRACT_ONLY`, continue with remaining papers

### Step 4.8: On-Demand Deep Reading *(after presenting the review)*

After the review is presented to the user, if they want deeper analysis of a specific paper, spawn a **single subagent** with an expanded extraction prompt:

- Increase the word limit to **800 words**
- Include the user's specific question about the paper
- Add a `### Detailed Analysis` section addressing the user's question
- Add a `### Future Directions` section (what the authors suggest for follow-up)
- Include more extensive quotes from relevant sections

This keeps the main context clean while allowing drill-down into any paper on demand.

### Step 4.9: PaperBLAST Cross-Reference *(Deep tier, or when genes/proteins are involved)*

When the research question involves specific genes, proteins, enzymes, or pathways, query the `kescience_paperblast` database in BERDL to find literature linked to specific gene/protein identifiers.

**Queries to run** (via the `/berdl` skill or direct SQL):

1. **Find papers mentioning relevant genes:**
   ```sql
   SELECT gp.geneId, gp.title, gp.journal, gp.year, gp.pmId, gp.doi
   FROM kescience_paperblast.genepaper gp
   WHERE gp.geneId = '<gene_accession>'
   ORDER BY CAST(gp.year AS INT) DESC
   LIMIT 20
   ```

2. **Get text snippets from those papers:**
   ```sql
   SELECT s.snippet, s.pmId, s.pmcId
   FROM kescience_paperblast.snippet s
   WHERE s.geneId = '<gene_accession>'
   LIMIT 10
   ```

3. **Find curated functional annotations with references:**
   ```sql
   SELECT cg.protId, cg.name, cg.desc, cg.organism, cg.comment, cp.pmId
   FROM kescience_paperblast.curatedgene cg
   JOIN kescience_paperblast.curatedpaper cp
     ON cg.db = cp.db AND cg.protId = cp.protId
   WHERE cg.name LIKE '%<gene_name>%' OR cg.desc LIKE '%<keyword>%'
   LIMIT 20
   ```

4. **Get GeneRIF functional summaries:**
   ```sql
   SELECT gr.comment, gr.pmId
   FROM kescience_paperblast.generif gr
   WHERE gr.geneId = '<gene_accession>'
   LIMIT 10
   ```

**Cross-reference** found PMIDs with papers already discovered in Steps 3-4 to identify:
- Papers already found (confirms relevance)
- New papers not caught by keyword search (add to results)
- Text snippets providing gene-specific context from full-text mining

See `.claude/skills/berdl/modules/paperblast.md` for full table schemas and additional query patterns.

> **Pitfall**: PaperBLAST `year` is stored as a string — always use `CAST(year AS INT)` for comparisons or ordering. Gene IDs span multiple namespaces (RefSeq NP_*, UniProt WP_*, VIMSS) — use `seqtoduplicate` table for cross-referencing.

### Step 5: Summarize Findings

Group results by theme and present as a structured summary. The depth of summary should match the review tier.

**Quick scan** — use the basic template below (themes + gaps).

**Standard/Deep review** — use the extended template with methods comparison, quantitative results, and evidence quality indicators.

```markdown
## Literature Review: [Topic]

**Review depth**: [Quick scan | Standard review | Deep review]
**Papers found**: [N total] | **Full text read**: [N] | **Abstract only**: [N]
**Sources searched**: [list sources used]

### Summary
[2-3 sentence overview of what the literature says]

### Key Findings by Theme

#### Theme 1: [e.g., "Pangenome methods"]
- **Author et al. (Year)** — [Key finding]. DOI: [doi] [FULL TEXT | ABSTRACT ONLY]
- **Author et al. (Year)** — [Key finding]. DOI: [doi] [FULL TEXT | ABSTRACT ONLY]

#### Theme 2: [e.g., "Core gene evolution"]
- ...

### Methods Comparison *(Standard + Deep tiers)*

| Study | Organism(s) | Method | Sample size | Key metric |
|---|---|---|---|---|
| Author (Year) | E. coli | Pangenome analysis (Roary) | 500 genomes | Core genes: 2,800 |
| ... | ... | ... | ... | ... |

### Key Quantitative Results *(Standard + Deep tiers)*

| Finding | Value | Study | Evidence quality |
|---|---|---|---|
| Core genome size | 2,800 genes | Author (2024) | Large-scale, peer-reviewed |
| Accessory/total ratio | 0.45 | Author (2023) | Preprint, n=50 |
| ... | ... | ... | ... |

### Evidence Quality Notes *(Standard + Deep tiers)*
- [Note which findings are from peer-reviewed vs. preprint sources]
- [Flag small sample sizes, single-organism studies, or methodological limitations]
- [Note if key claims are supported by multiple independent studies]

### Gaps in Current Knowledge
- [What hasn't been studied yet that BERDL could address]

### PaperBLAST Findings *(if Step 4.9 was performed)*
- [Gene-specific literature connections found via text mining]
- [PMIDs confirmed by both keyword search and PaperBLAST]
- [New papers found only through PaperBLAST]

### Relevance to BERDL
- [Specific tables/queries that could extend these findings]
- [Which BERDL species overlap with the studies found]
```

### Step 6: Store References

Save structured references to the project directory:

```markdown
# References

## [Topic or Research Question]

Searched: [date], Sources: [PubMed, bioRxiv, arXiv, Google Scholar, PaperBLAST — list those actually used]
Query: "[search terms used]"
Review depth: [Quick scan | Standard review | Deep review]

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

If MCP tools are unavailable:

1. **PubMed MCP unavailable**: Fall back to paper-search-mcp's `search_pubmed` for PubMed search
2. **paper-search-mcp unavailable**: Check `.mcp.json` is configured with `"command": "uvx", "args": ["--from", "paper-search-mcp", "python", "-m", "paper_search_mcp.server"]`. Test: `uvx --from paper-search-mcp python -m paper_search_mcp.server`
3. **All MCP unavailable**: Use `WebSearch` to search PubMed: `site:pubmed.ncbi.nlm.nih.gov [query]`
4. Use `WebFetch` to retrieve paper details from DOIs: `https://doi.org/[doi]`
5. Note in the output that results may be less comprehensive than MCP-based search (no full-text retrieval, no citation snowballing)

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.
