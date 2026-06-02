---
name: kg-synthesize
description: Write the cross-project synthesis narrative for a hub page (Topic, Organism, Direction, or the home "state of the science") from its deterministically-selected member assertions. Cached, cited, and tier-flagged. Use to generate the review-paper-quality prose that no single project's kg.yaml contains.
---

# kg-synthesize

The **core-value** LLM step. The deterministic core selects a hub page's **member set** (the
assertions/findings/conflicts reachable from the hub node via shared entities). This skill turns that
member set into a short, cited, review-style narrative — the thing that makes the wiki an *aggregation*
rather than an index.

## When to run
After a build, for hub pages whose **member-set hash changed** (section-level — unchanged sections are
not re-narrated). Offline; output is committed and replayed by the deterministic render.

## Procedure
1. **Member set (deterministic).** From the committed graph, collect the hub node's neighborhood:
   member findings/claims (with their project provenance and tiers) and any conflicts among them.
2. **Member-set hash.** `content_hash(sorted member assertion ids + their tiers)`. If a cached narrative
   exists for this hash, reuse it.
3. **Dispatch one subagent** with: the hub label/type, the member findings (statement + project id +
   tier), and any conflicts. Instruct it to write a **concise (120–200 word) synthesis** that:
   - states what is collectively known about the hub across projects,
   - **cites each claim** by its project id (e.g. "(acinetobacter_adp1_explorer)"),
   - **flags uncertainty**: note that findings are `asserted` (automated extraction, unverified) where so,
   - surfaces conflicts explicitly, and
   - invents nothing beyond the member set.
4. **Persist** `{hub_node_id: {"hash": ..., "narrative": ..., "members": [...], "tier": weakest_member_tier}}`
   to `kg/narration.json`.
5. **Render** with it: `render_site(graph, out_dir, narration=load("kg/narration.json"))`. The hub page
   shows a tier-flagged **Synthesis** section above the raw facts.

## Guarantees
- Non-deterministic draft, but **cached + provenance-stamped + committed** → reproducible build.
- The narrative's tier badge is the **weakest** tier among its inputs (a synthesis over `asserted`
  facts is itself badged unverified). Never on the render path.
