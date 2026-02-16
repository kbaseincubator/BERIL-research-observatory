# Getting Started: BERIL Observatory on BERDL JupyterHub

Use BERIL and AI coding assistants on JupyterHub to explore BERDL data and produce shareable research.

This guide walks through the end-to-end workflow: logging in, setting up an AI assistant, running a research project, and submitting it for review.

## Step 1: Log in to BERDL JupyterHub

1. Go to [https://hub.berdl.kbase.us](https://hub.berdl.kbase.us)
2. Log in with your KBase credentials
3. Start a **Large** cluster size (needed for Spark queries against large tables)

Once your server is running, you'll have access to a JupyterLab environment with Spark pre-configured.

## Step 2: Install an AI coding assistant

Open a **Terminal** in JupyterHub (File > New > Terminal) and install Claude Code:

```bash
npm install -g @anthropic-ai/claude-code
```

Or, for one-off use without a global install:

```bash
npx @anthropic-ai/claude-code
```

Alternatively, you can install [OpenAI Codex CLI](https://github.com/openai/codex) or another AI coding assistant that supports custom skills.

### Tips for Codex Users

- Start Codex from the repository root (`BERIL-research-observatory/`) so it can read `AGENTS.md` and skill files in `.claude/skills/`.
- For long instructions, avoid huge inline prompts. Ask Codex to read prompt files from disk (for example `.claude/reviewer/SYSTEM_PROMPT.md`) instead of pasting large prompt text directly in the command.
- If a Codex run fails with network or DNS errors in a restricted sandbox, rerun with network-enabled permissions.
- For `/submit`-style review generation, use a compact instruction like: "Read and follow `.claude/reviewer/SYSTEM_PROMPT.md`, review `projects/{project_id}/`, and write `projects/{project_id}/REVIEW.md`."

## Step 3: Configure your API provider

### Option A: Direct Anthropic API key

If you have a personal Anthropic API key:

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### Option B: LBL users via CBORG

If you're at Lawrence Berkeley National Lab, you can use the [CBORG proxy](https://cborg.lbl.gov/tools_claudecode/) instead of a direct Anthropic key. Set the following environment variables:

```bash
export ANTHROPIC_AUTH_TOKEN=$CBORG_API_KEY
export ANTHROPIC_BASE_URL=https://api.cborg.lbl.gov
export ANTHROPIC_MODEL=claude-sonnet-4-5
```

The CBORG page documents additional optional variables for small model routing, telemetry, etc.

### Persist across sessions

Store your secrets in a dedicated file that won't accidentally get shared:

```bash
cat >> ~/.secrets << 'EOF'
export ANTHROPIC_AUTH_TOKEN=$CBORG_API_KEY
export ANTHROPIC_BASE_URL=https://api.cborg.lbl.gov
export ANTHROPIC_MODEL=claude-sonnet-4-5
EOF
```

Then have your `~/.bashrc` source it by adding this line:

```bash
echo 'source ~/.secrets' >> ~/.bashrc
```

Apply the changes in your current session:

```bash
source ~/.bashrc
```

## Step 4: Clone the BERIL repository

```bash
git clone https://github.com/kbaseincubator/BERIL-research-observatory.git
cd BERIL-research-observatory
```

## Step 5: Start Claude and get oriented

Launch Claude Code from the repo root:

```bash
claude
```

Then run the `/berdl_start` skill:

```
/berdl_start
```

This gives you an overview of BERDL, lists available skills and existing projects, and lets you choose a path:

- **Start a new project** — create a research project from scratch
- **Explore data** — browse collections and run queries
- **Continue an existing project** — pick up where you or someone else left off
- **Understand the system** — learn about the observatory architecture

## Step 6: Do science

The typical workflow looks like this:

1. **Ask questions** — describe what you want to investigate and the agent will help formulate a research question
2. **Explore data** — use `/berdl` to query BERDL databases with Spark SQL
3. **Plan and analyze** — the agent develops hypotheses, writes a research plan, and generates notebooks
4. **Run notebooks** — execute them on the JupyterHub Spark cluster
5. **Document findings** — record discoveries, pitfalls, and insights as you go

Your notebooks execute on the same Spark cluster you logged into, so queries run against the full lakehouse without any extra setup.

For query guidance, see:
- [docs/pitfalls.md](pitfalls.md) — common SQL gotchas and how to avoid them
- [docs/performance.md](performance.md) — strategies for querying billion-row tables efficiently

## Step 7: Save your work as you go

Commit and push at any point — there's no need to wait until the project is "done":

```bash
git add projects/my_project/
git commit -m "Add initial analysis notebook"
git push
```

Others can see work in progress on the [Observatory UI](http://beril-observatory.knowledge-engine.development.svc.spin.nersc.org/). Pushing early and often makes your work visible and lets collaborators build on it.

## Step 8: Submit for review when ready

When your project is ready for feedback, run the `/submit` skill from within your project directory:

```
/submit
```

This will:

1. **Validate** that your README has the required sections (Research Question, Authors, etc.)
2. **Generate** an AI review (`REVIEW.md`) with feedback on methodology, reproducibility, and completeness
3. Prompt you to **commit and push** the review along with your final work

You can keep working on the project after submitting — submission is not a one-time event.

## Available Skills

| Skill | Description |
|-------|-------------|
| `/berdl_start` | Get oriented and start a research project — the agent drives the full workflow |
| `/berdl` | Query BERDL databases with Spark SQL |
| `/berdl-discover` | Discover and document new BERDL databases |
| `/literature-review` | Search PubMed, Europe PMC, and other sources for relevant literature |
| `/synthesize` | Interpret results and draft findings |
| `/submit` | Submit a project for automated validation and AI review |

## Resources

- **Observatory UI**: [BERIL Observatory](http://beril-observatory.knowledge-engine.development.svc.spin.nersc.org/)
- **BERDL JupyterHub**: [hub.berdl.kbase.us](https://hub.berdl.kbase.us)
- **CBORG (LBL users)**: [cborg.lbl.gov](https://cborg.lbl.gov/tools_claudecode/)
- **Collections overview**: [docs/collections.md](collections.md)
- **Query pitfalls**: [docs/pitfalls.md](pitfalls.md)
- **Performance tips**: [docs/performance.md](performance.md)
- **Schema documentation**: [docs/schemas/](schemas/)
