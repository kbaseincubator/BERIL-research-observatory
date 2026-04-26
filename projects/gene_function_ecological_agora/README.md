# Gene Function Ecological Agora

*Innovation Atlas Across the Bacterial Tree*

## Research Question

Across the prokaryotic tree (GTDB r214; 293,059 genomes / 27,690 species), do clades specialize in the *kind* of functional innovation they produce, and is the producer/consumer asymmetry observed by Alm, Huang & Arkin (2006) for two-component systems a general feature of regulatory function classes but not metabolic ones?

## Status

In Progress — research plan and design notes written; awaiting Phase 1 data extraction.

## Overview

A three-phase, multi-resolution atlas of clade-level functional innovation across GTDB r214. The atlas is built at three resolutions in a forced order: sequence-only (UniRef50), functional (KO), and architectural (Pfam multidomain architecture). Each phase's output gates and refines the next; the final synthesis cross-validates quadrant assignments across resolutions.

The atlas tests whether bacterial clades populate four quadrants — Closed Innovator, Broker, Sink, Open Innovator — for any function class, with three pre-registered weak-prior hypotheses spanning the regulatory-vs-metabolic divide:

- **Phase 1** (UniRef50): Bacteroidota → Open Innovator on PUL CAZymes
- **Phase 2** (KO): Mycobacteriota → Closed Innovator on mycolic-acid pathway
- **Phase 3** (Pfam architecture): Cyanobacteria → Broker on PSII architectures

The Alm 2006 two-component-system back-test is mandatory at Phases 2 and 3.

Total budget ~16 agent-weeks with three natural stop-points (publishable at the end of each of Phases 1, 2, 3) plus a final synthesis (Phase 4).

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — operational plan: phases, axis positions, hypotheses, query strategy
- [Design Notes](DESIGN_NOTES.md) — design record: critique of the brief, through-line argument, rejected alternatives, weak-prior acknowledgement
- [Report](REPORT.md) — *(to be written at Phase 4 synthesis)*

## Reproduction

*TBD — add prerequisites and step-by-step instructions after Phase 1 is complete.*

Will require:
- BERDL JupyterHub (Spark on-cluster)
- KBASE_AUTH_TOKEN in `.env`
- GTDB r214 species tree (newick) loaded externally from `https://data.gtdb.ecogenomic.org/releases/release214/`
- Python deps in `requirements.txt`

## Authors

- **Adam Arkin**
  - ORCID: 0000-0002-4999-2931
  - Affiliation: U.C. Berkeley / Lawrence Berkeley National Laboratory
