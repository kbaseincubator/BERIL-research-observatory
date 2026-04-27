# Gene Function Ecological Agora

*Innovation Atlas Across the Bacterial Tree*

## Research Question

Across the prokaryotic tree (GTDB r214; 293,059 genomes / 27,690 species), do clades specialize in the *kind* of functional innovation they produce, and is the producer/consumer asymmetry observed by Alm, Huang & Arkin (2006) for two-component systems a general feature of regulatory function classes but not metabolic ones?

## Status

**Phase 1A complete (2026-04-26): `PASS_WITH_REVISION`.** Methodology validated on a 1,000-species × 1,200-UniRef50 pilot. Four methodology revisions (M1–M4) documented for Phase 1B.

**Phase 1B complete (2026-04-27): `PASS_REFRAMED` + qualified pass via tree-aware diagnostic.** Methodology validated at full GTDB scale (18,989 bacterial species × 100,192 UniRef50s × 5 ranks = 1.29 M producer scores; ~1 hour wall time). Pre-registered Bacteroidota PUL Innovator-Exchange hypothesis falsified at the absolute-zero criterion (0/4 deep ranks). Post-gate work surfaced two further corrections:

- **A close re-reading of Alm 2006** (`docs/alm_2006_methodology_comparison.md`) showed the project had been mis-stating Alm 2006's methodology in three load-bearing ways. The four-quadrant framework is *this project's construction*, not Alm 2006's; they worked at single-domain level (≈ UniRef50, comparable to ours, not at "family"); they used phylogenetic-tree-aware reconciliation (we had been using parent-rank dispersion permutation null).
- **A tree-aware diagnostic** (Sankoff parsimony on the GTDB-r214 tree, NB08c) recovers the expected direction (positive HGT > negative housekeeping at p = 2.1×10⁻⁵) where parent-rank dispersion had produced the order-rank anomaly. **Methodology framework not broken; the metric was wrong.** But effect size at UniRef50 remains small (Cohen's d = 0.15; below the d ≥ 0.3 threshold). Phase 2 KO aggregation must amplify to d ≥ 0.3 or the substrate-hierarchy claim is falsified and an M11 reconciliation-based redesign triggers.

Eighteen methodology revisions across Phase 1A → 1B (M1–M18) baked into Phase 2. Three pre-registration omissions surfaced and corrected as project-discipline lessons (M2 dosage biology, M12 absolute-zero criterion, M14 misreading-of-Alm-2006).

See [REPORT.md](REPORT.md) for both milestone reports + diagnostic resolutions; [data/p1a_phase_gate_summary.md](data/p1a_phase_gate_summary.md) + [data/p1b_phase_gate_summary.md](data/p1b_phase_gate_summary.md) for formal gate decisions; [docs/alm_2006_methodology_comparison.md](../../docs/alm_2006_methodology_comparison.md) for the BERIL-level methodology memo.

**Phase 2 in planning** (KO functional aggregation; Sankoff parsimony as primary atlas metric; hard d ≥ 0.3 amplification gate).

## Overview

A multi-phase, multi-resolution atlas of clade-level functional innovation across GTDB r214. The atlas is built at three resolutions in a forced order: sequence-only (UniRef50), functional (KO), and architectural (Pfam multidomain architecture). Each phase's output gates and refines the next; the final synthesis cross-validates assignments across resolutions.

**At deep ranks (≥ family)** the atlas reports **Producer × Participation categories** (Innovator-Isolated / Innovator-Exchange / Sink/Broker-Exchange / Stable) — direction-agnostic because per-family DTL reconciliation is out of scope at full GTDB scale. **At genus rank** Phase 3 runs composition-based donor inference on the architectural deep-dive candidate set, producing the full four-quadrant labels (Open / Broker / Sink / Closed) on that subset.

Four pre-registered weak-prior hypotheses span the regulatory-vs-metabolic divide:

- **Phase 1A pilot**: positive controls (AMR, CRISPR-Cas, Alm 2006 TCS) + negative controls (ribosomal, tRNA-synthetase, RNAP) validate methodology on 1K species × 1K UniRef50s
- **Phase 1B** (UniRef50): Bacteroidota → Innovator-Exchange on PUL CAZymes (deep-rank)
- **Phase 2** (KO): Mycobacteriota → Innovator-Isolated on mycolic-acid pathway (deep-rank)
- **Phase 3** (Pfam architecture): Cyanobacteria → Broker on PSII architectures (genus-rank, with donor inference)
- **Phases 2 & 3**: Alm 2006 two-component-system back-test (KO + architectural)

Total budget ~17 agent-weeks with four natural stop-points (Phase 1A pilot, Phase 1B, Phase 2, Phase 3) plus a final synthesis (Phase 4).

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — operational plan: phases, axis positions, hypotheses, query strategy
- [Design Notes](DESIGN_NOTES.md) — design record: critique of the brief, through-line argument, rejected alternatives, weak-prior acknowledgement
- [Report](REPORT.md) — Phase 1A milestone report; will expand as Phases 1B–4 land
- [Phase 1A Gate Summary](data/p1a_phase_gate_summary.md) — formal Phase 1A → 1B gate decision with M1–M4 revisions

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
