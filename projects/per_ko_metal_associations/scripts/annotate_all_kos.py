"""
Annotate every KO tested across all project datasets with KEGG descriptions and
functional categories using two bulk KEGG REST requests (list/ko + br:ko00001).

Output: data/all_ko_annotations.csv
Cache:  data/kegg_bulk_cache.json  (persistent; re-runs are ~instant)

Run time: ~20 seconds first run, ~2 seconds on re-run.
"""

import json
import pathlib
import re
import urllib.request

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CACHE_PATH = DATA / "kegg_bulk_cache.json"
OUT_PATH = DATA / "all_ko_annotations.csv"


# ── 1. Collect KO universe ────────────────────────────────────────────────────

sources = {
    "in_mgnify":       (DATA / "mgnify_all_ko_associations.csv", "ko_id"),
    "in_spire":        (DATA / "spire_all_ko_associations.csv",  "ko_id"),
    "in_nb15":         (DATA / "nb15_usa_usgs_pointlevel_per_ko_mwas.csv", "ko_id"),
    "in_nb15b":        (DATA / "nb15b_usa_usgs_ph_adjusted_per_ko_mwas.csv", "ko_id"),
    "in_cme_pangenome":(ROOT.parent / "comprehensive_metal_ecology" / "data" /
                        "confound_results" / "ke_pangenome_genomewide_raw_scan.csv", "ko_id"),
    "in_cme_levinsb":  (ROOT.parent / "comprehensive_metal_ecology" / "data" /
                        "39_per_ko_levinsB_pgls.csv", "ko"),
}

membership = {}
for flag, (path, col) in sources.items():
    df = pd.read_csv(path, usecols=[col])
    for raw in df[col].dropna().unique():
        # ke_pangenome groups co-orthologs as "K00001,K00002" — split each
        for ko in str(raw).split(","):
            ko = ko.strip()
            if ko:
                membership.setdefault(ko, {})[flag] = True

all_kos = sorted(membership.keys())
print(f"Total unique KOs: {len(all_kos)}")
for flag in sources:
    n = sum(1 for v in membership.values() if v.get(flag))
    print(f"  {flag}: {n}")


# ── 2. Fetch KEGG data (two bulk requests, persistent cache) ──────────────────

def fetch_url(url, timeout=120):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read().decode()


def load_kegg_data():
    """Return (descriptions, brite_map) from cache or by fetching."""
    if CACHE_PATH.exists():
        d = json.loads(CACHE_PATH.read_text())
        if "descriptions" in d and "brite" in d:
            print("Loaded from cache.")
            return d["descriptions"], d["brite"]

    print("Fetching list/ko ...")
    list_txt = fetch_url("https://rest.kegg.jp/list/ko")
    descriptions = {}
    for line in list_txt.strip().splitlines():
        parts = line.split("\t", 1)
        if len(parts) == 2 and parts[0].startswith("K"):
            descriptions[parts[0]] = parts[1].strip()

    print(f"  {len(descriptions)} KO descriptions fetched")

    print("Fetching br:ko00001 BRITE hierarchy ...")
    brite_txt = fetch_url("https://rest.kegg.jp/get/br:ko00001")
    brite = {}   # ko_id → {l1_code, l1_name, l2_code, l2_name}
    cur_l1_code, cur_l1_name = "", ""
    cur_l2_code, cur_l2_name = "", ""
    for line in brite_txt.splitlines():
        if line.startswith("A"):
            m = re.match(r"A(09\d{3}) (.+)", line)
            if m:
                cur_l1_code, cur_l1_name = m.group(1), m.group(2).strip()
                cur_l2_code, cur_l2_name = "", ""
        elif line.startswith("B"):
            m = re.match(r"B {2}(09\d{3}) (.+)", line)
            if m:
                cur_l2_code, cur_l2_name = m.group(1), m.group(2).strip()
        elif line.startswith("D"):
            m = re.match(r"D {6}(K\d{5})", line)
            if m:
                ko = m.group(1)
                if ko not in brite:   # keep first occurrence (most specific)
                    brite[ko] = {
                        "l1_code": cur_l1_code, "l1_name": cur_l1_name,
                        "l2_code": cur_l2_code, "l2_name": cur_l2_name,
                    }

    print(f"  {len(brite)} KOs mapped in BRITE hierarchy")

    CACHE_PATH.write_text(json.dumps(
        {"descriptions": descriptions, "brite": brite}, indent=2))
    print(f"  Cache written to {CACHE_PATH}")
    return descriptions, brite


descriptions, brite = load_kegg_data()


# ── 3. Broad-category classification ─────────────────────────────────────────

# KEGG L2 code → broad_category
L2_MAP = {
    "09101": "Carbohydrate metabolism",
    "09102": "Energy metabolism",
    "09103": "Lipid metabolism",
    "09104": "Nucleotide metabolism",
    "09105": "Amino acid metabolism",
    "09106": "Metabolism of other amino acids",
    "09107": "Glycan biosynthesis / metabolism",
    "09108": "Cofactor biosynthesis",
    "09109": "Terpenoids / polyketides",
    "09110": "Secondary metabolites",
    "09111": "Xenobiotics biodegradation",
    "09112": "Metabolism — other",
    "09121": "Transcription",
    "09122": "Translation",
    "09123": "Protein folding / degradation",
    "09124": "DNA repair / stress",
    "09131": "Transport",
    "09132": "Signal transduction",
    "09133": "Signaling molecules",
    "09141": "Transport",
    "09142": "Cell growth / death",
    "09143": "Motility / flagellar",
    "09144": "Cellular community",
    "09145": "Cellular community",
    "09151": "Immune system",
    "09152": "Endocrine system",
    "09153": "Circulatory system",
    "09154": "Digestive system",
    "09155": "Excretory system",
    "09156": "Nervous system",
    "09157": "Sensory system",
    "09158": "Development and regeneration",
    "09159": "Aging",
    "09161": "Cancer",
    "09162": "Cardiovascular disease",
    "09163": "Immune disease",
    "09164": "Neurodegenerative disease",
    "09165": "Substance dependence",
    "09166": "Antimicrobial resistance",
    "09167": "Endocrine and metabolic disease",
    "09171": "Infectious disease: viral",
    "09172": "Infectious disease: bacterial",
    "09174": "Infectious disease: parasitic",
    "09181": "Protein families: metabolism",
    "09182": "Protein families: genetic information processing",
    "09183": "Protein families: signaling and cellular processes",
    "09184": "RNA family",
    "09191": "Unclassified: metabolism",
    "09192": "Unclassified: genetic information processing",
    "09193": "Unclassified: signaling and cellular processes",
    "09194": "Poorly characterized",
}

# L1 fallback
L1_MAP = {
    "09100": "Metabolism",
    "09120": "Genetic information processing",
    "09130": "Environmental information processing",
    "09140": "Cellular processes",
    "09150": "Organismal systems",
    "09160": "Human diseases",
    "09180": "Other",
    "09190": "Uncharacterized",
}

# Keyword overrides checked BEFORE BRITE (high-confidence biological labels)
METAL_RESIST_RE = re.compile(
    r"\bmer[ABCDFPRT2]\b|\bars[ABCR]\b|\barsH\b|\bchrA\b"
    r"|\bcadA\b|\bczcA\b|\bczc[BCDR]\b|\bsilA\b|\bcobalt.resist"
    r"|heavy.metal.{0,15}resist|metal.{0,10}resist|tellurite.resist"
    r"|arsenate.resist|chromate.resist",
    re.IGNORECASE,
)
DNA_REPAIR_RE = re.compile(
    r"\bDNA repair\b|photo.?lyase|\brecombination protein\b"
    r"|\bSOS response\b|\bumuC\b|\bumuD\b|\brecA\b|\blexA\b"
    r"|\bmutL\b|\bmutS\b|\bmutH\b|\bnucleotide excision\b"
    r"|\bbase.excision\b|\bmismatch repair\b",
    re.IGNORECASE,
)
NITROGEN_RE = re.compile(
    r"\bnitrogenase\b|\bnitrogen fixation\b|\bnitrite reductase\b"
    r"|\bnitrous.oxide\b|\bdenitrif|\bnifH\b|\bnifD\b",
    re.IGNORECASE,
)
MOTILITY_RE = re.compile(
    r"\bflagell|\bcheY\b|\bcheA\b|\bpili\b|\bfimbriae\b"
    r"|\bmotility\b|\bfliC\b|\bflgL\b|\bfliG\b",
    re.IGNORECASE,
)
MEMBRANE_RE = re.compile(
    r"\bouter membrane\b|\binner membrane\b|\blipoprotein\b"
    r"|\bpeptidoglycan\b|\bcell wall\b|\bporin\b|\bmembrane protein\b",
    re.IGNORECASE,
)
TRANSPORT_KW_RE = re.compile(
    r"\bABC transporter\b|\bMFS transporter\b|\befflux pump\b"
    r"|\bpermease\b|\buptake.*protein\b|\btransporter\b|\bchannel protein\b"
    r"|\btransport.*protein\b|\btransport system\b",
    re.IGNORECASE,
)
REGULATION_KW_RE = re.compile(
    r"\btranscriptional regulator\b|\btranscription factor\b"
    r"|\bresponse regulator\b|\bsensor histidine kinase\b"
    r"|\btwo-component\b|\bquorum.sensing\b|\bDNA-binding protein\b",
    re.IGNORECASE,
)
# L2 codes where KEGG BRITE is a catch-all and keyword rules are more informative
_UNINFORMATIVE_L2 = {
    "09181", "09182", "09183", "09184",
    "09191", "09192", "09193", "09194",
}


SIMPLIFIED = {
    # Metabolism sub-categories → "Metabolism"
    "Carbohydrate metabolism":          "Metabolism",
    "Energy metabolism":                "Metabolism",
    "Lipid metabolism":                 "Metabolism",
    "Nucleotide metabolism":            "Metabolism",
    "Amino acid metabolism":            "Metabolism",
    "Metabolism of other amino acids":  "Metabolism",
    "Glycan biosynthesis / metabolism": "Metabolism",
    "Terpenoids / polyketides":         "Metabolism",
    "Secondary metabolites":            "Metabolism",
    "Xenobiotics biodegradation":       "Metabolism",
    "Metabolism — other":               "Metabolism",
    "Protein families: metabolism":     "Metabolism",
    "Unclassified: metabolism":         "Metabolism",
    # Genetic info processing
    "Transcription":                    "Transcription / Regulation",
    "Signal transduction":              "Transcription / Regulation",
    "Signaling molecules":              "Transcription / Regulation",
    "Translation":                      "Metabolism",
    "Protein folding / degradation":    "Metabolism",
    # Specific categories preserved
    "Cofactor biosynthesis":            "Cofactor biosynthesis",
    "DNA repair / stress":              "DNA repair / stress",
    "Transport":                        "Transport",
    "Motility / flagellar":             "Motility / flagellar",
    "Membrane / cell envelope":         "Membrane / cell envelope",
    "Nitrogen cycling":                 "Nitrogen cycling",
    "Metal resistance":                 "Metal resistance",
    "Transcription / Regulation":       "Transcription / Regulation",
    "Cellular community":               "Other",
    "Cell growth / death":              "Other",
    "Protein families: signaling and cellular processes": "Other",
    "Protein families: genetic information processing":   "Other",
    "Unclassified: genetic information processing":       "Other",
    "Unclassified: signaling and cellular processes":     "Other",
    "Unclassified: metabolism":         "Metabolism",
    "Poorly characterized":             "Uncharacterized",
    "Human diseases":                   "Other",
    "Infectious disease: viral":        "Other",
    "Infectious disease: bacterial":    "Other",
    "Infectious disease: parasitic":    "Other",
    "Genetic information processing":   "Other",
    "Organismal systems":               "Other",
    "Other":                            "Other",
    "Uncharacterized":                  "Uncharacterized",
    # Catch-all for any unmapped
}


def simplified_category(broad):
    return SIMPLIFIED.get(broad, "Other")


def broad_category(ko_id, desc):
    b = brite.get(ko_id, {})
    l1 = b.get("l1_code", "")
    l2 = b.get("l2_code", "")

    # Keyword overrides (checked first)
    if METAL_RESIST_RE.search(desc):
        return "Metal resistance"
    if DNA_REPAIR_RE.search(desc):
        return "DNA repair / stress"
    if NITROGEN_RE.search(desc):
        return "Nitrogen cycling"
    if MOTILITY_RE.search(desc):
        return "Motility / flagellar"
    if MEMBRANE_RE.search(desc):
        return "Membrane / cell envelope"

    # For uninformative BRITE catch-alls, keyword classification is more useful
    if l2 in _UNINFORMATIVE_L2 or l1 in ("09180", "09190") or not l1:
        if TRANSPORT_KW_RE.search(desc):
            return "Transport"
        if REGULATION_KW_RE.search(desc):
            return "Transcription / Regulation"
        if MEMBRANE_RE.search(desc):
            return "Membrane / cell envelope"
        if MOTILITY_RE.search(desc):
            return "Motility / flagellar"
        if NITROGEN_RE.search(desc):
            return "Nitrogen cycling"

    # BRITE L2 (most specific, for informative categories)
    if l2 in L2_MAP:
        return L2_MAP[l2]

    # BRITE L1 fallback
    if l1 in L1_MAP:
        cat = L1_MAP[l1]
        if cat:
            return cat

    if not desc.strip():
        return "Uncharacterized"

    return "Other"


# ── 4. Build and save output table ────────────────────────────────────────────

rows = []
for ko in all_kos:
    desc = descriptions.get(ko, "")
    b = brite.get(ko, {})
    row = {
        "ko_id":          ko,
        "description":    desc,
        "kegg_l1_code":   b.get("l1_code", ""),
        "kegg_l1_name":   b.get("l1_name", ""),
        "kegg_l2_code":   b.get("l2_code", ""),
        "kegg_l2_name":   b.get("l2_name", ""),
        "broad_category": broad_category(ko, desc),
    }
    row["simplified_category"] = simplified_category(row["broad_category"])
    for flag in sources:
        row[flag] = membership[ko].get(flag, False)
    rows.append(row)

df = pd.DataFrame(rows)
df.to_csv(OUT_PATH, index=False)
print(f"\nWrote {len(df)} rows → {OUT_PATH}")
print("\nBroad category counts:")
print(df["broad_category"].value_counts().to_string())
print(f"\nDataset coverage:")
for flag in sources:
    print(f"  {flag}: {int(df[flag].sum())}")
print("\nSimplified category counts:")
print(df["simplified_category"].value_counts().to_string())
print(f"\nKOs with BRITE classification: {(df['kegg_l1_code'] != '').sum()}")
print(f"KOs with description:          {(df['description'] != '').sum()}")
