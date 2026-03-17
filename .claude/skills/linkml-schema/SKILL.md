---
name: linkml-schema
description: Generate LinkML schema YAML from markdown, Excel, or text descriptions. Scaffold a LinkML project repo and push to GitHub.
allowed-tools: Bash, Read, Write, Edit, AskUserQuestion
user-invocable: true
---

# LinkML Schema Generator Skill

## Overview

Convert informal data descriptions (markdown tables, Excel spreadsheets, plain text) into formal LinkML schema YAML. Optionally scaffold a full LinkML project repo and push it to GitHub.

## Workflow

Execute phases sequentially. Phases 4 and 5 are optional — offer them after Phase 3 succeeds.

---

### Phase 1 — Environment Setup

1. Check `python3` is available (`command -v python3`). If missing, **stop** and report.
2. Check for `linkml` and `openpyxl` Python packages:
   ```bash
   python3 -c "import linkml" 2>/dev/null && echo "linkml OK" || echo "linkml MISSING"
   python3 -c "import openpyxl" 2>/dev/null && echo "openpyxl OK" || echo "openpyxl MISSING"
   ```
3. Auto-install missing packages:
   - If a virtualenv is active (`$VIRTUAL_ENV` is set), use `pip install <pkg>`.
   - Otherwise use `pip install --user <pkg>`.
   - Packages to install: `linkml` (provides `linkml-validate` CLI), `openpyxl` (Excel reading).
4. **Do not** check for `copier` or `gh` yet — only check those lazily in Phases 4/5.

---

### Phase 2 — Input Parsing & Schema Inference

1. **Read reference files first:**
   - Read `references/linkml-cheatsheet.md` for schema syntax.
   - Read `references/type-mapping.md` for type inference rules.

2. **Identify inputs** — ask the user or detect from context. Supported formats:
   - **Markdown** (`.md`): Extract classes from `##` headers, slots from table rows or bullet lists, relationships from cross-references, enums from value lists.
   - **Excel** (`.xlsx`): Use inline Python with `openpyxl` to read the workbook:
     ```python
     import openpyxl, json
     wb = openpyxl.load_workbook("INPUT.xlsx", data_only=True)
     result = {}
     for sheet in wb.sheetnames:
         ws = wb[sheet]
         headers = [c.value for c in ws[1] if c.value]
         rows = []
         for row in ws.iter_rows(min_row=2, max_col=len(headers), values_only=True):
             rows.append(list(row))
         result[sheet] = {"headers": headers, "sample_rows": rows[:20]}
     print(json.dumps(result, indent=2, default=str))
     ```
     - Sheet names → candidate class names.
     - Column headers → candidate slot names.
     - Sample values → infer types using `references/type-mapping.md`.
     - Detect enums (≤10 distinct non-null values in a column, short strings, low cardinality ratio).
     - Detect identifiers (`id` or `*_id` column + all unique values).
     - Detect relationships (`*_id` columns whose name matches another sheet).
   - **Plain text**: Extract entities (nouns → classes), properties (adjectives/attributes → slots), relationships (verbs → references), listed values → enums.

3. **Merge inputs** when multiple files are provided. Prefer Excel-inferred types over markdown/text guesses. Deduplicate classes by name similarity.

4. **Interactive review** via `AskUserQuestion`:
   - Present inferred classes with their slots.
   - Confirm enum values.
   - Confirm relationships between classes.
   - Ask for: schema name, schema description, root class (container), default ID prefix.
   - Let the user rename, add, or remove items.

---

### Phase 3 — Schema Generation

1. **Build the schema YAML** using Python to ensure correct formatting:
   ```python
   import yaml

   schema = {
       "id": f"https://w3id.org/{schema_name}",
       "name": schema_name,
       "prefixes": {
           "linkml": "https://w3id.org/linkml/",
           schema_name: f"https://w3id.org/{schema_name}/",
       },
       "imports": ["linkml:types"],
       "default_range": "string",
       "classes": { ... },
       "enums": { ... },
   }

   with open(output_path, "w") as f:
       yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
   ```

2. **Naming conventions:**
   - Schema name: `snake_case`
   - Classes: `CamelCase`
   - Slots: `snake_case`
   - Enums: `CamelCaseEnum` (e.g., `SampleTypeEnum`)
   - Enum permissible values: `snake_case`

3. **Validate** the generated schema:
   ```bash
   linkml-validate -s SCHEMA.yaml
   ```
   - If validation fails, read the error, auto-fix the schema, and retry (up to 3 attempts).
   - Common fixes: missing `imports`, wrong range names, duplicate slot definitions.

4. **Present results** to the user:
   - Show the generated YAML (or a summary if large).
   - Report stats: number of classes, slots, enums, relationships.
   - Ask via `AskUserQuestion`: "What would you like to do next?"
     - **Refine** — edit the schema further.
     - **Scaffold project** — proceed to Phase 4.
     - **Done** — stop here.

---

### Phase 4 — Project Scaffolding (optional)

1. Read `references/copier-template-guide.md`.
2. Check and install `copier` if missing:
   ```bash
   python3 -c "import copier" 2>/dev/null || pip install copier
   ```
3. Ask for project metadata via `AskUserQuestion`:
   - Project name (default: schema name)
   - GitHub organization or username
   - Author full name
   - License (default: MIT)
4. Run copier:
   ```bash
   copier copy --trust \
     --data project_name=NAME \
     --data github_org=ORG \
     --data full_name="AUTHOR" \
     --data license=LICENSE \
     gh:linkml/linkml-project-copier ./PROJECT_DIR
   ```
5. Place the generated schema at `src/{project_name}/schema/{schema_name}.yaml`.
6. Validate within project context:
   ```bash
   cd PROJECT_DIR && linkml-validate -s src/*/schema/*.yaml
   ```
7. **Fallback**: if copier fails (network, template version mismatch), offer to create a minimal project structure manually:
   ```
   PROJECT_DIR/
   ├── src/{project_name}/schema/{schema_name}.yaml
   ├── project/
   │   └── .gitkeep
   ├── pyproject.toml   (minimal LinkML project config)
   └── Makefile          (gen-project, test, lint targets)
   ```

---

### Phase 5 — GitHub Push (optional)

1. Check `gh` is installed and authenticated:
   ```bash
   command -v gh && gh auth status
   ```
   If not authenticated, **stop** and tell the user to run `gh auth login`.

2. Ask via `AskUserQuestion`:
   - GitHub org or username
   - Repository name (default: project name)
   - Visibility: public or private

3. Create repo and push:
   ```bash
   cd PROJECT_DIR
   gh repo create ORG/REPO --VISIBILITY --source=. --remote=origin
   git init
   git add .
   git commit -m "Initial LinkML schema: SCHEMA_NAME"
   git branch -M main
   git push -u origin main
   ```

4. Report final URL and next steps:
   - `make setup` — install project dependencies
   - `make gen-project` — generate Python dataclasses, JSON-Schema, etc.
   - `make test` — run schema tests
   - `make gen-doc` — generate documentation site

---

## Error Handling

| Tier | Examples | Action |
|------|----------|--------|
| **Blocking** | `python3` missing, input file not found, `gh` not authenticated | Stop and report clearly |
| **Recoverable** | pip package missing, YAML validation error, copier failure | Auto-fix / retry up to 3 times, then fallback |
| **Ambiguous** | Unclear class names, type ambiguity, naming conflicts | Ask user via `AskUserQuestion` |

## Safety Rules

1. Never overwrite existing files without asking first.
2. Never push to GitHub without explicit user confirmation.
3. Always validate generated schemas before presenting them as complete.
4. Use `--trust` with copier only after confirming the template source with the user.
