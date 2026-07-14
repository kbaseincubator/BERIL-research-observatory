<!-- inventory_schema_version: 1 -->
# Tables Inventory

Auto-generated from `extract_tables.py` over `/home/aparkin/BERIL-research-observatory/projects/caulobacter_fur_lipida_loss`. Each table below comes with caption candidates ranked by source: section-heading first (the project's own authored heading), then preceding-sentence (the introductory paragraph's last sentence) as a fallback. v0.6 sources tables exclusively from REPORT.md markdown pipe-tables.

## Summary

- Total tables: **10**
- Column counts: [6, 3, 3, 5, 4, 3, 3, 3, 2, 2]
- Row counts: [2, 3, 2, 17, 5, 4, 2, 24, 10, 9]
- With heading caption: 10
- With preceding-sentence caption: 5

## Tables

### report_tbl_01 — Finding 2 — Fur-released TBDT subset shows marginal enrichment for envelope-stress phenotypes; SspB-buffered set does NOT exceed background (H2 partially supported)

_Columns: 6 (Gene set | n | phenotype-bearing | % | Background-corrected enrichment | Verdict)_
_Rows: 2_
_Column types: text | numeric | numeric | numeric | text | text_

**Caption candidates:**

- **section heading**: Finding 2 — Fur-released TBDT subset shows marginal enrichment for envelope-stress phenotypes; SspB-buffered set does NOT exceed background (H2 partially supported)
- **preceding sentence**: Hypergeometric enrichment against the background:

**Content (first 3 rows):**

| Gene set | n | phenotype-bearing | % | Background-corrected enrichment | Verdict |
|---|---|---|---|---|---|
| Path A (concordant_strong, clean Fur signature) | 32 | 17 | 53.1% | **fold = 1.60×, p = 0.016** | marginally enriched |
| Path B (SspB-buffered, cbb3/*fix*-rich) | 26 | 9 | 34.6% | fold = 1.04×, p = 0.515 | **indistinguishable from background** |

_Source: REPORT.md lines 19–22_

### report_tbl_02 — Finding 4 — Sphingolipid biosynthesis is constitutive; transcript-level Lpt apparatus stable/up with protein-level discordance; CtpA rejected at pre-registered bar; *lptC2* pilot observation (H3 partially supported)

_Columns: 3 (Sub-claim | Result | Verdict)_
_Rows: 3_
_Column types: text | text | text_

**Caption candidates:**

- **section heading**: Finding 4 — Sphingolipid biosynthesis is constitutive; transcript-level Lpt apparatus stable/up with protein-level discordance; CtpA rejected at pre-registered bar; *lptC2* pilot observation (H3 partially supported)
- **preceding sentence**: The CtpA verdict has been corrected from earlier draft "BORDERLINE" to **REJECTED at the pre-registered bar** in response to adversarial review:

**Content (first 3 rows):**

| Sub-claim | Result | Verdict |
|---|---|---|
| CtpA / CCNA_03113 upregulation in 4599-vs-4584 | logFC +0.58, pvalue=0.048, FDR=0.109 (transcript); NOT detected in OM proteome | **REJECTED at pre-registered bar** |
| Sphingolipid biosynthesis pathway constitutive (not induced) | 0/6 biosynthesis genes UP; *spt* DOWN -0.64 FDR 0.002; *sphk* DOWN -0.40 FDR 0.02 | SUPPORTED strongly |
| Canonical Lpt apparatus maintained (transcript) | 0 components DOWN at transcript; **MsbA-like CCNA_00307 +0.89 FDR 0.01**, **LptC-related CCNA_03716 +0.56 FDR 0.005** | SUPPORTED at transcript level (but see protein-level discordance below) |

_Source: REPORT.md lines 45–49_

### report_tbl_03 — Finding 4 — Sphingolipid biosynthesis is constitutive; transcript-level Lpt apparatus stable/up with protein-level discordance; CtpA rejected at pre-registered bar; *lptC2* pilot observation (H3 partially supported)

_Columns: 3 (Protein | log2(4672/4659) | log2(4672/4580))_
_Rows: 2_
_Column types: text | numeric | numeric_

**Caption candidates:**

- **section heading**: Finding 4 — Sphingolipid biosynthesis is constitutive; transcript-level Lpt apparatus stable/up with protein-level discordance; CtpA rejected at pre-registered bar; *lptC2* pilot observation (H3 partially supported)
- **preceding sentence**: **Protein-level discordance for the Lpt apparatus.** Of the canonical Lpt components actually detected in the OM proteome — **LptD** and **LptE** — both *decline* in the rescued strain relative to the intermediate AND to WT baseline:

**Content (first 3 rows):**

| Protein | log2(4672/4659) | log2(4672/4580) |
|---|---|---|
| LptD (CCNA_01760) | **−0.47** | −0.62 |
| LptE (CCNA_03866) | **−0.78** | −0.68 |

_Source: REPORT.md lines 55–58_

### report_tbl_04 — Hypothesis scorecard

_Columns: 5 (Hypothesis | Sub-claim | Pre-registered threshold | Observed | Verdict)_
_Rows: 17_
_Column types: text | text | text | text | text_

**Caption candidates:**

- **section heading**: Hypothesis scorecard

**Content (first 3 rows):**

| Hypothesis | Sub-claim | Pre-registered threshold | Observed | Verdict |
|---|---|---|---|---|
| **H1** ChvI cooperator + consequence | Phase structure | ≥10 genes per cohort | unique-early=20, both=10, late=49 | PASS |
| **H1** | SigU drives late cohort | ≥50% envelope/transport/regulator + Fisher p<1e-3 | 24.5% (literature gap, reframed) | PARTIAL |
| **H2** Critical Fur regulon subset | Path A (concordant_strong) | ≥10% phenotype-bearing | 17/32 = 53% (fold 1.60×, p=0.016 vs background 33.25%) | PASS (marginal enrichment) |

_(17 data rows total; see REPORT.md lines 97–115 for full table)_

_Source: REPORT.md lines 97–115_

### report_tbl_05 — NB06 — Comparative species presence/absence (PaperBLAST original) + NB06b NCBI confirmation

_Columns: 4 (Gene | PaperBLAST C.c. hits | NCBI C.c. hits | Verdict)_
_Rows: 5_
_Column types: text | numeric | numeric | text_

**Caption candidates:**

- **section heading**: NB06 — Comparative species presence/absence (PaperBLAST original) + NB06b NCBI confirmation
- **preceding sentence**: **PaperBLAST false negatives in C. crescentus confirmed** (NB06b vs NB06 for genes that PaperBLAST said 0 and NCBI confirms present):

**Content (first 3 rows):**

| Gene | PaperBLAST C.c. hits | NCBI C.c. hits | Verdict |
|---|---|---|---|
| LpxA | 0 | **11** | PaperBLAST false negative |
| LpxC (the deleted gene!) | 0 | **15** | PaperBLAST false negative |
| LpxD | 0 | **15** | PaperBLAST false negative |

_(5 data rows total; see REPORT.md lines 157–163 for full table)_

_Source: REPORT.md lines 157–163_

### report_tbl_06 — NB06 — Comparative species presence/absence (PaperBLAST original) + NB06b NCBI confirmation

_Columns: 3 (Gene/family | NCBI pattern (C/A/N/M) | Verdict)_
_Rows: 4_
_Column types: text | numeric | text_

**Caption candidates:**

- **section heading**: NB06 — Comparative species presence/absence (PaperBLAST original) + NB06b NCBI confirmation
- **preceding sentence**: **Biological claims CONFIRMED by NCBI annotation** (where NB06 and NB06b agree, pattern 1000 = Caulobacter only):

**Content (first 3 rows):**

| Gene/family | NCBI pattern (C/A/N/M) | Verdict |
|---|---|---|
| *spt* — serine palmitoyltransferase | 1000 | **Caulobacter-unique CONFIRMED** |
| *cerR* — ceramide reductase | 1000 | **Caulobacter-unique CONFIRMED** |
| ChvG — sensor kinase | 1000 | **Caulobacter-unique CONFIRMED** |

_(4 data rows total; see REPORT.md lines 167–172 for full table)_

_Source: REPORT.md lines 167–172_

### report_tbl_07 — Sources

_Columns: 3 (Collection | Tables Used | Purpose)_
_Rows: 2_
_Column types: text | text | text_

**Caption candidates:**

- **section heading**: Sources

**Content (first 3 rows):**

| Collection | Tables Used | Purpose |
|------------|-------------|---------|
| `kescience_fitnessbrowser` | `organism`, `experiment`, `fitbyexp_caulo`, `gene` | 198-experiment Caulobacter RB-TnSeq fitness ranking for the Fur-released gene set (NB02) |
| `kescience_paperblast` | `gene`, `genepaper`, `snippet`, `curatedgene` | Caulobacter SigU literature scout (NB03); cross-species presence/absence (NB06) |

_Source: REPORT.md lines 262–265_

### report_tbl_08 — Generated Data

_Columns: 3 (File | Rows | Description)_
_Rows: 24_
_Column types: text | numeric | text_

**Caption candidates:**

- **section heading**: Generated Data

**Content (first 3 rows):**

| File | Rows | Description |
|------|------|-------------|
| `data/NB01_leaden_fur_de.csv` | 93 | Leaden 2018 Δfur DEGs (parsed from Frontiers Table 2.XLSX) |
| `data/NB01_leaden_iron_de.csv` | 491 | Leaden 2018 iron-limitation (2h DP) DEGs |
| `data/NB01_fur_only_signature.csv` | 93 | Join of Leaden Δfur DEGs with our 4584-vs-4580 logFCs |

_(24 data rows total; see REPORT.md lines 269–294 for full table)_

_Source: REPORT.md lines 269–294_

### report_tbl_09 — Notebooks

_Columns: 2 (Notebook | Purpose)_
_Rows: 10_
_Column types: text | text_

**Caption candidates:**

- **section heading**: Notebooks

**Content (first 3 rows):**

| Notebook | Purpose |
|----------|---------|
| `00_orientation.ipynb` | Phase A scoping: data shape, sphingolipid panel, ChvI overlap, Zik suppressors, top DEGs |
| `01_leaden2018_fur_signature.ipynb` | Concordance with Leaden 2018 Δfur DEGs; identifies the SspB-buffered cbb3/*fix* cohort |
| `02_caulo_fitness_ranking.ipynb` | RB-TnSeq fitness ranking of Path A + Path B Fur-released sets; H2 threshold check |

_(10 data rows total; see REPORT.md lines 300–311 for full table)_

_Source: REPORT.md lines 300–311_

### report_tbl_10 — Figures

_Columns: 2 (Figure | Description)_
_Rows: 9_
_Column types: text | text_

**Caption candidates:**

- **section heading**: Figures

**Content (first 3 rows):**

| Figure | Description |
|--------|-------------|
| `figures/NB07_synthesis_master.png` | 4-panel synthesis (recommended Figure 1 for the manuscript) |
| `figures/00_sphingolipid_locus_heatmap.png` | Sphingolipid locus log2(CPM+1) heatmap across libraries |
| `figures/NB01_fur_signature_scatter.png` | Leaden Δfur vs our 4584-vs-4580 logFC scatter (recommended Figure 2A) |

_(9 data rows total; see REPORT.md lines 315–325 for full table)_

_Source: REPORT.md lines 315–325_
