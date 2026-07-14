```json
{
  "discrepancies": [
    {
      "entry_id": "D-001",
      "type_": "executed-not-prescribed",
      "plan_quote": "---",
      "plan_section": "---",
      "execution_citation": "notebook 02b_h2_hypergeometric_verdict.ipynb — entire notebook created post-hoc in response to adversarial review. Replaces the pre-registered H2 percentage threshold with a hypergeometric enrichment test (scipy.stats.hypergeom) against a genome background rate of 33.25%. Produces NB02b_h2_hypergeometric_verdict.csv.",
      "severity": "load-bearing",
      "recommendation": "The pre-registered H2 threshold ('>=10% phenotype-bearing') was scientifically invalid because the genome background rate (33.25%) exceeded it. The hypergeometric recalibration is methodologically sound but constitutes a post-hoc change to a pre-registered threshold. Document the threshold revision, its rationale, and the adversarial review citation explicitly in the Methods section."
    },
    {
      "entry_id": "D-002",
      "type_": "plan-prescribed-not-executed",
      "plan_quote": ">=10% of Fur-released DEGs (from NB01 or 4584-vs-4580) score 'phenotype-bearing' --- |fitness t-score|>4 in >=2 envelope-stress OR iron-limitation experiments",
      "plan_section": "Pre-registered significance thresholds, H2 critical Fur subset",
      "execution_citation": "NB02b replaces this threshold with hypergeometric fold-enrichment >= 1.5x AND p < 0.05 vs genome background. Path A: SUPPORTED (fold=1.60x, p=0.016); Path B: NOT SUPPORTED (fold=1.04x, p=0.515).",
      "severity": "load-bearing",
      "recommendation": "The original pre-registered threshold was below genome background and therefore uninformative. The replacement is justified but must be disclosed as a deviation from the pre-registration. Add a 'Deviations from pre-registration' subsection to Methods."
    },
    {
      "entry_id": "D-003",
      "type_": "executed-not-prescribed",
      "plan_quote": "---",
      "plan_section": "---",
      "execution_citation": "notebook 06b_ncbi_annotation_presence.ipynb — created to remediate ~50% false-negative rate in NB06's PaperBLAST-based comparative annotation. Uses NCBI Entrez protein annotation queries (Biopython) across 28 gene families and 4 species. Produces NB06b_ncbi_presence_counts.csv, NB06b_ncbi_presence_bool.csv, NB06b_paperblast_vs_ncbi_comparison.csv.",
      "severity": "load-bearing",
      "recommendation": "NB06b corrects a critical method failure in NB06 (PaperBLAST missed LpxA, LpxC, LptA, LptB, LptD, LptE in C. crescentus despite known presence). The NCBI remediation is necessary. Document both methods and the discordance analysis in Methods; note that the comparative arm conclusions rest on NB06b, not NB06 alone."
    },
    {
      "entry_id": "D-004",
      "type_": "plan-prescribed-not-executed",
      "plan_quote": "query each pangenome database for species coverage ... Try kbase_ke_pangenome, kbase_uniprot (any species-keyed table), and phagefoundry.acinetobacter for A. baumannii specifically.",
      "plan_section": "NB06 -- Comparative-species arm, Approach step 1 (BERDL coverage preflight)",
      "execution_citation": "NB06 queries kescience_paperblast.gene (description-regex matching on organism and gene family) instead of kbase_ke_pangenome or kbase_uniprot. No pangenome-level orthology was performed.",
      "severity": "load-bearing",
      "recommendation": "PaperBLAST description-matching is annotation-dependent and yielded a ~50% false-negative rate on known Caulobacter genes. The plan specified pangenome orthology databases (kbase_ke_pangenome) which would have used sequence-level homology. If pangenome databases lacked the target species, document the coverage check that led to the PaperBLAST fallback. Clarify in Methods that comparative claims are annotation-based, not sequence-homology-based."
    },
    {
      "entry_id": "D-005",
      "type_": "plan-prescribed-not-executed",
      "plan_quote": "run hmmsearch (HMMER 3) for each focal gene family (Pfam HMMs for serine-palmitoyltransferase PF00155, LptF/G PF03739, LpxC PF03331, Fur PF01475, CtpA C-terminal protease PF00574), tabulate hits per genome.",
      "plan_section": "NB06 -- Comparative-species arm, Approach step 2 (NCBI fallback)",
      "execution_citation": "NB06b uses NCBI Entrez protein keyword searches (Biopython Bio.Entrez.esearch) instead of hmmsearch with Pfam HMM profiles. No profile-HMM-based homology search was performed.",
      "severity": "load-bearing",
      "recommendation": "Pfam HMM profiles are more sensitive than keyword annotation search for detecting distant homologs, which is critical when the paper claims a gene family is 'absent' in a species. NCBI Entrez keyword search depends on annotation completeness and may produce false negatives (e.g., unannotated or divergently annotated homologs). The paper's 'uniquely Caulobacter' claim for sphingolipid biosynthesis genes should note this sensitivity limitation. Consider running hmmsearch on the 6 named reference genomes as a validation step."
    },
    {
      "entry_id": "D-006",
      "type_": "plan-prescribed-not-executed",
      "plan_quote": "Functional annotation enrichment of each partition (use existing GO terms file + paperBLAST where useful).",
      "plan_section": "NB03 -- ChvI regulon dissection and SigU, Approach step 2",
      "execution_citation": "NB03 uses keyword-based regex functional annotation (KEYWORD_SETS dictionary with categories like 'TBDT / OM receptor', 'envelope / OM', 'transport (ABC, MFS)', 'PG / cell wall') instead of formal GO enrichment. Notebook states: 'No GO annotation is available repo-wide.'",
      "severity": "unclear",
      "recommendation": "Keyword regex matching is less rigorous than formal GO enrichment (no controlled vocabulary, no multiple-testing correction across categories, no hierarchical structure). However, if no GO annotation file exists for this organism, the substitution is pragmatic. Verify whether a GO annotation file could be obtained (e.g., from UniProt or InterProScan) and note the limitation in Methods."
    },
    {
      "entry_id": "D-007",
      "type_": "plan-prescribed-not-executed",
      "plan_quote": "Identify Caulobacter SigU regulon members (literature + paperBLAST query) and test overlap with the late/consequence subset.",
      "plan_section": "NB03 -- ChvI regulon dissection and SigU, Approach step 3",
      "execution_citation": "NB03 performed a paperBLAST literature scout for SigU/CCNA_02977 which returned zero substantive Caulobacter SigU regulon members (documented in NB03_sigU_literature_gap.md). The SigU overlap test was reframed as a 'functional coherence test' using keyword theme enrichment (Fisher's exact test) rather than a regulon-membership overlap.",
      "severity": "unclear",
      "recommendation": "The plan assumed a published SigU regulon exists; it does not. The reframing is scientifically defensible but changes the nature of the H1 phase-structure test from 'SigU regulon overlap' to 'thematic coherence of late cohort.' Document the literature gap and the reframing rationale explicitly. The pre-registered threshold ('SigU regulon overlaps the late-cohort at hypergeometric p<1e-3') cannot be evaluated as stated."
    },
    {
      "entry_id": "D-008",
      "type_": "plan-prescribed-not-executed",
      "plan_quote": "Cross-reference the A. baumannii PBP1A and LdtJ/LdtK orthologs in Caulobacter (paperBLAST + BLAST against canonical sequences).",
      "plan_section": "NB05 -- Peptidoglycan remodeling (H4), Approach step 3",
      "execution_citation": "NB05 cites Kang et al. 2021 (PMID 33402533) for the A. baumannii PBP1A/LdtJ/LdtK route but does not perform any computational ortholog identification (no BLAST, no paperBLAST query, no sequence-based search). The comparison is narrative only.",
      "severity": "unclear",
      "recommendation": "The plan prescribed a computational cross-reference to determine whether Caulobacter PG-remodeling genes are orthologous to the A. baumannii PBP1A/LdtJ/LdtK route. Without this, the H4 claim that Caulobacter PG remodeling is 'mechanistically distinct from' the A. baumannii route rests on literature citation alone, not on sequence evidence. Either perform the planned BLAST search or soften the comparative claim to 'literature-based comparison.'"
    },
    {
      "entry_id": "D-009",
      "type_": "executed-not-prescribed",
      "plan_quote": "---",
      "plan_section": "---",
      "execution_citation": "notebook 01_leaden2018_fur_signature.ipynb cells 4-5 compute Pearson correlation (scipy.stats.pearsonr: r=0.453, p=5.27e-06) alongside the prescribed Spearman correlation. Additionally, NB01 produces an iron-limitation vs Dfur scatter (figures/NB01_leaden_iron_vs_fur.png, Spearman rho=0.771) and data/NB01_leaden_iron_de.csv (491 iron-limitation DEGs) --- neither prescribed in the plan.",
      "severity": "cosmetic",
      "recommendation": "The additional Pearson correlation and iron-limitation analysis are supplementary and do not conflict with the planned Spearman stop-condition check. Ensure the paper does not cite the Pearson r as the primary concordance metric (the pre-registered stop condition uses Spearman). The iron-limitation analysis adds useful context but should be noted as exploratory."
    },
    {
      "entry_id": "D-010",
      "type_": "cosmetic",
      "plan_quote": "Hypergeometric p<1e-5 for ChvI-induced intersection up-DEG in either contrast (Stein OR QY set).",
      "plan_section": "Pre-registered significance thresholds, H1 ChvI engagement",
      "execution_citation": "NB03 cell 10 uses scipy.stats.fisher_exact (alternative='greater') for the enrichment test rather than scipy.stats.hypergeom.",
      "severity": "cosmetic",
      "recommendation": "Fisher's exact test (one-sided, alternative='greater') is mathematically equivalent to the one-tailed hypergeometric test for set-overlap enrichment. No action required, but for consistency with pre-registered language, the Methods section should note 'Fisher's exact test (equivalent to one-tailed hypergeometric)' rather than presenting it as a different test."
    },
    {
      "entry_id": "D-011",
      "type_": "plan-prescribed-not-executed",
      "plan_quote": "Compute coverage caveats (does the OM proteome detect any of these inner-membrane proteins?).",
      "plan_section": "NB04 -- Sphingolipid flux, CtpA, and the canonical Lpt apparatus, Approach step 3",
      "execution_citation": "NB04 includes a qualitative note ('sphingolipid biosynthesis enzymes are IM/cytoplasmic --- expected absence from OM prep') and reports 5/15 sphingolipid genes detected in OM proteome, but does not perform a formal coverage analysis (e.g., fraction of known IM proteins detected, expected recovery rate, detection bias quantification).",
      "severity": "cosmetic",
      "recommendation": "The qualitative caveat is adequate for the current claims (no CtpA protein detection is noted as a limitation). A formal coverage analysis would strengthen the Discussion but is not required for the core H3 conclusions. Note the single-replicate proteome limitation in the same paragraph."
    },
    {
      "entry_id": "D-012",
      "type_": "plan-prescribed-not-executed",
      "plan_quote": "Optional: AlphaFold structural overlay of CtpA vs LpxF (just inspection --- no structural claim made).",
      "plan_section": "NB04 -- Sphingolipid flux, CtpA, and the canonical Lpt apparatus, Approach step 4",
      "execution_citation": "No AlphaFold analysis appears in NB04 or any other notebook. kescience_alphafold was not queried.",
      "severity": "cosmetic",
      "recommendation": "Marked optional in the plan. No action required unless the paper makes structural claims about CtpA/LpxF functional equivalence. If the CtpA substitutability claim is retained, consider adding this analysis or citing Zik 2022's published evidence directly."
    }
  ]
}
```
