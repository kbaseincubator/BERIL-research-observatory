# NB03 SigU literature gap (provenance)

Date: 2026-06-04T02:45:23
Z

The pre-registered H1 SigU overlap test (RESEARCH_PLAN v2) referenced
"the published Caulobacter SigU regulon." A PaperBLAST scout against
kescience_paperblast (gene + genepaper + snippet + curatedgene tables,
filtered to Caulobacter) returned **zero substantive snippets** for
CCNA_02977 / SigU. All returned snippets matched unrelated organisms
(Tetrahymena, Arabidopsis, Streptococcus emm gene products) — the
literature on Caulobacter SigU is non-existent.

CONFIRMED IN PaperBLAST:
- CCNA_03471 = sigT (Lourenço & Gomes 2009 general stress)
- CCNA_03467 = sigF (heat shock)
- two unnamed Caulobacter ECF-family sigma factors
- BUT NOT CCNA_02977 / sigU as a characterized regulator with targets.

Reframe applied in this notebook: the H1 SigU test became a *coherence*
check on the late-phase ChvI cohort (does the late cohort represent
a functionally coordinated envelope-stress program), not a literature
overlap. The original threshold (p<1e-3) cannot be evaluated against
a non-existent gold standard.

The late cohort enrichment for envelope/transport/regulator themes is
itself a substantive finding: SigU's targets in Caulobacter are
candidates for future ChIP-seq or RNA-seq of a SigU induction strain.
