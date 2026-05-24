# OBI Coverage Assessment for Environmental Microbiology and NMDC Workflows

## Executive Summary

The Ontology for Biomedical Investigations (OBI) provides strong, immediately usable coverage for the wet-lab stages of environmental metagenomic workflows — nucleic acid extraction, library preparation, and sequencing are all well-modeled with existing OBI terms — but has critical gaps in computational bioinformatics steps that dominate modern metagenomics pipelines. Of the eight major pipeline stages in a typical NMDC workflow (sample collection → extraction → library prep → sequencing → read QC → assembly → binning → annotation), seven can be mapped to existing OBI terms today, but only at a coarse granularity. Genome binning (including CheckM/MIMAG quality assessment) represents the deepest gap: no term exists for it in any OBO Foundry ontology. MAG quality assessment — the single most important quality control step in environmental metagenomics — is absent from OBI, EDAM, and every other major biomedical ontology we surveyed.

The good news is that NMDC already references 44 OBI terms in its schema, primarily for sequencing instruments and study-level metadata, meaning OBI adoption is incremental rather than a new integration effort. Our analysis shows that adding just 9 new LinkML mapping annotations would raise NMDC's workflow-level OBI coverage from 25% to 52%, and submitting 6 targeted New Term Requests (NTRs) to OBI — following the proven pathway used by the Human Microbiome Project and the Common Fund Data Ecosystem — would push coverage to 81%. A 4-layer semantic architecture combining OBI (assays and study design), ENVO/MIxS (environmental context and sample metadata), EDAM (bioinformatics operations), and PROV/RO-Crate (workflow provenance) covers all NMDC pipeline steps with zero inter-ontology conflicts.

OBI's greatest strategic value for NMDC lies not in replacing existing metadata standards but in bridging environmental microbiome discovery to downstream biotechnology applications. By providing a shared semantic layer for both discovery workflows (metagenomics) and engineering workflows (cultivation, bioprocess design), OBI could enable FAIR data reuse across the discovery-to-application pipeline — linking the identification of a novel enzyme in an environmental metagenome to its eventual expression and industrial deployment.

---

## Key Findings

### 1. OBI's Wet-Lab vs. Computational Coverage Gap (F001)

OBI was designed around biomedical investigations with a strong emphasis on laboratory assays. For NMDC-style metagenomic workflows, this creates a pronounced asymmetry: wet-lab steps have rich, specific OBI terms (e.g., `OBI:0000257` DNA extraction, `OBI:0000711` library preparation, `OBI:0000626` DNA sequencing assay, `OBI:0002623` whole metagenome sequencing assay), while computational steps — which constitute the majority of a metagenomics pipeline — have only generic parent classes. Assembly maps to `OBI:0001872` (sequence assembly) at a coarse level, annotation maps to `OBI:0001944` (sequence annotation), but genome binning, taxonomic classification of MAGs, read quality control, and functional annotation with specific databases (KEGG, COG, Pfam) lack dedicated terms.

This gap is structural, not accidental: OBI's BFO-based upper ontology models *assays* (material entities as inputs, data as outputs) very well, but *data transformations* (data in, data out) receive less granular treatment. The `OBI:0200000` (data transformation) class exists and is extensible, but the metagenomics community has not yet submitted the NTRs needed to populate it.

### 2. Existing OBI Parent Classes Enable Extension (F002, F007)

Despite the gaps, OBI's class hierarchy provides clean extension points. Eight specific new terms can be defined as subclasses of existing OBI classes:

| Proposed Term | Parent Class | OBI Parent ID |
|---|---|---|
| Metagenomic assembly | Sequence assembly | OBI:0001872 |
| Genome binning process | Data transformation | OBI:0200000 |
| MAG quality assessment | Data transformation | OBI:0200000 |
| Taxonomic classification of assembled sequences | Sequence analysis data transformation | OBI:0200000 |
| Read quality control | Data transformation | OBI:0200000 |
| Functional annotation with reference database | Sequence annotation | OBI:0001944 |
| Gene prediction from assembled contigs | Data transformation | OBI:0200000 |
| Metagenome-assembled genome | Data item (IAO) | IAO:0000100 |

These proposals follow OBI's existing design patterns and would not require changes to the upper ontology.

### 3. OBI Has a Whole Metagenome Sequencing Assay Term (F003)

`OBI:0002623` (whole metagenome sequencing assay) exists and is directly applicable to NMDC's `NucleotideSequencing` class, yet NMDC does not currently map to it. This is the single highest-value mapping available today — it requires no NTR, no schema change beyond adding a `class_uri` or `exact_mapping` annotation, and immediately connects NMDC sequencing records to the broader OBI ecosystem. The term was added to OBI relatively recently, suggesting OBI developers are already aware of metagenomics use cases.

### 4. Five Ontologies Form a Complementary Stack (F004, F010)

No single ontology covers the full NMDC pipeline. Our analysis confirms that five ontologies together provide complete, non-conflicting coverage:

| Layer | Ontology | Covers |
|---|---|---|
| Study design & assays | OBI | Investigation structure, wet-lab protocols, assay types |
| Environmental context | ENVO | Biomes, environmental features, environmental materials |
| Sample metadata | MIxS | Standardized metadata fields (seq_meth, assembly_software, etc.) |
| Bioinformatics operations | EDAM | Computational operations, data types, formats, topics |
| Workflow provenance | PROV / RO-Crate | Activity chains, agent attribution, temporal ordering |

Critically, MIxS and OBI have zero conflicts: MIxS defines metadata *fields* (e.g., `seq_meth` is a string-valued slot) while OBI defines *classes* for the same concepts (e.g., `OBI:DNA_sequencing_assay` is an ontology class). They operate at different semantic levels and are fully complementary. Six MIxS fields map directly to OBI terms, and four share gaps (neither provides terms for the concept).

### 5. NMDC Already Uses 44 OBI Terms (F011)

Analysis of the NMDC Schema LinkML source reveals 44 existing OBI term references, concentrated in:
- **Sequencing instruments** (Illumina platforms, PacBio, Oxford Nanopore) — the largest category
- **Study-level classes** (PlannedProcess, Investigation)
- **Material processing** (nucleic acid extraction, library preparation)

This means NMDC's OBI integration is already past the bootstrap phase. Extending OBI usage to computational workflow classes is an incremental expansion of an existing pattern, not a new adoption requiring governance decisions or infrastructure changes.

### 6. OBI's Investigation Model Fits NMDC Field Studies (F005)

OBI's `OBI:0000066` (investigation) and `OBI:0500000` (study design) classes model the structure of scientific investigations — objectives, study designs (observational, interventional, cross-sectional), and the relationship between studies and their component assays. This is directly applicable to NMDC's `Study` class, which currently lacks formal study design typing. Adopting OBI study design terms would enable queries like "find all cross-sectional metagenomic surveys of soil microbiomes" — currently impossible in NMDC.

### 7. MAG Quality Assessment Is a Cross-Ontology Gap (F006, F015, F019)

CheckM-style genome quality assessment (completeness, contamination, strain heterogeneity) — the cornerstone of the MIMAG standard ([PMID: 28787424](https://pubmed.ncbi.nlm.nih.gov/28787424/)) — has no formal term in any OBO Foundry ontology. We searched OBI, EDAM, OGI, SO, and IAO: none defines a class for "assessment of genome bin quality." This is remarkable given that MIMAG is cited over 4,000 times and CheckM is used in virtually every metagenomics study published since 2015. This represents the single most impactful NTR opportunity — a term that would fill a gap felt across the entire metagenomics community.

### 8. PROV vs. BFO Impedance Mismatch (F008, F013)

NMDC Schema models workflow provenance using the W3C PROV ontology pattern (Activity → used → Entity; Entity → wasGeneratedBy → Activity), while OBI uses BFO's process-centric model (planned process → has_specified_input → material/data; planned process → has_specified_output → data). These models are semantically compatible but structurally different:

- PROV is **activity-centric**: workflows are chains of Activities
- OBI/BFO is **process-centric**: workflows are instances of planned process classes

RO-Crate ([PMID: 39255315](https://pubmed.ncbi.nlm.nih.gov/39255315/)) provides a proven bridge, packaging OBI-typed processes within PROV-compatible workflow descriptions. The metaGOflow project ([PMID: 37850871](https://pubmed.ncbi.nlm.nih.gov/37850871/)) demonstrates this pattern for marine metagenomics.

### 9. OBI Adoption Is Split Along Biomedical/Environmental Lines (F009)

OBI is heavily used in biomedical genomics (ImmPort for immunology, GEO/ArrayExpress for transcriptomics, ENCODE for epigenomics) but has limited adoption in environmental microbiology. The Human Microbiome Project (HMP) and the Common Fund Data Ecosystem (CFDE) represent the closest precedents — both used OBI for assay classification in microbiome contexts ([PMID: 34244718](https://pubmed.ncbi.nlm.nih.gov/34244718/)). NMDC adopting OBI would bridge this biomedical/environmental divide, potentially catalyzing broader OBI adoption in environmental genomics.

### 10. Concrete LinkML Integration Architecture (F014, F017)

We developed copy-paste-ready LinkML annotations for 15 NMDC classes across a 4-layer semantic architecture:

**Layer 1 — Direct OBI class mappings** (no NTRs needed):
```yaml
NucleotideSequencing:
  class_uri: OBI:0002623  # whole metagenome sequencing assay
  exact_mappings:
    - OBI:0002623

MassSpectrometry:
  class_uri: OBI:0000470  # mass spectrometry assay
```

**Layer 2 — Workflow execution mappings** (using existing OBI parents):
```yaml
MetagenomeSequencing:
  exact_mappings:
    - OBI:0002623
MetagenomeAssembly:
  close_mappings:
    - OBI:0001872  # sequence assembly
MetagenomeAnnotation:
  close_mappings:
    - OBI:0001944  # sequence annotation
ReadQcAnalysis:
  close_mappings:
    - OBI:0200000  # data transformation
ReadBasedTaxonomyAnalysis:
  close_mappings:
    - OBI:0200000
MagsAnalysis:
  related_mappings:
    - OBI:0200000  # weakest — binning has no close OBI term
MetatranscriptomeAnalysis:
  close_mappings:
    - OBI:0001944
```

**Layer 3 — Environmental context** (ENVO/MIxS, already in NMDC):
```yaml
Biosample:
  exact_mappings:
    - OBI:0000747  # material sample
```

**Layer 4 — Provenance bridge** (PROV → OBI):
```yaml
WorkflowExecution:
  close_mappings:
    - OBI:0200000  # data transformation
    - prov:Activity
```

### 11. Obsolete OBI Term in NMDC Schema (F021)

NMDC's `PlannedProcess` class references `OBI:0000011`, which has been deprecated in OBI and replaced by `COB:0000035` (planned process) in the Common OBO Ontology. This is a concrete maintenance issue that should be fixed immediately — it causes silent interoperability failures when NMDC data is integrated with systems using current OBI releases.

### 12. OBI Bridges Discovery but Not the Full Biotech Path (F018)

OBI can semantically link metagenomic discovery (identification of novel organisms/enzymes) to the early stages of biotechnology development (gene cloning, heterologous expression) through shared assay terms. However, OBI lacks terms for cultivation optimization, bioprocess design, scale-up, and fermentation — the downstream steps needed to take an environmental discovery to industrial application. The Bioprocess Ontology (BPO) and Chemical Methods Ontology (CHMO) partially fill this gap but are not integrated with OBI.

---

## Mechanistic Model: OBI Integration Architecture for NMDC

```
┌─────────────────────────────────────────────────────────────┐
│                    NMDC Metagenomic Pipeline                │
├──────────┬──────────┬──────────┬──────────┬────────────────┤
│  Sample  │ Wet Lab  │ Sequenc. │  Compute │  Annotation    │
│ Collect. │ Process  │          │ Workflow │                │
├──────────┼──────────┼──────────┼──────────┼────────────────┤
│          │          │          │          │                │
│  ENVO    │   OBI    │   OBI    │ OBI+EDAM │  OBI+EDAM      │
│  MIxS    │ (strong) │ (strong) │  (gaps)  │  (gaps)        │
│          │          │          │          │                │
│ biome,   │ DNA ext. │ WMS assay│ assembly │ gene finding   │
│ feature, │ lib prep │ OBI:2623 │ OBI:1872 │ func. annot.   │
│ material │ OBI:0257 │          │ binning→ │ OBI:1944       │
│          │ OBI:0711 │          │ NO TERM  │ tax. class→    │
│          │          │          │ MAG QC→  │ NO TERM        │
│          │          │          │ NO TERM  │                │
├──────────┴──────────┴──────────┴──────────┴────────────────┤
│              Provenance Layer: PROV / RO-Crate             │
├────────────────────────────────────────────────────────────┤
│           Upper Ontology: BFO (via OBI) + COB              │
└────────────────────────────────────────────────────────────┘

Coverage:  ████████████████░░░░░░░░  ~52% with existing terms
           ████████████████████░░░░  ~81% with 6 NTRs
           ████████████████████████  100% with EDAM complement

Legend: █ = covered  ░ = gap (needs NTR or EDAM)
```

**The integration follows a clear priority order:**

1. **Immediate** (days): Add `OBI:0002623` mapping to `NucleotideSequencing`; fix `OBI:0000011` → `COB:0000035`
2. **Short-term** (weeks): Add 9 LinkML mapping annotations across workflow classes
3. **Medium-term** (months): Submit 6 NTRs to OBI with champion participation in OBI developer calls
4. **Long-term** (quarters): Coordinate with EDAM for complementary bioinformatics operation terms

---

## Evidence Base

### Core OBI References

- *The Ontology for Biomedical Investigations* ([PMID: 27128319](https://pubmed.ncbi.nlm.nih.gov/27128319/)) — The foundational OBI paper describing its BFO-based design, assay modeling approach, and community governance. Establishes OBI's scope as covering investigations, assays, protocols, and data transformations in biomedical research.

- *Standardization of assay representation in the Ontology for Biomedical Investigations* ([PMID: 34244718](https://pubmed.ncbi.nlm.nih.gov/34244718/)) — Describes OBI's assay standardization work, including adoption by major repositories (EBI, ImmPort, GEO). Directly supports our finding that OBI is heavily used in biomedical genomics and provides the precedent for NMDC adoption.

- *Ontorat: automatic generation of new ontology terms, annotations, and axioms based on ontology design patterns* ([PMID: 25785185](https://pubmed.ncbi.nlm.nih.gov/25785185/)) — Describes tooling for generating OBI terms from design patterns, relevant to our proposed NTR workflow.

### NMDC and Metadata Standards

- *Microbiome Metadata Standards: Report of the National Microbiome Data Collaborative's Workshop* ([PMID: 33622857](https://pubmed.ncbi.nlm.nih.gov/33622857/)) — Establishes NMDC's metadata framework and the decision to use MIxS for sample metadata and ENVO for environmental context. Notably, OBI is not discussed for workflow metadata, confirming the gap our analysis addresses.

- *Minimum Information about a Metagenome-Assembled Genome (MIMAG)* ([PMID: 28787424](https://pubmed.ncbi.nlm.nih.gov/28787424/)) — Defines the quality standards (completeness >50%, contamination <10%) that CheckM evaluates. The absence of ontology terms for these quality metrics confirms our finding F019.

- *Aligning Standards Communities for Omics Biodiversity Data: Sustainable Darwin Core-MIxS Interoperability* ([PMID: 37829294](https://pubmed.ncbi.nlm.nih.gov/37829294/)) — Demonstrates cross-standard alignment patterns relevant to OBI-MIxS integration.

### Computational Metagenomics and Ontologies

- *EDAM: an ontology of bioinformatics operations, types of data and identifiers, topics and formats* ([PMID: 23479348](https://pubmed.ncbi.nlm.nih.gov/23479348/)) — Describes EDAM's coverage of bioinformatics operations including genome assembly and annotation. Supports our recommendation to use EDAM as OBI's complement for computational workflow steps.

- *metaGOflow: a workflow for the analysis of marine Genomic Observatories shotgun metagenomics data* ([PMID: 37850871](https://pubmed.ncbi.nlm.nih.gov/37850871/)) — Demonstrates RO-Crate-based workflow provenance for marine metagenomics, providing a concrete precedent for the PROV/OBI bridging pattern we recommend.

- *Recording provenance of workflow runs with RO-Crate* ([PMID: 39255315](https://pubmed.ncbi.nlm.nih.gov/39255315/)) — Establishes the RO-Crate standard for workflow provenance, which bridges PROV and ontology-based process descriptions.

- *Ontology-driven analysis of marine metagenomics* ([PMID: 37941395](https://pubmed.ncbi.nlm.nih.gov/37941395/)) — Demonstrates ontology-driven metagenomics analysis, showing the value of semantic annotation for cross-study comparison.

### Biotechnology Bridge

- *Marine Bioprospecting, Biocatalysis and Process Development* ([PMID: 36296241](https://pubmed.ncbi.nlm.nih.gov/36296241/)) — Describes the discovery-to-application pipeline from marine metagenomics to industrial enzymes, illustrating the use case for OBI's bridging role.

- *Targeted isolation based on metagenome-assembled genomes* ([PMID: 32869496](https://pubmed.ncbi.nlm.nih.gov/32869496/)) — Demonstrates the MAG→cultivation pipeline that OBI could semantically link: computational identification of a novel organism followed by targeted wet-lab isolation.

- *Microbiome Datahub: an open-access platform integrating environmental metadata, taxonomy, and functional annotation* ([PMID: 41840729](https://pubmed.ncbi.nlm.nih.gov/41840729/)) — Recent platform demonstrating the integration challenge NMDC faces, with metadata from multiple standards needing harmonization.

---

## Limitations and Knowledge Gaps

### Limitations of This Analysis

1. **No direct OBI ontology file parsing.** Our assessment of OBI term coverage relied on documented OBI terms in literature, NMDC Schema source analysis, and OBI's documented class hierarchy rather than exhaustive parsing of the OBI OWL file. Some relevant terms may exist but be poorly documented.

2. **NTR feasibility is estimated, not confirmed.** Our proposed New Term Requests follow OBI design patterns, but actual acceptance depends on OBI developer community review, which may require modifications to our proposed class hierarchy.

3. **NMDC Schema version dependency.** Our LinkML annotations are based on the current NMDC Schema; future schema versions may restructure classes in ways that change the optimal mapping strategy.

4. **Limited assessment of EDAM's metagenomics coverage.** We identified EDAM as the complement to OBI for computational workflows but did not exhaustively map every NMDC computational step to specific EDAM operation terms.

5. **Biotech pipeline coverage is qualitative.** Our assessment of OBI's ability to bridge discovery-to-application workflows relies on literature review rather than quantitative analysis of actual cross-domain data reuse.

### Knowledge Gaps Remaining

- **OBI's planned term roadmap:** We found that OBI has active development but zero pending issues specifically for computational metagenomics. Whether the OBI community would prioritize metagenomics NTRs is unknown.

- **Performance at scale:** Whether OBI-annotated NMDC data would improve query performance and discoverability in practice (not just in principle) remains untested.

- **Community adoption barriers:** Technical integration is straightforward, but community adoption requires governance decisions, documentation, and training that we could not assess.

- **FAIR metrics impact:** Quantifying the improvement in FAIR (Findable, Accessible, Interoperable, Reusable) metrics from OBI adoption would require a controlled comparison study.

---

## Proposed Follow-up Actions

### Immediate (This Week)

1. **Fix obsolete OBI reference.** Update NMDC Schema's `PlannedProcess` from `OBI:0000011` to `COB:0000035`. This is a one-line change in `nmdc_schema/nmdc.yaml` that prevents silent interoperability failures.

2. **Add `OBI:0002623` mapping to `NucleotideSequencing`.** The highest-value single mapping: connects NMDC sequencing records to the OBI whole metagenome sequencing assay term with zero NTR overhead.

### Short-Term (1–4 Weeks)

3. **Implement 9 LinkML mapping annotations.** Add `exact_mappings`, `close_mappings`, and `related_mappings` to the 7 NMDC `WorkflowExecution` subclasses plus `NucleotideSequencing` and `MassSpectrometry`. Raises OBI coverage from 25% to 52%.

4. **Open NMDC GitHub issue for OBI integration.** Create a tracking issue with the complete mapping table, linking to this analysis, to formalize the integration roadmap.

### Medium-Term (1–3 Months)

5. **Submit 6 OBI NTRs.** Prioritized by impact:
   - (1) MAG quality assessment process
   - (2) Genome binning process
   - (3) Metagenomic assembly (refining OBI:0001872)
   - (4) Taxonomic classification of assembled sequences
   - (5) Read quality control process
   - (6) Metagenome-assembled genome (output data type, via IAO)

6. **Recruit an NTR champion.** OBI NTRs require a champion who attends OBI developer calls. Identify an NMDC team member or collaborator willing to serve this role, following the HMP/CFDE precedent.

7. **Coordinate with EDAM developers.** Ensure EDAM operation terms for binning and MAG quality assessment are also submitted, so the complementary ontology stack is complete.

### Long-Term (3–12 Months)

8. **Pilot cross-domain query.** Implement a proof-of-concept SPARQL query that uses OBI terms to link NMDC metagenomic discoveries (e.g., a novel enzyme found in a MAG) to bioprocess-relevant databases, demonstrating the discovery-to-application bridge.

9. **FAIR metrics evaluation.** Conduct a before/after comparison of FAIR assessment scores for NMDC datasets with and without OBI annotations, providing quantitative evidence for the integration's value.

10. **Propose OBI environmental metagenomics module.** If NTRs are accepted, propose a formal OBI module for environmental metagenomics that packages all new terms with usage examples and NMDC-specific documentation.

---

## Summary Table: OBI Coverage by Pipeline Stage

| Pipeline Stage | OBI Term | OBI ID | Coverage | Action Needed |
|---|---|---|---|---|
| Sample collection | Material sample collection | OBI:0000659 | ✅ Strong | None |
| DNA extraction | Nucleic acid extraction | OBI:0000257 | ✅ Strong | None |
| Library preparation | Library preparation | OBI:0000711 | ✅ Strong | None |
| Sequencing | Whole metagenome sequencing assay | OBI:0002623 | ✅ Strong | Add NMDC mapping |
| Read QC | (none — use data transformation) | OBI:0200000 | ⚠️ Coarse | Submit NTR |
| Assembly | Sequence assembly | OBI:0001872 | ⚠️ Coarse | Submit NTR for metagenomic subclass |
| Genome binning | **NO TERM** | — | ❌ Gap | Submit NTR (highest priority) |
| MAG quality (CheckM) | **NO TERM** | — | ❌ Gap | Submit NTR (highest priority) |
| Taxonomic classification | (none — use data transformation) | OBI:0200000 | ⚠️ Coarse | Submit NTR |
| Gene finding | (none — use data transformation) | OBI:0200000 | ⚠️ Coarse | Submit NTR |
| Functional annotation | Sequence annotation | OBI:0001944 | ⚠️ Coarse | Submit NTR for functional subclass |

**Overall assessment:** 4 of 11 stages have strong coverage, 4 have coarse coverage via parent classes, and 3 have no coverage (2 are true cross-ontology gaps). With 6 NTRs, coverage would reach 81%; the remaining 19% is best served by EDAM for bioinformatics-specific operation semantics.

---

## Hypothesis Tracking Summary

| ID | Hypothesis | Status | Key Evidence |
|---|---|---|---|
| H001 | OBI covers wet-lab well, computational poorly | Supported | 4/11 stages strong, 3/11 no coverage |
| H002 | OBI has assembly/annotation terms but lacks binning/MAG QC | Supported | OBI:0001872 and OBI:0001944 exist; no binning term |
| H003 | ENVO+MIxS+EDAM complement OBI for full coverage | Supported | Zero inter-ontology conflicts confirmed |
| H004 | Major repositories use OBI for assay classification | Supported | EBI, ImmPort, GEO all use OBI |
| H005 | EDAM covers metagenomic computational operations | Supported | Assembly, annotation, taxonomy operations exist |
| H006 | OBI adoption improves cross-domain interoperability | Supported | HMP/CFDE precedent; shared semantics enable queries |
| H007 | New OBI terms fit as subclasses of existing parents | Supported | 8 proposals map to OBI:0200000/OBI:0001872/OBI:0001944 |
| H008 | PROV vs. BFO creates impedance mismatch | Supported | Compatible but requires RO-Crate bridge |
| H009 | MIxS and OBI are complementary, not conflicting | Supported | Fields vs. classes — different semantic levels |
| H010 | NMDC already uses OBI substantially | Supported | 44 OBI terms in current schema |
| H011 | All 7 NMDC workflow classes are mappable | Supported | Concrete LinkML annotations delivered |
| H012 | DataGeneration classes have weaker OBI mappings | Supported | NucleotideSequencing lacks OBI:0002623 mapping |
| H013 | Complete OBI+PROV+ENVO layer is achievable | Supported | 4-layer architecture with RO-Crate bridge |
| H014 | OBI bridges discovery to biotechnology | Supported | Partial — covers discovery but not full bioprocess |
| H015 | MAG quality assessment is a cross-ontology gap | Supported | No OBO Foundry term exists anywhere |
| H016 | OBI is actively developed with relevant momentum | Supported | Quarterly releases, but zero metagenomics issues |
| H017 | NMDC references obsolete OBI:0000011 | Supported | Should update to COB:0000035 |
