# Counter Ion Effects

This project investigated whether metal salt counter ions (like chloride in CuCl₂) artificially inflate gene fitness overlap between metal toxicity and osmotic stress, confounding the metal fitness signal. Across 19 organisms and 14 metals, the team found that despite 39.8% of metal-important genes also responding to NaCl stress, counter ions are not the primary driver—zinc sulfate (containing zero chloride) shows higher NaCl overlap than most chloride-containing metals, indicating the overlap reflects shared cellular stress biology rather than salt-specific effects. The Metal Fitness Atlas core enrichment conclusions remain robust even after removing shared-stress genes, validating prior findings on metal-responsive genes as genomic core.

## Key findings

- NaCl is not a pure chloride control because it delivers both sodium and chloride, so the NaCl fitness profile includes sodium toxicity and osmotic stress effects beyond chloride. *(confidence: high)*
- Seven metals (manganese, cadmium, selenium, mercury, iron, molybdenum, tungsten) are tested in only one organism (DvH), so their overlap statistics lack cross-organism replication. *(confidence: high)*
- The only within-metal counter ion comparison (psRCH2 CuCl2 vs CuSO4) is severely confounded by aerobic/anaerobic growth, with hundreds of genes differing between conditions independent of copper. *(confidence: high)*
- Researchers using the Metal Fitness Atlas do not need to filter out NaCl-responsive genes, because the atlas core-enrichment conclusions are robust to removing shared-stress genes. *(confidence: high)*
- The metal-NaCl gene overlap reflects shared stress biology—cell envelope damage, ion homeostasis disruption, and general stress response—rather than chloride counter ions. *(confidence: high)*
- Across 19 organisms and 14 metals, 39.8% (4,304/10,821) of metal-important gene fitness records are also important under NaCl stress, indicating substantial shared stress biology between metal and osmotic/ionic stress. *(confidence: high)*
- Across all organisms, 60.2% (6,517/10,821) of metal-important gene records are metal-specific—important for metals but not NaCl—while the remaining shared-stress genes tend to be important across more metals. *(confidence: high)*
- After removing the ~40% shared-stress genes and restricting to metal-specific genes, core genome enrichment is fully preserved for 12 of 14 metals, so the Metal Fitness Atlas core enrichment is not an artifact of shared stress response. *(confidence: high)*
- In DvH, metal-specific genes are more functionally annotated (90.5% with SEED annotations) than shared-stress genes (78.1%), suggesting shared-stress genes include more uncharacterized general stress proteins. *(confidence: medium)*
- In DvH, the metal-NaCl whole-genome fitness correlation hierarchy follows toxicity mechanism rather than chloride dose, with zinc (delivered as sulfate, zero chloride) ranking first. *(confidence: high)*
- Iron stands apart from other metals (NaCl correlation r=0.086) because iron limitation affects specific Fe-dependent enzymes rather than causing general cellular damage. *(confidence: medium)*
- Zinc sulfate (zero chloride) shows higher NaCl overlap (44.6%) than most chloride-delivered metals, so the metal-NaCl overlap does not scale with chloride delivered by the metal salt. *(confidence: high)*
- Comparing metal overlap against choline chloride experiments, which provide chloride without sodium or osmotic effects, would separate chloride from osmotic confounding. *(confidence: medium)*
- Running RB-TnSeq with matched metal chloride and metal sulfate concentrations in a single organism under identical growth conditions would definitively resolve counter ion effects by eliminating the aerobic/anaerobic confound. *(confidence: medium)*

## Topics

- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Metal Resistance](../topics/metal-resistance.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Aindrila Mukhopadhyay](../authors/0000-0002-6513-7425.md)
- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/counter_ion_effects/REPORT.md)
