---
id: data.phage-mobile-defense
title: Phage, Mobile Elements, and Defense
type: data_type
status: draft
summary: Host-specific phage browsers, pathogen genome views, and mobile-element signals used to reason about host range, defense, resistance, and engineered interventions.
source_projects:
  - prophage_amr_comobilization
  - t4ss_cazy_environmental_hgt
source_docs:
  - ui/config/berdl_collections_snapshot.json
  - projects/prophage_amr_comobilization/REPORT.md
  - projects/t4ss_cazy_environmental_hgt/REPORT.md
related_collections:
  - phagefoundry_acinetobacter_genome_browser
  - phagefoundry_klebsiella_genome_browser_genomedepot
  - phagefoundry_paeruginosa_genome_browser
  - phagefoundry_pviridiflava_genome_browser
  - phagefoundry_strain_modelling
  - protect_genomedepot
  - kbase_ke_pangenome
  - kescience_mgnify
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - data.index
  - topic.mobile-elements-phage
  - claim.prophage-density-predicts-amr-breadth
order: 75
---

# Phage, Mobile Elements, and Defense

## Why This Lens Exists

Tenant and database boundaries do not match how scientists or agents plan analyses. This data-type lens groups collections by the kind of evidence they provide and the questions they make easier to ask.

## Collections In This Lens

- `phagefoundry_acinetobacter_genome_browser`
- `phagefoundry_klebsiella_genome_browser_genomedepot`
- `phagefoundry_paeruginosa_genome_browser`
- `phagefoundry_pviridiflava_genome_browser`
- `phagefoundry_strain_modelling`
- `protect_genomedepot`

## Best Uses

Use this lens to find reusable source data before choosing a specific collection. It is especially useful for agents that need to identify complementary data, select join keys, or explain why a derived product is reusable across projects.

Recent project use: `prophage_amr_comobilization` uses pangenome AMR and prophage markers to make prophage burden a covariate for resistance ecology, while `t4ss_cazy_environmental_hgt` uses environmental MAGs to connect T4SS neighborhoods, CAZy HGT, and metal-resistance enrichment.

## Metrics To Watch

- Evidence traces: which projects already used these collections.
- Reuse: whether derived products exist beyond a single project.
- Under-explored combinations: collection pairs with obvious scientific value but few projects.
- Caveat load: schema gaps, identifier mismatches, sampling bias, and staging status.
- Mechanism partitioning: whether a signal is prophage, plasmid, ICE/IME, T4SS, or generic genome openness.

## Caveats

Do not treat collection co-membership as proof that a join is valid. A join recipe should name stable identifiers, filtering rules, and failure modes before it supports a claim.
