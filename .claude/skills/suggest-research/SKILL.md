---
name: suggest-research
description: Review completed projects and their findings, then suggest a new high-impact research topic grounded in available BERDL data and scientific gaps. Use when the user wants to identify the next best research direction based on what has already been done.
allowed-tools: Bash, Read, Write, Edit, WebSearch, AskUserQuestion
user-invocable: true
---

# Suggest Research Skill

Survey the research landscape — completed projects, their findings, proposed ideas, and available BERDL data — then synthesize a prioritized recommendation for the next research topic. The recommendation is grounded in what has been learned, what data is available, and where scientific impact is highest.

## Usage

```
/suggest-research
```

No arguments required. The skill reads the full project landscape automatically.

## Workflow

### Step 1: Read the Research Idea Backlog

Read `docs/research_ideas.md` in full. For each entry, note:
- **Status**: PROPOSED, IN_PROGRESS, or COMPLETED
- **Priority** and **Effort** tags
- **Research Question** and **Hypotheses**
- **Impact** and **Dependencies**

Build three lists:
1. `completed_ideas` — ideas with Status: COMPLETED
2. `in_progress_ideas` — ideas with Status: IN_PROGRESS
3. `proposed_ideas` — ideas with Status: PROPOSED (candidates for recommendation)

### Step 2: Inventory All Projects

List all directories under `projects/`. For each project directory:

1. Read `projects/{id}/README.md` — capture the **Research Question**, **Status**, and any **Quick Links**
2. If Status indicates completion (contains "Complete" or links to a REPORT), mark it as a **finished project**
3. If Status indicates active work, mark it as **in-progress**

This cross-checks `research_ideas.md` against actual on-disk project state.

### Step 3: Read Findings from Completed Projects

For every finished project identified in Step 2:

1. Read `projects/{id}/REPORT.md`
2. Extract:
   - **Key Findings** (the 2–4 headline results)
   - **Future Directions** section — these are investigator-suggested follow-ups
   - **Limitations** — gaps the authors identified
   - **Novel Contribution** — what made the project scientifically unique
3. Note any cross-project patterns: recurring organisms, pathways, themes, or data gaps that appear in multiple reports

### Step 4: Read the Discoveries Log

Read `docs/discoveries.md`. Extract:
- Serendipitous findings not yet formalized into a project
- Patterns noted across multiple analyses
- Data anomalies flagged for follow-up

These often represent high-value starting points that are not yet in `research_ideas.md`.

### Step 5: Understand Available Data

Read `docs/collections.md` to inventory the BERDL data collections. For each collection, note:
- Collection name and identifier
- What organism/scale/data type it covers
- Whether it has been heavily used (cross-reference with reports) or is underexplored

Identify **underexplored collections** — present in BERDL but rarely cited in completed project reports.

### Step 6: Synthesize the Landscape

Build an internal summary across Steps 1–5:

| Dimension | Assessment |
|---|---|
| Completed topics | What themes have been thoroughly investigated? |
| Active topics | What is currently in progress (avoid duplicating)? |
| Proposed backlog | Which PROPOSED ideas have the strongest prerequisites now met? |
| Future directions | What did completed projects recommend as next steps? |
| Discovery log | What serendipitous patterns are unclaimed? |
| Underexplored data | Which BERDL collections have not been leveraged? |
| Recurring gaps | What limitation appears in multiple project reports? |

### Step 7: Ask the User for Priorities (Optional)

If the user did not specify a focus, ask:

> "I've reviewed the project landscape. To tailor my recommendation, a few quick questions:
> 1. Any preferred scientific theme? (e.g., evolution, metabolism, ecology, gene function)
> 2. Effort preference? (Low: 1–2 weeks / Medium: 1 month / High: multi-month)
> 3. Should the new topic extend an existing project or open a new direction entirely?"

If the user says "just suggest something," skip to Step 8 with no constraints.

### Step 8: Identify Top Candidates

From the synthesized landscape, identify 2–3 candidate topics. For each candidate, score it against:

| Criterion | Weight | Question |
|---|---|---|
| Scientific novelty | High | Is this genuinely new relative to completed work? |
| Data readiness | High | Is required BERDL data available and well-characterized? |
| Impact | High | Does it extend or challenge a significant existing finding? |
| Feasibility | Medium | Are dependencies met? Does similar methodology already exist in the repo? |
| Backlog alignment | Medium | Does it address a PROPOSED idea or Future Direction from a report? |
| Effort fit | Low | Is the scope appropriate for a focused project? |

Select the **top candidate** with the strongest combined score. Retain the runner-up as an alternative.

### Step 9: Search Literature for the Top Candidate

Invoke `/literature-review` (or search directly via `paper-search-mcp` tools) to answer:

1. Has this specific question been studied before? In which organisms/scales?
2. What methods were used and what were the results?
3. What remains unstudied or contested?
4. Are there contradictory findings that BERDL's scale could resolve?

Use this to sharpen the hypothesis and confirm novelty.

### Step 10: Present the Recommendation

Present a structured recommendation to the user:

```markdown
## Recommended Research Topic: {Title}

### Why Now?
{1–2 sentences: what completed work enables this, and why this is the right next step}

### Research Question
{The specific scientific question, one sentence}

### Hypotheses
- **H1**: {Primary hypothesis with direction}
- **H0**: {Null hypothesis}
- **H2** (optional): {Secondary exploratory hypothesis}

### Grounding in Completed Work
- Extends **{project_id}** (Finding: {key result from its REPORT.md})
- Addresses the limitation noted in **{project_id}**: "{limitation quote}"
- Uses methodology established in **{project_id}** (reuse notebooks/src/)

### Required BERDL Data
| Collection | Tables | What it provides |
|---|---|---|
| `{collection_id}` | `{table}` | {description} |

### Approach
1. {Step 1: data extraction query approach}
2. {Step 2: analysis method}
3. {Step 3: statistical test or model}
4. {Step 4: validation or comparison}

### Expected Impact
- {Scientific contribution 1}
- {Scientific contribution 2}
- {Connection to the broader BERIL mission}

### Literature Context
- Aligns with: {Author et al. Year} — {key point}
- Extends beyond: {Author et al. Year} — {what BERDL adds}
- Open question: {what the literature has not settled}

### Effort Estimate
**{Low / Medium / High}** — {brief rationale}

### Dependencies
- {Any prerequisite data, analysis, or completed project required}

---

### Alternative Topic: {Alt Title}
{2–3 sentence summary of the alternative and why it was ranked second}
```

### Step 11: Offer to Register and Start the Idea

After presenting the recommendation, ask:

> "Would you like me to register this in `docs/research_ideas.md` and start it as a new project?"

**Rules for `research_ideas.md`:**
- **Only append new entries.** Never edit, reformat, or modify existing sections or entries.
- If the recommendation is largely an update or extension of an existing project or PROPOSED idea, note the relationship in the new entry's summary (e.g., "Extends `{project_id}`" or "Builds on PROPOSED idea `{idea_title}`") but do not alter the original entry.

If yes:

1. **Add to research_ideas.md**: Append the new entry at the bottom of the file using the standard format matching existing entries (Status: PROPOSED, Priority, Effort, Research Question, Approach, Hypotheses, Impact, Dependencies, Location). Do not modify any existing content.
2. **Start the project**: Invoke `/berdl_start` to scaffold and begin the new project, using the confirmed research idea (title, research question, hypotheses, approach, and data sources from Step 10) as the starting context for ideation.

If no, leave no files modified.

## Integration

- **Reads from**: `docs/research_ideas.md`, `docs/discoveries.md`, `docs/collections.md`, `projects/*/README.md`, `projects/*/REPORT.md`
- **Calls**: `/literature-review` (Step 9, for novelty check on top candidate); `/berdl_start` (Step 11, if user confirms the idea)
- **Optionally writes**: `docs/research_ideas.md` (appends new PROPOSED entry only — never edits existing entries)
- **Consumed by**: `/literature-review`, `/synthesize`

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.
