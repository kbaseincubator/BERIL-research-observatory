---
name: kg-correct
description: Turn a natural-language correction ("X is wrong, it should be Y") into a structured, append-only correction record that overrides the KG deterministically and survives re-extraction. Resolves targets against the graph, proposes a generalized rule, and rebuilds the affected pages. Use for occasional human corrections under the minimal-review model.
---

# kg-correct

The feedback loop that makes minimal human review safe: humans correct occasionally; corrections are
permanent, propagate minimally, and teach the extractor.

## When to run
Whenever a reviewer spots an error in the wiki (often via the review queue of `asserted`/`conflict` items).

## Procedure
1. **Resolve the target(s).** Parse the NL correction; query the committed graph (`out/nodes.tsv`,
   `out/edges.tsv`, `kg/*.kg.yaml`) for the matching node(s)/assertion(s). If ambiguous, list candidates
   and confirm. A correction may span **many** assertions across projects (a class-wide misgrounding).
2. **Write a structured record** to `compendium/corrections/<entity-or-project>.yaml` (append-only):
   ```yaml
   - id: corr/0001
     targets: [a:9f3c1e]          # content-addressed -> survives re-extraction
     kind: reground               # retract|fix-value|reground|force-merge|force-split|promote|demote
     value: {curie: "NCBITaxon:62977"}
     scope: instance              # default; rule proposed below
     proposed_rule: {kind: grounding_override, label: "ADP1", curie: "NCBITaxon:62977"}
     rationale: "ADP1 is A. baylyi, not E. coli"
     author: <orcid-or-name>
     timestamp: <iso>
   ```
3. **Integrity check.** Flag (do not silently apply) any correction that contradicts a strong `grounded`
   assertion; record author + rationale. Conflicting corrections on one target resolve by timestamp (last-wins, surfaced).
4. **Generalize (D13).** Apply the instance override now; if the `proposed_rule` is machine-safe (e.g. a
   grounding override) or the human confirms, add it to the deterministic rule tables
   (`ground/dictionary.yaml` for grounding; the heading-synonym map for parsing).
5. **Learn.** Append the correction as a regression fixture under `tests/` and as a few-shot/negative
   example for `kg-extract`, so the error cannot recur.
6. **Rebuild.** `compendium all ...` — `corrections.apply_corrections` applies overrides at highest
   precedence, keyed to content-addressed ids; only the blast radius re-renders.

## Guarantees
- Corrections are the highest-precedence, deterministic build input; keyed to stable ids so they
  survive re-extraction. Nothing is silently overwritten — contradictions surface as `Conflict`s.
