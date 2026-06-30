# Bacillota B Subsurface Accessory

This project compared pangenomes of Bacillota B bacteria isolated from deep clay subsurface environments versus soil baselines to uncover the genetic basis of deep-subsurface specialization. The analysis identified 547 orthologous groups significantly enriched in deep-clay genomes—far exceeding the predicted ~10—with the enriched set dominated by anaerobic respiration, sporulation, and mineral-attachment functions, revealing that subsurface specialization in cultivable Bacillota B is driven by gene-content expansion rather than the genome streamlining observed in other subsurface lineages.

## Key findings

- Keyword-based functional categorization undercounted the anaerobic-niche signal, leaving a large unannotated bucket that manual reclassification suggests holds roughly 80-100 truly anaerobic-respiration OGs. *(confidence: medium)*
- Multi-heme cytochrome PFAMs are sparse within Bacillota_B, so CXXCH heme-binding motif counting on protein sequences carried most of the corrected iron-reduction signal that PFAM-only detection would have missed. *(confidence: medium)*
- With only 10 anchor versus 62 baseline genomes, marginal enrichment effects resting on anchor counts of 3-5 should be treated descriptively rather than inferentially, and genus-level phylogenetic confounding is only partly mitigated. *(confidence: medium)*
- The clay project's sulfate-reduction side of H3 remains robust because its SR markers (K11180, K11181, K00394, K00395, K00958) were correctly identified, even though the iron-reduction narrative loses force after correction. *(confidence: medium)*
- Within cultivable Bacillota_B, deep-clay specialization correlates with gene-content expansion rather than the reductive streamlining seen in Patescibacteria, refuting a universal 'subsurface equals streamlining' model for this niche. *(confidence: medium)*
- Deep-clay Bacillota_B genomes are significantly larger than soil-baseline congeners, encoding roughly 1 Mbp more genetic material at the same CheckM completeness, which rejects the H2 streamlining hypothesis in the opposite direction. *(confidence: high)*
- Per-OG Fisher's exact testing identified 547 eggNOG orthologous groups significantly enriched in deep-clay Bacillota_B versus soil-baseline Bacillota_B, far exceeding the pre-registered H1 prediction of at least 10. *(confidence: high)*
- The companion clay project's iron-reduction markers (K07811, K17324, K17323) were mismatched genes encoding TMAO reductase, glycerol ABC transport, and glycerol permease rather than iron-reduction functions. *(confidence: high)*
- The deep-clay-enriched OGs populate the five pre-registered functional categories (anaerobic respiration, sporulation revival, mineral attachment, regulators, osmoadaptation), with anaerobic respiration the largest annotated hit. *(confidence: high)*
- The molybdopterin-cofactor orthogroup COG1977, a cofactor source for anaerobic-respiration enzymes, was recovered in all ten anchor genomes versus only 11 of 62 baseline genomes, marking a strong subsurface-niche signal. *(confidence: medium)*
- With corrected triple-signal multi-heme cytochrome detection, the clay project's original 'shallow much greater than deep' iron-reduction pattern disappears and no cohort comparison remains statistically significant. *(confidence: high)*
- Combining curated PFAMs with sequence-based CXXCH heme-motif counting provides a reusable BERDL pattern for detecting multi-heme cytochromes when KEGG KO assignment is unreliable, applicable to future iron-reduction and electron-transfer questions across the pangenome. *(confidence: medium)*
- Per-genus decomposition of the H1 enrichment signal, expanded via BacDive linkage to additional clay-isolated genomes, would separate genus-specific lineage markers from recurrent deep-clay signatures and improve statistical power. *(confidence: low)*

## Topics

- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)
- [Topic: Subsurface Genomics](../topics/subsurface-genomics.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)

## Authors

- [David Lyon](../authors/0000-0002-1927-3565.md)

[Open the full report →](../../../projects/bacillota_b_subsurface_accessory/REPORT.md)
