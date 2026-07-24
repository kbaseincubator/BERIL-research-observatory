---
reviewer: BERIL Automated Review (Claude, claude-sonnet-5)
date: 2026-07-10
project: nmdc_context_audit
---

# Review: NMDC Context Audit

## Summary
This is a well-executed knowledge-engineering audit rather than a conventional statistical analysis, and it is honest about that framing from the outset. The project enumerates every BERDL resource whose name contains "nmdc," classifies each into one of six provenance classes across three tenants, and backs every claim with a live, reproducible probe (row counts and Iceberg snapshot timestamps) captured in a single notebook. The primary deliverable — a 15-file, cross-linked Open-Knowledge-Format directory under `knowledge/` — is genuinely useful and specific (a goal→resource decision guide, a prior-project reuse map, per-resource provenance pages). I spot-checked the two highest-stakes factual claims in the REPORT (the `docs/schemas/nmdc.md` 404 and the absence of NMDC content in the `berdl` skill) directly against the repo and both hold up. The main weakness is that the README was not brought current with the completed work: it still reads as a stub (`*TBD*` Quick Links, an empty Reproduction section) even though RESEARCH_PLAN.md and REPORT.md are both fully drafted, which will confuse anyone who opens README.md first.

## Methodology
The research question is clearly stated and, notably, is explicit about what kind of claim it is: "this is a knowledge-engineering audit, not a statistical test," with H0/H1 evaluated against enumerated, evidence-backed confusion modes rather than a p-value. That framing is appropriate to the subject matter (a documentation/discoverability gap) and the RESEARCH_PLAN.md is upfront about it, which avoids over-claiming statistical rigor the analysis doesn't have.

Data sources are clearly identified — every resource in `data/nmdc_landscape.csv` is tied to a specific database, a signature table, and a live row count / snapshot timestamp, all captured via the two probe scripts (`data/probe_identifiers.py`, `data/probe_provenance.py`) and consolidated in the single notebook (`00_nmdc_landscape.ipynb`). This is reproducible in the literal sense: the probe scripts and notebook can be re-run on-cluster and will regenerate `data/nmdc_landscape.csv`, `data/nmdc_naming_cruft.csv`, and both figures.

One limitation acknowledged in REPORT.md's own Limitations section, and worth restating here: the "does this labeling confuse BERIL users" half of the research question is tested indirectly — via inferred confusion modes (broken links, missing skill content, tenant/prefix mismatches) and a prior-project usage map — rather than via any direct evidence of a user actually making a wrong resource choice. The `nmdc-prior-project-usage.md` table is the closest thing to behavioral evidence (8/10 prior projects reached for `kbase.nmdc_arkin` rather than the genuine `nmdc` tenant), and it is a reasonable proxy, but the causal claim ("this labeling *causes* sub-optimal selection") is stronger than what the evidence directly shows. The REPORT is appropriately hedged about this in its own Limitations section.

## Code Quality
The notebook (`00_nmdc_landscape.ipynb`) is short, linear, and easy to follow: enumerate → classify/count/date → catalogue cruft → persist → visualize → takeaways. SQL is minimal and correct — `SELECT COUNT(*)` and `SELECT max(committed_at) FROM {table}.snapshots` are the only two query patterns, both of which are exactly what `docs/pitfalls.md`'s "REST API Reliability" section recommends (direct Spark SQL over the REST API, and Iceberg metadata for counts rather than full scans). The project's own Performance Notes in REPORT.md correctly document that `COUNT(*)` on a 1.83B-row table returns instantly via Iceberg metadata and that `DESCRIBE DATABASE EXTENDED` is `Forbidden` for `kbase.nmdc_*` even though reads succeed — both are accurate observations (visible directly in `data/provenance_probe.md`) and are the kind of finding that belongs in a shared pitfalls/performance file.

The dual dotted/underscore alias handling (de-duplicating to the dotted Iceberg form before iterating) directly reflects the general pitfall documented in `docs/pitfalls.md` ("Namespace Convention Changed from Underscores to Dots") — good awareness of prior art rather than rediscovering it. I did not find a project-local `memories/pitfalls.md` to cross-check against; none exists in this project directory.

I verified two of the REPORT's most consequential factual claims directly against the repository rather than taking them on faith:
- **Finding 4 / Recommendation 1**: `docs/schema.md:16` does link to `schemas/nmdc.md`, and `docs/schemas/` does not exist on disk — confirmed, the link is a genuine 404.
- **Finding 4 / Recommendation 2**: `docs/overview.md` contains no mention of "nmdc" (case-insensitive grep, zero hits), and `.claude/skills/berdl/modules/` contains no NMDC-named file — confirmed, the skill has zero NMDC content today.

Both check out, which gives me reasonable confidence in the rest of the evidence table (row counts, snapshot timestamps), which I did not independently re-run against the live cluster in this review session.

## Findings Assessment
The four findings in REPORT.md are each backed by a specific number traceable to `data/provenance_probe.md` or `data/nmdc_landscape.csv` (e.g., the 16,640 vs. 51.7M biosample scale trap, the ~4-month currency spread, the `ForbiddenException`-on-metadata-but-not-on-reads asymmetry). Conclusions are supported by the data shown, and nothing in the REPORT reads as "to be filled" or incomplete. Limitations are explicitly acknowledged (inferred provenance vs. an ingestion manifest; access-restricted `kbase.nmdc_*` database descriptions; no diff against live upstream NMDC/NCBI record counts). The Interpretation section is careful to note that co-hosting external data under the `nmdc` tenant is often *intentional and valuable* (BERDL's harmonization layer over 51.7M raw NCBI samples), rather than treating every provenance mismatch as a bug — this is a fair and non-alarmist read of the evidence.

The Discoveries and Performance Notes entries in REPORT.md are reasonable candidates for cross-project surfacing:
- The "nmdc tenant co-hosts a 51.7M-row NCBI mirror + Pfam vocabulary" discovery is well-scoped and directly supported by Finding 2.
- The "kbase.nmdc_neon is NEON, not NMDC" discovery is unambiguous and load-bearing (agency mis-attribution risk) — worth keeping.
- The "COUNT(*) on 1.83B rows returns instantly via Iceberg metadata" and "DESCRIBE DATABASE EXTENDED is Forbidden even when COUNT succeeds" performance notes are concrete, testable, and phrased at the right scope (general BERDL access-surface behavior, not project-specific).
- The dual dotted/underscore alias note is somewhat redundant with the existing `docs/pitfalls.md` "Namespace Convention Changed from Underscores to Dots" entry — it restates the general pitfall rather than adding new information (the `get_databases()` double-counting angle is a legitimate small addition, but the entry could be tightened to just that delta).

## Suggestions
1. **(Critical for submission) Update README.md before `/submit`.** The Quick Links section still marks RESEARCH_PLAN.md and REPORT.md as "(TBD)" and the Status line says "awaiting `/berdl-review` and `/submit`" — both fine as transient state, but the **Reproduction** section is a placeholder (`*TBD — add prerequisites and step-by-step instructions after the audit is complete.*`) even though the audit *is* complete and the reproduction steps are trivial to write (run the two probe scripts, then the notebook, on-cluster). A reader who opens README.md first — the documented entry point — will conclude the project is unfinished when it is not.
2. **Tighten the alias-dedup Performance Note to avoid redundancy with `docs/pitfalls.md`.** The general dotted/underscore migration pitfall is already documented repo-wide; keep only the `get_databases()`-returns-both-forms / de-dupe-before-iterating detail, which is the genuinely new piece.
3. **Consider strengthening the causal claim in Finding 1/Interpretation.** "The label...directly causes the sub-optimal-resource selection" is currently supported by inference (broken docs links, missing skill content, prior-project reuse skew toward `nmdc_arkin`) rather than direct observation of a wrong selection happening. This is already flagged in the Limitations section, but the Interpretation section's phrasing could be softened slightly to match ("is consistent with" rather than "directly causes"), or the prior-project usage map could be extended with a brief note on whether any of those 10 projects show an actual documented misstep (e.g., a query written against the wrong table).
4. **Minor**: `beril.yaml` shows `artifacts.review: false` — expected pre-review, will presumably flip after this review is filed; no action needed from the author beyond the normal submit flow.
5. **Nice-to-have**: `references.md` and REPORT.md's References section are near-duplicates; consider having REPORT.md's References section simply point to `references.md` to avoid maintaining the same list in two places as the project evolves.

## Review Metadata
- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-5)
- **Date**: 2026-07-10
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, beril.yaml, references.md, 1 notebook (`00_nmdc_landscape.ipynb`), 2 probe scripts, 3 data files, 2 figures, 15 knowledge-base files, docs/pitfalls.md (repo-level), docs/schema.md and docs/overview.md (spot-checked for cited claims)
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

<!-- report_hash: sha256:0881643a89c55c3cb0768074116e3c0f0f8c595016941033c4b386eb8650af2d -->
