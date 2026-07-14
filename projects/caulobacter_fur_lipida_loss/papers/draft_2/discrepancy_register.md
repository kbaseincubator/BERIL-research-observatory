# Audit Discrepancies Register

Comparison between RESEARCH_PLAN.md and methods_provenance.md for the Caulobacter *fur* lipid A loss project (draft_2).

**Execution date**: 2026-06-06  
**Audit type**: Plan-to-execution fidelity

---

## JSON Output

```json
{
  "discrepancies": [
    {
      "entry_id": "D-001",
      "type_": "plan-prescribed-not-executed",
      "plan_quote": "Fetch Frontiers in Microbiology PMC supplementary files for PMC6120978 via WebFetch / wget — Frontiers typically attaches Supplementary Table S1 (DEG matrix) directly. Check GEO at https://www.ncbi.nlm.nih.gov/geo/?term=SRP136695 for an author-provided processed-count or DEG table.",
      "plan_section": "NB01 → Preflight (NB01a, in-notebook, fast), step 1a–1b",
      "execution_citation": "notebooks/01_leaden2018_fur_signature.ipynb — Spearman/Pearson correlations shown in cells 4–5, but no WebFetch or wget calls documented in methods_provenance.md. Preflight source acquisition step not evident in methods extraction.",
      "severity": "cosmetic",
      "recommendation": "Verify whether NB01 cells 1–3 contain WebFetch/wget preflight logic before the correlation analyses in cells 4–5. If preflight was skipped (DEG table found through other means or Leaden data was already in-hand), document the alternative preflight pathway in the Methods section."
    },
    {
      "entry_id": "D-002",
      "type_": "executed-not-prescribed",
      "plan_quote": "—",
      "plan_section": "—",
      "execution_citation": "notebooks/02b_h2_hypergeometric_verdict.ipynb created as a separate notebook to compute and report H2 hypothesis verdict (Fur phenotype-bearing gene percentage threshold). The plan prescribes NB02 to output `data/NB02_fur_regulon_phenotype_rank.csv` and figures, with H2 verdict to be inferred from those outputs during the synthesis phase.",
      "severity": "cosmetic",
      "recommendation": "The separation of H2 verdict logic into NB02b is good practice (clean separation of ranking from threshold comparison) and does not alter the scientific conclusions. Add a brief note to the Methods section that hypothesis verdict was computed in a dedicated verification notebook for transparency."
    },
    {
      "entry_id": "D-003",
      "type_": "executed-not-prescribed",
      "plan_quote": "—",
      "plan_section": "—",
      "execution_citation": "notebooks/06b_ncbi_annotation_presence.ipynb — separate NCBI annotation and presence/absence analysis. The plan prescribes NB06 to handle BERDL + NCBI fallback within a single notebook; instead, NCBI presence/absence queries executed in a distinct NB06b notebook.",
      "severity": "cosmetic",
      "recommendation": "The two-notebook structure (NB06 for BERDL pangenome + framework, NB06b for NCBI supplementary queries) is organizationally sound and follows the plan's fallback intent. Document the split as 'NB06 (BERDL primary) + NB06b (NCBI fallback)' in the Methods section for clarity."
    },
    {
      "entry_id": "D-004",
      "type_": "executed-not-prescribed",
      "plan_quote": "Identify *Caulobacter* SigU regulon members (literature + paperBLAST query) and test overlap with the late/consequence subset.",
      "plan_section": "NB03 → Approach, step 3 (SigU regulon identification and overlap with late ChvI subset)",
      "execution_citation": "notebooks/03_chvi_phase_partition_sigU.ipynb — Fisher's exact test (alternative='greater') documented in methods_provenance.md cell 10, line 19. However, the plan specifies 'hypergeometric p<1e-5' as the statistical test for ChvI-induced gene overlaps (Expected Outcomes, H1 phase structure section). Fisher's exact test is conceptually related (both test categorical association), but is the two-sided contingency-table analog rather than the hypergeometric set-overlap test.",
      "severity": "unclear",
      "recommendation": "Verify: (1) did NB03 use Fisher's exact test for ChvI-late vs SigU overlap, (2) if so, confirm that the test was appropriate for the contingency table (2x2 table of regulon membership), and (3) justify in the Methods section why Fisher's exact was chosen over the pre-registered hypergeometric test. If the choice was incidental, consider re-running with hypergeometric for consistency with the pre-registered plan."
    },
    {
      "entry_id": "D-005",
      "type_": "plan-prescribed-not-executed",
      "plan_quote": "Optional: AlphaFold structural overlay of CtpA vs LpxF (just inspection — no structural claim made).",
      "plan_section": "NB04 → Approach, step 4",
      "execution_citation": "methods_provenance.md does not list any AlphaFold or structural biology module imports in notebooks/04_sphingolipid_lpt_panel.ipynb (imports: matplotlib.pyplot, numpy, pandas, pathlib, seaborn). No AlphaFold query, structure download, or comparison logic documented.",
      "severity": "cosmetic",
      "recommendation": "This is labeled 'Optional' in the plan; if it was deemed non-essential and omitted, this is acceptable. If it was intended as a supporting visual (e.g., for supplementary material), add a note that it was omitted as exploratory and not critical to the main hypothesis tests."
    }
  ]
}
```

---

## Summary

| Total discrepancies found | 5 |
|---|---|
| **load-bearing** | 0 |
| **cosmetic** | 4 |
| **unclear** | 1 |

### Key Findings

1. **No load-bearing changes detected** — The executed notebooks follow the core hypothesis structure (H1–H4) and statistical thresholds prescribed in the plan.

2. **Organizational improvements** — NB02b (H2 verdict) and NB06b (NCBI fallback) were separated into distinct notebooks, a cleaner structure that strengthens code maintainability without changing scientific conclusions.

3. **Statistical test ambiguity (D-004)** — The choice of Fisher's exact test vs. hypergeometric test in NB03 should be verified and justified in the Methods section to ensure alignment with pre-registered thresholds.

4. **Preflight clarity (D-001)** — The NB01 WebFetch preflight step should be verified in the notebook source; if it was executed, ensure it is documented. If it was omitted, note the alternative source of the Leaden 2018 DEG data.

5. **Optional analysis omitted (D-005)** — AlphaFold structural comparison was marked "Optional" in the plan and was not executed; this is acceptable given the label.

---

## Recommendations for Methods Section

- Add a brief subsection "Hypothesis Verdict Workflow" explaining the separation of NB02 (ranking) and NB02b (verdict computation) for clarity.
- Clarify the statistical test used in NB03 (Fisher's exact vs. hypergeometric) and justify the choice.
- Document the source of the Leaden 2018 DEG table (WebFetch preflight vs. alternative).
- Confirm that all pre-registered significance thresholds were applied as specified.
