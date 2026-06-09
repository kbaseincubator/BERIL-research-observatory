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
- **GapMind** — per-genome carbon-source + amino-acid utilization, per-step gene mapping; runs on all pangenome genomes. *Tier 2 — but its ~50–60-pathway catalog is common sugars/amino acids/organic acids, so it is expected to contribute **near-zero** coverage for these secondary metabolites; ModelSEED carries Tier 2. NB02 opens with a catalog-overlap check to quantify the gap.* (`metabolic_category` values are `'carbon'`/`'aa'`, not display names; `score_simplified` is binary 0/1.)
- **ModelSEED biochemistry** — compound → reaction → enzyme. *Tier 2/3.*
- **Pangenome functional annotations** (eggNOG/KEGG/EC) — enzyme presence across GTDB species pangenomes. *Tier 3.*
- **Fitness Browser / RB-TnSeq** — measured carbon-source experiments (~30 organisms linked to pangenome via `fb_pangenome_link.tsv`). *Tier 1.*
- **ENIGMA genome_depot** (`enigma_genome_depot_enigma`, 32 GenomeDepot tables) — **primary substrate for deliverable (a)**. `browser_protein` ↔ `browser_protein_kegg_reactions`/`_kegg_pathways`/`_kegg_orthologs`/`_ec_numbers`/`_cazy_families` give catabolic annotations *directly on ENIGMA isolate proteins*; `browser_gene`→`browser_genome`→`browser_strain`→`browser_taxon` chains genes to strains and to `browser_taxon.taxonomy_id` (**NCBI taxid**) + `eggnog_taxid` + `name` — the crosswalk for phylogeny placement and for joining environmental datasets (which key on NCBI taxids). *Tier 3 directly on isolates, no pangenome bridge needed.*
- **ENIGMA environmental observations** — `enigma` tenant (725 tables) for where isolates/taxa are seen in the field.
- **Environmental sources** — MGnify (`kescience_mgnify`), SPIRE (**`refdata.spire`**, dot-notation: `FROM refdata.spire.<table>`), NMDC (`nmdc_metadata`/`nmdc_results`/`nmdc_ncbi_biosamples` + **`kbase.nmdc_arkin`**, dot-notation), Planet Microbe (**`planetmicrobe.planetmicrobe`**), pangenome env metadata. For deliverable (c). *(DB names verified by live discovery in PLAN_REVIEW_1; dot-notation DBs require `tenant.db.table` SQL.)*

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
  pangenome annotations + ModelSEED for the broad reference set (GapMind only where catalog
  overlaps). *Note: genome_depot junction tables store **FK integer ids**, not strings — a
  3-hop join through the lookup tables (`browser_protein_kegg_orthologs`→`browser_kegg_ortholog`,
  `_ec_numbers`→`browser_ec_number`, `_kegg_reactions`→`browser_kegg_reaction`, etc.) is
  required to recover K-numbers/EC strings.* *Output:* `data/compound_organism_predictions.tsv`
  with tier + pathway completeness.
- **04_enigma_utilizers** — assemble per-compound ENIGMA-isolate predictions from
  genome_depot, joined `browser_gene.genome_id`→`browser_genome.strain_id`→
  `browser_strain.taxon_id`→`browser_taxon.id` (NCBI taxid in `taxonomy_id`, name in `name`)
  and ENIGMA environmental observations. **Deliverable (a).**
  *Output:* `data/enigma_utilizer_predictions.tsv`.
- **05_cooccurrence** — within-genome (metabolic-versatility profiles) and across-genome
  (modularity, phylogenetic clustering) pathway co-occurrence; tests H2. *Output:* figures + matrix.
- **06_phylo_maps** — per-compound utilizer maps on the GTDB tree with certainty scores.
  **Deliverable (b).** *Bridge genome_depot strains→pangenome via assembly accession
  (`browser_genome.external_id`), NOT short strain names (collision pitfall); cross-check
  genus after any NCBI-taxid join.* *Output:* per-compound figures + tree data.
- **07_environmental_atlas** — MGnify/SPIRE/NMDC/Planet Microbe/pangenome env distributions
  for implicated taxa+pathways; tests H3. **Deliverable (c).** *H3 resolves at **genus level**
  at best — ENIGMA CORAL field community data is genus-level only. Run as a standalone `.py`
  (`nohup` + checkpoint parquet): the env-table scans exceed the ~20-min JupyterHub kernel
  idle-timeout.* *Output:* figures + tables.
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
- **v3** (2026-06-09): Incorporated PLAN_REVIEW_1 (independent review, live discovery).
  Corrected DB names (SPIRE `refdata.spire`, Planet Microbe `planetmicrobe.planetmicrobe`,
  `kbase.nmdc_arkin` — all dot-notation). Noted genome_depot junction tables are FK ids
  needing a 3-hop lookup join for KO/EC strings. Reframed GapMind Tier 2 as expected
  near-zero (ModelSEED carries Tier 2) with a catalog-overlap check opening NB02. Added
  NB06 assembly-accession bridge (avoid short-name collision), NB07 genus-level H3 caveat
  + `.py`/nohup fallback for the idle-timeout-prone env scan.

- **v4** (2026-06-09): Analysis complete (NB01–NB08). Two execution deviations recorded.
  (1) **Catabolic-direction filter** added at NB03: a genome-prevalence-<10% signature
  reaction is kept only if it is catabolic *for the compound* (member of a KEGG
  degradation/catabolism-named map, or on a 3-reaction curated allowlist: R02107
  xanthine→urate, R02612 phenethylamine→phenylacetaldehyde, R07202 abscisate→8'-OH);
  reactions that *produce* the compound are excluded. This collapsed callable compounds
  15→8 and is the reason the dark fraction is 90%. (2) **H3 (source-tracking) reported
  UNTESTABLE/CONFOUNDED**, not run as a statistic: of 8 callable compounds only 2 are
  necromass (terephthalic + phthalic acid), both phthalate-class aromatics with
  Actinomycetota-heavy utilizers — source is inseparable from chemical class, n=2. NB07
  was reframed to an honest SSO field-occurrence atlas (Zhou Lab 16S, `enigma_coral`
  bricks) instead of fabricating a confounded source contrast.

- **v5** (2026-06-09): Post-review hardening + deepening, in response to
  ADVERSARIAL_REVIEW_1.md and a user content-gap audit. Two scopes:

  **Scope A — corrective re-runs (close two review findings):**
  - **I1 — "callable" must include every Tier-1 measured fitness.** NB02's
    compound→Fitness-Browser carbon-source match used acid/conjugate-base name strings and
    missed measured RB-TnSeq fitness (canonical miss: **lauric acid**, T1_measured yet
    flagged `callable=False`, `organism_dark_reason=only_biosynthetic_signatures`). Fix:
    resolve FB carbon-source names → PubChem CID → InChIKey and match on InChIKey (skeleton
    block) against the resolved compound table, so any compound with a Tier-1 measured
    carbon-source experiment is `callable=True` regardless of pathway-channel darkness.
    Re-emit `census_master_summary.tsv`. *Honesty flag:* FB carbon sources are mostly
    common metabolites, so the realistic payoff is **modest** (likely lauric acid + a small
    number of aromatics); report the delta plainly, do not imply it rescues the dark
    fraction. **I1 must run before any callable-vs-dark content analysis** (it moves the
    boundary).
  - **I4 — quantify co-occurrence effect size, no Spark re-run.** NB05 saved n11/n10/n01
    per block in `cooccurrence_matrix.tsv`; the missing cell is derivable
    (`n00 = 3109 − n11 − n10 − n01`, NGEN=3109 from build_nb05.py). Add Haldane-corrected
    **odds ratio + CI** and **Jaccard** per block by arithmetic only. Keep the v4 verdict
    (**no broad cross-module modularity**); foreground the concrete "≈25/3109 genomes carry
    both an aromatic and a non-aromatic catabolic capacity" rather than φ alone.

  **Scope B — NB09 deepening notebook (surface analysis already latent in the data):**
  the review and user audit agreed the report under-uses NB00 chemistry and never shows the
  utilizer→compound transpose, conservation, or a dark-matter taxonomy. NB09 adds, with
  figures, and folds into a re-synthesized REPORT.md:
  1. **Physicochemistry / bioavailability profiling** — MW/LogP/charge/solubility class
     from NB00/identity resolution; contrast **callable vs dark** and **groundwater vs
     necromass** property distributions. Frame bioavailability as a **ceiling on the
     environmental atlas** (a sorbed/insoluble compound's abundance signal ≠ flux).
  2. **Utilizer→compound transpose** — invert the per-compound predictions to a
     per-organism capacity profile; identify **generalist vs specialist chassis**; annotate
     each utilizer→compound inference with **catabolic-vs-biosynthetic provenance**
     (reversible-reaction heuristic, *not* proof of flux — carry the caveat).
  3. **Phylogenetic conservation of utilization** — per-clade prevalence of each catabolic
     capacity (how conserved vs sporadic across the GTDB tree), from `phylo_utilizer_map.tsv`.
  4. **Dark-matter leveling-up** — taxonomy of the 75 dark compounds:
     **biosynthesis-known-but-catabolism-unknown** (e.g., `only_biosynthetic_signatures`,
     `only_generic_rxns`) vs **fully orphan** (`no_kegg`, `kegg_no_rxn_in_genomes`); flag
     MIBiG as the external biosynthesis check (out-of-lakehouse, named not queried);
     report **source-stratified dark fraction** (groundwater vs necromass). Special
     properties of dark vs consumable matter feed back into point 1.

  *Pervasive honesty flags carried through Scope B:* **n=8 callable underpowers every
  callable-vs-dark contrast** — all such contrasts are descriptive/directional only, no
  inferential claims; catabolic direction is a reversible-reaction heuristic; "high
  certainty" tiers are not comparable across compounds. Execution order:
  **I1 → I4 → NB09 → re-synthesize → /berdl-review.**

## Authors
- Adam Arkin (University of California, Berkeley; ORCID 0000-0002-4999-2931)
