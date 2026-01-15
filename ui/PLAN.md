# BERIL Research Observatory

## Vision

**BERIL** is an AI integration layer for the **KBase BER Data Lakehouse (BERDL)** that creates resources, skills, and plugins to facilitate agent or co-scientist analysis of BERDL data. Through the BERIL Research Observatory, users can:

1. **Analyze BERDL data** using AI-assisted workflows and documented patterns
2. **Analyze their own data** in the context of BERDL reference collections
3. **Share discoveries**, lessons learned, pitfalls, and data products
4. **Explore multiple collections** across the data lakehouse
5. **Contribute** to a growing knowledge base with proper attribution

The platform is **collection-agnostic** - it supports multiple BERDL databases and encourages cross-collection analysis.

---

## BERDL Collections

The KBase BERDL Data Lakehouse contains multiple collections. BERIL will showcase these:

### Primary Research Collections

| Collection ID | Name | Scale | Key Use Cases |
|---------------|------|-------|---------------|
| `kbase_ke_pangenome` | Pangenome Collection | 293K genomes, 27K species, 1B+ genes | Comparative genomics, functional analysis, evolution, ecological adaptation |
| `kescience_fitnessbrowser` | Fitness Browser | 40+ organisms, 90+ tables | Essential genes, gene fitness, condition-specific phenotypes |
| `kbase_genomes` | Genomes Collection | 16 tables | Structural genomics, contigs, features, proteins |
| `kbase_msd_biochemistry` | ModelSEED Biochemistry | 4 tables | Metabolic modeling, reactions, compounds |
| `kbase_phenotype` | Phenotype Collection | 7 tables | Experimental phenotypes, conditions, measurements |

### Domain-Specific Collections

| Collection ID | Name | Description |
|---------------|------|-------------|
| `phagefoundry_*` | PhageFoundry Browsers | Phage genome browsers for specific hosts (Klebsiella, P. aeruginosa, Acinetobacter, P. viridiflava) |
| `enigma_coral` | ENIGMA Coral | ENIGMA project coral microbiome data |
| `planetmicrobe_planetmicrobe` | Planet Microbe | Ocean microbiome sampling and taxonomy |

### Reference Collections

| Collection ID | Name | Description |
|---------------|------|-------------|
| `kbase_uniref50/90/100` | UniRef Clusters | Protein sequence clusters at various identity thresholds |
| `kbase_uniprot_bacteria/archaea` | UniProt | UniProt protein annotations for bacteria and archaea |
| `kbase_ontology_source` | Ontologies | Ontology reference data |

---

## Information Architecture

### Site Map

```
BERIL Research Observatory
│
├── Home                         /
│   ├── Hero: What is BERIL?
│   ├── Featured Collections
│   ├── Latest Discoveries
│   └── Active Research
│
├── Collections                  /collections
│   ├── Collections Overview     /collections
│   ├── Collection Detail        /collections/{id}
│   │   ├── Overview & Philosophy
│   │   ├── Schema Browser
│   │   ├── Query Patterns
│   │   └── Related Collections
│   └── Cross-Collection Guide   /collections/cross-analysis
│
├── Projects                     /projects
│   ├── Projects List            /projects
│   ├── Project Detail           /projects/{id}
│   └── Notebook Viewer          /projects/{id}/notebooks/{name}
│
├── Knowledge                    /knowledge
│   ├── Discoveries              /knowledge/discoveries
│   ├── Pitfalls                 /knowledge/pitfalls
│   ├── Research Ideas           /knowledge/ideas
│   └── Performance Guide        /knowledge/performance
│
├── Community                    /community
│   ├── Contributors             /community/contributors
│   ├── How to Contribute        /community/contribute
│   └── Attribution Policy       /community/attribution
│
└── About                        /about
    ├── What is BERIL?           /about
    ├── What is BERDL?           /about/berdl
    ├── AI Integration           /about/ai
    └── Getting Started          /about/getting-started
```

---

## Page Specifications

### 1. Home Page (`/`)

**Purpose:** Introduce BERIL and provide entry points to all major sections.

**Hero Section:**
```
BERIL
Research Observatory

AI-powered exploration of the KBase Data Lakehouse.
Discover research findings, explore collection schemas,
and contribute to shared scientific knowledge.

[Explore Collections]  [Browse Projects]  [View Discoveries]
```

**Sections:**
1. **What is BERIL?** - Brief explanation (2-3 sentences)
2. **Featured Collections** - Cards for 4-5 primary collections with stats
3. **Latest Discoveries** - 3 discovery cards with collection tags and attribution
4. **Active Research** - 3 project cards with collection badges
5. **Quick Stats** - Total collections, discoveries, projects, contributors

---

### 2. Collections Section

#### 2.1 Collections Overview (`/collections`)

**Purpose:** Browse all available BERDL collections.

**Layout:**
- **Primary Collections** grid (large cards)
- **Domain-Specific Collections** grid (medium cards)
- **Reference Collections** list (compact)

**Collection Card:**
```
┌─────────────────────────────────┐
│  [Icon]  Pangenome Collection   │
│  kbase_ke_pangenome             │
├─────────────────────────────────┤
│  293,059 genomes                │
│  27,690 species                 │
│  14 tables                      │
├─────────────────────────────────┤
│  Comparative genomics,          │
│  functional analysis...         │
├─────────────────────────────────┤
│  [Explore Schema] [View Docs]   │
└─────────────────────────────────┘
```

#### 2.2 Collection Detail (`/collections/{collection_id}`)

**Purpose:** Deep dive into a specific collection.

**Sections:**
1. **Overview**
   - Collection name, ID, description
   - Philosophy: Why this collection exists, what questions it answers
   - Data sources and provenance
   - Scale statistics

2. **Schema Browser**
   - Left sidebar: Searchable table list with row counts
   - Main content: Table details (columns, types, relationships)
   - Sample queries with syntax highlighting
   - Foreign key relationship diagram

3. **Query Patterns**
   - Collection-specific query patterns
   - Performance tips for this collection
   - Common joins and aggregations

4. **Related Collections**
   - Collections that can be joined/combined
   - Cross-collection analysis examples

5. **Projects Using This Collection**
   - List of projects that use this collection
   - Discoveries from this collection

---

### 3. Projects Section

#### 3.1 Projects List (`/projects`)

**Purpose:** Browse all analysis projects.

**Changes from current:**
- Add **Collection badges** to each project card
- Add **Filter by collection** dropdown
- Show **cross-collection** projects prominently

#### 3.2 Project Detail (`/projects/{project_id}`)

**Purpose:** Deep dive into specific analysis.

**Changes from current:**
- Add **Collections Used** section with badges
- Add **Contributors** section with attribution
- Link to relevant collection schemas

---

### 4. Knowledge Section

**Key principle:** Knowledge spans all collections. Entries are tagged with relevant collection(s).

#### 4.1 Discoveries (`/knowledge/discoveries`)

**Changes:**
- Add **Collection filter** (show discoveries for specific collection)
- Add **Contributor attribution** to each discovery
- Group by date with collection badges

**Discovery Entry Format:**
```markdown
### [collection_tag] Discovery Title
**Contributor:** Name (Affiliation) | **Date:** 2026-01-14

Discovery content...
```

#### 4.2 Pitfalls (`/knowledge/pitfalls`)

**Changes:**
- Add **Collection filter** (some pitfalls are collection-specific, some are general)
- Tag each pitfall with applicable collection(s) or "General BERDL"

#### 4.3 Research Ideas (`/knowledge/ideas`)

**Changes:**
- Add **Collection tags** to each idea
- Highlight **cross-collection** ideas
- Show dependencies on other collections

---

### 5. Community Section (New)

#### 5.1 Contributors (`/community/contributors`)

**Purpose:** Recognize people who contribute discoveries, projects, and improvements.

**Content:**
- List of contributors with:
  - Name, affiliation (optional)
  - ORCID, GitHub (optional)
  - Number of discoveries, projects, pitfalls contributed
  - Link to their contributions

#### 5.2 How to Contribute (`/community/contribute`)

**Purpose:** Guide for adding discoveries, projects, and pitfalls.

**Content:**
- How to add a discovery
- How to add a project
- How to document a pitfall
- Attribution format
- Git workflow

#### 5.3 Attribution Policy (`/community/attribution`)

**Purpose:** Explain how credit works.

**Content:**
- How contributors are credited
- Co-authorship on discoveries
- Citation guidelines

---

### 6. About Section

#### 6.1 What is BERIL? (`/about`)

**Content:**
- BERIL as AI integration layer
- Goals: facilitate analysis, share knowledge, enable collaboration
- Relationship to KBase and BERDL

#### 6.2 What is BERDL? (`/about/berdl`)

**Content:**
- Berkeley Research Data Lake
- Delta Lakehouse architecture
- Available collections
- Access methods (Spark SQL, REST API, JupyterHub)

#### 6.3 AI Integration (`/about/ai`)

**Content:**
- Skills, plugins, agents
- MCP integration
- How to use BERIL with AI assistants
- Available tools and capabilities

#### 6.4 Getting Started (`/about/getting-started`)

**Content:**
- BERDL access setup (auth token, JupyterHub)
- Repository structure
- Starting a new project
- Using the schema browser
- JupyterHub workflow

---

## Data Model Updates

### New Models

```python
@dataclass
class Collection:
    """A BERDL data collection."""
    id: str                      # "kbase_ke_pangenome"
    name: str                    # "Pangenome Collection"
    description: str
    philosophy: str              # Why this collection exists
    category: str                # "primary", "domain", "reference"
    scale_stats: dict            # {genomes: 293059, species: 27000, ...}
    table_count: int
    data_sources: list[str]      # ["GTDB r214", "eggNOG v6", ...]
    related_collections: list[str]
    icon: str                    # Icon identifier or emoji

@dataclass
class Contributor:
    """A person who contributes to BERIL."""
    id: str                      # Slug from name
    name: str
    affiliation: str | None
    orcid: str | None
    github: str | None
    discoveries: list[str]       # Discovery IDs
    projects: list[str]          # Project IDs
```

### Updated Models

```python
@dataclass
class Discovery:
    # Existing fields...
    collections: list[str]       # NEW: Collection IDs this applies to
    contributors: list[str]      # NEW: Contributor IDs

@dataclass
class Project:
    # Existing fields...
    collections: list[str]       # NEW: Collection IDs used

@dataclass
class Pitfall:
    # Existing fields...
    collection: str | None       # NEW: Specific collection or None for general

@dataclass
class ResearchIdea:
    # Existing fields...
    collections: list[str]       # NEW: Collection IDs involved
```

---

## Collections Configuration

Collections will be defined in a configuration file: `ui/config/collections.yaml`

```yaml
collections:
  - id: kbase_ke_pangenome
    name: Pangenome Collection
    category: primary
    description: >
      Pangenome data for 293,059 genomes across 27,690 microbial species
      derived from GTDB r214.
    philosophy: >
      Enable comparative genomics at scale. Understand core vs accessory
      genome content, functional distributions, and evolutionary patterns
      across bacterial and archaeal species.
    data_sources:
      - GTDB r214
      - eggNOG v6
      - GapMind
      - AlphaEarth
    scale_stats:
      genomes: 293059
      species: 27690
      genes: "1B+"
      tables: 14
    related_collections:
      - kbase_genomes
      - kbase_msd_biochemistry
    icon: "🧬"

  - id: kescience_fitnessbrowser
    name: Fitness Browser
    category: primary
    description: >
      Gene fitness data from transposon mutant experiments across 40+
      bacterial organisms.
    philosophy: >
      Identify essential genes and condition-specific fitness effects.
      Connect genotype to phenotype through systematic mutagenesis.
    data_sources:
      - RB-TnSeq experiments
      - KEGG
      - MetaCyc
      - SEED
    scale_stats:
      organisms: 40
      experiments: 1000+
      tables: 90
    related_collections:
      - kbase_ke_pangenome
      - kbase_msd_biochemistry
    icon: "📊"

  # ... more collections
```

---

## Markdown Format Updates

### Discovery Attribution Format

```markdown
### [kbase_ke_pangenome] Universal functional partitioning in bacterial pangenomes
**Contributor:** Jane Smith (LBNL) | **ORCID:** 0000-0001-2345-6789

Analysis of 32 species across 9 phyla reveals...
```

### Project Collections Format

In project README.md, add a `## Collections` section:

```markdown
## Collections Used

- **kbase_ke_pangenome**: Gene clusters, functional annotations
- **kbase_msd_biochemistry**: Reaction mappings

## Contributors

- Jane Smith (LBNL) - Analysis design, notebooks
- John Doe (JGI) - Data extraction
```

---

## Implementation Phases

### Phase 1: BERIL Rebranding (1 week)
- Update all templates with BERIL branding
- Update home page messaging and hero
- Rename "Data" to "Collections"
- Update navigation
- Update About section

### Phase 2: Multi-Collection Architecture (2 weeks)
- Create collections.yaml configuration
- Add Collection model and parser
- Create collections overview page
- Create collection detail pages with schema browsers
- Add collection badges to projects and discoveries
- Add collection filters to knowledge pages

### Phase 3: Attribution System (1 week)
- Add Contributor model
- Parse contributors from markdown
- Create community/contributors page
- Add attribution to discovery and project templates
- Create "How to Contribute" guide

### Phase 4: Cross-Collection Features (1 week)
- Add cross-collection analysis guide
- Highlight cross-collection projects
- Add related collections to collection detail
- Create cross-collection research ideas section

---

## File Changes Required

### New Files
- `ui/config/collections.yaml` - Collection definitions
- `ui/app/templates/collections/` - Collection templates
  - `overview.html` - Collections grid
  - `detail.html` - Collection detail with schema
- `ui/app/templates/community/` - Community templates
  - `contributors.html` - Contributors list
  - `contribute.html` - How to contribute guide
  - `attribution.html` - Attribution policy

### Modified Files
- `ui/app/main.py` - New routes for collections, community
- `ui/app/models.py` - Add Collection, Contributor models
- `ui/app/parser.py` - Parse collections, contributors, collection tags
- `ui/app/templates/base.html` - Update nav, branding
- `ui/app/templates/home.html` - Complete redesign for BERIL
- `ui/app/templates/projects/*.html` - Add collection badges
- `ui/app/templates/knowledge/*.html` - Add collection filters
- `ui/app/static/css/main.css` - Collection-specific styling

### Renamed/Removed
- `ui/app/templates/data/` → Merge into `collections/`

---

## Success Metrics

1. **All 8+ collections browsable** with schemas and documentation
2. **Cross-collection relationships** clearly shown
3. **Every discovery and project** tagged with collections used
4. **Contributors recognized** on community page
5. **New contributor onboarding** documented in /community/contribute
6. **Collection filters** work on all knowledge pages
7. **Collection-specific pitfalls** distinguished from general ones

---

## Questions to Resolve

1. **Schema for non-pangenome collections**: Need to document schemas for fitness browser, biochemistry, etc.
2. **Collection philosophy**: Need input on the "why" for each collection
3. **Initial contributors**: Who should be listed as initial contributors?
4. **Cross-collection examples**: What are good examples of cross-collection analysis to highlight?

---

## Frontend Design (Unchanged)

The "Research Observatory" dark theme design system from the previous plan remains in effect. See the "Frontend Design" section below for typography, colors, and styling details.

---

<!-- Previous frontend design content follows -->

## Frontend Design

### Design Direction: "Research Observatory"

**Concept:** A dark-themed interface that positions the user as a researcher peering into a vast dataset. The UI recedes into the background while data and discoveries take center stage with high contrast. Think: mission control for genomic exploration.

**What makes it memorable:** The contrast between the dark, minimal chrome and the vibrant data visualizations. When you see a heatmap or gene distribution chart, it should feel like looking at a star field through a telescope.

**Tone:** Refined, precise, serious—but not cold. The interface respects the user's expertise and doesn't oversimplify. Generous whitespace (or rather, "darkspace") lets the science breathe.

**Key principles:**
- **Navigation stays predictable:** Header, sidebar, and wayfinding use conventional patterns. Users never hunt for how to get around.
- **Content areas get creative:** Within the predictable frame, content layouts can use asymmetry, overlapping elements, and unexpected compositions.
- **Data is the hero:** The UI is a stage; the research findings are the performance.

---

### Typography

**Display/Headlines:** [Newsreader](https://fonts.google.com/specimen/Newsreader) — A contemporary serif with editorial gravitas. Designed for long-form reading but distinctive enough for headlines. Has optical sizing for crisp rendering at all scales.

**Body/UI:** [DM Sans](https://fonts.google.com/specimen/DM Sans) — A geometric sans-serif with subtle warmth. Clean enough for UI elements, readable for body text. Pairs well with Newsreader's curves.

**Code/Data:** [JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono) — Purpose-built for code readability with ligatures for common operators. Slightly wider than typical monospace fonts, improving scanability for SQL and data tables.

---

### Color System (Dark Theme)

```css
/* static/css/main.css */

:root {
  /* Typography */
  --font-display: 'Newsreader', Georgia, serif;
  --font-body: 'DM Sans', -apple-system, system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Surface colors - Dark theme */
  --surface-base: #0d1117;        /* GitHub-dark inspired base */
  --surface-raised: #161b22;      /* Cards, panels */
  --surface-overlay: #21262d;     /* Dropdowns, modals */
  --surface-border: #30363d;      /* Subtle borders */

  /* Text colors */
  --text-primary: #e6edf3;        /* Primary text - high contrast */
  --text-secondary: #8b949e;      /* Secondary, muted text */
  --text-tertiary: #6e7681;       /* Timestamps, metadata */
  --text-link: #58a6ff;           /* Links */

  /* Accent - Cyan/Electric Blue (scientific precision) */
  --accent-primary: #39d4e6;      /* Primary accent - vibrant cyan */
  --accent-primary-muted: #1a6b75; /* Hover states, backgrounds */
  --accent-secondary: #f0883e;    /* Secondary accent - warm amber for highlights */

  /* Data visualization palette */
  --viz-core: #39d4e6;            /* Core genes - cyan */
  --viz-auxiliary: #a371f7;       /* Auxiliary genes - purple */
  --viz-novel: #f0883e;           /* Novel genes - amber */
  --viz-positive: #3fb950;        /* Enrichment, success */
  --viz-negative: #f85149;        /* Depletion, errors */

  /* Status colors (adjusted for dark theme) */
  --status-completed: #3fb950;
  --status-in-progress: #58a6ff;
  --status-proposed: #8b949e;

  /* Priority colors */
  --priority-high: #f85149;
  --priority-medium: #f0883e;
  --priority-low: #3fb950;

  /* Spacing scale */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;
  --space-16: 64px;

  /* Border radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
}
```

---

### Collection-Specific Styling (New)

```css
/* Collection category colors */
--collection-primary: #39d4e6;     /* Primary research collections */
--collection-domain: #a371f7;      /* Domain-specific collections */
--collection-reference: #8b949e;   /* Reference collections */

/* Collection badges */
.collection-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: 0.75rem;
  font-weight: 600;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  background: var(--accent-primary-bg);
  color: var(--accent-primary);
}

.collection-badge.primary {
  background: rgba(57, 212, 230, 0.15);
  color: #39d4e6;
}

.collection-badge.domain {
  background: rgba(163, 113, 247, 0.15);
  color: #a371f7;
}

.collection-badge.reference {
  background: rgba(139, 148, 158, 0.15);
  color: #8b949e;
}
```

---

### Animation Strategy (Future Enhancement)

Animations are intentionally deferred to a later phase. For a scientific audience, motion can feel performative or distracting if not executed with restraint.

**Potential future additions (post-MVP, with A/B testing):**
- Subtle fade-in for page content (150-200ms)
- Staggered reveal for card grids
- Smooth scroll-linked progress indicators
- Hover state transitions (already included in MVP: 150ms ease)

**MVP includes only:**
- Basic CSS transitions on hover states (color, border, shadow changes)
- No page transitions, no scroll animations, no loading sequences
