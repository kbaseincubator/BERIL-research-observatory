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

## Review Brief

What changed: this claim adds genomic rare-earth biology to an Atlas area that previously emphasized missing REE fitness data.

Why review matters: reviewers should decide whether the pangenome marker evidence is strong enough to guide rare-earth experiment design, while keeping direct REE fitness as an explicit gap.

Evidence to inspect:

- xoxF versus mxaF prevalence across the pangenome.
- Family-weighted and mixed-model checks that reduce phylogenetic overcounting.
- Soil/sediment enrichment for xoxF.
- Marker-source disagreements for `lanM`, xoxJ, Bakta, eggNOG, and KO annotations.

Questions for reviewers:

- Is the claim wording too broad, or does it correctly say "methylotrophy marker evidence" rather than measured REE fitness?
- Which marker source should be treated as canonical for lanmodulin and xox-family screening?
- Should the REE-AMD case study be treated as negative evidence for methylotrophy at contaminated rare-earth sites, or only as a site-specific stress signal?
- What taxon or condition should be prioritized for the first REE RB-TnSeq experiment?

## Evidence

`lanthanide_methylotrophy_atlas` reports an xoxF:mxaF ratio of about 19:1 across 293K genomes, with family-equal-weight and mixed-model checks supporting the direction of the result. It also reports soil/sediment enrichment for xoxF and a descriptive REE-AMD case study where acidophile and metal-stress functions dominate over methylotrophy.

## Why It Matters

This changes the rare-earth section of the Atlas from "zero direct fitness coverage" to a richer state: direct REE RB-TnSeq is still missing, but pangenome marker evidence now identifies candidate taxa, environments, marker pitfalls, and specific experiments.

## Caveats

Marker source matters. The project finds that eggNOG `Preferred_name='lanM'` is unreliable, that KO `K02030` is non-specific for xoxJ, and that Bakta and eggNOG disagree for several REE markers. Direct REE fitness phenotyping remains absent.

## Promotion Criteria

Promote this claim only after a reviewer confirms the marker definitions and agrees that the claim is about genomic potential and environmental enrichment, not direct rare-earth-dependent fitness.
