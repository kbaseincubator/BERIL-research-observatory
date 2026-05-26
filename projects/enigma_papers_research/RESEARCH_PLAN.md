# Research Plan: ENIGMA Papers Research

## Research Question

What are the major scientific contributions of the ENIGMA SFA across its full publication record? What are the key organisms, environments, methods, findings, and open questions?

## Hypotheses

- **H1 (Thematic coherence)**: ENIGMA publications cluster into a small number of well-defined research themes (e.g., subsurface geochemistry, fitness genomics, community ecology, regulatory networks) that have remained consistent over the program's lifetime, with some themes gaining or losing prominence over time.
  - **H0**: Publications are distributed diffusely across topics with no clear thematic structure.

- **H2 (Model organism focus)**: A small set of model organisms (e.g., *Caulobacter crescentus*, *Rhodopseudomonas palustris*, *Shewanella oneidensis*, ORFRC community members) account for the majority of mechanistic studies, while metagenomics-based papers cover a broader community.
  - **H0**: ENIGMA mechanistic studies are spread broadly across organisms with no dominant models.

- **H3 (Methodological innovation)**: RB-TnSeq fitness profiling is a disproportionately cited methodological contribution and appears as a central method in a large fraction of the mechanistic publications.
  - **H0**: No single method dominates the methodological contributions.

## Literature Search Strategy

### Primary Search (PubMed)

Search term: `ENIGMA[Affiliation] OR "Ecosystems and Networks Integrated with Genes and Molecular Assemblies"[All Fields]`

Secondary terms to maximize recall:
- `"Lawrence Berkeley National Laboratory"[Affiliation] AND ("subsurface microbial" OR "fitness library" OR "RB-TnSeq" OR "Oak Ridge Field Research Center")`
- `"ORFRC"[All Fields] AND microbial`

### Secondary Search (Google Scholar)

- `ENIGMA SFA site:lbl.gov`
- `"ENIGMA" "fitness library" microbial`
- Direct author searches for key ENIGMA PIs (Adam Arkin, Aindrila Mukhopadhyay, Trent Northen, Jillian Banfield, etc.)

### Inclusion Criteria

- Peer-reviewed research articles and reviews
- Published in any year
- At least one author with LBNL/ENIGMA affiliation OR explicit ENIGMA acknowledgment
- Primary focus on microbial biology, ecology, genomics, or geochemistry relevant to ENIGMA goals

### Exclusion Criteria

- Book chapters, dissertations, and conference abstracts (unless no journal version exists)
- Papers where ENIGMA affiliation is incidental (e.g., author moved institutions)

## Synthesis Approach

### Thematic Coding Schema

Each paper will be coded for:

| Field | Values |
|-------|--------|
| Theme | fitness_genomics, metagenomics, geochemistry, ecophysiology, regulatory_networks, methodology, field_study, modeling, review |
| Primary organism(s) | free text genus/species |
| Environment | ORFRC_aquifer, lab_culture, soil, other_field, in_silico |
| Method | RB-TnSeq, metagenomics, transcriptomics, proteomics, metabolomics, imaging, modeling, biochemistry |
| Finding class | mechanism, distribution, ecology, tool_development, review |

### Key Questions to Answer in Synthesis

1. What are the 5-10 most-cited / highest-impact ENIGMA papers and what do they establish?
2. Which organisms have the deepest mechanistic characterization?
3. What has ENIGMA contributed to understanding the ORFRC subsurface system specifically?
4. What methodological tools (software, protocols) were developed and are they in broad use?
5. What are the explicit open questions raised in ENIGMA reviews and perspective pieces?
6. How has the program's focus evolved over time (early vs. recent papers)?

## Data Sources

| Source | Purpose |
|--------|---------|
| PubMed | Primary literature search (MCP tool) |
| Google Scholar | Supplementary search; citation counts |
| PubMed Central | Full-text access for open-access papers |
| User-provided list | Ground-truth set if ENIGMA maintains an official publication list |

## Generated Data

| File | Description |
|------|-------------|
| `data/enigma_papers.csv` | Full paper metadata: PMID, title, authors, year, journal, abstract, DOI |
| `data/enigma_papers_coded.csv` | Paper metadata + thematic coding columns |
| `data/theme_summary.csv` | Paper counts by theme, year, organism |
| `data/key_findings.md` | Narrative synthesis of major findings by theme |

## Timeline

1. Paper collection and deduplication (Session 1)
2. Thematic coding (Session 1–2)
3. Synthesis and REPORT.md draft (Session 2–3)
