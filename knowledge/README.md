# Layer 3: Semantic Knowledge Graph

The knowledge graph captures biological entities, their relationships, hypothesis lifecycle, and research timeline across all BERIL Research Observatory projects. It enables cross-project discovery and research continuity across sessions.

## Architecture

```
knowledge/
  entities/
    organisms.yaml      # Biological organisms with NCBI taxonomy IDs
    genes.yaml           # Genes and gene groups with KEGG KO IDs
    pathways.yaml        # Metabolic and functional pathways with KEGG IDs
    methods.yaml         # Analytical and experimental methods
    concepts.yaml        # Scientific concepts and theoretical frameworks
  relations.yaml         # Typed, evidence-backed edges between entities
  hypotheses.yaml        # Hypothesis lifecycle tracking (proposed -> validated/rejected)
  timeline.yaml          # Chronological research events
  schema/
    research_graph.yaml  # LinkML schema governing all data
  README.md              # This file
```

## How It Fits

```
Layer 1 (per-project):   provenance.yaml           <- Project-level metadata
Layer 2 (global index):  docs/project_registry.yaml <- Searchable registry
                         docs/figure_catalog.yaml
                         docs/findings_digest.md
Layer 3 (semantic):      knowledge/                 <- THIS LAYER
```

- **Layer 1** answers: "What data/methods/references does project X use?"
- **Layer 2** answers: "Which projects studied topic Y?"
- **Layer 3** answers: "Which organisms share essential gene patterns?", "What pathways connect project A's findings to project B's?", "How has our understanding of core genome function evolved?"

## Entity Types

| Type | File | External IDs | Count |
|------|------|-------------|-------|
| Organism | `entities/organisms.yaml` | NCBI Taxonomy | 20 |
| Gene | `entities/genes.yaml` | KEGG KO, UniProt | 16 |
| Pathway | `entities/pathways.yaml` | KEGG Pathway | 11 |
| Method | `entities/methods.yaml` | — | 15 |
| Concept | `entities/concepts.yaml` | — | 21 |

## Adding Entities

Add a new entity to the appropriate file under `entities/`. Follow the existing format:

```yaml
- id: org_neworganism           # Prefix: org_, gene_, path_, meth_, conc_
  name: Full Species Name
  ncbi_taxid: 12345             # External ID (type-specific)
  projects: [project_id]        # Which projects reference this entity
  role: "Brief description"     # What role it plays
```

Entity IDs use prefixes: `org_`, `gene_`, `path_`, `meth_`, `conc_`.

## Adding Relations

Add evidence-backed edges to `relations.yaml`:

```yaml
- subject: org_ecoli
  predicate: has_essential_gene_data    # See schema for valid predicates
  object: conc_essential_genes
  evidence_project: essential_genome    # Must reference a real project
  confidence: high                      # high, medium, low, preliminary
  note: "Brief evidence description"
```

## Hypothesis Lifecycle

Hypotheses track the evolution of scientific understanding:

```
proposed -> refined -> testing -> validated
                                  rejected
                                  merged
                                  superseded
```

Each hypothesis has:
- **statement**: The claim being tested
- **status**: Current lifecycle state
- **evidence**: Supporting and contradicting evidence with project provenance
- **evolution**: Chronological state changes
- **parent/spawned**: Lineage connections to other hypotheses

## Querying the Knowledge Graph

Use the `/knowledge` skill:

```
/knowledge entities organism          # List all organisms
/knowledge connections org_adp1       # Find all relations for ADP1
/knowledge hypotheses validated       # List validated hypotheses
/knowledge gaps                       # Find unexplored entity combinations
/knowledge timeline                   # Show research evolution
```

## Updating After New Projects

When `/synthesize` completes a project, it automatically:
1. Registers new entities discovered
2. Adds/updates relations with evidence
3. Creates/updates hypotheses
4. Appends timeline events

## Schema Validation

The LinkML schema at `schema/research_graph.yaml` governs all data files. To validate:

```bash
# Generate JSON Schema (one-time)
gen-json-schema knowledge/schema/research_graph.yaml > knowledge/schema/research_graph.json

# Validate entity files
linkml-validate -s knowledge/schema/research_graph.yaml knowledge/entities/*.yaml
```
