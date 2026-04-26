# Report: The Fitness Browser Stubborn Set — Curator-Like Genes Left Unannotated

> **Status**: pilot complete — 610 of 137,798 ranked genes evaluated (~0.44% of the queue). The verdict distribution has been remarkably stable across rounds (110, 210, 310, 410, 510, 610 → percentages within ~4pp of one another).

## Research Question

Of the ~137K Fitness Browser genes that were **not** in Price's curated `kescience_fitnessbrowser.reannotation` table (1,762 entries across 36 organisms), which have evidence supporting an annotation improvement and which are genuinely unresolvable from current BERDL data?

We started with the question "which genes did Price's curators look at but couldn't improve?" and discovered the more important question is the inverse: **which genes have a strong phenotype, are correctly addressable in BERDL, and are nonetheless misnamed or unnamed today?**

## Headline Findings (n = 610 of 137,798)

### Verdict distribution

| Verdict | n | % |
|---|---:|---:|
| already_correctly_named | 231 | 38% |
| improvable_correction | 195 | 32% |
| improvable_new | 123 | 20% |
| recalcitrant | 61 | 10% |

**318 of 610 (52%) top-ranked non-reannotated genes have evidence supporting an annotation improvement.** Roughly 60% are corrections to existing names (the gene already has a name, but the evidence supports a different or more specific function); 40% are new annotations for currently-hypothetical / DUF / vague-named genes.

**The verdict distribution is remarkably stable across rounds.** Walking from 110 → 210 → 310 → 410 → 510 → 610 produced consistent rates:

| Round | already_named | improvable | recalcitrant |
|---|---:|---:|---:|
| 110 | 36% | 52% | 12% |
| 210 | 34% | 58% | 8% |
| 310 | 35% | 55% | 9% |
| 410 | 37% | 55% | 8% |
| 510 | 38% | 54% | 8% |
| 610 | 38% | 52% | 10% |

Across all 610 genes, the rates settle at ~38% already-named, ~52% improvable, ~10% recalcitrant. The recalcitrant base rate is concentrated in two pools: (1) **prophage-region genes** (MR-1 LambdaSo and CP4So prophages account for ~15 of the 61 recalcitrant calls) where homologs themselves lack characterized function, and (2) **ionic-liquid / aminoglycoside-specific phenotypes** with sparse literature.

![Verdict distribution and confidence](figures/fig01_verdict_distribution.png)

![Verdict by existing annotation category](figures/fig02_verdict_by_category.png)

![Verdict by rank](figures/fig03_verdict_by_rank.png)

### Confidence

- **398 high-confidence verdicts (65%)** — evidence aligns and is internally consistent
- 169 medium-confidence (28%)
- 43 low-confidence (7%) — concentrated in the recalcitrant set

### Literature consultation

- **280 of 610 genes (46%) had paper consultation** during reasoning
- **382 PMC full-text fetches** across **274 unique PMIDs**
- Subagents reported **~30-40% of fetches *changed* the verdict** (vs. just confirming dossier evidence)

### Cross-gene cluster discoveries

24 PMIDs were each cited by ≥3 genes during reasoning — a signal that the LLM reasoning, with literature in hand, recovered published functional clusters that the per-gene FB annotations miss:

| PMID | n genes | Cluster |
|---|---:|---|
| 24795702 (Korte 2014) | 10 | DvH/Miya nitrate-tolerance cluster (NtrYX-like) |
| 32934357 (Zhou 2020) | 9 | Same cluster, evolution evidence |
| 34215744 (Cimermancic 2014) | 6 | PV4 aryl polyene biosynthesis (APE BGC) |
| 18194565 (Visca 2008) | 5 | pseudo5 pyoverdine NRPS biosynthesis (5+ genes) |
| 37865075 (Pellegrini 2024) | 3 | Ponti Tl/As resistance operon (metallophosphoesterase + ArsR + glyoxalase) |
| 37239993 (Awasthi 2023) | 3 | Cross-organism SAM-methyltransferase tetracycline tolerance |
| 38832093 (Yang 2024) | 3 | Pseudomonas MexT/MexEF HMF tolerance regulon |
| (17 additional cluster PMIDs) | 3-5 each | see [data/cross_gene_clusters.md](data/cross_gene_clusters.md) |

The DvH nitrate cluster is the most striking: 10 genes across two organisms (DvH and Miya) all resolved by one paper. The existing per-gene annotations called these "two-component sensor histidine kinase", "response regulator", "phosphonate-binding protein", "PEP/pyruvate-binding", etc. — all generic family-level names. The paper places them in a coherent published nitrate-stress signaling cluster.

### Notable individual corrections

- **WCS417::GFF4430**: "chemotaxis CheY" → GltR-2 glucose response regulator (different pathway entirely)
- **Cup4G11::RR42_RS10910**: "aminodeoxychorismate lyase" → MltG endolytic peptidoglycan transglycosylase (wrong family)
- **WCS417::GFF2574**: "aspartyl beta-hydroxylase" → LpxO lipid A 2-hydroxylase
- **PV4::5210365**: "type IV pilus assembly PilZ" → MotL c-di-GMP-binding flagellar motor regulator (paper cited as "MotL")
- **5 PV4 genes** flipped from "fatty acid synthesis" to "aryl polyene biosynthesis cluster" — they're not redundant FAS, they're a specialized BGC
- **5 pseudo5 NRPS genes** all identified as pyoverdine biosynthesis components from one paper

### Per-organism curation depth — the model-organism bias

The visited 310-gene subset shows a sharp split between well-curated and less-curated FB organisms:

| Organism | Total visited | already_named % | improvable % |
|---|---:|---:|---:|
| **Koxy** (*K. oxytoca*) | 21 | **81%** | 14% |
| **Keio** (*E. coli* BW25113) | 14 | **71%** | 21% |
| Kang | 7 | 71% | 14% |
| pseudo6_N2E2 | 18 | 50% | 39% |
| Marino | 15 | 27% | 53% |
| WCS417 (*P. simiae*) | 17 | 29% | 59% |
| **DvH** | 20 | 20% | **65%** |
| **PV4** | 22 | 23% | **73%** |
| **pseudo5_N2C3_1** | 24 | 21% | **75%** |
| **Miya** | 9 | 22% | **78%** |
| **BFirm** | 5 | 20% | **80%** |

E. coli K-12 and *Klebsiella oxytoca* (which inherits much of the *E. coli* gene catalog) have ≥70% of top-ranked genes already correctly named. In contrast, less-studied organisms (*Pseudomonas* sp. PV4, *Pseudomonas* sp. pseudo5, *Desulfovibrio vulgaris*, *Methylotenera* MMSC, *Bacillus firmus*) have 65-80% of their top-ranked genes needing reannotation. This is unsurprising in retrospect — FB's curated reannotation pipeline naturally focuses on well-characterised model organisms — but quantifies the gap: **the most curator-actionable improvements are in the non-model organisms**, exactly where literature-anchored homology-driven proposals add the most value.

### Recalcitrant genes — why they resist

Of the 17 recalcitrant genes, the failures cluster:
- Family-level annotations that are correct (TonB-dependent receptor, TPR repeat, sigma factor) but specific role unresolvable from cofitness alone
- Deeply conserved unknowns (DUF/UPF families) where homologs in PaperBLAST also lack characterised function
- Cases where the phenotype condition is unusual (e.g. specific sensitivity to ionic liquids, urea-as-N-source) and PaperBLAST homologs have no relevant literature

These are the genuine "BERDL-stubborn" genes — strong fitness signal, no resolvable function from existing evidence.

## Methodology

### Architecture

```
00_extract_gene_features.py            (Spark; primary fitness/cofit features per gene)
02_extract_secondary_evidence.py       (Spark; 6 binary flags)
03_extract_paperblast_via_swissprot.py (Spark; FB SwissProt → PaperBLAST direct ID join)
04_dump_paperblast_sequences.py        (local; PaperBLAST uniq parquet → FASTA)
                                        + DIAMOND blastp FB AA seqs vs PaperBLAST uniq
05_paperblast_via_diamond.py           (local; DIAMOND hits + paperblast.gene/genepaper joins)
06_extract_phenotype_conditions.py     (Spark; specific + strong phenotypes WITH conditions)
07_extract_partners_and_neighbors.py   (Spark; cofit partners + ±5 gene neighborhood)
08_extract_functional_text.py          (Spark; SwissProt + domain + KEGG + SEED text)

dossier.py                              (module; lazily indexes 13 parquets, builds per-gene dossier)

01_rank_genes.py                       (rank by in_specificphenotype DESC, max_abs_fit*max_abs_t DESC)
02_prepare_batch.py                    (top-N un-judged dossiers → per-batch input.md)
                                        ↓
                  5-10 Claude Code subagents in parallel (Agent tool)
                  each fetches PMC full text via PubMed MCP for borderline genes
                                        ↓
                  per-batch output.jsonl
                                        ↓
03_aggregate_verdicts.py               (merge batch JSONLs → llm_verdicts.jsonl)
04_characterise_verdicts.py            (contingency tables + figures + summary)
05_synthesize.py                       (improvable.tsv, recalcitrant.tsv, cited_pmids.tsv,
                                        cross_gene_clusters.md)
```

### What's in each gene's dossier

8 evidence layers — what a Price-2018 curator actually reads:

1. Fitness phenotype with **conditions** (e.g., "specifically sick on D-mannose, fit=-13.08")
2. Cofit partners with their **annotations** (guilt-by-association)
3. Genomic neighborhood (±5 positions, operon context)
4. SwissProt RAPSearch2 hit + curated description
5. Pfam/TIGRFam domain hits with EC + definitions
6. KEGG KO description + EC
7. SEED descriptions
8. PaperBLAST homologs (Stage 1 SwissProt-direct + Stage 2 DIAMOND vs `uniq`) + paper titles

Subagents fetch full PMC text via the PubMed MCP for the most relevant 1-2 papers per gene where dossier evidence is borderline.

### Throughput

- 5-10 subagents in parallel: ~16 genes/min effective wall throughput
- Each subagent: ~100-400 seconds for a 25-gene batch including paper fetches
- Total wall time for 210 genes: ~30 min spread across two rounds

## Limitations and Caveats

1. **Walked top 210 of 137,798 ranked genes (0.15%)**. The improvable rate at this depth is 58%; rates may decline at lower-priority ranks but the pattern of cross-gene cluster discovery is likely persistent.
2. **LLM reasoning is not infallible**. Confidence labels reflect the subagent's self-assessment; some "high-confidence" calls may be overconfident, and "medium" calls especially benefit from human curator review.
3. **Paper coverage is asymmetric**. PaperBLAST's 815K sequences index only papers in PMC full-text or curated databases; recent papers and non-OA journals may be undercovered.
4. **`already_correctly_named` is not the same as "perfect"**. It only means the existing FB annotation matches the evidence at the level of granularity in the dossier. EC numbers, organism context, and substrate specificity may still be missing.
5. **No structural evidence (yet)**. AlphaFold structural homology was not consulted; some borderline calls might resolve with structure.

## Reproduction

*To be filled in: prerequisites, step-by-step instructions, expected runtime.*

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory

---

# Phase 2 — Negative & Positive Training Set Construction (random sample + Codex cross-check)

> **Status (April 2026):** Phase 2 walked 4,600 randomly sampled non-reannotated genes, applied two-LLM agreement (Claude + Codex with full-text paper summaries) to harden the verdicts, and produced training-ready JSONL artifacts for a downstream gene-function annotation agent.

## Motivation

The Phase 1 priority queue (top of `(in_specificphenotype DESC, max_abs_fit*max_abs_t DESC)`) is biased toward easy cases — strong, specific, high-confidence phenotypes. To train an agent that can learn **when not to update an annotation**, we needed two artifacts:

1. **Negative training set**: genes with strong evidence signal but no defensible specific name (the "recalcitrant" class).
2. **Positive training set**: genes whose existing annotation is supported by the evidence (the "already_correctly_named" class), especially the high-confidence subset where the name is clearly correct.

The priority queue would over-represent improvable genes; a random sample better mirrors the distribution the agent will encounter in production.

## Random sample track

`01b_sample_random_genes.py` draws a fixed-seed (`20260425`) uniform random sample of **5,000 genes** from `ranked_genes.parquet`. Sampled genes are written to `data/random_sample_genes.parquet` and walked through the same dossier → subagent → verdict pipeline as Phase 1, with batches prefixed `batch_R*` (vs `batch_B*` for the priority queue).

### Walk results (n = 4,600 of 5,000 sampled genes; 184 batches)

| Verdict | n | % |
|---|---:|---:|
| already_correctly_named | 1,828 | 39.7% |
| recalcitrant | **1,220** | **26.5%** |
| improvable_correction | 726 | 15.8% |
| improvable_new | 826 | 18.0% |

The recalcitrant rate at random sampling (26.5%) is **~3× higher** than at the priority-queue top (~10%), confirming that priority-queue selection biases toward improvable cases.

### Codex paper summarization (the manuscript-summaries.tsv pipeline)

To re-run the verdicts with literature in hand — and to produce evidence in the format the downstream gene-function agent ingests — we generated per-(geneId, paper) summaries for every PaperBLAST DIAMOND homolog of every recalcitrant gene plus a 500-gene high-confidence positive subset.

```
06_build_paper_tasks.py     → (pmId, [gene_identifiers]) tasks for the recalcitrant set
07_fetch_pmc.py             → NCBI E-utilities efetch → cached PMC XML (1,631 papers in PMC)
08_run_codex_summarize.sh   → per-paper Codex (gpt-5.5) call w/ summarizer prompt
                              → per-gene summary in TSV (manuscript_id, source_type, gene_identifier, summary)
09_run_all_codex.sh         → parallel xargs (P=12) over all cached papers
10_concat_summaries.py      → final manuscript-summaries.tsv (4-col agent schema)

15_build_positive_paper_tasks.py → 500 high-conf already_correctly_named positive subset
                                   → 3,353 unique papers, 5,015 (geneId, pmId) pairs
                                   → re-run 07/08/09 with SUM_DIR override
```

Key design choices:
- Summarizer prompt matches the gene-function agent's `summarizer_prompt` verbatim (4-col TSV output keyed on `(manuscript_id, gene_identifier)`).
- Codex CLI invocation uses `--ephemeral --sandbox workspace-write` (matches `/review` skill pattern) to avoid session-state errors.
- Two Codex CLI binaries supported via `CODEX_BIN` env var: personal account (`codex`) for the recalcitrant pass, enterprise (`codex-work`) for the positive pass.
- PMC cache is shared across both passes (papers can appear in both sets).
- Oversized papers (>700KB XML) hit Codex's 1MB context limit; resolved by truncating the XML head to ~300KB.

### Final summary corpus

| Metric | Recalcitrant pass | Positive pass | **Combined** |
|---|---:|---:|---:|
| Genes targeted | 1,220 | 500 | 1,720 |
| Papers requested | 1,804 | 3,353 | 5,157 |
| PMC XMLs cached | 1,631 (90%) | 3,001 (89%) | 4,632 |
| Per-paper Codex TSVs written | 1,631 | 3,000 | 4,631 |
| Non-null summaries (after concat + dedup) | — | — | **4,803** |
| Final `data/manuscript-summaries.tsv` | — | — | **4.0 MB** |

## Codex cross-check (two-LLM agreement on the recalcitrant set)

The 1,220 Claude-recalcitrant verdicts were re-classified by Codex (`gpt-5.5`) given an **augmented dossier**: the original 8-layer evidence dossier **plus** the per-paper PaperBLAST literature summaries we just generated.

```
12_build_codex_xcheck_batches.py  → 49 batches × 25 augmented dossiers = data/codex_xcheck/batch_X*/input.md
13_run_codex_xcheck.sh            → per-batch codex exec → output.jsonl (25 verdicts)
14_run_all_xcheck.sh              → parallel xargs (P=12) over all 49 batches
```

### Cross-check results

Of 1,220 Claude-recalcitrants, Codex (with literature in hand) said:

| Codex verdict | n | % |
|---|---:|---:|
| **recalcitrant** (✓ both agree → final negative set) | **755** | **61.9%** |
| already_correctly_named (Codex says existing name is fine) | 225 | 18.4% |
| improvable_new (Codex named it from summaries) | 171 | 14.0% |
| improvable_correction (Codex says fix the name) | 69 | 5.7% |

**By Claude confidence at intake:**

| Claude conf | survived | total | survival % |
|---|---:|---:|---:|
| high | 445 | 535 | **83%** |
| low | 111 | 187 | 59% |
| medium | 199 | 498 | 40% |

Claude's *high*-confidence recalcitrants survived best (83%). Codex sees the augmented dossier and most often flips Claude's medium-confidence calls — exactly where two-LLM agreement adds the most signal.

## Final training artifacts

| File | Purpose | Rows | Schema |
|---|---|---:|---|
| `data/training_recalcitrant_final.jsonl` | Negative training set (Claude ∩ Codex agree recalcitrant) | **755** | orgId, locusId, Claude verdict + rationale, Codex verdict + rationale |
| `data/training_recalcitrant.jsonl` | Pre-cross-check version (with full dossier_md + paperblast_hits + per-paper summaries inlined) | 1,220 | full evidence record per gene |
| `data/manuscript-summaries.tsv` | Per-(paper, gene_identifier) summaries — the format the downstream agent ingests | **4,803** | manuscript_id, source_type, gene_identifier, summary |
| `data/positive_sample_500.jsonl` | The 500 high-confidence already_correctly_named genes selected for the positive set | 500 | full Claude verdict + rationale |
| `data/codex_summaries/` + `data/codex_summaries_positive/` | Per-paper Codex outputs (one TSV per pmId) + cached PMC XMLs | — | per-paper |
| `data/codex_xcheck/batch_X*/output.jsonl` | Codex cross-check verdicts for all 1,220 recalcitrant | 1,220 | per-gene Codex verdict |

### Negative-set quality breakdown (n = 755)

| Sub-tier | n | Quality |
|---|---:|---|
| Both Claude & Codex high confidence | 204 | Gold-standard "I literally cannot pin this down" |
| Has ≥1 real summary attached (literature available, both still recalcitrant) | 84 | Hardest negatives |
| All summaries null but has DIAMOND hits | 89 | Homologs exist but uncharacterized |
| Orphans (zero PaperBLAST hits) | 582 | Easy negatives ("nothing to look up") |

## Codex cross-check on the positive set (n = 500)

The 500 high-confidence `already_correctly_named` genes were re-classified by Codex (`gpt-5.5`) using the same augmented-dossier methodology — original 8-layer dossier plus per-paper PaperBLAST literature summaries from the positive-set summarization run (3,000 papers summarized; `manuscript-summaries-positive.tsv`, 4,572 rows).

```
17_build_codex_xcheck_positive.py  → 20 batches × 25 dossiers = data/codex_xcheck_positive/batch_P*/input.md
14_run_all_xcheck.sh (XCHECK_DIR=…codex_xcheck_positive BATCH_PREFIX=batch_P) → parallel xargs (P=8)
18_build_training_positive_final.py → training_positive_final.jsonl + training_positive_xcheck.jsonl
```

### Cross-check results

Of 500 Claude-`already_correctly_named` (all high confidence at intake), Codex with literature in hand said:

| Codex verdict | n | % |
|---|---:|---:|
| **already_correctly_named** (✓ both agree → final positive set) | **445** | **89.0%** |
| improvable_correction (Codex says fix the name) | 27 | 5.4% |
| improvable_new (Codex names it differently) | 14 | 2.8% |
| recalcitrant (Codex cannot confirm the name) | 14 | 2.8% |

89% agreement is much higher than the recalcitrant cross-check's 62%, as expected: high-confidence positive calls anchor on direct evidence (matching SwissProt / KEGG / characterized homolog) and survive a second LLM read more often than recalcitrant judgments, which depend on absence-of-evidence reasoning.

## Final training artifacts (updated)

| File | Purpose | Rows | Schema |
|---|---|---:|---|
| `data/training_recalcitrant_final.jsonl` | Negative training set (Claude ∩ Codex agree recalcitrant) | **755** | Claude + Codex verdict + rationale |
| `data/training_positive_final.jsonl` | Positive training set (Claude ∩ Codex agree already_correctly_named) | **445** | Claude + Codex verdict + rationale |
| `data/training_recalcitrant.jsonl` | Pre-cross-check negative (with full dossier_md + paperblast_hits + per-paper summaries) | 1,220 | full evidence record per gene |
| `data/training_positive_xcheck.jsonl` | Pre-cross-check positive (all 500 + Codex verdict merged) | 500 | flat per-gene record |
| `data/manuscript-summaries.tsv` | Per-(paper, gene) summaries — recalcitrant set | **4,803** | manuscript_id, source_type, gene_identifier, summary |
| `data/manuscript-summaries-positive.tsv` | Per-(paper, gene) summaries — positive set | **4,572** | same schema |
| `data/codex_xcheck_positive/batch_P*/output.jsonl` | Codex cross-check verdicts for all 500 positive | 500 | per-gene Codex verdict |

## Negative-set stratification (n = 755)

Cross-cutting the four sub-tiers above by intake confidence and fitness strength sharpens which negatives are scientifically interesting:

| Cut | n | Notes |
|---|---:|---|
| Orphan (zero PaperBLAST hits) | 582 | Easy negatives; "no homolog in the literature corpus" |
| Hits but all summaries null | 89 | Homolog families with papers that never characterize the protein |
| Hits with ≥1 real summary | **84** | Hardest negatives — literature was read; both LLMs still couldn't resolve |
| Both Claude + Codex high-confidence | 204 | Quality filter — most-trustworthy "I cannot pin this down" |
| **Strong phenotype** (\|fit\|≥2 & \|t\|≥5) | **42** | **Wet-lab targets** — strong fitness signal, no annotation possible from current evidence |

The 42-gene strong-phenotype shortlist is the highest-value experimental cohort: fitness signal is unambiguous, evidence was thoroughly read, and neither LLM could name the function. Top by |fit|: `Caulo::CCNA_02030` (|fit|=6.98, |t|=23), `Caulo::CCNA_02021` (|fit|=3.69, |t|=16.2), `MR1::202102` (|fit|=3.27, |t|=24.8), `Pedo557::CA265_RS09335` (|fit|=3.23, |t|=16.2), `Btheta::349844` (|fit|=2.87, |t|=15.4).

Outputs: `data/negatives_stratified.tsv` (all 755) and `data/negatives_strong_targets.tsv` (42), produced by `notebooks/19_stratify_negatives.py`.

## Distributable training set

The clean, self-contained deliverable for downstream consumers (gene-function annotation agent training) lives in **[`data/training_set/`](data/training_set/)**:

| File | Rows | Label |
|---|---:|---|
| `negatives.jsonl` | 755 | `recalcitrant` — both LLMs agree the gene cannot be annotated from current evidence |
| `positives.jsonl` | 445 | `already_correctly_named` — both LLMs agree the existing FB annotation is correct |
| `README.md` | — | Schema, category breakdown, usage notes, caveats |

Each row carries Claude's verdict + rationale and Codex's verdict + rationale, plus (for negatives) `evidence_tier` and `strong_phenotype` so a consumer can filter without reading the project. See `data/training_set/README.md` — it is the intended entry point for anyone receiving this set in isolation.

## Outstanding work

See [TODO.md](TODO.md). Two open items:

- Manual spot-check of the 55 positive disagreements (excluded from the distributable set).
- Wet-lab analysis of the 42 strong-phenotype recalcitrants.
