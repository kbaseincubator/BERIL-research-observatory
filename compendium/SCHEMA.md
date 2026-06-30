# Compendium Artifact Contract

This is the v1 contract for the lightweight topic-MOC wiki. It is intentionally
not LinkML, Biolink, KGX, or an ontology schema. Runtime validation lives in
`src/compendium/validate.py` and tests.

## Statement Cards

One project card file contains project metadata plus statement cards:

```yaml
project:
  id: adp1_deletion_phenotypes
  title: ADP1 deletion phenotypes
statements:
  - id: stmt:adp1-condition-independence-finding
    kind: finding
    text: ADP1 carbon-source growth assays provide several independent phenotypic dimensions.
    confidence: high
    topics:
      - topic:adp1-carbon-fitness
    entities:
      - entity:adp1
    links:
      supports:
        - stmt:adp1-continuum-claim
      contradicts: []
      refines: []
    evidence:
      - source_project: adp1_deletion_phenotypes
        source_doc: REPORT.md
        source_section: Results
        quote: The low pairwise correlations (median Pearson r = 0.25, maximum r = 0.58) demonstrate that each carbon source imposes a largely independent set of gene requirements.
```

Required fields:

- `project.id`
- `statements[].id`
- `statements[].kind`: `finding`, `claim`, `caveat`, or `opportunity`
- `statements[].text`
- `statements[].confidence`: `low`, `medium`, or `high`
- `statements[].topics`
- `statements[].entities`
- `statements[].evidence[].source_project`
- `statements[].evidence[].source_doc`
- `statements[].evidence[].quote`

Optional fields:

- `project.title`
- `statements[].links.supports`
- `statements[].links.contradicts`
- `statements[].links.refines`
- `statements[].evidence[].source_section`
- `statements[].evidence[].notebook`
- `statements[].evidence[].figure`

## Registry

The registry maps raw per-project topic and entity slugs onto stable canonical
keys:

```yaml
topics:
  adp1-carbon-fitness:
    label: ADP1 Carbon Fitness
    definition: Condition-dependent gene fitness and essentiality of ADP1 across carbon sources.
    aliases:
      - topic:adp1-carbon-fitness
entities:
  adp1:
    label: Acinetobacter baylyi ADP1
    kind: organism
    definition: A naturally competent soil bacterium used as a model system for metabolism and genetics.
    aliases:
      - entity:adp1
    url: https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=62977
```

Required fields:

- `topics.<key>.label`
- `topics.<key>.definition`
- `topics.<key>.aliases`
- `entities.<key>.label`
- `entities.<key>.kind`
- `entities.<key>.definition`
- `entities.<key>.aliases`

Optional fields:

- `topics.<key>.url`
- `entities.<key>.url`

Entity `kind` should stay broad: `organism`, `compound`, `gene_or_pathway`,
`method`, `dataset`, `place`, or `concept`.

## Page Context

Page contexts are deterministic writer briefs. They are not public graph exports.

```json
{
  "page": {"id": "topic:adp1-carbon-fitness", "type": "topic"},
  "statements": [],
  "projects": [],
  "topics": [],
  "entities": [],
  "authors": [],
  "data_collections": [],
  "adjacent_pages": [],
  "narrative": {"lead": "", "section_plan": []},
  "allowed_citations": []
}
```

The LLM writer uses this context to produce synthesized Markdown pages with
plain introductions, sections, cross-links, and caveats/open directions, placing
each `[stmt:id; project]` citation inline at the claim it supports. At publish time
`page-artifact` rewrites those inline tokens into numbered `[N]` markers and appends a
generated `## References` list that links to the per-project pages.
