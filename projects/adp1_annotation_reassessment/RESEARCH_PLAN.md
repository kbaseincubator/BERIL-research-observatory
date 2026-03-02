# Research Plan: ADP1 Annotation Reassessment

## Motivation

Gene function annotation is a critical bottleneck in microbial genomics. RAST and Bakta provide automated annotations based on sequence homology, but many genes remain annotated as "hypothetical protein." A new approach using GPT-5.2 reasoning over InterProScan domain evidence produced 2,992 functional annotations for ADP1's 3,083 protein sequences.

ADP1 is uniquely suited for evaluating annotation quality because five prior experimental projects provide rich ground truth: deletion fitness on 8 carbon sources, TnSeq essentiality, FBA metabolic modeling, proteomics, and characterized pathway memberships.

## Approach

### Phase 1: Data Integration (NB01)
- Join agent annotations to genome features by protein sequence
- Build master table with all annotation sources and experimental data
- Classify annotations: specific function / hypothetical / missing

### Phase 2: Hypothetical Resolution (NB02)
- Quantify how many RAST/Bakta hypotheticals the agent resolves
- Categorize agent vs RAST/Bakta agreement when both provide functions
- Identify genes with genuinely new functional information

### Phase 3: Phenotype Concordance (NB03)
- Score each annotation source against experimental ground truth
- Test condition-specific genes: does annotation explain the phenotype?
- Validate against characterized subsystems (aromatic network, respiratory chain)

### Phase 4: Model Reconciliation (NB04)
- Examine FBA-discordant genes: do new annotations explain discrepancies?
- Check if new annotations suggest missing reaction mappings
- Assess potential for metabolic model improvement

## Expected Outputs
- Master annotation table with coverage statistics
- Hypothetical resolution rates per annotation source
- Phenotype concordance scores
- Model improvement candidates
- Figures for each analysis
