# LinkML Project Copier Template Guide

## Overview

The [linkml-project-copier](https://github.com/linkml/linkml-project-copier) template scaffolds a full LinkML project with build tooling, tests, documentation generation, and GitHub Actions CI.

## Installation

```bash
pip install copier
```

## Usage

### Basic Command

```bash
copier copy --trust gh:linkml/linkml-project-copier ./my-project
```

### Non-Interactive (Scripted) Usage

Pass all required answers via `--data` flags:

```bash
copier copy --trust \
  --data project_name=my_project \
  --data github_org=my-org \
  --data full_name="Jane Doe" \
  --data license=MIT \
  gh:linkml/linkml-project-copier ./my-project
```

### Important: `--trust` Flag

The template runs post-generation tasks (e.g., `make setup`). The `--trust` flag is required to allow these tasks. Only use with trusted template sources.

## Template Questions

| Question | `--data` Key | Default | Description |
|----------|-------------|---------|-------------|
| Project name | `project_name` | — | `snake_case` name used for package and directories |
| GitHub org | `github_org` | — | GitHub organization or username |
| Full name | `full_name` | — | Author name for metadata |
| License | `license` | `MIT` | One of: `MIT`, `BSD-3`, `Apache-2.0`, `CC-BY-4.0`, `GNU-GPL-v3.0` |

## Generated Directory Structure

After running copier, the project directory will look like:

```
my-project/
├── src/
│   └── my_project/
│       ├── schema/
│       │   └── my_project.yaml    ← Place your schema here
│       └── datamodel/
│           └── __init__.py
├── project/
│   ├── jsonschema/
│   ├── owl/
│   ├── shacl/
│   └── sqlschema/
├── tests/
│   └── test_data.py
├── docs/
├── examples/
├── Makefile
├── pyproject.toml
├── mkdocs.yml
└── README.md
```

### Key Paths

- **Schema location**: `src/{project_name}/schema/{schema_name}.yaml`
- **Generated artifacts**: `project/` (JSON Schema, OWL, SHACL, SQL)
- **Python datamodel**: `src/{project_name}/datamodel/` (after `make gen-project`)
- **Tests**: `tests/`
- **Documentation config**: `mkdocs.yml`

## Key Make Targets

After scaffolding, use `make` targets for common tasks:

| Target | Description |
|--------|-------------|
| `make setup` | Install project dependencies into a virtualenv |
| `make gen-project` | Generate Python dataclasses, JSON Schema, OWL, etc. from schema |
| `make test` | Run schema validation and tests |
| `make lint` | Lint the schema and generated code |
| `make gen-doc` | Generate documentation site (via mkdocs) |
| `make all` | Run gen-project + test + lint |
| `make deploy` | Deploy documentation to GitHub Pages |

### Typical First-Time Workflow

```bash
cd my-project
make setup         # Creates venv, installs deps
make gen-project   # Generates artifacts from schema
make test          # Validates everything works
```

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `copier: command not found` | copier not installed | `pip install copier` |
| `Template not found` | Network issue or wrong URL | Check internet; use `gh:linkml/linkml-project-copier` |
| `PermissionError` on post-tasks | Missing `--trust` | Add `--trust` flag |
| `make setup` fails | Python version mismatch | Ensure Python 3.9+ |
| `make gen-project` errors | Schema validation failure | Fix schema YAML first, then retry |
| Copier version conflict | Old copier version | `pip install --upgrade copier` |
| `jinja2` template error | Copier/Jinja2 incompatibility | `pip install copier>=9.0` |

## Updating an Existing Project

To pull in template updates later:

```bash
cd my-project
copier update --trust
```

This re-applies the template while preserving your changes (via git merge).
