---
id: data.phenotypes-assays
title: Experimental Phenotypes, Traits, and Assays
type: data_type
status: draft
summary: Measured organism and gene behavior across laboratory conditions, including mutant fitness, growth phenotypes, utilization traits, and exometabolomic observations.
source_projects:
  []
source_docs:
  - ui/config/berdl_collections_snapshot.json
  - ui/config/berdl_collections_snapshot.json
related_collections:
  - kescience_fitnessbrowser
  - kbase_phenotype
  - kescience_bacdive
  - kescience_webofmicrobes
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-29
related_pages:
  - data.index
order: 71
---

# Experimental Phenotypes, Traits, and Assays

## Why This Lens Exists

Tenant and database boundaries do not match how scientists or agents plan analyses. This data-type lens groups collections by the kind of evidence they provide and the questions they make easier to ask.

## Collections In This Lens

- `kescience_fitnessbrowser`
- `kbase_phenotype`
- `kescience_bacdive`
- `kescience_webofmicrobes`

## Best Uses

Use this lens to find reusable source data before choosing a specific collection. It is especially useful for agents that need to identify complementary data, select join keys, or explain why a derived product is reusable across projects.

## Metrics To Watch

- Evidence traces: which projects already used these collections.
- Reuse: whether derived products exist beyond a single project.
- Under-explored combinations: collection pairs with obvious scientific value but few projects.
- Caveat load: schema gaps, identifier mismatches, sampling bias, and staging status.

## Caveats

Do not treat collection co-membership as proof that a join is valid. A join recipe should name stable identifiers, filtering rules, and failure modes before it supports a claim.
