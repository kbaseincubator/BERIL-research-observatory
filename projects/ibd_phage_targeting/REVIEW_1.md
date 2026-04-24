---
reviewer: BERIL Automated Review (Claude, claude-sonnet-4-20250514)
date: 2026-04-24
project: ibd_phage_targeting
---

# Review: Metagenome-Prioritized Phage Cocktails for Crohn's Disease and IBD

## Summary

This is an exceptionally well-designed and methodologically rigorous project that addresses a clinically important question: how to design personalized phage cocktails for IBD patients based on microbiome stratification. The work demonstrates sophisticated understanding of compositional data analysis, ecotype discovery methods, and the pitfalls of pooled differential abundance testing. While only Pillar 1 (patient stratification) is complete, the foundation established is scientifically sound and the approach is methodologically exemplary. The project successfully develops a four-ecotype IBD framework and projects UC Davis patients onto it, providing the foundation for subsequent pathobiont targeting. The documentation quality, reproducibility practices, and attention to methodological details set a high standard.

## Methodology

**Research Question**: The multi-part question is clearly stated and testable: identify bacterial pathobionts that are enriched, ubiquitous, and non-protective within distinct patient subgroups, and determine which are tractable phage therapy targets.

**Approach Soundness**: The five-pillar analytical framework is well-designed:
1. **Patient stratification** using rigorous ecotype discovery (LDA + GMM with cross-method validation)
2. **Within-ecotype pathobiont identification** using compositional-aware DA  
3. **Functional drivers** through pathway/metabolite/BGC analysis
4. **Phage targetability** assessment via coverage matrices
5. **Per-patient cocktail design** for UC Davis cohort

**Data Sources**: Exceptionally well-documented with 12+ integrated databases from BERDL ecosystem. The local `~/data/CrohnsPhage` mart (33 tables, schema v2.4) provides comprehensive integration of taxonomic, functional, clinical, and viromics data.

**Reproducibility Strengths**: 
- **Taxonomy synonymy layer**: The 2,417-alias → 1,848-canonical species mapping (`data/species_synonymy.tsv`) addresses a critical cross-cohort integration pitfall
- **Methodological rigor**: Cross-method ARI for K-selection, held-out validation for LDA, compositional-aware DA with CLR transformation
- **Pitfall awareness**: Directly addresses known issues from `docs/pitfalls.md` including compositional bias, taxonomy reconciliation, and strain name collisions

**Novel Methodological Contributions**:
- Cross-method ARI as K-selection criterion when per-method metrics are monotonic
- Documentation of Kaiju ↔ MetaPhlAn3 projection asymmetry (LDA robust, GMM fragile)
- Quantification of OvR-AUC vs. patient-level agreement gap in pooled classifier validation

## Code Quality

**Statistical Methods**: Appropriate and sophisticated. The compositional-aware differential abundance (CLR + Mann-Whitney) properly addresses the sum-to-constant constraint that biases raw relative abundance testing. The ecotype discovery using both LDA and GMM with cross-validation represents best practices.

**SQL/Data Management**: The local mart approach avoids large Spark queries while maintaining data lineage. Table schemas are well-documented in `data/table_schemas.md`.

**Notebook Organization**: Excellent. Each notebook has clear purpose, proper imports, saved outputs, and logical flow from setup → analysis → visualization. The NB00 data audit establishing compositional DA proof-of-concept before ecotype training shows good analytical planning.

**Pitfall Handling**: Exemplary attention to known issues:
- Taxonomy synonymy reconciliation prevents log₂FC ≈ 28 artifacts from genus renames
- Compositional correction recovers protective species depletion signals missed by raw Mann-Whitney
- Proper handling of MetaPhlAn3 vs. Kaiju classifier differences in projection

**Code Documentation**: Every function and analysis step is clearly documented. The progression from proof-of-concept (NB00) to final implementation (NB01b) shows iterative refinement.

## Findings Assessment

**Pillar 1 Deliverables** (completed and well-supported):

1. **Four reproducible ecotypes**: K=4 consensus from cross-method ARI maximization. Biologically interpretable as diverse-commensal (E0), Bacteroides-transitional (E1), Prevotella enterotype (E2), and severe Bacteroides-expanded (E3).

2. **UC Davis projection**: Non-random distribution (χ² p=0.019) across E0 (27%), E1 (42%), E3 (31%), E2 (0%), consistent with Western active-disease cohort expectations.

3. **Clinical classifier limitation**: AUC 0.80 on pooled data but only 41% agreement with metagenomic assignments on UC Davis patients. The classifier collapses to "IBD → E1" because `is_ibd` dominates training, highlighting that metagenomics remains necessary for ecotype assignment.

4. **Compositional artifact quantification**: CLR correction recovers protective species depletion signals (F. prausnitzii, A. muciniphila, R. hominis) and corrects R. intestinalis sign flip, but C. scindens paradox persists, requiring the planned within-ecotype stratification.

**Conclusion Support**: All findings are well-supported by data and appropriately interpreted. The acknowledgment that compositional correction alone doesn't resolve the C. scindens paradox sets up the logical next experiment (within-ecotype DA in NB04).

**Limitations Properly Acknowledged**: Small UC Davis cohort (n=23), Kaiju vs. MetaPhlAn3 classifier mismatch, HMP2 data not yet reprocessed, incomplete coverage of all pathobiont strains in MAG catalog.

## Reproducibility

**Notebook Outputs**: **Excellent**. All executed notebooks (NB00, NB01, NB01b, NB02, NB03) have saved outputs including text results, tables, and visualizations. This contrasts favorably with the pitfall noted in `docs/pitfalls.md` about analyses existing only in transcripts.

**Figures**: **Comprehensive**. 15 high-quality figures covering all major analysis stages: cohort summaries, K-selection curves, ecotype characterization, clinical projections, compositional DA comparisons. Each figure directly supports findings in the REPORT.

**Dependencies**: `requirements.txt` is comprehensive and realistic, covering data processing (pandas, numpy), statistics (scipy, statsmodels), machine learning (scikit-learn, lightgbm), and visualization (matplotlib, seaborn).

**Data Artifacts**: **Well-organized**. Key intermediate results committed:
- `species_synonymy.tsv`: Reusable taxonomy reconciliation backbone
- `ecotype_assignments.tsv`: K=4 consensus with confidence scores  
- `ucdavis_*_ecotype_*.tsv`: Patient projections and clinical integration
- `table_schemas.md`: Comprehensive mart documentation

**Reproduction Guide**: Planned but not yet complete (appropriate for interim status). The TODO acknowledges need for BERDL prerequisites, execution order, runtime estimates.

**Known Gaps**: Properly documented in `lineage.yaml` known_data_gaps and throughout documentation. Examples: Dave lab clinical metadata pending, HMP2 MetaPhlAn3 reprocessing required.

## Suggestions

### Critical Issues (None)
The completed work has no critical flaws. The methodology is sound and implementation is high-quality.

### Important Improvements

1. **Complete Pillars 2-5**: The ecotype framework provides an excellent foundation, but the pathobiont atlas, phage targetability assessment, and per-patient cocktails remain to be developed. NB04 (within-ecotype DA) is the critical next experiment to resolve the C. scindens paradox.

2. **Expand UC Davis cohort or validate externally**: With n=23 patients, the per-patient cocktail designs (Pillar 5) will have limited statistical power. Consider projecting additional IBD cohorts from MGnify onto the ecotype framework for validation.

3. **Add HMP2 MetaPhlAn3 integration**: When `PENDING_HMP2_RAW` is resolved, refit ecotypes on CMD+HMP2 (~11.5K samples) and test whether the H1c clinical classifier improves with better training coverage.

4. **Develop rapid ecotype assignment**: The H1c finding that metagenomics is required for ecotype assignment creates a clinical workflow bottleneck. Consider developing a qPCR panel for the 4-6 ecotype-defining species (F. prausnitzii, P. copri, P. vulgatus, B. fragilis) for rapid screening.

### Minor Enhancements

5. **Complete reproduction documentation**: Add the deferred reproduction section covering BERDL prerequisites, notebook execution order, runtime estimates, and external database access.

6. **Systematic literature review**: The current `references.md` covers Pillar 1 well but will need expansion for the pathobiont biology, phage therapy trials, and mechanism papers relevant to Pillars 2-4.

7. **Validate longitudinal stability**: The patient 6967 E1↔E3 shift observation is intriguing but based on n=1. When more longitudinal samples are available, systematically assess ecotype stability implications for dosing schedules.

## Review Metadata

- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-4-20250514)
- **Date**: 2026-04-24
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 5 executed notebooks, 15 figures, 7 data artifacts, requirements.txt
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.