---
name: kg-narrate
description: Generate review-paper-quality prose for an entity page from its committed KG facts, section by section, cited and tier-aware. Regenerates only sections whose fact-hash changed. Use to make entity pages read like an encyclopedia article rather than a fact dump.
---

# kg-narrate

Optional prose layer for **entity** pages (the synthesis-hub narrative is `kg-synthesize`). Most page
text is templated directly from facts; this skill adds a readable lede/summary where it adds value.

## When to run
After a build, for entity pages whose **section fact-hash changed** (see `ids.section_fact_hash`).
Offline; committed and replayed by the deterministic render — never on the render path.

## Procedure
1. **Per section**, collect the canonical facts feeding it and compute its `section_fact_hash`. Skip
   sections whose hash is unchanged (no re-narration → stable prose, minimal diff).
2. **Dispatch a subagent** with only those facts (predicate + neighbor + tier + provenance). Instruct:
   write 1–3 sentences **strictly from the supplied facts**, cite provenance project ids, and mark
   `asserted` facts as unverified. No new claims, no external knowledge.
3. **Persist** the prose keyed by `{node_id: {section_id: {hash, html}}}` and inject via the render
   `narration` channel.

## Guarantees
- Section-level → a new finding updates one paragraph, not the whole article; same facts → same prose
  (cached). Tier-aware; cited; reproducible build.
