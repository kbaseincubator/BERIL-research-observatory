---
id: claim.lanthanide-methylotrophy-widespread
title: Lanthanide-dependent methylotrophy is widespread and soil-linked
type: claim
status: draft
summary: XoxF markers are far more common than canonical MxaF markers across the BERDL pangenome, with strong soil/sediment enrichment and important marker-calibration caveats.
source_projects:
  - lanthanide_methylotrophy_atlas
source_docs:
  - projects/lanthanide_methylotrophy_atlas/REPORT.md
  - docs/discoveries.md
related_collections:
  - kbase_ke_pangenome
  - kescience_bacdive
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - topic.critical-minerals
  - direction.rare-earth-cross-metal-inference
  - data.rare-earth-fitness-gap
evidence:
  - source: lanthanide_methylotrophy_atlas
    support: Across 293,059 genomes, xoxF is reported in 3,690 genomes versus 195 mxaF genomes, and the xoxF dominance survives family-weighted and mixed-model phylogenetic checks.
  - source: lanthanide_methylotrophy_atlas
    support: Soil/sediment genomes are significantly enriched for xoxF, while the REE-AMD case study is dominated by acid and metal stress biology rather than methylotrophs.
order: 40
---

# Lanthanide-dependent methylotrophy is widespread and soil-linked

## Claim

Lanthanide-dependent methanol oxidation appears to be much more widespread than the calcium-dependent canonical pathway in the BERDL pangenome, and its strongest broad environmental signal is soil/sediment rather than only rare-earth-impacted sites.

## Evidence

`lanthanide_methylotrophy_atlas` reports an xoxF:mxaF ratio of about 19:1 across 293K genomes, with family-equal-weight and mixed-model checks supporting the direction of the result. It also reports soil/sediment enrichment for xoxF and a descriptive REE-AMD case study where acidophile and metal-stress functions dominate over methylotrophy.

## Why It Matters

This changes the rare-earth section of the Atlas from "zero direct fitness coverage" to a richer state: direct REE RB-TnSeq is still missing, but pangenome marker evidence now identifies candidate taxa, environments, marker pitfalls, and specific experiments.

## Caveats

Marker source matters. The project finds that eggNOG `Preferred_name='lanM'` is unreliable, that KO `K02030` is non-specific for xoxJ, and that Bakta and eggNOG disagree for several REE markers. Direct REE fitness phenotyping remains absent.
