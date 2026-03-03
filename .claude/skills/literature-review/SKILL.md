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

### Step 3: Discover and Rank Papers via Subagent

The discovery pipeline (search, deduplicate, rank, citation snowball) runs inside a subagent that returns a compact manifest. This keeps ~15-40K+ tokens of raw search results, abstracts, and citation data out of the main context.

> **Context budget**: The discovery subagent returns ~100-150 tokens per paper in a structured manifest (~2-4K total for a standard review) vs. 15-40K+ tokens if search + rank + snowball ran in the main context.

#### 3a: Prepare Inputs

Gather these values from Steps 1-2:
- Research question
- Review tier (`quick_scan`, `standard`, `deep`)
- Search queries (PubMed, preprint, Scholar)
- Organism filters
- Paper count target (5-10 for quick, 20-30 for standard, 50+ for deep)

#### 3b: Spawn Discovery Subagent

Spawn via `Agent(subagent_type="general-purpose")` with this prompt template (fill `[bracketed]` values):

```
You are a literature discovery agent. Search scientific databases, deduplicate, rank by relevance, and return a compact paper manifest.

RESEARCH QUESTION: [research_question]
REVIEW TIER: [quick_scan|standard|deep]
SEARCH QUERIES:
- PubMed: [pubmed_query]
- Preprint: [preprint_query]
- Scholar: [scholar_query]
- Organism filters: [organism_filters]
PAPER COUNT TARGET: [5-10|20-30|50+]

STEP 1 — Load tools via ToolSearch:
- "select:mcp__pubmed__search_articles"
- "select:mcp__paper-search__search_biorxiv"
- "select:mcp__paper-search__search_arxiv"
- "select:mcp__paper-search__search_google_scholar"
- "select:mcp__pubmed__convert_article_ids"
- "select:mcp__pubmed__find_related_articles"

STEP 2 — Search all sources (priority order):
1. PubMed → 2. bioRxiv → 3. arXiv → 4. Google Scholar
Start focused; broaden if <5 results; narrow if >100.
Collect: title, authors, year, DOI, PMID/PMCID, abstract, source.
If a tool fails, note failure and continue with remaining sources.

STEP 3 — Deduplicate by DOI (primary) or PMID.
Use convert_article_ids to resolve PMID↔PMCID↔DOI.
For PubMed papers, check if PMCID exists (record has_pmcid).
Track which sources each paper appeared in.

STEP 4 — Rank by BERDL relevance:
HIGH: BERDL organism overlap, pangenome/comparative genomics, metabolic pathway analyses, environmental genomics with BERDL taxonomic overlap
MEDIUM: Methodology papers, reviews, related organisms/pathways
LOW: Tangential topics, distant organisms

STEP 5 — Citation snowball (SKIP for quick_scan):
For top 10 PMIDs, call find_related_articles (pubmed_pubmed).
Score new papers by same criteria. Deduplicate again.

STEP 6 — Return EXACTLY this format:

DISCOVERY_MANIFEST
TOTAL_FOUND: [N]
TOTAL_AFTER_DEDUP: [N]
TOTAL_RANKED: [N]
SOURCES_SEARCHED: [list]
SOURCES_FAILED: [list or "none"]
SNOWBALL_PERFORMED: [yes|no]
SNOWBALL_NEW_PAPERS: [N]

---PAPERS---

1. TITLE: [title]
   AUTHORS: [first author et al.]
   YEAR: [year]
   PMID: [or "none"]
   PMCID: [or "none"]
   DOI: [or "none"]
   SOURCE: [pubmed|biorxiv|arxiv|scholar]
   FOUND_IN: [sources list]
   RELEVANCE: [HIGH|MEDIUM|LOW]
   HAS_PMCID: [yes|no]
   ABSTRACT_SUMMARY: [2-3 sentences focused on the research question]

---END---

Sort: HIGH→MEDIUM→LOW, newest first within each tier.
~100-150 tokens per entry. Do NOT include full abstracts.
```

#### 3c: Parse the Discovery Manifest

The subagent returns a `DISCOVERY_MANIFEST` with:
- Summary stats (total found, after dedup, sources searched/failed, snowball stats)
- Per-paper entries: title, authors, year, IDs, relevance tier, abstract summary
- Papers sorted HIGH → MEDIUM → LOW, newest first within each tier

Use this manifest for all downstream steps. If the subagent fails, fall back to running search + rank directly in main context (see Error Handling below).

### Step 4: PaperBLAST Cross-Reference via Subagent *(Deep tier, or when genes/proteins are involved)*

> **Launch in parallel with Step 3**: Steps 3 and 4 are independent — spawn both subagents in a **single message** (two Agent tool calls) for efficiency.

When the research question involves specific genes, proteins, enzymes, or pathways, a PaperBLAST subagent queries BERDL's `kescience_paperblast` database and returns a compact gene-literature summary.

> **Context budget**: ~1-3K tokens returned vs. 9.5-40K+ tokens if PaperBLAST SQL ran in the main context.

#### 4a: Extract Gene/Protein Identifiers

From the research question, identify:
- Gene names (e.g., rpoB, dnaA)
- Protein accessions (e.g., NP_*, WP_*)
- Enzyme EC numbers
- Pathway identifiers

#### 4b: Spawn PaperBLAST Subagent

Spawn via `Agent(subagent_type="general-purpose")` with this prompt template (fill `[bracketed]` values):

```
You are a PaperBLAST cross-reference agent. Query BERDL's PaperBLAST database for gene/protein literature and return a compact summary.

RESEARCH QUESTION: [research_question]
GENE/PROTEIN IDENTIFIERS: [list]
ORGANISMS OF INTEREST: [organisms]

AUTH SETUP:
AUTH_TOKEN=$(grep "KBASE_AUTH_TOKEN" .env | cut -d'"' -f2)

SQL via curl:
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "<SQL>", "limit": 1000, "offset": 0}' \
  https://hub.berdl.kbase.us/apis/mcp/delta/tables/query

QUERIES (for each identifier):
1. Gene lookup: SELECT geneId, organism, desc FROM kescience_paperblast.gene WHERE desc LIKE '%[name]%' OR geneId='[accession]' LIMIT 20
2. Gene-paper: SELECT geneId, title, journal, CAST(year AS INT) as year, pmId, doi FROM kescience_paperblast.genepaper WHERE geneId='[geneId]' ORDER BY CAST(year AS INT) DESC LIMIT 20
3. Snippets (top 5 genes): SELECT snippet, pmId, pmcId FROM kescience_paperblast.snippet WHERE geneId='[geneId]' LIMIT 10
4. Curated: SELECT cg.protId, cg.name, cg.desc, cg.organism, cg.comment, cp.pmId FROM kescience_paperblast.curatedgene cg JOIN kescience_paperblast.curatedpaper cp ON cg.db=cp.db AND cg.protId=cp.protId WHERE cg.name LIKE '%[name]%' LIMIT 20
5. GeneRIF: SELECT comment, pmId FROM kescience_paperblast.generif WHERE geneId='[geneId]' LIMIT 10

IMPORTANT: year is STRING — always CAST(year AS INT).

Return EXACTLY:

PAPERBLAST_SUMMARY
GENES_SEARCHED: [N]
GENES_FOUND: [N]
TOTAL_PAPERS: [N unique]
TOTAL_SNIPPETS: [N]

---GENE_RESULTS---

GENE: [name / geneId]
ORGANISM: [organism]
DESCRIPTION: [description]
PAPERS_FOUND: [N]
  PAPER: [title] | [journal] | [year] | PMID:[pmid]
  CURATED: [db]: [description] | PMID:[pmid]
  GENERIF: "[summary]" | PMID:[pmid]
  SNIPPET: "[truncated ~100 chars]..." | PMID:[pmid]

---ALL_PMIDS---
[comma-separated unique PMIDs for cross-referencing]

---END---

Truncate snippets to ~100 chars. If auth fails, report error and stop.
```

#### 4c: Cross-Reference with Discovery Manifest

After both subagents return:
1. Extract `---ALL_PMIDS---` from the PaperBLAST summary
2. Compare against PMIDs in the discovery manifest (Step 3)
3. Categorize:
   - **Confirmed**: PMIDs found in both (confirms relevance)
   - **New from PaperBLAST**: PMIDs not in discovery manifest (add to results)
   - **Discovery-only**: Papers without PaperBLAST gene associations (still relevant for broader context)

If the PaperBLAST subagent fails (auth missing, crash), proceed with discovery results alone (see Error Handling below).

> **Pitfall**: PaperBLAST `year` is stored as a string — always use `CAST(year AS INT)` for comparisons or ordering. Gene IDs span multiple namespaces (RefSeq NP_*, UniProt WP_*, VIMSS) — use `seqtoduplicate` table for cross-referencing.

See `.claude/skills/berdl/modules/paperblast.md` for full table schemas and additional query patterns.

### Step 5: Deep Reading of Key Papers via Subagents *(Standard + Deep tiers only)*

Full-text papers are 5K-20K+ tokens each. Reading them directly in the main context would consume 50K-200K tokens, leaving little room for synthesis. Instead, delegate full-text reading to **subagents** that each return a structured summary (~200-400 tokens).

> **Context budget**: ~200-400 tokens per paper summary vs. 5K-20K+ for raw full text. For 10 papers this reduces context consumption from ~100K tokens to ~3K-5K tokens.

#### 5a: Build the Paper Manifest

From the discovery manifest (Step 3), select the top papers to read in full:

| Field | Description |
|---|---|
| `title` | Paper title |
| `id` | PMID, PMCID, arXiv ID, or DOI |
| `source` | `pubmed`, `arxiv`, `biorxiv`, or `medrxiv` |
| `has_pmcid` | Whether a PMCID is available (from the discovery manifest's `HAS_PMCID` field) |

Standard tier: top 10 papers. Deep tier: top 20 papers.

#### 5b: Spawn Paper-Reader Subagents

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
and note the reason. The main agent will use the abstract summary from the discovery manifest instead.
```

#### 5c: Collect and Tag Results

After all subagents return:
1. Collect each structured extraction
2. Tag each paper as `[FULL TEXT]` or `[ABSTRACT ONLY]` based on the STATUS field
3. For `ABSTRACT_ONLY` papers, use the abstract summary from the discovery manifest for synthesis
4. Use the structured extractions (not raw full text) for the summary in Step 6

**Error handling:**
- **Paper not in PMC**: Subagent returns `STATUS: ABSTRACT_ONLY` — use abstract summary from the discovery manifest
- **MCP tool unavailable**: Subagent returns `ABSTRACT_ONLY` with reason — fall back per the Fallback section
- **PDF extraction fails**: Same `ABSTRACT_ONLY` fallback
- **Subagent timeout/failure**: Note as `ABSTRACT_ONLY`, continue with remaining papers

### Step 5.5: On-Demand Deep Reading *(after presenting the review)*

After the review is presented to the user, if they want deeper analysis of a specific paper, spawn a **single subagent** with an expanded extraction prompt:

- Increase the word limit to **800 words**
- Include the user's specific question about the paper
- Add a `### Detailed Analysis` section addressing the user's question
- Add a `### Future Directions` section (what the authors suggest for follow-up)
- Include more extensive quotes from relevant sections

This keeps the main context clean while allowing drill-down into any paper on demand.

### Step 6: Summarize Findings

Group results by theme and present as a structured summary. The depth of summary should match the review tier.

**Quick scan** — use the basic template below (themes + gaps).

**Standard/Deep review** — use the extended template with methods comparison, quantitative results, and evidence quality indicators.

```markdown
## Literature Review: [Topic]

**Review depth**: [Quick scan | Standard review | Deep review]
**Papers found**: [N total] | **Full text read**: [N] | **Abstract only**: [N] | **PaperBLAST additions**: [N]
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

### PaperBLAST Findings *(if Step 4 was performed)*
- [Gene-specific literature connections found via text mining]
- [PMIDs confirmed by both keyword search and PaperBLAST]
- [New papers found only through PaperBLAST]

### Relevance to BERDL
- [Specific tables/queries that could extend these findings]
- [Which BERDL species overlap with the studies found]
```

### Step 7: Store References

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

### Step 8: Connect to BERDL (optional)

If the literature review reveals organisms, genes, or pathways present in BERDL:

1. Note which BERDL tables contain relevant data
2. Suggest specific queries to test literature findings at scale
3. Identify discrepancies between published results and BERDL data
4. Flag opportunities for novel analysis

## Error Handling

Both discovery and PaperBLAST subagents are **optimizations**, not hard requirements. If a subagent fails, degrade gracefully:

| Failure | Recovery |
|---------|----------|
| Discovery: single source fails | Subagent proceeds with remaining sources (noted in `SOURCES_FAILED`) |
| Discovery: all sources fail | Fall back to WebSearch in main context |
| Discovery: subagent crash | Run search + rank + snowball directly in main context (degraded) |
| PaperBLAST: auth missing | Warn user, proceed without PaperBLAST |
| PaperBLAST: gene not found | Normal — note in summary |
| PaperBLAST: subagent crash | Omit PaperBLAST section, proceed with discovery results |

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
