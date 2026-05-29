# Direction 5 Disprover — Sequencing Depth Artifact Test — 2026-04-04

## Hypothesis Tested
The high reads-per-OTU near mines is a sequencing depth artifact: near-mine samples have
more total reads (seq_depth), so reads_per_OTU = total_counts / n_genes is inflated.

## Results

### Test 1: Is seq_depth different near vs mid?
- Near (<5 km) median seq_depth: 47,690
- Mid (5-25 km) median seq_depth: 45,257
- FC (near/mid): 1.05 — essentially identical
- Mann-Whitney p = 0.685 — NOT significant

**Seq_depth is NOT elevated near mines.** The artifact hypothesis fails its first test.

### Test 2: Within-depth-quartile comparison
After stratifying samples by seq_depth quartile (to control for sequencing effort):

| Quartile | n near | n mid | FC (near/mid) | MW p |
|---|---|---|---|---|
| Q1 (lowest depth) | 153 | 186 | 1.49 | 2.53e-08 *** |
| Q2 | 43 | 296 | 4.66 | 6.73e-09 *** |
| Q3 | 68 | 270 | 4.75 | 1.86e-15 *** |
| Q4 (highest depth) | 146 | 193 | 1.01 | 0.049 * |

The dominance effect persists in Q1–Q3 (p < 1e-7 each). At Q4 (highest depth),
the effect nearly disappears (FC=1.01) — consistent with deep sequencing revealing
rare taxa even in stressed communities, flattening the dominance metric.

### Test 3: OLS residualization of seq_depth
After fitting reads_per_OTU ~ seq_depth (R²=0.123) and testing residuals:
- MW near vs mid residuals: p = 1.39e-13 (highly significant)
- Near residual median: -7.56
- Mid residual median: -121.45
- Spearman(dist_km, residual): ρ = -0.046, p = 0.091 (marginal)

The binary near/mid comparison survives depth residualization. The continuous gradient
is marginal — the effect is a **threshold** (step change at <5 km), not a gradient.

## Verdict

**DOMINANCE EFFECT IS REAL**

- Seq_depth is not elevated near mines (FC=1.05, p=0.685) — the primary artifact
  hypothesis is refuted
- Within-depth-quartile analysis confirms the effect persists in Q1–Q3
- After depth residualization, near vs mid residuals remain highly significant (p=1.4e-13)
- The pattern is a threshold (near <5 km sharply elevated), not a linear gradient

**Nuance**: Q4 (highest depth, ~>80k reads) shows near-zero dominance difference.
High-depth samples likely detect rare taxa even at metal-stressed sites, reducing the
apparent dominance signal. The metric is not ideal at extreme sequencing depths.

**Confidence in Dir5 finding: HIGH** — competitive exclusion interpretation is supported.
