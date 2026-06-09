# Research Plan — ENIGMA Carbon Census 1

## Research Question
For 83 carbon compounds (59 SSO-groundwater + 24 necromass) selected for community
enrichment and isolate phenotyping, assemble a **knowledge census** answering, per
compound: (1) known environmental distribution, (2) candidate catabolic/utilization
pathways, (3) organisms encoding those pathways, (4) how those pathways co-occur
within and across organisms, and (5) which ENIGMA isolates or environmentally
observed organisms are likely utilizers — each prediction carrying an explicit
confidence measure.

### Three concrete deliverables
- **(a) Per-compound ENIGMA-isolate utilizer table** — for each compound, the ENIGMA
  isolates predicted to utilize it, tier-stratified by evidence strength.
- **(b) Per-compound phylogenetic utilizer map** — predicted utilizers placed on the
  GTDB tree, with a per-prediction certainty score.
- **(c) Pathway co-occurrence + environmental atlas** — modularity of catabolic
  capacity within/across genomes, and the environmental distribution of the implicated
  pathways and taxa (MGnify, SPIRE, NMDC, Planet Microbe, pangenome env metadata).

## Central Challenge (drives the whole design)
The source compounds are **natural-product secondary metabolites** (26 alkaloids,
25 shikimates/phenylpropanoids, 17 terpenoids, 10 fatty acids, 2 polyketides,
2 amino acids/peptides) and the spreadsheet has **no SMILES/InChIKey/structure
column**. Two consequences:

1. **Identity resolution is prerequisite to everything** — names must be resolved to
   structures and database cross-references before any pathway linkage. PubChem name
   resolution is approved for this.
2. **Catabolic knowledge will be non-uniform and sparse.** Curated biodegradation
   databases (enviPath/EAWAG-BBD, OASIS, MetaCyc) are overwhelmingly *xenobiotic*-focused
   (pesticides, aromatics, plastics); they cover the pollutant-adjacent subset of our
   compounds, not most alkaloids/terpenoids. The honest output is therefore a **tiered
   confidence atlas**, where "no linkage" (Tier 0) is itself a deliverable — it tells the
   wet lab which enrichments are *discover-new* vs *characterize-known*.

## Hypotheses (weak-prior, pre-registered)
- **H1 — Coverage gradient / knowledge gap.** Catabolic knowledge for the 83 compounds
  is non-uniform and biased by chemical class: pollutant-adjacent classes
  (phenylpropanoids/shikimates, fatty acids) have substantially higher pathway and
  utilizer coverage than alkaloids/terpenoids. *H0:* coverage is uniform across classes.
- **H2 — Modularity / co-occurrence.** Catabolic capacities co-occur non-randomly within
  genomes (capacity for compound class X predicts capacity for class Y) and cluster
  phylogenetically. *H0:* pathway presence is independent across genomes.
- **H3 — Environmental selection.** The environmental abundance of a compound's predicted
  utilizers tracks the geochemical setting where the compound was sourced
  (groundwater vs necromass). *H0:* no association between predicted-utilizer
  distribution and compound source.
- **H4 — ENIGMA predicted utilizers.** A tier-stratified, phylogenetically concentrated
  set of ENIGMA isolates is predicted per compound, enabling targeted phenotyping.
  *H0:* no isolates predicted above Tier 4 / predictions are phylogenetically diffuse.

## Evidence Tiers (the certainty measure for deliverables a & b)
| Tier | Evidence | Source |
|---|---|---|
| **1** | *Measured* growth/fitness on the compound as carbon source | Fitness Browser RB-TnSeq carbon-source experiments |
| **2** | Gene-complete catabolic pathway reconstructed in the genome | GapMind per-genome calls; ModelSEED model |
| **3** | Key catabolic enzyme(s) present by annotation | ENIGMA genome_depot protein↔KO/EC/pathway annotations; pangenome eggNOG/KEGG/EC |
| **4** | Biotransformation-rule inferred degradability + rule-enzyme presence | enviPath (EAWAG-BBD/SOIL) rules |
| **5** | Literature-curated catabolic gene/enzyme for the compound or close analog | PaperBLAST, PubMed/bioRxiv mining (esp. alkaloid/terpenoid classes) |
| **6** | Taxonomic prior only (relatives known to degrade the class) | Literature / DB taxon associations |
| **0** | No linkage found | — (flagged as knowledge gap) |

> Tier 5 (literature) is deliberately elevated as a first-class channel: curated
> biodegradation DBs miss most **alkaloids and terpenoids**, but their catabolism *is*
> described in primary literature. Literature-curated enzymes/KOs/Pfams are then searched
> back into the genomes — a literature hit with a matching genomic enzyme effectively
> promotes a prediction to Tier 3.

## Data Sources
**In-lakehouse (backbone):**
- **GapMind** — per-genome carbon-source + amino-acid utilization, per-step gene mapping; runs on all pangenome genomes. *Tier 2.*
- **ModelSEED biochemistry** — compound → reaction → enzyme. *Tier 2/3.*
- **Pangenome functional annotations** (eggNOG/KEGG/EC) — enzyme presence across GTDB species pangenomes. *Tier 3.*
- **Fitness Browser / RB-TnSeq** — measured carbon-source experiments (~30 organisms linked to pangenome via `fb_pangenome_link.tsv`). *Tier 1.*
- **ENIGMA genome_depot** (`enigma_genome_depot_enigma`, 32 GenomeDepot tables) — **primary substrate for deliverable (a)**. `browser_protein` ↔ `browser_protein_kegg_reactions`/`_kegg_pathways`/`_kegg_orthologs`/`_ec_numbers`/`_cazy_families` give catabolic annotations *directly on ENIGMA isolate proteins*; `browser_gene`→`browser_genome`→`browser_strain`→`browser_taxon` chains genes to strains and to `browser_taxon.taxonomy_id` (**NCBI taxid**) + `eggnog_taxid` + `name` — the crosswalk for phylogeny placement and for joining environmental datasets (which key on NCBI taxids). *Tier 3 directly on isolates, no pangenome bridge needed.*
- **ENIGMA environmental observations** — `enigma` tenant (725 tables) for where isolates/taxa are seen in the field.
- **Environmental sources** — MGnify (`kescience_mgnify`), SPIRE (`refdata_spire`), NMDC (`nmdc_metadata`/`nmdc_results`/`nmdc_ncbi_biosamples` + `kbase.nmdc_arkin`), Planet Microbe (`planetmicrobe` tenant), pangenome env metadata. For deliverable (c).

**External (supplementary, for compound→pathway linkage):**
- **PubChem** — name → CID → InChIKey/SMILES + KEGG/ChEBI/ModelSEED/MetaCyc cross-refs (PUG-REST). *Foundational identity resolution.*
- **enviPath** — free public REST API, anonymous read, `enviPath-python` package; EAWAG-BBD package (`32de3cf4-e3e6-4168-956e-32fa5ddb0ce1`) + EAWAG-SOIL. *Tier 4, pollutant-adjacent subset only.*
- **Literature mining** — PaperBLAST (gene↔paper), PubMed + bioRxiv/arXiv via the `pubmed` and `paper-search` MCP servers, and `/literature-review`. **Targeted at alkaloid and terpenoid catabolism**, which the curated DBs miss. *Tier 5; promotes to Tier 3 when the literature enzyme is found in a genome.*
- OASIS / BioSysMO — no programmatic access; manual reference only if a specific compound demands it.

## Query Strategy
- **Compound-first, then organism, then environment** — resolve identities and pathway
  links for 83 compounds (small, cacheable), expand to organisms via annotation joins,
  and only then pull environmental distributions for the (much smaller) implicated
  taxon/pathway set. Avoids scanning large environmental tables for compounds that have
  no linkage.
- External APIs (PubChem, enviPath) hit ≤83 times each, cached to `data/` as TSV/JSON.
- Performance tier: identity + linkage = light (API + small joins). Organism mapping =
  medium (pangenome annotation joins, filtered to implicated enzymes/pathways).
  Environmental atlas = heavy (large env tables) — run last, filtered to the implicated
  taxon set per `docs/performance.md`.

## Analysis Plan (numbered notebooks)
- **00_exploration** — load xlsx, profile the 83 compounds (class composition, source,
  MW/LogP), sanity checks. *Output:* compound profile + figures.
- **01_identity_resolution** — name → PubChem CID → InChIKey/SMILES → KEGG/ChEBI/
  ModelSEED/MetaCyc cross-refs. *Output:* `data/resolved_compounds.tsv`; coverage report
  (how many resolved, by class).
- **02_pathway_linkage** — multi-channel compound→pathway/enzyme mapping: ModelSEED,
  KEGG/MetaCyc, enviPath rules, GapMind carbon-source catalog overlap, Fitness Browser
  carbon-source experiment matches, **and literature mining (PaperBLAST + PubMed/bioRxiv)
  focused on alkaloid/terpenoid catabolism**. Assign evidence channel + tier per link.
  *Output:* `data/compound_pathway_links.tsv`.
  → **PHASE-1 STOP-GATE:** report linkage coverage by class (with/without the literature
  channel). If coverage is too thin to support downstream mapping, pause and re-scope.
- **03_organism_mapping** — pathway/enzyme → organisms. Two substrates: (i) **ENIGMA
  genome_depot** protein↔KO/EC/pathway/reaction tables for direct isolate calls; (ii)
  pangenome annotations + GapMind per-genome + ModelSEED for the broad reference set.
  *Output:* `data/compound_organism_predictions.tsv` with tier + pathway completeness.
- **04_enigma_utilizers** — assemble per-compound ENIGMA-isolate predictions from
  genome_depot, joined to `browser_taxon` (NCBI taxid + name) and ENIGMA environmental
  observations. **Deliverable (a).** *Output:* `data/enigma_utilizer_predictions.tsv`.
- **05_cooccurrence** — within-genome (metabolic-versatility profiles) and across-genome
  (modularity, phylogenetic clustering) pathway co-occurrence; tests H2. *Output:* figures + matrix.
- **06_phylo_maps** — per-compound utilizer maps on the GTDB tree with certainty scores.
  **Deliverable (b).** *Output:* per-compound figures + tree data.
- **07_environmental_atlas** — MGnify/SPIRE/NMDC/Planet Microbe/pangenome env distributions
  for implicated taxa+pathways; tests H3. **Deliverable (c).** *Output:* figures + tables.
- **08_synthesis** — assemble the three deliverables; per-compound knowledge-census summary
  (incl. Tier-0 gap list for enrichment design).

## Expected Outcomes
- **Supports H1** if linkage/utilizer coverage differs sharply by chemical class
  (expected: shikimates/fatty acids high, alkaloids/terpenoids low). A clean Tier-0 list
  by class is the actionable enrichment-design output regardless.
- **Supports H2** if pathway co-occurrence within genomes exceeds random expectation and
  clusters by clade.
- **Supports H3** if predicted-utilizer environmental abundance differs between
  groundwater- and necromass-sourced compounds in the expected direction.
- **Supports H4** if compounds yield phylogenetically concentrated ENIGMA-isolate
  predictions above Tier 4.
- **Confounders:** identity-resolution failures (exotic names → no CID); biodegradation-DB
  xenobiotic bias inflating coverage for aromatics; GapMind catalog not overlapping our
  compound set (would collapse Tier 2 onto ModelSEED only). The pangenome↔ENIGMA
  taxonomic-bridge limitation is now *avoided* for deliverable (a) by mapping directly on
  genome_depot annotations; it remains relevant only when transferring GapMind/pangenome
  Tier-2 reconstructions onto isolates lacking genome_depot coverage.

## Revision History
- **v1** (2026-06-08): Initial plan. Tiered-confidence-atlas design; biodegradation-DB
  landscape assessed (enviPath usable, others reference-only); three deliverables and
  four hypotheses fixed; Phase-1 stop-gate after pathway linkage.
- **v2** (2026-06-09): Per user feedback. (1) Added **literature mining** as a first-class
  evidence channel (new Tier 5; PaperBLAST + PubMed/bioRxiv) targeted at alkaloid/terpenoid
  catabolism that curated DBs miss. (2) Verified `enigma_genome_depot_enigma` schema:
  catabolic annotations sit directly on ENIGMA isolate proteins, and `browser_taxon`
  carries NCBI taxid + eggnog_taxid + name. Deliverable (a) now maps **directly on
  genome_depot**, mapping isolates via NCBI id / taxonomic name and avoiding the coarse
  pangenome bridge. Tiers renumbered (taxonomic-prior is now Tier 6).

## Authors
- Adam Arkin (University of California, Berkeley; ORCID 0000-0002-4999-2931)
