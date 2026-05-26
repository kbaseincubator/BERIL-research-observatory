# ENIGMA Papers Research

## Research Question

What are the major scientific contributions of the ENIGMA (Ecosystems and Networks Integrated with Genes and Molecular Assemblies) SFA, spanning the full publication record? What organisms, communities, environments, methodologies, and key findings define the program's scientific legacy, and what open questions remain?

## Status

In progress — see [Research Plan](RESEARCH_PLAN.md) for approach.

## Overview

ENIGMA is a DOE Office of Biological and Environmental Research Scientific Focus Area (SFA) based at Lawrence Berkeley National Laboratory. The program studies how microbial communities in subsurface and other environments respond to physical and chemical stresses, with flagship field work at the Oak Ridge Field Research Center (ORFRC) in Tennessee (uranium/heavy-metal contaminated aquifer) and laboratory investigations spanning fitness genomics, genome-resolved metagenomics, regulatory networks, and ecological modeling.

This project performs a systematic literature review and synthesis of all ENIGMA publications, cataloging:
- Key organisms studied (e.g., *Caulobacter*, *Rhodopseudomonas*, *Cupriavidus*, ORFRC community members)
- Environmental systems and field sites
- Core methodological innovations (RB-TnSeq, fitness libraries, metagenomics, ecophysiology)
- Major findings by research theme
- Open questions and future directions

## Data Collections

- PubMed (primary literature search via MCP tools)
- Google Scholar (supplementary coverage)
- ENIGMA publications list (user-provided if available)

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypotheses, search strategy, synthesis approach
- [Report](REPORT.md) — findings and synthesis (TBD)

## Reproduction

**Prerequisites**:
- Internet access for PubMed/Google Scholar queries via MCP tools

**Pipeline**:

1. `notebooks/01_paper_collection.ipynb` — Systematic PubMed search for ENIGMA publications; export metadata to `data/enigma_papers.csv`
2. `notebooks/02_thematic_coding.ipynb` — Categorize papers by organism, environment, method, and theme
3. `notebooks/03_synthesis.ipynb` — Cross-paper synthesis; identify major findings and gaps

All output CSVs are committed to `data/`.
