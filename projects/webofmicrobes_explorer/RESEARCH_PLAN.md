# Research Plan: Web of Microbes Data Explorer

## Research Question
What does the Web of Microbes exometabolomics collection contain, and how effectively can it be linked to Fitness Browser fitness data and pangenome-predicted metabolic capabilities?

## Hypothesis
- **H0**: WoM metabolite profiles do not meaningfully connect to existing BERDL collections (low organism overlap, poor metabolite-to-pathway mapping)
- **H1**: WoM provides actionable cross-links — organisms overlap with the Fitness Browser, metabolites map to GapMind pathways and ModelSEED reactions, and exometabolomic profiles complement gene-level fitness data

## Literature Context
- Kosina et al. 2018 (BMC Microbiology) introduced WoM as the first exometabolomics repository
- Douglas 2020 (Phil Trans R Soc B) reviewed the microbial exometabolome as an ecological resource
- The BERDL copy is the 2018 archived snapshot (37 organisms, 589 metabolites, 10 environments, 10,744 observations)
- WoM data includes ENIGMA groundwater isolates (FW/GW-series) which may overlap with Fitness Browser organisms

## Query Strategy

### Tables Required
| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `kescience_webofmicrobes.observation` | Core data: metabolite actions | 10,744 | Join to organism/compound/environment |
| `kescience_webofmicrobes.compound` | Metabolite identities | 589 | Full scan (small) |
| `kescience_webofmicrobes.organism` | Organism names | 37 | Full scan |
| `kescience_webofmicrobes.environment` | Growth conditions | 10 | Full scan |
| `kescience_webofmicrobes.project` | Publication references | 5 | Full scan |
| `kescience_fitnessbrowser.organism` | FB organism IDs | ~48 | Full scan |
| `kescience_fitnessbrowser.gene` | Gene annotations | 228K | Filter by matched orgId |
| `kbase_ke_pangenome.gapmind_pathways` | Pathway predictions | 305M | Filter by matched genome |
| `kbase_msd_biochemistry.compound` | ModelSEED compounds | ~46K | Name/formula matching |

### Performance Plan
- **Tier**: REST API for small WoM tables; Spark for FB/pangenome joins
- **Estimated complexity**: Low-moderate (WoM is tiny; cross-collection joins are the only challenge)
- **Known pitfalls**: FB columns are all strings (CAST needed); GapMind requires MAX aggregation per genome-pathway pair

## Analysis Plan

### Notebook 1: Database Overview & Fitness Browser Overlap
- **Goal**: Characterize WoM contents; identify FB organism matches
- Inventory: organisms, metabolites, environments, projects, actions
- Categorize metabolites (amino acids, nucleotides, sugars, organic acids, unknowns)
- Match WoM organisms to FB organisms by strain name
- For matched organisms: compare metabolite profiles to FB condition coverage
- **Expected output**: `data/wom_summary.csv`, `data/fb_overlap.csv`, summary statistics

### Notebook 2: Cross-Collection Linking
- **Goal**: Map WoM metabolites to GapMind pathways and ModelSEED compounds
- Match WoM compound names to ModelSEED compound names/formulas
- For FB-overlapping organisms: check which consumed metabolites correspond to GapMind pathway substrates
- Assess: what fraction of WoM metabolites have pathway-level or reaction-level annotations in BERDL?
- **Expected output**: `data/metabolite_links.csv`, `data/pathway_overlap.csv`

### Notebook 3: Metabolite Interaction Profiles (if warranted)
- **Goal**: Visualize organism × metabolite interaction patterns
- Heatmap of organism × metabolite actions across environments
- Identify universally consumed/produced metabolites
- Compare metabolic profiles between organism groups (Pseudomonas spp. vs others)
- **Expected output**: `figures/metabolite_heatmap.png`, `figures/organism_profiles.png`

## Expected Outcomes
- **If H1 supported**: WoM provides a validated exometabolomics layer that links metabolite measurements to gene fitness and pathway predictions — enabling a future "metabolite dependencies predict gene essentiality" project
- **If H0 not rejected**: WoM data is too small, too poorly linked, or too dated to add value — document the gaps and identify what additional data (e.g., newer WoM from GNPS2, or Northen lab datasets) would be needed
- **Potential confounders**: 2018 snapshot may be outdated; organism name matching may have ambiguities; R2A medium conditions may not match FB experimental conditions

## Revision History
- **v1** (2026-02-23): Initial plan — characterize WoM and assess cross-collection utility

## Authors
Paramvir S. Dehal (https://orcid.org/0000-0001-5810-2497), Lawrence Berkeley National Laboratory
