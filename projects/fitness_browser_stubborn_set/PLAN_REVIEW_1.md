**Overall**: The plan is well-framed and mostly feasible with BERDL-native Fitness Browser data, but a few query details should be tightened before notebook work starts so the candidate set and evidence joins are reproducible.

**Critical**:
1. The candidate-pool definition depends on `|fit|_95`, but `docs/schemas/fitnessbrowser.md` documents only `genefitness.fit`, `t`, and the precomputed `specificphenotype` table; I could not verify any `fit95`/`fit_95` column in repo docs. Suggest either defining the candidate pool from `specificphenotype` directly or documenting exactly how `|fit|_95` will be reconstructed.
2. The MetaCyc path is underspecified: the schema docs list `metacycpathwayreaction` between `metacycpathway` and `metacycreaction`, but the plan only names `metacycpathway` and `metacycreaction`. Suggest adding the full join chain now so Notebook 02 does not stall on missing linkage tables.
3. `docs/pitfalls.md` notes that `kgroupec` uses column `ecnum`, not `ec`; the plan currently says "KO → EC number" but does not note the column-name gotcha. Suggest baking that exact column name into the query strategy.

**Recommended**:
1. The plan mixes environments ("JupyterHub Spark" and "via `/berdl-query` proxy chain locally") but does not pin the notebook execution pattern. Suggest stating one primary environment for notebooks and the exact `get_spark_session()` initialization that matches it, per `PROJECT.md`.
2. For SEED evidence, the plan treats `seedannotation` as sufficient for "functional subsystem" calls, but repo docs only verify `seedannotation.seed_desc`; subsystem hierarchy lives behind `seedannotation -> seedannotationtoroles -> seedroles` in `docs/pitfalls.md`. Suggest either downgrading this to description-level evidence or adding the full hierarchy join.
3. The overlap check looks reasonable, but Notebook 03’s comparisons to `functional_dark_matter` and `truly_dark_genes` should explicitly reuse archived outputs rather than re-derive them. Suggest naming the upstream files or lakehouse paths in the plan, similar to `essential_genome` and `truly_dark_genes`.
4. `README.md` has the expected sections, but the `Reproduction` section is still placeholder text. Suggest adding which notebooks require BERDL JupyterHub vs local execution before analysis begins, since `PROJECT.md` asks for this explicitly.

**Optional**:
1. The distinct framing versus `functional_dark_matter` and `truly_dark_genes` is credible, but there is still substantial table overlap. Suggest calling out any specific reusable extracts from those projects to reduce duplicated Spark work.
2. The row-count estimates are mostly aligned with `docs/schemas/fitnessbrowser.md`; if you keep the `reannotation` count as 1,762, consider noting that the schema doc leaves this table’s row count as "varies" and that your count is project-specific.

**Relevant pitfalls from docs/pitfalls.md**:
- `Fitness Browser KO Mapping Is a Two-Hop Join`: directly applies to the `besthitkegg -> keggmember -> kgroupdesc/kgroupec` evidence path; the plan already accounts for this correctly.
- `String-Typed Numeric Columns`: directly applies to `genefitness.fit`, `t`, `cofit`, and likely any thresholding in Notebook 01; the plan already notes the cast requirement.
- `Experiment Table Is Named experiment, Not exps`: relevant because the plan relies on `experiment.expGroup` and `condition_1`; the current plan uses the correct names.
- `seedannotationtoroles Joins on seed_desc, Not orgId/locusId`: relevant if "functional subsystem" evidence is meant literally rather than free-text SEED descriptions.

Plan reviewed by Codex (gpt-5.4).
