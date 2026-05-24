"""Topic-tagging heuristics for BERDL tables.

A table is assigned one primary topic (best-fit) and zero or more secondary topics.
Tags are derived from (db_name, table_name, column_names) via regex rules ordered
from most specific to most general. The first matching rule wins for the primary
tag; additional matches become secondary tags.

The tag set is intentionally small (~15) so the resulting topic-map figure is
readable. If a table is genuinely "everything," prefer the dominant function.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    tag: str
    db_pattern: str | None = None
    table_pattern: str | None = None
    column_pattern: str | None = None


# Ordered from most specific to most general. First match wins for primary.
RULES: list[Rule] = [
    # ---- Phage / mobile elements ----
    Rule("mobile_phage", db_pattern=r"phagefoundry_.*"),
    Rule("mobile_phage", db_pattern=r"arkinlab_mobilome"),
    Rule("mobile_phage", db_pattern=r"refdata_jgi_virus"),
    Rule("mobile_phage", table_pattern=r"^(prophage|mge|virus|phage|genomad|host_mag|imgvr_|metavr_|uvig_).*"),
    Rule("mobile_phage", column_pattern=r"(prophage|phage_id|terminase|capsid|integrase|mge_id|uvig)"),
    # ---- Multi-omics ----
    Rule("multiomics", db_pattern=r"nmdc_results"),
    Rule("multiomics", table_pattern=r"^(metabolomics|proteomics|lipidomics|transcriptomics|mass_spectrometry|biosample_set_metag|biosample_set_metat|biosample_set_metab|biosample_set_metap|biosample_set_metal).*"),
    Rule("multiomics", column_pattern=r"(metabolite|m_z_value|peak_area|protein_id|lipid_class|read_count_metat)"),
    # nmdc_arkin: kraken/gottcha taxonomic profiles, NOM mass spec, metaT
    Rule("multiomics", db_pattern=r"nmdc_arkin", table_pattern=r"^(nom_|kraken_|gottcha_|metatranscriptomics_).*"),
    # ---- Structural biology ----
    Rule("structural", db_pattern=r".*(alphafold|pdb).*"),
    Rule("structural", table_pattern=r"^(alphafold|pdb_|structural_).*"),
    # ---- Literature / curated ----
    Rule("literature", db_pattern=r"kescience_(paperblast|pubmed)"),
    Rule("literature", table_pattern=r"^(pubmed_|curatedgene|curatedpaper|paper).*"),
    Rule("literature", column_pattern=r"(pmid|pubmed_id|doi|paper_id)"),
    # ---- Reference protein families ----
    Rule("reference_protein", db_pattern=r".*(uniref|uniprot|interpro).*"),
    Rule("reference_protein", table_pattern=r"^(clustermember|cluster|entity)$", db_pattern=r".*(uniref|uniprot).*"),
    # ---- Fitness / phenotype ----
    Rule("fitness_phenotype", db_pattern=r"kescience_fitnessbrowser"),
    Rule("fitness_phenotype", db_pattern=r"kescience_bacdive"),
    Rule("fitness_phenotype", db_pattern=r"kescience_webofmicrobes"),
    Rule("fitness_phenotype", db_pattern=r"kbase_phenotype"),
    Rule("fitness_phenotype", db_pattern=r"globalusers_phenotype.*"),
    Rule("fitness_phenotype", db_pattern=r"globalusers_carbon_source_phenotypes"),
    Rule("fitness_phenotype", table_pattern=r"^(growth|fitness|tnseq|rb_tnseq|gene_fitness|gene_expt|gene_essential|trait_).*"),
    Rule("fitness_phenotype", column_pattern=r"(fitness_score|t_score|growth_rate|umax|carbon_source_growth)"),
    # ---- Biochemistry / models ----
    Rule("biochemistry", db_pattern=r"kbase_msd_biochemistry"),
    Rule("biochemistry", table_pattern=r"^(reaction|compound|molecule|modelseed|metacyc|fba_).*"),
    Rule("biochemistry", column_pattern=r"(rxn_id|cpd_id|modelseed_id|metacyc_id|delta_g)"),
    # ---- Pathway / function ----
    Rule("pathway", table_pattern=r"^(gapmind|pathway|kegg_pathway|brite|pwy_|module_completeness).*"),
    Rule("pathway", column_pattern=r"(pathway_id|gapmind_score|module_id|kegg_pathway)"),
    # ---- Pangenome / gene families ----
    Rule("pangenome", db_pattern=r"kbase_ke_pangenome"),
    Rule("pangenome", db_pattern=r"globalusers_kepangenome.*"),
    Rule("pangenome", table_pattern=r"^(gene_cluster|pangenome|gene_genecluster|core_gene|accessory_gene|orthogroup|encoded_feature).*"),
    Rule("pangenome", column_pattern=r"(gene_cluster_id|is_core|is_accessory|is_singleton)"),
    # ---- Annotation ----
    Rule("annotation", table_pattern=r".*(eggnog|bakta|interpro|cog|pfam|kegg|kofam|go_mapping|amrfinder|cazy).*"),
    Rule("annotation", column_pattern=r"(eggnog_og|cog_category|pfam_id|interpro_id|ec_number|kegg_ko|cazy_family)"),
    # nmdc_arkin ontology integration (GO/EC/RHEA terms + hierarchies)
    Rule("annotation", db_pattern=r"nmdc_arkin", table_pattern=r"^(go_|ec_|rhea_|annotation_).*"),
    # ---- Taxonomy / phylogeny ----
    Rule("taxonomy", table_pattern=r".*(gtdb|taxonomy|taxon_mapping|phylogenetic_tree|species_clade|asv).*"),
    Rule("taxonomy", column_pattern=r"(gtdb_taxonomy|ncbi_taxon_id|taxon_id|phylum|family|genus|species)"),
    Rule("taxonomy", db_pattern=r"nmdc_arkin", table_pattern=r"^taxstring.*"),
    # ---- Genome reference / assembly ----
    Rule("genome", db_pattern=r"refdata_(gem_mags|jgi_gem_mags|ncbi|spire)"),
    Rule("genome", db_pattern=r"kbase_all_the_bacteria"),
    Rule("genome", db_pattern=r"kbase_genomes"),
    Rule("genome", table_pattern=r"^(genome|assembly|contig|checkm2?|dram|browser_).*"),
    Rule("genome", column_pattern=r"(genome_id|assembly_accession|gcf|gca|checkm_completeness)"),
    # ---- Field / observational ----
    Rule("field_observational", db_pattern=r"enigma_coral"),
    Rule("field_observational", db_pattern=r"usgs_produced_waters"),
    Rule("field_observational", db_pattern=r"netl_pw_dna"),
    Rule("field_observational", db_pattern=r"planetmicrobe_planetmicrobe.*"),
    Rule("field_observational", db_pattern=r"u_.*planetmicrobe.*"),
    Rule("field_observational", db_pattern=r"arkinlab_envdbs"),
    Rule("field_observational", db_pattern=r"arkinlab_microbeatlas"),
    Rule("field_observational", db_pattern=r"msyscolo_grow"),
    Rule("field_observational", table_pattern=r"^(sdt_|ddt_|core_|well_|sample_).*"),
    # ---- Sample / environment metadata ----
    Rule("environment", db_pattern=r"nmdc_(metadata|ncbi_biosamples)"),
    Rule("environment", table_pattern=r"^(biosample|ncbi_env|img_env|sample|isolation|alphaearth).*"),
    Rule("environment", column_pattern=r"(latitude|longitude|env_broad|env_local|envo_id|gold_id|isolation_source)"),
    # ---- Strain modelling / integration ----
    Rule("integration", db_pattern=r"protect_(integration|mind)"),
    Rule("integration", db_pattern=r"phagefoundry_strain_modelling"),
    Rule("integration", db_pattern=r"ese_ganymede"),
    Rule("integration", table_pattern=r"^(strainmodelling|mind_|protect_)"),
    # nmdc_arkin ML embeddings (token/abiotic/biochem/trait/unified embeddings)
    Rule("integration", db_pattern=r"nmdc_arkin", table_pattern=r"^(embedding|.*_embeddings|abiotic_|biochemical_|vocab_registry|unified_embeddings).*"),
    # KBase Workspace shadow tables (per-user "u_*" or "kbase_*" with canonical_blob_uri signature)
    Rule("integration", column_pattern=r"(canonical_blob_uri|source_upa|kbase_type)"),
    # ---- System / infra ----
    Rule("system", db_pattern=r".*(test|ontology_source).*"),
    Rule("system", table_pattern=r"^(test_|ontology_|prefix|entailed_edge|statements).*"),
    Rule("system", db_pattern=r"globalusers_(demo_shared|spark_queries)"),
    Rule("system", db_pattern=r"nmdc_arkin", table_pattern=r"^(omics_files_table|trait_sources)$"),
]


def tag_table(db_name: str, table_name: str, column_names: list[str]) -> tuple[str, list[str]]:
    """Return (primary_tag, list_of_secondary_tags) for a table.

    Falls back to 'unclassified' if no rule matches — that's a signal worth
    investigating, not an error.
    """
    matched: list[str] = []
    cols_blob = " ".join(column_names).lower()
    for r in RULES:
        if r.db_pattern and not re.fullmatch(r.db_pattern, db_name):
            continue
        if r.table_pattern and not re.match(r.table_pattern, table_name.lower()):
            continue
        if r.column_pattern and not re.search(r.column_pattern, cols_blob):
            continue
        if r.tag not in matched:
            matched.append(r.tag)
    if not matched:
        return ("unclassified", [])
    return (matched[0], matched[1:])


# Manually curated tenant -> agency/program mapping. Update as authoritative
# information becomes available; this is a first-pass inference from the
# `data/berdl_inventory.md` tenant descriptions and public program pages.
TENANT_TO_AGENCY = {
    "arkinlab":     {"agency": "DOE/Academic",  "program": "LBNL Arkin Lab",                       "primary_funder": "DOE-BER + multi"},
    "enigma":       {"agency": "DOE-BER",       "program": "ENIGMA SFA",                            "primary_funder": "DOE-BER"},
    "ese":          {"agency": "DOE-BER",       "program": "OPAL platform",                         "primary_funder": "DOE-BER"},
    "globalusers":  {"agency": "Multi",          "program": "Shared/global user namespace",          "primary_funder": "mixed"},
    "kbase":        {"agency": "DOE-BER",       "program": "KBase",                                 "primary_funder": "DOE-BER"},
    "kescience":    {"agency": "DOE-BER",       "program": "KBase Knowledge Engine",                "primary_funder": "DOE-BER"},
    "msyscolo":     {"agency": "Academic",      "program": "Microbial Ecosystems Lab (CSU)",        "primary_funder": "NSF/USDA (likely)"},
    "netl":         {"agency": "DOE-FE",        "program": "NETL Produced Water DNA",               "primary_funder": "DOE-FE"},
    "nmdc":         {"agency": "DOE-BER",       "program": "NMDC",                                  "primary_funder": "DOE-BER"},
    "phagefoundry": {"agency": "Defense/HHS",   "program": "Phage Foundry",                         "primary_funder": "DOD/HHS (likely)"},
    "planetmicrobe":{"agency": "NSF",           "program": "Planet Microbe",                        "primary_funder": "NSF"},
    "protect":      {"agency": "ARPA-H",        "program": "PROTECT",                               "primary_funder": "ARPA-H"},
    "refdata":      {"agency": "DOE-BER",       "program": "KBase Reference Data",                  "primary_funder": "DOE-BER"},
    "u":            {"agency": "User",          "program": "User personal namespace",                "primary_funder": "n/a"},
    "usgs":         {"agency": "DOI",           "program": "USGS Produced Waters / River Geochem",  "primary_funder": "DOI"},
}


def tenant_of(db_name: str) -> str:
    """Extract tenant prefix from a database name."""
    return db_name.split("_", 1)[0]
