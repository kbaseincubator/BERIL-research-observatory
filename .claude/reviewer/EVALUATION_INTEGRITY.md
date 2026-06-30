# Evaluation Integrity checklist

The single source of truth for the silent failures that make a result look better
than it is. Referenced by the project reviewer (`SYSTEM_PROMPT.md`), the plan
reviewer (`PLAN_REVIEW_PROMPT.md`), and the refutation pass (`REFUTATION_PROMPT.md`)
so the criteria live in **one** place.

Anchored to the leakage taxonomy of Kapoor & Narayanan, *"Leakage and the
reproducibility crisis in machine-learning-based science"* (Patterns, 2023), and
the **REFORMS** reporting checklist (Kapoor et al., 2024). These failures hide in
the **numbers**, not the prose — inspect the cell `outputs` (split sizes, class
balances, the exact metric computed), name the cell/query, and state the check
that would rule each relevant failure in or out.

## Universal — apply even to plain descriptive SQL

1. **Selection bias** — non-representative subsetting, survivorship filtering, or
   dropping rows in a way that flatters the result.
2. **Metric misuse** — a metric mismatched to the question, accuracy on an
   imbalanced target, or no multiple-comparison correction / p-hacking.

## Conditional — only when the analysis trains or tunes a model or threshold

3. **Train/test leakage** — target, feature, look-ahead/temporal, or group leakage
   (related rows — same genome, taxon, or sample — straddling the split); or
   reporting performance on the same data a model/threshold was tuned on.
4. **Benchmark/baseline selection** — a cherry-picked or missing comparator, or no
   held-out set.

Most BERDL analyses are descriptive SQL with no model — **don't force a train/test
leakage hunt where nothing was fit.** If none is evident, say so briefly.

If `projects/<id>/claims.json` is present, read it: each claim's computed
**groundedness** and **tier_mismatch** shows where a written confidence may outrun
its evidence. Corroborate against the actual cell outputs.
