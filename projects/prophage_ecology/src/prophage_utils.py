"""
Prophage module classification and annotation search utilities.

Defines the 7 operationally defined prophage gene modules (A-G) and provides
functions to classify eggNOG-annotated gene clusters into modules based on
PFAMs, Description keywords, KEGG KOs, and COG categories.
"""

import re
from typing import Optional

# =============================================================================
# Module Definitions
# =============================================================================
# Each module has:
#   - description_keywords: case-insensitive substrings to match in eggNOG Description
#   - pfam_keywords: case-insensitive substrings to match in eggNOG PFAMs column
#   - kegg_kos: exact KEGG KO identifiers (matched with LIKE '%KO%')
#   - presence_rule: how to determine module presence per genome
#   - key_markers: the most diagnostic genes for this module

MODULES = {
    "A_packaging": {
        "full_name": "Packaging Module",
        "description_keywords": [
            "terminase large subunit", "terminase small subunit",
            "terminase", "terl", "ters",
            "portal protein", "phage portal",
            "dna packaging", "phage packaging",
        ],
        "pfam_keywords": [
            "Terminase_1", "Terminase_GpA", "Terminase_6",
            "Terminase_3", "Terminase_5",
            "Phage_portal", "SPP1_gp7",
        ],
        "kegg_kos": [
            "K06909",  # terminase large subunit
            "K07474",  # phage portal protein (some annotations)
        ],
        "presence_rule": "TerL alone OR Portal + TerS",
        "key_markers": ["terminase large subunit"],
    },
    "B_head_morphogenesis": {
        "full_name": "Head Morphogenesis Module",
        "description_keywords": [
            "major capsid protein", "capsid protein",
            "hk97", "head morphogenesis",
            "capsid protease", "scaffold protein",
            "prohead", "head-tail connector",
        ],
        "pfam_keywords": [
            "HK97", "Phage_cap_E", "Phage_cap_P2",
            "Peptidase_S14",  # capsid maturation protease
            "Phage_Mu_F",
        ],
        "kegg_kos": [],
        "presence_rule": "MCP (major capsid protein) required",
        "key_markers": ["major capsid protein"],
    },
    "C_tail": {
        "full_name": "Tail Module",
        "description_keywords": [
            "tail tube", "tail sheath", "tape measure",
            "baseplate", "tail fiber", "tail spike",
            "tail protein", "tail assembly",
            "tail length", "tail tip",
        ],
        "pfam_keywords": [
            "Phage_tail_S", "Phage_sheath",
            "Phage_fiber", "Phage_fiber_2",
            "Phage_base_V", "BppU_N",
            "Tail_P2_S", "PhageMin_Tail",
            "Phage_T4_gp19",  # tail tube
            "Phage_spike_2",
        ],
        "kegg_kos": [],
        "presence_rule": ">=1 structural tail protein",
        "key_markers": ["tail tube protein", "tail sheath protein", "tape measure protein"],
    },
    "D_lysis": {
        "full_name": "Lysis Module",
        "description_keywords": [
            "holin", "endolysin", "lysin",
            "spanin", "lysis protein",
            "rz", "rz1",
            "n-acetylmuramoyl",  # lysozyme family
            "lysozyme",
            "murein transglycosylase",
        ],
        "pfam_keywords": [
            "Phage_holin_1", "Phage_holin_2", "Phage_holin_3",
            "Phage_holin_4", "Phage_holin_5", "Phage_holin_6",
            "Phage_lysozyme", "Endolysin_autolysin",
            "SLT",  # soluble lytic transglycosylase
            "Glyco_hydro_108",  # lambda lysozyme
            "Glyco_hydro_19",  # chitinase/lysozyme
            "Phage_lysis",
        ],
        "kegg_kos": [],
        "presence_rule": "Holin OR endolysin",
        "key_markers": ["holin", "endolysin"],
    },
    "E_integration": {
        "full_name": "Integration Module",
        "description_keywords": [
            "integrase", "site-specific recombinase",
            "excisionase", "phage integrase",
            "tyrosine recombinase", "serine recombinase",
        ],
        "pfam_keywords": [
            "Phage_integrase", "Phage_int_SAM_5",
            "Phage_int_SAM_4", "Phage_int_SAM_9",
            "Recombinase",  # broad
            "Phage_integ_N",
        ],
        "kegg_kos": [
            "K14059",  # phage integrase
        ],
        "presence_rule": "Integrase required",
        "key_markers": ["integrase"],
    },
    "F_lysogenic_regulation": {
        "full_name": "Lysogenic Regulation Module",
        "description_keywords": [
            "ci repressor", "ci-like", "phage repressor",
            "cro", "cro-like", "cro regulator",
            "antitermination", "antiterminator",
            "lambda repressor", "phage regulatory",
            "n-like antitermination", "q-like antitermination",
        ],
        "pfam_keywords": [
            "XRE_N",  # CI-like HTH domain
            "HTH_3",  # Cro-like HTH domain
            "Phage_CI_repr",
            "Lambda_repressor",
            "Phage_antiter_Q",  # Q antiterminator
        ],
        "kegg_kos": [],
        "presence_rule": "CI-like repressor required",
        "key_markers": ["CI-like repressor"],
    },
    "G_anti_defense": {
        "full_name": "Anti-Defense Module",
        "description_keywords": [
            "anti-crispr", "anti-restriction",
            "anti-defense", "ardA",
            "anti-cbass", "ocr",
            "restriction alleviation",
        ],
        "pfam_keywords": [
            "ArdA",
            "Anti_CRISPR",
        ],
        "kegg_kos": [],
        "presence_rule": "Any recognized anti-defense gene",
        "key_markers": ["anti-CRISPR", "anti-restriction"],
    },
}


def classify_gene_to_module(
    description: Optional[str],
    pfams: Optional[str],
    kegg_ko: Optional[str],
    cog_category: Optional[str],
) -> list[str]:
    """
    Classify a gene cluster into one or more prophage modules based on
    eggNOG annotation fields.

    Parameters
    ----------
    description : str or None
        eggNOG Description field
    pfams : str or None
        eggNOG PFAMs field
    kegg_ko : str or None
        eggNOG KEGG_ko field
    cog_category : str or None
        eggNOG COG_category field

    Returns
    -------
    list of str
        Module IDs (e.g., ["A_packaging", "E_integration"]) that match.
        Empty list if no module matches.
    """
    matches = []
    desc_lower = (description or "").lower()
    pfams_lower = (pfams or "").lower()
    kegg_str = kegg_ko or ""

    for module_id, module_def in MODULES.items():
        matched = False

        # Check description keywords
        for kw in module_def["description_keywords"]:
            if kw.lower() in desc_lower:
                matched = True
                break

        # Check PFAMs keywords
        if not matched:
            for kw in module_def["pfam_keywords"]:
                if kw.lower() in pfams_lower:
                    matched = True
                    break

        # Check KEGG KOs
        if not matched:
            for ko in module_def["kegg_kos"]:
                if ko in kegg_str:
                    matched = True
                    break

        if matched:
            matches.append(module_id)

    return matches


def is_terL(description: Optional[str], pfams: Optional[str], kegg_ko: Optional[str]) -> bool:
    """Check if a gene cluster is a terminase large subunit (TerL)."""
    desc_lower = (description or "").lower()
    pfams_lower = (pfams or "").lower()
    kegg_str = kegg_ko or ""

    # Description match
    if "terminase large subunit" in desc_lower:
        return True
    if "terminase, large subunit" in desc_lower:
        return True

    # PFam match for TerL-specific domains
    if "terminase_1" in pfams_lower or "terminase_gpa" in pfams_lower:
        return True

    # KEGG KO match
    if "K06909" in kegg_str:
        return True

    return False


def build_spark_where_clause() -> str:
    """
    Build a Spark SQL WHERE clause to find all potential prophage gene clusters
    from eggnog_mapper_annotations.

    Returns
    -------
    str
        WHERE clause string (without the WHERE keyword)
    """
    conditions = []

    # Collect all unique description keywords across modules
    all_desc_keywords = set()
    for module_def in MODULES.values():
        for kw in module_def["description_keywords"]:
            all_desc_keywords.add(kw.lower())

    # Collect all unique PFam keywords
    all_pfam_keywords = set()
    for module_def in MODULES.values():
        for kw in module_def["pfam_keywords"]:
            all_pfam_keywords.add(kw)

    # Collect all KEGG KOs
    all_kegg_kos = set()
    for module_def in MODULES.values():
        for ko in module_def["kegg_kos"]:
            all_kegg_kos.add(ko)

    # Build Description conditions
    for kw in sorted(all_desc_keywords):
        conditions.append(f"LOWER(ann.Description) LIKE '%{kw}%'")

    # Build PFAMs conditions
    for kw in sorted(all_pfam_keywords):
        conditions.append(f"LOWER(ann.PFAMs) LIKE '%{kw.lower()}%'")

    # Build KEGG KO conditions
    for ko in sorted(all_kegg_kos):
        conditions.append(f"ann.KEGG_ko LIKE '%{ko}%'")

    return "\n   OR ".join(conditions)


def get_module_summary() -> str:
    """Return a formatted summary of all modules for documentation."""
    lines = []
    for module_id, module_def in MODULES.items():
        lines.append(f"### Module {module_id}: {module_def['full_name']}")
        lines.append(f"- **Presence rule**: {module_def['presence_rule']}")
        lines.append(f"- **Key markers**: {', '.join(module_def['key_markers'])}")
        lines.append(f"- **Description keywords**: {len(module_def['description_keywords'])}")
        lines.append(f"- **PFam keywords**: {len(module_def['pfam_keywords'])}")
        lines.append(f"- **KEGG KOs**: {len(module_def['kegg_kos'])}")
        lines.append("")
    return "\n".join(lines)
