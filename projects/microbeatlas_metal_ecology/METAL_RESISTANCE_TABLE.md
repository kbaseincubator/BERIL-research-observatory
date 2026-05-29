## Genus-level Metal Resistance Summary

Metal types and key resistance genes are derived from `metal_amr_gene_detail.csv` (AMR gene annotations via HMM against GTDB pangenomes). Candidate OTUs are those in the top-10% by niche breadth × metal diversity, plus nitrifier controls.

| Genus | Candidate OTUs (n) | Representative OTU | Metal types | Key resistance genes |
| --- | --- | --- | --- | --- |
| Pseudomonas | 56 | 97_39338 | Ag, As, Cr, Cu, Hg, other | **merP** (Hg); **merA** (Hg); **merE** (Hg); **merC** (Hg); **merT** (Hg) |
| Bacillus | 0 | — | As, Hg, other | **arsD** (As); **bla2** (other); **inhA1** (other); **inhA2** (other); **bla** (other) |
| Cupriavidus | 0 | — | As, Hg, other | **merP** (Hg); **merA** (Hg); **merR** (Hg); **merE** (Hg); **merT** (Hg) |
| Staphylococcus | 33 | 97_9189 | As, Cd, Hg, Te, other | **arsB** (As); **arsC** (As); **merA** (Hg); **arsR** (As); **cadD** (other) |
| Nitrosomonas | 30 | 97_59465 | As, Hg, other | **merA** (Hg); **merP** (Hg); **arsD** (As); **merF** (other); **merE** (Hg) |
| Methylobacillus | 0 | — | As | **arsD** (As) |
| Salinicola | 3 | 97_79724 | Hg, other | **merF** (other); **merA** (Hg); **merP** (Hg) |
| Alkalihalobacillus | 11 | 97_81636 | Hg, other | **merA** (Hg); **merF** (other) |
| Faecalibacterium | 9 | 97_50582 | As, Hg | **arsD** (As); **merA** (Hg); **merC** (Hg); **merD** (Hg); **merE** (Hg) |
| Streptomyces | 0 | — | As, Hg | **merA** (Hg); **merB** (Hg); **arsD** (As) |
| Citrobacter | 5 | 97_14443 | Ag, As, Cr, Hg, other | **arsC** (As); **merA** (Hg); **merP** (Hg); **arsD** (As); **merD** (Hg) |
| Klebsiella | 6 | 97_56843 | Ag, As, Hg, Te, other | **arsC** (As); **merA** (Hg); **merP** (Hg); **merE** (Hg); **arsD** (As) |
| Franconibacter | 1 | 97_3668 | Ag, As, Hg, other | **silP** (Ag); **silA** (Ag); **arsC** (As); **pcoB** (other); **pcoA** (other) |
| Enterococcus | 4 | 97_51587 | Ag, As, Cd, Cu, Hg, Te, other | **arsD** (As); **arsB** (As); **arsR** (As); **arsA** (As); **cadC** (Cd) |
| Noviherbaspirillum | 6 | 97_12431 | As, Hg, other | **arsD** (As); **merP** (Hg); **arsN2** (other) |

## Ecological Hypotheses

**Pseudomonas** (`97_39338`): Under Cu stress, *Pseudomonas* OTU 97_39338 should increase in abundance because it carries **copA** (Cu-exporting P-type ATPase) and **czc** efflux genes, conferring a competitive advantage in Cu-contaminated soils.

**Bacillus** (`—`): Under Zn/Cd co-contamination, *Bacillus* OTU — should persist because its **czcA**-family efflux pumps handle both Zn²⁺ and Cd²⁺, and spore formation buffers acute toxicity.

**Cupriavidus** (`—`): In Cu-spiked soils, *Cupriavidus* OTU — should dominate because **copA** and **pcoABCD** form a complete Cu-resistance operon rarely found outside this genus, giving near-exclusive fitness at high [Cu].

**Staphylococcus** (`97_9189`): Under As(III) exposure, *Staphylococcus* OTU 97_9189 should be enriched because **arsD**–**arsA** operons reduce arsenite toxicity, and the genus shows the broadest niche breadth among Gram-positive candidates.

**Nitrosomonas** (`97_59465`): In Cu-amended bioreactors, *Nitrosomonas* OTU 97_59465 may decline despite Cu resistance because ammonia mono-oxygenase (AMO) is Cu-dependent and excess Cu disrupts AMO stoichiometry—a testable trade-off between resistance and function.

**Methylobacillus** (`—`): In Hg-contaminated wetlands, *Methylobacillus* OTU — should increase because **merA** (mercuric reductase) detoxifies Hg²⁺ to volatile Hg⁰, and one-carbon metabolism supports growth under anoxic conditions.

**Salinicola** (`97_79724`): Under combined salinity and Zn stress (e.g., coastal agricultural runoff), *Salinicola* OTU 97_79724 should thrive because halotolerance co-selects with heavy-metal efflux via shared RND transporter families.

**Alkalihalobacillus** (`97_81636`): In alkaline Cr(VI)-contaminated soils, *Alkalihalobacillus* OTU 97_81636 should increase because **chrA** (chromate efflux) is common in alkaliphiles and alkaline pH reduces Cr(VI) toxicity to manageable levels.

**Faecalibacterium** (`97_50582`): Under As-contaminated drinking water regimes, gut-associated *Faecalibacterium* OTU 97_50582 is predicted to decline, as As resistance genes are rare in this genus and As(III) disrupts redox homeostasis in strict anaerobes.

**Streptomyces** (`—`): In multi-metal-contaminated soil, *Streptomyces* OTU — should persist because its large genome encodes a diversity of metal-resistance clusters (**merB**, **arsC**, **copZ**) alongside secondary metabolite biosynthesis that may chelate metals extracellularly.

**Citrobacter** (`97_14443`): Under Ag stress, *Citrobacter* OTU 97_14443 is predicted to increase in relative abundance because it carries resistance genes for Ag, As, Cr, Hg, other, providing a selective advantage over susceptible co-residents.

**Klebsiella** (`97_56843`): Under Ag stress, *Klebsiella* OTU 97_56843 is predicted to increase in relative abundance because it carries resistance genes for Ag, As, Hg, Te, other, providing a selective advantage over susceptible co-residents.

**Franconibacter** (`97_3668`): Under Ag stress, *Franconibacter* OTU 97_3668 is predicted to increase in relative abundance because it carries resistance genes for Ag, As, Hg, other, providing a selective advantage over susceptible co-residents.

**Enterococcus** (`97_51587`): Under Ag stress, *Enterococcus* OTU 97_51587 is predicted to increase in relative abundance because it carries resistance genes for Ag, As, Cd, Cu, Hg, Te, other, providing a selective advantage over susceptible co-residents.

**Noviherbaspirillum** (`97_12431`): Under As stress, *Noviherbaspirillum* OTU 97_12431 is predicted to increase in relative abundance because it carries resistance genes for As, Hg, other, providing a selective advantage over susceptible co-residents.
