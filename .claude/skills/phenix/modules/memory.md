# Cross-Project Memory

How the phenix agent uses and updates the structural biology memory system.

## Memory Sources

1. **Living document**: `docs/structural_biology_memory.md` — manually curated lessons and patterns
2. **Delta Lake queries**: `kescience_structural_biology.refinement_cycles` — quantitative history
3. **Provenance logs**: Per-project `provenance.jsonl` files on MinIO

## When to Consult Memory

- **Starting a new project**: Check resolution-strategy recommendations before choosing parameters
- **MR fails**: Check if similar proteins had MR issues and what worked
- **Refinement stalls**: Check what strategies resolved similar plateaus
- **Validation outliers**: Check if certain outliers are known false positives

## Reading the Memory Document

```bash
# Always read before starting refinement
cat docs/structural_biology_memory.md
```

The document has sections:
- **Refinement Strategies** — by resolution and method
- **AlphaFold Integration Lessons** — pLDDT thresholds, MR success patterns
- **Common Pitfalls** — project-specific lessons learned

## Querying Historical Data

### What refinement strategy works at this resolution?

```sql
SELECT refinement_strategy,
       AVG(r_free) AS avg_rfree,
       AVG(molprobity_score) AS avg_molprobity,
       COUNT(*) AS n_projects
FROM kescience_structural_biology.refinement_cycles rc
WHERE rc.cycle_number = (
    SELECT MAX(rc2.cycle_number)
    FROM kescience_structural_biology.refinement_cycles rc2
    WHERE rc2.project_id = rc.project_id
)
GROUP BY refinement_strategy
ORDER BY avg_rfree;
```

### Best starting parameters for a given resolution range?

```sql
SELECT sp.resolution, rc.refinement_strategy, rc.r_free, rc.molprobity_score
FROM kescience_structural_biology.refinement_cycles rc
JOIN kescience_structural_biology.structure_projects sp
  ON sp.project_id = rc.project_id
WHERE sp.resolution BETWEEN 2.5 AND 3.0
  AND rc.cycle_number = 1
ORDER BY rc.r_free;
```

### How many cycles did similar projects need?

```sql
SELECT sp.method, sp.resolution,
       MAX(rc.cycle_number) AS total_cycles,
       MIN(rc.r_free) AS best_rfree
FROM kescience_structural_biology.refinement_cycles rc
JOIN kescience_structural_biology.structure_projects sp
  ON sp.project_id = rc.project_id
WHERE sp.status = 'completed'
GROUP BY sp.method, sp.resolution
ORDER BY sp.resolution;
```

## When to Update Memory

Update `docs/structural_biology_memory.md` when:

1. **A new refinement strategy proves effective** — add to the resolution-strategy table
2. **An AlphaFold pattern is confirmed** — add to the AF integration section
3. **A pitfall is encountered** — add to the Common Pitfalls section with project ID
4. **A parameter recommendation changes** — update the relevant section

### How to Update

```bash
# Read current memory
cat docs/structural_biology_memory.md

# Add new lesson (use Edit tool, not manual)
# Example: adding a new pitfall
```

Format for pitfalls:
```
- [{project_id}] {Description of what happened and the resolution}
```

Format for strategy updates:
```
### {Resolution Range}
- **Strategy**: {what works}
- **Evidence**: {project_id} — {brief result}
```

## Memory vs Provenance

| Aspect | Memory (docs/) | Provenance (MinIO) | Delta Lake |
|--------|---------------|-------------------|------------|
| Purpose | Human-readable lessons | Machine-readable audit trail | Queryable analytics |
| Granularity | Patterns across projects | Every action in one project | Aggregated metrics |
| Update frequency | When lessons are learned | Every agent action | After each cycle |
| Who reads it | Agent + humans | Debugging, audits | Agent queries, dashboards |

## Bootstrap: No History Yet

When `kescience_structural_biology` is empty (no prior projects), the agent should:

1. Use the static recommendations in `docs/structural_biology_memory.md`
2. Use the resolution-strategy tables in [resolution-strategies.md](../references/resolution-strategies.md)
3. Fall back to Phenix defaults
4. Be transparent: "This is the first project — using standard Phenix defaults for {resolution} A data"
