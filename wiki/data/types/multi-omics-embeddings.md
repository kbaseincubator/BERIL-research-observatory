---
id: data.multi-omics-embeddings
title: Multi-Omics, Embeddings, and Molecular Profiles
type: data_type
status: draft
summary: Metabolomics, proteomics, trait profiles, embeddings, and other matrix-style summaries that create reusable sample or organism representations.
source_projects:
  []
source_docs:
  - docs/collections.md
  - ui/config/berdl_collections_snapshot.json
related_collections:
  - nmdc_arkin
  - kbase_ke_pangenome
  - kescience_webofmicrobes
  - enigma_coral
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-29
related_pages:
  - data.index
order: 74
---

# Multi-Omics, Embeddings, and Molecular Profiles

## Why This Lens Exists

Tenant and database boundaries do not match how scientists or agents plan analyses. This data-type lens groups collections by the kind of evidence they provide and the questions they make easier to ask.

## Collections In This Lens

- `nmdc_arkin`
- `kbase_ke_pangenome`
- `kescience_webofmicrobes`
- `enigma_coral`

## Best Uses

Use this lens to find reusable source data before choosing a specific collection. It is especially useful for agents that need to identify complementary data, select join keys, or explain why a derived product is reusable across projects.

## Metrics To Watch

- Evidence traces: which projects already used these collections.
- Reuse: whether derived products exist beyond a single project.
- Under-explored combinations: collection pairs with obvious scientific value but few projects.
- Caveat load: schema gaps, identifier mismatches, sampling bias, and staging status.

## Caveats

Do not treat collection co-membership as proof that a join is valid. A join recipe should name stable identifiers, filtering rules, and failure modes before it supports a claim.
