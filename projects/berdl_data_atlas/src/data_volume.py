"""Per-entity-class volume inventory for BERDL.

Where the rest of the atlas measures *breadth* (how many tables, how many
cross-tenant bridges), this module measures *depth*: how many genomes,
genes, proteins, samples, measurements, etc. actually live in the
lakehouse.

Each entry in ENTITIES is `(entity_class, table, count_col, label)`:
  - entity_class: a coarse category (Genomes, Proteins, Fitness, ...)
  - table:        `<db>.<table>` identifier
  - count_col:    None for COUNT(*); a column name for COUNT(DISTINCT col)
  - label:        human-readable description for the figure
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VolumeRow:
    entity_class: str       # "Genomes", "Proteins", etc.
    table:        str       # "kbase_ke_pangenome.genome"
    count_col:    str | None  # None = COUNT(*); else COUNT(DISTINCT col)
    label:        str       # "KBase pangenome genomes (distinct)"


ENTITIES: list[VolumeRow] = [
    # ---- Genomes (assemblies / MAGs / host genomes / depots) ----
    VolumeRow("Genomes",              "kbase_ke_pangenome.genome",                                        "genome_id",  "KBase ke_pangenome genomes"),
    VolumeRow("Genomes",              "kbase_ke_pangenome.gtdb_metadata",                                  None,        "KBase GTDB-r214 genome metadata"),
    VolumeRow("Genomes",              "refdata_jgi_gem_mags.genome_metadata",                              None,        "JGI GEM-MAGs (refdata)"),
    VolumeRow("Genomes",              "refdata_spire.genome_metadata",                                     None,        "SPIRE MAGs (refdata)"),
    VolumeRow("Genomes",              "enigma_genome_depot_enigma.browser_genome",                         None,        "ENIGMA genome depot"),
    VolumeRow("Genomes",              "protect_genomedepot.browser_genome",                                None,        "PROTECT genome depot (MIND)"),
    VolumeRow("Genomes",              "phagefoundry_acinetobacter_genome_browser.browser_genome",          None,        "PhageFoundry Acinetobacter genomes"),
    VolumeRow("Genomes",              "phagefoundry_klebsiella_genome_browser_genomedepot.browser_genome", None,        "PhageFoundry Klebsiella genomes"),
    VolumeRow("Genomes",              "phagefoundry_paeruginosa_genome_browser.browser_genome",            None,        "PhageFoundry P. aeruginosa genomes"),
    VolumeRow("Genomes",              "phagefoundry_pviridiflava_genome_browser.browser_genome",           None,        "PhageFoundry P. viridiflava genomes"),
    VolumeRow("Genomes",              "phagefoundry_ecoliphagesgenomedepot.browser_genome",                None,        "PhageFoundry E. coli genomes"),
    VolumeRow("Genomes",              "enigma_coral.sdt_genome",                                           None,        "ENIGMA SDT genomes (canonical)"),

    # ---- Species-level pangenomes / clades ----
    VolumeRow("Species pangenomes",   "kbase_ke_pangenome.gtdb_species_clade",                             None,        "KBase species pangenomes (GTDB clades)"),
    VolumeRow("Species pangenomes",   "kbase_ke_pangenome.pangenome",                                      None,        "KBase computed pangenome records"),

    # ---- Gene clusters / orthogroups ----
    VolumeRow("Gene clusters",        "kbase_ke_pangenome.gene_cluster",                                   None,        "KBase pangenome gene clusters"),

    # ---- Genes (features) ----
    VolumeRow("Genes (features)",     "kbase_ke_pangenome.gene",                                           None,        "KBase pangenome genes"),
    VolumeRow("Genes (features)",     "kescience_fitnessbrowser.gene",                                     None,        "FitnessBrowser genes"),
    VolumeRow("Genes (features)",     "enigma_genome_depot_enigma.browser_gene",                           None,        "ENIGMA genome-depot genes"),
    VolumeRow("Genes (features)",     "protect_genomedepot.browser_gene",                                  None,        "PROTECT genome-depot genes"),
    VolumeRow("Genes (features)",     "phagefoundry_acinetobacter_genome_browser.browser_gene",            None,        "PhageFoundry Acinetobacter genes"),

    # ---- Proteins ----
    VolumeRow("Proteins",             "refdata_uniprot.protein",                                           None,        "UniProt proteins (refdata)"),
    VolumeRow("Proteins",             "refdata_uniref50_2026_01.cluster",                                  None,        "UniRef50 clusters"),
    VolumeRow("Proteins",             "refdata_uniref90_2026_01.cluster",                                  None,        "UniRef90 clusters"),
    VolumeRow("Proteins",             "refdata_uniref100_2026_01.cluster",                                 None,        "UniRef100 clusters"),
    VolumeRow("Proteins",             "enigma_genome_depot_enigma.browser_protein",                        None,        "ENIGMA proteins"),
    VolumeRow("Proteins",             "protect_genomedepot.browser_protein",                               None,        "PROTECT proteins"),

    # ---- Structural biology ----
    VolumeRow("AlphaFold models",     "kescience_alphafold.alphafold_entries",                             None,        "AlphaFold predicted structures"),
    VolumeRow("PDB entries",          "refdata_pdb.pdb_entries",                                           None,        "PDB experimental structures (refdata)"),
    VolumeRow("PDB entries",          "kescience_pdb.pdb_entries",                                         None,        "PDB experimental structures (kescience)"),

    # ---- Fitness data ----
    VolumeRow("Fitness data",         "kescience_fitnessbrowser.genefitness",                              None,        "FitnessBrowser per-gene fitness rows"),
    VolumeRow("Fitness data",         "kescience_fitnessbrowser.experiment",                               None,        "FitnessBrowser fitness experiments"),

    # ---- Organismal phenotype / growth ----
    VolumeRow("Organismal phenotype", "kescience_bacdive.strain",                                          None,        "BacDive strain phenotype profiles"),
    VolumeRow("Organismal phenotype", "kescience_webofmicrobes.observation",                               None,        "Web of Microbes growth observations"),
    VolumeRow("Organismal phenotype", "kescience_webofmicrobes.organism",                                  None,        "Web of Microbes organisms"),
    VolumeRow("Organismal phenotype", "globalusers_carbon_source_phenotypes.phenotype_data_table",         None,        "Carbon-source phenotype measurements"),

    # ---- Field samples ----
    VolumeRow("Field samples",        "nmdc_metadata.biosample_set",                                       None,        "NMDC biosamples"),
    VolumeRow("Field samples",        "enigma_coral.sdt_sample",                                           None,        "ENIGMA SDT samples"),
    VolumeRow("Field samples",        "enigma_coral.ddt_ndarray",                                          None,        "ENIGMA DDT measurement datasets"),
    VolumeRow("Field samples",        "planetmicrobe_planetmicrobe.sample",                                None,        "Planet Microbe samples"),
    VolumeRow("Field samples",        "netl_pw_dna.dna_metadata",                                          None,        "NETL produced-water DNA samples"),
    VolumeRow("Field samples",        "usgs_produced_waters.usgspwdb_c",                                   None,        "USGS produced waters (curated)"),
    VolumeRow("Field samples",        "usgs_produced_waters.usgspwdb_n",                                   None,        "USGS produced waters (national)"),

    # ---- Metagenomic profiles ----
    VolumeRow("Metagenome profiles",  "nmdc_arkin.kraken_gold",                                            None,        "NMDC kraken taxonomic profiles"),
    VolumeRow("Metagenome profiles",  "nmdc_arkin.gottcha_gold",                                           None,        "NMDC gottcha taxonomic profiles"),
    VolumeRow("Metatranscriptomes",   "nmdc_arkin.metatranscriptomics_gold",                               None,        "NMDC metatranscriptomic abundance"),

    # ---- Mass spectrometry / metabolomics ----
    VolumeRow("Mass spec features",   "nmdc_arkin.nom_gold",                                               None,        "NMDC NOM mass spec assignments"),
    VolumeRow("Mass spec features",   "nmdc_arkin.nom_matrix_optimized",                                   None,        "NMDC NOM matrix (samples × m/z)"),

    # ---- 16S / ASV / OTU ----
    VolumeRow("16S / ASV / OTU",      "arkinlab_microbeatlas.otu_counts_long",                             None,        "MicrobeAtlas OTU counts (sample × OTU)"),
    VolumeRow("16S / ASV / OTU",      "arkinlab_microbeatlas.otu_metadata",                                None,        "MicrobeAtlas OTUs (distinct)"),
    VolumeRow("16S / ASV / OTU",      "arkinlab_microbeatlas.sample_metadata",                             None,        "MicrobeAtlas samples (16S)"),
    VolumeRow("16S / ASV / OTU",      "enigma_coral.sdt_asv",                                              None,        "ENIGMA SDT ASVs"),

    # ---- Environmental embeddings ----
    VolumeRow("Env embeddings",       "kbase_ke_pangenome.alphaearth_embeddings_all_years",                None,        "AlphaEarth env embeddings (KBase)"),

    # ---- ML / trait embeddings ----
    VolumeRow("Trait / ML embeddings","nmdc_arkin.embeddings_v1",                                          None,        "NMDC unified embeddings (v1)"),
    VolumeRow("Trait / ML embeddings","nmdc_arkin.trait_features",                                         None,        "NMDC organism trait features"),

    # ---- Phages / viruses / MGE ----
    VolumeRow("Phages / MGE",         "refdata_jgi_virus.imgvr_sequence_info",                             None,        "IMG/VR viral sequences"),
    VolumeRow("Phages / MGE",         "refdata_jgi_virus.metavr_main",                                     None,        "MetaVR viral catalog"),
    VolumeRow("Phages / MGE",         "phagefoundry_strain_modelling.strainmodelling_genome",              None,        "PhageFoundry strain models (genomes)"),
    VolumeRow("Phages / MGE",         "phagefoundry_strain_modelling.strainmodelling_gene",                None,        "PhageFoundry strain-model genes"),

    # ---- Reactions / biochemistry ----
    VolumeRow("Reactions",            "kbase_msd_biochemistry.reaction",                                   None,        "ModelSEED reactions (KBase MSD)"),
    VolumeRow("Reactions",            "nmdc_arkin.rhea_reactions",                                         None,        "Rhea reactions (NMDC integrated)"),
    VolumeRow("Compounds",            "kbase_msd_biochemistry.molecule",                                   None,        "ModelSEED compounds/molecules"),

    # ---- Annotations / ontology terms ----
    VolumeRow("Ontology terms",       "nmdc_arkin.go_terms",                                               None,        "GO terms (NMDC integrated)"),
    VolumeRow("Ontology terms",       "nmdc_arkin.ec_terms",                                               None,        "EC terms (NMDC integrated)"),

    # ---- Literature ----
    VolumeRow("Curated literature",   "kescience_paperblast.curatedgene",                                  None,        "PaperBLAST curated genes"),
    VolumeRow("Curated literature",   "kescience_pubmed.pubmed_article_wide",                              None,        "PubMed article records (kescience)"),
]


def collect_volumes(spark) -> list[dict]:
    """Run each COUNT(*) / COUNT(DISTINCT) and return one row per ENTITIES entry."""
    rows: list[dict] = []
    for v in ENTITIES:
        try:
            if v.count_col:
                q = f"SELECT COUNT(DISTINCT `{v.count_col}`) FROM {v.table}"
            else:
                q = f"SELECT COUNT(*) FROM {v.table}"
            n = spark.sql(q).collect()[0][0]
            rows.append({
                "entity_class": v.entity_class,
                "table":        v.table,
                "count_col":    v.count_col or "",
                "rows":         n,
                "label":        v.label,
                "error":        "",
            })
            print(f"  OK   {v.table:65s}  {n:>15,}")
        except Exception as e:
            msg = str(e).split("\n", 1)[0][:100]
            rows.append({
                "entity_class": v.entity_class,
                "table":        v.table,
                "count_col":    v.count_col or "",
                "rows":         None,
                "label":        v.label,
                "error":        msg,
            })
            print(f"  FAIL {v.table:65s}  {msg}")
    return rows
