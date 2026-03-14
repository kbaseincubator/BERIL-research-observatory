# Structural Biology Memory

Living document capturing lessons learned across structural biology projects. The phenix agent reads this before starting refinement and updates it when new patterns are confirmed.

## Refinement Strategies

### By Resolution (X-ray)

| Resolution | Strategy | Notes |
|-----------|----------|-------|
| < 1.5 A | `individual_sites + individual_adp` (anisotropic if ratio > 3) | Hydrogens visible in density |
| 1.5-2.0 A | `individual_sites + individual_adp` | Standard isotropic B-factors |
| 2.0-3.0 A | `individual_sites + individual_adp + tls` (1 group/chain) | TLS captures domain motion |
| 3.0-4.0 A | `individual_sites + group_adp` + reference model | Too few observations for individual ADPs |
| > 4.0 A | `rigid_body` + NCS constraints | Jelly-body restraints help |

### By Method (Cryo-EM)

| Resolution | Strategy | Notes |
|-----------|----------|-------|
| < 2.5 A | `minimization_global + local_grid_search + adp` | Similar to high-res X-ray |
| 2.5-3.5 A | `minimization_global + local_grid_search + morphing` | Morphing helps domain fitting |
| 3.5-5.0 A | `minimization_global + morphing + simulated_annealing` | + NCS constraints for complexes |
| > 5.0 A | `rigid_body` only | Only domain placement meaningful |

## AlphaFold Integration Lessons

- AF models with mean pLDDT > 80: reliable for MR, typically solve with LLG > 100
- AF models with pLDDT 50-80: trim to confident regions before MR
- AF models with pLDDT < 50: unlikely to solve by MR alone
- PAE matrix is more informative than pLDDT for domain boundaries
- For bacterial proteins, VRMS=0.7 works in most cases; use 1.0 for eukaryotic
- MSA depth > 300 (from BERDL `alphafold_msa_depths`) correlates well with pLDDT > 70

## Common Pitfalls

_No project-specific pitfalls recorded yet. This section will grow as projects are completed._

<!-- Template for new entries:
- [project_id] Description of what happened and the resolution
-->
