# Direction 4 Disprover — TRI Geographic Confound — 2026-04-04

## Hypothesis Tested
TRI annotations are US-only, so the TRI advantage over MRDS is a geographic confound
(US deserts are systematically richer than non-US deserts for unrelated reasons).

## Results

### Region Distribution
| Region | n total | n TRI-annotated | TRI rate | Median richness |
|---|---|---|---|---|
| US | 1058 | 631 | 60% | 1010 |
| Asia/ME | 439 | 0 | 0% | 457 |
| S. America | 246 | 0 | 0% | 56 |
| Africa | 206 | 0 | 0% | 238 |
| other | 280 | 36 | 13% | 198 |
| Australia | 6 | 0 | 0% | 618 |

### Key Finding: Within-US Comparison
TRI coverage is 60% US-only vs 0% for Africa/Asia/S.America. US deserts have
**4.2× higher median richness** than African deserts and **18× higher** than S. American deserts.
This IS a geographic confound — the TRI dataset is not globally representative.

**However**: Within US-only samples, TRI still outperforms MRDS:
- US MRDS ρ = +0.179 (n=939, p=3.1e-08)
- US TRI ρ = +0.614 (n=631, p=1.3e-66)

The TRI advantage (ρ=0.614 vs 0.179) PERSISTS within the same geographic region (US).

### Non-US MRDS for comparison
Non-US MRDS ρ = +0.336 (p=1.9e-12, n=416) — actually STRONGER than US MRDS

## Verdict

**PARTIAL CONFOUND CONFIRMED — TRI EFFECT ALSO REAL**

- The TRI dataset is entirely US-biased (0% of non-US samples annotated)
- US desert samples have systematically higher richness than global deserts (potentially
  due to sampling methodology, ecosystem type, or soil organic matter differences)
- **BUT**: within US geography alone, TRI distance (ρ=+0.614) still dramatically
  outperforms MRDS mine distance (ρ=+0.179)

The remaining question is whether TRI proximity captures **industrial chemical exposure**
or **urbanization/anthropogenic land use** more broadly (sites near factories may also
be near roads, agriculture, and other richness-altering factors).

**Confidence in Dir4 finding: MEDIUM** — geographic bias is real, but TRI signal
persists within-US and is unlikely to be purely a regional artifact.
